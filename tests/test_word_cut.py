# -*- coding: utf-8 -*-
"""စာလုံး ဆွဲရွေးပြီး ဖြတ်ခြင်း — **ရွေးချယ်မှုက စာလုံးအလိုက် · ဖြတ်မှတ်က အသံအလိုက်**

⚠️ Zin ၂၀၂၆-၁၀-၀၄ (Descript ပြပြီး): 「လက်ရှိ ဖြတ်ချက်ပုံစံမျိုးနဲ့
   ဖြတ်လို့ရအောင်」。

⚠️⚠️ **ASR ရဲ့ စကားလုံး အချိန်အတိုင်း တည့်တည့် မဖြတ်ရ**。 တိုင်းထား
   (Zin ရဲ့ ဖိုင် · စကားလုံး နယ်နိမိတ် ၁၀၀ ခု): **၈၄ ခု (၈၄%)** က စကားသံ
   အထဲမှာ ကျသည်。 `words_conf` ဖြန့်ကျက်: min ၀.၀၀ · med ၀.၈၃ · max ၁.၀၀。
   ⇒ တည့်တည့် ဖြတ်လျှင် ၁၀ ခါမှာ ၈ ခါ စကားလုံး ပြတ်မည်。
   `web/script.html` ထဲက မှတ်ချက် (၁၇၁၁ ကြောင်း) ကလည်း အတူတူ ပြောထားသည်:
   「စကားလုံး အချိန်မှတ် (ASR words) ကို မသုံးပါ — ဖြတ်ဖို့ ကြမ်းလွန်းသည်」。

ဖြေရှင်းချက်: browser မှာ အသံလှိုင်း အပြည့် ရှိပြီးသား (`WAVE`) ⇒ အနီးဆုံး
တိတ်ဆိတ်မှုဆီ **ရွှေ့**ပြီးမှ ဖြတ်သည် (server ကို မမေးရ)。

⚠️⚠️ threshold ကို server နဲ့ **တူညီအောင်** ထားရသည်。 ပထမ အကြိမ်မှာ
   browser က **peak** (၅ms) ပေါ် `max(p95−20, p10+7)` တွက်မိပြီး
   **−၃၁.၈၅ dB** ထွက်ခဲ့သည် — server က **−၃၈.၉၂ dB** (၂၀ms RMS)。
   **၇ dB ကွာ** ⇒ တိတ်ဆိတ်မှုကို စောပြီး 「တွေ့ပြီ」 ထင်ကာ စကားသံထဲ
   ဖြတ်မိမည်。 ၂၀ms RMS track သီးသန့် တွက်တော့ browser −၃၈.၉၂ ·
   server −၃၈.၉၂ — **အတိအကျ တူ**。

တိုင်းထားသော ရလဒ် (browser ထဲ တကယ် ပြေးပြီး · ၂၆ ဝါကျ · ၁၃၀ စာလုံး):

    နယ်နိမိတ် ၂၆၀ ခု · မရွှေ့ခင် စကားသံထဲ ၁၅၅ (၆၀%) → ရွှေ့ပြီး ၆၄ (၂၅%)
    ရွှေ့ချက် med ၀.၀၂s · p90 ၀.၂၄s · အများဆုံး ၀.၃၀s (ဝင်းဒိုး)
    စကားစု ရွေးချက်: ၁ လုံး ၅၉% · ၂ လုံး ၆၃% · ၃ လုံး ၆၀% နှစ်ဖက်လုံး တိတ်
    **ဝါကျ အစ/အဆုံး ပါလျှင် ၈၀%**

⚠️ ကျန်တဲ့ ၂၀–၄၀% က ဆက်တိုက် ပြောနေသဖြင့် **တိတ်ဆိတ်မှု ကို မရှိ**ခြင်း —
   ရုပ်ပိုင်းဆိုင်ရာ ကန့်သတ်ချက်、ပုံသေနည်းနဲ့ ဖြေလို့ မရ。 ⇒ **ဖုံးမထားဘဲ
   ပြောရမည်** (「⚠️ စကားသံထဲ ဖြတ်ရမည် — အသံ ပြတ်နိုင်」)。
"""
import io
import os
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(*p):
    return io.open(os.path.join(_R, *p), encoding="utf-8").read()


class Api(unittest.TestCase):
    def test_the_words_reach_the_editor(self):
        s = _src("api", "main.py")
        i = s.find("    sents = [dict(n=i + 1,")
        self.assertGreater(i, 0)
        self.assertIn("words=[dict(w=", s[i:i + 1400])

    def test_a_sentence_without_words_sends_none_not_an_empty_list(self):
        """⚠️ `[]` ပို့လျှင် UI က 「စာလုံး ရှိတယ်」 ထင်ပြီး ဗလာ span ထုတ်မည်"""
        s = _src("api", "main.py")
        i = s.find("    sents = [dict(n=i + 1,")
        self.assertIn("or None)", s[i:i + 1400])


class Snap(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_threshold_formula_matches_the_server(self):
        """⚠️⚠️ မတူလျှင် UI ပြောတာနဲ့ တကယ် ဖြတ်တာ ကွဲမည်"""
        i = self.s.find("function waveThr(")
        w = self.s[i:i + 700]
        self.assertIn("q(0.95)-20", w)
        self.assertIn("q(0.10)+7", w)
        srv = _src("core", "measure.py")
        self.assertIn('percentile(db,95))-20', srv)
        self.assertIn('percentile(db,10))+7', srv)

    def test_the_threshold_is_built_on_rms_not_peaks(self):
        """⚠️⚠️ peak ပေါ် တင်လျှင် ၇ dB လွဲသည် (−၃၁.၈၅ vs −၃၈.၉၂)"""
        i = self.s.find("function waveThr(")
        w = self.s[i:i + 700]
        self.assertIn("WAVE.db", w)
        self.assertNotIn("WAVE.peaks", w)
        i2 = self.s.find("function wdb(")
        self.assertIn("WAVE.db", self.s[i2:i2 + 300])

    def test_the_rms_track_is_computed_at_decode_time(self):
        """⚠️ သီးသန့် ဆွဲချလျှင် ၄၈ kbps ဖိုင်ကို နှစ်ခါ ဆွဲရမည်"""
        i = self.s.find("function waveLoad(")
        w = self.s[i:i + 1800]
        self.assertIn("WAVE.db=dbt", w)
        self.assertIn("Math.sqrt(", w)

    def test_the_snap_never_shrinks_the_selection(self):
        """⚠️⚠️ ကျုံ့လျှင် ဖျက်ခိုင်းထားတဲ့ စကားလုံး ပြန်ကြားရမည် —
           ၂၀၂၆-၁၀-၀၃ မှာ ဒါက အဓိက အမှား ဖြစ်ခဲ့သည်。"""
        i = self.s.find("function snapQuiet(")
        w = self.s[i:i + 800]
        self.assertIn("dir*k*step", w)
        j = self.s.find("a=snapQuiet(raw0,-1")
        self.assertGreater(j, 0, "အစက နောက်ပြန်သာ ရွှေ့ရမည်")
        self.assertIn("b=snapQuiet(raw1,+1", self.s)

    def test_the_search_window_is_bounded(self):
        """⚠️ အကန့်အသတ် မရှိလျှင် ဘေးက စကားလုံးတွေပါ တိတ်တဆိတ် ပါသွားမည်"""
        self.assertIn("var SNAP_WIN=0.30", self.s)

    def test_it_stops_at_the_first_quiet_point(self):
        """⚠️ အဝေးဆုံး တိတ်ဆိတ်မှုဆီ သွားလျှင် မလိုဘဲ များများ ဖြတ်မည်"""
        i = self.s.find("function snapQuiet(")
        w = self.s[i:i + 800]
        self.assertIn("if(d<thr) return", w)


class Ui(unittest.TestCase):
    def setUp(self):
        self.s = _src("web", "script.html")

    def test_corrected_text_keeps_word_spans(self):
        """⚠️⚠️ (၂၀၂၆-၁၀-၀၆ ပြောင်း) `FIX[n]` ⇒ span **မဖြုတ်ရ** — ဖြုတ်ခဲ့ရာ script ✓ ပြီး
           ဝါကျမှာ စာလုံးလိုက် ဖြတ်လို့ မရ (Zin 「စာသားဖျက်ပေမယ့် timeline မပျက်」)。
           ⇒ စကားလုံး အရေ တူ ⇒ ASR အချိန် · မတူ ⇒ **ခန့်မှန်း (`est`)** · ဖြတ်ချိန် တိတ်ဆိတ်ရာ snap。"""
        i = self.s.find("function txHtml(")
        w = self.s[i:i + 700]
        self.assertIn("wordsOf(s)", w)
        j = self.s.find("function wordsOf(")
        v = self.s[j:j + 1600]
        self.assertIn("toks.length===ws.length", v)      # အရေ တူ ⇒ ASR အချိန် ပြန်သုံး
        self.assertIn("est:1", v)                         # မတူ ⇒ ခန့်မှန်း အမှတ်
        self.assertIn("snapQuiet(raw0", self.s)           # ဖြတ်ချိန် snap ဆက်ရှိ

    def test_selecting_a_whole_sentence_deletes_the_line(self):
        """⚠️ ✂ အပိုင်းနဲ့ ဖုံးလျှင် ရေတွက်မှု · အစီရင်ခံစာ နှစ်ခု ကွဲမည်"""
        self.assertIn("if(x.whole){ DEL[x.n]=1; return }", self.s)

    def test_it_says_when_the_cut_lands_inside_speech(self):
        """⚠️⚠️ **ဖုံးမထားရ** — တိုင်းထား: အလယ်ထဲ ရွေးချက်ရဲ့ ၄၀% က
           တိတ်ဆိတ်မှု မရောက်ပါ (ဆက်တိုက် ပြောနေ၍)。"""
        self.assertIn("⚠️ စကားသံထဲ ဖြတ်ရမည်", self.s)
        i = self.s.find("var clean = whole ||")
        self.assertGreater(i, 0)
        self.assertIn("wdb(a)<thr && wdb(b)<thr", self.s[i:i + 200])

    def test_it_reuses_the_existing_trim_machinery(self):
        """⚠️ `TRIM` က `tlDrops()` · server နဲ့ ချိတ်ပြီးသား —
           အသစ် ဆောက်လျှင် နှစ်ခု ကွဲသွားမည်。"""
        i = self.s.find("function selCut(")
        w = self.s[i:i + 900]
        self.assertIn("TRIM[x.n]=TRIM[x.n]||[]", w)

    def test_undo_handles_both_shapes(self):
        """⚠️⚠️ UNDO ထဲမှာ ပုံစံ ၂ မျိုး — `DEL` ကူးယူချက် သက်သက် နဲ့
           `{DEL,TRIM}`。 မခွဲလျှင် DEL က wrapper ဖြစ်သွားပြီး **ဝါကျတိုင်း
           ဖျက်ထားသလို** ဖြစ်မည် (စမ်းစဉ် တွေ့)。"""
        i = self.s.find("function undo(")
        w = self.s[i:i + 900]
        self.assertIn("_u.__both", w)
        self.assertIn("DEL=_u.DEL; TRIM=_u.TRIM", w)
        self.assertIn("DEL=_u||{}", w)
        self.assertIn("__both:1", self.s)

    def test_the_bar_disappears_when_the_selection_does(self):
        self.assertIn('addEventListener("selectionchange"', self.s)

    def test_the_bar_flips_below_when_there_is_no_room_above(self):
        """⚠️ ပထမ စာကြောင်းမှာ အပေါ်က နေရာ မရှိ"""
        i = self.s.find("function selBarShow(")
        self.assertIn("r.top-h-10>8 ? r.top-h-10 : r.bottom+10", self.s[i:i + 2200])


if __name__ == "__main__":
    unittest.main(verbosity=2)
