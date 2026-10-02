# -*- coding: utf-8 -*-
"""keyword pop — **ဘောင်ကျော်လျှင် စာလုံး မဖြုတ်ဘဲ အရွယ် ချုံ့ရမည်**

⚠️⚠️ ၂၀၂၆-၁၀-၀၂ short-916 render ရဲ့ တိုင်းချက် (ဖိုင်ကနေ တိုက်ရိုက်):
      size 233 ⇒ မှင် x    0–1079 (ပြတ်)   · အမြင့် 193
      size 200 ⇒ မှင် x    0–1079 (ပြတ်)   · အမြင့် 193
      size 164 ⇒ မှင် x    0–1079 (ပြတ်)   · အမြင့် 158
      size 134 ⇒ မှင် x   31–1044 (မပြတ်)  · အမြင့် 128 ⇒ အကျယ် ၁၀၁၃
   ကန့်သတ်က ၉၉၃ (W×0.92) ⇒ ၁၀၁၃ က **၂% ပဲ ကျော်**သည်。
   ယခင် ကုဒ်က ၂ ကြိမ်သာ ချုံ့ပြီး ၃ ကြိမ်မြောက်မှာ စာလုံး ဖြုတ်သဖြင့်
   「Western Union」⇒「Western」·「Cashback Mobile」⇒「Cashback」ဖြစ်ခဲ့သည်。

⚠️ **ပြတ်နေချိန်မှာ တိုင်းချက် မယုံရ** — မှင်က ဘောင်အတိုင်း ထွက်သည် ⇒
   တကယ့် အကျယ် မသိရ ⇒ အချိုးနဲ့ မတွက်နိုင် (၀.၈၂ စီ ချုံ့ရသည်)。
   မပြတ်တော့မှ မှင်က အရွယ်နဲ့ မျဉ်းဖြောင့် ⇒ တစ်ခါတည်း တွက်သည်。
"""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import run as W                                               # noqa: E402

WW = 1080


class PopFit(unittest.TestCase):
    def test_clipped_shrinks_by_fixed_step(self):
        self.assertEqual(W._pop_fit(233, 1079, WW, True, 97), int(233 * 0.82))

    def test_unclipped_computes_in_one_step(self):
        """၁၀၁၃px မှာ ပစ်မှတ် ၉၂၈ (W×0.86) ⇒ 134×928/1013 ≈ 122"""
        n = W._pop_fit(134, 1013, WW, False, 56)
        self.assertEqual(n, int(134 * (WW * 0.86) / 1013))
        self.assertLess(n, 134)
        # ⇒ ချုံ့ပြီးနောက် အကျယ်က ကန့်သတ် (၉၉၃) အောက် ရောက်ရမည်
        self.assertLessEqual(1013.0 * n / 134.0, WW * 0.92)

    def test_never_returns_bigger(self):
        for ww in (900, 1000, 1500):
            n = W._pop_fit(100, ww, WW, False, 20)
            self.assertLess(n, 100, (ww, n))

    def test_floor_returns_none(self):
        """ကြမ်းခင်း အောက် ⇒ `None` ⇒ ခေါ်သူက စာလုံး ဖြုတ်သည်"""
        self.assertIsNone(W._pop_fit(60, 1079, WW, True, 56))

    def test_floor_boundary_is_inclusive(self):
        self.assertEqual(W._pop_fit(100, 1079, WW, True, 82), 82)

    def test_minimum_size_respected(self):
        n = W._pop_fit(30, 3000, WW, False, 10)
        self.assertGreaterEqual(n, 24)

    def test_zero_size_is_safe(self):
        self.assertIsNone(W._pop_fit(0, 1079, WW, True, 24))
        self.assertIsNone(W._pop_fit(None, 1079, WW, True, 24))

    def test_real_sequence_converges(self):
        """တကယ့် တိုင်းချက် အတိုင်း — ၅ ကြိမ်အတွင်း ဝင်ရမည် · စာလုံး မဖြုတ်ရ

        မှင် အကျယ်ကို size နဲ့ မျဉ်းဖြောင့် အဖြစ် တုပသည်
        (တိုင်းချက်: 134 ⇒ 1013 ⇒ တစ်ယူနစ်လျှင် ၇.၅၆px)。
        """
        K = 1013.0 / 134.0
        size = 233
        wmin = max(24, int(233 * 0.42))
        for _ in range(5):
            true_w = K * size
            ww = min(true_w, float(WW) - 1)         # ဘောင်က ဖြတ်သည်
            clip = true_w >= WW
            if ww <= WW * 0.92:
                break
            n = W._pop_fit(size, ww, WW, clip, wmin)
            self.assertIsNotNone(n, "စာလုံး ဖြုတ်ခဲ့သည် — size %d" % size)
            size = n
        self.assertLessEqual(K * size, WW * 0.92, size)
        self.assertGreaterEqual(size, wmin)

    def test_truncation_drops_last_word_not_all(self):
        src = io.open(os.path.join(os.path.dirname(__file__), "..", "worker",
                                   "run.py"), encoding="utf-8").read()
        self.assertIn('_pr3["text"] = " ".join(_t1[:-1])', src)
        self.assertNotIn('_pr3["text"] = _t1[0]', src)

    def test_loop_has_five_tries(self):
        src = io.open(os.path.join(os.path.dirname(__file__), "..", "worker",
                                   "run.py"), encoding="utf-8").read()
        self.assertIn("for _wtry in (1, 2, 3, 4, 5):", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
