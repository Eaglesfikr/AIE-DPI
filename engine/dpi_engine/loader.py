"""规则文件加载与校验骨架（阶段 1 实现）。

把 YAML 规则编译为内部匹配结构（matcher 用），并做 schema 校验。
"""


class RuleLoader:
    def __init__(self, schema_version: str = "v0") -> None:
        self.schema_version = schema_version

    def load(self, path: str):
        """加载规则文件 → 编译后的规则集合。

        阶段 1 实现：PyYAML 读取 + 校验 + 按 cost/priority 排好序的结构。
        """
        raise NotImplementedError("阶段 1 实现：规则加载与校验")
