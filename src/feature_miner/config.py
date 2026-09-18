"""全局配置：会话切分、特征命名、路径等。

阶段 1 可扩展为 YAML 配置加载（--config 参数）。
"""

from pathlib import Path

# 项目根目录（src/feature_miner/config.py -> 向上 3 级）
ROOT = Path(__file__).resolve().parents[3]

# 数据目录
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LABELED_DIR = DATA_DIR / "labeled"

# 规则输出目录
RULES_DIR = ROOT / "rules"


class SessionConfig:
    """会话重组口径（与 docs/数据标注约定.md 第 5 节对齐）。"""

    UDP_IDLE_TIMEOUT_S = 120.0   # UDP/QUIC 空闲断流阈值
    TCP_IDLE_TIMEOUT_S = 180.0   # TCP 空闲断流阈值（兜底）
    MIN_PACKETS = 2              # 少于该包数的"会话"丢弃
    MAX_SESSION_DURATION_S = 3600.0  # 单会话最长时长（防粘包）
    QUIC_IDLE_TIMEOUT_S = 30.0   # QUIC 连接内 idle（QUIC 特性，更激进）


class FeatureConfig:
    """特征命名与计算口径。"""

    # 命名：维度_子维度_统计（见架构设计.e4）
    NAMING_SEP = "."
    FLOW_SLICE_S = 5.0           # 流段统计的时间窗（阶段 1 细化）
