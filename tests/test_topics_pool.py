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
        # ⚠️⚠️ **overlay pool တစ်ခုတည်းနဲ့ မတိုင်းရ**。 ၂၀၂၆-၁၀-၀၂ မှာ
        #    template ၆၁၇ လုံး ဖုံးအုပ်မှု တိုင်းပြီး ဘောင်အပြည့် ၄၅ ခု
        #    အသစ် တွေ့သဖြင့် overlay pool က ၃၂၄ → **၂၉၁** ကျသည် —
        #    ဒါက ဆုံးရှုံးခြင်း **မဟုတ်**、အဲဒီ ၄၅ ခုက ဖြတ်ပြောင်း လမ်းသို့
        #    ရွှေ့သွားခြင်း ဖြစ်သည် (ဘောင်အပြည့် ဆေးသုတ်သူကို ပြောသူပေါ်
        #    ထပ်တင်လျှင် ပြောသူ ပျောက်မည်)。 ⇒ **လမ်း ၂ ခုပေါင်း** တိုင်းသည်。
        import planner as _PL
        import gfxcat as _GC
        _ff = {e["id"] for e in _GC.catalog() if _PL._full_frame(e["id"])}
        self.assertGreater(len(wide | _ff), 380, (len(wide), len(_ff)))
        # overlay pool ကိုယ်တိုင်လည် ကျဉ်းမသွားရ (လက်ရေး ၆၀ ထက် အများကြီး)
        self.assertGreater(len(wide), 280, len(wide))

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

    def test_no_pair_requiring_template(self):
        """⚠️ အတွဲ (အညွှန်း, ကိန်း) လိုသူ မပါရ — **category နဲ့ ဖမ်းလို့ မရ**

        `charts.gantt` က category `"chart"` (「infographic」 မဟုတ်) ဖြစ်၍
        ပထမ ရေကန်ထဲ ဝင်ပြီး knowledge render မှာ
        `ValueError: too many values to unpack (expected 3)` နဲ့ ကျခဲ့သည်。
        အတွဲ လိုသူ ၂၀ ခုက category ၅ မျိုး ကွဲသည် ⇒ `pairs_bad` နဲ့ စစ်ရမည်。
        """
        ent = {e["id"]: e for e in GC.catalog()}
        for r in ROLES:
            for i in TP.pool_ids(r):
                self.assertFalse(TP._wants_pairs(ent[i]), (r, i))

    def test_no_chart_or_cutaway(self):
        # chart = ဒေတာ လို (ကိန်း မတီထွင်ရ) · cutaway = ဘောင်အပြည့် (engine သီးသန့်)
        for r in ROLES:
            for i in TP.pool_ids(r):
                self.assertFalse(i.startswith(("charts.", "dash.", "maps.")), (r, i))
                self.assertFalse(i.split(".", 1)[1].startswith("cut_"), (r, i))

    def test_no_full_frame_card(self):
        """⚠️ ဘောင်အပြည့် ကတ် မပါရ — `gfx` slot က **ထပ်တင်** ဖြစ်သည်

        knowledge render မှာ `insert.insert_label` (1079px) ရွေးမိပြီး
        「⊘ နေရာ မတည့် · မျက်နှာဇုန် 151–756」 နဲ့ ပယ်ခံခဲ့သည် ⇒ ရွေး ၁၀
        ထဲ တပ်ရ ၄ ခုသာ · gfx_share 0.134 (ပစ်မှတ် 0.17)。
        ⚠️ `h_pct` နဲ့ မစစ်ရ — canvas တိုင်းသဖြင့် `prem.lower_third` ကို
           0.999 ပြသည် (တကယ်တော့ အောက်ခြေ strip)。
        """
        import planner as PL
        for r in ROLES:
            for i in TP.pool_ids(r):
                self.assertFalse(PL._full_frame(i), (r, i))

    def test_lower_third_kept(self):
        """⚠️ negative control — ဘောင်အပြည့် ဖယ်တာက **တကယ့်** lower third
           ကို မဖယ်မိရ。

        ⚠️⚠️ အရင်က `prem.lower_third` ကို သုံးခဲ့သည် — **နာမည်ကို ယုံခဲ့ခြင်း**
           ဖြစ်သည်。 ၂၀၂၆-၁၀-၀၂ တိုင်းချက်: `prem.lower_third` ရဲ့ alpha
           ဖုံးအုပ်မှုက **၁.၀၀၀** (ဘောင်တစ်ခုလုံး အလင်းပိတ် ဆေးသုတ်သည် —
           `prem` မိသားစု အားလုံး နောက်ခံ gradient ဆွဲသဖြင့်) ⇒ overlay
           အဖြစ် ချလျှင် ပြောသူ လုံးဝ ပျောက်မည်。
           `titles.lower_third` က ၀.၀၉၉ · cy ၀.၇၅ ⇒ **အဲဒါက တကယ့် lower third**。
        """
        self.assertIn("titles.lower_third", TP.pool_ids("label"))
        # ⚠️ ဘောင်အပြည့် ဆေးသုတ်သူက overlay pool ထဲ **မရှိရ**
        self.assertNotIn("prem.lower_third", TP.pool_ids("label"))

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
