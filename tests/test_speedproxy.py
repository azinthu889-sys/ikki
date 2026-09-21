# -*- coding: utf-8 -*-
"""proxy နာမည်က **အရှိန် အလိုက် ကွဲရမည်** — မကွဲလျှင် ၁.၀၃× ကို တိတ်တဆိတ် ကျော်မည်。

⚠️ ၂၀၂၆-၀၉-၂၁ တွေ့ရှိချက် — `{jid}_px.mp4` တစ်ခုတည်း ဖြစ်သဖြင့် ၁.၀၀× နဲ့
   ထုတ်ပြီးသား proxy ရှိနေလျှင် သုံးစွဲသူ ၁.၀၃× ရွေးလိုက်တာကို `_have_px` က
   ဖုံးပြီး retiming လုံးဝ မလုပ်ဘဲ ၁.၀၀× ထွက်ခဲ့မည်。
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "worker"))
sys.path.insert(0, os.path.join(ROOT, "core"))
import run as W          # noqa: E402


class SpeedProxy(unittest.TestCase):

    def test_speeds_differ(self):
        """အရှိန် ၃ မျိုးက ဖိုင် ၃ ခု ဖြစ်ရမည်"""
        names = {W._pxname("j_x", s) for s in (1.0, 1.03, 1.06)}
        self.assertEqual(len(names), 3, "အရှိန် မတူပါလျက် နာမည် တူနေသည်")

    def test_default_keeps_legacy_name(self):
        """၁.၀၀× က အရင်နာမည်ကို ထိန်းရမည် — ရှိပြီးသား proxy ပြန်သုံးရန်"""
        self.assertTrue(W._pxname("j_x", 1.0).endswith("j_x_px.mp4"))
        self.assertTrue(W._pxname("j_x").endswith("j_x_px.mp4"))

    def test_speed_tag(self):
        self.assertTrue(W._pxname("j_x", 1.03).endswith("j_x_px_s103.mp4"))
        self.assertTrue(W._pxname("j_x", 1.06).endswith("j_x_px_s106.mp4"))

    def test_bad_speed_is_default(self):
        """မှားသော တန်ဖိုးက ပုံသေ ဖြစ်ရမည် — ကျဘမ်း မဖြစ်ရ"""
        for bad in (None, "", "abc", 0):
            self.assertTrue(W._pxname("j_x", bad).endswith("j_x_px.mp4"))

    def test_under_big(self):
        """BIG အောက်မှာ ရှိရမည် — Mac ထဲ scratch မဟုတ်"""
        self.assertTrue(W._pxname("j_x", 1.03).startswith(W.BIG))

    def test_pitch_filter_preserves_voice(self):
        """retiming က `atempo` သုံးရမည် — pitch ပြောင်းသော နည်း မဟုတ်"""
        import inspect
        src = inspect.getsource(W.speed_source)
        self.assertIn("atempo", src, "atempo မပါ — pitch ပြောင်းမည်")
        self.assertIn("setpts", src)
        self.assertNotIn("asetrate", src, "asetrate က pitch ပြောင်းသည်")

    def test_only_three_speeds_accepted(self):
        """worker က (1.00 · 1.03 · 1.06) သာ လက်ခံရမည်"""
        import inspect
        src = inspect.getsource(W.handle)
        self.assertIn("(1.0, 1.03, 1.06)", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
