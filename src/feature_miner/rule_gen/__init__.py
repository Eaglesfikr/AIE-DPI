"""规则生成层：将识别方案转成 DPI 引擎可加载的规则文件。"""

from .generator import RuleGenerator

__all__ = ["RuleGenerator"]
