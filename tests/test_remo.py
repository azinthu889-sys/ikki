# -*- coding: utf-8 -*-
"""Remotion cinematic scene director (core/remo.py) — Zin ၂၀၂၆-၁၀-၀၆ 「ဒီလိုပုံစံ」"""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import remo as R  # noqa: E402

CAPS = [dict(start=0.1, end=8.7, text="ပြည်ပနေ Western Union ဖြင့် ငွေလွှဲပြီးတော့ ကျပ် ၅ သိန်းထိ"),
        dict(start=15.6, end=26.5, text="တစ်ကြိမ်ကို အနည်းဆုံး ၅ သိန်းကျပ်လွှဲပြီး KPay နဲ့ လက်ခံရုံဖြင့်")]
EV = [(2.2, 1.4, "modern.mt_neon_box", {"text": "Western Union"}),
      (3.0, 1.4, "modern.mt_neon_box", {"text": "KBZ Pay"}),
      (17.9, 1.8, "modern.mt_counter", {"value": "5"}),
      (34.0, 2.2, "modern.mt_pill_list", {"head": "ဆု", "items": ["A", "B", "C"]})]


class Director(unittest.TestCase):
    def test_scenes(self):
        sc = R.plan_scenes(EV, CAPS, 60.1)
        kinds = [s["type"] for s in sc]
        self.assertEqual(kinds, ["title", "neon", "list", "subscribe"])   # 3.0 က gap အတွင်း ⇒ ကျော်
        self.assertEqual(sc[0]["title"], "WESTERN UNION")
        self.assertEqual(sc[1]["title"], "KBZ PAY")                      # KPay ⇒ KBZ PAY
        self.assertIn("၅", sc[1]["hi"])
        self.assertTrue(all(b["start"] >= a["start"] + a["dur"] - 0.01 for a, b in zip(sc, sc[1:])))

    def test_short_video_no_subscribe(self):
        self.assertFalse([s for s in R.plan_scenes([], CAPS, 15.0) if s["type"] == "subscribe"])

    def test_compose_noop_without_scenes(self):
        self.assertFalse(R.compose("/nonexistent.mp4", [], "/tmp", log=lambda *a: None))


if __name__ == "__main__":
    unittest.main()
