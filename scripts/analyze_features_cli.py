"""跑通 1.4 特征智能分析：合并多个应用特征 CSV → 特征选择 → 打印 FeatureSummary。

用法：
    # facebook(正类) vs instagram+twitter(对照)
    .venv/bin/python scripts/analyze_features_cli.py \
        --csv data/processed/features_facebook.csv \
               data/processed/features_instagram.csv \
               data/processed/features_twitter.csv \
        --target facebook
    # 用 --label-col 指定标签列（默认 app），--out 可保存 top 特征清单
    # --save <out.csv>：把 selected 特征清单保存为 CSV
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.feature_miner.analyzer.select import FeatureSelector

# 纯标识/血缘列与时间戳伪特征，不参与特征学习
_DROP = {"pcap", "app", "src_ip", "dst_ip", "start_time", "end_time",
         "time_first", "time_last", "flow_stat", "hdr_desc"}


def main() -> None:
    ap = argparse.ArgumentParser(description="1.4 特征分析 CLI")
    ap.add_argument("--csv", nargs="+", required=True, help="一个或多个特征 CSV")
    ap.add_argument("--target", required=True, help="正类应用名（其余视为负类）")
    ap.add_argument("--label-col", default="app")
    ap.add_argument("--save", default=None, help="保存 top 特征清单到 CSV")
    args = ap.parse_args()

    parts = [pd.read_csv(c) for c in args.csv]
    df = pd.concat(parts, ignore_index=True)
    print(f"== 合并样本: {df.shape[0]} 流 × {df.shape[1]} 列")
    print(f"   标签分布: {dict(df[args.label_col].value_counts())}")
    print(f"   正类目标: {args.target}")

    y = (df[args.label_col] == args.target).astype(int)
    drop = set(_DROP) & set(df.columns)
    X = df.drop(columns=list(drop))

    sel = FeatureSelector()
    summary = sel.select(X, y)

    print(f"\n== 特征有效率: {summary.usable_rate:.1f}%  "
          f"({summary.n_usable_features}/{summary.n_total_features})  目标 ≥80%")
    print(f"== 被选特征数: {len(summary.selected)}")
    print("   " + "-" * 70)
    # 分字符串/数值两部分打印，突出可解释性
    print("【指纹/字符串通道】—— 直接可规则化：")
    for s in [s for s in summary.selected if s.kind == "string"]:
        print(f"   [{s.score:>6.3f}] {s.name:20s} {s.direction:22s} | {s.rationale}")
    print("【数值统计通道】—— 按区分度得分:")
    for s in [s for s in summary.selected if s.kind == "numeric"]:
        print(f"   [{s.score:>6.3f}] {s.name:36s} | {s.rationale}")
    print("   " + "-" * 70)
    print(f"== 有效性自评: {summary.note}")

    if args.save:
        rows = [{"name": s.name, "kind": s.kind, "score": s.score,
                 "direction": s.direction, "coverage": s.coverage,
                 "rationale": s.rationale} for s in summary.selected]
        out = Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(out, index=False)
        print(f"\n已保存 top 特征清单 → {out}")


if __name__ == "__main__":
    main()
