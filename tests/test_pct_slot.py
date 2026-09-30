# -*- coding: utf-8 -*-
"""ရာခိုင်နှုန်း အကွက်ကို **ဘယ်ကိန်းမဆို** နဲ့ မဖြည့်ရ

⚠️ ၂၀၂၆-၁၀-၀၁ တွေ့ချက် — `planner.fill` က `"pct": num or ""` ဟု ရေးထားရာ
   ဝါကျထဲက ပထမ ကိန်းကို ရာခိုင်နှုန်း အကွက်ထဲ ထည့်ခဲ့သည်:
     「အချက် ၃ ချက် ရှိပါတယ်」   ⇒ gauge က **၃%**
     「ကျောင်းလခ ယန်း ၆၈၀၀၀၀」 ⇒ **၆၈၀၀၀၀%**
   ဖန်သားပြင်ပေါ် **မဟုတ်သော အချက်** တင်လိုက်တာ — ကိန်းက အမှန်၊
   အဓိပ္ပာယ်က အမှား ⇒ ကိန်း တီထွင်တာထက် ဆိုးသည်。
   ရာခိုင်နှုန်း လိုသော template ၁၃ ခု · plan လမ်းက ၁၂ ခု ထိသည်。
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import planner as P   # noqa: E402
import gfxcat as GC   # noqa: E402


class PctOf(unittest.TestCase):
    def test_plain_count_rejected(self):
        self.assertIsNone(P.pct_of("အချက် ၃ ချက် ရှိပါတယ်"))

    def test_money_rejected(self):
        self.assertIsNone(P.pct_of("ကျောင်းလခ ယန်း ၆၈၀၀၀၀"))

    def test_year_rejected(self):
        self.assertIsNone(P.pct_of("၂၀၂၆ မှာ ဖွင့်ပါမယ်"))

    def test_burmese_percent_sign(self):
        self.assertEqual(P.pct_of("ကျောင်းသား ၉၅% အောင်ပါတယ်"), "၉၅")

    def test_space_before_sign(self):
        self.assertEqual(P.pct_of("ဝင်ခွင့် 87 % ရပါတယ်"), "87")

    def test_burmese_word(self):
        self.assertEqual(P.pct_of("ရာခိုင်နှုန်း ၄၂ ဖြစ်ပါတယ်"), "၄၂")

    def test_word_after_number(self):
        self.assertEqual(P.pct_of("အောင်ချက် ၉၅ ရာခိုင်နှုန်း"), "၉၅")

    def test_over_100_rejected(self):
        # ⚠️ gauge/ring က ၁၀၀ မှာ ဆုံးသည် ⇒ ၁၂၀% ပြလျှင် widget ကျော်မည်
        self.assertIsNone(P.pct_of("၁၂၀% တိုးလာပါတယ်"))

    def test_picks_the_one_beside_the_sign(self):
        # ⚠️ ပထမ ကိန်း မဟုတ်ဘဲ % နဲ့ တွဲသူကို ယူရမည်
        self.assertEqual(P.pct_of("ကျောင်းသား ၂၄၀ ထဲ ၉၅% အောင်"), "၉၅")

    def test_empty(self):
        self.assertIsNone(P.pct_of(""))
        self.assertIsNone(P.pct_of(None))


class FillGuards(unittest.TestCase):
    def _pct_ids(self):
        return [e["id"] for e in GC.catalog()
                if any(q.get("name") in ("pct", "percent", "ratio")
                       and q.get("required") and not q.get("auto")
                       for q in (e.get("params") or []))]

    def test_templates_exist(self):
        # ⚠️ ၀ ဆိုလျှင် အောက်က loop ဘာမှ မစစ်ပါ
        self.assertGreater(len(self._pct_ids()), 5)

    def test_no_card_from_a_plain_count(self):
        bad = []
        for cid in self._pct_ids():
            try:
                r = P.fill(cid, "number", "အချက် ၃ ချက် ရှိပါတယ်")
            except Exception:
                continue
            if r and str(r.get("pct") or r.get("percent") or r.get("ratio") or ""):
                bad.append((cid, r))
        self.assertEqual(bad, [], "ကိန်း သက်သက်ကနေ ရာခိုင်နှုန်း ထုတ်မိ: %s" % (bad,))

    def test_real_percent_still_works(self):
        ok = 0
        for cid in self._pct_ids():
            try:
                r = P.fill(cid, "number", "ကျောင်းသား ၉၅% အောင်ပါတယ်")
            except Exception:
                continue
            if r and str(r.get("pct") or ""):
                ok += 1
        self.assertGreater(ok, 0, "တကယ့် ရာခိုင်နှုန်း နဲ့လည် ကတ် မရ")


class LatinDigits(unittest.TestCase):
    def test_converts(self):
        self.assertEqual(P._latin_digits("၉၅"), "95")
        self.assertEqual(P._latin_digits("87"), "87")
        self.assertEqual(P._latin_digits("၄၂.၅"), "42.5")


if __name__ == "__main__":
    unittest.main(verbosity=2)
