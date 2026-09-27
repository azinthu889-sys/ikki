# -*- coding: utf-8 -*-
"""Kinetic keyword titles (short-916 · reference r3, 2026-09-27)."""
import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import kinetitle as KT    # noqa: E402


def cap(ws, kw):
    return dict(text=" ".join(w[0] for w in ws), start=ws[0][1], end=ws[-1][2], words=ws, kw=kw)


class Groups(unittest.TestCase):

    def test_on_is_spoken_time_and_text_verbatim(self):
        c = cap([("ဂျပန်မှာ", 1.0, 1.4), ("Tokutei", 1.45, 1.9), ("ဗီဇာ", 1.95, 2.3)], ["Tokutei"])
        g = KT.groups([c], [], 30.0)
        self.assertEqual(len(g), 1)
        self.assertEqual(g[0]["tokens"][0][0], "Tokutei")
        self.assertAlmostEqual(g[0]["tokens"][0][1], 1.45 - KT.ON_LEAD)

    def test_never_over_a_graphic(self):
        c = cap([("Tokutei", 5.0, 5.4)], ["Tokutei"])
        self.assertEqual(KT.groups([c], [(4.0, 7.0)], 30.0), [])

    def test_spacing(self):
        caps = [cap([("Tokutei", t, t + 0.4)], ["Tokutei"]) for t in (1.0, 3.0, 9.0, 11.0, 20.0)]
        g = KT.groups(caps, [], 40.0, gap=6.0)
        for p, q in zip(g, g[1:]):
            self.assertGreaterEqual(q["a"] - p["b"], 6.0)

    def test_keyword_not_in_words_is_skipped(self):
        c = cap([("ဂျပန်မှာ", 1.0, 1.4)], ["COE"])
        self.assertEqual(KT.groups([c], [], 30.0), [])

    def test_duration_bounds(self):
        c = cap([("Tokutei", 2.0, 2.4), ("ဗီဇာ", 2.5, 2.9)], ["Tokutei", "ဗီဇာ"])
        g = KT.groups([c], [], 30.0)[0]
        self.assertLessEqual(g["b"] - g["a"], KT.MAX_GROUP + KT.EXIT + 1e-6)
        self.assertGreaterEqual(g["b"] - g["tokens"][-1][1], KT.ENTER + KT.HOLD - 1e-6)


if __name__ == "__main__":
    unittest.main()
