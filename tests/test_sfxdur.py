# -*- coding: utf-8 -*-
"""SFX budget က **ဖြတ်ပြီး အရှည်**နဲ့ တွက်ရမည် — QC က ထွက်ဖိုင်ပေါ်မှာ တိုင်းသည်。

⚠️ ၂၀၂၆-၀၉-၂၁ j_1f9561de04b3 — မူရင်း ၁၇၈.၇s နဲ့ တွက်၍ cue ၁၇ ခု ခွင့်ပြုခဲ့ရာ
   ဖြတ်ချက်က ၄၉% ဖယ်ပြီး ထွက် ၆၉.၃s သာ ဖြစ်သဖြင့် **၆.၉၃/min** ဖြစ်ကာ
   ဂိတ် (≤၆.၀/min) ကျခဲ့သည်。 ဂိတ် မလျှော့ရ — ယန္တရား ပြင်ရသည်。
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import planner as PL          # noqa: E402
import sfxpol as SP           # noqa: E402

SRC, OUT, PM = 178.7, 69.3, 6.0


def _events(n, span):
    """`n` ခု ကို `span` စက္ကန့် အတွင်း အညီအမျှ — card kind (SFX ရှိသည်)"""
    return [dict(id=f"e{i}", motionKitTemplateId="headtop.ht_stat_ring",
                 startTime=round(i * span / max(1, n), 2),
                 endTime=round(i * span / max(1, n) + 2.0, 2),
                 style=dict(kind="card"))
            for i in range(n)]


def _moments(cues):
    """QC ရဲ့ ရေတွက်နည်း — ဖြစ်ရပ် တစ်ခုရဲ့ အထပ်များက **တစ်ခု** သာ"""
    if not cues:
        return 0
    return len({(c.get("props") or {}).get("event")
                or round(float(c.get("startTime") or 0), 2) for c in cues})


class SfxDur(unittest.TestCase):

    def test_budget_uses_out_dur(self):
        """out_dur ပေးလျှင် အဲဒါနဲ့ တွက်ရမည်"""
        self.assertEqual(SP.budget(dict(per_min=PM), OUT), int(PM * OUT / 60.0))
        self.assertEqual(SP.budget(dict(per_min=PM), SRC), int(PM * SRC / 60.0))
        self.assertLess(SP.budget(dict(per_min=PM), OUT),
                        SP.budget(dict(per_min=PM), SRC))

    def test_plan_respects_out_dur(self):
        """ဖြတ်ပြီး အရှည် ပေးလျှင် cue အရေအတွက် လျော့ရမည်"""
        ev = _events(24, SRC)
        a = PL.sfx_plan(ev, SRC, PM, style="headtop")
        b = PL.sfx_plan(ev, SRC, PM, style="headtop", out_dur=OUT)
        ma = _moments(a); mb = _moments(b)
        self.assertGreater(ma, 0, "မူရင်းနဲ့ဆို cue ရရမည်")
        self.assertLessEqual(mb, ma, "ဖြတ်ပြီး အရှည်ဆို မပိုရ")

    def test_density_gate_would_pass(self):
        """ဖြတ်ပြီး အရှည်နဲ့ တွက်လျှင် ဂိတ် (≤၆.၀/min) အောင်ရမည်"""
        ev = _events(24, SRC)
        cues = PL.sfx_plan(ev, SRC, PM, style="headtop", out_dur=OUT)
        moments = _moments(cues)
        per = moments / (max(60.0, OUT) / 60.0)
        self.assertLessEqual(round(per, 2), PM,
                             f"{moments} moments / {OUT}s = {per:.2f}/min > {PM}")

    def test_old_way_would_fail(self):
        """out_dur မပေးလျှင် ဂိတ် ကျနိုင်သည် — ဒါက ပြင်ခဲ့သော အမှား"""
        ev = _events(24, SRC)
        cues = PL.sfx_plan(ev, SRC, PM, style="headtop")
        moments = _moments(cues)
        self.assertGreater(moments, int(PM * OUT / 60.0),
                           "မူရင်းနဲ့ တွက်လျှင် ထွက်ဖိုင်ရဲ့ ဘောင် ကျော်သင့်သည်")

    def test_out_dur_zero_falls_back(self):
        """out_dur ၀/None ဆို မူရင်းကို ပြန်သုံးရမည် — ကျဘမ်း မဖြစ်ရ"""
        ev = _events(8, SRC)
        for bad in (None, 0, 0.0, -5):
            self.assertIsInstance(
                PL.sfx_plan(ev, SRC, PM, style="headtop", out_dur=bad), list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
