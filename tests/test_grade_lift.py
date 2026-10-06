# -*- coding: utf-8 -*-
"""အသားရေ အလင်း (`lutyuv`) ကို **အပိုင်းလိုက် မထည့်ရ**

⚠️ ၂၀၂၆-၁၀-၀၁ တိုင်းချက် — filter **တူတူ**、ဝင်းဒိုး အရေအတွက်သာ ကွာ:
     အပိုင်း ၁ ခု (ဝင်းဒိုး မပါ)  အသားရေ G−B  ၇.၃၀
     အပိုင်း ၂ ခု                            ၈.၇၅
     အပိုင်း ၅ ခု                           ၁၂.၄၅
   `lutyuv` က YUV filter ဖြစ်၍ RGB filter ကြားမှာ ထည့်တိုင်း ffmpeg က
   yuv↔rgb အသွားအပြန် ထည့်သည် ⇒ ၅ ခါ ဆိုလျှင် ၈-bit အမှား ပေါင်းသည်。
   အဆုံးမှာ တစ်ခါတည်း ထည့်လျှင် ၇.၃၀ — ဝင်းဒိုး မပါတာနဲ့ **အတိအကျ တူ**。
   Y က ပစ်မှတ်ကို ပြန်ချိန်သဖြင့် luma မှာ မပေါ် ⇒ တိတ်တဆိတ် ဖြစ်ခဲ့သည်。
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import grade as GR      # noqa: E402
import shotlook as SH   # noqa: E402
import recipes as RC    # noqa: E402

LL = (78.0, 130.0)


def _rc():
    r = dict(RC.get("headtop"))
    r["luma_lift"] = LL
    return r


class LumaFilter(unittest.TestCase):
    def test_builds(self):
        f = GR.luma_filter(_rc())
        self.assertTrue(f.startswith("lutyuv=y='"), f[:40])
        self.assertTrue(f.endswith("'"))

    def test_none_without_lift(self):
        r = _rc(); r["luma_lift"] = None
        self.assertEqual(GR.luma_filter(r), "")

    def test_rejects_bad_range(self):
        # ⚠️ ပစ်မှတ်က skin ထက် ၄ အောက် ကွာလျှင် မထည့်ရ (အလကား လုပ်စရာ)
        for bad in ((78.0, 80.0), (5.0, 130.0), (245.0, 250.0), ("a", "b"), (78.0,)):
            r = _rc(); r["luma_lift"] = bad
            self.assertEqual(GR.luma_filter(r), "", bad)

    def test_knee_present(self):
        # အနက် knee — မထားလျှင် p05 ၃၄ → ၉၀ (နို့ရည်ရောင်)
        # premium (headtop) — အနက်ကို ×၀.၇၅ နက်စေသော knee (ဆွဲမတင်)
        f = GR.luma_filter(_rc())
        self.assertTrue("lt(val,20.0)" in f or "val*0.75" in f, f)
        r = _rc(); r["grade_look"] = None
        self.assertIn("lt(val,20.0)", GR.luma_filter(r))

    def test_premium_look_once(self):
        # look (RGB) က chain(lift=True) မှာ တစ်ခါ · lift=False မှာ မပါ
        self.assertEqual(GR.chain(_rc()).count("colortemperature"), 1)
        self.assertNotIn("colortemperature", GR.chain(_rc(), lift=False))


class ChainLift(unittest.TestCase):
    def test_chain_includes_by_default(self):
        self.assertIn("lutyuv", GR.chain(_rc()))

    def test_chain_excludes_when_off(self):
        self.assertNotIn("lutyuv", GR.chain(_rc(), lift=False))

    def test_only_lutyuv_differs(self):
        # ⚠️ `lift=False` က **lutyuv တစ်ခုသာ** ဖယ်ရမည် — တခြား filter မထိရ
        # ⚠️ `,` နဲ့ ခွဲလို့ **မရ** — lutyuv ရဲ့ expression ထဲ `,` ပါသည်
        #    (ပထမ ရေးမိပြီး test က မှားခဲ့သည်)。 substring ဖယ်ပြီး နှိုင်းသည်。
        a = GR.chain(_rc())
        b = GR.chain(_rc(), lift=False)
        lf = GR.luma_filter(_rc())
        self.assertIn(lf, a)
        lk = GR.look_filter(_rc())     # premium look လည်း lift နဲ့ အတူ「အဆုံးမှာ တစ်ခါ」ဘက်
        self.assertEqual(a.replace("," + lf, "").replace(lf, "").replace("," + lk, ""), b)

    def test_no_lift_recipe_unchanged(self):
        r = _rc(); r["luma_lift"] = None
        lk = GR.look_filter(r)
        self.assertEqual(GR.chain(r).replace("," + lk, ""), GR.chain(r, lift=False))


class SegmentedChain(unittest.TestCase):
    """အပိုင်းလိုက် ဆောက်ရာမှာ lutyuv **တစ်ခုသာ** ပါရမည်"""

    WINS = [(0.0, 6.0, "indoor"), (6.0, 39.0, "neutral"),
            (39.0, 42.0, "indoor"), (42.0, 87.0, "neutral"),
            (87.0, 89.9, "indoor")]

    def _sg(self, lift_in_parts):
        rc = _rc()
        parts = []
        for a, b, k in self.WINS:
            fc = GR.chain(SH.merge(rc, k, {}), lift=lift_in_parts)
            if fc:
                parts.append(SH.windowed(fc, a, b))
        sg = ",".join(parts)
        if not lift_in_parts:
            lf = GR.luma_filter(rc)
            if lf:
                sg += "," + lf
        return sg

    def test_old_way_had_five(self):
        # ⚠️ negative control — အရင် လမ်းက တကယ် ၅ ခု ဖြစ်ကြောင်း အရင် ပြရမည်
        self.assertEqual(self._sg(True).count("lutyuv"), 5)

    def test_new_way_has_one(self):
        self.assertEqual(self._sg(False).count("lutyuv"), 1)

    def test_lift_is_last_and_unwindowed(self):
        sg = self._sg(False)
        ix = sg.index("lutyuv")
        tail = sg[ix:]
        self.assertNotIn("enable=", tail, "အဆုံး lutyuv မှာ ဝင်းဒိုး ပါနေသည်")
        self.assertEqual(sg.rindex("lutyuv"), ix, "lutyuv ၂ ခု ရှိသည်")

    def test_windows_still_gated(self):
        # အပိုင်းတိုင်းရဲ့ RGB filter တွေမှာ enable ကျန်ရမည်
        sg = self._sg(False)
        head = sg[:sg.index("lutyuv")]
        self.assertEqual(head.count("colorlevels"), 5)
        self.assertEqual(head.count("enable="), head.count("colorlevels")
                         + head.count("curves"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
