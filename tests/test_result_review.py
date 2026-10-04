# -*- coding: utf-8 -*-
"""ထုတ်ပြီး ရလဒ်ကို **တည်းဖြတ်ခန်း pane ထဲမှာပဲ** စစ်ခြင်း。

Zin ၂၀၂၆-၁၀-၀၄: 「ဖြတ်ချက် OK လို့ Motion ထည့်ပြီးရင်လဲ · Layout pane
မှာပဲ စစ်လို့ရတဲ့ပုံစံမျိုးက ပိုပြီးကောင်းမယ်」。

⚠️⚠️ ဤဖိုင်ရဲ့ အဓိက အကြောင်းအရာက **အချိန် အခြေခံ ၂ မျိုး**。
   စာတမ်း · လှိုင်း · ဖြတ်မှတ် ⇒ မူရင်း အချိန်
   ထုတ်ပြီး ဗီဒီယို · `vplan` ⇒ ထွက် အချိန်
   တိုင်းထား (j_3f7316e4b795): ဂရပ်ဖစ် နောက်ဆုံး ၄၇.၁၂s · ထွက် ၆၄.၈၀s
   ⇒ ၇၃%。 မူရင်း ၁၇၈.၆၈s နဲ့ ဆွဲလျှင် ၂၆% ⇒ **၄၇% လွဲ** (တကယ် ရှိခဲ့သော အမှား)。
"""
import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ⚠️ `api/main.py` က import ချိန်မှာ `/data` ကို ဆောက်ဖို့ ကြိုးစားသည်
#    (ဤ Mac မှာ read-only) ⇒ import မလုပ်ခင် ညွှန်ပြရမည်
_T = tempfile.mkdtemp(prefix="ikki_rr_")
os.environ.setdefault("IKKI_DATA", _T)
os.environ.setdefault("IKKI_DB", os.path.join(_T, "t.db"))


def _src(*p):
    return io.open(os.path.join(ROOT, *p), encoding="utf-8").read()


class CutMapApi(unittest.TestCase):
    """မူရင်း⇒ထွက် မြေပုံကို API က ပေးရမည် — မရှိလျှင် ခန့်မှန်းလို့ မရ"""

    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "api"))
        try:
            import main as M
        except ImportError:
            self.skipTest("fastapi မရှိ — ကျော်သည်")
        self.M = M

    def test_the_rendered_map_wins(self):
        """⚠️ worker ပို့တဲ့ `cut_map` က **တကယ် render လုပ်တဲ့** span"""
        j = {"out_dur": 10.0, "cut_map": "[[0,5],[20,25]]",
             "cut_spans": "[[0,99]]", "over": json.dumps({"_spans": [[0, 77]]})}
        m = self.M._cut_map(j)
        self.assertEqual(m["src"], "render")
        self.assertEqual(m["spans"], [[0.0, 5.0], [20.0, 25.0]])
        self.assertTrue(m["exact"])

    def test_the_frozen_approve_spans_come_next(self):
        j = {"out_dur": 7.0, "over": json.dumps({"_spans": [[1, 5], [9, 12]]})}
        m = self.M._cut_map(j)
        self.assertEqual(m["src"], "approve")
        self.assertTrue(m["exact"])

    def test_the_plan_fallback_is_marked_approximate(self):
        """⚠️⚠️ တိုင်းထား: `plan` ကနေ တွက်လျှင် ၆၇.၆၀s ထွက်ပြီး တကယ့်
           `out_dur` က ၆၄.၈၀s ⇒ **၂.၈၀s လွဲ**。 အတိအကျ ဟု မပြောရ。"""
        j = {"out_dur": 64.8,
             "plan": json.dumps({"spans": [[0, 70], [100, 130]]}),
             "over": json.dumps({"_drop": [[10, 15]]})}
        m = self.M._cut_map(j)
        self.assertEqual(m["src"], "plan")
        self.assertFalse(m["exact"], "ခန့်မှန်းကို အတိအကျ ဟု မပြောရ")

    def test_a_map_that_disagrees_with_out_dur_is_not_exact(self):
        """⚠️ ဘယ် အရင်းအမြစ် ဖြစ်ဖြစ် တကယ့် ထွက်ရှည်နဲ့ တိုက်စစ်ရမည်"""
        j = {"out_dur": 10.0, "cut_map": "[[0,30]]"}
        self.assertFalse(self.M._cut_map(j)["exact"])
        j2 = {"out_dur": 10.0, "cut_map": "[[0,10.4]]"}
        self.assertTrue(self.M._cut_map(j2)["exact"], "၀.၅၀s အတွင်း ခွင့်ပြုသည်")

    def test_no_map_means_no_guess(self):
        """⚠️ မရှိဘဲ ခန့်မှန်းပြီး ဆွဲလျှင် မှားတဲ့ နေရာ ပြမည်"""
        self.assertIsNone(self.M._cut_map({"out_dur": 10.0}))

    def test_the_endpoint_carries_the_map_and_the_plan(self):
        s = _src("api", "main.py")
        i = s.find('return {"job": jid, "title": j.get("title")')
        w = s[i:i + 1600]
        self.assertIn('"cut_map": _cmap', w)
        self.assertIn('"vplan": _jload(j.get("vplan"))', w)

    def test_the_rendered_map_has_its_own_column(self):
        """⚠️ `cut_spans` နဲ့ မရောရ — အဲဒါက အတည်မပြုရသေးတဲ့ preview အတွက်
           ဖြစ်ပြီး Premium export ဂိတ် (`_short_cut_spans`) က သုံးသည်"""
        self.assertIn('("cut_map", "TEXT")', _src("api", "db.py"))
        s = _src("api", "main.py")
        self.assertIn('db.run("UPDATE jobs SET cut_map=? WHERE id=?"', s)
        # re-edit တိုင်း ရှင်းရမည် — မရှင်းလျှင် ဟောင်းနေသော မြေပုံ ကျန်မည်
        self.assertEqual(s.count("cut_spans=NULL,cut_map=NULL"), 3)

    def test_the_worker_sends_the_spans_it_rendered(self):
        s = _src("worker", "run.py")
        self.assertIn('st["cut_map"] = [[round(float(_a), 3), round(float(_b), 3)]'
                      ' for _a, _b in spans]', s)
        self.assertIn("cut_map=st.get(\"cut_map\")", s)
        # ⚠️ `spans` က `render()` ထဲမှာသာ ရှိသည် — `handle()` ထဲ မရှိ
        i, k = s.find('st["cut_map"]'), s.find("SP.spans(src, _render_spans")
        self.assertGreater(k, i, "render မလုပ်ခင် မှတ်ရမည်")


class OutMode(unittest.TestCase):
    """တည်းဖြတ်ခန်း က ထွက် အချိန် ဝင်ရိုးကို ပြောင်းသုံးခြင်း"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_axis_follows_the_output(self):
        i = self.s.find("function tlDur(){")
        self.assertIn("OUT.on ? (OUT.dur||OUT.total)", self.s[i:i + 200])

    def test_the_map_is_required(self):
        """⚠️ မြေပုံ မရှိဘဲ OUT mode ဖွင့်လျှင် နေရာ အားလုံး လွဲမည်"""
        i = self.s.find("function outInit(")
        w = self.s[i:i + 700]
        self.assertIn("if(!m || !m.spans || !m.spans.length) return", w)
        self.assertIn('d.status!=="done" || !d.out_dur', w)

    def test_the_graphics_row_needs_the_output_axis(self):
        """⚠️⚠️ `vplan.at` က ထွက် အချိန် — မူရင်း ဝင်ရိုးပေါ် ဆွဲလျှင်
           ၄၇.၁၂s က ၇၃% အစား ၂၆% ⇒ တကယ် ရှိခဲ့သော အမှား"""
        i = self.s.find("function tlGfx(")
        self.assertIn("VPLAN.length && OUT.on", self.s[i:i + 900])

    def test_the_player_time_is_converted_both_ways(self):
        """⚠️ `seekTo` က မူရင်း လက်ခံ · player က ထွက် ⇒ `s2o`
           `tickAll` က player ကနေ လာ ⇒ `o2s`"""
        i = self.s.find("function seekTo(")
        self.assertIn("OUT.on ? Math.max(0, s2o(t))", self.s[i:i + 600])
        j = self.s.find("function tickAll(")
        self.assertIn("if(OUT.on){ rowNow(o2s(t)); vpos(a); tlHead(t); return }",
                      self.s[j:j + 600])

    def test_the_timeline_click_is_not_converted_twice(self):
        """⚠️ `tOf()` က ဝင်ရိုး အချိန် (= ထွက်) ⇒ `seekTo` ကို တန်းပေးလျှင်
           `s2o` နှစ်ထပ် ခံပြီး အများကြီး လွဲမည်"""
        i = self.s.find("function go(ev){")
        self.assertIn("seekTo(OUT.on ? o2s(_t) : _t)", self.s[i:i + 2600])

    def test_there_is_no_skipping_in_the_output(self):
        """⚠️ ဖြတ်ပြီးသား — ခုန်လျှင် မူရင်းနဲ့ ထွက် အချိန် ရောပြီး ကျော်မိမည်"""
        i = self.s.find("function tickAll(")
        w = self.s[i:i + 400]
        self.assertLess(w.find("if(OUT.on)"), w.find("skipCached()"))

    def test_the_cut_row_is_frozen(self):
        """⚠️ နှိပ်လို့ရသလို ပြထားပြီး ဘာမှ မဖြစ်လျှင် 「ပျက်နေတယ်」 ဟု ထင်မည်
           (၂၀၂၆-၁၀-၀၄ `rv` မှာ တကယ် ဖြစ်ခဲ့)"""
        i = self.s.find("function tlCuts(")
        w = self.s[i:i + 700]
        self.assertIn("if(OUT.on){", w)
        self.assertIn('_rw.hidden=true', w)

    def test_deleted_lines_leave_the_caption_row(self):
        i = self.s.find("function tlCaps(")
        self.assertIn("if(OUT.on && DEL[x.n]) return", self.s[i:i + 600])

    def test_the_waveform_is_remapped_per_pixel(self):
        """⚠️ မူရင်း လှိုင်းကို တန်းဆွဲလျှင် ဖြတ်ထားတာတွေပါ ပါလာပြီး
           ဗီဒီယိုနဲ့ လုံးဝ မကိုက်"""
        i = self.s.find("function tlDraw(")
        w = self.s[i:i + 2200]
        self.assertIn("var _st=o2s(_x/W*dur)", w)

    def test_the_round_trip_is_identity(self):
        """⚠️ `s2o(o2s(t)) === t` မဟုတ်လျှင် နှိပ်တိုင်း တဖြည်းဖြည်း လွဲမည်。
           ဤစစ်ချက်ကို JS ကနေ ကူးရေးသည် (browser မှာ တိုင်းထား: err ၀.၀၀၀)"""
        M = [[14.75, 15.15], [22.37, 30.97], [145.11, 152.61]]
        acc, run = [], 0.0
        for a, b in M:
            acc.append(run); run += b - a

        def s2o(t):
            for i, (a, b) in enumerate(M):
                if t < a: return acc[i]
                if t <= b: return acc[i] + (t - a)
            return run

        def o2s(t):
            for i in range(len(M) - 1, -1, -1):
                if t >= acc[i]: return min(M[i][1], M[i][0] + (t - acc[i]))
            return M[0][0]

        for t in (0.0, 0.2, 5.0, 9.0, 12.34, run):
            self.assertAlmostEqual(s2o(o2s(t)), t, places=6)


class ResultInThePane(unittest.TestCase):
    """ရလဒ်ကို card သေးသေးထဲ မပြတော့ — pane ထဲမှာပဲ"""

    def setUp(self):
        self.s = _src("web", "script.html")

    def test_the_player_shows_the_rendered_file(self):
        """⚠️ proxy က ဖြတ်မထား · ဂရပ်ဖစ် မပါ ⇒ Motion စစ်လို့ မရ。
           `VPROX` တစ်ခုတည်း ပြောင်းရုံနဲ့ player · filmstrip · ခုန်ခြင်း
           အားလုံး ထွက်ဖိုင် ဖြစ်သွားသည် (လမ်းကြောင်း အသစ် မဆောက်ရ)"""
        i = self.s.find("if(JOB && OUT.on){")
        w = self.s[i:i + 400]
        self.assertIn('VPROX="/api/jobs/"+JOB+"/file?t="', w)
        self.assertIn('classList.add("rv")', w)
        self.assertIn("FILM.done=false", w)

    def test_watchjob_switches_the_pane_not_a_card(self):
        i = self.s.find('if(st==="done"){')
        w = self.s[i:i + 1200]
        self.assertIn('fetch("/api/script/"+jid', w)
        self.assertIn("render(dd)", w)
        self.assertIn("_doneCard(jid, j, el)", w)   # အရန်သာ

    def test_a_done_job_can_still_be_re_edited(self):
        """⚠️⚠️ ရလဒ်ကို အမြဲ ကြည့်ရုံပဲ ပြလျှင် 「✂️ Edit」 လမ်းကြောင်း
           ပိတ်သွားမည် — အရင်က ထုတ်ပြီးသားကို တည်းဖြတ်လို့ ရခဲ့သည်"""
        self.assertIn("function outEdit(", self.s)
        i = self.s.find("function outEdit(")
        w = self.s[i:i + 900]
        self.assertIn("REEDIT=true", w)
        self.assertIn('classList.remove("rv","done")', w)
        self.assertIn('_v.removeAttribute("src")', w)   # src="" က စာမျက်နှာကို ဖတ်မည်
        j = self.s.find("function outInit(")
        self.assertIn("if(REEDIT) return", self.s[j:j + 300])

    def test_the_banner_does_not_rely_on_the_hidden_attribute(self):
        """⚠️ `[hidden]{display:none !important}` က class ကို လွှမ်းမည်"""
        self.assertIn('<div id="donote">', self.s)
        self.assertNotIn('<div id="donote" hidden>', self.s)
        self.assertIn("body.done #donote{display:flex}", self.s)

    def test_the_visual_plan_panel_lives_in_the_pane(self):
        a, b = self.s.find('<div id="vplan"></div>'), self.s.find("</main>")
        self.assertGreater(a, 0)
        self.assertLess(a, b, "`#vplan` က pane ထဲ ရှိရမည်")
        self.assertIn("function vplanTry(", self.s)

    def test_a_graphic_chip_seeks_to_itself(self):
        """Motion ကို နေရာအလိုက် စစ်ဖို့ အဓိက လမ်း"""
        i = self.s.find("function go(ev){")
        w = self.s[i:i + 900]
        self.assertIn('ev.target.closest(".tlgfx i")', w)
        self.assertIn("seekTo(o2s(+ge.at||0))", w)

    def test_only_one_banner_shows(self):
        """⚠️ ထုတ်ပြီးသားမှာ `rv` ပါ တွဲပါသဖြင့် banner ၂ ခု ထပ်ပေါ်ပြီး
           「ပြန်ပြင်」 ခလုတ် ၂ ခု ဖြစ်ခဲ့သည် (ဖရိမ်း ကြည့်မှ တွေ့)。
           ⚠️ specificity တူ၍ **နောက်က** အနိုင်ရသည် ⇒ `body.rv #rvnote`
              ပြီးနောက်မှ ထားရမည် — ရှေ့မှာ ထားလျှင် အလကား。"""
        self.assertIn("body.done #rvnote{display:none}", self.s)
        self.assertGreater(self.s.index("body.done #rvnote{display:none}"),
                           self.s.index("body.rv #rvnote{display:flex"))

    def test_approve_is_dead_once_rendered(self):
        """⚠️⚠️ နှိပ်လျှင် `approve` က 409 「အဆင့်မှာ မရှိပါ (done)」 ပြန်သည်。
           ⚠️ ပြန်ပြင်တဲ့အခါ **ပြန်ဖွင့်ပေးရမည်** — မဖွင့်လျှင် ပြင်ပြီးမှ
              ထုတ်လို့ မရတော့ (လမ်းပိတ်)。"""
        i = self.s.find('var _bk2=document.getElementById("bok")')
        self.assertGreater(i, 0)
        self.assertIn('_bk2.disabled=true', self.s[i:i + 200])
        j = self.s.find("function outEdit(")
        w = self.s[j:j + 1100]
        self.assertIn("_bk3.disabled=false", w)
        self.assertIn("✂️ Edit", w)

    def test_only_one_banner_shows(self):
        """⚠️ ထုတ်ပြီးသားမှာ `rv` ပါ တွဲပါသဖြင့် banner ၂ ခု ထပ်ပေါ်ပြီး
           「ပြန်ပြင်」 ခလုတ် ၂ ခု ဖြစ်ခဲ့သည် (ဖရိမ်း ကြည့်မှ တွေ့)。"""
        self.assertIn("body.done #rvnote{display:none}", self.s)

    def test_approve_is_dead_once_rendered(self):
        """⚠️⚠️ နှိပ်လျှင် `approve` က 409 「အဆင့်မှာ မရှိပါ (done)」 ပြန်သည်。
           ⚠️ ပြန်ပြင်တဲ့အခါ **ပြန်ဖွင့်ပေးရမည်** — မဖွင့်လျှင် ပြင်ပြီးမှ
              ထုတ်လို့ မရတော့ (လမ်းပိတ်)。"""
        i = self.s.find('var _bk2=document.getElementById("bok")')
        self.assertGreater(i, 0)
        self.assertIn("_bk2.disabled=true", self.s[i:i + 200])
        j = self.s.find("function outEdit(")
        w = self.s[j:j + 1300]
        self.assertIn("_bk3.disabled=false", w)
        self.assertIn("✂️ Edit", w)

    def test_the_script_pane_is_on_the_left(self):
        """⚠️ `.vbar` က DOM ထဲ ပထမ ⇒ wrapper က နောက်မှ ဝင်ပြီး ဗီဒီယိုက
           ဘယ်ဘက် ရောက်သည် (တိုင်းထား: vbar x=18 · spane x=390)。
           `order` နဲ့ ပြောင်းသည် — DOM ရွှေ့လျှင် `<video>` ပြန်စမည်"""
        i = self.s.find("@media(min-width:1100px){")
        w = self.s[i:i + 1400]
        self.assertIn("#spane{order:1", w)
        self.assertIn("main.editor>.vbar{order:2", w)


if __name__ == "__main__":
    unittest.main(verbosity=2)
