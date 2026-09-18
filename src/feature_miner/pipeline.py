"""数据 pipeline 骨架（阶段 1 实现各步骤）。

流程：PCAP → 会话重组 → 基础特征 → 高级特征 → 特征 CSV 入库。

用法（见 README）：
    python -m src.feature_miner.pipeline --input data/raw --output data/processed

阶段 1 实现：
  parser.reassemble 产出 Session 列表，
  features 计算 FeatureStore，
  结果写 data/processed/<name>_features.csv + <name>_sessions.json。
"""

import argparse


def parse_args():
    ap = argparse.ArgumentParser(description="PCAP → 会话重组 → 特征提取 pipeline")
    ap.add_argument("--input", required=True, help="PCAP 目录或文件")
    ap.add_argument("--output", required=True, help="结果输出目录 (data/processed)")
    return ap.parse_args()


def run(input_path: str, output_path: str) -> None:
    # 阶段 1 实现组装各模块
    # 1) PcapReader.read_packets  → 2) reassemble → 3) features → 4) 落盘 CSV/JSON
    raise NotImplementedError("阶段 1 实现：组装解析→特征→落盘")


if __name__ == "__main__":
    args = parse_args()
    run(args.input, args.output)
