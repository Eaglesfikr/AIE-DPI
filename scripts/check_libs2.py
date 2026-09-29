"""检查 WSL venv 关键依赖（闭环需要 numpy/pandas/scipy/yaml/sklearn）。"""
import importlib

pkgs = ["numpy", "pandas", "scipy", "yaml", "sklearn"]
for name in pkgs:
    try:
        m = importlib.import_module(name)
        print(f"{name:12s} OK  {getattr(m, '__version__', '?')}")
    except Exception as e:
        print(f"{name:12s} MISSING  ({e})")
