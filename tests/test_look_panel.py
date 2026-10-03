# -*- coding: utf-8 -*-
"""ဖြတ်ပြီးရင် **SFX · Motion ဆီ ဆက်သွားနိုင်ရမည်**

⚠️ Zin ၂၀၂၆-၁၀-၀၄: 「နောက်ထပ် SFX, Motion ဆီကို ဆက်သွားတဲ့ ခလုတ်ပါ
   ထည့်ပေးတာ ပိုကောင်းမယ်」。 အရင်က `cut_review` ကနေ render ဆီ တန်းသွားပြီး
   ကြားထဲ အလှအပ ချိန်စရာ မရှိခဲ့ပါ (「ချိန်ညှိချက်」 ထဲမှာ စာတန်း အရွယ် နဲ့
   「တီးလုံး မလို」 ၂ ခုသာ)。

⚠️⚠️ UI မှာ **ကိန်းသေ မရေးရ** — ၂၀၂၆-၁၀-၀၁ မှာ hard-code လုပ်ထားသော UI
   ဘောင်က style ၄ ခုရဲ့ **ကိုယ်ပိုင် ပုံသေကို ပြလို့ မရ**ခဲ့ပါ (`cap_pct`)。
   ⇒ ပုံသေ · ဘောင် နှစ်ခုလုံး `/api/jobs/{id}/look` ကနေ ယူသည်。

⚠️ စစ်ဆေးမှု အသစ် **မဆောက်ရ** — `recipes.clean()` က BOUNDS နဲ့ စစ်ပြီးသား。
   ဒါပေမယ့် `clean()` က BOUNDS ထဲက key **အားလုံး** လက်ခံသဖြင့် whitelist
   လိုသည် — မရှိလျှင် ဒီမျက်နှာပြင်က မပြတဲ့ ကိန်းတွေ (ဖြတ်ချက် · အရောင်)
   တိတ်တဆိတ် ပြောင်းသွားနိုင်သည်。

⚠️⚠️ `over` ထဲမှာ engine ရဲ့ ဖြတ်ချက် ဒေတာ (`_drop` · `_drop_exact` ·
   `_take_map`) ရှိသည် — ရှင်းတဲ့အခါ **LOOK key တွေပဲ** ဖြုတ်ရမည်。
   အကုန် ရှင်းလျှင် သုံးစွဲသူရဲ့ ဖြတ်ချက် တစ်ခုလုံး ပျောက်မည်。
   စမ်းချက် (browser ထဲ တကယ်): ↺ နှိပ်ပြီးနောက် over ထဲ
   `['_drop', '_drop_exact', '_take_map']` ကျန်ပြီး LOOK key ၀ ခု。
"""
import io
import os
import sys
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))


def _src(*p):
    return io.open(os.path.join(_R, *p), encoding="utf-8").read()


class Keys(unittest.TestCase):
    def setUp(self):
        self.s = _src("api", "main.py")

    def test_the_whitelist_exists(self):
        self.assertIn("LOOK_KEYS = (", self.s)

    def test_every_key_is_real(self):
        """⚠️ BOUNDS မှာ မရှိသော key ပါလျှင် `clean()` က တိတ်တဆိတ် ဖြုတ်ပြီး
           သုံးစွဲသူက 「ဘာမှ မဖြစ်ဘူး」 ဟု တွေ့မည် — အကြောင်းရင်း မသိဘဲ。"""
        import recipes as R
        i = self.s.find("LOOK_KEYS = (")
        j = self.s.find(")", i)
        keys = [k.strip().strip('"\'') for k in self.s[i + 13:j].split(",") if k.strip()]
        self.assertGreaterEqual(len(keys), 8)
        for k in keys:
            self.assertIn(k, R.BOUNDS, k)

    def test_the_cut_dials_are_not_in_it(self):
        """⚠️⚠️ ဒီမျက်နှာပြင်က ဖြတ်ချက် ကိန်းတွေ **မပြပါ** — whitelist ထဲ
           ပါသွားလျှင် သိမ်းတိုင်း တိတ်တဆိတ် ဖြုတ်ခံရမည်
           (endpoint က ပို့မလာသော LOOK key ကို ရှင်းသည်)。"""
        i = self.s.find("LOOK_KEYS = (")
        j = self.s.find(")", i)
        w = self.s[i:j]
        for k in ("keep_pause", "min_sil", "cap_pct", "cap_base", "lufs"):
            self.assertNotIn('"%s"' % k, w, k)

    def test_a_key_shown_nowhere_is_not_whitelisted(self):
        """⚠️ `sfx_per_min_off` ကို မျက်နှာပြင်မှာ မပြပါ ⇒ whitelist ထဲ
           ပါနေလျှင် သိမ်းတိုင်း ဖြုတ်ခံရမည်。"""
        i = self.s.find("LOOK_KEYS = (")
        j = self.s.find(")", i)
        self.assertNotIn('"sfx_per_min_off"', self.s[i:j])


class Endpoint(unittest.TestCase):
    def setUp(self):
        self.s = _src("api", "main.py")

    def test_the_defaults_come_from_the_recipe(self):
        """⚠️⚠️ UI က ကိန်းသေ ရေးလျှင် style ရဲ့ ပုံသေကို ပြလို့ မရ (`cap_pct`)"""
        self.assertIn('@app.get("/api/jobs/{jid}/look")', self.s)
        i = self.s.find("def job_look(")
        w = self.s[i:i + 1400]
        self.assertIn("_RC.apply(j.get(\"recipe\"), {})", w)
        self.assertIn('"bounds"', w)
        self.assertIn('"base"', w)
        self.assertIn('"over"', w)

    def test_saving_validates_through_recipes_clean(self):
        i = self.s.find('if "look" in (b or {}):')
        self.assertGreater(i, 0)
        self.assertIn("_RC.clean(lk)", self.s[i:i + 1400])

    def test_music_none_survives_clean(self):
        """⚠️⚠️ 「တီးလုံး မထည့်ပါ」 = `music: None`。 `clean()` က `None` ကို
           float/choice အဖြစ် ကိုင်လို့ မရသဖြင့် ဖြုတ်ပစ်မည် ⇒ ပိတ်လို့ မရတော့。"""
        i = self.s.find('if "look" in (b or {}):')
        w = self.s[i:i + 1400]
        self.assertIn('_mu = ("music" in lk', w)
        self.assertIn('lk["music"] = None', w)

    def test_only_the_look_keys_are_cleared(self):
        """⚠️⚠️ `over` ထဲမှာ `_drop` · `_drop_exact` ရှိသည် — အကုန် ရှင်းလျှင်
           သုံးစွဲသူရဲ့ ဖြတ်ချက် တစ်ခုလုံး ပျောက်မည်。"""
        i = self.s.find('if "look" in (b or {}):')
        w = self.s[i:i + 1400]
        self.assertIn("for k in LOOK_KEYS: over.pop(k, None)", w)
        self.assertNotIn("over.clear()", w)

    def test_it_returns_what_was_actually_stored(self):
        """⚠️ server က ဘောင်အတွင်း ချပြီးသား တန်ဖိုး ပြန်ပေးရမည် —
           မပေးလျှင် UI က ပြတာနဲ့ တကယ် သိမ်းတာ ကွဲမည်。"""
        i = self.s.find('if "look" in (b or {}):')
        self.assertIn('out["look"] = lk', self.s[i:i + 1400])


class Panel(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_panel_exists_on_the_cut_screen(self):
        self.assertIn('id="lkbox"', self.s)
        self.assertIn("အလှအပ · SFX · Motion", self.s)

    def test_rows_are_built_from_the_served_bounds(self):
        """⚠️⚠️ ကိန်းသေ ရေးလျှင် `cap_pct` ထောင်ချောက် ပြန်ဖြစ်မည်"""
        i = self.s.find("function lkRows(")
        w = self.s[i:i + 2600]
        self.assertIn("(LOOK.bounds||{})[k]", w)
        self.assertIn("(LOOK.base||{})[k]", w)

    def test_only_touched_keys_are_sent(self):
        """⚠️ မထိတာတွေပါ ပို့လျှင် style ပြောင်းလျှင် လိုက်မပြောင်းတော့ဘဲ
           အေးခဲသွားမည်。"""
        i = self.s.find("function lkSave(")
        self.assertIn("JSON.stringify({look:LOOKD})", self.s[i:i + 900])

    def test_it_loads_only_when_opened(self):
        """⚠️ မဖွင့်ဘဲ ဆွဲလျှင် ဖွင့်မကြည့်သူတိုင်းအတွက် အလကား တောင်းဆိုမှု"""
        self.assertIn('bx.addEventListener("toggle"', self.s)
        self.assertIn("if(bx.open && !LOOK) lkLoad(jid)", self.s)

    def test_music_off_is_not_shown_as_default(self):
        """⚠️⚠️ `music: null` က အဓိပ္ပာယ် ၂ မျိုး — 「မသတ်မှတ်ထား」 နဲ့
           「မထည့်ပါ」。 「ပုံသေ」 ဟု ပြလျှင် ပိတ်ထားမှန်း မသိတော့ပါ
           (စမ်းစဉ် တွေ့)。"""
        i = self.s.find("function lkFmt(")
        w = self.s[i:i + 900]
        self.assertIn("k===\"music\" && (touched", w)

    def test_the_default_label_is_not_doubled(self):
        """⚠️ `lkFmt` ကိုယ်တိုင် 「ပုံသေ」 ပြပြီးသား ⇒ ထပ်ထည့်လျှင်
           「ပုံသေပုံသေ」 (စမ်းစဉ် တွေ့)。"""
        i = self.s.find("var _shown=(cur!==null")
        self.assertGreater(i, 0)
        self.assertIn("(!on && _shown)", self.s[i:i + 300])

    def test_the_saved_message_survives_the_redraw(self):
        """⚠️⚠️ `lkRows()` က box တစ်ခုလုံး ပြန်ဆောက်သဖြင့် အရင် ထည့်လျှင်
           ချက်ချင်း ပျောက်သည် — သုံးစွဲသူက သိမ်းမိ/မမိ မသိရ (စမ်းစဉ် တွေ့)。"""
        i = self.s.find("function lkSave(")
        w = self.s[i:i + 1400]
        a = w.find("lkRows(jid)")
        b = w.find("သိမ်းပြီး ✓")
        self.assertGreater(a, 0)
        self.assertGreater(b, a, "စာကို lkRows ပြီးမှ ထည့်ရမည်")

    def test_every_control_has_a_plain_label(self):
        """⚠️ `gfx` · `broll_pct` လို နာမည်တွေက သုံးစွဲသူအတွက် ဘာမှ မဆိုလို"""
        i = self.s.find("var LOOKL={")
        w = self.s[i:i + 1400]
        for k in ("gfx:", "broll_pct:", "sfx_per_min:", "music:", "cam_moves:"):
            self.assertIn(k, w, k)

    def test_the_free_preview_is_right_there(self):
        """⚠️ ချိန်ပြီး **မြင်ရမည်** — မမြင်ရလျှင် မှန်းပြီး ချိန်ရမည်"""
        i = self.s.find("function lkRows(")
        self.assertIn("အခမဲ့ preview", self.s[i:i + 2600])


if __name__ == "__main__":
    unittest.main(verbosity=2)
