# -*- coding: utf-8 -*-
"""Descript ပုံစံ **အောက်ခြေ timeline** — စနစ်က IKKI အတိုင်း

⚠️ Zin ၂၀၂၆-၁၀-၀၄: 「UI view ကို descript လို Edit timeline view နဲ့ ပြတာ
   ပိုနားလည်လွယ်ရမယ်。 **စနစ်ကိုက ikki အတိုင်း**နဲ့ UI view ကို descript လို」。

အတန်း ၄ ခု — အားလုံး **IKKI ရဲ့ တကယ့် ဒေတာ**:
    ပေတံ (အချိန်) · ရုပ်ပုံ (proxy ကနေ) · စာတန်း (ဝါကျ) · အသံလှိုင်း + ဖျက်ချက်

⚠️ Descript ရဲ့ clip ရွှေ့ခြင်း · အလွှာ ထပ်ခြင်း **မပါ** — IKKI က ဖျက်တာပဲ
   လုပ်ပြီး ရိုက်ထားတဲ့ အစီအစဉ်အတိုင်း ထားသည် ⇒ ရွှေ့လို့ရသလို ပြလျှင်
   မဖြစ်နိုင်တာကို ကတိပေးရာ ကျမည်。

⚠️⚠️ CSS grid ရဲ့ **ကိန်းသေ span ၂ မျိုးလုံး မှား**ခဲ့သည် — နှစ်ခုလုံး
   စာမျက်နှာ အမြင့် တိုင်းမှ တွေ့ရသည်:

     `grid-row: 1 / span 999`  ⇒ row ၉၉၉ ခု **တကယ် ဆောက်** ⇒ စာမျက်နှာ
                                 **၂၅,၉၄၇px** (စာရင်းက ၁,၇၅၇px ပဲ)
     `grid-row: 1 / -1`        ⇒ `-1` က **explicit** grid ရဲ့ နောက်ဆုံး မျဉ်း。
                                 explicit row မရှိ ⇒ row ၁ ခုသာ ⇒ row 1 က
                                 ၃၃၉px (ဘေးတိုင် အမြင့်) ဖြစ်ကာ စာရင်းက
                                 **၆၅၁px အောက်** ကျသည် (စာကြောင်း ၁ ကြောင်းပဲ)

   ⇒ JS က တကယ့် အရေအတွက်နဲ့ `span N` ပေးရသည်。
   ပြင်ပြီး တိုင်းထား: စာမျက်နှာ **၂,၄၆၀px** · စာရင်း **၃၄၇px** မှာ စ ·
   **စာကြောင်း ၆ ကြောင်း** ပထမ မျက်နှာပြင်မှာ。
"""
import io
import os
import re
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(*p):
    return io.open(os.path.join(_R, *p), encoding="utf-8").read()


class Rows(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_bar_has_all_four_rows(self):
        for i in ('id="tlruler"', 'id="tlfilm"', 'id="tlcaps"', 'id="tlc"'):
            self.assertIn(i, self.s, i)

    def test_every_row_is_real_ikki_data(self):
        """⚠️ ရုပ်ပုံက proxy ကနေ · စာတန်းက ဝါကျ · လှိုင်းက WAVE"""
        self.assertIn("function tlFilm(", self.s)
        self.assertIn("function tlCaps(", self.s)
        i = self.s.find("function tlCaps(")
        self.assertIn("D.sentences", self.s[i:i + 700])

    def test_no_multitrack_was_added(self):
        """⚠️ clip ရွှေ့ · အလွှာ ထပ် — IKKI က မလုပ်ပါ"""
        for w in ("draggable", "ondragstart", "clip-row", "track-lane"):
            self.assertNotIn(w, self.s, w)

    def test_the_captions_follow_the_deletions(self):
        i = self.s.find("function tlCaps(")
        self.assertIn('DEL[x.n]?"gone":""', self.s[i:i + 900])

    def test_a_missing_proxy_shows_nothing_invented(self):
        """⚠️ proxy မရှိလျှင် အတုအယောင် ပုံ မပြရ"""
        i = self.s.find("function tlFilm(")
        w = self.s[i:i + 900]
        self.assertIn("if(!VPROX || !dur)", w)
        self.assertIn("proxy မရှိပါ", w)


class Offscreen(unittest.TestCase):
    """⚠️⚠️ ဖရိမ်း ထုတ်ရာမှာ သုံးစွဲသူ မြင်နေရတဲ့ ဗီဒီယိုကို သုံးလျှင်
       ပုံ ခုန်သွားပြီး သူ timeline နှိပ်လိုက်ရင် ထုတ်နေတာ ပျက်သည်
       (စမ်းစဉ် တကယ် တွေ့: `FILM.done=false` နဲ့ filmstrip တဝက်)。"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_a_separate_hidden_video_is_used(self):
        self.assertIn("function filmVid(", self.s)
        i = self.s.find("function filmVid(")
        w = self.s[i:i + 500]
        self.assertIn("left:-9999px", w)
        self.assertIn("createElement(\"video\")", w)

    def test_the_visible_player_is_never_seeked_for_frames(self):
        i = self.s.find("function tlFilm(")
        j = self.s.find("/* ③ စာတန်း အတန်း")
        w = self.s[i:j]
        self.assertGreater(j, i)
        self.assertNotIn('getElementById("vid")', w)

    def test_the_loop_cannot_run_forever(self):
        """⚠️ seek မအောင်လျှင် အဆုံးမရှိ ဖြစ်နိုင်သည်"""
        i = self.s.find("function tlFilm(")
        self.assertIn("guard>n*4", self.s[i:i + 1800])


class GridSpan(unittest.TestCase):
    """⚠️⚠️ ကိန်းသေ span ၂ မျိုးလုံး မှားခဲ့သည် (အထက်က docstring)"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_no_hard_coded_span_in_css(self):
        # ⚠️ မှတ်ချက်ထဲက စာသားကို မရေတွက်ရ — **သတ်မှတ်ချက်** ကိုသာ စစ်သည်
        import re as _re
        css = _re.sub(r"/\*.*?\*/", "", self.s, flags=_re.S)
        i = css.find("@media(min-width:1100px){")
        self.assertGreater(i, 0)
        w = css[i:i + 900]
        self.assertNotIn("span 999", w)
        self.assertNotIn("grid-row:1 / -1", w)
        self.assertIn("main.editor > .vbar{grid-column:2;position:sticky", w)

    def test_the_span_is_computed_from_the_real_count(self):
        self.assertIn("function vbarSpan(", self.s)
        i = self.s.find("function vbarSpan(")
        w = self.s[i:i + 700]
        self.assertIn('"1 / span " + Math.max(1, n)', w)
        self.assertIn('e.offsetParent!==null', w)

    def test_fixed_children_are_excluded(self):
        """⚠️ `#tlbar` က fixed — row တစ်ခု ရေတွက်မိလျှင် နေရာ လွဲမည်"""
        i = self.s.find("function vbarSpan(")
        self.assertIn('getComputedStyle(e).position!=="fixed"', self.s[i:i + 700])

    def test_the_fixed_bar_is_outside_the_grid(self):
        """⚠️ `main` ထဲ ထားလျှင် grid က row ခွဲပေးသည်"""
        a = self.s.find('<div id="tlbar"')
        b = self.s.find("</main>")
        self.assertGreater(a, b, "tlbar က </main> ပြီးနောက် ရှိရမည်")


class DeadCss(unittest.TestCase):
    def test_the_2026_09_24_block_is_gone(self):
        """⚠️ သေနေသော `#tlc{height:76px}` က အသစ် `40px` ကို လွှမ်းနေခဲ့သည်"""
        s = _src("web", "script.html")
        self.assertEqual(len(re.findall(r"(?m)^#tlc\{", s)), 1)
        self.assertNotIn("#tl .tlh{", s)
        self.assertNotIn("#tl .tlb{", s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
