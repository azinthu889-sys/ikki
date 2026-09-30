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


class SeqVsDataNumber(unittest.TestCase):
    """`num` အကွက် — အစဉ်လိုက်လား ဒေတာလား ခွဲရမည်

    ⚠️ ၂၀၂၆-၁၀-၀၁ — `"num": num or "1"` ဟု ရေးထားရာ ဝါကျထဲ ကိန်း မပါလျှင်
       **「၁」 တီထွင်** ပေးခဲ့သည်。 ဆိုးကျိုး ၂ ချက်:
         ① `titles2.big_number` · `typo.number_hero` က ကြီးမားသော 「၁」 ပြ
            — ဗီဒီယိုထဲ မရှိသော အချက်
         ② chapter ကတ် ၃ ခုက **၃ ခုလုံး 「၁」** ပြ (အစဉ်လိုက် မဖြစ်)
    """

    SEQ = ("titles.chapter", "prem.chapter", "titles3.chapter_split",
           "qcard.num_point")
    DATA = ("titles2.big_number", "typo.number_hero")
    NO = "COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ"
    HAS = "အချက် ၃ ချက် ရှိပါတယ်"

    def test_data_card_rejected_without_a_number(self):
        for cid in self.DATA:
            self.assertIsNone(P.fill(cid, "number", self.NO), cid)

    def test_data_card_uses_the_real_number(self):
        for cid in self.DATA:
            r = P.fill(cid, "number", self.HAS)
            self.assertIsNotNone(r, cid)
            self.assertEqual(r.get("num"), "၃", cid)

    def test_sequence_cards_count_up(self):
        P.seq_reset()
        got = [(P.fill(c, "section", self.NO) or {}).get("num") for c in self.SEQ]
        self.assertEqual(got, ["01", "02", "03", "04"], got)

    def test_sequence_resets_per_video(self):
        P.seq_reset()
        P.fill(self.SEQ[0], "section", self.NO)
        P.fill(self.SEQ[1], "section", self.NO)
        P.seq_reset()
        self.assertEqual((P.fill(self.SEQ[0], "section", self.NO) or {}).get("num"), "01")

    def test_plan_resets(self):
        # ⚠️ worker က ဗီဒီယို အများ ဆောက်သည် ⇒ `plan()` က reset ရမည်
        import io as _io, os as _os
        src = _io.open(_os.path.join(_os.path.dirname(__file__), "..",
                                     "core", "planner.py"), encoding="utf-8").read()
        ix = src.find("def plan(segs, dur")
        self.assertGreater(ix, 0)
        self.assertIn("seq_reset()", src[ix:ix + 900])


class GfxcatPathToo(unittest.TestCase):
    """⚠️ **topics လမ်းကလည် တီထွင်နေခဲ့သည်** — တစ်လမ်းပဲ ပြင်မိသော အမှား

    `planner.fill` ကိုသာ ပြင်ခဲ့ရာ recipe ၃ ခု (plan=True) မှာသာ ရောက်သည်。
    ကျန် **၁၁ ခု** က `gfxcat.fill` ကို သုံးပြီး အဲဒီမှာ
      `NUMFILL.get(nm, pct if pct is not None else 3)`
    ဟု ရေးထားသဖြင့် နာမည် မသိသော ကိန်း param တိုင်းကို **「၃」 တီထွင်**
    ပေးခဲ့သည် ⇒ ရာခိုင်နှုန်း template ၁၃ ခုမှာ ဖန်သားပြင်ပေါ်
    **「၃%」 အမြဲ** ပြခြင်း。 (Zin မေးမှ တွေ့သည်: 「Talking Head ကိုပဲ
    လုပ်ပေးနေတာ ဟုတ်ရဲ့လား」)
    """

    NO = "အချက် ၃ ချက် ရှိပါတယ်"
    YES = "ကျောင်းသား ၉၅% အောင်ပါတယ်"

    def _pct_entries(self):
        return [e for e in GC.catalog()
                if any(q.get("name") in ("pct", "percent", "ratio")
                       and q.get("required") and not q.get("auto")
                       for q in (e.get("params") or []))]

    def test_entries_exist(self):
        self.assertGreater(len(self._pct_entries()), 5)

    def test_no_invented_percent(self):
        bad = []
        for e in self._pct_entries():
            a = GC.fill(e, self.NO, "ZAE")
            if a is not None:
                bad.append((e["id"], a))
        self.assertEqual(bad, [], "ရာခိုင်နှုန်း တီထွင်မိ: %s" % (bad[:4],))

    def test_real_percent_fills(self):
        ok = sum(1 for e in self._pct_entries()
                 if GC.fill(e, self.YES, "ZAE") is not None)
        self.assertGreater(ok, 0)

    def test_structural_numbers_still_default(self):
        # ⚠️ start · count · secs · h · m · s · n · steps · total က
        #    animation/layout ကိန်း — အကြောင်းအရာ မဟုတ် ⇒ ပုံသေ ရဆဲ
        for nm in ("start", "count", "secs", "h", "m", "s", "n", "steps", "total"):
            self.assertIn(nm, GC.NUMFILL, nm)
        ents = [e for e in GC.catalog()
                if any(q.get("name") in GC.NUMFILL and q.get("required")
                       and not q.get("auto") for q in (e.get("params") or []))]
        if ents:
            self.assertIsNotNone(GC.fill(ents[0], self.NO, "ZAE"), ents[0]["id"])

    def test_content_names_listed(self):
        for nm in ("pct", "percent", "ratio", "value", "target", "num"):
            self.assertIn(nm, GC._CONTENT_NUM, nm)


if __name__ == "__main__":
    unittest.main(verbosity=2)
