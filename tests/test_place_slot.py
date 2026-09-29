# -*- coding: utf-8 -*-
"""📍 tag က **နေရာ နာမည်** ပြရမည် — ဝါကျအပိုင်းအစ မဟုတ်

⚠️ ၂၀၂၆-၀၉-၂၉ (D2) — Zin ရဲ့ screenshot မှာ 📍「ကျောင်းရဲ့ ဒီနေရာကလည်း」
   ပေါ်ခဲ့သည်。 တကယ့် နေရာ 「Takadanobaba」 က အဲဒီ ဝါကျ ထဲမှာပဲ ရှိသည်。
⚠️ `planner.place_of` က **planner လမ်း** မှာသာ တပ်ထားခဲ့သည် — short-916 က
   **topics လမ်း** ကို သုံး၍ ပြင်ချက် မရောက်ခဲ့ပါ (numbered-item route နဲ့
   တူညီသော အမှား)。 ⇒ ဒီ test က **လမ်း ၂ ခုလုံး** ကို စစ်သည်。
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import topics as TP      # noqa: E402
import gfxcat as GC      # noqa: E402

NO_PLACE = "ကျောင်းရဲ့ ဒီနေရာကလည်း အရမ်း အဆင်ပြေပါတယ်"
HAS_LAT  = "ကျောင်းရဲ့ ဒီနေရာကလည်း Takadanobaba မှာ ရှိပါတယ်"
HAS_MM   = "ရုံးခန်းက မန္တလေးမြို့ မှာ ရှိပါတယ်"
# ⚠️ နေရာ နာမည်က ၃၂ အက္ခရာ (GTXT) အလွန်မှာ — trim ပြီးသား စာသား နဲ့
#    ရှာလျှင် လွတ်သွားမည်
LATE     = "ကျောင်းရဲ့ ဒီနေရာကလည်း အရမ်း အဆင်ပြေတဲ့ Shinjuku မှာ ရှိပါတယ်"


class TopicsRoute(unittest.TestCase):
    def test_no_place_rejected(self):
        self.assertIsNone(TP.targs("locator", NO_PLACE))

    def test_latin_place(self):
        self.assertEqual(TP.targs("locator", HAS_LAT), ("Takadanobaba", ""))

    def test_burmese_place(self):
        a = TP.targs("locator", HAS_MM)
        self.assertIsNotNone(a)
        self.assertIn("မန္တလေး", a[0])

    def test_place_beyond_trim(self):
        # ⚠️ `targs` က ရှေးဆုံး `trim(text, 32)` လုပ်သည် ⇒ မူရင်း နဲ့ ရှာရမည်
        self.assertGreater(len(LATE), TP.GTXT)
        self.assertEqual(TP.targs("locator", LATE), ("Shinjuku", ""))

    def test_sentence_never_in_slot(self):
        for t in (NO_PLACE, HAS_LAT, HAS_MM, LATE):
            a = TP.targs("locator", t)
            if a is None:
                continue
            self.assertNotIn("ဒီနေရာကလည်း", a[0], a)
            self.assertLess(len(a[0]), 24, a)


class GfxcatRoute(unittest.TestCase):
    """`gfxcat.fill` က `place` param ကို round-robin နဲ့ ဖြည့်ခဲ့သည်"""

    def _entries(self):
        return [e for e in GC.catalog()
                if any(q.get("name") in ("place", "city", "location")
                       for q in (e.get("params") or []))]

    def test_entries_exist(self):
        # ⚠️ ဒီ test က **ဖုံးအုပ်တာ မဟုတ်** ကြောင်း သက်သေ — entry ၀ ဆိုလျှင်
        #    အောက်က loop တွေ ဘာမှ မစစ်ပါ
        self.assertGreater(len(self._entries()), 0)

    def test_no_place_rejected(self):
        for e in self._entries():
            self.assertIsNone(GC.fill(e, NO_PLACE), e["id"])

    def test_place_used(self):
        for e in self._entries():
            a = GC.fill(e, HAS_LAT)
            self.assertIsNotNone(a, e["id"])
            ix = [q.get("name") for q in e["params"]].index(
                next(q["name"] for q in e["params"]
                     if q.get("name") in ("place", "city", "location")))
            self.assertEqual(a[ix], "Takadanobaba", (e["id"], a))


if __name__ == "__main__":
    unittest.main(verbosity=2)
