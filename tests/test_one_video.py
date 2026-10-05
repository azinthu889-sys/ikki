# -*- coding: utf-8 -*-
"""editor — ဗီဒီယို **တစ်ခုတည်း** · အခြေအနေ ကတ်က ဗီဒီယို အောက် (Zin ၂၀၂၆-၁၀-၀၅)

「video view က တစ်ခုပဲ ပြရင်ရပါတယ်」 — cut_review မှာ ဖြတ်ပြီး preview က စာတမ်း
pane ထဲ · မူရင်း player က ညာ ⇒ ဗီဒီယို ၂ ခု ပေါ်ခဲ့。 ထုတ်နေဆဲ progress လည်း
စာတမ်း scroll ဆင်းထားလျှင် မမြင်ရ。
"""
import os
import unittest

R = os.path.join(os.path.dirname(__file__), "..", "web", "script.html")


class OneVideo(unittest.TestCase):
    def setUp(self):
        with open(R, encoding="utf-8") as f:
            self.s = f.read()

    def test_status_card_goes_under_the_video(self):
        self.assertIn("function dnPlace(el)", self.s)
        self.assertIn('el.id="dn"; el.className="done"; dnPlace(el);', self.s)
        self.assertIn("     dnPlace(el);\n", self.s)

    def test_cut_review_hides_the_source_player(self):
        # ၂၀၂၆-၁၀-၀၅: proxy ရှိလျှင် live player တစ်ခုတည်း · မရှိမှ server ဖိုင် (cutrev)
        self.assertIn('document.body.classList.toggle("cutrev", !_live);', self.s)
        self.assertIn("body.cutrev #vid,body.cutrev .vbar .vside{display:none !important}", self.s)

    def test_result_card_follows(self):
        self.assertIn("function donePlace()", self.s)
        self.assertIn("try{ donePlace() }catch(e){}", self.s)

    def test_crossing_the_breakpoint_replaces_cards(self):
        self.assertIn('mq.addEventListener("change", re)', self.s)


if __name__ == "__main__":
    unittest.main()
