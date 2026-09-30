# -*- coding: utf-8 -*-
"""topics လမ်းက motionkit ကို **ကျယ်ကျယ်** သုံးရမည်

⚠️ ၂၀၂၆-၁၀-၀၁ တိုင်းချက် — `POOLS` က လက်ရေး bare fn ၄၃ ခုသာ ဖြစ်ပြီး
   catalog မှာ ၆၁၇ ခု ⇒ topics လမ်း **၇.၀%**。 recipe ၁၄ ခုမှာ ၁၁ ခု
   (plan=False) က ဒီလမ်း ⇒ ဗီဒီယိုတိုင်း တစ်ပုံစံတည်း。
   plan လမ်း (၃ ခု) က ၇၇.၁% ထိပြီးသား ⇒ ပုံစံ တူတူ ကူးယူသည်。
⚠️ fn နာမည် ၂၁ အုပ်စု module အချင်းချင်း တူသည် (`big_number` က ၃ ခု) ⇒
   bare နာမည်က verify မထားသူကို တိတ်တဆိတ် ယူနိုင်သည်。
"""
import os, re, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import topics as TP   # noqa: E402
import gfxcat as GC   # noqa: E402
import mkcat as MK    # noqa: E402

ROLES = ("title", "chapter", "fact", "label", "cta", "typo")
T = "COE စိတ်ချရတဲ့ Class ကို ရွေးချယ်ပါ"


class Pool(unittest.TestCase):
    def test_much_wider_than_handwritten(self):
        # ⚠️ negative control — လက်ရေး စာရင်းက တကယ် သေးကြောင်း အရင် ပြသည်
        hand = set()
        for r in ROLES:
            hand |= set(TP.POOLS.get(r, []))
        self.assertLess(len(hand), 60, "လက်ရေး စာရင်း သေးမနေလျှင် ဒီ test ဘာမှ မစစ်ပါ")
        wide = set()
        for r in ROLES:
            wide |= set(TP.pool_ids(r))
        self.assertGreater(len(wide), 300, len(wide))

    def test_all_ids_are_qualified(self):
        for r in ROLES:
            for i in TP.pool_ids(r):
                self.assertIn(".", i, (r, i))

    def test_all_verified(self):
        ver = set(MK.verified())
        for r in ROLES:
            for i in TP.pool_ids(r):
                self.assertIn(i, ver, i)

    def test_no_overlay_unsafe_category(self):
        # ⚠️ mockup (ပုံ လို) · transition/motion (slot သီးသန့်) ·
        #    infographic (ဒေတာ လို — ကိန်း မတီထွင်ရ) မပါရ
        cat = {e["id"]: str(e.get("cat") or e.get("category") or "") for e in GC.catalog()}
        for r in ROLES:
            for i in TP.pool_ids(r):
                self.assertNotIn(cat.get(i), TP._BAD_CAT, (r, i, cat.get(i)))

    def test_curated_stays_first(self):
        # ⚠️ အရည်အသွေး အစဉ်လိုက် မပျက်ရ — လက်ရေး စာရင်းက ရှေ့မှာ
        for r in ROLES:
            ids = TP.pool_ids(r)
            hand = [TP._id_of(f) for f in TP.POOLS.get(r, [])]
            hand = [h for h in hand if h]
            self.assertEqual(ids[:len(hand)], hand, r)

    def test_role_character_at_head(self):
        # regex က role နဲ့ ကိုက်သူကို လက်ရေး စာရင်း နောက်မှာ ထားရမည်
        rx = re.compile(TP._ROLE_RX["cta"], re.I)
        ids = TP.pool_ids("cta")
        hand = len([1 for f in TP.POOLS["cta"] if TP._id_of(f)])
        nxt = ids[hand:hand + 6]
        self.assertTrue(any(rx.search(i.split(".", 1)[1]) for i in nxt), nxt)

    def test_deterministic(self):
        self.assertEqual(TP.pool_ids("fact"), TP.pool_ids("fact"))

    def test_no_duplicates(self):
        for r in ROLES:
            ids = TP.pool_ids(r)
            self.assertEqual(len(ids), len(set(ids)), r)


class Fillable(unittest.TestCase):
    def test_nearly_all_fill_with_brand(self):
        ids = TP.pool_ids("fact")
        ok = sum(1 for i in ids if TP.targs(i, T, "ZAE"))
        self.assertGreater(ok / float(len(ids)), 0.95, "%d/%d" % (ok, len(ids)))

    def test_most_fill_without_brand(self):
        # brand မရှိလျှင် ဒုတိယ စာသား လိုသူက None ပြန်သည် (မှန်သည်)
        ids = TP.pool_ids("fact")
        ok = sum(1 for i in ids if TP.targs(i, T, ""))
        self.assertGreater(ok / float(len(ids)), 0.70, "%d/%d" % (ok, len(ids)))


class Templ(unittest.TestCase):
    def test_returns_qualified_id(self):
        self.assertIn(".", TP.templ("title", 0, set()))

    def test_curated_first_for_seed_zero(self):
        self.assertEqual(TP.templ("title", 0, set()), TP._id_of("title_card"))

    def test_avoids_used(self):
        a = TP.templ("fact", 0, set())
        b = TP.templ("fact", 0, {a})
        self.assertNotEqual(a, b)

    def test_varies_by_seed(self):
        v = {TP.templ("fact", s, set()) for s in range(12)}
        self.assertGreater(len(v), 6, v)


class TargsIds(unittest.TestCase):
    def test_dotted_and_bare_agree_for_curated(self):
        a = TP.targs("title_card", T, "ZAE")
        b = TP.targs(TP._id_of("title_card"), T, "ZAE")
        self.assertEqual(a, b)

    def test_exact_id_not_first_fn_match(self):
        # ⚠️ `big_number` က infogfx · titles2 · prem2 ၃ ခုမှာ ရှိသည် ⇒
        #    id အပြည့် ပေးလျှင် **အဲဒီ module ကသာ** ယူရမည်
        got = [e["id"] for e in GC.catalog() if e["fn"] == "big_number"]
        self.assertGreater(len(got), 1, got)
        for i in got:
            a = TP.targs(i, T, "ZAE")
            self.assertIsNotNone(a, i)

    def test_place_slot_still_guarded(self):
        # 📍 locator က နေရာ နာမည် မရှိလျှင် ပယ်ရမည် (dotted နဲ့လည်း)
        bad = "ကျောင်းရဲ့ ဒီနေရာကလည်း အရမ်း အဆင်ပြေပါတယ်"
        self.assertIsNone(TP.targs("locator", bad, "ZAE"))
        lid = TP._id_of("locator")
        if lid:
            self.assertIsNone(TP.targs(lid, bad, "ZAE"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
