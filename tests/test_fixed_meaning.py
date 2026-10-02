# -*- coding: utf-8 -*-
"""**အဓိပ္ပာယ် သတ်မှတ်ပြီးသား** template ကို ယေဘုယျ ဝါကျအတွက် မရွေးရ

⚠️⚠️ ၂၀၂၆-၁၀-၀၂ short-916 render — ငွေလွှဲ အကြောင်း ဝါကျ (၁၆.၂s) မှာ
   `prem3.countdown`「၃ · ၂ · ၁ စတော့မယ်」ရွေးမိပြီး ဘောင်အပြည့် အမှောင်နဲ့
   ပြောသူကို ဖုံးခဲ့သည် — ရေတွက်ဆင်းစရာ ဘာမှ မရှိပါ。

ဘာကြောင့် — Gemini က **template မရွေးပါ**。 ဝါကျကို အမျိုးအစား ၁၁ မျိုး
ခွဲပေးရုံပြီး IKKI က pool ကနေ ရွေးသည်。 `_profile_candidates` က
label-specific စာရင်းနောက်မှာ **ယေဘုယျ `fact` pool တစ်ခုလုံး** ဆက်တွဲသဖြင့်
(ဂရပ်ဖစ် နည်းတာ ပြင်ရန် ၂၀၂၆-၀၉-၂၅ မှာ တမင် လုပ်ထားခြင်း) label က
**အစီအစဉ်သာ ပြောင်းပြီး ကန့်သတ် မပေးပါ**。

⚠️ စာရင်းကို catalog ရဲ့ **ကိုယ်ပိုင် `label_en`** ကနေ ဆောက်သည် (ဒီဇိုင်နာ
   ကိုယ်တိုင် ပေးထားသော အမည်) — မှန်းချက် မဟုတ်။ နာမည်နဲ့ **arg ပုံစံ**
   မှန်းလို့ မရပေမယ် **အဓိပ္ပာယ်** က အမည်ထဲမှာ ရှိသည်。
⚠️ **လမ်းကြောင်း ၂ ခုလုံး** စစ်ရမည် — `planner` (plan လမ်း) နဲ့
   `topics` (topics လမ်း)。 တစ်ဘက်ပဲ ပြင်မိတာ ဤ session မှာ ၄ ကြိမ် ဖြစ်ခဲ့သည်。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import planner as PL                                          # noqa: E402
import topics as TP                                           # noqa: E402

GENERIC = ("plain", "number", "warning", "steps", "compare", "fact",
           "checklist", "location", "screen")


class Grouping(unittest.TestCase):
    def test_countdown_is_time(self):
        fm = PL.fixed_meaning()
        self.assertEqual(fm.get("prem3.countdown"), "time")
        self.assertEqual(fm.get("titles.countdown"), "time")

    def test_subscribe_is_cta(self):
        self.assertEqual(PL.fixed_meaning().get("titles3.subscribe_bug"), "cta")

    def test_end_card_is_close(self):
        self.assertEqual(PL.fixed_meaning().get("titles.end_card"), "close")

    def test_logo_is_brand(self):
        self.assertEqual(PL.fixed_meaning().get("titles.logo_sting"), "brand")

    def test_plain_card_not_flagged(self):
        """⚠️ negative control — သာမန် ကတ်ကို မဖမ်းမိရ"""
        fm = PL.fixed_meaning()
        for t in ("thm.hook_two", "titles.lower_third", "qcard.num_point",
                  "kinetic2.strike_in", "headtop.ht_outline_title"):
            self.assertIsNone(fm.get(t), t)

    def test_count_is_small(self):
        """⚠️ စာရင်း ကြီးလွန်းလျှင် pool ကို ဖျက်မိမည်"""
        self.assertLess(len(PL.fixed_meaning()), 60, len(PL.fixed_meaning()))
        self.assertGreater(len(PL.fixed_meaning()), 20)


class PlanPath(unittest.TestCase):
    def test_generic_labels_have_none(self):
        fm = PL.fixed_meaning()
        for lab in GENERIC:
            c = PL._profile_candidates(lab, "premium")
            bad = [x for x in c if fm.get(x)]
            self.assertEqual(bad, [], (lab, bad[:4]))

    def test_hook_keeps_opening(self):
        """⚠️ ဖွင့်ချက် template တွေက hook မှာ သင့်သည် — မဖယ်ရ"""
        c = PL._profile_candidates("hook", "premium")
        self.assertIn("titles3.opening_bars", c)

    def test_time_never_auto(self):
        for lab in GENERIC + ("hook", "section", "chapter", "cta"):
            c = PL._profile_candidates(lab, "premium")
            self.assertNotIn("prem3.countdown", c, lab)
            self.assertNotIn("titles.countdown", c, lab)

    def test_pool_not_gutted(self):
        """⚠️ စစ်ထုတ်ချက်က pool ကို ဖျက်မပစ်ရ"""
        for lab in ("plain", "number", "fact"):
            self.assertGreater(len(PL._profile_candidates(lab, "premium")), 240)

    def test_allow_fixed_default_true(self):
        self.assertTrue(PL.allow_fixed("thm.hook_two", "plain"))
        self.assertFalse(PL.allow_fixed("prem3.countdown", "plain"))
        self.assertTrue(PL.allow_fixed("titles3.opening_bars", "hook"))


class TopicsPath(unittest.TestCase):
    def test_roles_only_by_rule_or_curation(self):
        """⚠️ topics လမ်းကလည် အတူတူ စစ်ရမည်。

        fixed-meaning id က role pool ထဲ ရှိခွင့် **၂ မျိုးသာ** —
          ① `_FIXED_ALLOW` က ခွင့်ပြုထား (ဥပမာ `cta` role ⇒ cta အုပ်စု)
          ② **လက်ရေး `POOLS`** ထဲ ဒီဇိုင်နာ တမင် ထည့်ထား
             (ဥပမာ `titles2.clock_strip` က `label` role ထဲ)
        အဲဒီ ၂ ခု မဟုတ်ဘဲ ရှိနေလျှင် အလိုအလျောက် တွဲချက် ယိုနေခြင်း。
        """
        fm = PL.fixed_meaning()
        for r in sorted(TP.POOLS):
            hand = {TP._id_of(f) for f in TP.POOLS.get(r, [])}
            leak = [x for x in TP.pool_ids(r)
                    if fm.get(x) and x not in hand and not PL.allow_fixed(x, r)]
            self.assertEqual(leak, [], (r, leak[:4]))

    def test_chapter_keeps_opening(self):
        """⚠️ ဖွင့်ချက် template က chapter မှာ သင့်သည် — မဖယ်ရ"""
        fm = PL.fixed_meaning()
        got = [x for x in TP.pool_ids("chapter") if fm.get(x) == "open"]
        self.assertGreater(len(got), 0)
        # ⚠️ ဒါပေမယ့် `time`/`close`/`brand` က မပါရ
        for x in TP.pool_ids("chapter"):
            self.assertNotIn(fm.get(x), ("time", "close", "brand"), x)

    def test_cta_role_keeps_cta(self):
        c = [x for x in TP.pool_ids("cta") if PL.fixed_meaning().get(x) == "cta"]
        self.assertGreater(len(c), 0)

    def test_pool_not_gutted(self):
        for r in ("fact", "label"):
            self.assertGreater(len(TP.pool_ids(r)), 240, r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
