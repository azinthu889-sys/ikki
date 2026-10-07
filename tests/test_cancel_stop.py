# -*- coding: utf-8 -*-
"""ဖျက်လိုက်လျှင် worker **ရပ်ရမည်** · အလုပ်များနေတာကို ပျောက်နေတာ ဟု မပြရ。

⚠️⚠️ တကယ် ဖြစ်ခဲ့သည် (၂၀၂၆-၁၀-၀၇ · j_4dd59bb90b5a):
   job ကို ဖျက်ပြီး **၆၃ မိနစ်** ကြာမှ —
     · ffmpeg ၂ ခု CPU ၇၇–၉၄% နဲ့ ဆက်လည်နေ (၂၇ မိနစ် ၄၀ စက္ကန့်)
     · `~/.ikki/busy` က ကိုင်ထား ⇒ job အသစ် မယူနိုင်
     · heartbeat ရိုး၍ `/api/health` က 「worker မရှိ」 ပြနေ
   အကြောင်းရင်း: `cancel` က DB ကိုပဲ ပြောင်းပြီး worker ကို ဘာမှ မအကြောင်းကြား。
"""
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = tempfile.mkdtemp(prefix="ikki_cx_")
os.environ.setdefault("IKKI_DATA", _T)
os.environ.setdefault("IKKI_DB", os.path.join(_T, "t.db"))


def _src(*p):
    return io.open(os.path.join(ROOT, *p), encoding="utf-8").read()


class ServerAnswers(unittest.TestCase):
    """server က 「ဆက်လုပ်ရမလား」 ကို **တစ်နေရာတည်း**က ပြောရမည်"""

    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "api"))
        try:
            import main as M
        except ImportError:
            self.skipTest("fastapi မရှိ — ကျော်သည်")
        self.M = M

    def test_only_running_is_wanted(self):
        """⚠️ `cancelled` · `failed` · `done` · မရှိတော့တာ — အားလုံး ရပ်ရမည်"""
        M = self.M
        M.db.run("DELETE FROM jobs WHERE id LIKE 'j_t%'")
        for st, want in (("running", True), ("cutting", True),
                         ("cancelled", False), ("failed", False),
                         ("done", False), ("queued", False)):
            jid = "j_t" + st
            M.db.run("INSERT INTO jobs(id,status) VALUES(?,?)", jid, st)
            r = M._w_want(jid)
            self.assertEqual(r["want"], want, "%s → %s" % (st, r))
            self.assertEqual(r["status"], st)

    def test_a_missing_job_is_not_wanted(self):
        """⚠️ ဖျက်ပစ်လိုက်လျှင် row မရှိတော့ — `None` က 「ဆက်လုပ်」 မဟုတ်"""
        self.assertFalse(self.M._w_want("j_tnope")["want"])

    def test_stage_returns_the_answer(self):
        """⚠️ endpoint အသစ် မလို — worker က အဆင့်တိုင်း ဒီကို ခေါ်ပြီးသား"""
        s = _src("api", "main.py")
        i = s.find('@app.post("/api/w/{jid}/stage")')
        self.assertIn("return _w_want(jid)", s[i:i + 1400])

    def test_there_is_a_beat_for_long_stages(self):
        """⚠️ အဆင့်တစ်ခုက ရှည်နိုင်သည် (တိုင်းထား: `sound` ၂၇ မိနစ်)"""
        s = _src("api", "main.py")
        self.assertIn('@app.post("/api/w/{jid}/beat")', s)
        i = s.find('@app.post("/api/w/{jid}/beat")')
        w = s[i:i + 700]
        self.assertIn("_beat()", w)
        self.assertIn("return _w_want(jid)", w)

    def test_health_separates_busy_from_down(self):
        """⚠️ `worker:false` တစ်ခုတည်းနဲ့ 「ပျက်နေပြီ」 ဟု ထင်စေခဲ့သည်"""
        s = _src("api", "main.py")
        i = s.find("def health():")
        w = s[i:i + 1200]
        self.assertIn("status='running'", w)
        self.assertIn('"busy"', w)


class WorkerStops(unittest.TestCase):
    def setUp(self):
        self.s = _src("worker", "run.py")

    def test_both_stage_helpers_listen(self):
        """⚠️ တစ်ခုပဲ ထည့်လျှင် cinematic job က ဖျက်လို့ မရတော့"""
        self.assertEqual(self.s.count("_want(req(f\"/api/w/{jid}/stage\""), 2)

    def test_the_beat_runs_while_a_stage_is_long(self):
        i = self.s.find("def _beat_start(")
        w = self.s[i:i + 1200]
        self.assertIn("ev.wait(30)", w)
        self.assertIn("daemon=True", w)
        self.assertIn('f"/api/w/{jid}/beat"', w)
        # ⚠️ ကွန်ရက် ပြတ်တာက render ကို မရပ်စေရ
        self.assertIn("except Exception:", w)

    def test_cancel_is_not_a_failure(self):
        """⚠️ `fail` ပို့လျှင် status က `failed` ပြန်ဖြစ်ပြီး သုံးစွဲသူက
           「ဖျက်လိုက်တာ ပျက်သွားတယ်」 ဟု မြင်မည်"""
        i = self.s.find("except Cancelled as e:")
        self.assertGreater(i, 0)
        w = self.s[i:i + 420]
        self.assertNotIn("/fail", w)

    def test_the_busy_marker_and_scratch_are_released(self):
        """⚠️ မလွှတ်လျှင် job အသစ် မယူနိုင် · scratch က disk ဖြည့်"""
        i = self.s.find("_beat_start(jid)\n                try: handle(d)")
        self.assertGreater(i, 0, "ခေါ်တဲ့ နေရာ ရှာမတွေ့")
        w = self.s[i:i + 1500]
        self.assertIn("_beat_stop()", w)
        self.assertIn("sweep_scratch(keep=None)", w)
        self.assertIn("os.remove(BUSY)", w)

    def test_a_network_blip_does_not_cancel(self):
        """⚠️ `want` မပါလျှင် ဆက်လုပ်ရမည် — ကွန်ရက် ပြတ်တိုင်း
           render ပျက်လျှင် ပိုဆိုးသည်"""
        i = self.s.find("def _want(")
        w = self.s[i:i + 420]
        self.assertIn('d.get("want") is False', w)


class McpTellsTheSameTruth(unittest.TestCase):
    """⚠️ MCP · API · worker **သုံးခုလုံး အဖြေ တူရမည်**"""

    def setUp(self):
        p = os.path.expanduser("~/ikki-mcp/server.py")
        if not os.path.exists(p):
            self.skipTest("ikki-mcp မရှိ — ကျော်သည်")
        self.s = io.open(p, encoding="utf-8").read()

    def test_health_names_the_state(self):
        i = self.s.find("def t_health(")
        w = self.s[i:i + 1400]
        for k in ('"ready"', '"busy"', '"down"'):
            self.assertIn(k, w)

    def test_cancel_does_not_promise_instant(self):
        """⚠️ 「ချက်ချင်း ရပ်」 ဟု ကတိပေးလျှင် မှားသည် — အဆင့် နယ်နိမိတ်မှာ ရပ်"""
        i = self.s.find('"ikki_cancel_job"')
        self.assertIn("next stage boundary", self.s[i:i + 420])


if __name__ == "__main__":
    unittest.main(verbosity=2)
