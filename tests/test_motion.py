# -*- coding: utf-8 -*-
"""overlay ရဲ့ **လှုပ်ရှားမှု** တိုင်းချက် — `card_in` · `card_out` · easing。

⚠️ ဤနေရာက render report ရဲ့ **တစ်ခုတည်းသော အမှောင်ကွက်** ဖြစ်ခဲ့သည် —
   `card_in — မတိုင်းရသေး · card_out — မတိုင်းရသေး · easing — မတိုင်းရသေး`
   ဟု hardcode ထားခဲ့သဖြင့် ကတ် **ဘယ်လို ပေါ်တာ** ဘယ်တော့မှ မသိရ。
⚠️ တိုင်းလိုက်တာနဲ့ ချွတ်ယွင်းချက် ၂ ခု ပေါ်လာသည် (၂၀၂၆-၀၉-၂၁ · clip ၃ ခု) —
     card_in  ၀.၄၀s  ပစ်မှတ် ၀.၄၆၇ [၀.၂၃၃–၀.၇၃၃]  ✓
     card_out ၀.၀၀s  ပစ်မှတ် ၀.၂၀၀ [၀.၁၃၃–၀.၂၆၇]  ✗ ← pop ချက်ချင်း ပျောက်
     ease     ၀.၁၁၆  spec ၀.၆၆၇                    ✗ ← မျဉ်းဖြောင့် နီးပါး
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
sys.path.insert(0, os.path.join(ROOT, "worker"))
import motmeas as MM          # noqa: E402
import run as W               # noqa: E402


class Motion(unittest.TestCase):

    # ── ease metric calibration ──
    def test_linear_is_zero(self):
        self.assertAlmostEqual(MM._bezier_area(1/3., 1/3., 2/3., 2/3.), 0.0,
                               places=2)

    def test_spec_is_ease_out(self):
        """spec `cubic-bezier(.22,.8,.24,1)` က ease-out အားကောင်း ⇒ အပေါင်"""
        self.assertGreater(MM.SPEC_EASE, 0.5)
        self.assertEqual(MM.SPEC_EASE, MM._bezier_area(0.22, 0.8, 0.24, 1.0))

    def test_ease_in_is_negative(self):
        self.assertLess(MM._bezier_area(0.42, 0.0, 1.0, 1.0), 0.0)

    # ── ဂိတ်က peak နဲ့ အချိုးကျ ဖြစ်ရမည် ──
    def test_thresholds_relative(self):
        """⚠️ ကိန်းသေ ဂိတ်ဆိုလျှင် pop အားလုံး ပယ်ခံမည် — alpha ပျမ်းမျှက
        ဘောင်တစ်ခုလုံးအပေါ် ဖြစ်၍ စာလုံးလေးဆို ~၁–၃% သာ ရှိသည်。"""
        import inspect
        src = inspect.getsource(MM.measure)
        self.assertIn("pk <= FLOOR", src)
        self.assertIn("ON * pk", src)
        self.assertIn("FULL * pk", src)
        self.assertLessEqual(MM.FLOOR, 0.01)

    def test_missing_file_is_none(self):
        self.assertIsNone(MM.measure("/nope/x.mov"))
        self.assertEqual(MM.alpha_series("/nope/x.mov"), ([], 0.0))

    def test_summary_empty(self):
        self.assertIsNone(MM.summary([]))
        self.assertIsNone(MM.summary(None))

    # ── fade-out ──
    def test_fade_out_only(self):
        """⚠️ **ဝင်ချိန်ကို မထိရ** — template ရဲ့ ဝင်ချိန် ဘောင်အတွင်း ရှိပြီး"""
        f = W._fade_out("1:v", "pf1", 5.0, 7.0)
        self.assertIn("fade=t=out", f)
        self.assertNotIn("t=in", f)
        self.assertIn("alpha=1", f)

    def test_fade_out_before_gate(self):
        """fade က `enable` ပိတ်ချိန် မတိုင်ခင် ပြီးရမည် (ခုန်ချမှု မဖြစ်စေရန်)"""
        import re
        f = W._fade_out("1:v", "pf", 0.0, 2.0)
        st = float(re.search(r"st=([\d.]+)", f).group(1))
        d = float(re.search(r"d=([\d.]+)", f).group(1))
        self.assertLess(st + d, 2.0)

    def test_fade_out_clamped_on_short(self):
        """clip တိုလျှင် fade က အရှည်ရဲ့ ၄၅% ထက် မပိုရ"""
        import re
        f = W._fade_out("1:v", "pf", 0.0, 0.3)
        d = float(re.search(r"d=([\d.]+)", f).group(1))
        self.assertLessEqual(d, 0.3 * 0.45 + 1e-6)
        self.assertGreaterEqual(d, 0.06)

    def test_worker_only_fades_when_missing(self):
        """⚠️ ထွက်ချိန် ရှိပြီးသား clip မှာ **ထပ်မတပ်ရ** (နှစ်ထပ် ဖြစ်မည်)"""
        src = open(os.path.join(ROOT, "worker", "run.py"), encoding="utf-8").read()
        self.assertIn('_m2.get("out_s") or 0.0) < 0.10', src)
        self.assertIn("_fade_out(f\"{n}:v\"", src)

    def test_report_shows_numbers(self):
        """report က 「မတိုင်းရသေး」မဟုတ်ဘဲ တကယ့် ကိန်း ပြရမည်"""
        _p, txt = W.write_report("t_mo", dict(
            motion=dict(n=3, in_s=0.4, out_s=0.0, ease=0.116,
                        spec_ease=0.667, hold_s=1.37)))
        line = [l for l in txt.split("\n") if l.startswith("MOTION")][0]
        self.assertIn("0.4", line)
        self.assertNotIn("မတိုင်းရသေး", line)
        self.assertIn("✗", txt)          # ထွက်ချိန် ၀ ⇒ ကျ
        self.assertIn("စက်ဆန်", txt)      # ease ၀.၁၁၆ ⇒ သတိပေး


if __name__ == "__main__":
    unittest.main(verbosity=2)
