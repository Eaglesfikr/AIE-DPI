"""冒烟测试：对最小的 pcap 跑一次 joyfuljay.extract()，确认输出结构。

用法：
    .venv/bin/python scripts/smoke_extract.py [--pcap <path>] [--save features/smoke.csv]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joyfuljay as jj


def main() -> None:
    ap = argparse.ArgumentParser(description="joyfuljay 冒烟提取测试")
    ap.add_argument("--pcap", default=Path("data/twitter/twitter-09.pcapng").as_posix())
    ap.add_argument("--save", default=None, help="输出 CSV 路径")
    ap.add_argument("--nrows", type=int, default=5)
    args = ap.parse_args()

    print(f"== 提取 {args.pcap} ...")
    df = jj.extract(args.pcap)  # 默认配置
    print(f"== 返回类型: {type(df)}")
    print(f"== 形状: {df.shape}")
    if hasattr(df, "columns"):
        cols = list(df.columns)
        print(f"== 列数: {len(cols)}")
        print("== 前 40 列:")
        for c in cols[:40]:
            print(f"   {c}")
        if len(cols) > 40:
            print(f"   ... 其余 {len(cols) - 40} 列")
        print("\n== 前 5 行（转置预览）:")
        with pd_option():
            print(df.head(args.nrows).T.to_string()[:6000])
        if args.save:
            out = Path(args.save)
            out.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(out, index=False)
            print(f"\n已写入 {out}")
    elif isinstance(df, list):
        print(f"== list of {len(df)} dicts, 第一个的 keys:")
        if df:
            keys = list(df[0].keys())
            print(f"   {len(keys)} keys: {keys[:40]}")
            if args.save:
                import csv
                out = Path(args.save)
                out.parent.mkdir(parents=True, exist_ok=True)
                with out.open("w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=keys)
                    w.writeheader()
                    for row in df:
                        w.writerow(row)
                print(f"已写入 {out}")


def pd_option():
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        import pandas as pd

        old = pd.option_context("display.max_columns", 60, "display.width", 200)
        with old:
            yield

    return _ctx()


if __name__ == "__main__":
    main()
