# -*- coding: utf-8 -*-
"""ကတ်က **ဘောင်အကျယ် ထက် မကျော်ရ** (`dress.track`)

⚠️⚠️ ယခင်က အကျယ် ချိန်ညှိချက်က **ဘေးနေရာ အကိုင်းထဲမှာသာ** ရှိခဲ့သည်
   (`side_room(avoid, W) >= W*0.22`)。 ၉:၁၆ မှာ ပြောသူက အကျယ် အပြည့်
   ယူသဖြင့် ဘေးနေရာက **၂px** သာ ⇒ အကိုင်း ဘယ်တော့မှ မပြေး ⇒ ကတ်
   ဘောင်ထက် ကျယ်လျှင် အစွန် ပြတ်သည်。
   တိုင်းချက် (၂၀၂၆-၁၀-၀၂ short-916 v2 · ၆၉.၉s `thm.hook_red`):
   「upgrade လုပ်ထားသူများသာ ဒီ 3」က ညာဘက် ပြတ်နေခဲ့သည်。

⚠️ `gfx_size_*.json` ရဲ့ `w` နဲ့ **ကြိုမသိနိုင်** — အဲဒါက demo စာသားနဲ့
   တိုင်းထားသည် (`thm.hook_red` ၉၃၀px = ၈၆%) ပြီး တကယ့် မြန်မာ စာသားက
   ပိုရှည်သည် ⇒ ဆောက်ပြီးမှ တိုင်းရသည်。
"""
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import numpy as np                                            # noqa: E402
from PIL import Image                                         # noqa: E402

import dress as DR                                            # noqa: E402

W, H = 1080, 1920
SRC = os.path.join(os.path.dirname(__file__), "..", "core", "dress.py")


def _png(d, name, w, h, x0, x1):
    """အကျယ် `x0..x1` မှာ မှင် ရှိသော ပွင့်လင်း PNG"""
    a = np.zeros((h, w, 4), dtype=np.uint8)
    a[:, x0:x1, :3] = 255
    a[:, x0:x1, 3] = 255
    p = os.path.join(d, name)
    Image.fromarray(a, "RGBA").save(p)
    return p


class XBox(unittest.TestCase):
    def test_measures_widest_frame(self):
        """⚠️ frame တစ်ခုတည်း မဟုတ် — **အကျယ်ဆုံး** ကို ယူရမည်"""
        with tempfile.TemporaryDirectory() as d:
            a = _png(d, "a.png", W, 200, 400, 600)     # ကျဉ်း
            b = _png(d, "b.png", W, 200, 100, 900)     # ကျယ်
            el = {"anim": [(a, 0, 0)] * 4 + [(b, 0, 0)] + [(a, 0, 0)] * 4}
            x0, x1, iw = DR._xbox(el)
            self.assertEqual((x0, x1), (100, 899), (x0, x1))
            self.assertEqual(iw, 799)

    def test_offset_counted(self):
        with tempfile.TemporaryDirectory() as d:
            a = _png(d, "a.png", 400, 100, 50, 350)
            el = {"anim": [(a, 120, 0)] * 2}
            x0, x1, iw = DR._xbox(el)
            self.assertEqual(x0, 170)
            self.assertEqual(x1, 469)

    def test_empty_is_zero(self):
        with tempfile.TemporaryDirectory() as d:
            a = _png(d, "z.png", 200, 100, 0, 0)
            self.assertEqual(DR._xbox({"anim": [(a, 0, 0)] * 2}), (0, 0, 0))
        self.assertEqual(DR._xbox({"anim": []}), (0, 0, 0))


class Plumbing(unittest.TestCase):
    def setUp(self):
        self.s = io.open(SRC, encoding="utf-8").read()

    def test_width_fit_is_unconditional(self):
        """⚠️ ချုံ့ချက်က `side_room` အကိုင်းရဲ့ **ပြင်ပ**မှာ ရှိရမည်"""
        i_fit = self.s.index("_ox0, _ox1, _iw0 = _xbox(el)")
        i_sr = self.s.index("_sr = side_room(avoid, W)")
        self.assertLess(i_fit, i_sr, "ချုံ့ချက်က ဘေးနေရာ အကိုင်းထဲ ရောက်နေသည်")

    def test_floor_is_070(self):
        """⚠️ ဖတ်ရလွယ်မှု ကြမ်းခင်း — ဘေးနေရာ အကိုင်းနဲ့ အတူတူ"""
        i = self.s.index("_need = _avail / float(_iw0)")
        seg = self.s[i:i + 700]
        self.assertIn("_need >= 0.70", seg)

    def test_margin_is_2pct(self):
        i = self.s.index("_ox0, _ox1, _iw0 = _xbox(el)")
        seg = self.s[i:i + 400]
        self.assertIn('_m0 = max(8, int(W * 0.02))', seg)

    def test_unfittable_is_logged_not_silent(self):
        """⚠️ ချုံ့လည် မဝင်လျှင် **တိတ်တဆိတ် မပြတ်စေရ** — ရေတွက်ပြီး ပြရမည်"""
        self.assertIn('LAST["too_wide"]', self.s)
        self.assertIn("too_wide=0", self.s)
        self.assertIn("fit_w=0", self.s)

    def test_side_branch_reuses_measurement(self):
        """⚠️ အကိုင်းထဲမှာ ထပ်မတိုင်းရ — မိတ္တူ ၂ ခု ကွဲသွားမည်"""
        i = self.s.index("_sr = side_room(avoid, W)")
        seg = self.s[i:i + 2600]
        self.assertNotIn("_np.nonzero(_a0.max(axis=0) > 8)", seg)
        self.assertIn("_sr / float(_iw0)", seg)

    def test_scaled_box_used_for_clamp(self):
        """⚠️ dx ကန့်သတ်ချက်က **gsc ချိန်ပြီး** မှင်နဲ့ တွက်ရမည်"""
        self.assertIn("_ix0, _ix1 = int(_ox0 * gsc), int(_ox1 * gsc)", self.s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
