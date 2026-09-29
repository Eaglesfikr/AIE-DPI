"""探查特征 CSV：指纹类列的真实列名 + facebook 与其它类在指纹列上的分布对比。"""
import glob

import pandas as pd

KEYWORDS = ("sni", "ja3", "alpn", "fp_hash", "fingerprint")

print("== 各 CSV 中涉嫌指纹/标识的列名 ==")
for f in sorted(glob.glob("data/processed/features_facebook.csv")):
    df = pd.read_csv(f)
    cols = [c for c in df.columns if any(k in c.lower() for k in KEYWORDS)]
    print(f, "->", cols)

print("\n== 全样本在候选指纹列上的取值分布（facebook vs 其他） ==")
files = ["data/processed/features_facebook.csv",
         "data/processed/features_instagram.csv",
         "data/processed/features_twitter.csv"]
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
for col in [c for c in df.columns if any(k in c.lower() for k in KEYWORDS)]:
    non_null = df[col].notna().sum()
    n_fb = int(((df["app"] == "facebook") & df[col].notna()).sum())
    n_ig = int(((df["app"] == "instagram") & df[col].notna()).sum())
    n_tw = int(((df["app"] == "twitter") & df[col].notna()).sum())
    print(f"{col:40s} 非空 {non_null:6d}  fb={n_fb} ig={n_ig} tw={n_tw}")
    for app in ("facebook", "instagram", "twitter"):
        sub = df[df["app"] == app][col].dropna()
        if sub.empty:
            continue
        vc = sub.value_counts()
        top = vc.head(3)
        print(f"    {app:9s} top: {dict(zip(top.index.map(str), top.values))}")
