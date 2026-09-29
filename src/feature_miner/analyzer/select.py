"""特征选择与有效性分析（阶段 1 已实现，对应 TODO 1.4）。

目标（对齐赛题指标 + 阶段1规划 §4.3）：
- 在样本上快速给出**可解释**的候选特征维度清单与识别方案；
- 特征有效率自测 ≥ 80%；
- 输出 FeatureSummary 供 rule_gen 消费，生成可人工修正的规则文件。

两个通道：
  A) 字符串/指纹特征（tls_sni / ja3_hash / ja3s_hash / tls_alpn）——
     做"类内覆盖率 + 类间区分"分析。这类特征语义极强，往往可直接规则化
     （如 'SNI ∈ {xxx} ⇒ 应用'），是对 DPI 规则最直接有用的产物。
  B) 数值统计特征（flow/timing/size/tcp）——
     单变量筛选（信息增益 / 单变量 AUC）快筛 → 树模型增益复核，
     输出重要性排序，供生成统计阈值规则。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


# 绝对时间戳类特征：区分度来自"抓包起始时刻不同"的人为差异，
# 对真实识别无辨识力（数据泄漏伪特征），一律剔除出特征学习。
_NON_ANALYTIC = {
    "time_first", "time_last", "start_time", "end_time",
    "first_response_time",
}


@dataclass
class SelectedFeature:
    """一个被选中的特征及其可解释依据。"""

    name: str                      # 特征名（与特征矩阵列名一致）
    score: float                   # 区分度得分（信息增益/AUC/覆盖率等，越大越好）
    rationale: str                 # 可解释依据（直接进规则 schema 的注释）
    kind: str = "numeric"          # 'numeric' | 'string'
    direction: str = ""            # 阈值方向/命中说明（供规则生成）
    coverage: float = 0.0          # 该特征的样本覆盖率（0~1）


@dataclass
class FeatureSummary:
    """识别方案总结：被选特征 + 建议规则形态。"""

    selected: list[SelectedFeature]
    n_total_features: int = 0      # 初筛前总特征数
    n_usable_features: int = 0     # 剔除 NaN/常量后可用数
    usable_rate: float = 0.0       # 特征有效率（≥80% 目标）
    proposed_schema_version: str = "v0"
    note: str = ""


class FeatureSelector:
    """从特征矩阵 + 标签中选出可解释的高区分特征，并产出有效性自评。"""

    def __init__(self, top_k_threshold: float = 0.95,
                 min_coverage: float = 0.05,
                 max_string_features: int = 30) -> None:
        """Args:
            top_k_threshold: 数值通道保留累计增益占比达该值的特征。
            min_coverage:     特征在样本中的最小覆盖率下限。
            max_string_features: 字符串特征输出上限（防指纹特征过多）。
        """
        self.top_k_threshold = top_k_threshold
        self.min_coverage = min_coverage
        self.max_string_features = max_string_features

    # ------------------------------------------------------------------ #
    # 对外主入口
    # ------------------------------------------------------------------ #
    def select(self, feature_matrix: pd.DataFrame, labels: Iterable,
               **_) -> FeatureSummary:
        """特征矩阵(DataFrame) + 标签 → FeatureSummary。

        标签可为 2 类（正/负，对应社交 vs 非社交）。只支持数值/标签对齐的行。
        """
        df = feature_matrix.copy()
        labels = np.asarray(labels)
        if len(labels) != len(df):
            raise ValueError("labels 长度与 feature_matrix 行数不一致")
        df["__label__"] = labels

        # 剔除绝对时间戳等伪特征（数据泄漏防护）
        drop_time = _NON_ANALYTIC & set(df.columns)
        if drop_time:
            df = df.drop(columns=list(drop_time))

        # 剔除常量列与全 NaN 列（特征有效率口径）
        df, dropped = self._drop_useless(df)
        n_total = df.shape[1] - 1  # 减去 __label__
        usable = max(0, n_total - len(dropped))
        usable_rate = (usable / n_total * 100.0) if n_total else 0.0

        string_cols = [c for c in df.columns
                       if c != "__label__" and df[c].dtype == object]
        num_cols = [c for c in df.columns
                    if c != "__label__" and df[c].dtype != object]

        selected: list[SelectedFeature] = []

        # 通道 A：字符串/指纹特征（直接可规则化）
        selected.extend(self._analyze_string_features(df, string_cols))

        # 通道 B：数值统计特征（单变量初筛 + 树模型复核）
        selected.extend(self._analyze_numeric_features(df, num_cols))

        # 有效性自评：top 特征在简单阈值/单特征上的会话级准确率
        note = self._self_assess(df, selected)

        return FeatureSummary(
            selected=selected,
            n_total_features=n_total,
            n_usable_features=usable,
            usable_rate=usable_rate,
            proposed_schema_version="v0",
            note=note,
        )

    # ------------------------------------------------------------------ #
    # 预处理
    # ------------------------------------------------------------------ #
    def _drop_useless(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
        """剔除：(1) 全 NaN 列 (2) 常量列（唯一值 ≤ 1，除 __label__ 外）。"""
        dropped: list[str] = []
        keep = []
        for c in df.columns:
            if c == "__label__":
                keep.append(c)
                continue
            n_unique = df[c].nunique(dropna=False)
            if n_unique <= 1 or df[c].isna().all():
                dropped.append(c)
            else:
                keep.append(c)
        return df[keep], dropped

    # ------------------------------------------------------------------ #
    # 通道 A：字符串/指纹特征
    # ------------------------------------------------------------------ #
    def _analyze_string_features(self, df: pd.DataFrame, string_cols) -> list[SelectedFeature]:
        """对字符串特征做类内覆盖率分析，产出可规则化候选。

        对每个 (特征, 取值)，计算该取值内各标签占比。若某个取值在某类中
        高占比（如 SNI='b-api.facebook.com' 在 facebook 中占 60%），
        则是很好的『正类命中断言』规则特征。
        """
        result: list[SelectedFeature] = []
        n = len(df)

        for col in string_cols:
            cov = df[col].notna().mean()
            if cov < self.min_coverage:
                continue
            for val, val_df in df[[col, "__label__"]].dropna().groupby(col):
                label_counts = val_df["__label__"].value_counts()
                total = label_counts.sum()
                global_share = total / n     # 该取值在全体样本中的占比
                for lab, cnt in label_counts.items():
                    share_in_val = cnt / total   # 该取值内此类的占比
                    score = share_in_val * global_share
                    if share_in_val >= 0.8 and global_share >= self.min_coverage:
                        result.append(SelectedFeature(
                            name=col, score=round(score, 4),
                            rationale=f"{col}={val!r} 在『{lab}』中占 {share_in_val*100:.0f}%"
                                      f"（总体覆盖 {global_share*100:.0f}%），可作高置信断言规则",
                            kind="string",
                            direction=f"== '{val}'",
                            coverage=round(global_share, 3),
                        ))
            # 排序去重，保留最强的前 max_string_features 个
            result.sort(key=lambda s: s.score, reverse=True)
            result = result[:self.max_string_features]

        return result

    # ------------------------------------------------------------------ #
    # 通道 B：数值统计特征
    # ------------------------------------------------------------------ #
    def _analyze_numeric_features(self, df: pd.DataFrame, num_cols) -> list[SelectedFeature]:
        """单变量信息增益初筛 + XGBoost 特征增益复核。"""
        if not num_cols:
            return []
        X = df[num_cols].astype(float).fillna(df[num_cols].astype(float).mean())
        y = df["__label__"].astype(int)

        imp = self._rank_features(X, y)

        # 累计增益截断：保留至 top_k_threshold
        ordered = sorted(imp, key=lambda kv: kv[1], reverse=True)
        total = sum(v for _, v in ordered) if ordered else 0
        selected: list[SelectedFeature] = []
        acc = 0.0
        for name, v in ordered:
            acc += v
            ratio = v / total if total else 0.0
            coverage = 1.0 - df[name].isna().mean()
            selected.append(SelectedFeature(
                name=name, score=round(ratio, 4),
                rationale=self._auto_rationale(name, ratio, coverage),
                kind="numeric",
                coverage=round(coverage, 3),
            ))
            if acc >= self.top_k_threshold * total:
                break
        return selected

    # ------------------------------------------------------------------ #
    # 数值评分内核
    # ------------------------------------------------------------------ #
    def _univariate_scores(self, X, y) -> pd.Series:
        """单变量信息增益（快筛，可解释）。"""
        from sklearn.feature_selection import mutual_info_classif
        mi = mutual_info_classif(X.values, y.values, random_state=0)
        return pd.Series(mi, index=X.columns)

    def _tree_gain(self, X, y) -> pd.Series:
        """XGBoost 特征增益重要性（复核）。"""
        import xgboost as xgb
        clf = xgb.XGBClassifier(
            n_estimators=60, max_depth=4, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, random_state=0,
            eval_metric="logloss", tree_method="hist", n_jobs=-1,
        )
        clf.fit(X.astype(float).values, y.values)
        return pd.Series(clf.feature_importances_, index=X.columns)

    def _rank_features(self, X, y) -> list[tuple[str, float]]:
        """综合 信息增益 + 树增益 → 归一化总分。"""
        mi = self._univariate_scores(X, y)
        gain = self._tree_gain(X, y)

        def _norm(s: pd.Series) -> pd.Series:
            m = s.max()
            if m == 0 or m != m:
                return s * 0.0
            return s / m

        score = _norm(mi.fillna(0)) + _norm(gain.fillna(0))
        return list(zip(X.columns, score.values))

    def _auto_rationale(self, name: str, ratio: float, coverage: float) -> str:
        """为数值特征生成可解释说明。"""
        hints = {
            "tls_sni": "TLS SNI 域名，握手即得，可解释强",
            "ja3_hash": "JA3 客户端握手指纹，标识客户端库/版本",
            "ja3s_hash": "JA3S 服务端指纹，标识服务器能力",
            "tls_alpn": "ALPN 协商协议(h2/http1.1)可观察",
            "tls_cipher_suite": "TLS 密码套件协商",
            "total_packets": "流内包总数",
            "total_bytes": "流内总字节数",
            "bytes_ratio": "上下行字节比（应用交互特征）",
            "packets_ratio": "上下行包数比",
            "duration": "会话持续时间",
            "iat": "包到达间隔时序节奏",
            "pkt_len": "包长分布（MTU/应用块大小）",
            "burst": "突发传输节奏",
            "payload_len": "L7 载荷长度分布",
        }
        for k, v in hints.items():
            if k in name:
                return f"{name}（{v}）区分度占比 {ratio*100:.1f}%，覆盖率 {coverage*100:.0f}%"
        return f"{name} 区分度占比 {ratio*100:.1f}%，覆盖率 {coverage*100:.0f}%"

    # ------------------------------------------------------------------ #
    # 有效性自评
    # ------------------------------------------------------------------ #
    def _self_assess(self, df: pd.DataFrame, selected) -> str:
        """用被选特征训练简单分类器，报告会话级准确率（快速自检）。

        这不是最终测评（最终在任务二 · 引擎上做），只是 1.4 自检：
        确认选出的特征确实携带区分信息。
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.metrics import accuracy_score
            from sklearn.model_selection import train_test_split
        except Exception:
            return "（sklearn 不可用，跳过自评）"

        num_feats = [s.name for s in selected if s.kind == "numeric"
                     and s.name in df.columns]
        if not num_feats:
            return "仅产出指纹/字符串特征，未做数值自评（见规则通道 A）"

        X = df[num_feats].astype(float).fillna(0.0).values
        y = df["__label__"].astype(int).values
        if len(np.unique(y)) < 2:
            return "单标签样本，跳过分类自评"

        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                              random_state=0, stratify=y)
        rf = RandomForestClassifier(n_estimators=100, random_state=0, n_jobs=-1)
        rf.fit(Xtr, ytr)
        acc = accuracy_score(yte, rf.predict(Xte))
        return (f"自评：top数值特征 {len(num_feats)} 个，"
                f"随机森林会话级准确率 {acc*100:.1f}%"
                f"（最终指标以任务二 DPI 引擎为准）")


# 便捷函数：直接读 CSV + 标签 → FeatureSummary
def analyze_csv(features_csv: str, label_col: str = "app",
                target_class: str = "facebook") -> FeatureSummary:
    """从特征 CSV 读入，按二元标签(目标类 vs 其余)做特征选择。"""
    df = pd.read_csv(features_csv)
    y = (df[label_col] == target_class).astype(int)
    # 丢弃纯标识列（不参与特征学习）
    drop = {c for c in df.columns
            if c in ("pcap", "app", "src_ip", "dst_ip", "start_time", "end_time")}
    X = df.drop(columns=list(drop))
    return FeatureSelector().select(X, y)
