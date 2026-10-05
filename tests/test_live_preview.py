# -*- coding: utf-8 -*-
"""preview ↔ timeline ချိတ်ဆက် · ဖြတ်ချက် panel tab (Zin ၂၀၂၆-၁၀-၀၅)

「timeline နဲ့ preview video နဲ့ ချိတ်ဆက်မှု မရှိဘူး · Timeline ထဲ ဖျက်လိုက်တာတွေကို
 Preview မှာ မပြပါနဲ့ · ညှိလိုက်တာနဲ့ Preview ပါ ပြောင်း」
「ဒီ ရွေးချယ်စရာတွေကို menu button နဲ့ စနစ်တကျ · မလိုတာ ဖြုတ်」
"""
import os
import unittest

R = os.path.join(os.path.dirname(__file__), "..", "web", "script.html")


class LivePreview(unittest.TestCase):
    def setUp(self):
        with open(R, encoding="utf-8") as f:
            self.s = f.read()

    def test_preview_skips_engine_silences_and_adjustments(self):
        i = self.s.find("function tlDrops(")
        w = self.s[i:i + 2600]
        self.assertIn('if(SKEEP[k]) return;', w)
        self.assertIn("if(SADJ[k]){ d.push([SADJ[k][0], SADJ[k][1]]); return }", w)

    def test_cut_review_uses_the_live_player(self):
        self.assertIn('var _live=!!VPROX;', self.s)
        self.assertIn('document.body.classList.toggle("cutrev", !_live);', self.s)

    def test_approved_decisions_are_restored(self):
        i = self.s.find("function restoreDecisions(")
        w = self.s[i:i + 2600]
        self.assertIn("JOBROW.keep_n", w)
        self.assertIn("ov._drop_exact", w)
        self.assertIn("ov._keep", w)
        self.assertIn("try{ restoreDecisions() }catch(e){}", self.s)

    def test_changes_in_cut_review_can_be_applied(self):
        i = self.s.find("function tcApply(")
        w = self.s[i:i + 1400]
        self.assertIn('/recut"', w)
        self.assertIn("bk.click(); bk.click();", w)

    def test_panel_is_tabbed(self):
        self.assertIn("function cutPanelTabs(el, jid)", self.s)
        self.assertIn("try{ cutPanelTabs(el, jid) }catch(e){}", self.s)
        for k in ('["cut","✂ ဖြတ်ချက်"]', '["motion","✨ Motion"]', '["sound","🔊 အသံ"]', '["caps","T စာတန်း"]'):
            self.assertIn(k, self.s)

    def test_script_is_editable_in_cut_review(self):
        # 「script မှာလဲ ဖျက်လို့ရအောင်」 — cut_review မှာ rv (အေးခဲ) မထား
        self.assertIn('if(j.status!=="cut_review") document.body.classList.add("rv");', self.s)

    def test_header_button_exports_in_cut_review(self):
        self.assertIn("function bokCutPaint()", self.s)


if __name__ == "__main__":
    unittest.main()
