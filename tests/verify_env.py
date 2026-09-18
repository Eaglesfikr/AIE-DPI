"""环境验证脚本：导入依赖 + 跑会话骨架单测。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

mods = ["scapy", "numpy", "pandas", "sklearn", "xgboost", "yaml"]
for m in mods:
    mod = __import__(m)
    print(f"import {m}: ok ({getattr(mod, '__version__', 'n/a')})")

import unittest

suite = unittest.defaultTestLoader.discover(start_dir=Path(__file__).parent)
res = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if res.wasSuccessful() else 1)
