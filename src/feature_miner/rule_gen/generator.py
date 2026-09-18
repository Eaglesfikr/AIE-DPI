"""规则文件生成器骨架（阶段 1 实现）。

规则文件是挖掘工具与 DPI 引擎的**接口契约**，必须：
- 可解释、成体系、逻辑严谨；
- 引擎可直接加载、低代价匹配；
- 结构为 YAML schema（便于人工修正：赛题要求'人工修正后可用率≥90%'）。

schema 版本 v0（阶段 1 定稿，可能演进）：
rules/ 下每场景一个文件，如 rules/social.yaml。
"""

from dataclasses import dataclass


@dataclass
class RuleModel:
    """单条规则：条件 → 结论。阶段 1 细化 schema 字段。"""

    rule_id: str
    priority: int           # 低数字=更高优先级（先评估）
    condition: dict         # 特征 → 比较条件（如 {flow.pkt_len.mean: ">= 900"})
    conclusion: dict        # 识别结果（app / behavior / confidence）
    cost: str = "low"       # 评估代价档位：low | mid | high（分层匹配用）


class RuleGenerator:
    def __init__(self, schema_version: str = "v0") -> None:
        self.schema_version = schema_version

    def build_from_summary(self, summary) -> dict:
        """由 FeatureSummary（analyzer 输出）构造完整规则文件 dict。

        阶段 1 实现：把 selected 特征 + 阈值方案编译为规则条件。
        """
        raise NotImplementedError("阶段 1 实现：规则文件生成")

    def to_yaml(self, rules: dict) -> str:
        """序列化为 YAML 字符串。阶段 1 用 PyYAML 实现。"""
        raise NotImplementedError("阶段 1 实现：YAML 输出")
