"""会话对象定义。

会话 = 一次应用交互的包集合，含五元组、方向标注、起止时间。
会话划分口径见 docs/数据标注约定.md 第 5 节。
阶段 1 将补充：重传/乱序处理、TLS 握手元数据。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Session:
    """一个网络会话。

    Attributes:
        session_id: 唯一 ID（协议_五元组_hash）。
        five_tuple: (src_ip, src_port, dst_ip, dst_port, proto)。
        packets: 保序的包列表（阶段 1 为简单包对象，后续可换为按方向/序列分组）。
        client_to_server: 方向判断（True 表示 src 是客户端）。
        start_ts / end_ts: 微秒级时间戳（与 pcap 一致）。
    """

    session_id: str = ""
    five_tuple: tuple = ()
    packets: list = field(default_factory=list)
    client_to_server: bool = True
    start_ts: int = 0
    end_ts: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_us(self) -> int:
        return max(0, self.end_ts - self.start_ts)

    @property
    def proto(self) -> str:
        """'tcp' / 'udp' / 'raw'（无法判定时）。"""
        return self.five_tuple[4] if len(self.five_tuple) == 5 else "raw"

    def to_dict(self) -> dict:
        """序列化（data/processed 的会话 JSON 用）。"""
        return {
            "session_id": self.session_id,
            "five_tuple": list(self.five_tuple),
            "n_packets": len(self.packets),
            "client_to_server": self.client_to_server,
            "start_ts": self.start_ts,
            "end_ts": self.end_ts,
            "duration_us": self.duration_us,
            "meta": self.meta,
        }
