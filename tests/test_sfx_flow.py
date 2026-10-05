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
        i = self.s.find('if(D.status==="review" && !window._autoGo){')
        self.assertGreater(i, 0)
        self.assertIn("sfxOpen(); return }", self.s[i:i + 300])

    def test_cut_review_is_skipped_with_a_plan(self):
        self.assertIn('if(st==="cut_review" && planGet(jid)){', self.s)
        i = self.s.find('if(st==="cut_review" && planGet(jid)){')
        w = self.s[i:i + 1600]
        self.assertIn('/cutok"', w)
        self.assertIn("preview:!!_pl.preview", w)

    def test_sfx_button_never_disappears_in_cut_review(self):
        # 「SFX ဆက်သွားမည့် ခလုတ်ပါ ပျောက်နေတယ်」
        self.assertIn('var want = dirty ? "💾 သိမ်းပြီး ပြန်ထုတ်" : (_na ? _na.lab : "✨ Motion · SFX →");', self.s)
        self.assertIn('var nx=document.getElementById("tlnext"); if(nx) nx.hidden=false;', self.s)

    def test_pro_basics(self):
        # 「Professional app တစ်ခု ဖြစ်အောင်」 — step bar · Space ဖွင့်/ရပ် · ပထမ frame · မသိမ်းရသေး သတိပေး
        self.assertIn('<ol class="steps" id="steps"', self.s)
        self.assertIn("function stepPaint()", self.s)
        self.assertIn('else if(e.key===" "){ e.preventDefault(); if(PLAYALL) stopAll();', self.s)
        self.assertIn('<video id="vid" playsinline preload="auto"></video>', self.s)
        self.assertIn('window.addEventListener("beforeunload"', self.s)

    def test_next_button_does_the_next_step(self):
        # 「နှိပ်လို့ မရ」 — panel ရောက်ပြီးရင် ခလုတ်က Preview/Export ကို တကယ် စ
        self.assertIn("function nextAction()", self.s)
        self.assertIn("var _na=nextAction(); if(_na && _na.el){ _na.el.click(); return }", self.s)

    def test_preview_then_export(self):
        self.assertIn("function exportAfterPreview()", self.s)
        self.assertIn('JOBROW.mode==="prev"', self.s)
        self.assertIn('body:JSON.stringify({motion:pl.motion||"auto", preview:false})', self.s)


if __name__ == "__main__":
    unittest.main()
