"""检查 venv 中对 1.4 特征分析可用的库（避免 shell 引号问题）。"""
import importlib.util

LIBS = [
    "numpy", "pandas", "scipy", "sklearn", "xgboost",
    "shap", "scapy", "yaml", "matplotlib", "seaborn",
]

for name in LIBS:
    spec = importlib.util.find_spec(name)
    if spec is None:
        print(f"  {name:12s} MISSING")
        continue
    try:
        mod = importlib.import_module(name)
        ver = getattr(mod, "__version__", "?")
    except Exception as e:
        ver = f"(import err: {e})"
    print(f"  {name:12s} OK       v{ver}")
