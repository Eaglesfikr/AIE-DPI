"""PCAP 读取骨架（阶段 1 实现细节）。

决策见 docs/架构设计.md §5：首选 scapy 解析与 TCP 流重组。
本骨架只定义公共接口，保证上层 (pipeline) 不依赖解析库细节。
"""

from pathlib import Path
from typing import Iterable

from .session import Session

# 统一包对象的最小字段（后续可按需扩展）
# 上层代码只依赖这些字段名，解析实现可替换。
_REQUIRED_PACKET_FIELDS = (
    "ts_us",        # 时间戳（微秒）
    "src_ip",       # 源 IP
    "src_port",     # 源端口
    "dst_ip",       # 目的 IP
    "dst_port",     # 目的端口
    "proto",        # 'tcp' | 'udp' | ...
    "payload",      # 应用层负载 bytes（可空）
)


class PcapReader:
    """PCAP/PCAPNG 读取器。"""

    def __init__(self) -> None:
        self._impl = None  # 阶段 1：scapy.rdpcap / RawPcapReader 封装

    def read_packets(self, path: str | Path) -> Iterable[dict]:
        """逐包 yield 统一格式 dict（字段见 _REQUIRED_PACKET_FIELDS）。"""
        raise NotImplementedError("阶段 1 实现：依赖 scapy 读取和字段归一")

    def reassemble(self, packets: Iterable[dict]) -> list[Session]:
        """将包序列按会话口径切分/重组为 Session 列表。

        阶段 1 实现：五元组分组 + 排序(乱序) + 重传去重 + 空闲超时断流。
        """
        raise NotImplementedError("阶段 1 实现：会话重组")
