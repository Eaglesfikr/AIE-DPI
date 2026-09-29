"""用 joyfuljay 对 MPAF pcapng 做『基础特征』提取，产出 CSV 特征矩阵。

特征组（对应任务一 1.2 基础特征维度，恰好 = joyfuljay 的 CORE profile）：
    flow_meta  基础协议/流统计（包数、字节、时长、方向比、端口）
    timing     时序行为（IAT、burst、节奏）
    size       包长统计（mean/std/fwd/bwd、对称性）
    tcp        协议结构（握手/关闭标志、标志位比例）
    tls        握手指纹（SNI、ALPN、cipher、JA3/JA3S、证书）

用法：
    # 单个 pcap
    .venv/bin/python scripts/extract_features_joyfuljay.py --pcap data/twitter/twitter-09.pcapng
    # 整类应用（默认 facebook）→ data/processed/features_<app>.csv
    .venv/bin/python scripts/extract_features_joyfuljay.py --app facebook [--out data/processed/features_facebook.csv]
    # 自定义特征组
    ... --groups flow_meta timing size tcp tls fingerprint

说明：
- 每个 pcap 一行 = 一个『流(会话)』。本脚本把同 app 所有 pcap 提取的流合并，
  并附 app / pcap 标签列，直接可作为分类特征矩阵。
- 跳过会触发 connection 图特征(需 networkx)的默认 "all"，只提基础组。
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joyfuljay as jj

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PROCESSED_DIR = DATA_DIR / "processed"

BASE_GROUPS = ["flow_meta", "timing", "size", "tcp", "tls"]


def extract_one(pcap_path: Path, groups: list[str]):
    """对单个 pcap 提取特征，返回 DataFrame（每行一个流）。"""
    df = jj.extract(str(pcap_path), output_format="dataframe", features=groups)
    return df


def run_pcap(pcap_path: Path, groups, out: Path | None = None) -> None:
    t0 = time.time()
    print(f"== 提取 {pcap_path.name} ...", flush=True)
    df = extract_one(pcap_path, groups)
    df = df.copy()
    df.insert(0, "pcap", pcap_path.name)
    dt = time.time() - t0
    print(f"   流数 {df.shape[0]:5d}  特征数 {df.shape[1]}  耗时 {dt:.1f}s", flush=True)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
        print(f"   已写入 {out}", flush=True)


def run_app(app: str, groups, out: Path | None = None) -> None:
    app_dir = DATA_DIR / app
    if not app_dir.is_dir():
        print(f"!! 目录不存在: {app_dir}")
        sys.exit(1)
    pcaps = sorted(app_dir.glob("*.pcap*"))
    if not pcaps:
        print(f"!! {app_dir} 下没有 pcap/pcapng")
        sys.exit(1)

    print(f"== 共 {len(pcaps)} 个 pcap，开始按类提取（app={app}）", flush=True)
    parts = []
    t_total = time.time()
    for i, p in enumerate(pcaps, 1):
        t0 = time.time()
        print(f"[{i}/{len(pcaps)}] {p.name} ...", flush=True)
        df = extract_one(p, groups)
        df = df.copy()
        df.insert(0, "pcap", p.name)
        df.insert(1, "app", app)
        parts.append(df)
        print(f"   流数 {df.shape[0]:5d}  耗时 {time.time() - t0:.1f}s", flush=True)

    import pandas as pd

    big = pd.concat(parts, ignore_index=True)
    dt = time.time() - t_total
    print(f"== 合并完成: 总流数 {big.shape[0]}  特征数 {big.shape[1]}  总耗 {dt:.1f}s", flush=True)

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        big.to_csv(out, index=False)
        print(f"== 已写入 {out}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="joyfuljay 基础特征提取")
    ap.add_argument("--pcap", default=None, help="单个 pcap 文件")
    ap.add_argument("--app", default="facebook", help="应用目录名（默认 facebook）")
    ap.add_argument("--out", default=None, help="输出 CSV 路径")
    ap.add_argument("--groups", nargs="*", default=BASE_GROUPS,
                    help=f"特征组（默认: {' '.join(BASE_GROUPS)}）")
    args = ap.parse_args()

    groups = args.groups or BASE_GROUPS

    if args.pcap:
        out = Path(args.out) if args.out else None
        run_pcap(Path(args.pcap), groups, out)
    else:
        out = Path(args.out) if args.out else PROCESSED_DIR / f"features_{args.app}.csv"
        run_app(args.app, groups, out)


if __name__ == "__main__":
    main()
