# -*- coding: utf-8 -*-
"""Gemini ဆီ ပို့သော clip ၁၂၀ ထဲ **သက်ဆိုင်သူ အားလုံး** ပါရမည်

⚠️⚠️ ၂၀၂၆-၁၀-၀၁ တိုင်းချက် — knowledge render မှာ `match 0` ဖြစ်ခဲ့ခြင်းရဲ့
   အကြောင်းရင်း。 `broll.match()` က `av[:120]` ကို **index အစဉ်အတိုင်း**
   ယူသည် ⇒ အသစ်/သက်ဆိုင်သူက အောက်ဆုံး ကျသည်:
     index 432 · သက်ဆိုင် 57
     screen() ပြီး 253 · သက်ဆိုင် 46
     av[:120] ထဲ သက်ဆိုင် **19** ⇒ **133 ခု Gemini မမြင်ရ · အဲဒီထဲ
     သက်ဆိုင်သူ 27** (「classroom · students · online · learning」 —
     ဂျပန် ပညာရေး ဗီဒီယိုအတွက် အတိအကျ လိုတဲ့ ရုပ်)
⚠️ ဒီ ချွတ်ယွင်းချက်က **ဒုတိယ အခါ** — ၂၀၂၆-၀၉-၁၇ မှာ ၆၀ ကနေ ၁၂၀ သို့
   တိုးခဲ့ပြီး index ကြီးလာတာနဲ့ ပြန်ဖြစ်သည်。 ကန့်သတ်ချက် တိုးတာက
   ဖြေရှင်းချက် မဟုတ် — **ဆိုင်မှု အရင် စီရမည်** (retrieve-then-rerank)。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import broll as BR   # noqa: E402

SEGS = [{"text": t} for t in (
    "COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ",
    "ကျောင်းသားတွေ စာသင်ခန်းထဲ စာလေ့လာနေပါတယ်",
    "ဂျပန်စာ N5 အောင်လက်မှတ် လိုအပ်ပါတယ်",
    "လေဆိပ်ကနေ ရထားနဲ့ သွားရပါတယ်",
)]
KW_EN = ("student", "classroom", "school", "study", "visa", "passport",
         "airport", "train", "japan", "tokyo", "lecture", "notebook",
         "learning", "graduation", "teacher")
KW_MY = ("ကျောင်းသား", "စာသင်ခန်း", "ကျောင်း", "ဗီဇာ", "လေဆိပ်", "ရထား",
         "ဂျပန်", "မှတ်စု")


def _rel(c):
    my = " ".join(c.get("my") or [])
    en = " ".join(c.get("en") or []).lower()
    return any(k in en for k in KW_EN) or any(k in my for k in KW_MY)


def _clips():
    return (BR.load().get("clips") or [])


class LibraryPresent(unittest.TestCase):
    """⚠️ library မရှိလျှင် အောက်က test တွေ ဘာမှ မစစ်ပါ — အရင် ပြသည်"""

    def test_index_has_clips(self):
        self.assertGreater(len(_clips()), 50)

    def test_some_are_relevant(self):
        self.assertGreater(sum(1 for c in _clips() if _rel(c)), 10)


@unittest.skipIf(len(_clips()) < 50, "B-roll index သေးသည်")
class RelevanceFirst(unittest.TestCase):
    def setUp(self):
        self.av = BR.screen(list(_clips()), log=lambda *a: None)
        self.best = {}
        for c in self.av:
            self.best[c["path"]] = max(
                [BR._score(s["text"], c) for s in SEGS] or [0])

    def _sorted(self):
        return sorted(self.av, key=lambda c: -self.best.get(c["path"], 0))

    def test_index_order_loses_relevant_clips(self):
        """negative control — index အစဉ်က တကယ် လွတ်ကြောင်း အရင် ပြရမည်"""
        total = sum(1 for c in self.av if _rel(c))
        inwin = sum(1 for c in self.av[:120] if _rel(c))
        self.assertGreater(total, 120 and inwin,
                           "index အစဉ်မှာ မလွတ်လျှင် ဒီ test ဘာမှ မစစ်ပါ")

    def test_sorting_brings_them_all_in(self):
        """⚠️⚠️ ၂၀၂၆-၁၀-၀၂ — `_rel` က **ပုံသေ keyword စာရင်း**နဲ့ စစ်ပြီး
        `_score` က **ဝါကျ**နဲ့ စစ်သည် ⇒ 「တိုကျို」 tag ပါပြီး ဝါကျထဲ
        တိုကျို မပါလျှင် `_rel`=True · `_score`=0 ဖြစ်ကာ စစ်ချက်က
        ကုဒ်ကို အပြစ်တင်မိသည်。 ⇒ **တကယ့် ဂုဏ်သတ္တိ** ကို စစ်ရမည်:
        **အမှတ်ရသူ (score > 0) အားလုံး window ထဲ ရောက်ရမည်**。
        (index ၄၃၂ → ၈၃၅ တိုးတော့ အမှတ်ရသူ ၁၃၇ ဖြစ်ပြီး ကန့်သတ် ၁၂၀ ကို
         ကျော်ခဲ့သည် — ကန့်သတ်ချက် တစ်လမ်းသာ တင်တာ အဖြေ မဟုတ်ကြောင်း
         ၆၀ → ၁၂၀ မှာ သင်ခန်းစာ ရပြီးသား)。
        """
        import broll as _BR
        scored = [c for c in self.av if self.best.get(c["path"], 0) > 0]
        win = _BR.window(self.av, self.best)
        inwin = sum(1 for c in win if self.best.get(c["path"], 0) > 0)
        self.assertEqual(inwin, min(len(scored), 240), (inwin, len(scored)))
        # ⚠️ အမှတ် မရသူတွေနဲ့ ၁၂၀ ပြည့်အောင် ဖြည့်ရမည် (ကွဲပြားမှု အတွက်)
        self.assertGreaterEqual(len(win), min(120, len(self.av)))

    def test_top_of_list_is_on_topic(self):
        top = self._sorted()[:5]
        self.assertTrue(any(_rel(c) for c in top),
                        [(c.get("en") or [])[:3] for c in top])

    def test_scored_clips_before_unscored(self):
        srt = self._sorted()
        seen_zero = False
        for c in srt:
            v = self.best.get(c["path"], 0)
            if v == 0:
                seen_zero = True
            elif seen_zero:
                self.fail("score ၀ ပြီးမှ score>0 ပြန်ပေါ်သည်")

    def test_unscored_keep_original_order(self):
        # ⚠️ score ၀ သူများက ယခင် အစဉ်အတိုင်း ကျန်ရမည် (တည်ငြိမ် sort)
        srt = self._sorted()
        zeros = [c["path"] for c in srt if self.best.get(c["path"], 0) == 0]
        orig = [c["path"] for c in self.av if self.best.get(c["path"], 0) == 0]
        self.assertEqual(zeros, orig)


class MatchUsesIt(unittest.TestCase):
    def test_match_sorts_before_the_window(self):
        import io
        src = io.open(os.path.join(os.path.dirname(__file__), "..",
                                   "core", "broll.py"), encoding="utf-8").read()
        # ⚠️ ၂၀၂၆-၁၀-၀၂ — ကန့်သတ်ချက်က `av[:120]` မဟုတ်တော့ဘဲ
        #    `window(av, _best)` ဖြစ်သွားသည် (အမှတ်ရသူ အားလုံး ဝင်ရန်)。
        ix = src.find("_win = window(av, _best)")
        self.assertGreater(ix, 0, "window() ကို မသုံးတော့ဘူးလား")
        head = src[max(0, ix - 1800):ix]
        self.assertIn("retrieve-then-rerank", head)
        self.assertIn("av = sorted(av", head)
        # ⚠️ စီချက်က window ရဲ့ **ရှေ့** မှာ ရှိရမည်
        self.assertLess(src.find("av = sorted(av"), ix)


if __name__ == "__main__":
    unittest.main(verbosity=2)
