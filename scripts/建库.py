"""建库脚本骨架：把 raw pcap 批量转成标注 manifest。

输入：data/raw/ 下已按类别/平台整理的 pcap（或抓包后手动分类），
输出：data/labeled/manifest.csv（格式见 docs/数据标注约定.md）。

用法（阶段 1 后）：
    python scripts/建库.py --raw data/raw --out data/labeled

阶段 1 实现：
  1. 遍历 raw 目录结构（app/platform/文件名），提取会话；
  2. 用 pipeline 得到会话区间与五元组，生成 manifest 行；
  3. 可选：按会话切片 pcap 存入 labeled/。
"""

import argparse


def main():
    ap = argparse.ArgumentParser(description="构建标注数据集 manifest")
    ap.add_argument("--raw", default="data/raw", help="原始 pcap 目录")
    ap.add_argument("--out", default="data/labeled", help="输出目录")
    ap.parse_args()

    # 阶段 1 实现：遍历 + 会话提取 + manifest.csv 生成
    raise NotImplementedError("阶段 1 实现：建库逻辑")


if __name__ == "__main__":
    main()
