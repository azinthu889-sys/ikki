# -*- coding: utf-8 -*-
"""ခေါင်းစဉ်က စာရင်းကို **ပြန်ဆိုမနေ** ရန်

⚠️ ၂၀၂၆-၀၉-၂၉ တွေ့ချက် — `callouts.side_note` က
     ခေါင်းစဉ် 「COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ။」
     စာရင်း ၁ 「COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ။ အေဂျင်စီကောင်း တစ်ခု」
   ⇒ ဝါကျ ၂ ခု ကနေ စာသား ၃ ခု ထွက်ပြီး ခေါင်းစဉ်က စာရင်း ၁ ရဲ့ **အထဲမှာ**
     အပြည့် ပါနေသည်。 `split2` က space နေရာမှာ ခွဲ၍ ဝါကျကိုပါ **အလယ်မှာ
     ဖြတ်**ခဲ့သည် (「အေဂျင်စီကောင်း တစ်ခု」 / 「လိုအပ်ပါတယ်။」)。
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import planner as P  # noqa: E402

T3 = ("COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ။ အေဂျင်စီကောင်း တစ်ခု လိုအပ်ပါတယ်။ "
      "ပြီးတော့ စာမေးပွဲ အောင်လက်မှတ် ရှိရပါမယ်။")
T2 = "COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ။ အေဂျင်စီကောင်း တစ်ခု လိုအပ်ပါတယ်။"
T1 = "COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပြီး အေဂျင်စီကောင်း တစ်ခု လိုအပ်ပါတယ်"


class Sents(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(P.sents(T3)), 3)
        self.assertEqual(len(P.sents(T2)), 2)
        self.assertEqual(len(P.sents(T1)), 1)

    def test_no_punct_left(self):
        for one in P.sents(T3):
            self.assertNotIn("။", one, "ဝါကျဆုံး ကို ဖြုတ်ရမည်")
            self.assertTrue(one.strip())

    def test_short_tail_merges(self):
        # ⚠️ 「ဟုတ်ကဲ့။」 တစ်ခုတည်း ဝါကျ မဖြစ်ရ — ရှေ့ဝါကျ နဲ့ ပေါင်းရမည်
        v = P.sents("အေဂျင်စီကောင်း တစ်ခု လိုအပ်ပါတယ်။ ဟုတ်ကဲ့။")
        self.assertEqual(len(v), 1, v)

    def test_empty(self):
        self.assertEqual(P.sents(""), [])
        self.assertEqual(P.sents(None), [])


class Clauses(unittest.TestCase):
    """「၊」 က တကယ့် ပုဒ်ထီး မဟုတ် ⇒ ပုံသေမှာ မခွဲရ"""

    CL = "ကိုယ်ပိုင်မှတ် တင်ရမယ်၊ ဘက်ထာတ်စာ လိုမယ်၊ လုပ်ငှှန်းခ ရှိရပာမယ်။"

    def test_default_keeps_one(self):
        # ပုံသေမှာ 「၊」 မခွဲ ⇒ ဝာကျ တစ်ခု
        self.assertEqual(len(P.sents(self.CL)), 1)

    def test_clause_mode_splits(self):
        self.assertEqual(len(P.sents(self.CL, clauses=True)), 3)

    def test_fill_uses_clauses_when_one_sentence(self):
        # ⚠️ ဝာကျ တစ်ခုတည်း ပေမယ့် ပုဒ်ဖြတ် ့ ခု ပိုင်းရ ⇒ ကတ် ထွက်ရမည်
        r = P.fill("callouts.side_note", "checklist", self.CL)
        self.assertIsNotNone(r, "ပုဒ်ဖြတ် ့ ခု ⇒ ကတ် ရရမည်")
        tv = next((r[k] for k in P._TITLE_K if k in r), "")
        lv = next((r[k] for k in P._LIST_K if k in r), None)
        self.assertEqual(len(lv), 2)
        self.assertFalse(P.dup_title(tv, lv), (tv, lv))

    def test_two_clauses_still_rejected(self):
        # ပုဒ်ဖြတ် ံ ခုပဲ ⇒ ခောင်းစင် + စာရင်း ၁ ခု ⇒ မလုံလောက် ⇒ ပယ်
        two = "ကိုယ်ပိုင်မှတ် တင်ရမယ်၊ ဘက်ထာတ်စာ လိုမယ်။"
        self.assertEqual(len(P.sents(two, clauses=True)), 2)
        self.assertIsNone(P.fill("callouts.side_note", "checklist", two))


class DupTitle(unittest.TestCase):
    def test_substring_caught(self):
        self.assertTrue(P.dup_title("COE စိတ်ချရတဲ့ Class",
                                    ["COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ"]))

    def test_reverse_caught(self):
        # စာရင်းက ခေါင်းစဉ် ထဲ ပါလျှင်လည် ထပ်တာပါ
        self.assertTrue(P.dup_title("COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ",
                                    ["COE စိတ်ချရတဲ့ Class"]))

    def test_space_insensitive(self):
        # ⚠️ `split2` က space နေရာမှာ ခွဲ၍ space ပါလျှင် substring မမိပါ
        self.assertTrue(P.dup_title("အေဂျင်စီ ကောင်း", ["အေဂျင်စီကောင်း တစ်ခု"]))

    def test_distinct_ok(self):
        self.assertFalse(P.dup_title("COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ",
                                     ["အေဂျင်စီကောင်း တစ်ခု လိုအပ်ပါတယ်"]))

    def test_short_title_never_dup(self):
        # ၆ လုံး အောက် က ဘယ်စာရင်းထဲမှာမဆို ပါနိုင် ⇒ မစစ်ပါ
        self.assertFalse(P.dup_title("N5", ["N5 အောင်လက်မှတ် လိုပါတယ်"]))

    def test_pair_rows(self):
        # rows က (အညွှန်း, ကိန်း) အတွဲ ⇒ အညွှန်း ကိုသာ နှိုင်းရမည်
        self.assertTrue(P.dup_title("ကျောင်းလခ", [["ကျောင်းလခ စုစုပေါင်း", 240]]))
        self.assertFalse(P.dup_title("နှစ်စဉ် ကုန်ကျစရိတ်", [["ကျောင်းလခ", 240]]))


class FillSideNote(unittest.TestCase):
    """`callouts.side_note` = title + lines ⇒ တကယ့် ပြင်ချက် ဒီမှာ မြင်ရမည်"""

    CID = "callouts.side_note"

    def _one(self, text):
        r = P.fill(self.CID, "checklist", text)
        if not r:
            return None, None
        tv = next((r[k] for k in P._TITLE_K if k in r), "")
        lv = next((r[k] for k in P._LIST_K if k in r), None)
        return tv, lv

    def test_three_sents_not_dup(self):
        tv, lv = self._one(T3)
        self.assertIsNotNone(lv, "၃ ဝါကျ ⇒ ကတ် ရရမည်")
        self.assertFalse(P.dup_title(tv, lv), (tv, lv))
        self.assertEqual(len(lv), 2, "ခေါင်းစဉ် ၁ + စာရင်း ၂")

    def test_lines_are_whole_sentences(self):
        # ⚠️ `split2` က ဝါကျကို **အလယ်မှာ** ဖြတ်ခဲ့သည် ⇒ မဖြစ်ရ
        _, lv = self._one(T3)
        for one in lv:
            self.assertNotIn("။", one)
            self.assertTrue(len(one.split()) >= 2, one)

    def test_two_sents_one_item(self):
        tv, lv = self._one(T2)
        self.assertIsNotNone(lv)
        self.assertEqual(len(lv), 1)
        self.assertFalse(P.dup_title(tv, lv), (tv, lv))

    def test_one_sent_rejected(self):
        # ⚠️ ဝါကျ တစ်ခုတည်း ကနေ ခေါင်းစဉ်+စာရင်း ခွဲလို့ **မရ** ⇒ ပယ်ရမည်
        tv, lv = self._one(T1)
        self.assertIsNone(lv, "ဝါကျ ၁ ခု ⇒ ပယ်ရမည် (%r / %r)" % (tv, lv))


class NoRegression(unittest.TestCase):
    """ခေါင်းစဉ်သာ / စာရင်းသာ လိုသူကို **မထိရ**"""

    def test_title_only_unchanged(self):
        # `title` တစ်ခုသာ လိုသူ ⇒ အရင်အတိုင်း `_short(text, 24)`
        r = P.fill("titles2.big_number", "number", "ကျောင်းသား ၂၄၀ ယောက် ရှိပါတယ်")
        if r and "title" in r:
            self.assertEqual(r["title"], P._short("ကျောင်းသား ၂၄၀ ယောက် ရှိပါတယ်", 24))

    def test_list_only_gets_split2(self):
        # `items` တစ်ခုသာ လိုသူ ⇒ `split2` အတိုင်း ၂ ကြောင်း
        r = P.fill("thm.list_tick", "checklist", T1)
        if r:
            lv = next((r[k] for k in P._LIST_K if k in r), None)
            if lv is not None:
                self.assertEqual(len(lv), len(P.split2(T1)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
