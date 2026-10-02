# -*- coding: utf-8 -*-
"""mastering ရဲ့ limiter ခေါင်း — **တွက်ရမည်၊ ချိုးဖြတ်၍ မရ**

⚠️⚠️ ၂၀၂၆-၁၀-၀၂ render `j_s41` — ချိန် ၅ ကြိမ်လုံး မပြေလည်ဘဲ
   **I −14.70 LUFS · TP −3.97 dBTP** နဲ့ ထွက်သွားခဲ့သည် (ကျန် render ၃ ခုက
   −14.3~−14.4 / −1.2~−1.6)。 log က ယန္တရား ပြသည် —
     ချိန် ၁ TP −1.30 · ceiling −2.00
     ချိန် ၂ TP **+1.00** (၀ dBFS ကျော်) ⇒ ceiling −4.25 သို့ **ချ**
     ချိန် ၃ TP −2.60 · ချိန် ၄ TP −0.30 · ချိန် ၅ TP −3.60
   ⇒ ① `alimiter` က **နမူနာ အထွတ်**ကိုသာ ကန့်သတ်ပြီး true peak က
        inter-sample/AAC ကြောင့် **၃ dB ကျော်** နိုင်သည်
     ② ကုဒ်က ခေါင်းကို **တစ်လမ်းသာ ချ**ပြီး ပြန်မတင် ⇒ headroom
        အမြဲ ဆုံးရှုံးကာ TP က တုန်ခါသည်
     ③ loop က `out` ကို နေရာတွင်း လဲနေပြီး **အကောင်းဆုံးကို မမှတ်** ⇒
        မပြေလည်လျှင် နောက်ဆုံး (အဆိုးဆုံး ဖြစ်နိုင်) ဟာကို ပို့သည်
"""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import spans as SP                                            # noqa: E402

SRC = os.path.join(os.path.dirname(__file__), "..", "core", "spans.py")


class Ceiling(unittest.TestCase):
    def test_first_pass_has_no_overshoot_data(self):
        """⚠️ ခေါင်း မသုံးရသေးလျှင် ကျော်မှု မသိ ⇒ −၂.၀ ကနေ စရမည်"""
        self.assertAlmostEqual(SP._solve_ceiling(-1.30, -1.0, None), -2.0)

    def test_solves_from_measured_overshoot(self):
        """တကယ့် ကိန်း — ခေါင်း −၂.၀၀ မှာ TP +၁.၀၀ ⇒ ကျော်မှု ၃.၀
           ⇒ ပစ်မှတ် −၁.၀ ရဖို့ ခေါင်း **−၄.၀**"""
        self.assertAlmostEqual(SP._solve_ceiling(1.00, -1.0, -2.0), -4.0)

    def test_ceiling_recovers_when_tp_is_low(self):
        """⚠️ **အဓိက** — TP နိမ့်လျှင် ခေါင်း **ပြန်တက်ရမည်**。
           ယခင် ကုဒ်က ဘယ်တော့မှ ပြန်မတင်ခဲ့。"""
        # ခေါင်း −၄.၂၅ မှာ TP −၂.၆၀ ⇒ ကျော်မှု ၁.၆၅ ⇒ ခေါင်း −၂.၆၅
        got = SP._solve_ceiling(-2.60, -1.0, -4.25)
        self.assertAlmostEqual(got, -2.65)
        self.assertGreater(got, -4.25, "ခေါင်း ပြန်မတက်ပါ")

    def test_never_above_minus_one(self):
        """headroom အနည်းဆုံး ချန်ရမည်"""
        self.assertLessEqual(SP._solve_ceiling(-9.0, -1.0, -2.0), -1.0)

    def test_floor_is_bounded(self):
        self.assertGreaterEqual(SP._solve_ceiling(20.0, -1.0, -2.0), -12.0)

    def test_real_trajectory_converges(self):
        """j_s41 ရဲ့ တကယ့် ကိန်းနဲ့ တုပ — ၂ ကြိမ်အတွင်း ပစ်မှတ် ရရမည်

        ⚠️ ကျော်မှုက တည်ငြိမ်သည် ဟု ယူဆသည် (inter-sample/AAC ကြောင့်
           ဖြစ်၍ gain နဲ့ သိပ် မပြောင်း)。
        """
        OVER = 3.0                      # တိုင်းထားသော ကျော်မှု
        tp = -1.0
        applied, got = None, -1.30
        for _ in range(3):
            c = SP._solve_ceiling(got, tp, applied)
            applied, got = c, c + OVER
        self.assertLessEqual(got, tp + 0.01, got)
        self.assertGreater(got, tp - 1.0, got)   # အလွန်အကျွံ မချရ


class Loop(unittest.TestCase):
    def setUp(self):
        self.s = io.open(SRC, encoding="utf-8").read()

    def test_keeps_best_state(self):
        self.assertIn("bestp = out + \".best.mp4\"", self.s)
        self.assertIn("os.replace(best[1], out)", self.s)

    def test_penalty_weights_tp_violation(self):
        """⚠️ TP ကျော်တာက ဂိတ် ပျက်ခြင်း · TP နိမ့်တာက မပျက် ⇒ ၂ ဆ ဒဏ်"""
        self.assertIn("_pen = max(0.0, d_tp) * 2.0 + abs(d_i)", self.s)

    def test_measures_final_state(self):
        """⚠️ နောက်ဆုံး ချိန်ချက်ရဲ့ ရလဒ်ကိုပါ တိုင်းရမည် (ITER + ၁)"""
        self.assertIn("for _it in range(ITER + 1):", self.s)
        self.assertIn("if _it >= ITER:", self.s)

    def test_ratchet_removed(self):
        """⚠️ တစ်လမ်းသာ ချသော ကုဒ် ကျန်မနေရ"""
        self.assertNotIn("ceil_db -= (d_tp + 0.25)", self.s)
        self.assertIn("ceil_db = _solve_ceiling(got_tp, tp, applied)", self.s)

    def test_applied_tracked(self):
        self.assertIn("applied = ceil_db", self.s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
