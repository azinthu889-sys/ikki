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




class MergeDrops(unittest.TestCase):
    """ထပ်/ကပ် ဖျက်ချက် ပေါင်း (j_4dd59bb90b5a — ၁၂/၂၇ ငြင်းခံရမှု · ၂၀၂၆-၁၀-၀၆)"""
    def test_merge(self):
        m = C.merge_drops([[114.46, 114.73], [114.0, 114.46], [120, 121], [121.02, 121.5], [130, 131]])
        self.assertEqual(m, [[114.0, 114.73], [120.0, 121.5], [130.0, 131.0]])

    def test_merged_edges_validated_outside(self):
        # အပိုင်းအစ (အစက စကားထဲ) + ဘေးက ဝါကျ ဖျက်ချက် ⇒ ပေါင်း ⇒ အပြင်အစွန်း တိတ်ဆိတ်ရာ ⇒ ok
        sp = [(1.0, 3.0), (5.0, 7.0)]
        piece, sent = [6.5, 7.2], [4.8, 6.5]
        ok1, bad1 = C.validate_drops([piece], sp, 10.0)
        self.assertFalse(ok1)
        ok2, bad2 = C.validate_drops(C.merge_drops([piece, sent]), sp, 10.0)
        self.assertEqual(ok2, [[4.8, 7.2]])

    def test_garbage(self):
        self.assertEqual(C.merge_drops([None, [3, 2], ["a", 1]]), [])

if __name__ == "__main__":
    unittest.main()
