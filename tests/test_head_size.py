# -*- coding: utf-8 -*-
"""ဂရပ်ဖစ် ခေါင်းစဉ်က **စာတန်းထက် မသေးရ** (ရနိုင်သမျှ)

⚠️⚠️ ၂၀၂၆-၁၀-၀၂ Zin: 「fitting မဖြစ်」。 ၉:၁၆ render မှာ —
     lower3 ခေါင်းစဉ် **၅၂px** · စာတန်း `xl` **၁၈၂px** ⇒ **၃.၅ ဆ သေး**。
   `R_HEAD_MIN/MAX` က ဘောင်အမြင့်ရဲ့ ၃.၀–၄.၇% သာ ဖြစ်ပြီး စာတန်းက ၉.၅%。
   ခေါင်းစဉ်က body စာထက် သေးတာက ဘယ် resolution မှာမဆို ပျက်နေသည်。

⚠️ **ကြမ်းခင်း မတင်ရ — အထက်ကန့်သာ တင်ရမည်**。 `hmin` ကို ၁၈၂ တင်ကြည့်ရာ
   panel (၇၄၅px) ထဲ ၁၈၂px စာလုံး ၁ လုံးပဲ ဆံ့၍ token **၅ → ၁** ဖြစ်သွားသည်
   (「COE」 ကျန်) — ဖတ်ရပေမယ့် အဓိပ္ပာယ် မရှိ。 ⇒ စတင် အရွယ်ကိုသာ တင်သည်。

⚠️ ဝါကျ ရှည်မှာ panel အကျယ်က ကန့်သတ်ဆဲ ⇒ 「ခေါင်းစဉ် ≥ စာတန်း」 ကို
   **အမြဲ မရနိုင်**。 အဲဒါ ရဖို့ ၂ ကြောင်း ခွဲရမည် (Zin ဆုံးဖြတ်ရန်)。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
MK = ("/Applications/my file/My bussiness/ZAE NEW　OPERATION/"
      "N8N Work Flow/n8n All Workflow/motionkit")


def _fit(title, size=None):
    """lt_number ကို ဆောက်ပြီး `LAST_FIT` ကနေ တိုင်းချက် ယူသည်"""
    cwd = os.getcwd()
    if MK not in sys.path:
        sys.path.insert(0, MK)
    os.chdir(MK)
    try:
        import lower3
        lower3.lt_number("t_%d_%s" % (len(title), size), "1", title,
                         dur=1.0, size=size)
        return dict(getattr(lower3, "LAST_FIT", {}) or {})
    finally:
        os.chdir(cwd)


@unittest.skipUnless(os.path.isdir(MK), "motionkit မရှိ")
class SizeFloor(unittest.TestCase):
    SHORT = "ဗီဇာ"                        # ဗီဇာ
    MID = "N5 အောင်လက်မှတ်"
    LONG = ("COE စိတ်ချရတဲ့ Class "
            "ကို ရွေးချယ်ပါ")

    def test_signature_accepts_size(self):
        import inspect
        cwd = os.getcwd()
        if MK not in sys.path:
            sys.path.insert(0, MK)
        os.chdir(MK)
        try:
            import lower3
            sig = inspect.signature(lower3.lt_number)
        finally:
            os.chdir(cwd)
        self.assertIn("size", sig.parameters)
        # ⚠️ `dur` နောက်မှာ ရှိရမည် — `gfxcat.fill` က auto param မှာ ရပ်သဖြင့်
        #    positional လမ်းကို မထိစေရန်
        names = list(sig.parameters)
        self.assertGreater(names.index("size"), names.index("dur"))

    def test_short_headline_grows_to_caption(self):
        a = _fit(self.SHORT)
        b = _fit(self.SHORT, 182)
        self.assertGreater(b.get("size", 0), a.get("size", 0) * 2,
                           (a.get("size"), b.get("size")))
        self.assertEqual(b.get("size"), 182)

    def test_mid_headline_grows_some(self):
        a = _fit(self.MID)
        b = _fit(self.MID, 182)
        self.assertGreater(b.get("size", 0), a.get("size", 0), (a, b))

    def test_no_word_is_lost_at_any_size(self):
        """⚠️ အရေးအကြီးဆုံး — အရွယ် တင်လို့ စကားလုံး မပျောက်ရ"""
        for t in (self.SHORT, self.MID, self.LONG):
            for sz in (None, 182):
                f = _fit(t, sz)
                self.assertEqual(f.get("tok_kept"), f.get("tok_all"),
                                 (t[:20], sz, f))

    def test_long_headline_grows_with_lines(self):
        """⚠️ ၂၀၂၆-၁၀-၀၂ — ဤစစ်ချက်က အရင်「မပြောင်းရ」ဟု ဆိုခဲ့သည်。

        အဲဒါက **ကန့်သတ်ချက်ကို စစ်ချက် အဖြစ် ရေးထားခြင်း** ဖြစ်သည် —
        panel အကျယ်က ကန့်သတ်သဖြင့် ၁ ကြောင်းနဲ့ မတက်နိုင်ခဲ့。
        ကြောင်း ခွဲခြင်း ထည့်ပြီးနောက် **တက်သည်** (၆၇ → ၈၀) ⇒
        စစ်ချက်က မှားနေသည်、ကုဒ်က မမှား。
        """
        a = _fit(self.LONG)
        b = _fit(self.LONG, 182)
        self.assertGreater(b.get("size", 0), a.get("size", 0), (a, b))
        self.assertGreaterEqual(b.get("lines", 1), 2, b)
        # ⚠️ အရေးကြီးဆုံး — စကားလုံး မပျောက်ရ
        self.assertEqual(b.get("tok_kept"), b.get("tok_all"), b)

    def test_none_keeps_old_behaviour(self):
        a = _fit(self.MID)
        self.assertLess(a.get("size", 999), 182)


class Plumbing(unittest.TestCase):
    def test_props_ok_accepts_size(self):
        import manifest as MF
        ok, errs = MF.props_ok("lower3.lt_number",
                               {"value": "1", "title": "x", "size": 182})
        self.assertTrue(ok, errs)

    def test_catalog_marks_it_auto(self):
        import gfxcat as GC
        e = next(x for x in GC.catalog() if x["id"] == "lower3.lt_number")
        p = next(q for q in e["params"] if q["name"] == "size")
        self.assertFalse(p["required"])
        self.assertTrue(p["auto"])

    def test_positional_fill_untouched(self):
        # ⚠️ `gfxcat.fill` က `dur`/auto မှာ ရပ်သဖြင့် `size` မရောက်ရ
        import gfxcat as GC
        e = next(x for x in GC.catalog() if x["id"] == "lower3.lt_number")
        a = GC.fill(e, "COE Class", "ZAE")
        self.assertIsNotNone(a)
        self.assertLessEqual(len(a), 3, a)

    def test_worker_passes_cap_pct(self):
        import io
        src = io.open(os.path.join(os.path.dirname(__file__), "..",
                                   "worker", "run.py"), encoding="utf-8").read()
        self.assertIn("cap_pct=rc.get(\"cap_pct\")", src)

    def test_planner_computes_cap_px(self):
        import io
        src = io.open(os.path.join(os.path.dirname(__file__), "..",
                                   "core", "planner.py"), encoding="utf-8").read()
        self.assertIn("_cap_px", src)
        ix = src.find('cid, pr = NUM_LT')
        self.assertGreater(ix, 0)
        self.assertIn('pr["size"]', src[ix:ix + 400])


if __name__ == "__main__":
    unittest.main(verbosity=2)
