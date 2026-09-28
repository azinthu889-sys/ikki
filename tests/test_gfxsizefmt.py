# -*- coding: utf-8 -*-
"""`sizes(fmt)` — format အလိုက် cache + **အချိုးတူ** fallback。

⚠️ ၂၀၂၆-၀၉-၂၁ ဖမ်းမိသော အမှား ၂ ခု —
  ① `_SIZE` က global **တစ်ခုတည်း** cache ဖြစ်သဖြင့် worker က job ဆက်တိုက်
     လုပ်ရာမှာ **ပထမ format ရဲ့ ဒေတာက ကျန်တာအားလုံးကို လွှမ်း**ခဲ့သည်
     (worker က ရှည်ရှည် ပြေးသည်)。
  ② `4K16:9` က `16:9` နဲ့ **အချိုး တူ** ပါလျက် သီးသန့် ဖိုင် မရှိသဖြင့်
     ကြိုစစ်ချက် လုံးဝ အလုပ်မလုပ်ခဲ့ — ယခု `h_pct` ကနေ ပြန်တွက်သည်。
⚠️ အချိုး **မတူ**လျှင် ပြန်မသုံးရ — ၉:၁၆ က ၁၆:၉ ရဲ့ layout နဲ့ မတူပါ ⇒
   ဗလာ ပြန်ပေးပြီး `fits()` က **ကြိုမပယ်**ရ (ပယ်လျှင် ဂရပ်ဖစ် အလကား ပျောက်မည်)。
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import dress as DR          # noqa: E402


class GfxSizeFmt(unittest.TestCase):

    def setUp(self):
        DR._SIZE = None          # cache ရှင်း

    def test_16x9_loaded(self):
        z = DR.sizes("16:9")
        self.assertGreater(len(z), 100, f"entry {len(z)} ခုသာ")

    def test_4k_reuses_same_aspect(self):
        """`4K16:9` က `16:9` ရဲ့ `h_pct` ကနေ **၂ ဆ** ရရမည်"""
        a, b = DR.sizes("16:9"), DR.sizes("4K16:9")
        self.assertEqual(len(a), len(b))
        k = next(iter(a))
        self.assertAlmostEqual(b[k]["h"] / float(a[k]["h"]), 2.0, delta=0.05)

    def test_cache_per_format(self):
        """⚠️ format အလိုက် ခွဲ cache ရမည် — မဟုတ်လျှင် ပထမဟာက လွှမ်းမည်

        ⚠️ ၂၀၂၆-၀၉-၂၈ — ယခင်က `9:16` ဖိုင် **မရှိ**သဖြင့် 「ဗလာ ဖြစ်ရမည်」
           ဆိုတာကို probe အဖြစ် သုံးခဲ့သည်。 ယခု ဖိုင် ရှိပြီ (616 · h ပါ 514)
           ⇒ ဗလာ မဟုတ်တော့ ⇒ **cache ခွဲ/မခွဲ ကို လုံးဝ မစစ်တော့ခဲ့**。
           ယခု ဘောင်အမြင့် `H` နဲ့ တိုက်ရိုက် စစ်သည် — 16:9 ⇒ 1080 ·
           9:16 ⇒ 1920 ⇒ လွှမ်းလျှင် ချက်ချင်း ပေါ်သည်。
        """
        a = DR.sizes("16:9")
        b = DR.sizes("9:16")
        self.assertGreater(len(a), 100, f"16:9 entry {len(a)} ခုသာ")

        # ① တခြား format ဖတ်ပြီးနောက် 16:9 မပျက်ရ
        a2 = DR.sizes("16:9")
        self.assertGreater(len(a2), 100, "16:9 က ပျက်သွားသည်")
        self.assertIs(a, a2, "format အလိုက် cache မခွဲထားပါ — object ကွဲနေသည်")

        # ② 9:16 ထဲမှာ 16:9 ရဲ့ ဒေတာ မကျန်ရ (ဘောင်အမြင့်နဲ့ စစ်)
        if b:
            k = next(iter(set(a) & set(b)))
            self.assertEqual(a[k]["H"], 1080, f"16:9 ရဲ့ H မှား: {a[k]['H']}")
            self.assertEqual(b[k]["H"], 1920, f"9:16 မှာ 16:9 လွှမ်းထားသည်: {b[k]['H']}")

    def test_missing_format_is_empty(self):
        """အချိုး မတူတာ မရှိလျှင် ဗလာ — `fits()` က ကြိုမပယ်ရ"""
        for f in ("9:16", "3:4", "4:5", "1:1"):
            DR._SIZE = None
            z = DR.sizes(f)
            if z:                      # တိုင်းထားပြီးဆိုလျှင် ကျော်
                continue
            self.assertTrue(DR.fits("titles.title_card", (0, 500), 900, 1440,
                                    fmt=f, W=1080),
                            f"{f} — ဗလာဆို ကြိုမပယ်ရ")

    def test_fmt_hw(self):
        self.assertEqual(DR._fmt_hw("16:9"), (1920, 1080))
        self.assertEqual(DR._fmt_hw("3:4"), (1080, 1440))
        self.assertEqual(DR._fmt_hw("မသိ"), (1920, 1080))


if __name__ == "__main__":
    unittest.main(verbosity=2)
