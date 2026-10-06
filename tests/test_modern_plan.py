# -*- coding: utf-8 -*-
"""Premium talking-head = modern family တစ်ခုတည်း (Zin ၂၀၂၆-၁၀-၀၆)

「လက်ရှိ motion တွေက သဘာဝ မကျ · modern မဆန် · Premium Talking Head Motion edit
 စတိုင်ကို အပြည့်အဝ」 — j_d96beb16229d မှာ family ၇ မျိုး ရော (maps · infogfx ·
 prem4 · thm · kinetic …)。 ⇒ premium profile မှာ `modern.mt_*` သာ · ခေါင်းပေါ်
 kinetic pop မထည့် · အဓိပ္ပာယ် ပြည့် props (သိန်း ယူနစ် · ၊ နဲ့ ခွဲ · keyword)。
"""
import os
import sys
import unittest

R = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(R, "core"))
import planner as PL  # noqa: E402

SEGS = [(23.88, 30.82, "ပြည်ပနေ Western Union ဖြင့် ငွေလွှဲပြီးတော့ ကျပ် ၅ သိန်းထိ ဆုတံဆိပ်များ ရရှိနိုင်တဲ့ အခွင့်အရေးတစ်ခုကို ပြောပြပေးချင်ပါတယ်။"),
        (49.56, 54.36, "တစ်ကြိမ်ကို အနည်းဆုံး ၅ သိန်းကျပ်လွှဲပြီး KPay နဲ့ လက်ခံရုံဖြင့်"),
        (97.94, 105.66, "ဘယ်လိုဆုတွေရမှာလဲဆိုရင် Casper ငွေပြန်အမ်းတဲ့ဆုရယ်၊ Mobile Top-up၊ ဖုန်းဘေစတဲ့ဆုတွေရရှိမှာဖြစ်ပါတယ်။"),
        (145.26, 152.46, "သတိထားရမှာတော့ KBZ Pay account ကို level 2 ထိ upgrade လုပ်ထားသူများက ဒီအစီအစဉ်မှာ ပါဝင်နိုင်မှာ ဖြစ်ပါတယ်။")]


class ModernPlan(unittest.TestCase):
    def setUp(self):
        if not PL._modern_ids("section"):
            self.skipTest("motionkit modern pack မရှိ (VPS)")

    def test_only_modern_family(self):
        segs = [dict(start=a, end=b, text=t) for a, b, t in SEGS]
        p, _w = PL.plan(segs, 178.68, {"style": "headtop", "gfx_gap_max": 4.2},
                        video_id="t", log=lambda *a: None)
        ids = [e["motionKitTemplateId"] for e in p["templateEvents"]]
        self.assertTrue(ids)
        self.assertTrue(all(x.startswith("modern.") for x in ids), ids)
        self.assertFalse(any((e.get("style") or {}).get("kind") == "pop" for e in p["templateEvents"]))

    def test_meaningful_props(self):
        self.assertEqual(PL._modern_props("modern.mt_counter", "number", SEGS[1][2]),
                         {"value": "5", "label": "သိန်းကျပ်"})
        pl = PL._modern_props("modern.mt_pill_list", "checklist", SEGS[2][2])
        self.assertEqual(pl["items"], ["Casper ငွေပြန်အမ်းတဲ့ဆု", "Mobile Top-up", "ဖုန်းဘေ"])
        self.assertIsNone(PL._modern_props("modern.mt_counter", "number",
                                           "စက်တင်ဘာလ ၂၉ ရက်နေ့မှာ"))   # ရက်စွဲ ⇒ stat မပြ

    def test_no_template_more_than_cap(self):
        long = [dict(start=10.0 + i * 9, end=16.0 + i * 9,
                     text=f"ဒီအချက် {i} က အရေးကြီးပါတယ် ပြည်ပ ငွေလွှဲ Western Union KBZ Pay လုပ်ရမယ်")
                for i in range(18)]
        p, _w = PL.plan(long, 200.0, {"style": "headtop", "gfx_gap_max": 4.2},
                        video_id="cap", log=lambda *a: None)
        ids = [e["motionKitTemplateId"] for e in p["templateEvents"]]
        for x in set(ids):
            self.assertLessEqual(ids.count(x), PL.MODERN_CAP, (x, ids))

    def test_legacy_path_still_available(self):
        PL.MODERN_LOOK = False
        try:
            self.assertFalse(PL._modern_on("premium"))
        finally:
            PL.MODERN_LOOK = True


if __name__ == "__main__":
    unittest.main()
