"""探查单个 pcap 的协议构成（调试/数据摸底用）。

统计：总包数、TCP/UDP/其他、443 端口占位、TLS 握手 (0x16 首字节)、UDP/443(疑似 QUIC)。
用法：
    .venv/bin/python scripts/probe_pcap.py <pcap路径> [<pcap路径>...]
"""
import sys

from scapy.all import IP, IPv6, PcapReader, Raw, TCP, UDP

TLS_FIRST_BYTE = b"\x16"


def probe(path: str) -> None:
    n = 0
    n_tcp = 0
    n_udp = 0
    n_other = 0
    n_tcp443 = 0
    n_tls_hello = 0
    n_udp443 = 0
    n_ip = 0
    n_ip6 = 0
    for pkt in PcapReader(path):
        n += 1
        if pkt.haslayer(TCP):
            n_tcp += 1
            t = pkt[TCP]
            if t.sport == 443 or t.dport == 443:
                n_tcp443 += 1
                if pkt.haslayer(Raw) and pkt[Raw].load[:1] == TLS_FIRST_BYTE:
                    n_tls_hello += 1
        elif pkt.haslayer(UDP):
            n_udp += 1
            u = pkt[UDP]
            if u.sport == 443 or u.dport == 443:
                n_udp443 += 1
        else:
            n_other += 1
        if pkt.haslayer(IP):
            n_ip += 1
        if pkt.haslayer(IPv6):
            n_ip6 += 1

    print(f"== {path}")
    print(f"   总包数     : {n}")
    print(f"   TCP        : {n_tcp} ({100.0 * n_tcp / max(n, 1):.1f}%)")
    print(f"   UDP        : {n_udp} ({100.0 * n_udp / max(n, 1):.1f}%)")
    print(f"   其他       : {n_other} ({100.0 * n_other / max(n, 1):.1f}%)")
    print(f"   IPv4/IPv6  : {n_ip} / {n_ip6}")
    print(f"   TCP:443    : {n_tcp443}  (其中 TLS 握手首字节0x16: {n_tls_hello})")
    print(f"   UDP:443    : {n_udp443}  (疑似 QUIC)")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for path in sys.argv[1:]:
        probe(path)


if __name__ == "__main__":
    main()
