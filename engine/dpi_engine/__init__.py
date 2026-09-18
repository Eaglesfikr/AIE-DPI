"""高效 DPI 规则识别引擎。

职责：加载挖掘工具的规则文件 → 分层匹配（低代价优先/命中短路）→ 输出识别结果。
识别指标：召回率≥98%、准确率≥95%、精确率≥95%、假阳率≤5%。
"""

from .result import AppLabel, DetectionResult

__version__ = "0.1.0"
__all__ = ["AppLabel", "DetectionResult"]
