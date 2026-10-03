# -*- coding: utf-8 -*-
"""ဖြတ်ချက်ရဲ့ **ကိန်း ၂ လုံး** — ပြောတဲ့အတိုင်း ဖြစ်ရမည်

⚠️⚠️ ၂၀၂၆-၁၀-၀၃ Zin — Descript ရဲ့ 「Shorten word gaps」 ကို ကြည့်ပြီး
   「ကိန်း ၂ လုံးနဲ့ အစားထိုးပြီး လုပ်ပေးပါ」。

ဖတ်နည်း: **「`min_sil` ထက် ရှည်တဲ့ ခဏရပ်ကို `keep_pause` ဖြစ်အောင် လျှော့」**

⚠️ ယခင်က အဲဒီ ကိန်း ၂ လုံးအပေါ် `pause_ratio`/`pause_max` ဆိုတဲ့
   **ဒုတိယ ယန္တရား** တွဲထားခဲ့သည် (ကွက်လပ် ရှည်လေ ပိုချန်လေ · ၁.၅s အထိ)
   ⇒ **ကိန်းက ပြောတာနဲ့ တကယ် ဖြစ်တာ မတူ**ခဲ့。 ပြီးတော့ အချိုး ဖြစ်၍
   ဖိုင်တိုင်း အဓိပ္ပာယ် မတူ — ချိန်ဖို့ ဗီဒီယို အများကြီး လိုခဲ့。

⚠️⚠️ ratio ကို ဖြုတ်ပြီး ကိန်းသေ ဖြစ်အောင် လုပ်တော့ `tight`/`snappy` မှာ
   **ချန်ချက် > ဂိတ်** ဖြစ်သွားသည် (၀.၅၀ > ၀.၄၅) ⇒ ဂိတ်နဲ့ ချန်ချက်
   ကြားက ကွက်လပ်တွေက ဖြတ်မှတ် ရေတွက်ထဲ ပါပေမယ့် **ဘာမှ မဖြစ်**。
   ⇒ ကိန်း ၂ လုံးလုံး ပြန်ရှာရသည် — ဖြုတ်မှု ပမာဏ မပြောင်းအောင်。

တိုင်းချက် (ဖိုင် ၁၇၈.၇s · ကွက်လပ် ၉၅ ခု) — preset တိုင်း ±၀.၁ မှတ်:
  gentle ၃၉.၀→၃၉.၀% (ဖြတ် ၁၇→၁၇) · normal ၄၁.၉→၄၁.၈% (၂၃→၂၁)
  tight  ၄၄.၉→၄၄.၉% (၃၂→၂၆) · snappy ၄၇.၃→၄၇.၃% (၄၃→၂၇)
**ဖြတ်ချက် လျော့တာက အပိုအမြတ်** — no-op ဖြတ်ချက်တွေ ပျောက်၍。
"""
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "core"))


def _src(*p):
    import io
    return io.open(os.path.join(HERE, "..", *p), encoding="utf-8").read()


class Honest(unittest.TestCase):
    """**ချန်ချက် ≤ ဂိတ်** — မဟုတ်လျှင် ကိန်းက လိမ်နေသည်"""

    def test_every_preset_is_honest(self):
        import recipes as RC
        for k, (kp, ms) in RC.CUTS.items():
            if kp is None:
                continue
            self.assertLessEqual(kp, ms, f"{k}: ချန် {kp} > ဂိတ် {ms}")

    def test_every_recipe_is_honest(self):
        """⚠️ `CUTS` က preset ရွေးမှသာ သုံးသည် — recipe တွေမှာ **ကိုယ်ပိုင်
           ကိန်း ၂ လုံး** ရှိပြီး အဲဒါတွေက ပုံသေ ဖြစ်သည်。"""
        import recipes as RC
        for k in RC.R:
            r = RC.get(k)
            kp, ms = r.get("keep_pause"), r.get("min_sil")
            if kp is None or ms is None:
                continue
            self.assertLessEqual(kp, ms, f"{k}: ချန် {kp} > ဂိတ် {ms}")

    def test_a_user_cannot_invert_them(self):
        """⚠️ သုံးစွဲသူက ကိန်း ၂ လုံးကို တိုက်ရိုက် ထည့်နိုင်သည်"""
        import recipes as RC
        r = RC.apply("vlog", {"keep_pause": 2.0, "min_sil": 0.5})
        self.assertLessEqual(r["keep_pause"], r["min_sil"], r)

    def test_the_guard_runs_after_the_user_values_land(self):
        """⚠️ `r.update(o)` မတိုင်ခင် စစ်လျှင် ဘာမှ မဖမ်းမိ — တကယ် ဖြစ်ခဲ့"""
        s = _src("core", "recipes.py")
        a = s.find("    r.update(o)")
        b = s.find('_kp, _ms = r.get("keep_pause"), r.get("min_sil")')
        self.assertGreater(a, 0)
        self.assertGreater(b, a)


class RatioIsOff(unittest.TestCase):
    def test_the_second_mechanism_is_gone_from_every_recipe(self):
        """⚠️ ပိတ်ထားတာ မဟုတ် — **လုံးဝ ဖယ်**ထားရမည်。 ပိတ်ထားတဲ့ ကုဒ်က
           နောက်တစ်ယောက်ကို လမ်းလွဲစေသည် (dead config)。"""
        import recipes as RC
        for k in RC.R:
            r = RC.get(k)
            self.assertIsNone(r.get("pause_ratio"), k)
            self.assertIsNone(r.get("pause_max"), k)

    def test_the_engine_no_longer_takes_it(self):
        import inspect
        import cut as CUT
        sig = inspect.signature(CUT.plan)
        self.assertNotIn("pause_ratio", sig.parameters)
        self.assertNotIn("pause_max", sig.parameters)
        self.assertFalse(hasattr(CUT, "pause_keep"))

    def test_the_dial_is_gone(self):
        """⚠️ dead config က လမ်းလွဲစေသည် — ဖယ်ထားကြောင်း အတည်ပြု"""
        import recipes as RC
        self.assertFalse(hasattr(RC, "PAUSES"))
        self.assertFalse(hasattr(RC, "PAUSE_LABEL"))
        self.assertNotIn("pause", RC.BOUNDS)

    def test_an_old_client_sending_it_is_ignored_not_crashed(self):
        import recipes as RC
        r = RC.apply("vlog", {"pause": "keep"})
        self.assertIsNone(r.get("pause_ratio"))
        self.assertAlmostEqual(r["keep_pause"], 0.70)   # vlog ရဲ့ ပုံသေ


class Controls(unittest.TestCase):
    def test_both_numbers_are_settable(self):
        import recipes as RC
        for k in ("keep_pause", "min_sil"):
            self.assertIn(k, RC.BOUNDS, k)
        r = RC.apply("vlog", {"min_sil": 1.50, "keep_pause": 0.80})
        self.assertAlmostEqual(r["min_sil"], 1.50)
        self.assertAlmostEqual(r["keep_pause"], 0.80)

    def test_the_listing_shows_them(self):
        """⚠️ `listing()` မှာ မပါလျှင် UI က ပုံသေကို မပြနိုင်"""
        import recipes as RC
        for row in RC.listing():
            self.assertIn("keep_pause", row, row.get("id"))
            self.assertIn("min_sil", row, row.get("id"))
            self.assertNotIn("pause", row, row.get("id"))

    def test_the_presets_still_work_as_shortcuts(self):
        import recipes as RC
        for k, (kp, ms) in RC.CUTS.items():
            if kp is None:
                continue
            r = RC.apply("vlog", {"cut": k})
            self.assertAlmostEqual(r["keep_pause"], kp, msg=k)
            self.assertAlmostEqual(r["min_sil"], ms, msg=k)


class Ui(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "app.js")

    def test_the_old_dial_is_removed(self):
        for dead in ("PAUSEOPT", "adjpause", "ADJ.pause"):
            self.assertNotIn(dead, self.s, dead)

    def test_both_numbers_are_shown(self):
        self.assertIn("num('min_sil'", self.s)
        self.assertIn("num('keep_pause'", self.s)

    def test_the_label_reads_as_one_sentence(self):
        """⚠️ ကိန်း ၂ လုံးက **အတူတွဲ** ဖတ်ရမှ အဓိပ္ပာယ် ရှိသည်"""
        self.assertIn("ဘယ်လောက်ထက် ရှည်ရင် ဖြတ်မလဲ", self.s)
        self.assertIn("ဘယ်လောက် ချန်မလဲ", self.s)

    def test_the_api_no_longer_sends_the_dial(self):
        a = _src("api", "main.py")
        self.assertNotIn("PAUSE_LABEL", a)

    def test_the_bounds_come_from_the_api(self):
        """⚠️⚠️ ကိန်းသေ ရေးထားလျှင် server ဘက် `BOUNDS` ပြောင်းချိန် UI က
           လိုက်မပြောင်းဘဲ ပုံစံတချို့ရဲ့ ပုံသေကို **ပြလို့ မရ**တော့ —
           ၂၀၂၆-၁၀-၀၁ မှာ `cap_pct` နဲ့ တကယ် ဖြစ်ခဲ့ (ပုံစံ ၄ ခု)。
        """
        i = self.s.find("function num(k,label,hint,min,max,step)")
        self.assertGreater(i, 0)
        w = self.s[i:i + 900]
        self.assertIn("SMETA.ranges[k]", w)
        self.assertIn("min=_R.min", w)
        self.assertIn("max=_R.max", w)

    def test_the_style_editor_shows_both_too(self):
        """⚠️⚠️ UI မှာ ဖြတ်ချက် ပြတဲ့ နေရာ **၂ ခု** ရှိသည် — ချိန်ညှိ panel နဲ့
           ပုံစံ တည်းဖြတ် စခရင်。 ပထမတစ်ခုပဲ ပြင်ခဲ့ရာ ပုံစံ တည်းဖြတ်မှာ
           `silence_ms` (ms slider) တစ်ခုတည်း ကျန်ပြီး 「ဘယ်လောက် ချန်မလဲ」
           **လုံးဝ မရှိ**ခဲ့ — ၁၂၀၀ms အမြင့်ဆုံးက cinematic-vlog ရဲ့ ၁.၂၀s
           နဲ့ ထိနေပြီးသား。 ⇒ ၂ နေရာလုံး တူညီရမည်。
        """
        self.assertIn("row('min_sil'", self.s)
        self.assertIn("row('keep_pause'", self.s)
        self.assertNotIn("rng('silence_ms'", self.s)

    def test_the_style_editor_sliders_read_the_api_ranges(self):
        i = self.s.find("function rng(key,min,max,step,val,fmt)")
        self.assertGreater(i, 0)
        w = self.s[i:i + 400]
        self.assertIn("SMETA.ranges[key]", w)

    def test_both_get_a_seconds_label(self):
        """⚠️ ms နဲ့ မပြရ — ကိန်း ၂ လုံးက စက္ကန့်"""
        self.assertIn("k==='min_sil'||k==='keep_pause'", self.s)
        self.assertIn("toFixed(2)+'s'", self.s)

    def test_the_old_key_still_works_server_side(self):
        """⚠️ `silence_ms` ကို API မှာ **ချန်**ထားသည် — သိမ်းထားပြီးသား
           ပုံစံတွေမှာ ပါနိုင်၍ (UI မှာသာ မပြတော့)。"""
        import recipes as RC
        self.assertIn("silence_ms", RC.BOUNDS)
        r = RC.apply("vlog", {"silence_ms": 700})
        self.assertAlmostEqual(r["min_sil"], 0.70)

    def test_the_api_ships_those_ranges(self):
        a = _src("api", "main.py")
        self.assertIn('"ranges"', a)
        self.assertIn("RC.BOUNDS.items()", a)


if __name__ == "__main__":
    unittest.main(verbosity=2)
