"""分层匹配器（阶段 1 已实现，对应 TODO 2.1）。

匹配策略：低代价规则优先评估，命中即短路（stop on first match）。
	分层顺序 low → mid → high：
	- low    : 握手/首包/端口类，立刻可得，最省
	- mid    : 流统计特征（需要短暂观察）
	- high   : 时序/长窗口特征（需要收满会话）
组内按 priority 升序评估。输入统一为"特征字典"（特征名 → 值），
调用方（CLI / pcap 管线）负责把会话/流转成该字典。
"""

from __future__ import annotations

from typing import Any

# 分层评估顺序（loader 的 by_cost 键）
_COST_LAYER_ORDER = ("low", "mid", "high")


class RuleMatcher:
	"""对特征字典做分层匹配。"""

	def __init__(self, compiled: dict) -> None:
		"""
		Args:
			compiled: RuleLoader.load 的输出（含 by_cost 分组）。
		"""
		self._by_cost = compiled["by_cost"]

	def match_features(self, features: dict[str, Any]) -> dict | None:
		"""对单个特征字典匹配，返回命中规则的 conclusion（含 rule_id/cost）；未命中 None。

		低代价优先、组内 priority 升序、命中即短路。
		"""
		for layer in _COST_LAYER_ORDER:
			for rule in self._by_cost[layer]:
				if rule.match(features):
					res = dict(rule.conclusion)
					res["matched_rule_id"] = rule.rule_id
					res["cost"] = rule.cost
					return res
		return None

	def match(self, session: dict[str, Any]) -> dict | None:
		"""兼容接口：session 即特征字典（引擎统一以特征为输入）。"""
		return self.match_features(session)

	def classify(self, features: dict[str, Any]) -> dict:
		"""返回带 UNKNOWN 兜底的完整判定（供上层直接消费）。"""
		hit = self.match_features(features)
		if hit is None:
			return {"app": "unknown", "confidence": 0.0,
					"matched_rule_id": None, "cost": None}
		return hit
