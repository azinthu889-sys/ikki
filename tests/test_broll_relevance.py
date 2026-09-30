# -*- coding: utf-8 -*-
"""B-roll က ဇာတ်လမ်းနဲ့ **ဆိုင်ရမည်** — မဆိုင်တာ ထည့်တာထက် မထည့်တာ သာ

⚠️⚠️ ၂၀၂၆-၁၀-၀၁ တိုင်းချက် (knowledge · ပို့တဲ့အတိုင်း render):
     B-roll · ရုပ်အရည် မမီ၍ ဖယ် 177 ခု
     B-roll · လိုက်ဖက်သော clip 10 / 253 ခု (Gemini)
     B-roll တွဲမှု · **match 0** · **ကျပန်း ဖြည့် 6**
     2.40 · 8.40 · 14.40 · 20.40 · 26.40 · 32.40s  ← ၆ စက္ကန့် တစ်ခါ
     အားလုံး ၃.၀s · အားလုံး တူညီသော folder
   ဗီဒီယိုက ဂျပန် ပညာရေး (COE · N5 · အေဂျင်စီ · ကျောင်းလခ)、library က
   ကား · abstract motion · office stock ⇒ **ဆိုင်စရာ မရှိ**。
   ⇒ `match 0` က matcher ပျက်တာ **မဟုတ်** — library မှာ အကြောင်းအရာ မရှိတာ。
⚠️ `broll_strict` က headtop · ref-talk · short-916 ၃ ခုမှာ ဖွင့်ပြီးသား ဖြစ်ပြီး
   B-roll သုံးသော အခြား ၆ ခုမှာ **မဖွင့်ခဲ့** ⇒ အဲဒီ ၆ ခုက ကျပန်း ဖြည့်သည်။
"""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import recipes as RC   # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _worker_src():
    return io.open(os.path.join(ROOT, "worker", "run.py"), encoding="utf-8").read()


class StrictOnByDefault(unittest.TestCase):
    def test_every_broll_style_is_strict(self):
        bad = [k for k in sorted(RC.R)
               if (RC.get(k).get("broll") or 0) > 0
               and not RC.get(k).get("broll_strict")]
        self.assertEqual(bad, [], "ကျပန်း ဖြည့် ခွင့်ပြုနေသူ: %s" % (bad,))

    def test_at_least_six_styles_use_broll(self):
        # ⚠️ ၀ ဆိုလျှင် အပေါ်က test ဘာမှ မစစ်ပါ
        n = sum(1 for k in RC.R if (RC.get(k).get("broll") or 0) > 0)
        self.assertGreaterEqual(n, 6, n)

    def test_can_be_turned_off_per_style(self):
        # ⚠️ တိုင်းထားသော look အတွက် ပြန်ပိတ်နိုင်ရမည် (BOUNDS ထဲ ရှိ)
        self.assertIn("broll_strict", RC.BOUNDS)
        self.assertFalse(RC.apply("knowledge", {"broll_strict": 0})["broll_strict"])

    def test_explicit_true_survives(self):
        self.assertTrue(RC.apply("headtop", {})["broll_strict"])

    def test_default_applies_through_apply_too(self):
        # ⚠️ `_expand()` က `get()` ရော `apply()` ရော ကနေ ခေါ်ရသည် —
        #    တစ်ခုတည်းမှာ ထားလျှင် သုံးစွဲသူ ပြင်ချက် ပေါင်းပြီးနောက် ပျောက်မည်
        self.assertTrue(RC.apply("vlog", {"gfx": 8})["broll_strict"])


class NeedIsDeclared(unittest.TestCase):
    """match ၀ ဆိုလျှင် **ဘာ footage လိုလဲ** ပြောရမည် ([[sourcing-first-rule]])"""

    def test_worker_declares_the_gap(self):
        src = _worker_src()
        self.assertIn("B-roll လိုအပ်ချက်", src)
        self.assertIn('REPORT["broll_need"]', src)

    def test_guarded_on_match_zero_only(self):
        src = _worker_src()
        ix = src.find("B-roll လိုအပ်ချက်")
        self.assertGreater(ix, 0)
        head = src[max(0, ix - 900):ix]
        self.assertIn("if not _m and nb:", head)


if __name__ == "__main__":
    unittest.main(verbosity=2)
