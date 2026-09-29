"""TCP/UDP 会话重组与切分。

流程：按双向端点(4元组)分组 → 判定客户端方向 →
TCP 按 seq 排序(乱序)并去重传 → 按空闲超时切成 1..N 个会话。
"""

from dataclasses import dataclass, field

from .session import Session
from ..config import SessionConfig


@dataclass
class _Stream:
    key: tuple
    packets: list[dict] = field(default_factory=list)


_FIN, _SYN, _ACK = 0x01, 0x02, 0x10


def _stream_key(p: dict) -> tuple:
    """归一化 4 元组 key（不区分方向）。"""
    a = (p["src_ip"], p["src_port"])
    b = (p["dst_ip"], p["dst_port"])
    if a < b:
        return (a[0], a[1], b[0], b[1])
    return (b[0], b[1], a[0], a[1])


def _guess_client(stream: _Stream) -> tuple[str, int]:
    """客户端 = 发 SYN(无ACK) 者（TCP）；UDP 取首包 src。"""
    for p in stream.packets:
        if p["proto"] == "tcp" and (p["flags"] & _SYN) and not (p["flags"] & _ACK):
            return p["src_ip"], p["src_port"]
    p0 = stream.packets[0]
    return p0["src_ip"], p0["src_port"]


def _sort_dedup_tcp(stream: _Stream) -> None:
    """按(方向,seq)排序处理乱序；同(方向,seq)去重传。"""
    ordered = sorted(stream.packets,
                     key=lambda p: (p["src_ip"], p["src_port"], p["seq"]))
    seen = set()
    out = []
    for p in ordered:
        k = (p["src_ip"], p["src_port"], p["seq"])
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    stream.packets = out


def _cut_sessions(stream: _Stream, c_ip: str, c_port: int) -> list[Session]:
    """按空闲超时切分会话。"""
    cfg = SessionConfig()
    pkts = sorted(stream.packets, key=lambda p: p["ts_us"])
    sessions: list[Session] = []
    cur: list[dict] = []
    prev_ts: int | None = None

    def flush() -> None:
        nonlocal cur
        if len(cur) >= cfg.MIN_PACKETS:
            sessions.append(_make_session(cur, stream.key, c_ip, c_port))
        cur = []

    for p in pkts:
        proto = p["proto"]
        timeout = (cfg.TCP_IDLE_TIMEOUT_S if proto == "tcp"
                   else cfg.UDP_IDLE_TIMEOUT_S)
        if prev_ts is not None and p["ts_us"] - prev_ts > timeout * 1e6:
            flush()
        cur.append(p)
        prev_ts = p["ts_us"]
    flush()
    return sessions


def _make_session(packets: list[dict], key, c_ip: str, c_port: int) -> Session:
    ts0, ts1 = packets[0]["ts_us"], packets[-1]["ts_us"]
    session_id = f"{packets[0]['proto']}_{key[0]}_{key[1]}_{key[2]}_{key[3]}_{ts0}"
    return Session(
        session_id=session_id,
        five_tuple=(c_ip, c_port, key[2], key[3], packets[0]["proto"]),
        packets=packets,
        client_to_server=True,
        start_ts=ts0, end_ts=ts1,
        meta={"stream_key": list(key),
              "n_c2s": sum(1 for p in packets if p["src_ip"] == c_ip)},
    )


def reassemble(packets) -> list[Session]:
    """包序列 → 会话列表。

    Args:
        packets: 统一 dict 包序列（PcapReader.read_packets 产出）。

    Returns:
        Session 列表（已切片、已乱序/重传处理）。
    """
    streams: dict[tuple, _Stream] = {}
    for p in packets:
        k = _stream_key(p)
        st = streams.get(k)
        if st is None:
            st = streams[k] = _Stream(key=k)
        st.packets.append(p)

    sessions: list[Session] = []
    for st in streams.values():
        c_ip, c_port = _guess_client(st)
        _sort_dedup_tcp(st)
        sessions.extend(_cut_sessions(st, c_ip, c_port))
    sessions.sort(key=lambda s: s.start_ts)
    return sessions
