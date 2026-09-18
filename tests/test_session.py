"""Session 基础单元测试（验证骨架可用）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.feature_miner.parser.session import Session


def test_session_properties():
    s = Session(
        session_id="tcp_abc",
        five_tuple=("1.2.3.4", 12345, "5.6.7.8", 443, "tcp"),
        start_ts=1_000_000,
        end_ts=2_000_000,
    )
    assert s.proto == "tcp"
    assert s.duration_us == 1_000_000
    s.add  # placeholder no-op attribute check
    assert s.to_dict()["n_packets"] == 0


def test_duration_nonnegative():
    s = Session(five_tuple=("a", 1, "b", 2, "udp"), start_ts=10, end_ts=5)
    assert s.duration_us == 0
