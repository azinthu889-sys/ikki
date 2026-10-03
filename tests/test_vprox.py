# -*- coding: utf-8 -*-
"""Script Editor မှာ **ဗီဒီယိုနဲ့ မြင်ရမည်** — Descript ပုံစံ

⚠️ Zin ၂၀၂၆-၁၀-၀၄ (Descript project ပြပြီး): 「IKKI UI ကို ဒီလို preview နဲ့
   မြင်ရအောင် လုပ်ပေးပြီး လက်ရှိ ဖြတ်ချက်ပုံစံမျိုးနဲ့ ဖြတ်လို့ရအောင်」。

ရှိပြီးသား: အသံ proxy (၄၈ kbps m4a) · ဝါကျတိုင်း ▶ · ရွေ့နေသော playhead ·
လှိုင်းပုံ · ✂ ဝါကျအတွင်း ဖြတ် · `tlDrops()` (ဖျက်ထားသမျှ)。
မရှိခဲ့: **ဗီဒီယို** · **အစအဆုံး တစ်ဆက်တည်း ဖွင့်မှု** · မီးမောင်း · ခုန်ခြင်း。

⚠️⚠️ **tab ဖျောက်ထားလျှင် `requestAnimationFrame` က လုံးဝ မခေါ်**ပါ —
   တိုင်းထား (browser ထဲ တကယ် စမ်း): `document.hidden=true` မှာ ၆၀၀ms
   အတွင်း **၀ ကြိမ်**。 ⇒ rAF တစ်ခုတည်းနဲ့ ခုန်ကျော်မှု ထားလျှင် tab
   ပြောင်းလိုက်တာနဲ့ **ဖျက်ထားတဲ့ စကား ပြန်ကြားရ**မည်。
   `timeupdate` က ဖျောက်ထားလည်း ဆက်ခေါ်သည် ⇒ အဲဒီမှာပါ ထားရသည်。

proxy ကုန်ကျစရိတ် (တကယ် ထုတ်ပြီး တိုင်းထား · ၁၇၈.၇s · ၁၈၃.၃ MB မူရင်း):
    640×360 · CRF၂၆ · veryfast → **၄.၄ MB · ၁၀–၁၂s** (၁.၅ MB/မိနစ်)
"""
import io
import os
import sys
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(*p):
    return io.open(os.path.join(_R, *p), encoding="utf-8").read()


class Api(unittest.TestCase):
    def setUp(self):
        self.s = _src("api", "main.py")

    def test_both_ends_exist(self):
        self.assertIn('@app.post("/api/w/{jid}/vprox")', self.s)
        self.assertIn('@app.get("/api/jobs/{jid}/vprox")', self.s)

    def test_the_player_can_pass_its_token_in_the_query(self):
        """⚠️ `<video>` က Authorization header မပို့နိုင် — အသံနဲ့ တူညီသော ပုံစံ"""
        i = self.s.find('def job_vprox(')
        w = self.s[i:i + 700]
        self.assertIn('t: str = ""', w)
        self.assertIn('f"Bearer {t}"', w)

    def test_it_is_the_user_token_not_the_worker_one(self):
        """⚠️⚠️ WTOKEN နဲ့ ထားလျှင် **အကောင့်တိုင်း** တစ်ယောက်ဟာ တစ်ယောက်
           ကြည့်လို့ ရသွားမည်。"""
        i = self.s.find('def job_vprox(')
        w = self.s[i:i + 700]
        self.assertIn("UTOKEN", w)
        self.assertIn("mine(", w)

    def test_the_upload_is_capped(self):
        i = self.s.find('async def w_vprox(')
        w = self.s[i:i + 1600]
        self.assertIn("HTTPException(413", w)

    def test_the_script_payload_says_whether_there_is_video(self):
        """⚠️ မရှိဘဲ `<video>` ပြလျှင် မည်းနေသော ဘောင်သာ မြင်ရမည်"""
        self.assertIn('"vprox": os.path.exists(', self.s)
        self.assertIn('"aud": os.path.exists(', self.s)

    def test_deleting_a_job_removes_both_proxies(self):
        """⚠️⚠️ အရင်က ပုံငယ်ပဲ ရှင်းပြီး **အသံ proxy က ကျန်ခဲ့** — job
           ဖျက်ပြီးသားလည်း ဖိုင် ကျန်နေသည် (disk ယိုစိမ့်မှု)。"""
        i = self.s.find('for t in (os.path.join(THUMB, jid + ".jpg"),')
        self.assertGreater(i, 0, "ရှင်းတဲ့ loop မတွေ့")
        w = self.s[i:i + 400]
        self.assertIn('"aud", jid + ".m4a"', w)
        self.assertIn('"vprox", jid + ".mp4"', w)


class Worker(unittest.TestCase):
    def setUp(self):
        self.s = _src("worker", "run.py")

    def test_the_proxy_is_built_and_posted(self):
        self.assertIn("def post_vprox(", self.s)
        self.assertIn("vprox.mp4", self.s)

    def test_the_long_edge_is_capped_not_the_width(self):
        """⚠️⚠️ `scale=640:-2` က ထောင်လိုက် (၉:၁၆) ဖိုင်မှာ ၆၄၀×၁၁၃၈ ဖြစ်ပြီး
           proxy က မူရင်းလောက် ကြီးသွားမည်。"""
        self.assertIn("force_original_aspect_ratio=", self.s)
        self.assertNotIn('"scale=640:-2"', self.s)

    def test_faststart_is_on(self):
        """⚠️ moov အဆုံးမှာ ကျန်လျှင် browser က အကုန် ဆွဲပြီးမှ ပြမည်"""
        i = self.s.find('_vp = os.path.join(work, "vprox.mp4")')
        self.assertGreater(i, 0)
        self.assertIn("+faststart", self.s[i:i + 900])

    def test_a_failed_proxy_does_not_break_review(self):
        """⚠️ proxy က အဆင်ပြေစေရန်သာ — မရလည်း ဖြတ်ချက် ဆုံးဖြတ်လို့ ရရမည်"""
        i = self.s.find('_vp = os.path.join(work, "vprox.mp4")')
        w = self.s[i:i + 1200]
        self.assertIn("except Exception", w)

    def test_the_audio_proxy_still_works(self):
        """⚠️ refactor လုပ်ရာမှာ အသံလမ်းကြောင်း မပျက်စေရ"""
        self.assertIn("def post_audio(", self.s)
        self.assertIn('"audio", "a.m4a"', self.s)


class Editor(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_skipping_does_not_depend_on_requestanimationframe_alone(self):
        """⚠️⚠️ **အရေးကြီးဆုံး** — tab ဖျောက်ထားလျှင် rAF က ၀ ကြိမ် ခေါ်သည်
           (၆၀၀ms အတွင်း တိုင်းထား) ⇒ ဖျက်ထားတဲ့ စကား ပြန်ကြားရမည်。"""
        i = self.s.find("function loopAll(")
        self.assertGreater(i, 0)
        w = self.s[i:i + 900]
        self.assertIn('addEventListener("timeupdate"', w)
        self.assertIn("setInterval(", w)

    def test_stopping_clears_the_interval_too(self):
        """⚠️ မရပ်လျှင် ရပ်ပြီးသားမှာလည်း ၄၀ms တိုင်း ဆက်ပြေးနေမည်"""
        i = self.s.find("function stopAll(")
        w = self.s[i:i + 500]
        self.assertIn("clearInterval(", w)

    def test_one_player_only(self):
        """⚠️ ဗီဒီယိုနဲ့ အသံ နှစ်ခုလုံး ဖွင့်မိလျှင် echo ထွက်မည်"""
        i = self.s.find("function med(")
        w = self.s[i:i + 500]
        self.assertIn("if(VPROX)", w)
        self.assertIn('getElementById("vid")', w)

    def test_deleted_lines_are_never_highlighted(self):
        """⚠️ ခုန်ကျော်ပြီးသား ဝါကျကို မီးမောင်း ထိုးလျှင် 「ဒါ ပြနေတယ်」 ဟု
           ထင်မှားစေသည် (စမ်းပြီး တွေ့: ၃၁.၈၇s မှာ ဖျက်ထားတဲ့ ဝါကျ ၃)。"""
        i = self.s.find("function rowNow(")
        w = self.s[i:i + 700]
        self.assertIn("if(!DEL[S[i].n]) hit=S[i].n", w)

    def test_the_highlight_holds_through_pauses(self):
        """⚠️ ဝါကျ ကြားက တိတ်ဆိတ်ချိန်မှာ ပျောက်လျှင် မှိတ်တုတ်မှိတ်တုတ် ဖြစ်မည်"""
        i = self.s.find("function rowNow(")
        w = self.s[i:i + 700]
        self.assertIn("S[i].start-0.05>t", w)

    def test_the_skip_list_merges_overlaps(self):
        """⚠️ မပေါင်းလျှင် ခုန်ပြီးမှ နောက်တစ်ခုထဲ ပြန်ဝင်ကာ တုန်နေမည်"""
        i = self.s.find("function skipList(")
        w = self.s[i:i + 800]
        self.assertIn("L[1]=Math.max(L[1], r[1])", w)

    def test_it_reuses_the_existing_deletion_list(self):
        """⚠️ `tlDrops()` က ဝါကျ · အသံ · ❓ · ✂ · ကိုယ်တိုင် အားလုံး ပေးပြီးသား —
           ထပ်ရေးလျှင် နှစ်ခု ကွဲသွားမည်。"""
        i = self.s.find("function skipList(")
        self.assertIn("tlDrops()", self.s[i:i + 400])

    def test_the_list_is_not_rebuilt_every_frame(self):
        """⚠️ ၆၀fps မှာ ဝါကျ အားလုံး ဖြတ်သန်းလျှင် ဖြုန်းတီးမှု"""
        self.assertIn("function skipCached(", self.s)

    def test_playing_one_line_stops_the_continuous_play(self):
        """⚠️ မရပ်လျှင် နှစ်ခု ပြိုင်ပြီး ခုန်နေမည်"""
        i = self.s.find("function playRange(")
        self.assertIn("stopAll();", self.s[i:i + 500])

    def test_clicking_the_text_still_deletes_not_seeks(self):
        """⚠️⚠️ စာသား နှိပ်တာက **ဖျက်/ပြန်ချန်** ဖြစ်နေသည် — seek ကို အဲဒီမှာ
           တပ်လျှင် ဖျက်ချင်တိုင်း ဗီဒီယို ခုန်မည် ⇒ အချိန် (`.no`) မှာသာ。"""
        i = self.s.find('var sk=e.target.closest(".row .no")')
        self.assertGreater(i, 0, "seek လမ်းကြောင်း မတွေ့")

    def test_the_player_is_hidden_when_there_is_nothing_to_play(self):
        self.assertIn("_vb.hidden = !medOK()", self.s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
