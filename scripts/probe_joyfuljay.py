"""确认 WSL venv 中 'joyfuljay' 包的身份与可用接口（探查用，非交付代码）。

打印：模块位置、版本、公开函数/类签名、是否有 pcap→特征 的入口。
用法：
    .venv/bin/python scripts/probe_joyfuljay.py
"""
import inspect
import importlib.util
import sys

NAME = "joyfuljay"

spec = importlib.util.find_spec(NAME)
if spec is None:
    print(f"!! 无法 import '{NAME}'（未安装或名称不对）")
    sys.exit(1)

print(f"== 模块位置: {spec.origin}")
mod = importlib.import_module(NAME)

for attr in ("__version__", "__file__"):
    try:
        print(f"   {attr} = {getattr(mod, attr)}")
    except Exception as e:
        print(f"   {attr} = <无> ({e})")

print("\n== 顶层公开成员:")
names = [n for n in dir(mod) if not n.startswith("_")]
for n in names:
    obj = getattr(mod, n)
    if inspect.isfunction(obj) or inspect.isclass(obj):
        try:
            sig = inspect.signature(obj)
            print(f"  {n}{sig}   [{type(obj).__name__}]")
        except (ValueError, TypeError):
            print(f"  {n}  [{type(obj).__name__}]")
    else:
        print(f"  {n} = {type(obj).__name__}")

print("\n== 子模块/子包:")
if hasattr(mod, "__path__"):
    for n in dir(mod):
        sub = getattr(mod, n)
        if hasattr(sub, "__path__") and not n.startswith("_"):
            try:
                print(f"   subpkg: {NAME}.{n} -> {sub.__path__}")
            except Exception:
                pass

print("\n== 帮助文档（前 60 行）:")
try:
    doc = inspect.getdoc(mod) or "(无模块级 docstring)"
    print("\n".join(doc.splitlines()[:60]))
except Exception as e:
    print("  (无法取 doc)", e)
