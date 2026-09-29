"""特征矩阵质量摸底：NaN/常量占比 → 特征有效率，预判任务一 1.4 指标。

对 joyfuljay 产出的特征 CSV 做体检：
- 行/列规模、列按特征组前缀分布
- 特征有效率 = 非全 NaN 且非常量列占比（目标 ≥ 80%）
- 每组的 NaN 比例
- 非数值列（字符串：IP/SNI/JA3 等）清单与覆盖率

用法：
    .venv/bin/python scripts/assess_features.py <features.csv> [<features.csv>...]
"""
import sys

import pandas as pd


def assess(path: str) -> None:
    df = pd.read_csv(path)
    n_rows, n_cols = df.shape
    print(f"\n===== {path}")
    print(f"    规模: {n_rows} 行 × {n_cols} 列")

    # 按前缀分组计数（提取器组：flow_meta/timing/size/tcp/tls 等）
    groups: dict[str, int] = {}
    for c in df.columns:
        g = c.split(".")[0]
        groups[g] = groups.get(g, 0) + 1
    print("    列前缀分布:", {k: v for k, v in sorted(groups.items())})

    # 全 NaN 列
    all_nan = [c for c in df.columns if df[c].isna().all()]
    print(f"    全 NaN 列: {len(all_nan)}  {all_nan[:12]}")

    # 常量列（唯一值 <= 1）
    def _nunique(c: str) -> int:
        return df[c].nunique(dropna=False)

    const_cols = [c for c in df.columns if _nunique(c) <= 1]
    print(f"    常量列(唯一值<=1): {len(const_cols)}  {const_cols[:12]}")

    # 有效率：非全NaN 且非常量 的列占比
    usable = [c for c in df.columns if not df[c].isna().all() and _nunique(c) > 1]
    rate = len(usable) / n_cols * 100 if n_cols else 0.0
    print(f"    特征有效率(非NaN且非常量): {rate:.1f}%   ({len(usable)}/{n_cols})  ← 目标 ≥80%")

    # 每列 NaN 比例分布（数值列）
    num_cols = df.select_dtypes(include="number").columns
    nan_rate = df[num_cols].isna().mean()
    if len(nan_rate):
        print(f"    数值列平均 NaN 率: {nan_rate.mean() * 100:.1f}%  "
              f"最高: {nan_rate.max() * 100:.1f}% ({nan_rate.idxmax()})")

    # 字符串列（非数值）与覆盖率
    obj_cols = df.select_dtypes(include="object").columns
    print(f"    字符串列: {len(obj_cols)}")
    for c in obj_cols[:25]:
        n_non_nan = df[c].notna().sum()
        uniq = df[c].dropna().nunique()
        sample = df[c].dropna().unique()[:3]
        print(f"      {c:28s} 覆盖 {n_non_nan/n_rows*100:5.1f}%  唯一值 {uniq:4d}  样例 {sample!r}")

    # tls 指纹特征专项（加密流量核心）
    tls_cols = [c for c in df.columns if c.startswith("tls.")]
    if tls_cols:
        print(f"    TLS 组 ({len(tls_cols)} 列) 覆盖率:")
        for c in tls_cols:
            cov = df[c].notna().mean() * 100
            print(f"      {c:32s} {cov:5.1f}%")
        if "tls.ja3_hash" in df.columns:
            print(f"    JA3 样本: {df['tls.ja3_hash'].dropna().unique()[:3].tolist()}")
        if "tls.sni" in df.columns:
            print(f"    SNI 样本: {df['tls.sni'].dropna().unique()[:8].tolist()}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for p in sys.argv[1:]:
        assess(p)


if __name__ == "__main__":
    main()
