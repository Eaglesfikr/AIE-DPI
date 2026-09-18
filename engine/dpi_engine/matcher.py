"""分层匹配器骨架（阶段 1 实现）。

匹配策略：低代价规则优先评估，命中即短路（stop on first match）。
代价低 → 不需要复杂计算的字段（首包/端口/方向比），
代价高 → 流级统计/时序特征（需要收满整个会话或窗口）。

阶段 1 实现：根据 loader 排序后的规则集，对每个会话/流做匹配，
并在 engine/cmd 对检测结果跑指标（precision/recall/fpr）。
"""


class RuleMatcher:
    def __init__(self, compiled_rules):
        """compiled_rules: RuleLoader.load 的输出（阶段 1 定结构）。"""
        self._rules = compiled_rules

    def match(self, session) -> dict | None:
        """对单个会话做匹配，返回命中规则的 conclusion；未命中返回 None。

        阶段 1 实现：按 cost/priority 遍历规则，计算所需特征并短路。
        """
        raise NotImplementedError("阶段 1 实现：分层匹配逻辑")
