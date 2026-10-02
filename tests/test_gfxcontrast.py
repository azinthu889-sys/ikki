# -*- coding: utf-8 -*-
"""စာသား ဖတ်နိုင်မှု ဂိတ် (`tools/gfxcontrast.py`) ရဲ့ ဖွဲ့စည်းပုံ စစ်ချက်

⚠️ ဤဂိတ်က ၂၀၂၆-၁၀-၀၂ မှာ **ငါ့ကို ပြန်တည့်မတ်ပေး**ခဲ့သည် — render ဖရိမ်းကနေ
   「၁.၇၅:၁ ⇒ မဖတ်နိုင်」 ဟု ငါ တိုင်းခဲ့ပြီး ဂိတ်က ၁၈.၉:၁ ပြသည်。 ဂိတ်က မှန်သည် —
   ငါ ဝင်လာစ ဖရိမ်း (+၀.၆s) ကို ယူမိခြင်း ဖြစ်သည် ([[ikki-settled-frame-rule]])。

⚠️ ဖမ်းမိခဲ့သော ချွတ်ယွင်းချက် ၃ ခု (ဤစစ်ချက်တွေက ထပ်မဖြစ်စေရန်) —
   ① ကလေး process က **motionkit ဖိုလ်ဒါသို့ မပြောင်း**လျှင် PNG တွေက
      `~/ikki/work` ထဲ ရောက်ပြီး `rp()` က `G.MK` ကို ရှာသဖြင့် ဖရိမ်း
      တစ်ခုမှ မတိုင်းဖြစ်ဘဲ 「မှင် မလုံလောက်」 ထွက်သည်。
   ② `scipy` **မရှိ**ပါ — dependency မတိုးရ ⇒ numpy သာ သုံးရသည်。
   ③ alpha က စာသားနဲ့ ကတ်အခွံကို **မခွဲနိုင်** (၂ ခုလုံး alpha ၁.၀) ⇒
      အလင်းပိတ် ကွက်အတွင်းက အလင်း ဖွဲ့စည်းပုံနဲ့ တိုင်းရသည်。
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "tools", "gfxcontrast.py")


class Shape(unittest.TestCase):
    def setUp(self):
        self.s = io.open(SRC, encoding="utf-8").read()

    def test_child_compiles(self):
        import importlib.util as iu
        sp = iu.spec_from_file_location("_gc", SRC)
        m = iu.module_from_spec(sp)
        sp.loader.exec_module(m)
        compile(m.CHILD, "<child>", "exec")

    def test_chdir_before_build(self):
        """⚠️ chdir က **ဆောက်ခြင်းရဲ့ ရှေ့** မှာ ရှိရမည်"""
        i_cd = self.s.index("os.chdir(G.MK)")
        i_build = self.s.index("el = DR._call_template")
        self.assertLess(i_cd, i_build, "chdir က ဆောက်ခြင်း နောက်မှာ ရှိနေသည်")

    def test_no_scipy_import(self):
        """⚠️ scipy မရှိပါ — dependency မတိုးရ"""
        self.assertNotIn("import scipy", self.s)
        self.assertNotIn("from scipy", self.s)

    def test_uses_ikki_colours_first(self):
        """⚠️ demoargs က template ရဲ့ ကိုယ်ပိုင် အရောင် ⇒ IKKI ပို့သော
           accent/ink/dim နဲ့ အရင် တိုင်းရမည်"""
        i_tf = self.s.index("kw = DR._tf_args(")
        i_demo = self.s.index("import demoargs as _DA")
        self.assertLess(i_tf, i_demo)

    def test_measures_inside_solid_blocks(self):
        self.assertIn("solid = al >= 0.90", self.s)
        self.assertIn("full = Sf.all(axis=1)", self.s)

    def test_median_not_extremes(self):
        """⚠️ အဆိုးဆုံး = noise · အကောင်းဆုံး = ဝါရောင် ဂဏန်း တစ်ခုက
           ကတ် တစ်ခုလုံးကို အောင်စေမည် ⇒ အလယ်မှတ်"""
        self.assertIn("r = float(np.median(rr))", self.s)

    def test_threshold_named(self):
        self.assertIn("MIN_RATIO = 3.0", self.s)

    def test_writes_only_with_cache(self):
        self.assertIn("gfx_contrast_%s.json", self.s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
