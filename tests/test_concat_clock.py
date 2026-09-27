# -*- coding: utf-8 -*-
"""Caption concat clock (2026-09-27): the running sum of concat durations is
the burned time. A <=40 ms gap, or a card dropped after its blank, must not
shift later cards (it did: median -80 ms, max -120 ms on short-916)."""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import captions as CP    # noqa: E402


def starts(items):
    t = 0.0; out = {}
    for p, d in items:
        if p != "_":
            out.setdefault(p, round(t, 4))
        t += max(0.02, d)
    return out, t


class ConcatClock(unittest.TestCase):

    def test_small_gaps_do_not_drift(self):
        timed = [[0.1 + i * 0.54, 0.1 + i * 0.54 + 0.50, "c%d" % i] for i in range(40)]  # 40 ms gaps
        s, _ = starts(CP.concat_items(timed, "_", 0, None))
        for a, b, p in timed:
            self.assertAlmostEqual(s[p], a, places=3)

    def test_dropped_card_does_not_double_count_blank(self):
        timed = [[0.0, 1.0, "a"], [2.0, 2.05, "short"], [3.0, 4.0, "b"]]
        s, _ = starts(CP.concat_items(timed, "_", 0, None))
        self.assertNotIn("short", s)
        self.assertAlmostEqual(s["b"], 3.0, places=3)

    def test_total_length_kept(self):
        timed = [[0.5, 1.0, "a"], [1.03, 2.0, "b"]]
        _, T = starts(CP.concat_items(timed, "_", 0, None, total=10.0))
        self.assertAlmostEqual(T, 10.0, places=3)

    def test_overlap_starts_at_previous_end(self):
        timed = [[0.0, 1.0, "a"], [0.8, 2.0, "b"]]
        s, _ = starts(CP.concat_items(timed, "_", 0, None))
        self.assertAlmostEqual(s["b"], 1.0, places=3)


if __name__ == "__main__":
    unittest.main()
