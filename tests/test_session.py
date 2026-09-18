"""Session 单元测试（验证骨架可用）。"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.feature_miner.parser.session import Session


class TestSession(unittest.TestCase):
    def test_basic_properties(self):
        s = Session(
            session_id="tcp_abc",
            five_tuple=("1.2.3.4", 12345, "5.6.7.8", 443, "tcp"),
            start_ts=1_000_000,
            end_ts=2_000_000,
        )
        self.assertEqual(s.proto, "tcp")
        self.assertEqual(s.duration_us, 1_000_000)
        self.assertEqual(s.to_dict()["n_packets"], 0)

    def test_duration_nonnegative(self):
        s = Session(five_tuple=("a", 1, "b", 2, "udp"), start_ts=10, end_ts=5)
        self.assertEqual(s.duration_us, 0)

    def test_defaults(self):
        s = Session()
        self.assertTrue(s.client_to_server)
        self.assertFalse(s.session_id)
        self.assertEqual(s.to_dict()["duration_us"], 0)


if __name__ == "__main__":
    unittest.main()
