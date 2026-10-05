# -*- coding: utf-8 -*-
"""timeline ✂ အတန်း — ဖြတ်ချက် အားလုံး · တစ်ချက်နှိပ် ဖြတ်/ပြန်ထည့် · ချိန်ညှိ
(Zin ၂၀၂၆-၁၀-၀၅) + 「ဖြတ်ပြီး · Motion · SFX →」 ခလုတ်"""
import os
import unittest

R = os.path.join(os.path.dirname(__file__), "..", "web", "script.html")


class TimelineCuts(unittest.TestCase):
    def setUp(self):
        with open(R, encoding="utf-8") as f:
            self.s = f.read()

    def test_all_cut_kinds_listed(self):
        i = self.s.find("function tcItems()")
        w = self.s[i:i + 3000]
        for k in ('kind:"s"', 'kind:"d"', 'kind:"t"', 'kind:"x"', 'kind:"u"'):
            self.assertIn(k, w)

    def test_restored_stay_visible_for_readd(self):
        self.assertIn('TCRES["d|"+x.n]', self.s)
        self.assertIn("cut:false", self.s)

    def test_click_toggles_edge_drags(self):
        self.assertIn("if(_eg){ tcDrag(ev, _eg); return }", self.s)
        self.assertIn('tcToggle(t.getAttribute("data-tc"))', self.s)

    def test_adjusted_silence_sent_as_keep_then_drop(self):
        i = self.s.find("Object.keys(SADJ).forEach(function(k){")
        w = self.s[i:i + 300]
        self.assertIn("ks.push([+o[0], +o[1]])", w)
        self.assertIn("ds.push(", w)

    def test_next_button_uses_the_same_path(self):
        self.assertIn('id="tlnext"', self.s)
        i = self.s.find('var nx=document.getElementById("tlnext")')
        w = self.s[i:i + 900]
        self.assertIn("bk.click()", w)

    def test_motion_section_open_in_cut_review(self):
        self.assertIn("bx.open=true;", self.s)


class AutoJoin(unittest.TestCase):
    """「ဖြတ်ချက်တွေ ဆက်နေရင် အော်တို အကုန်ဆက်」 · 「ဖြတ်ချက်နဲ့ အစိမ်း ကြား ကွာဟချက် မဟ」"""
    def setUp(self):
        with open(R, encoding="utf-8") as f:
            self.s = f.read()

    def test_adjacent_cuts_join_in_view_preview_and_export(self):
        self.assertIn("var MERGE_GAP=0.35;", self.s)
        self.assertIn("function tcView()", self.s)
        self.assertIn("if(L && r[0]<=L[1]+MERGE_GAP)", self.s)
        self.assertIn("try{ tcBridges().forEach(function(r){ ds.push(r) }) }catch(e){}", self.s)

    def test_group_click_restores_all(self):
        self.assertIn('if(it.kind==="g"){', self.s)
        self.assertIn("ဆက်နေတဲ့ ဖြတ်ချက်", self.s)

    def test_red_green_gap_goes_to_the_kept_side(self):
        i = self.s.find("function tcView()")
        w = self.s[i:i + 3200]
        self.assertIn("if(g1>0.005 && g1<=MERGE_GAP) v.a=c.b;", w)


if __name__ == "__main__":
    unittest.main()
