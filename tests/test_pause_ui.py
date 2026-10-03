# -*- coding: utf-8 -*-
"""「ဘယ်လောက် ဖြုတ်မလဲ」 ခလုတ်က **သုံးစွဲသူဆီ ရောက်ရမည်**

⚠️⚠️ Zin ၂၀၂၆-၁၀-၀၃ လက္ခဏာ ③: 「ဖြုတ်တာ များလွန်း/နည်းလွန်း」。
   တိုင်းချက် (ဖိုင် ၁၇၈.၇s · မူရင်းရဲ့ ၆၁% က တိတ်ဆိတ်မှု):
     `cut` ညင်သာ→ပြတ်သား : ဖြုတ်မှု ၃၉→၄၆% (**၇ မှတ်**) ·
                            ဖြတ်ချက် ၁၇→၄၃ (**၂.၅ ဆ**)
     `pause` max→keep     : ဖြုတ်မှု ၄၅→၁၈% · **ဖြတ်ချက် ၂၃ အမြဲ**
   ⇒ **မေးခွန်း ၂ ခု · ခလုတ် ၂ ခု**。 ရောထားလျှင် သုံးစွဲသူက မှားတဲ့
     ခလုတ်ကို ရွှေ့နေမည် — ဒါက တကယ် ဖြစ်ခဲ့သော အမှား。

⚠️ ဘောင်/ရွေးစရာကို UI ထဲ **ကိန်းသေ မရေးရ** — API ကနေပဲ လာရမည်
   (၂၀၂၆-၁၀-၀၁ မှာ slider ရဲ့ ကန့်သတ်ချက် ကိန်းသေ ရေးထားခဲ့၍ ပုံစံ ၄ ခုရဲ့
   ပုံသေကို ပြလို့ မရခဲ့)。
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "core"))


def _src(*p):
    return io.open(os.path.join(HERE, "..", *p), encoding="utf-8").read()


class Api(unittest.TestCase):
    def setUp(self):
        self.s = _src("api", "main.py")

    def test_the_options_are_sent(self):
        self.assertIn('"pauses": [{"id": k, "my": v[0], "en": v[1]}', self.s)
        self.assertIn("RC.PAUSE_LABEL.items()", self.s)

    def test_it_sits_next_to_the_cut_options(self):
        """⚠️ တစ်နေရာတည်းက လာမှ ၂ ခုလုံး ပြမလား မပြမလား ကွဲမှု မရှိ"""
        a = self.s.find('"cuts": [{"id": k')
        b = self.s.find('"pauses": [{"id": k')
        self.assertGreater(a, 0)
        self.assertGreater(b, a)
        self.assertLess(b - a, 900, "ဝေးလွန်းသည် — တွဲမနေတော့")


class Web(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "app.js")

    def test_the_options_are_read_from_the_api(self):
        """⚠️ UI ထဲ ကိန်းသေ မရေးရ"""
        self.assertIn("PAUSEOPT = sd.pauses || []", self.s)
        self.assertNotIn('"အသက်ရှုခွင့် ချန်"', self.s)

    def test_the_select_is_rendered_and_bound(self):
        self.assertIn('id="adjpause"', self.s)
        self.assertIn("ADJ.pause=e.target.value", self.s)

    def test_it_shows_the_current_value(self):
        """⚠️ ပုံသေကို မပြနိုင်လျှင် သုံးစွဲသူက ဘာကနေ ရွှေ့ရမှန်း မသိ"""
        i = self.s.find("var popt=(PAUSEOPT||[])")
        self.assertGreater(i, 0)
        w = self.s[i:i + 300]
        self.assertIn("ADJ.pause||d.pause", w)

    def test_it_degrades_when_the_api_is_older(self):
        """⚠️ `pauses` မပါသော API နဲ့ ဆိုလျှင် **မပြရ** — မရှိတဲ့ feature ကို
           ခလုတ်နဲ့ ကတိ မပေးရ。"""
        i = self.s.find("id=\"adjpause\"")
        w = self.s[max(0, i - 800):i]
        self.assertIn("(popt ?", w)

    def test_the_label_says_what_it_does_not_do(self):
        """⚠️ `cut` နဲ့ ဘာကွာလဲ မပြောလျှင် ၂ ခုလုံး ရှိတာက ပိုရှုပ်စေမည်"""
        self.assertIn("ဖြတ်ချက် အရေအတွက် မပြောင်းပါ", self.s)


class EndToEnd(unittest.TestCase):
    def test_the_value_survives_the_whole_chain(self):
        """UI ရွေးချက် → `over` → `clean()` → `apply()` → engine ကိန်း"""
        import recipes as RC
        for k, (a, b) in RC.PAUSES.items():
            kept = RC.clean({"pause": k})
            self.assertEqual(kept.get("pause"), k, k)
            r = RC.apply("short-916", {"pause": k})
            self.assertAlmostEqual(r["pause_ratio"], a, msg=k)
            self.assertAlmostEqual(r["pause_max"], b, msg=k)

    def test_every_option_the_api_offers_actually_works(self):
        """⚠️ ပြထားပြီး အလုပ် မလုပ်တာက အဆိုးဆုံး"""
        import recipes as RC
        for k in RC.PAUSE_LABEL:
            self.assertIn(k, RC.PAUSES, k)
            self.assertEqual(RC.clean({"pause": k}).get("pause"), k, k)

    def test_a_bad_value_is_dropped_not_crashed(self):
        import recipes as RC
        self.assertNotIn("pause", RC.clean({"pause": "zzz"}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
