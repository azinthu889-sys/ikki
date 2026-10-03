# -*- coding: utf-8 -*-
"""`odo.count_pill` — ဂဏန်းက **ဖတ်လို့ရရမည်**

⚠️⚠️ ၂၀၂၆-၁၀-၀၃ render s7 · ၉.၃s · `odo.count_pill` · တန်ဖိုး 「၂၉」 —
   အမှား ၂ ခု တိုင်းတွေ့သည်:

   ① **ကော်လံ ၆ ခု** ပြခဲ့သည် — `digits=6` ပုံသေ ဖြစ်ပြီး IKKI က
      `digits` **မပို့**ပါ (`gfxcat.fill` ရဲ့ auto param က `dur` မှာ ရပ်သည်)。
      `"၂၉".rjust(6,"0")` = `"0000၂၉"` ⇒ မြင်ရတာ 「၀ ၀ ၀ ၀ ၂ ၉」。

   ② **ဘယ်တော့မှ မငြိမ်** — `(u−k·0.05)/0.62` ⇒ နောက်ဆုံး ကော်လံ (k=5)
      က u=၀.၈၇ မှာမှ ရပ်သည်。 ကတ်က ၂.၆s ပဲ ပေါ်သဖြင့် ငြိမ်နေချိန်
      **၀.၃၄s** ⇒ သုံးစွဲသူက 「၂၉」 ကို **ဘယ်တော့မှ မဖတ်နိုင်**。
      တိုင်းချက် (ထွက်ဗီဒီယိုကနေ): ဖရိမ်းချင်း ကွာခြားမှု ၉.၅–၁၁.၇s မှာ
      ၂၀–၄၀ (လည်နေဆဲ) · ၁၂.၁s နောက် ၃–၇ (ကတ် ပျောက်ပြီး · နောက်ခံသာ)。

ပြင်ပြီး — ကော်လံ ၂ ခု · u=၀.၄၉၄ မှာ ငြိမ် ⇒ ငြိမ်နေချိန် ၁.၃၀s
(**၃.၈ ဆ**)。 တကယ် ထုတ်ပြီး တိုင်းထားသည်。

⚠️ `_wheel` ရဲ့ ပုံသေ ၀.၆၂ ကို **မထိပါ** — `odometer`/`timer`/`count_up`
   တို့ရဲ့ အပြုအမူ မပြောင်းစေရန် (motionkit က ZAE/ZJL/IKKI သုံး ဖြစ်၍)。
"""
import os
import sys
import unittest

MK = ("/Applications/my file/My bussiness/ZAE NEW　OPERATION/"
      "N8N Work Flow/n8n All Workflow/motionkit")


@unittest.skipUnless(os.path.isdir(MK), "motionkit မရှိ")
class Shape(unittest.TestCase):
    def setUp(self):
        if MK not in sys.path:
            sys.path.insert(0, MK)

    def _sig(self, fn):
        import inspect
        cwd = os.getcwd()
        os.chdir(MK)
        try:
            import odo
            return inspect.signature(getattr(odo, fn))
        finally:
            os.chdir(cwd)

    def test_digits_is_derived_not_fixed(self):
        """⚠️ IKKI က `digits` မပို့ ⇒ ပုံသေက တန်ဖိုးတိုင်းအတွက် သုံးခံရသည်"""
        self.assertIsNone(self._sig("count_pill").parameters["digits"].default)

    def test_the_wheel_takes_a_settle_fraction(self):
        p = self._sig("_wheel").parameters
        self.assertIn("settle", p)

    def test_the_other_odometers_are_untouched(self):
        """⚠️⚠️ motionkit က ZAE/ZJL/IKKI သုံး — ပုံသေ ပြောင်းလျှင်
           မသက်ဆိုင်သော ဗီဒီယိုတွေ ပါ ပြောင်းသွားမည်。"""
        self.assertAlmostEqual(self._sig("_wheel").parameters["settle"].default,
                               0.62)
        self.assertEqual(self._sig("odometer").parameters["digits"].default, 6)
        self.assertEqual(self._sig("timer").parameters["m"].default, 59)


class Timing(unittest.TestCase):
    """ငြိမ်ချိန်ကို သင်္ချာနဲ့ — `(u − k·0.05)/settle` က ၁ ရောက်တဲ့ u"""

    @staticmethod
    def _settle_u(digits, settle):
        return (digits - 1) * 0.05 + settle

    def test_the_old_shape_was_unreadable(self):
        """ကော်လံ ၆ · settle ၀.၆၂ ⇒ ၂.၆s ကတ်မှာ ငြိမ်နေချိန် ၀.၃၄s"""
        u = self._settle_u(6, 0.62)
        self.assertAlmostEqual(u, 0.87, places=2)
        self.assertLess((1 - u) * 2.6, 0.40)

    def test_the_new_shape_holds_half_the_card(self):
        """⚠️ **အဓိက** — ဖတ်ချိန် ရှိရမည်"""
        u = self._settle_u(2, 0.45)
        self.assertAlmostEqual(u, 0.50, places=2)
        self.assertGreater((1 - u) * 2.6, 1.20)

    def test_a_long_value_still_settles_in_time(self):
        """⚠️ ဂဏန်း များလျှင် stagger က တွန်းတက်သည် — ၅ လုံးဆိုလည်း
           ကတ်ရဲ့ ထက်ဝက်ကျော် မကျော်ရ。"""
        u = self._settle_u(5, 0.45)
        self.assertLessEqual(u, 0.70, u)


@unittest.skipUnless(os.path.isdir(MK), "motionkit မရှိ")
class Burmese(unittest.TestCase):
    """⚠️ တန်ဖိုးက မြန်မာဂဏန်း ဖြစ်တတ်သည် (IKKI က မြန်မာစာ ဗီဒီယို)"""

    def test_burmese_digits_are_digits(self):
        for ch in "၂၉":
            self.assertTrue(ch.isdigit(), ch)
            self.assertIn(int(ch), (2, 9))

    def test_padding_was_what_put_the_zeros_there(self):
        """「၀ ၀ ၀ ၀ ၂ ၉」 ဆိုတာ ဘယ်ကလာလဲ ဆိုတဲ့ သက်သေ"""
        v = "၂၉"
        self.assertEqual(v.rjust(6, "0"), "0000၂၉")
        self.assertEqual(v.rjust(len(v), "0"), v)

    def test_the_column_count_follows_the_value(self):
        for v, want in (("၂၉", 2), ("5", 1), ("59581", 5)):
            self.assertEqual(max(1, len(str(v))), want, v)


if __name__ == "__main__":
    unittest.main(verbosity=2)
