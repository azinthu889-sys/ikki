# -*- coding: utf-8 -*-
"""Script Editor ရဲ့ **ခန့်မှန်းချက်** — အလိုအလျောက် ဖြတ်ချက်ကိုပါ ထည့်တွက်ရမည်

⚠️⚠️ ၂၀၂၆-၁၀-၀၃ — Descript ရဲ့ 「Shorten all (၂၆)」 နည်းအတိုင်း
   「ဘယ်လောက် ဖြတ်မလဲ · ဘယ်လောက် တိုမလဲ」 ကို **render မလုပ်ခင်** ပြရန်。

ယခင် ကုဒ်က `left = src − sec` ဖြစ်ပြီး `sec` က **သုံးစွဲသူ ဖျက်ချက်ပဲ** —
engine ရဲ့ တိတ်ဆိတ်မှု ဖြတ်ချက် (မြီးမြီး ၁၀၀င်း) ကို **မထည့်တွက်**ခဲ့。
တိုင်းချက် (ဖိုင် ၁၇၈.၇s · vlog · ဖျက်ချက် ၂၀s):
   ယခင် UI : မူရင်း ၂:၅၈ → ခန့်မှန်း **၂:၃၉**
   တကယ်   : မူရင်း ၂:၅၉ → ဖြတ်ပြီး ၁:၄၄ → **၁:၂၄**
⇒ မိနစ် ၃ ဗီဒီယိုမှာ **၇၅ စက္ကန့် လွဲ**ခဲ့သည် — သုံးစွဲသူက အဲဒီကိန်းနဲ့
  အစီအစဉ် ဆွဲသည်。

⚠️ `plan` က `kept` ကို **ပို့ပြီးသား** ဖြစ်ခဲ့သည် — UI က မသုံးခဲ့တာ。
   ဒါက 「ဒေတာ မရှိလို့」 မဟုတ်ဘဲ 「ရှိတာကို မသုံးလို့」 ဖြစ်သော အမှား。
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(__file__)


def _src(*p):
    return io.open(os.path.join(HERE, "..", *p), encoding="utf-8").read()


class Payload(unittest.TestCase):
    def setUp(self):
        self.s = _src("worker", "run.py")

    def test_the_plan_carries_the_two_numbers(self):
        """⚠️ 「ဘယ်လောက် တိုမလဲ」 ပြရုံနဲ့ မလုံလောက် — **ဘာကြောင့်လဲ**
           မပြနိုင်လျှင် သုံးစွဲသူက ဘယ်ခလုတ် ရွှေ့ရမှန်း မသိ。"""
        i = self.s.find("raise ReviewStop(segs, dict(")
        self.assertGreater(i, 0)
        w = self.s[i:i + 2200]
        self.assertIn('min_sil=rc.get("min_sil")', w)
        self.assertIn('keep_pause=rc.get("keep_pause")', w)

    def test_it_already_carried_the_kept_duration(self):
        """⚠️ ဒေတာက ရှိပြီးသား — UI က မသုံးခဲ့တာ"""
        i = self.s.find("raise ReviewStop(segs, dict(")
        w = self.s[i:i + 2200]
        self.assertIn("kept=round(_kept, 2)", w)
        self.assertIn('cuts=int(st.get("cuts", 0))', w)


class Forecast(unittest.TestCase):
    """UI ရဲ့ တွက်ချက်မှုကို **ကုဒ်ထဲက အတိုင်း** ပြန်ပြေးပြီး စစ်သည်"""

    def setUp(self):
        self.s = _src("web", "app.js")

    def _calc(self, plan, sec):
        """`revSum` ရဲ့ တွက်နည်း — ကုဒ်နဲ့ တူညီအောင် ရေးထားသည်"""
        src = float(plan.get("src_dur") or 0)
        eng = float(plan["kept"]) if plan.get("kept") else src
        return src, eng, max(0.0, eng - sec)

    def test_the_automatic_cut_is_subtracted(self):
        """⚠️ **အဓိက** — ဖိုင် ၁၇၈.၇s · engine က ၁၀၃.၉s ချန် · ဖျက် ၂၀s"""
        src, eng, left = self._calc({"src_dur": 178.7, "kept": 103.9}, 20.0)
        self.assertAlmostEqual(left, 83.9, places=1)
        # ယခင် နည်း — ၁၅၈.၇s (၇၅s လွဲ)
        self.assertLess(left, src - 20.0 - 60)

    def test_the_code_uses_kept_not_just_src(self):
        i = self.s.find("var p=state.plan||{}, src=+p.src_dur||0;")
        self.assertGreater(i, 0)
        w = self.s[i:i + 900]
        self.assertIn("p.kept", w)
        self.assertIn("eng - sec", w)
        # ⚠️ ယခင် မှားသော တွက်နည်း ပြန်မဝင်ရ
        self.assertNotIn("Math.max(0, src - sec)", w)

    def test_an_old_plan_without_kept_still_works(self):
        src, eng, left = self._calc({"src_dur": 178.7}, 20.0)
        self.assertAlmostEqual(eng, 178.7, places=1)
        self.assertAlmostEqual(left, 158.7, places=1)

    def test_no_plan_shows_nothing_silly(self):
        src, eng, left = self._calc({}, 20.0)
        self.assertEqual(src, 0.0)
        self.assertEqual(left, 0.0)


class Why(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "app.js")

    def test_the_two_numbers_are_shown_as_a_sentence(self):
        self.assertIn("p.min_sil", self.s)
        self.assertIn("p.keep_pause", self.s)
        self.assertIn("ထက် ရှည်တဲ့ ခဏရပ်ကို", self.s)

    def test_it_degrades_without_them(self):
        """⚠️ plan အဟောင်းနဲ့ ဆိုလျှင် ခန့်မှန်းချက်က ဆက်မှန်ရမည်"""
        i = self.s.find("var why = (p.min_sil!==undefined")
        self.assertGreater(i, 0)
        w = self.s[i:i + 600]
        self.assertIn("p.keep_pause!==undefined)", w)
        self.assertIn(": '';", w)

    def test_it_says_how_many_and_how_much(self):
        """⚠️ Descript ရဲ့ 「Shorten all (၂၆)」 — အရေအတွက်နဲ့ ပမာဏ ၂ ခုလုံး"""
        self.assertIn("p.cuts", self.s)
        self.assertIn("(src-eng).toFixed(0)", self.s)

    def test_both_languages(self):
        i = self.s.find("var why = (p.min_sil!==undefined")
        w = self.s[i:i + 700]
        self.assertIn("pauses over ", w)
        self.assertIn("ထက် ရှည်တဲ့", w)


if __name__ == "__main__":
    unittest.main(verbosity=2)
