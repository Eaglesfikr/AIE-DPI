"""规则文件生成器（阶段 1 已实现，对应 TODO 1.5）。

规则文件是挖掘工具与 DPI 引擎的**接口契约**，必须：
- 可解释、成体系、逻辑严谨；
- 引擎可直接加载、低代价匹配；
- 结构为 YAML schema v0（便于人工修正：赛题要求『人工修正后可用率 ≥ 90%』）。

schema v0 结构（rules/ 下每场景一个文件，如 rules/social.yaml）：

    schema_version: v0
    target: social_classification
    description: ...
    rules:
      - rule_id: r001
        priority: 10            # 数值小 = 越优先评估（低代价规则在前）
        cost: low               # low(握手/首包) | mid(流统计) | high(时序/长窗口)
        conditions:             # AND 语义：全部满足才命中
          - feature: tls_sni
            op: in
            value: [www.facebook.com, "*.facebook.com"]
        conclusion: { app: facebook, confidence: 0.95 }

支持的 op：in / eq / neq / gte / lte / gt / lt / range。
in 与 eq 对字符串做==比较；值中 `*.` 前缀表示后缀匹配（SNI 通配习惯）。
"""  # noqa: E501

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

# 支持的比较操作符
VALID_OPS = {"in", "eq", "neq", "gte", "lte", "gt", "lt", "range"}

# 代价档位语义（引擎按此分组建索引，低代价优先）
COST_ORDER = {"low": 0, "mid": 1, "high": 2}


@dataclass
class RuleModel:
    """单条规则：条件（AND）→ 结论。"""

    rule_id: str
    conclusion: dict                # 识别结果 {app / behavior / confidence}
    conditions: list[dict] = field(default_factory=list)   # [{feature, op, value}]
    priority: int = 100             # 低数字 = 更高优先级（先评估）
    cost: str = "mid"               # low | mid | high

    def validate(self) -> None:
        """校验规则结构合法性（生成时即兜底，引擎 loader 再验一遍）。"""
        if self.cost not in COST_ORDER:
            raise ValueError(f"rule {self.rule_id}: 非法 cost={self.cost!r}")
        if not self.conditions:
            raise ValueError(f"rule {self.rule_id}: conditions 为空")
        for c in self.conditions:
            op = c.get("op")
            if op not in VALID_OPS:
                raise ValueError(f"rule {self.rule_id}: 非法 op={op!r}")
            if "feature" not in c or "value" not in c:
                raise ValueError(f"rule {self.rule_id}: condition 缺少 feature/value")


class RuleGenerator:
    """把 RuleModel 列表组装为规则文件 dict，并序列化为 YAML。"""

    def __init__(self, schema_version: str = "v0") -> None:
        self.schema_version = schema_version

    def build(self, rules: list[RuleModel], target: str = "social_classification",
              description: str = "", sort: bool = True) -> dict:
        """RuleModel 列表 → 规则文件 dict。

        Args:
            rules: 规则列表（可无序，build 会按 priority 升序排好）。
            target: 场景标识（如 social_classification）。
            description: 规则文件说明（人工可读，进 YAML 顶层）。
            sort: 按 (priority, cost) 升序排序，保证引擎按最优序评估。
        """
        for r in rules:
            r.validate()
        ordered = sorted(rules, key=lambda r: (r.priority, COST_ORDER[r.cost]))
        return {
            "schema_version": self.schema_version,
            "target": target,
            "description": description,
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "priority": r.priority,
                    "cost": r.cost,
                    "conditions": [dict(c) for c in r.conditions],
                    "conclusion": dict(r.conclusion),
                }
                for r in ordered
            ],
        }

    def to_yaml(self, rules: dict) -> str:
        """规则文件 dict → YAML 字符串（含生成时间注释）。"""
        import datetime

        header = (
            f"# 规则文件（自动生成 {datetime.date.today().isoformat()}）\n"
            "# 人工可修改：调整 priority/阈值/confidence 后引擎重载即可。\n"
            f"# schema_version: {rules['schema_version']}\n"
        )
        body = yaml.safe_dump(rules, allow_unicode=True, sort_keys=False,
                              default_flow_style=False)
        return header + body

    def dump(self, rules: dict, path: str) -> None:
        """写入 YAML 文件。"""
        from pathlib import Path

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_yaml(rules), encoding="utf-8")
