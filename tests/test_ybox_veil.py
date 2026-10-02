# -*- coding: utf-8 -*-
"""`dress._ybox()` — **မှိန်သော နောက်ခံလွှာကို မှင် ဟု မမှတ်ရ**

⚠️⚠️ တိုင်းချက် (၂၀၂၆-၁၀-၀၂ · `tools/gfxypos.py` · template ၅၀၅ ခု):
   `retro.*` ၉ ခုက `alpha > 8` box က ဘောင်ရဲ့ ၉၁–၁၀၀% ဖြစ်ပါလျက်
   ဖုံးအုပ်မှု ၀.၀၁၀–၀.၂၃၃ သာ ⇒ `track()` က 「နေရာ မတည့်」 နဲ့ ပယ်ခဲ့သည်。
   ဥပမာ `retro.count_tape` box ၉၃% · mass ၀.၀၁၀ (တကယ့် မှင် ၈၆%… ⚠️ မဟုတ် —
   `mass-h` ၀.၈၆၆ က **မှင် ဘန်း** ဖြစ်ပြီး mass ၀.၀၁၀ က **ပျမ်းမျှ alpha**)。

⚠️ **ကျန် template မပြောင်းရ** — ဒါက အဓိက အာမခံချက်。 ပုံမှန် ကတ်
   (အလင်းပိတ် အပြည့် · ဘောင်ရဲ့ အပိုင်းတစ်ခု) မှာ box က မပြောင်းရ。
⚠️ ဖရိမ်းကို **လက်နဲ့ ဆောက်**သည် — motionkit မလို ⇒ စစ်ချက်က မြန်ပြီး
   template ပြောင်းလဲမှုနဲ့ မဆိုင်ပါ。
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import numpy as np                                             # noqa: E402
from PIL import Image                                          # noqa: E402

import dress as DR                                             # noqa: E402

W, H = 1080, 1920


def _png(dirp, name, a):
    p = os.path.join(dirp, name)
    rgba = np.zeros((a.shape[0], a.shape[1], 4), dtype=np.uint8)
    rgba[:, :, :3] = 255
    rgba[:, :, 3] = a
    Image.fromarray(rgba, "RGBA").save(p)
    return p


def _el(paths):
    # ⚠️ `_ybox` က `anim` ရဲ့ **နောက်ပိုင်း တစ်ဝက်** ကိုသာ ယူသည် ⇒
    #    ဖရိမ်း ၂ ခု ထည့်ပြီး ၂ ခုလုံး တူညီစေသည်。
    return {"anim": [(p, 0, 0) for p in paths] * 2, "statics": []}


class Veil(unittest.TestCase):
    def test_faint_full_frame_veil_is_not_ink(self):
        """၇% veil + အောက်ပိုင်းမှာ စာတုံး ⇒ box က စာတုံးသာ ဖြစ်ရမည်"""
        with tempfile.TemporaryDirectory() as d:
            a = np.full((H, W), 18, dtype=np.uint8)       # ၇% ≈ alpha 18
            a[1500:1700, 100:900] = 255                   # တကယ့် မှင်
            p = _png(d, "veil.png", a)
            y0, y1 = DR._ybox(_el([p]), H)
            self.assertGreater(y0, 1000, (y0, y1))
            self.assertLess(y1, 1900, (y0, y1))
            self.assertLess(y1 - y0, int(H * 0.30), (y0, y1))

    def test_opaque_card_unchanged(self):
        """အလင်းပိတ် ကတ် — box က အတိအကျ ကတ်အတိုင်း ဖြစ်ရမည်"""
        with tempfile.TemporaryDirectory() as d:
            a = np.zeros((H, W), dtype=np.uint8)
            a[1200:1500, 80:1000] = 255
            p = _png(d, "card.png", a)
            self.assertEqual(DR._ybox(_el([p]), H), (1200, 1499))

    def test_true_full_frame_unchanged(self):
        """⚠️ **တကယ့် ဘောင်အပြည့်** (mass ၁.၀) ကို မထိရ — ဖြတ်ပြောင်းတွေက
           ပြောသူကို တကယ် ဖုံးရမည်。 ၅၀၅ ခုမှာ ၈၃ ခုက ဒီအုပ်စု。"""
        with tempfile.TemporaryDirectory() as d:
            a = np.full((H, W), 255, dtype=np.uint8)
            p = _png(d, "full.png", a)
            y0, y1 = DR._ybox(_el([p]), H)
            self.assertEqual(y0, 0)
            self.assertGreaterEqual(y1, int(H * 0.99))

    def test_half_opaque_full_frame_unchanged(self):
        """mass ၀.၅ ကျော် (၆၀% alpha အပြည့်) ⇒ veil မဟုတ် ⇒ မပြောင်းရ"""
        with tempfile.TemporaryDirectory() as d:
            a = np.full((H, W), 160, dtype=np.uint8)      # ၆၃%
            p = _png(d, "half.png", a)
            y0, y1 = DR._ybox(_el([p]), H)
            self.assertEqual(y0, 0)
            self.assertGreaterEqual(y1, int(H * 0.99))

    def test_tall_but_not_full_unchanged(self):
        """box ၈၅% (၉၀% အောက်) ⇒ ဖျော့လည် မထိရ — စစ်ချက် ၂ ခုလုံး လိုသည်"""
        with tempfile.TemporaryDirectory() as d:
            a = np.full((H, W), 18, dtype=np.uint8)
            a[:int(H * 0.14), :] = 0                      # အပေါ် ၁၄% ဖယ်
            a[1500:1700, 100:900] = 255
            p = _png(d, "tall.png", a)
            y0, y1 = DR._ybox(_el([p]), H)
            self.assertLessEqual(y0, int(H * 0.15), (y0, y1))

    def test_empty_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            p = _png(d, "zero.png", np.zeros((H, W), dtype=np.uint8))
            self.assertEqual(DR._ybox(_el([p]), H), (0, int(H * 0.32)))

    def test_offset_strip_respected(self):
        """strip PNG က offset ရှိသည် ⇒ box က offset ပါ ပေါင်းရမည်"""
        with tempfile.TemporaryDirectory() as d:
            a = np.zeros((300, 900), dtype=np.uint8)
            a[50:250, :] = 255
            p = _png(d, "strip.png", a)
            el = {"anim": [(p, 60, 1400)] * 2, "statics": []}
            self.assertEqual(DR._ybox(el, H), (1450, 1649))

    def test_thresholds_are_named(self):
        self.assertAlmostEqual(DR._VEIL_SPAN, 0.90)
        self.assertAlmostEqual(DR._VEIL_MASS, 0.50)
        self.assertAlmostEqual(DR._VEIL_PEAK, 0.20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
