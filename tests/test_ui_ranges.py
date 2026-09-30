# -*- coding: utf-8 -*-
"""UI က ပုံစံရဲ့ **ပုံသေကို ပြနိုင်ရမည်** — slider ရဲ့ ဘောင် အပါအဝင်

⚠️ ၂၀၂၆-၁၀-၀၁ တိုင်းချက် — `web/app.js` က slider ရဲ့ အနိမ့်/အမြင့်ကို
   **ကိန်းသေ** ရေးထားသည်:
     rng('cap_pct', 0.035, 0.110, …)   ⇒ knowledge 0.024 · ref-slides 0.024 ·
                                          ref-fast 0.026 · short-biz 0.0333
                                          **ပြလို့ မရ**
     rng('cap_base', 0.550, 0.870, …)  ⇒ headtop 0.92 · course 0.88 ·
                                          short-video 0.877 **ပြလို့ မရ**
     rng('broll', 0, 10, …)            ⇒ BOUNDS က ၂၀ ခွင့်ပြုသည်
   ⇒ ဘောင်ကို server ကနေ (`/api/styles` ရဲ့ `ranges`) ပို့ပြီး UI က အဲဒါကို
     ဦးစားပေးသည်。 ဒီ test က နှစ်ဖက် တူကြောင်း ထိန်းသည်。
"""
import io, os, re, sys, unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "core"))
import recipes as RC   # noqa: E402

APP = io.open(os.path.join(ROOT, "web", "app.js"), encoding="utf-8").read()
RNG = re.compile(r"rng\('([a-z_]+)',\s*([-0-9.]+),\s*([-0-9.]+),")


class ServerSendsRanges(unittest.TestCase):
    def test_bounds_serialisable(self):
        rng = {k: dict(min=v[1], max=v[2], int=(v[0] == "int"))
               for k, v in RC.BOUNDS.items()
               if isinstance(v, tuple) and len(v) == 3 and v[0] in ("int", "float")}
        self.assertGreater(len(rng), 20, len(rng))
        for k, v in rng.items():
            self.assertLess(v["min"], v["max"], k)

    def test_api_includes_ranges(self):
        src = io.open(os.path.join(ROOT, "api", "main.py"), encoding="utf-8").read()
        self.assertIn('"ranges"', src)


class UiReadsRanges(unittest.TestCase):
    def test_rng_prefers_server(self):
        self.assertIn("SMETA.ranges", APP)

    def test_rng_widens_to_the_value(self):
        # ⚠️ server ဘောင်ထက် ပုံသေက ကျော်နေလျှင်လည် ပြနိုင်ရမည်
        self.assertIn("if(val<min) min=val", APP)
        self.assertIn("if(val>max) max=val", APP)

    def test_hardcoded_fallbacks_cover_defaults(self):
        """ကိန်းသေ fallback တွေက ပုံသေ အားလုံးကို ခြုံရမည် (server မရလျှင်)"""
        bad = []
        for m in RNG.finditer(APP):
            k, lo, hi = m.group(1), float(m.group(2)), float(m.group(3))
            for n in sorted(RC.R):
                v = RC.get(n).get(k)
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    continue
                if not (lo <= v <= hi):
                    bad.append((k, n, v, (lo, hi)))
        self.assertEqual(bad, [], "slider fallback က ပုံသေကို မခြုံ: %s" % (bad,))

    def test_fallbacks_match_bounds(self):
        bad = []
        for m in RNG.finditer(APP):
            k, lo, hi = m.group(1), float(m.group(2)), float(m.group(3))
            b = RC.BOUNDS.get(k)
            if not b or b[0] not in ("int", "float"):
                continue
            if abs(lo - b[1]) > 1e-9 or abs(hi - b[2]) > 1e-9:
                bad.append((k, (lo, hi), (b[1], b[2])))
        self.assertEqual(bad, [], "fallback နဲ့ BOUNDS မကိုက်: %s" % (bad,))


class CutLabel(unittest.TestCase):
    def test_custom_has_a_label(self):
        # ⚠️ ပုံစံ ၅ ခု (headtop အပါ) က `cut_name` = "custom" ⇒ ကုတ် စကားလုံး
        #    အတိုင်း ပြခဲ့သည်。 dropdown နဲ့ တူညီသော စကားလုံး ဖြစ်ရမည်。
        self.assertIn("k==='custom'", APP)

    def test_five_styles_are_custom(self):
        cus = [n for n in sorted(RC.R) if RC.cut_name(RC.get(n)) == "custom"]
        self.assertGreater(len(cus), 0, "custom ပုံစံ မရှိလျှင် ဒီ test ဘာမှ မစစ်ပါ")
        self.assertIn("headtop", cus)


if __name__ == "__main__":
    unittest.main(verbosity=2)
