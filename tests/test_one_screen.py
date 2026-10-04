# -*- coding: utf-8 -*-
"""စာတမ်းက **စာမျက်နှာ** ဖြစ်ရမည် — ကျန်တာ အကုန် ⚙ ထဲ

⚠️⚠️ ၂၀၂၆-၁၀-၀၄ Zin: 「မင်းလုပ်ပေးတဲ့ပုံစံက user ကို ပိုပြီး ရှုပ်ထွေးသွားစေတယ်။
   မင်း အဆင်ပြေသလို **စနစ်တကျ** လုပ်ပေးပါ」。

   မှန်သည် — ကျွန်တော် မေးခွန်းတစ်ခုချင်းကို ခလုတ်တစ်ခုချင်း ထပ်ဖြည့်ခဲ့သည်
   (ဗီဒီယို bar · မြေပုံ · စာလုံး ရွေးချယ်မှု · SFX panel · ခဏရပ် dial)。
   တစ်ခုချင်း ကျိုးကြောင်း ရှိပေမယ့် **စုပေါင်းလိုက်တော့** သုံးလို့ မရတော့。

တိုင်းထားချက် (၅၉၄×၈၁၄ မျက်နှာပြင်):

    စာတမ်း မစခင် ကြိုရှိနေတာ   **၁,၁၄၀px**  (ဖန်သားပြင် ၈၁၄px)
    ⇒ စာမျက်နှာ ဖွင့်လိုက်ရင် **ပထမ စာကြောင်းကို မမြင်ရ**ပါ
    vbar ၆၂၃ · editnote ၁၂၁ · scrp ၄၉ · pzbox ၁၁၁

စီပြီးနောက်: **၅၉၇px** ⇒ မြင်ရသည်。 ကျယ်တဲ့မှာ (၁၂၈၀×၉၀၀):
**၃၄၇px · စာကြောင်း ၂၈ ကြောင်း ပထမ မျက်နှာပြင်မှာ**。

စည်းမျဉ်း ၃ ခု:
  ① စာမျက်နှာမှာ **လုပ်စရာ တစ်ခုပဲ** — စာတမ်း。
  ② ချိန်ညှိတာ မှန်သမျှ **⚙ တစ်ခုထဲ** (အသေးစိတ် · ဖျက်တာပဲ ပြ · ခဏရပ်)。
  ③ အပေါ်တန်းမှာ **ထွက်လမ်း + ဆက်သွား** သာ (🔴 က ရှိမှ ပေါ်သည်)。
"""
import io
import os
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(*p):
    return io.open(os.path.join(_R, *p), encoding="utf-8").read()


class OneGear(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_settings_live_in_one_place(self):
        self.assertIn('<details class="setd" id="setbox">', self.s)

    def test_every_dial_is_inside_it(self):
        """⚠️ တစ်ခုခု ပြင်ပမှာ ကျန်ခဲ့လျှင် 「ဘယ်မှာလဲ」 ပြန်ဖြစ်မည်"""
        i = self.s.find('<details class="setd" id="setbox">')
        j = self.s.find("</details>", i)
        w = self.s[i:j]
        for k in ('id="bsimple"', 'id="bonly"', 'id="pzbox"'):
            self.assertIn(k, w, k)

    def test_the_pause_box_is_not_in_the_page_flow(self):
        """⚠️ `pzbox` က စာတမ်းအထက်မှာ ၁၁၁px ယူနေခဲ့သည်"""
        i = self.s.find('id="setbox"')
        j = self.s.find("</details>", i)
        k = self.s.find('<div id="pzbox">')
        self.assertGreater(k, i, "pzbox က ⚙ ထဲ ရှိရမည်")
        self.assertLess(k, j, "pzbox က ⚙ ထဲ ရှိရမည်")

    def test_a_closed_gear_really_hides_its_panel(self):
        """⚠️⚠️ `position:absolute` ထည့်လိုက်လျှင် browser ရဲ့
           `details:not([open])>*:not(summary){display:none}` က **မကိုင်တော့** ⇒
           ပိတ်ထားလည်း panel ပေါ်နေသည် (စမ်းစဉ် တွေ့)。"""
        self.assertIn(".setd:not([open]) .setb{display:none}", self.s)

    def test_the_panel_fits_a_narrow_screen(self):
        """⚠️ `right:0` က ကျဉ်းတဲ့ မျက်နှာပြင်မှာ ဘယ်ဘက် ကျော်ထွက်သည်
           (ဖရိမ်းမှာ တွေ့ — ၂၉၀px panel · ၅၉၄px မျက်နှာပြင်)。"""
        # ⚠️ `@media(max-width:760px)` block က **၂ ခု** ရှိသည် (timeline အတွက်
        #    နောက်တစ်ခု ထပ်လာ) ⇒ `.setb` စည်းမျဉ်းကိုသာ တိုက်ရိုက် ရှာရမည်。
        self.assertIn(".setb{position:fixed", self.s)


class TopBar(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_only_exit_and_continue_remain(self):
        """⚠️ အပေါ်တန်းမှာ ခလုတ် ၅ ခု ရှိခဲ့သည်"""
        i = self.s.find('<div class="acts">')
        j = self.s.find("</div>", self.s.find('id="bok"'))
        w = self.s[i:j]
        self.assertIn('href="/"', w)          # ထွက်လမ်း
        self.assertIn('id="bok"', w)          # ဆက်သွား
        self.assertIn('id="setbox"', w)       # ⚙
        # ⚠️ ချိန်ညှိချက် ခလုတ်တွေ **တိုက်ရိုက်** မရှိရ — ⚙ ထဲမှာသာ
        g = w.find('id="setbox"')
        self.assertGreater(w.find('id="bsimple"'), g)
        self.assertGreater(w.find('id="bonly"'), g)

    def test_the_warning_button_hides_at_zero(self):
        i = self.s.find('document.getElementById("nsec").textContent=SECS.length;')
        self.assertIn("_bs.hidden = !SECS.length", self.s[i:i + 420])


class Compact(unittest.TestCase):
    """⚠️ ကျဉ်းတဲ့ မျက်နှာပြင်မှာ player က ၆၂၃px ယူနေခဲ့သည်"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_narrow_player_is_compact(self):
        i = self.s.find("@media(max-width:1099px){")
        self.assertGreater(i, 0)
        w = self.s[i:i + 700]
        self.assertIn(".vbar video{width:132px", w)
        self.assertIn(".vbar .vnote{display:none}", w)
        self.assertIn("#tlc{height:30px}", w)

    def test_the_help_is_one_line(self):
        """⚠️ လမ်းညွှန်က ၁၂၁px (၃ ကြောင်း) ယူနေခဲ့သည်"""
        i = self.s.find('<div class="editnote"')
        j = self.s.find("</div>", i)
        w = self.s[i:j]
        self.assertEqual(w.count("<span"), 2, w)   # ⚠️ လမ်းညွှန် + editstate

    def test_the_row_shows_how_to_delete(self):
        """⚠️⚠️ 「ဘယ်လို ဖျက်ရမလဲ」 ဆိုတာ **ကြည့်ရုံနဲ့ သိရမည်** —
           စာကြောင်းတိုင်းမှာ 「✕ ဖျက်」 ပေါ်ရသည် (`.act`)。
           ရိုးရှင်းစနစ်မှာ ဖျောက်မိလျှင် မေးခွန်း ပြန်ဖြစ်မည်。"""
        i = self.s.find("body.simple .snd")
        self.assertNotIn(".act", self.s[i:i + 420])


if __name__ == "__main__":
    unittest.main(verbosity=2)
