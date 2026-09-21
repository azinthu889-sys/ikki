# -*- coding: utf-8 -*-
"""template ကို **အကြောင်းအရာနဲ့** ဖြည့်ခြင်း — မရလျှင် ငြင်းရမည်。

⚠️ ဤ module က ရွေးချယ်မှု ဘောင်ကို ချဲ့ရန် အခြေခံ — plan လမ်းကြောင်းက
   ယခု label တစ်ခုလျှင် candidate ၁–၄ ခုသာ မြင်သည် (တိုင်းထားသည်)。
   catalog ၄၇၉ ခုထဲ **၄၄၇ ခု** က ဖြည့်လို့ရသည်。
⚠️ **planner ကို မချိတ်ရသေး** — ချိတ်ခင် template တစ်ခုချင်း render စမ်းပြီး
   ink box · မြန်မာစာ ဝင်မဝင် · safe zone တိုင်းရမည်。 မတိုင်းဘဲ ချိတ်လျှင်
   ပြန်ပြန်ပေါ်တာကို **ပျက်နေတဲ့ ဂရပ်ဖစ်**နဲ့ လဲလိုက်ရာ ကျမည်。
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import tmplfit as TF          # noqa: E402

TH = dict(accent="#F5D000", ink="#0A0A0A", dim="#8B8B8B")


def _e(*params, cat="text"):
    return dict(id="m.t", module="m", fn="t", category=cat,
                params=[dict(name=n, type=t, required=r, default=None, auto=False)
                        for n, t, r in params])


class TmplFit(unittest.TestCase):

    def test_text_slot(self):
        k = TF.fit(_e(("text", "text", True)), dict(head="မင်္ဂလာပါ"), **TH)
        self.assertEqual(k, {"text": "မင်္ဂလာပါ"})

    def test_refuse_number_without_data(self):
        """⚠️ **ဂဏန်း မတီထွင်ရ** — transcript မှာ မရှိလျှင် ငြင်းရမည်"""
        e = _e(("pct", "number", True), ("label", "text", True))
        self.assertIsNone(TF.fit(e, dict(head="ဂဏန်း မပါသော စာသား"), **TH))
        k = TF.fit(e, dict(head="ကျောင်းသား 85% အောင်"), **TH)
        self.assertEqual(k["pct"], 85.0)

    def test_refuse_list_too_short(self):
        e = _e(("items", "list", True))
        self.assertIsNone(TF.fit(e, dict(head="ခေါင်းစဉ်", items=["တစ်"]), **TH))
        self.assertIsNotNone(TF.fit(e, dict(head="ခေါင်းစဉ်",
                                            items=["တစ်", "နှစ်"]), **TH))

    def test_refuse_image(self):
        """ရုပ်ပုံ လိုလျှင် ငြင်းရမည် — ပုံ မရှိပါ"""
        self.assertIsNone(TF.fit(_e(("img", "file", True)), dict(head="x"), **TH))

    def test_no_duplicate_text(self):
        """စာသား တစ်ခုကို နေရာ ၂ ခုမှာ မထည့်ရ"""
        k = TF.fit(_e(("label", "text", True), ("title", "text", True)),
                   dict(head="ခေါင်းစဉ်", sub="ခေါင်းစဉ်ခွဲ"), **TH)
        self.assertEqual(len(set(k.values())), len(k))

    def test_no_duplicate_colour(self):
        """⚠️ အရောင် ၂ ခု တူလျှင် effect ပျောက်သည် (`hot`==`col`)"""
        k = TF.fit(_e(("text", "text", True), ("hot", "color", True),
                      ("col", "color", True)), dict(head="စာသား"), **TH)
        cs = [v for kk, v in k.items() if kk in ("hot", "col")]
        self.assertEqual(len(set(cs)), len(cs), f"အရောင် ထပ်နေသည်: {k}")

    def test_refuse_when_no_text_at_all(self):
        """စာသား တစ်လုံးမှ မထည့်ရလျှင် ဗလာကွက် ⇒ ငြင်း"""
        self.assertIsNone(TF.fit(_e(("col", "color", False)), dict(head=""), **TH))

    def test_burmese_digits(self):
        """မြန်မာ ဂဏန်းကိုပါ ဖတ်ရမည်"""
        k = TF.fit(_e(("pct", "number", True), ("label", "text", True)),
                   dict(head="ကျောင်းသား ၈၅% အောင်"), **TH)
        self.assertEqual(k["pct"], 85.0)

    def test_real_catalog(self):
        """တကယ့် catalog — ဖြည့်လို့ရတာ ၂၀၀ ကျော်ရမည် · ထပ်နေတာ ၀"""
        try:
            import gfxcat as GC
        except Exception:
            self.skipTest("gfxcat မရ")
        cat = GC.catalog()
        c = dict(head="ကျောင်းသား ၈၅% အောင်", sub="၂၀၂၆ စာမေးပွဲ",
                 items=["N5", "N4", "N3"])
        ok = [e for e in cat if TF.fits(e, c, **TH)]
        self.assertGreater(len(ok), 200, f"ဖြည့်လို့ရ {len(ok)} ခုသာ")
        for e in ok:
            k = TF.fit(e, c, **TH)
            vs = [v for v in k.values() if isinstance(v, str)]
            self.assertEqual(len(vs), len(set(vs)),
                             f"{e['id']} မှာ ထပ်နေသည်: {k}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
