"""PCAP 读取：scapy 逐包流式，统一为轻量包 dict。

设计：
- 用 PcapReader 逐包流式读取，大 pcap 不整载入内存。
- 统一字段（见 _REQUIRED_PACKET_FIELDS），另保留 seq/ack/flags(/方向) 供会话重组。
- 上游（reassembler/features）只依赖这些字段名，解析实现可替换。
"""

from pathlib import Path
from typing import Iterable

from scapy.all import IP, IPv6, PcapReader, TCP, UDP, Raw

# 统一包字段
_REQUIRED_PACKET_FIELDS = (
    "ts_us", "src_ip", "src_port", "dst_ip", "dst_port", "proto",
    "payload", "seq", "acl", "flags", "src_mac", "dst_mac",
)


def _pcap_timestamp_us(pkt) -> int:
    """scapy Packet.time 是 float 秒，统一转微秒。"""
    return int(round(float(pkt.time) * 1e6))


def _dir_key(p) -> tuple:
    """标记方向的字段元组（用于重排序/去重的 key）。"""
    if p.haslayer(TCP):
        return (p[TCP].seq, int(p[TCP].flags))
    return (None, None)


def _to_packet_dict(pkt) -> dict | None:
    """scapy packet → 统一 dict；非 IP/TCP/UDP 返回 None。"""
    if not (pkt.haslayer(IP) or pkt.haslayer(IPv6)):
        return None
    ip = pkt[IP] if pkt.haslayer(IP) else pkt[IPv6]
    src_ip, dst_ip = ip.src, ip.dst

    if pkt.haslayer(TCP):
        t = pkt[TCP]
        proto, sport, dport = "tcp", t.sport, t.dport
        seq, ack, flags = t.seq, t.ack, int(t.flags)
    elif pkt.haslayer(UDP):
        u = pkt[UDP]
        proto, sport, dport = "udp", u.sport, u.dport
        seq, ack, flags = None, None, 0
    else:
        return None

    payload = bytes(pkt[Raw].load) if pkt.haslayer(Raw) else b""
    return {
        "ts_us": _pcap_timestamp_us(pkt),
        "src_ip": src_ip, "src_port": sport,
        "dst_ip": dst_ip, "dst_port": dport,
        "proto": proto, "payload": payload,
        "seq": seq, "ack": ack, "flags": flags,
    }


class PcapReader:
    """PCAP/PCAPNG 流式读取器。"""

    def read_packets(self, path: str | Path) -> Iterable[dict]:
        """逐包 yield 统一 dict；非 IP/TCP/UDP 跳过。"""
        with PcapReader(str(path)) as rd:
            for pkt in rd:
                d = _to_packet_dict(pkt)
                if d is not None:
                    yield d

    def read_all(self, path: str | Path) -> list[dict]:
        """一次性读回全部包（小样本/演示用）。"""
        return list(self.read_packets(path))
