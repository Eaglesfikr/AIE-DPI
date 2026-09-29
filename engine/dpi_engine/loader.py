"""规则文件加载与编译（阶段 1 已实现，对应 TODO 2.1）。

把 YAML 规则文件编译为引擎内部的 CompiledRule + 分层索引：
- 校验 schema（schema_version / rules / conditions / conclusion / op 合法）
- 按 cost 分组建索引（low/mid/high），组内按 priority 升序 —— 供 matcher 分层短路。

schema v0（与 src/feature_miner.rule_gen.generator 输出一致）：
    conditions: [{feature, op, value}]   # AND 语义
    op ∈ {in, eq, neq, gte, lte, gt, lt, range}
    in / eq 对字符串按 == 比较；value 中 ``*.`` 前缀表示后缀匹配（SNI 通配习惯）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

VALID_OPS = {"in", "eq", "neq", "gte", "lte", "gt", "lt", "range"}
COST_ORDER = {"low": 0, "mid": 1, "high": 2}
SUPPORTED_SCHEMA = "v0"


@dataclass
class CompiledCondition:
    """单条已编译条件：给定特征值 → bool。"""

    feature: str
    op: str
    value: object

    def match(self, features: dict) -> bool:
        """评估一条条件。features: 特征名 → 值 的字典。"""
        if self.feature not in features:
            return False  # 缺特征 → 条件不成立（不命中）
        val = features.get(self.feature)
        op = self.op
        if op in ("eq", "in"):
            return self._match_in(val)
        if op == "neq":
            return not self._match_in(val)
        try:
            v = float(val)
        except (TypeError, ValueError):
            return False  # 非数值特征对数值 op → 不命中
        v = float(val)
        if op == "gte":
            return v >= self.value
        if op == "lte":
            return v <= self.value
        if op == "gt":
            return v > self.value
        if op == "lt":
            return v < self.value
        if op == "range":
            lo, hi = self.value
            return lo <= v <= hi
        return False

    def _match_in(self, val) -> bool:
        """in/eq 语义：支持 exact 与 ``*.`` 后缀通配。"""
        candidates = self.value if isinstance(self.value, list) else [self.value]
        s = str(val)
        for c in candidates:
            c = str(c)
            if c.startswith("*."):
                if s.endswith(c[1:]):
                    return True
            elif s == c:
                return True
        return False


@dataclass
class CompiledRule:
    """一条已编译规则。"""

    rule_id: str
    priority: int
    cost: str
    conditions: list[CompiledCondition] = field(default_factory=list)
    conclusion: dict = field(default_factory=dict)

    def match(self, features: dict) -> bool:
        """全部条件成立才算命中（AND）。"""
        return all(c.match(features) for c in self.conditions)


class RuleLoader:
    """加载 YAML 规则文件 → 分层编译结构。"""

    def __init__(self, schema_version: str = "v0") -> None:
        self.schema_version = schema_version

    def load(self, path: str | Path) -> dict:
        """读取 + 校验 + 编译。返回分层索引 dict：
            {
              "schema_version": str,
              "target": str,
              "by_cost": { "low": [CompiledRule...], "mid": [...], "high": [...] },
              "all": [CompiledRule...],   # 按 (priority, cost) 全排序
            }
        """
        doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if doc.get("schema_version") != SUPPORTED_SCHEMA:
            raise ValueError(
                f"不支持的 schema_version={doc.get('schema_version')!r}，"
                f"期望 {SUPPORTED_SCHEMA}")
        raw_rules = doc.get("rules")
        if not isinstance(raw_rules, list) or not raw_rules:
            raise ValueError("rules 为空或缺失")

        by_cost = {k: [] for k in COST_ORDER}
        all_rules: list[CompiledRule] = []
        for raw in raw_rules:
            rule = self._compile_rule(raw)
            by_cost[rule.cost].append(rule)
            all_rules.append(rule)

        # 组内按 (priority) 升序，保证低 priority 先评估
        for k in by_cost:
            by_cost[k].sort(key=lambda r: r.priority)
        all_rules.sort(key=lambda r: (COST_ORDER[r.cost], r.priority))

        return {
            "schema_version": doc.get("schema_version"),
            "target": doc.get("target"),
            "description": doc.get("description", ""),
            "by_cost": by_cost,
            "all": all_rules,
        }

    def _compile_rule(self, raw: dict) -> CompiledRule:
        rule_id = raw.get("rule_id")
        conclusion = raw.get("conclusion")
        conds_raw = raw.get("conditions")
        if not rule_id or not conclusion or not conds_raw:
            raise ValueError(f"规则缺少 rule_id/conclusion/conditions: {raw}")

        cost = raw.get("cost", "mid")
        if cost not in COST_ORDER:
            raise ValueError(f"rule {rule_id}: 非法 cost={cost!r}")

        conds: list[CompiledCondition] = []
        for c in conds_raw:
            op = c.get("op")
            if op not in VALID_OPS:
                raise ValueError(f"rule {rule_id}: 非法 op={op!r}")
            if "feature" not in c or "value" not in c:
                raise ValueError(f"rule {rule_id}: condition 缺少 feature/value")
            conds.append(CompiledCondition(
                feature=c["feature"], op=op, value=c["value"]))
        if not conds:
            raise ValueError(f"rule {rule_id}: conditions 为空")

        return CompiledRule(
            rule_id=rule_id,
            priority=int(raw.get("priority", 100)),
            cost=cost,
            conditions=conds,
            conclusion=conclusion,
        )
