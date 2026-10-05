# -*- coding: utf-8 -*-
"""`validate_drops` 「ကျန်မည်」 စစ်ချက် — ကျန်နေသော span နဲ့ ထပ်တာသာ နုတ်ရမည်

၂၀၂၆-၁၀-၀၅ j_d96beb16229d: editor ရဲ့ 「အစိမ်းမှ အစိမ်း」 ဖြတ်ချက် ၅ ခုက ဖျက်ပြီးသား
အပိုင်းကို ဖုံးသဖြင့် အရှည် တစ်ခုလုံး နုတ်ရာ 「-21.6s သာ ကျန်မည်」 ဟု ၅/၅ ငြင်း ⇒
၀.၃၅s အပိုင်းအစ ၁၀ ခု ကျန် ⇒ export က 0.60s အောက် shot နဲ့ ပိတ် ⇒ ဂရပ်ဖစ် မထုတ်။
"""
import json
import os
import sys
import unittest

R = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(R, "core"))
import cut as C  # noqa: E402

SPANS = json.loads("[[22.4,31.17],[34.99,41.69],[47.83,58.93],[66.59,74.07],[76.94,77.44],"
                   "[80.58,80.93],[81.87,82.22],[86.08,87.71],[91.51,93.05],[94.85,95.2],"
                   "[96.72,97.07],[97.59,106.01],[112.11,112.46],[118.52,118.87],[121.15,121.5],"
                   "[126.5,126.85],[133.83,134.18],[139.16,141.59],[142.97,143.79],[144.91,152.81],"
                   "[157.87,166.08],[167.46,170.27],[173.89,176.33],[178.33,178.68]]")
DROPS = [[166.08, 167.46], [0.0, 22.42], [73.82, 97.84], [105.76, 145.16], [170.02, 178.68]]


class Overlap(unittest.TestCase):
    def test_regions_over_removed_parts_are_accepted(self):
        kept = sum(b - a for a, b in SPANS)
        ok, bad = C.validate_drops(DROPS, [], 178.68, kept=kept, spans=SPANS)
        self.assertEqual(len(ok), 5, bad)

    def test_still_refuses_when_nothing_would_be_left(self):
        sp = [[10.0, 12.0]]
        ok, bad = C.validate_drops([[9.0, 13.0]], [], 60.0, kept=2.0, spans=sp)
        self.assertEqual(ok, [])
        self.assertTrue(bad)

    def test_worker_passes_spans(self):
        with open(os.path.join(R, "worker", "run.py"), encoding="utf-8") as f:
            self.assertIn("kept=_kept, spans=spans)", f.read())


if __name__ == "__main__":
    unittest.main()
