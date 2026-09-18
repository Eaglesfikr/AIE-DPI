"""特征选择与有效性分析骨架（阶段 1 实现）。

目标（对应赛题指标）：小样本上快速给出可解释的候选特征维度清单与
识别方案；特征有效率 ≥ 80%。

阶段 1 计划：
- 信息增益 / 单变量 AUC 初筛（快、可解释）→ SHAP 补强；
- 输出"候选特征清单 + 可行识别方案"结构对象，供 rule_gen 消费。
"""

from dataclasses import dataclass


@dataclass
class SelectedFeature:
    name: str
    score: float
    rationale: str  # 可解释依据（供规则 schema 使用）


@dataclass
class FeatureSummary:
    """识别方案总结：被选特征 + 建议规则形态。"""

    selected: list[SelectedFeature]
    proposed_schema_version: str  # 规则文件 schema 版本


class FeatureSelector:
    def select(self, feature_matrix, labels) -> FeatureSummary:
        """特征矩阵(DataFrame) + 标签 → FeatureSummary。

        阶段 1 实现：重要性排序 + 有效性自评（有效率 ≥ 80%）。
        """
        raise NotImplementedError("阶段 1 实现：特征选择与分析")
