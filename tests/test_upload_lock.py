# -*- coding: utf-8 -*-
"""ပုံစံ မရွေးမချင်း upload ကို **မြင်သာအောင် ပိတ်**ရမည်

⚠️⚠️ ၂၀၂၆-၁၀-၀၃ Zin: 「ဗီဒီယို upload လုပ်လို့ မရဘူး ဖြစ်နေတယ်」。
   စစ်ကြည့်တော့ server · auth · chunk အားလုံး အဆင်ပြေပြီး (HTTP 200)
   `start()` ရဲ့ guard တစ်ခုမှာ ရပ်နေတာ:

       if(!cine && !state.vfmt){ alert('ဒီဗီဒီယိုက ဘယ်ပုံစံလဲ ရွေးပေးပါ'); return; }

   alert တစ်ခါ ပေါ်ပြီး ပျောက်သွားတာက **「upload မရဘူး」 ဟု ထင်စေ**သည် —
   Zin ကိုယ်တိုင် အဲဒီလို ထင်ခဲ့သည်。 ⇒ နှိပ်ပြီးမှ ပြောတာထက်
   **နှိပ်လို့ မရကြောင်း ကြိုပြ**ရမည်。

⚠️ ပုံစံ ရွေးစရာက upload ခလုတ်ရဲ့ **အပေါ်မှာ** ရှိသည် (တိုင်းထား:
   y ၂၆၈၃ vs ၂၇၄၈) ⇒ မြှား 「↑」。 「အောက်မှာ」 ဟု ရေးမိခဲ့ပြီး
   browser မှာ တကယ် တိုင်းမှ တွေ့ရသည်。
"""
import io
import os
import unittest

HERE = os.path.dirname(__file__)


def _src(*p):
    return io.open(os.path.join(HERE, "..", *p), encoding="utf-8").read()


class Lock(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "app.js")

    def test_the_lock_exists(self):
        self.assertIn("function uplock()", self.s)
        i = self.s.find("function uplock()")
        w = self.s[i:i + 900]
        self.assertIn("d.disabled = need", w)
        self.assertIn("classList.toggle('locked', need)", w)

    def test_it_matches_the_guard_in_start(self):
        """⚠️⚠️ **အရေးကြီးဆုံး** — ခလုတ်က ပိတ်ပြီး `start()` က ခွင့်ပြုလျှင်
           (သို့) ပြောင်းပြန်ဆိုလျှင် သုံးစွဲသူ ပိုရှုပ်မည်。 စည်းမျဉ်း တူရမည်。
        """
        i = self.s.find("function uplock()")
        w = self.s[i:i + 900]
        self.assertIn("!isCine() && !state.vfmt", w)
        j = self.s.find("if(!cine && !state.vfmt){")
        self.assertGreater(j, 0, "start() ထဲက guard မတွေ့")

    def test_it_runs_on_every_path_that_changes_the_need(self):
        """⚠️ ပုံစံ ရွေးချိန် · style ပြောင်းချိန် · စာမျက်နှာ ဆောက်ချိန်"""
        self.assertGreaterEqual(self.s.count("uplock();"), 3)
        i = self.s.find("state.vfmt=vf.getAttribute('data-vfmt')")
        self.assertGreater(i, 0)
        self.assertIn("uplock()", self.s[i:i + 400])

    def test_cinematic_is_not_locked(self):
        """⚠️ cinematic မှာ `vfmt` မလို — `start()` နဲ့ တူညီရမည်"""
        i = self.s.find("function uplock()")
        w = self.s[i:i + 900]
        self.assertIn("!isCine()", w)

    def test_the_hint_points_the_right_way(self):
        """⚠️ ရွေးစရာက **အပေါ်မှာ** (browser မှာ တိုင်းထား)"""
        self.assertIn("↑ အပေါ်မှာ", self.s)
        self.assertNotIn("↑ အောက်မှာ", self.s)

    def test_the_original_note_comes_back(self):
        """⚠️ ရွေးပြီးတာနဲ့ 「MP4 · MOV · 4K …」 ပြန်ပေါ်ရမည်"""
        i = self.s.find("function uplock()")
        w = self.s[i:i + 1100]
        self.assertIn("data-was", w)
        self.assertIn("n.textContent = n.getAttribute('data-was')", w)

    def test_both_languages(self):
        i = self.s.find("function uplock()")
        w = self.s[i:i + 1100]
        self.assertIn("First choose what kind of video", w)


class Style(unittest.TestCase):
    def test_the_locked_look_is_defined(self):
        c = _src("web", "app.css")
        self.assertIn(".dropbig.locked", c)
        self.assertIn("cursor:not-allowed", c)

    def test_hover_is_suppressed_when_locked(self):
        """⚠️ မပိတ်လျှင် ပိတ်ထားတဲ့ ခလုတ်က နှိပ်လို့ရသလို ခံစားရမည်"""
        c = _src("web", "app.css")
        self.assertIn(".dropbig.locked:hover", c)


if __name__ == "__main__":
    unittest.main(verbosity=2)
