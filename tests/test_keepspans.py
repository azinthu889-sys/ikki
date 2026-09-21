# -*- coding: utf-8 -*-
"""⏸ **အနားယူချက် ပြန်ချန်ခြင်း** — engine က ပုံသေ ဖြတ်သည်。

⚠️ Zin ၂၀၂၆-၀၉-၂၁: 「ဒီနေရာတွေပါ စိတ်ကြိုက် edit လို့ရအောင်」。
   အနားယူချက် တချို့က တမင် ထားတာ (အသားပေးချက် · အသက်ရှူ · ရပ်တန့်ချက်) —
   ဖြတ်လိုက်လျှင် စကားက လျှောက်ပြောနေသလို သဘာဝ မကျပါ。
⚠️ **ဖျက်ခိုင်းချက်က အထက်တန်း** — worker မှာ `readd()` ကို `user_drop`
   မတိုင်ခင် လုပ်သဖြင့် သုံးစွဲသူ ဖြတ်ခိုင်းတာက ချန်ခိုင်းတာကို ပြန်ဖြတ်နိုင်သည်。
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import cut as CUT            # noqa: E402

WEB = open(os.path.join(ROOT, "web", "script.html"), encoding="utf-8").read()
API = open(os.path.join(ROOT, "api", "main.py"), encoding="utf-8").read()
WRK = open(os.path.join(ROOT, "worker", "run.py"), encoding="utf-8").read()


class KeepSpans(unittest.TestCase):

    # ── core ──
    def test_readd_merges(self):
        o, add = CUT.readd([(0.0, 2.0), (5.0, 8.0)], [[2.0, 5.0]], 10.0)
        self.assertEqual(o, [(0.0, 8.0)])
        self.assertAlmostEqual(add, 3.0)

    def test_readd_middle(self):
        o, add = CUT.readd([(0.0, 2.0), (5.0, 8.0)], [[3.0, 4.0]], 10.0)
        self.assertEqual(o, [(0.0, 2.0), (3.0, 4.0), (5.0, 8.0)])
        self.assertAlmostEqual(add, 1.0)

    def test_readd_clamps_to_dur(self):
        """⚠️ ဘောင်ပြင် မထွက်ရ — ထွက်လျှင် ffmpeg က အပိုင်းအစ ထပ်ထုတ်မည်"""
        o, _ = CUT.readd([(0.0, 2.0)], [[9.0, 99.0]], 10.0)
        self.assertLessEqual(max(b for _a, b in o), 10.0)

    def test_readd_sorted_no_overlap(self):
        o, _ = CUT.readd([(5.0, 8.0), (0.0, 2.0)], [[1.0, 6.0]], 10.0)
        for i in range(len(o) - 1):
            self.assertLessEqual(o[i][1], o[i + 1][0])

    def test_readd_empty_is_noop(self):
        sp = [(0.0, 2.0)]
        self.assertEqual(CUT.readd(sp, [], 10.0), (sp, 0.0))
        self.assertEqual(CUT.readd(sp, None, 10.0), (sp, 0.0))

    def test_readd_bad_input(self):
        """ကျဘမ်း မဖြစ်ရ"""
        for bad in ([["a", "b"]], [[1.0]], [None]):
            o, _ = CUT.readd([(0.0, 2.0)], bad, 10.0)
            self.assertEqual(o, [(0.0, 2.0)])

    # ── ကွင်းဆက် ──
    def test_ui_sends_keep_spans(self):
        self.assertIn("keep_spans: ks", WEB)
        self.assertIn("SKEEP", WEB)
        self.assertIn("data-pkeep", WEB)

    def test_api_stores_keep(self):
        self.assertIn('b.get("keep_spans")', API)
        self.assertIn('over["_keep"]', API)

    def test_worker_applies_keep(self):
        self.assertIn('over.pop("_keep"', WRK)
        self.assertIn("CUT.readd(spans, user_keep", WRK)

    def test_drop_wins_over_keep(self):
        """⚠️ `readd` က `user_drop` **မတိုင်ခင်** ဖြစ်ရမည်"""
        i_keep = WRK.index("CUT.readd(spans, user_keep")
        i_drop = WRK.index("CUT.subtract(spans, user_drop")
        self.assertLess(i_keep, i_drop, "ဖျက်ခိုင်းချက်က အထက်တန်း ဖြစ်ရမည်")


if __name__ == "__main__":
    unittest.main(verbosity=2)
