"""从特征矩阵自动生成规则文件（1.5 规则生成器 CLI，可解释、可人工修正）。

流程：合并特征 CSV → 二元标签(target vs rest) → 特征分析(1.4) →
      编译规则（两类）→ 写 rules/social.yaml

规则编译：
  A) 指纹断言规则（cost=low 优先评估）：字符串/指纹特征（tls_sni/ja3_hash/ja3s_hash/
     tls_alpn）中『在 target 类占比 ≥ 0.8 且全局覆盖 ≥ 5%』的取值，
     同特征聚合为一条 `in [...]` 规则 —— 握手即得、最省，优先命中。
  B) 统计阈值规则（cost=mid）：在 top 数值特征上用浅决策树抽路径（决策树路径抽规则），
     叶子正类纯度 ≥ 阈值 → 一条阈值规则。

用法：
    .venv/bin/python scripts/gen_rules_cli.py \
        --csv data/processed/features_facebook.csv \
              data/processed/features_instagram.csv \
              data/processed/features_twitter.csv \
        --target facebook \
        [--out rules/social.yaml] [--min-purity 0.85]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.dpi_engine.loader import RuleLoader  # noqa: E402  复用其 op 白名单/校验思路
from src.feature_miner.analyzer.select import FeatureSelector  # noqa: E402
from src.feature_miner.rule_gen.generator import RuleGenerator, RuleModel  # noqa: E402

_NON_FEATURE = {"pcap", "app", "src_ip", "dst_ip", "start_time", "end_time",
                "time_first", "time_last", "flow_stat", "hdr_desc"}

# 指纹特征名（字符串通道）→ 代价档位
_FINGERPRINT_COLS = ("tls_sni", "tls_alpn", "ja3_hash", "ja3s_hash")
# 时序类数值特征 → 归为 mid（更贵）的提示（这里统一 mid 即可，规则可人工调）


def _load_matrix(csvs: list[str]) -> pd.DataFrame:
    parts = [pd.read_csv(c) for c in csvs]
    df = pd.concat(parts, ignore_index=True)
    return df


def _fingerprint_rules(df: pd.DataFrame, target: str,
                       share_min: float = 0.8, cov_min: float = 0.005) -> list[RuleModel]:
    """通道 A：指纹特征 → 高置信 in 断言规则（cost=low, priority 靠前）。"""
    rules: list[RuleModel] = []
    n = len(df)
    prio = 10
    for col in _FINGERPRINT_COLS:
        if col not in df.columns:
            continue
        sub = df[[col, "app"]].dropna(subset=[col])
        if sub.empty:
            continue
        # 对每个取值：target 占比、全局覆盖率
        grouped = sub.groupby(col)["app"].agg(lambda s: (s == target).mean())
        cnt = sub.groupby(col).size()
        cand_vals = grouped[(grouped >= share_min) & (cnt / n >= cov_min)]
        if cand_vals.empty:
            continue
        values = sorted(cand_vals.index.tolist())
        conf = min(0.99, float(cand_vals.mean()))
        rules.append(RuleModel(
            rule_id=f"fp_{col}",
            priority=prio, cost="low",
            conditions=[{"feature": col, "op": "in", "value": values}],
            conclusion={"app": target, "confidence": round(conf, 3)},
        ))
        prio += 10
    return rules


def _tree_rule_paths(df: pd.DataFrame, target: str, num_cols: list[str],
                     purity_min: float, max_rules: int = 20) -> list[RuleModel]:
    """通道 B：浅决策树抽路径 → 统计阈值规则（cost=mid）。"""
    from sklearn.tree import DecisionTreeClassifier

    rules: list[RuleModel] = []
    n = len(df)
    X = df[num_cols].astype(float).fillna(df[num_cols].astype(float).median())
    y = (df["app"] == target).astype(int).values
    if y.sum() == 0 or y.sum() == len(y):
        return rules

    clf = DecisionTreeClassifier(max_depth=4, min_samples_leaf=max(100, int(n * 0.005)),
                                 random_state=0, class_weight="balanced")
    clf.fit(X.values, y)
    t = clf.tree_

    def walk(node: int, conds: list[dict], depth: int) -> None:
        if t.children_left[node] == t.children_right[node]:
            total = t.n_node_samples[node]
            pos = t.value[node][0][1]
            purity = pos / total if total else 0.0
            if purity >= purity_min and conds:
                rules.append(RuleModel(
                    rule_id=f"stat_{len(rules) + 1:03d}",
                    priority=100 + len(rules),
                    cost="mid",
                    conditions=conds,
                    conclusion={"app": target, "confidence": round(min(0.99, purity), 3)},
                ))
            return
        fname = X.columns[t.feature[node]]
        thr = float(t.threshold[node])
        walk(t.children_left[node],
             conds + [{"feature": fname, "op": "lte", "value": round(thr, 4)}], depth + 1)
        walk(t.children_right[node],
             conds + [{"feature": fname, "op": "gt", "value": round(thr, 4)}], depth + 1)

    walk(0, [], 0)
    return rules[:max_rules]


def main() -> None:
    ap = argparse.ArgumentParser(description="1.5 规则生成 CLI")
    ap.add_argument("--csv", nargs="+", required=True, help="一个或多个特征 CSV")
    ap.add_argument("--target", required=True, help="正类应用名")
    ap.add_argument("--out", default="rules/social.yaml")
    ap.add_argument("--min-purity", type=float, default=0.85, help="叶子正类纯度阈值")
    ap.add_argument("--share-min", type=float, default=0.8, help="指纹取值内 target 占比")
    ap.add_argument("--cov-min", type=float, default=0.005, help="指纹取值全局覆盖下限")
    ap.add_argument("--max-stat-rules", type=int, default=20)
    args = ap.parse_args()

    df = _load_matrix(args.csv)
    if "app" not in df.columns:
        print("!! 特征 CSV 缺少 app 标签列（extract_features_joyfuljay.py 会加）")
        sys.exit(1)
    print(f"== 样本: {df.shape[0]} 流; 标签分布 {dict(df['app'].value_counts())}")

    # 1) 特征分析（顺带输出有效率）
    y = (df["app"] == args.target).astype(int)
    drop = _NON_FEATURE & set(df.columns)
    sel = FeatureSelector()
    summary = sel.select(df.drop(columns=list(drop)), y)
    print(f"== 特征有效率 {summary.usable_rate:.1f}%; 自评: {summary.note}")

    # 2) 编译规则（两类）
    fingerprint = _fingerprint_rules(df, args.target,
                                     share_min=args.share_min, cov_min=args.cov_min)
    num_cols = [c for c in df.columns if c not in _NON_FEATURE
                and df[c].dtype != object]
    stat = _tree_rule_paths(df, args.target, num_cols,
                            purity_min=args.min_purity,
                            max_rules=args.max_stat_rules)
    rules = fingerprint + stat
    if not rules:
        print("!! 未生成任何规则（阈值过紧或样本太相似），可放宽 --share-min/--min-purity")
        sys.exit(1)

    # 3) 组装并写 YAML
    gen = RuleGenerator()
    doc = gen.build(rules, target=f"social:{args.target}",
                    description=f"场景一社交应用分类 — 正类 {args.target} "
                                f"(自动生成，可人工修正)")
    out = Path(args.out)
    gen.dump(doc, str(out))
    print(f"\n== 已生成 {len(rules)} 条规则 → {out}")
    print(f"   指纹断言 {len(fingerprint)} 条 (cost=low) | 统计阈值 {len(stat)} 条 (cost=mid)")
    if fingerprint:
        print("   指纹规则示例:")
        for r in fingerprint:
            vals = r.conditions[0]["value"]
            print(f"     {r.rule_id:8s} {r.conditions[0]['feature']:12s} in "
                  f"{vals[:4]}{'...' if len(vals) > 4 else ''}  → {r.conclusion}")
    if stat:
        print("   统计规则示例:")
        for r in stat[:5]:
            cond = "; ".join(f"{c['feature']} {c['op']} {c['value']}" for c in r.conditions)
            print(f"     {r.rule_id:8s} {cond}  → {r.conclusion}")

    # 4) 自检：生成的文件能被引擎 loader 重新加载（契约闭环验证）
    try:
        compiled = RuleLoader().load(str(out))
        n_rules = sum(len(v) for v in compiled["by_cost"].values())
        layers = {k: len(v) for k, v in compiled["by_cost"].items()}
        print(f"\n== [自检] 引擎可加载 ✓  {n_rules} 条规则, 分层 {layers}")
    except Exception as e:
        print(f"\n!! [自检] 引擎加载失败: {e}")


if __name__ == "__main__":
    main()
