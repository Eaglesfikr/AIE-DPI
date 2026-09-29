"""深度探查 joyfuljay 的特征体系（枚举、profile、提取器、可用特征名）。

用法：
    .venv/bin/python scripts/probe_joyfuljay2.py
"""
import inspect

import joyfuljay as jj


def dump_enum(name: str, enum, max_items: int = 200) -> None:
    print(f"== {name}:")
    vals = list(enum)
    for v in vals[:max_items]:
        print(f"   {v.name} = {v.value!r}")
    if len(vals) > max_items:
        print(f"   ... 共 {len(vals)} 项")


dump_enum("FeatureGroup", jj.FeatureGroup)

# 找 ProfileType
for mod_name, mod in [("core", jj.core), ("annotations", jj.annotations)]:
    for n in dir(mod):
        if "Profile" in n or "profile" in n:
            obj = getattr(mod, n)
            if inspect.isclass(obj):
                try:
                    members = getattr(obj, "__members__", None)
                    if members:
                        print(f"\n== {mod_name}.{n} (枚举):")
                        for k, v in members.items():
                            print(f"   {k} = {v.value!r}")
                except Exception:
                    pass
                else:
                    pass
            print(f"   ({mod_name}.{n} = {type(obj).__name__})")

# extractors 子模块里的类
print("\n== joyfuljay.extractors 成员:")
for n in dir(jj.extractors):
    if n.startswith("_"):
        continue
    obj = getattr(jj.extractors, n)
    if inspect.isclass(obj):
        print(f"   class {n}: {obj.__doc__ and obj.__doc__.splitlines()[0] or ''}")
    elif inspect.ismodule(obj):
        print(f"   module {n}")

# annotations 里的 _Feature 结构：看有哪些 feature 常量
print("\n== joyfuljay.annotations 公开成员:")
for n in dir(jj.annotations):
    if n.startswith("_"):
        continue
    obj = getattr(jj.annotations, n)
    if inspect.isclass(obj):
        doc = (obj.__doc__ or "").splitlines()
        print(f"   class {n}{str(inspect.signature(obj)) if len(doc) > 1 else ''}")
    elif isinstance(obj, str):
        print(f"   {n} = {obj!r}")
    else:
        print(f"   {n} = {type(obj).__name__}")
