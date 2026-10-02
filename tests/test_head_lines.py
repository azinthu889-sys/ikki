# -*- coding: utf-8 -*-
"""ခေါင်းစဉ်ကို **ကြောင်း ခွဲ**ခြင်း (lower3.lt_number)

⚠️⚠️ ၂၀၂၆-၁၀-၀၂ — 「ခေါင်းစဉ် ≥ စာတန်း」 ကို ၁ ကြောင်းနဲ့ **အမြဲ မရနိုင်**。
   panel အကျယ်က ၉:၁၆ မှာ ၆၉၂px သာ (ဘောင်ရဲ့ ၆၄%) ဖြစ်ပြီး စာတန်း `xl` က
   ၁၈၂px ⇒ စာလုံး ၂ လုံးပဲ ဆံ့သည် ⇒ **ကြောင်း ခွဲ**ရသည်。

တိုင်းချက် (ထုတ်လုပ်မှု ဘောင် · `head_phrase` ပြီး ခေါင်းစဉ်):
   ၁၆:၉ · စာတန်း ၁၀၃px — cluster ≤ ၉ ⇒ ၁၀၃ ✓ · cluster ၁၉–၂၂ ⇒ ၅၅–၇၁
   ၉:၁၆ · စာတန်း ၁၈၂px — cluster ၂ ⇒ ၁၈၂ ✓ · ၅ ⇒ ၁၀၆ · ၉ ⇒ ၇၂–၇၄
⇒ ၉:၁၆ မှာ ဝါကျ အရှည်အတွက် 「≥ စာတန်း」 က **ဂျီဟောမက်ထရီအရ မရနိုင်**。
  အဲဒါ လိုလျှင် ခေါင်းစဉ် တိုရမည် (planner) ဒါမှမဟုတ် card template ရမည်。

⚠️ **ကန့်သတ်ချက်ကို စစ်ချက် အဖြစ် မရေးရ** — `test_head_size.py` ရဲ့
   「long headline unchanged」 က အဲဒီ အမှား ဖြစ်ခဲ့သည် (ကုဒ် ကောင်းလာတော့
   စစ်ချက် ကျသည်)。 ဤမှာ **ရည်မှန်းချက်** ကို စစ်သည်: စကားလုံး မပျောက်ရ ·
   အရွယ် တက်ရ · panel က ဘောင်ရဲ့ ၁/၃ မကျော်ရ。
"""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
MK = ("/Applications/my file/My bussiness/ZAE NEW　OPERATION/"
      "N8N Work Flow/n8n All Workflow/motionkit")
SRC = os.path.join(MK, "lower3.py")


def _fit(title, size=None, tag=None):
    cwd = os.getcwd()
    if MK not in sys.path:
        sys.path.insert(0, MK)
    os.chdir(MK)
    try:
        import lower3
        lower3.lt_number(tag or ("L%d_%s" % (len(title), size)), "1", title,
                         dur=1.0, size=size)
        return dict(getattr(lower3, "LAST_FIT", {}) or {})
    finally:
        os.chdir(cwd)


@unittest.skipUnless(os.path.isdir(MK), "motionkit မရှိ")
class Lines(unittest.TestCase):
    ONE = "ဗီဇာ"
    TWO = "N5 အောင်လက်မှတ်"
    FIVE = "COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ"

    def test_short_stays_one_line(self):
        f = _fit(self.ONE, 182)
        self.assertEqual(f.get("lines"), 1, f)
        self.assertEqual(f.get("size"), 182, f)

    def test_two_token_splits(self):
        f = _fit(self.TWO, 182)
        self.assertGreaterEqual(f.get("lines", 1), 2, f)
        self.assertEqual(f.get("tok_kept"), f.get("tok_all"), f)

    def test_five_token_keeps_every_word(self):
        f = _fit(self.FIVE, 182)
        self.assertEqual(f.get("tok_kept"), f.get("tok_all"), f)
        self.assertGreaterEqual(f.get("lines", 1), 2, f)

    def test_panel_within_one_third(self):
        """⚠️ panel က ဘောင်ရဲ့ ၁/၃ ကျော်လျှင် lower third မဟုတ်တော့ —
           ပထမ စမ်းချက်မှာ ၅၁% အထိ ချဲ့ခဲ့ (Zin:「ပုံတုံးတယ်」)。"""
        for t in (self.ONE, self.TWO, self.FIVE):
            f = _fit(t, 182)
            self.assertLessEqual(f["bh"], int(f["h"] / 3.0) + 2,
                                 (t[:16], f["bh"], f["h"]))

    def test_no_size_keeps_old_path(self):
        f = _fit(self.ONE)
        self.assertLess(f.get("size", 999), 182, f)

    def test_fit_budget_is_92pct(self):
        """⚠️ `infogfx.T()` က `w*0.92` ကျော်လျှင် ကိုယ်တိုင် ချုံ့သည် ⇒
           ဆံ့မဆံ့ကို `tw` နဲ့ စစ်လျှင် နောက်ဆုံး ဆွဲချိန် အရွယ် ပြောင်းမည်。"""
        f = _fit(self.TWO, 182)
        self.assertIn("lim", f)
        self.assertLess(f["lim"], f["tw"], f)
        self.assertLessEqual(f["wide"], f["lim"], f)

    def test_every_line_same_size(self):
        # ကုဒ်ဘက် စစ်ချက် — ကြောင်းအားလုံးကို `hs` တစ်ခုတည်းနဲ့ ဆွဲရမည်
        s = io.open(SRC, encoding="utf-8").read()
        self.assertIn("def _draw(ls, size):", s)
        ix = s.find("def _draw(ls, size):")
        self.assertIn("for _i, _t in enumerate(ls)", s[ix:ix + 300])

    def test_clip_id_is_per_line(self):
        """⚠️ clipPath id ထပ်လျှင် နောက်ကြောင်းက ရှေ့ကြောင်းရဲ့ clip ကို
           ယူပြီး **မပေါ်**ပါ。"""
        s = io.open(SRC, encoding="utf-8").read()
        self.assertIn('cid = f"{tag}c{i}_{_ii}"', s)
        self.assertNotIn("'k' if png is kk else 'h'", s)

    def test_refuses_when_meaning_lost(self):
        """⚠️ စကားလုံး သုံးပုံတစ်ပုံထက် ပိုပျောက်လျှင် **ပယ်**ရမည် —
           ၆ လုံးကနေ ၂ လုံး ပြတာက ဖတ်ရပေမယ့် အဓိပ္ပာယ် လွဲသည်。"""
        long_t = ("ဂျပန်မှာ အလုပ် ရှာဖွေခြင်း အတွက် "
                  "လိုအပ်သော အချက်များ")
        try:
            f = _fit(long_t, 182)
        except Exception as e:
            self.assertIn("lt_number", str(e))
            return
        # ပယ်မလျှင် စကားလုံး မပျောက်ရ
        self.assertEqual(f.get("tok_kept"), f.get("tok_all"), f)

    def test_split_only_at_spaces(self):
        s = io.open(SRC, encoding="utf-8").read()
        ix = s.find("def _split(t, size, nl):")
        self.assertGreater(ix, 0)
        seg = s[ix:ix + 1400]
        self.assertIn("str(t).split()", seg)
        self.assertIn("itertools.combinations", seg)

    def test_measure_matches_draw_font(self):
        """⚠️ `_mw` က `txt()` နဲ့ **အတူတူ** ဖောင့်/အရွယ် ပြောင်းရမည်。"""
        s = io.open(SRC, encoding="utf-8").read()
        ix = s.find("def _mw(t, size):")
        self.assertGreater(ix, 0)
        seg = s[ix:ix + 900]
        self.assertIn("P.MM_SCALE", seg)
        self.assertIn("P.MM_MAP", seg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
