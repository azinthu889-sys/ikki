# -*- coding: utf-8 -*-
"""Reference visual style (Zin ၂၀၂၆-၁၀-၀၇ 「typography · ဂရပ်ဖစ် ပုံစံ ကိုလည်း ယူ」)"""
import os
import sys
import unittest

R = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(R, "core"))
import refdna as RD   # noqa: E402
import recipes as RC  # noqa: E402



def _dna(**vi):
    return RD.labels({"visual": vi})


class RefStyle(unittest.TestCase):
    def test_apply_visual(self):
        d = _dna(accent="#F0CA14", accent_conf=0.8, cap_fill="#FFE55D", cap_conf=0.9,
                 cap_stroke=True, panel="light", panel_conf=0.7)
        over, _ = RD.apply_to(d, RC.get("headtop"))
        self.assertEqual(over["ref_accent"], "#F0CA14")
        self.assertEqual(over["cap_fill"], "#FFE55D")
        self.assertEqual(over["beat_variant"], "light")

    def test_dark_caption_rejected(self):
        d = _dna(cap_fill="#3A2A20", cap_conf=0.9)
        over, notes = RD.apply_to(d, RC.get("headtop"))
        self.assertNotIn("cap_fill", over)
        self.assertTrue(any("မှောင်လွန်း" in n for n in notes))

    def test_low_conf_ignored(self):
        d = _dna(accent="#FF0000", accent_conf=0.1, panel="solid", panel_conf=0.1)
        over, _ = RD.apply_to(d, RC.get("headtop"))
        self.assertNotIn("ref_accent", over)
        self.assertNotIn("beat_variant", over)

    def test_unknown_stays_unknown(self):
        d = RD.labels({"visual": None})
        self.assertEqual(d["accent"], RD.UNK)
        self.assertEqual(d["panel"], RD.UNK)

    def test_brand_never_touched(self):
        d = _dna(accent="#F0CA14", accent_conf=0.9)
        over, _ = RD.apply_to(d, RC.get("headtop"))
        for bad in ("brand_id", "font", "mmf", "latin", "accent"):
            self.assertNotIn(bad, over)


if __name__ == "__main__":
    unittest.main()
