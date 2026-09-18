"""识别结果与应用类型枚举。"""

from dataclasses import dataclass
from enum import Enum


class AppLabel(str, Enum):
    """应用类型标签（阶段 1 按场景补充更多）。"""

    UNKNOWN = "unknown"
    SOCIAL = "social"
    NON_SOCIAL = "non_social"
    # 阶段 2 扩展：IM 行为、匿名工具等
    ANONYMOUS = "anonymous"


class Behavior(str, Enum):
    UNKNOWN = "unknown"
    # 阶段 2 扩展：voice_call / video_call / text_chat / post_text


@dataclass
class DetectionResult:
    """一条流/会话的识别结论。"""

    session_id: str
    app: AppLabel = AppLabel.UNKNOWN
    behavior: Behavior = Behavior.UNKNOWN
    confidence: float = 0.0
    matched_rule_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "app": self.app.value,
            "behavior": self.behavior.value,
            "confidence": self.confidence,
            "matched_rule_id": self.matched_rule_id,
        }
