# -*- coding: utf-8 -*-
"""တည်းဖြတ်ခန်း ရဲ့ **မြင်ကွင်း ၅ မျိုး** — job အခြေအနေ တစ်ခုချင်း。

⚠️⚠️ ဤဖိုင် ဖြစ်လာရခြင်းက ၂၀၂၆-၁၀-၀၅ မှာ Zin 「ကျန်တဲ့ view တွေပါ ပြပါ」
   ဟု ပြောလို့ တစ်ခုချင်း ဖွင့်ကြည့်ရင်း **၃ ခု ပျက်နေတာ တွေ့**လို့ပါ。
   `review` နဲ့ `done` ၂ ခုပဲ စမ်းခဲ့သဖြင့် ကျန်တာ လွတ်သွားခဲ့သည်。
   ⇒ မြင်ကွင်း တိုင်းကို စစ်ရမည် — အသုံးများတာ ၂ ခုတည်း မဟုတ်。
"""
import io
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(*p):
    return io.open(os.path.join(ROOT, *p), encoding="utf-8").read()


class PaneColumns(unittest.TestCase):
    """⚠️⚠️ `main.editor{display:flex}` ⇒ **ကလေးတိုင်းက ကော်လံ တစ်ခု**。"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_later_panels_are_adopted_into_the_pane(self):
        """⚠️⚠️ `#dn` (ဖြတ်ချက် · ထုတ်နေသည် · ကျဘမ်း) က `.wrap` ထဲ တိုက်ရိုက်
           ဝင်သဖြင့် pane ၃ ခု မဟုတ်တော့ဘဲ ၄ ခု ဖြစ်ခဲ့သည်。
           တိုင်းထား (၁၅၁၂px · cut_review): #dn x=0 w=538 · #spane **w=400**
           · #vbar w=575 ⇒ စာတမ်းက ၉၃၇ ကနေ ၄၀၀px ကျဉ်းသွားခဲ့。
           ပြင်ပြီးနောက်: #spane 937 + #vbar 575 = 1512 (ကလေး ၂ ခုသာ)。"""
        i = self.s.find("function spane(){")
        w = self.s[i:i + 1700]
        self.assertIn("var stray=", w)
        self.assertIn("e!==v && e!==w", w)
        self.assertIn("w.insertBefore(e, ref)", w)

    def test_every_panel_insert_uses_the_pane_host(self):
        """⚠️ `.wrap` ထဲ တိုက်ရိုက် ထည့်တဲ့ နေရာ ကျန်နေလျှင် ကော်လံ ပြန်ကွဲမည်"""
        self.assertIn("function paneHost(){", self.s)
        body = self.s[self.s.find("function paneHost(){"):]
        self.assertEqual(body.count('document.querySelector(".wrap").prepend'), 0,
                         ".wrap ထဲ တိုက်ရိုက် ထည့်တာ မကျန်ရ")
        self.assertGreaterEqual(self.s.count("paneHost()"), 4)

    def test_the_wrapper_is_built_even_when_render_never_runs(self):
        """⚠️⚠️ `spane()` က `tlAll()` ထဲကသာ ခေါ်ထားသဖြင့် ASR မပြီး/ကျဘမ်း
           မှာ wrapper မရှိဘဲ **ကော်လံ ၅ ခု ကွဲ**နေခဲ့သည် (`failed` မှာ တွေ့)。"""
        i = self.s.find("try{ spane() }catch(e){}\n/* ⚠️⚠️ **`r.ok`")
        self.assertGreater(i, 0, "စာမျက်နှာ ဖွင့်ကတည်းက spane() ခေါ်ရမည်")

    def test_the_wrapper_is_not_rebuilt_twice(self):
        i = self.s.find("function spane(){")
        w = self.s[i:i + 1700]
        self.assertIn('var w=document.getElementById("spane")', w)
        self.assertIn("if(!w){", w)


class LoadErrors(unittest.TestCase):
    """⚠️⚠️ 400 ကို ရလဒ် ဟု မှတ်ပြီး `render()` ဆက်ပြေးခဲ့သည်。"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_response_status_is_checked(self):
        """⚠️ အရင်က `r.json()` ကိုပဲ ယူ ⇒ `d.sentences` မရှိဘဲ `S.forEach`
           မှာ ကျကာ သုံးစွဲသူက **「Cannot read properties of undefined
           (reading 'forEach')」** မြင်ရသည် (queued · failed နှစ်ခုလုံး)。"""
        i = self.s.find("fetch(url,opt)")
        w = self.s[i:i + 900]
        self.assertIn("return {ok:r.ok, status:r.status, d:d}", w)
        self.assertIn("if(!z.ok){", w)

    def test_the_servers_own_message_is_shown(self):
        """server က 「စာသား မရှိ — ASR မပြီးသေး」 ဟု ဗမာလို ပြောပြီးသား"""
        i = self.s.find("fetch(url,opt)")
        w = self.s[i:i + 900]
        self.assertIn("z.d.detail", w)

    def test_a_broken_body_does_not_mask_the_error(self):
        """⚠️ `r.json()` ကိုယ်တိုင် ကျလျှင် status ပျောက်သွားမည်"""
        i = self.s.find("fetch(url,opt)")
        self.assertIn(".catch(function(){ return {} })", self.s[i:i + 900])


class FailedView(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_failed_is_watched(self):
        """⚠️ စာရင်းထဲ မပါလျှင် ကျဘမ်းကြောင်း **ဘာမှ မပြ**ဘဲ အပေါ်က ခလုတ်က
           နှိပ်လို့ရနေပြီး နှိပ်လျှင် 409 ရသည်"""
        self.assertIn('["queued","running","cutting","cut_review","failed"]', self.s)

    def test_the_top_button_says_what_happened(self):
        self.assertIn('(j.status==="failed")      ? "⚠️ ကျဘမ်း ဖြစ်ထားသည်"', self.s)

    def test_there_is_a_way_forward(self):
        """⚠️ အမှားစာ တစ်ကြောင်းတည်းနဲ့ မလုံလောက် — ဘာလုပ်ရမလဲ ပေးရမည်"""
        i = self.s.find('if(st==="failed"){')
        w = self.s[i:i + 1600]
        self.assertIn('id="rtf"', w)
        self.assertIn('"/api/jobs/"+jid+"/retry"', w)
        self.assertIn("watchJob(jid, el)", w)


class Banners(unittest.TestCase):
    """banner က ဘာပြောလဲ — အဲဒါ မှန်ရမည်"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_re_edit_banner_needs_an_actual_cut(self):
        """⚠️ banner က 「ဒါက ဖြတ်ပြီးသား ရလဒ်ပါ」 ⇒ ထုတ်နေဆဲ · ကျဘမ်း မှာ
           ပြလျှင် **မမှန်** (၂၀၂၆-၁၀-၀၅ queued · failed နှစ်ခုလုံးမှာ တွေ့)。"""
        self.assertIn("body.rv.rvcut #rvnote{display:flex", self.s)
        # ၂၀၂၆-၁၀-၀၅: cut_review မှာ စာတမ်း တိုက်ရိုက် ပြင်လို့ရ ⇒ banner/rv မထား
        #   (「script မှာလဲ ဖျက်လို့ရအောင်」) — queued/failed မှာလည်း မပေါ်ရ (rvcut မထည့်)
        self.assertNotIn('document.body.classList.add("rvcut")', self.s)
        self.assertIn('document.body.classList.add("rv","rvcut")', self.s)

    def test_only_one_banner_at_a_time(self):
        """⚠️ specificity တူ၍ **နောက်က** အနိုင်ရသည်"""
        self.assertGreater(self.s.index("body.done #rvnote{display:none}"),
                           self.s.index("body.rv.rvcut #rvnote{display:flex"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
