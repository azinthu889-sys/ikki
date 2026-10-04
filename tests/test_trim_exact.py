# -*- coding: utf-8 -*-
"""✂ စကားစုထဲ ဖြတ်ချက်ကို **ပို့တဲ့အတိုင်း အတိအကျ** ဖြတ်ကြောင်း

Zin ၂၀၂၆-၁၀-၀၄: 「တိကျမှု · စိတ်ကြိုက် ချိန်ညှိနိုင်ဖို့」。 Script Editor မှာ
စာလုံး ဖြတ်ပြီး ◀▶ (၀.၀၄s) နဲ့ ညှိကာ ဆက်ထားသော အသံကို နားထောင်ပြီးသား —
render က ဖြတ်မှတ်ကို ရွှေ့လျှင် **ကြားခဲ့တာနဲ့ မတူသော** ရလဒ် ထွက်မည်。

`worker/run.py` က ဒီ ✂ တွေကို `CUT.subtract(spans, _inph, None, snap=0.12, db=…)`
နဲ့ ဖြတ်သည်。 snap=0.12 ဆိုပေမယ့် **ရွှေ့ချက် မဖြစ်** — `subtract` က
  · ဘယ်တော့မှ မကျုံ့ (အတွင်းဘက် ချိုင့်ကို ယူလျှင် ပြန်ချ)
  · အပြင်ဘက် ကျယ်လျှင် တိတ်ဆိတ်မှု မြေပုံ (`sil`) ထဲ ဖြစ်မှသာ — `None` ⇒ မကျယ်
ဒီ test က အဲဒီ အပြုအမူကို ချုပ်ထားသည်။ snap ကို တစ်ယောက်ယောက် ပြောင်းလိုက်လျှင်
editor ရဲ့ နားထောင်ကြည့်ချက်နဲ့ render ကွဲမည် ⇒ ဒီမှာ ကျမည်。

⚠️ ၂၀၂၆-၁၀-၀၄ မှာ ဒီ ✂ တွေ ±0.12s ရွေ့တယ်ထင်ပြီး 「pin」 စနစ် (editor → API →
   worker) ဆောက်ခဲ့သည် — `subtract` ကို ဖတ်ပြီးမှ ရွှေ့ချက် **မရှိ** ကြောင်း
   သိရ၍ ဖယ်လိုက်သည်。 ပြန်မဆောက်ခင် ဒီ test ကို ကြည့်ပါ。
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "core"))
import cut as CUT  # noqa: E402

HOP = 0.02


def _track(dips):
    """20ms dB track · `dips` [(a,b)] ကြား −60dB · ကျန်တာ စကား −20dB"""
    return [(-60.0 if any(a <= i * HOP < b for a, b in dips) else -20.0)
            for i in range(200)]


class TrimExact(unittest.TestCase):
    def _cut(self, req, dips):
        spans, rm = CUT.subtract([[0.0, 4.0]], [req], None, snap=0.12,
                                 db=_track(dips), hop=HOP)
        return spans, rm

    def _assert_exact(self, req, dips):
        spans, rm = self._cut(req, dips)
        self.assertEqual(len(spans), 2, spans)
        self.assertAlmostEqual(spans[0][1], req[0], places=3, msg=spans)
        self.assertAlmostEqual(spans[1][0], req[1], places=3, msg=spans)
        self.assertAlmostEqual(rm, req[1] - req[0], places=3)

    def test_dip_just_outside(self):          # ချဲ့ချင်စရာ ချိုင့် အပြင်ဘက်
        self._assert_exact([1.00, 2.00], [(0.92, 0.98), (2.02, 2.08)])

    def test_dip_just_inside(self):           # ကျုံ့ချင်စရာ ချိုင့် အတွင်းဘက်
        self._assert_exact([1.00, 2.00], [(1.04, 1.10), (1.90, 1.96)])

    def test_no_dip(self):                    # စကား ဆက်တိုက် (မြန်မာ အများစု)
        self._assert_exact([1.00, 2.00], [])

    def test_worker_call_keeps_sil_none(self):
        """worker ရဲ့ ✂ ဖြတ်ချက်က `sil` မပေးရ — ပေးလျှင် တိတ်ဆိတ်မှုထဲ ကျယ်ပြီး
        နားထောင်ကြည့်ခဲ့တာနဲ့ ကွဲနိုင်သည်"""
        with open(os.path.join(ROOT, "worker", "run.py"), encoding="utf-8") as f:
            s = f.read()
        self.assertRegex(s, r"CUT\.subtract\(spans, _inph, None, snap=0\.12")


if __name__ == "__main__":
    unittest.main()
