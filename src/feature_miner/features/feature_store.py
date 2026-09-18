"""特征存储与命名规范。

命名规则：维度_子维度_统计（例：flow.pkt_len.mean、tls.ja3）。
阶段 1 将添加：base.py（流统计/流段统计/时序行为）与
advanced.py（包长序列、burst、周期、关联特征）。
"""

from dataclasses import dataclass, field


@dataclass
class FeatureStore:
    """会话级特征字典。"""

    values: dict[str, float | str] = field(default_factory=dict)

    def set(self, name: str, value: float | str) -> None:
        self.values[name] = value

    def get(self, name: str, default=None):
        return self.values.get(name, default)

    def names(self) -> list[str]:
        return list(self.values.keys())

    def to_dict(self) -> dict:
        return dict(self.values)
