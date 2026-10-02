# -*- coding: utf-8 -*-
"""အနားယူချိန်ကို **မူရင်း အရှည်အလိုက်** ပြန်ပေးသည်

⚠️⚠️ ယခင်က တိတ်ဆိတ်မှု အရှည် ဘယ်လောက်ပဲဖြစ်ဖြစ် `2×pad` ပဲ ချန်ခဲ့သည် ⇒
   ၁၄.၉s အနားယူချိန်နဲ့ ၀.၅s အနားယူချိန် **ရလဒ် တူတူ**。 တိုင်းချက်
   (၂၀၂၆-၁၀-၀၂ · short-916 ထွက်ဖိုင်): အရှည်ဆုံး **၀.၈၈s** · p90 ၀.၄၂s ⇒
   စည်းချက် ပြားသွားသည်。 Zin: 「ခေါင်းစဉ်ပြောင်းတဲ့နေရာမှာ အသက်ရှုခွင့်
   ပြန်ပေးပါ」。

⚠️ ပစ်မှတ်ကို **Zin ရဲ့ ကိုယ်ပိုင် ဗီဒီယို ၁၀ ခု** (ZJL knowledge) ကနေ တိုင်းသည် —
   p50 ၀.၁၆ · p75 ၀.၃၆ · **p90 ၀.၅၆** · အရှည်ဆုံး ၁.၄–၁၃.၀ (အလယ် ၄.၉)。
   တိုတဲ့အနားတွေက ကိုက်နေပြီး အရှည်ပဲ ကွာသည် ⇒ **အရှည်ကိုသာ** ပြန်ပေးရသည်。

⚠️ cut အဆင့်က planner **ထက် စော**သည် (stage 3 vs 5) ⇒ 「ခေါင်းစဉ်」 label
   မရသေးပါ。 ပြောသူ ကိုယ်တိုင် ရပ်ထားတဲ့ **အနားယူချိန် အရှည်ကိုယ်တိုင်**က
   တစ်ခုတည်းသော အချက်ပြ ဖြစ်သည်。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import cut as C                                               # noqa: E402
import recipes as R                                           # noqa: E402

PAD = 0.09
MIN_SIL = 0.34


class Curve(unittest.TestCase):
    def test_short_pause_keeps_the_floor(self):
        """⚠️ `min_sil` အနီး တိတ်ဆိတ်မှုက ယခင်အတိုင်း — တိုတာတွေ မထိရ"""
        # ⚠️ ၀.၃၅s က `min_sil` ထက် ၀.၀၁ ပဲ ကျော်သဖြင့် ၀.၁၈ + ၀.၀၀၁
        self.assertAlmostEqual(C.pause_keep(0.35, PAD, MIN_SIL), 0.18, places=2)
        self.assertLess(C.pause_keep(0.40, PAD, MIN_SIL), 0.20)

    def test_long_pause_keeps_more(self):
        a = C.pause_keep(1.0, PAD, MIN_SIL)
        b = C.pause_keep(5.0, PAD, MIN_SIL)
        c = C.pause_keep(14.9, PAD, MIN_SIL)
        self.assertGreater(a, 0.18)
        self.assertGreater(b, a)
        self.assertGreaterEqual(c, b)

    def test_capped(self):
        """⚠️ ကန့်သတ် မရှိလျှင် ၁၄.၉s အနားယူချိန်က ၁.၅s+ ဖြစ်မည်"""
        self.assertLessEqual(C.pause_keep(14.9, PAD, MIN_SIL), C.PAUSE_MAX + 1e-6)
        self.assertLessEqual(C.pause_keep(60.0, PAD, MIN_SIL), C.PAUSE_MAX + 1e-6)

    def test_never_below_floor(self):
        for L in (0.35, 0.5, 1.0, 3.0, 20.0):
            self.assertGreaterEqual(C.pause_keep(L, PAD, MIN_SIL), 2 * PAD - 1e-6)

    def test_ratio_zero_restores_old_behaviour(self):
        """⚠️ ပြန်ပိတ်နိုင်ရမည် — ယခင် အပြုအမူ အတိအကျ"""
        for L in (0.5, 2.0, 14.9):
            self.assertAlmostEqual(C.pause_keep(L, PAD, MIN_SIL, ratio=0.0),
                                   2 * PAD, places=6)

    def test_tuned_values_are_the_measured_ones(self):
        """⚠️ ကိန်းက **ညှိပြီး ရွေးထားတာ** — မှန်းချက် မဟုတ် (ratio ၀.၁၀
           ⇒ p90 ၀.၅၈ · ပစ်မှတ် ၀.၅၆)"""
        self.assertAlmostEqual(C.PAUSE_RATIO, 0.10)
        self.assertAlmostEqual(C.PAUSE_MAX, 1.5)


class Wiring(unittest.TestCase):
    def test_recipes_carry_the_knobs(self):
        for n in ("short-916", "knowledge", "headtop"):
            rc = R.get(n)
            self.assertIsNotNone(rc.get("pause_ratio"), n)
            self.assertIsNotNone(rc.get("pause_max"), n)

    def test_bounds_allow_disabling(self):
        lo, hi = R.BOUNDS["pause_ratio"][1], R.BOUNDS["pause_ratio"][2]
        self.assertEqual(lo, 0.0)
        self.assertGreaterEqual(hi, 0.10)

    def test_plan_reports_the_values(self):
        import io
        src = io.open(os.path.join(os.path.dirname(__file__), "..", "core",
                                   "cut.py"), encoding="utf-8").read()
        self.assertIn("pause_ratio=_pr, pause_max=_pm", src)

    def test_worker_passes_them(self):
        import io
        src = io.open(os.path.join(os.path.dirname(__file__), "..", "worker",
                                   "run.py"), encoding="utf-8").read()
        self.assertIn('pause_ratio=rc.get("pause_ratio")', src)
        self.assertIn('pause_max=rc.get("pause_max")', src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
