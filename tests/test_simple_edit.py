# -*- coding: utf-8 -*-
"""ဖြတ်နည်း **၂ မျိုးပဲ** · ပုံမှန်က ရိုးရှင်းစနစ်

⚠️⚠️ ၂၀၂၆-၁၀-၀၄ Zin (UI မှာ တကယ် စမ်းပြီး): 「မင်း UI design က နားလည်ရခက်ပြီး
   **ဖြတ်ချက်အားလုံး ဖျက်လို့ မရ** ဖြစ်နေတယ်။ user တွေအတွက် အရိုးရှင်းဆုံးနဲ့
   ဖြတ်ရလွယ်အောင် လုပ်ပေးပါ」。

ပြဿနာ ၂ ခု — နှစ်ခုလုံး တိုင်းပြီး အတည်ပြုထားသည်:

① **ဆွဲရွေးတိုင်း ဝါကျတစ်ခုလုံး ဖျက်ခံရသည်**。 browser က mousedown/mouseup
   တူညီသော ancestor ပေါ် `click` ပစ်သည် ⇒ စာလုံး ဆွဲရွေးတာနဲ့ row ရဲ့
   「နှိပ် = ဖျက်」 handler က ပါ ပစ်သည်。 ပြီးတော့ `paint()` က DOM ပြန်ဆောက်
   သဖြင့် ရွေးထားတာ ပျောက်ပြီး cut bar **ဘယ်တော့မှ မပေါ်**。
   ⇒ စာလုံး ဖြတ်ချက် လုံးဝ မရ (「ဖျက်လို့ မရ」 ဆိုတာ ဒါ)。
   ပြင်: ၄px ထက် ပို ရွေ့လျှင် (သို့) ရွေးထားမှု ရှိလျှင် **နှိပ်ချက် မဟုတ်**。

② **မျက်နှာပြင်က ရှုပ်လွန်းသည်**。 တိုင်းထားချက် (ဝါကျ ၃၀ ရှိသော job):

       နှိပ်လို့ရတဲ့ အရာ   **၁၉၂** ခု
       engine chip        ၃၂ (အနားယူ ၂၀ · အသံ ၈ · ❓ ၄) — ဝါကျကြား ညပ်နေ
       ဝါကျတိုင်း ခလုတ်    ၃ (▶ ✂ ⋯) + လှိုင်းပုံ

   ဝါကျ ၃၀ ဖျက်ဖို့ ခလုတ် ၁၉၂ ခု ကြားက ရှာရသည်。
   ⇒ **ရိုးရှင်းစနစ် ပုံမှန်** — ဝါကျ + ▶ သာ。 engine ရဲ့ ဆုံးဖြတ်ပြီးသားက
     「⚙ အသေးစိတ်」 နှိပ်မှ。 တိုင်းထား ပြင်ပြီး: **၁၉၂ → ၅၆ (၇၁% လျှော့)** ·
     row အမြင့် ၆၈px → ၄၆px。

⚠️ ဖျောက်ထားတာက **ဆုံးဖြတ်ချက် မပြောင်းစေပါ** — အသံ/❓/အနားယူ တို့ရဲ့
   ပုံသေက 「ချန်」 ဖြစ်ပြီး engine က အလိုအလျောက် မဖျက်ပါ ⇒ မမြင်ရလည်း
   ဘာမှ မပျောက်。 ပြင်ချင်သူက ⚙ နဲ့ ဖွင့်ရသည်。
"""
import io
import os
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(*p):
    return io.open(os.path.join(_R, *p), encoding="utf-8").read()


class DragVsClick(unittest.TestCase):
    """⚠️⚠️ **အဓိက bug** — ဆွဲရွေးတာနဲ့ နှိပ်တာ ခွဲရမည်"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_separator_exists(self):
        self.assertIn("function wasDrag(", self.s)

    def test_the_row_click_refuses_a_drag(self):
        """⚠️ ဒီစာကြောင်း မပါလျှင် စာလုံး ရွေးတိုင်း ဝါကျတစ်ခုလုံး ပျောက်မည်"""
        self.assertIn("if(r && wasDrag(e)) return;", self.s)

    def test_it_checks_both_movement_and_selection(self):
        """⚠️ ရွေးထားမှု တစ်ခုတည်း စစ်လျှင် ဆွဲပြီး လွှတ်မိတာကို မဖမ်းနိုင် ·
           ရွေ့ချက် တစ်ခုတည်းဆိုလည်း touch မှာ လွဲနိုင်သည်。"""
        i = self.s.find("function wasDrag(")
        w = self.s[i:i + 420]
        self.assertIn("e.clientX-_DN[0])>4", w)
        self.assertIn("isCollapsed", w)

    def test_the_mousedown_point_is_captured_in_the_capture_phase(self):
        """⚠️ bubble မှာ ထားလျှင် `stopPropagation` လုပ်တဲ့ handler တွေက
           ရှေ့ကနေ ဖြတ်သွားပြီး အမှတ် မရတော့ပါ。"""
        self.assertIn('document.addEventListener("mousedown", function(e){ _DN=', self.s)
        i = self.s.find('document.addEventListener("mousedown", function(e){ _DN=')
        self.assertIn("}, true)", self.s[i:i + 160])


class SimpleDefault(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_simple_is_the_default(self):
        """⚠️ ပုံသေက အသေးစိတ် ဖြစ်နေလျှင် ဘာမှ မပြောင်းသလို ဖြစ်မည်"""
        i = self.s.find('saved=localStorage.getItem("ikki_simple")')
        self.assertGreater(i, 0)
        self.assertIn('put(saved!=="0")', self.s[i:i + 300])

    def test_the_noisy_parts_are_hidden(self):
        """⚠️ ဝါကျ ၃၀ အတွက် engine chip ၃၂ ခု ကြားညပ်နေခဲ့သည်"""
        i = self.s.find("body.simple .snd")
        self.assertGreater(i, 0)
        w = self.s[i:i + 420]
        for k in (".snd", ".unl", ".pau", "[data-trim]", "[data-spl]", ".rowwave"):
            self.assertIn(k, w, k)

    def test_the_play_button_stays(self):
        """⚠️⚠️ နားမထောင်ဘဲ ဖြတ်လို့ မရ — ▶ ကို ဘယ်တော့မှ မဖျောက်ရ"""
        i = self.s.find("body.simple .snd")
        self.assertNotIn("rplay", self.s[i:i + 420])

    def test_the_text_stays_clickable_in_simple_mode(self):
        """⚠️ `.row` ကို ဖျောက်မိလျှင် ဖျက်လို့ မရတော့"""
        i = self.s.find("body.simple .snd")
        w = self.s[i:i + 420]
        self.assertNotIn("body.simple .row{display:none", w)
        self.assertIn("body.simple .row{padding", self.s)

    def test_the_choice_is_remembered(self):
        self.assertIn('localStorage.setItem("ikki_simple"', self.s)

    def test_the_toggle_says_which_state_it_goes_to(self):
        """⚠️ ခလုတ်စာက လက်ရှိ အခြေအနေ ပြလျှင် နှိပ်ရင် ဘာဖြစ်မလဲ မသိရ"""
        i = self.s.find('b.textContent = on ?')
        self.assertGreater(i, 0)
        self.assertIn('"⚙ အသေးစိတ်"', self.s[i:i + 160])


class ResultViewIsNotAnEditor(unittest.TestCase):
    """⚠️⚠️ **「ဖျက်လို့ မရ」 ရဲ့ တကယ့် အကြောင်းရင်း** (၂၀၂၆-၁၀-၀၄)

    စာမျက်နှာ **၂ ခု** ရှိသည် — တူညီသော `script.html` ပေမယ့် အခြေအနေ မတူ:
      `review`      → တည်းဖြတ်。 `cursor:pointer` · 「✕ ဖျက်」 မြင်ရ
      `cut_review`  → **ရလဒ်** (`body.rv`)。 `cursor:default` · `.act` ဖျောက်

    `body.rv` မှာ **နှိပ်လို့ ရနေသေးသည်** ⇒ နှိပ်လိုက်တာနဲ့ `DEL[n]=1` ဖြစ်ပြီး
    `body.rv .row.del{display:none}` က စာကြောင်းကို **လုံးဝ ဖျောက်**သည်
    (တိုင်းထား: အမြင့် ၄၆px → ၀ · မမြင်ရ) ⇒ ပြန်ယူလို့ မရ。 ပိုဆိုးတာက
    ဖြတ်မှတ်က အေးခဲပြီးသားမို့ **ထွက်လာမယ့် ဗီဒီယိုကို မပြောင်း** —
    ဟာလာဟင်းလင်းထဲ ဖျက်နေခြင်း。

    ⇒ ဒီအဆင့်မှာ နှိပ်ခြင်းက **ခုန်ခြင်း** ဖြစ်ရမည်、ဖျက်ခြင်း မဟုတ်。
      ပြင်ချင်လျှင် `/recut` နဲ့ `review` ကို ပြန်သွားရသည်。
    """

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_clicking_a_row_in_result_view_does_not_delete(self):
        i = self.s.find('if(r && document.body.classList.contains("rv")){')
        self.assertGreater(i, 0, "rv guard မတွေ့")
        w = self.s[i:i + 420]
        self.assertIn("seekTo(", w)
        self.assertIn("return;", w)

    def test_the_guard_comes_before_the_toggle(self):
        """⚠️ အောက်မှာ ထားလျှင် `toggle()` က ရှေ့ကနေ ပြေးသွားမည်"""
        g = self.s.find('if(r && document.body.classList.contains("rv")){')
        t = self.s.find('if(r){ toggle(+r.getAttribute("data-n")); return }')
        self.assertGreater(g, 0)
        self.assertGreater(t, g)

    def test_the_keyboard_shortcut_is_blocked_too(self):
        """⚠️ `x` ခလုတ်က နှိပ်ချက်နဲ့ အတူတူ လမ်းကြောင်း"""
        i = self.s.find('e.key.toLowerCase()==="x"')
        w = self.s[i:i + 400]
        self.assertIn('classList.contains("rv")', w)

    def test_the_way_back_is_above_the_list(self):
        """⚠️ အောက်က panel ထဲက 「↩ ဖြတ်ချက် ပြန်ပြင်」 ကို သုံးစွဲသူ မတွေ့ပါ"""
        i = self.s.find('<div id="rvnote">')
        j = self.s.find('<div id="list">')
        self.assertGreater(i, 0, "rvnote မတွေ့")
        self.assertGreater(j, i, "rvnote က စာရင်းအပေါ်မှာ ရှိရမည်")
        self.assertIn("✏️ ပြန်ပြင်မယ်", self.s)

    def test_it_reuses_the_existing_recut_path(self):
        """⚠️ လမ်းကြောင်း ၂ ခု ဆောက်လျှင် တစ်ခုက နောက်ကျကျန်မည်"""
        i = self.s.find('_rve.onclick=function(){')
        w = self.s[i:i + 400]
        self.assertIn('getElementById("crc")', w)

    def test_the_banner_is_not_hidden_by_the_important_rule(self):
        """⚠️ `[hidden]{display:none !important}` စာရင်းထဲ `#rvnote` ပါသွားလျှင်
           ဘယ်တော့မှ မပေါ်တော့ပါ (ရေးပြီး ချက်ချင်း တွေ့ခဲ့)。"""
        self.assertNotIn("#rvnote[hidden]", self.s)
        self.assertIn('<div id="rvnote">', self.s)


class SmallThings(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_video_shows_a_frame_not_black(self):
        """⚠️ `preload="metadata"` က ဖရိမ်း မဆွဲ ⇒ မည်းနေပြီး
           「ပျက်နေတယ်」 ဟု ထင်စေသည် (ဖရိမ်း ကြည့်မှ တွေ့)。"""
        i = self.s.find("_vd2._poster=true")
        self.assertGreater(i, 0)
        self.assertIn('addEventListener("loadedmetadata"', self.s[i:i + 420])

    def test_a_zero_count_button_is_hidden(self):
        """⚠️ 「🔴 ၀ ခု စစ်ရန်」 က အဓိပ္ပာယ် မရှိ"""
        i = self.s.find('document.getElementById("nsec").textContent=SECS.length;')
        self.assertIn("_bs.hidden = !SECS.length", self.s[i:i + 420])


class Instructions(unittest.TestCase):
    def test_the_two_methods_are_stated_plainly(self):
        """⚠️ 「ဘယ်လို ဖြတ်ရမလဲ」 ကို ခန့်မှန်းခိုင်းလို့ မရ"""
        s = _src("web", "script.html")
        self.assertIn("ဖြတ်နည်း ၂ မျိုးပဲ ရှိပါတယ်", s)
        self.assertIn("စာကြောင်းကို နှိပ်", s)
        self.assertIn("စာလုံးတွေကို ဆွဲရွေး", s)

    def test_nothing_is_lost_by_hiding(self):
        """⚠️⚠️ ဖျောက်ထားတာက **ရလဒ်ကို မပြောင်းစေရ** — ဖျောက်တာက
           「ပြင်ခွင့်」 ပဲ ဖြစ်ရမည်、「ဆုံးဖြတ်ချက်」 မဟုတ်。

           ပုံသေ ၃ မျိုးက မတူသည်:
             `SDEL` (အသံ) · `UDEL` (❓) — ဗလာ = **ချန်** (engine မဖျက်)
             `SKEEP` (အနားယူ)         — ဗလာ = **engine ဖြတ်မည်** (ပုံသေ)
           သုံးခုလုံး ဗလာ ဖြစ်နေသရွေ့ ဖျောက်လိုက်တာက ရလဒ် မပြောင်းပါ —
           ⚙ နဲ့ ဖွင့်မှ ပြင်လို့ ရသည်。 ဗလာ မဟုတ်တော့လျှင် (တစ်ယောက်က
           ပုံသေ ပြောင်းလျှင်) ဖျောက်ထားတာက တိတ်တဆိတ် ပြောင်းရာ ကျမည်。"""
        s = _src("web", "script.html")
        self.assertIn("var SDEL={}, TRIM={};", s)
        i = s.find("var UDEL")
        self.assertGreater(i, 0)
        self.assertIn("UDEL={}", s[i:i + 60])
        j = s.find("var SKEEP")
        self.assertGreater(j, 0)
        self.assertIn("SKEEP={}", s[j:j + 60])


class PauseDial(unittest.TestCase):
    """ကြားထဲ ခဏရပ် — **တည်းဖြတ်ခန်းမှာ ချိန်လို့ ရရမည်**

    ⚠️ Zin ၂၀၂၆-၁၀-၀၄: 「ကြားထဲမှာ တိတ်နေတဲ့ space တွေကို ဘယ်လို ဖြတ်ရမှာလဲ」。
       engine က ဖြတ်ပြီးသား ဖြစ်ပေမယ့် ကိန်းက upload စာမျက်နှာမှာ ရှိပြီး
       တည်းဖြတ်ခန်းမှာ **မရှိ**ခဲ့ပါ ⇒ မမြင်ရ · ချိန်လို့ မရ。

    တိုင်းထားချက် (Zin ရဲ့ ဖိုင် · တကယ့် `cut.plan()`):
        min_sil ၀.၅၅ (ပုံသေ) → ဖြတ် ၂၆ · ဖယ် ၈၇.၁s (၄၈.၇%)
        min_sil ၀.၃၀        → ဖြတ် ၄၁ · ဖယ် ၉၀.၆s (၅၀.၇%)  = **+၃.၅s**
        min_sil ၀.၂၅        → ဖြတ် ၄၈ · ဖယ် ၉၃.၀s (၅၂.၁%)
        **အားလုံးမှာ စကားပေါ် ကျတာ ၀ ခု** ⇒ တင်းတင်း ထားလည်း ဘေးကင်း。

    ⚠️ ကျန်နေတဲ့ တိတ်ဆိတ်မှုရဲ့ အများစုက **ဝါကျ အတွင်း** ဖြစ်သည် —
       ချန်ထားတဲ့ ဝါကျ ၅၅.၆s ထဲမှာ ၉.၃s (၁၇%)。 အဲဒီ တိတ်ဆိတ်မှုတွေရဲ့
       p90 က ၀.၅၄s ဖြစ်ပြီး ပုံသေ min_sil က ၀.၅၅ ⇒ **မဖြတ်ဖြစ်**ခဲ့ခြင်း。
       ဒါကြောင့် ဒီ dial က တကယ် အရေးပါသည်。

    ⚠️⚠️ အရေအတွက်ကို browser မှာပဲ တွက်သည် — `WAVE.db` (၂၀ms RMS) နဲ့
       server ရဲ့ `thr_of` အတိအကျ တူသော threshold。 တိုက်စစ်ထား:
       ၀.၅၅ ⇒ ၂၆ vs ၂၆ · ၀.၇၀ ⇒ ၂၄ vs ၂၄ (**အတိအကျ**)、တင်းတဲ့ဘက်မှာ
       ၃–၆ ကွာ (planner က ၀.၀၈s အောက်ကို ကျော်ပြီး အပိုင်းတိုတွေ ပေါင်းသည်)
       ⇒ 「~」 နဲ့ **ခန့်မှန်းမှန်း ပြောရမည်**。
    """

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_dial_is_in_the_editor(self):
        self.assertIn('id="pzbox"', self.s)
        self.assertIn('id="pzr"', self.s)

    def test_it_is_one_number_not_two(self):
        """⚠️ ကိန်း ၂ လုံး ပြလျှင် ရှုပ်မည် — ချန်မယ့် အရှည်က လိုက်ညှိသည်"""
        i = self.s.find('<div id="pzbox">')
        w = self.s[i:i + 700]
        self.assertEqual(w.count('type="range"'), 1)
        self.assertIn("ခဏရပ်တိုင်း", self.s)

    def test_it_is_hidden_once_the_cut_is_frozen(self):
        """⚠️ `body.rv` မှာ ဖြတ်မှတ် အေးခဲပြီး — ချိန်လို့ ရသလို ပြလျှင် လိမ်ရာ ကျ"""
        self.assertIn("body.rv #pzbox{display:none}", self.s)

    def test_the_bounds_come_from_the_server(self):
        """⚠️ UI မှာ ကိန်းသေ ရေးလျှင် style အလိုက် ကွဲတာကို ပြလို့ မရ"""
        i = self.s.find("function pzLoad(")
        w = self.s[i:i + 900]
        self.assertIn("c.bounds", w)
        self.assertIn("r.min=c.bounds[1]", w)

    def test_the_count_uses_the_same_threshold_as_the_server(self):
        """⚠️⚠️ threshold မတူလျှင် UI ပြောတာနဲ့ တကယ် ဖြတ်တာ ကွဲမည်"""
        i = self.s.find("function pzRuns(")
        w = self.s[i:i + 900]
        self.assertIn("waveThr()", w)
        self.assertIn("WAVE.db", w)
        self.assertIn("0.35", w)          # server ရဲ့ smoothing hit

    def test_the_count_is_labelled_as_an_estimate(self):
        """⚠️ voice ratio က browser မှာ မရှိ ⇒ အတိအကျ မဟုတ် — လိမ်မပြရ"""
        i = self.s.find("function pzPaint(")
        self.assertIn('"s"+(n===null?"" : " · ~"+n+" နေရာ")', self.s[i:i + 700])

    def test_it_repaints_when_the_waveform_arrives(self):
        """⚠️ လှိုင်းပုံ မရောက်ခင် ဆွဲမိလျှင် ကိန်း မပါဘဲ ကျန်မည် (စမ်းစဉ် တွေ့)"""
        i = self.s.find('WAVE.peaks=pk; WAVE.dur=buf.duration; WAVE.state="ok";')
        self.assertIn("pzPaint()", self.s[i:i + 420])

    def test_the_server_keeps_the_pair_valid(self):
        """⚠️ `keep_pause > min_sil` ဖြစ်လျှင် ဖြတ်မှတ် ရေတွက်ထဲ ပါပေမယ့်
           ဘာမှ မဖြစ် (no-op) — server က ညှိရမည်。"""
        a = _src("api", "main.py")
        i = a.find('if "min_sil" in (b or {}):')
        self.assertGreater(i, 0)
        w = a[i:i + 900]
        self.assertIn("round(_ms * 0.85, 3)", w)
        self.assertIn("_RC.clean(", w)


if __name__ == "__main__":
    unittest.main(verbosity=2)
