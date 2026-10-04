# -*- coding: utf-8 -*-
"""ဗီဒီယို တစ်ခုလုံးရဲ့ **မြေပုံ** — ကြည့်ရုံ (ဖြတ်လို့ မရ)

⚠️⚠️ ဒီ feature က **ရှိပြီးသား** ဖြစ်ခဲ့သည်。 git သမိုင်း:

  ၂၀၂၆-၀၉-၂၂  Zin: 「Audio လှိုင်းအကုန်လုံး script editor မှာ လာပြပေးပါ ·
              engine မဖြတ်ဘူး ပြပဲပြပေး · user ကိုယ်တိုင် ဆုံးဖြတ်」
              ⇒ တည်ဆောက်ခဲ့သည် (ဆွဲရွေး → နားထောင် → ✕ ဖြတ် / ↩ ပြန်ချန်)
  ၂၀၂၆-၀၉-၂၄  commit 7cffb70 「infra · UI · B-roll — လုပ်ဆောင်နေဆဲ အလုပ်များ」
              မှာ `<canvas id="tlc">` နဲ့ `tlBind(); tlDraw();` **ခေါ်ချက်
              ၂ ကြောင်း** ဖျက်ခံရသည်。 `tlDraw` · `tlBind` · `tlDrops` ·
              `TSEL` (၄၄ ကြိမ်) · CSS အားလုံး **ကျန်ခဲ့**သည်။
  ၂၀၂၆-၁၀-၀၄  browser မှာ စစ်တော့: `typeof tlDraw === "function"` ဖြစ်ပြီး
              `document.getElementById("tlc") === null`。 ဆိုလိုတာက
              ၁၀ ရက်လောက် **ဘယ်သူမှ မမြင်ခဲ့ပါ**。

⚠️ Zin ၂၀၂၆-၁၀-၀၄ (Descript ပြပြီး): **「ကြည့်ရုံပဲ ထားပြီး လုပ်ပေးပါ」**
   ⇒ ✕ ဖြတ် · ↩ ပြန်ချန် · ဆွဲရွေး ခလုတ်တွေ **မပြန်ထည့်ရ**。
   ဖြတ်နည်း ၃ မျိုး (ဝါကျ နှိပ် · စာလုံး ဆွဲရွေး · strip ဆွဲရွေး) ဖြစ်လျှင်
   「အဆင့်ဆင့်တွေက user တွေကို ပိုရှုပ်စေတယ်」 ဆိုတဲ့ ပြဿနာ ပြန်ဖြစ်မည်。

⚠️ Descript ရဲ့ အောက်ပိုင်း (clip အတန်း + text layer ၂ ခု + caption chip)
   ကို **မယူပါ** — အဲဒါတွေက 「ရွှေ့လို့ရ · အလွှာထပ်လို့ရ · ဘယ်နေရာမဆို
   ထည့်လို့ရ」 ဟု ကတိပေးသည်。 IKKI က ဖျက်တာပဲ လုပ်ပြီး ရိုက်ထားတဲ့
   အစီအစဉ်အတိုင်း ထားသည် ⇒ မလုပ်နိုင်တာကို လုပ်နိုင်သလို ပြတာက
   မြေပုံ မရှိတာထက် ပိုဆိုးသည်。
"""
import io
import os
import re
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(*p):
    return io.open(os.path.join(_R, *p), encoding="utf-8").read()


class OnThePage(unittest.TestCase):
    """⚠️ **အရေးကြီးဆုံး** — ကုဒ် ရှိရုံနဲ့ မလုံလောက်、စာမျက်နှာပေါ် ရောက်ရမည်"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_canvas_is_in_the_markup(self):
        """၂၀၂၆-၀၉-၂၄ မှာ ပျောက်သွားတဲ့ စာကြောင်း အတိအကျ"""
        self.assertIn('<canvas id="tlc">', self.s)

    def test_both_calls_are_made(self):
        """⚠️ `tlBind(); tlDraw();` ၂ ကြောင်း ပျောက်လို့ feature တစ်ခုလုံး
           လက်လှမ်းမမီ ဖြစ်ခဲ့သည်。"""
        # ⚠️ ၂၀၂၆-၁၀-၀၄ — အတန်း ၄ ခု ဖြစ်သွားသဖြင့် `tlAll()` က အားလုံး ဆွဲသည်
        self.assertIn("tlBind(); tlAll()", self.s)

    def test_it_is_redrawn_on_every_edit(self):
        """⚠️ ဖျက်ချက် ပြောင်းတိုင်း မလိုက်ပြောင်းလျှင် **မှားတဲ့ ပုံ** ပြနေမည်"""
        # ⚠️ ၂၀၂၆-၁၀-၀၄ — `tlRefresh()` က ဒေတာ အတန်း ၂ ခု (စာတန်း + လှိုင်း)
        #    ကိုသာ ပြန်ဆွဲသည်。 ရုပ်ပုံ အတန်းကို ပြန်မထုတ်ပါ — ဖရိမ်း ထုတ်တာ
        #    ကြာပြီး ဖျက်တိုင်း ထုတ်နေလျှင် သုံးလို့ မရတော့。
        i = self.s.find("function counts(){")
        j = self.s.find("\n}", i)
        self.assertIn("tlRefresh()", self.s[i:j])

    def test_the_legend_is_there(self):
        """⚠️ အရောင် ၄ မျိုးက ဘာကို ဆိုလိုလဲ မပြလျှင် မြေပုံက အဓိပ္ပာယ် မရှိ"""
        for w in ("ဝါကျ", "စာတမ်းမှာ မပါ", "engine ဖြတ်ထား", "ဖျက်မည်"):
            self.assertIn(w, self.s, w)


class ViewOnly(unittest.TestCase):
    """⚠️⚠️ Zin ရဲ့ ဆုံးဖြတ်ချက် — 「ကြည့်ရုံ」"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_there_is_no_cut_button_on_the_map(self):
        for i in ("tlcut", "tlkeep", "tlclr", "tlplay"):
            self.assertNotIn('id="%s"' % i, self.s, i)

    def test_the_drag_to_select_handlers_are_gone(self):
        """⚠️ handler ကျန်နေလျှင် နောက်တစ်ယောက်က ခလုတ် ပြန်တပ်ရုံနဲ့
           ဖြတ်နည်း ၃ မျိုး ပြန်ဖြစ်မည်。"""
        i = self.s.find("function tlBind(){")
        j = self.s.find("\nfunction tlHead(")
        w = self.s[i:j]
        self.assertGreater(j, i)
        self.assertNotIn("_ovl(MCUT", w)
        self.assertNotIn("_sub(MKEEP", w)
        self.assertNotIn("TDRAG", w)

    def test_clicking_seeks(self):
        i = self.s.find("function tlBind(){")
        j = self.s.find("\nfunction tlHead(")
        # ⚠️ ၂၀၂၆-၁၀-၀၄ — ထုတ်ပြီးသားမှာ `tOf()` က **ထွက်** အချိန် ပြန်ပေး
        #    သဖြင့် `seekTo()` (မူရင်း လက်ခံ) ကို တန်းမပေးရတော့。
        self.assertIn("seekTo(OUT.on ? o2s(_t) : _t)", self.s[i:j])

    def test_no_multitrack_was_added(self):
        """⚠️ Descript ရဲ့ clip အတန်း · text layer · caption chip —
           IKKI က ရွှေ့တာ · အလွှာထပ်တာ မလုပ်ပါ。"""
        for w in ("grid-template-rows", "track-row", "cliprow"):
            self.assertNotIn(w, self.s, w)


class Playhead(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_it_moves_without_redrawing_the_canvas(self):
        """⚠️ ၆၀fps မှာ canvas ပြန်ဆွဲလျှင် ဝါကျ · ဖျက်ချက် အားလုံးကို
           frame တိုင်း ပြန်ဖြတ်သန်းရမည် (ဖြုန်းတီးမှု)。"""
        i = self.s.find("function tlHead(")
        w = self.s[i:i + 600]
        self.assertIn("e.style.left", w)
        self.assertNotIn("tlDraw()", w)

    def test_it_is_driven_by_the_same_tick_as_the_highlight(self):
        i = self.s.find("function tickAll(")
        self.assertIn("tlHead(", self.s[i:i + 900])

    def test_it_hides_when_playback_stops(self):
        i = self.s.find("function stopAll(")
        self.assertIn("tlHead(null)", self.s[i:i + 700])


class Layout(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_a_video_with_no_proxy_is_really_hidden(self):
        """⚠️⚠️ `.vbar video{display:block}` က UA ရဲ့ `[hidden]{display:none}`
           ကို **လွှမ်း**သည် ⇒ proxy မရှိတဲ့ job မှာ မည်းနေသော ဘောင် ပေါ်ပြီး
           「ပျက်နေတယ်」 ဟု ထင်စေသည် (ကိုယ်တိုင် သတိပေးထားပြီး ကိုယ်တိုင်
           ကျခဲ့ — ဖရိမ်း ကြည့်မှ တွေ့)。"""
        self.assertIn(".vbar video[hidden]{display:none}", self.s)

    def test_the_side_column_does_not_squeeze_the_transcript(self):
        """⚠️ `.wrap` က ~၇၈၀px ⇒ ညာဘက် ၃၇၂px ထပ်ထည့်လျှင် စာတမ်းက
           ၃၅၄px ကျန်မည် (တိုင်းထား)。 Descript pane ဖြစ်သွားပြီ ⇒ pane က
           ကျယ်သော်လည်း **စာဖတ်ရ အကျယ်** (`--w`) ကို ထိန်းရသည်。
           တိုင်းထား: ၁၂၈၀px မှာ စာတမ်း pane ၉၀၈ · ဘေးတိုင် ၃၇၂。"""
        i = self.s.find("@media(min-width:1100px){")
        self.assertGreater(i, 0)
        w = self.s[i:i + 1700]
        self.assertIn("#spane>*{max-width:var(--w)", w)
        # ⚠️ `order` — `.vbar` က DOM ထဲ ပထမ ဖြစ်နေသဖြင့် (တိုင်းထား:
        #    vbar x=18 · spane x=390)。 DOM ရွှေ့လျှင် `<video>` ပြန်စမည်。
        self.assertIn("main.editor>.vbar{order:2;flex:0 0 372px", w)

    def test_the_side_column_stays_put_while_the_script_scrolls(self):
        """⚠️ ရည်ရွယ်ချက်က 「ဗီဒီယိုက ပုံသေ · စာတမ်းပဲ ရွေ့」。 အရင်က
           `position:sticky` နဲ့ လုပ်ခဲ့သည်; ယခု pane နှစ်ခု **သီးသန့်စီ**
           scroll လုပ်သည် ⇒ sticky မလိုတော့ပါ。"""
        i = self.s.find("@media(min-width:1100px){")
        w = self.s[i:i + 1700]
        self.assertIn("html,body{height:100%;overflow:hidden}", w)
        self.assertIn("#spane{order:1;flex:1 1 auto;min-width:0;overflow-y:auto", w)
        self.assertIn("overflow-y:auto", w[w.find("main.editor>.vbar{"):])


class Graphics(unittest.TestCase):
    """⚠️ `vplan` က render ပြီးမှ ထွက်သည် — ဖြတ်ချက် စစ်ချိန်မှာ မရှိသေး"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_layer_is_only_drawn_when_there_is_a_plan(self):
        """⚠️ မရှိဘဲ ခန့်မှန်း ဆွဲလျှင် **မှားတဲ့ နေရာ** ပြမည် —
           ဘာမှ မပြတာက ပိုကောင်းသည်。"""
        # ⚠️ ၂၀၂၆-၁၀-၀၄ — `vplan.at` က **ထွက်** အချိန် ဖြစ်ကြောင်း တိုင်းပြီး
        #    သိရသဖြင့် မူရင်း ဝင်ရိုးပေါ် ဆွဲတာကို ရပ်လိုက်သည် ⇒ `OUT.on` ပါ လိုသည်
        #    (၄၇.၁၂s က ၇၃% အစား ၂၆% မှာ ပေါ်နေခဲ့)。 ရည်ရွယ်ချက် မပြောင်း:
        #    **မရှိဘဲ ခန့်မှန်း မဆွဲရ**。
        i = self.s.find("if(OUT.on && VPLAN && VPLAN.length){")
        self.assertGreater(i, 0)

    def test_its_legend_is_hidden_until_then(self):
        # ⚠️ ၂၀၂၆-၁၀-၀၄ — အောက်ခြေ timeline ဆောက်ရင်း markup ပြောင်းသွားသည်。
        #    အညွှန်းက **ပေါ်ရမယ့် အချိန်မှာသာ** ပေါ်ရမည် ဆိုတာက မပြောင်း。
        self.assertIn('id="tlgx" hidden', self.s)
        self.assertIn("if(_gx) _gx.hidden=!_on;", self.s)
        self.assertIn("_on=!!(VPLAN && VPLAN.length)", self.s)

    def test_a_missing_graphic_is_not_drawn(self):
        """⚠️ engine က စီစဉ်ပြီး ဆောက်မရခဲ့တာကို ထွက်ခဲ့သလို မပြရ"""
        i = self.s.find("if(OUT.on && VPLAN && VPLAN.length){")
        self.assertIn("if(e.missing) return", self.s[i:i + 400])


class Summary(unittest.TestCase):
    def test_the_map_states_the_result(self):
        """⚠️ မြေပုံက ကိန်းကိုပါ ပြရမည် — 「၂:၅၉ → ၂:၂၉ (−၃၀.၂s)」"""
        s = _src("web", "script.html")
        i = s.find('var inf=document.getElementById("tlinfo")')
        self.assertGreater(i, 0)
        self.assertIn("tlDrops()", s[i:i + 500])


if __name__ == "__main__":
    unittest.main(verbosity=2)
