# -*- coding: utf-8 -*-
"""ဖြတ် → ✨ Motion·SFX → 👁 Preview → ✅ Export (Zin ၂၀၂၆-၁၀-၀၅)

「ဖြတ်ချက်စစ်တာကို cut အဆင့်မှာတင် လုပ်လို့ရ ⇒ အဲဒီအဆင့် ဖြုတ် · SFX အဆင့် သွားဖို့
 ခလုတ် · SFX ပြီး preview မှာ စစ် · အဆင်ပြေရင် export」
server အဆင့်များ (approve → cut → cutok) မပြောင်း — client က cut_review ကို အလိုလို ကျော်。
"""
import os
import unittest

R = os.path.join(os.path.dirname(__file__), "..", "web", "script.html")


class SfxFlow(unittest.TestCase):
    def setUp(self):
        with open(R, encoding="utf-8") as f:
            self.s = f.read()

    def test_review_button_opens_the_sfx_panel(self):
        self.assertIn('id="bok">✨ Motion · SFX →</button>', self.s)
        self.assertIn('if(D.status==="review" && !window._autoGo){ sfxOpen(); return }', self.s)

    def test_cut_review_is_skipped_with_a_plan(self):
        self.assertIn('if(st==="cut_review" && planGet(jid)){', self.s)
        i = self.s.find('if(st==="cut_review" && planGet(jid)){')
        w = self.s[i:i + 1600]
        self.assertIn('/cutok"', w)
        self.assertIn("preview:!!_pl.preview", w)

    def test_preview_then_export(self):
        self.assertIn("function exportAfterPreview()", self.s)
        self.assertIn('JOBROW.mode==="prev"', self.s)
        self.assertIn('body:JSON.stringify({motion:pl.motion||"auto", preview:false})', self.s)


if __name__ == "__main__":
    unittest.main()
