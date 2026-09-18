"""引擎 CLI 骨架（阶段 1 实现）。

用法（见 README）：
    python -m engine.dpi_engine.cli --rules rules/social.yaml --input <pcap或会话JSON>

阶段 1 实现：加载规则 → 对输入流做会话重组（复用 src/feature_miner.parser）
或读入现成会话特征 → matcher 匹配 → 输出 DetectionResult 列表。
"""

import argparse


def main():
    ap = argparse.ArgumentParser(description="高效 DPI 规则识别引擎 CLI")
    ap.add_argument("--rules", required=True, help="规则文件 (rules/*.yaml)")
    ap.add_argument("--input", required=True, help="输入 pcap / 会话特征 JSON / 目录")
    ap.add_argument("--format", default="auto",
                    choices=["auto", "pcap", "json"], help="输入格式")
    args = ap.parse_args()

    # 阶段 1 实现：loader.load(args.rules) -> matcher -> 结果输出
    raise NotImplementedError("阶段 1 实现：CLI 组装")
