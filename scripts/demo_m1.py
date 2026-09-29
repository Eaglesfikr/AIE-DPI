"""M1 演示：读取 PCAP → 会话重组 → 打印统计。

用法（WSL，在项目根目录）：
    .venv/bin/python scripts/demo_m1.py <pcap文件> [--out data/processed/sessions.json]
    .venv/bin/python scripts/demo_m1.py /mnt/d/Datasets/MPAF-dataset-pcap/Automatic/facebook/facebook-10.pcapng
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.feature_miner.parser.pcap_reader import PcapReader
from src.feature_miner.parser.reassembler import reassemble


def main() -> None:
    ap = argparse.ArgumentParser(description="M1 解析+会话重组演示")
    ap.add_argument("pcap", help="pcap/pcapng 文件路径")
    ap.add_argument("--out", default=None, help="会话 JSON 输出路径（默认仅打印统计）")
    args = ap.parse_args()

    print(f"== 读取 {args.pcap}")
    rd = PcapReader()
    packets = rd.read_all(args.pcap)
    print(f"包数: {len(packets)}")

    sessions = reassemble(packets)
    print(f"重组会话数: {len(sessions)}")

    by_proto = Counter(s.proto for s in sessions)
    print("按协议:", dict(by_proto))
    print("前8个会话:")
    for s in sessions[:8]:
        print(f"  {s.session_id[:44]}  pkt={len(s.packets)}  dur={s.duration_us}us  f5={s.five_tuple[:2]}")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps([s.to_dict() for s in sessions], indent=1, ensure_ascii=False))
        print(f"已写入 {out}")


if __name__ == "__main__":
    main()
