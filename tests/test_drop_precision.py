# -*- coding: utf-8 -*-
"""သုံးစွဲသူ ဖျက်ချက် — **တောင်းချက်ထက် ပို၍ မဖျက်ရ**

⚠️⚠️ Zin ၂၀၂၆-၁၀-၀၂: 「user ရွေးလိုက်တဲ့ ဖျက်ချက်တစ်ခုချင်းစီကို သေချာ
   ဖြတ်ပေးနိုင်ဖို့ အရမ်းအရေးကြီးတယ်」。 တကယ့်ဖိုင်ပေါ် တိုင်းကြည့်ရာ —
     ဖျက် ၀.၄s ⇒ **ဘေးက စကား ၀.၂၂s ပါသွား** (၃၀/၅၁ ခုမှာ)
     ဖျက် ၀.၉s ⇒ p90 **၀.၅၆s** · အများဆုံး ၀.၆၆s (၂၇/၃၀)
   မြန်မာစာ အမြန်နှုန်းနဲ့ဆို **စကားလုံး တစ်လုံးစာ** ဖြစ်သည်。

အကြောင်းရင်း — `subtract` ရဲ့ `snapto` က ဖြတ်မှတ်ကို တိတ်ဆိတ်မှုဆီ ဆွဲရာမှာ
   `[a−snap, b+snap]` အထိ **ကန့်သတ်မရှိ ကျယ်ခွင့်** ပေးထားသည်。 ဝါကျအလယ်မှာ
   အတိတ်ဆုံးမှတ်က တောင်းချက် ပြင်ပမှာ ရှိတတ်၍ ဘေးက စကား ပါသွားသည်。

⚠️⚠️ **အမှတ် တစ်ခုတည်း စစ်လို့ မရ** — ပထမ ပြင်ချက်မှာ ဆွဲမည့် အမှတ်ကိုသာ
   「တိတ်ဆိတ်မှုထဲလား」 စစ်ခဲ့ရာ ကိန်း **လုံးဝ မပြောင်း**ခဲ့သည်。 တိတ်ဆိတ်မှု
   တစ်ခုရဲ့ **အနားသတ်** က အမြဲ တိတ်ဆိတ်မှုထဲ ဖြစ်ပြီး အဲဒီအနားသတ်ကနေ
   တောင်းချက်အထိ ကြားမှာ စကား ရှိနေနိုင်သည် ⇒ **နယ်ပယ် တစ်ခုလုံး** စစ်ရမည်。
"""
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import cut as C                                               # noqa: E402

SRC = os.path.join(os.path.dirname(__file__), "..", "core", "cut.py")
# စကား ၂ ပိုင်း ကြားမှာ တိတ်ဆိတ်မှု ၁ ခု — လက်နဲ့ ဆောက်ထားသော ပုံစံ
SIL = [(0.0, 1.0), (4.70, 5.30), (9.0, 10.0)]
SPANS = [(0.0, 10.0)]


def _removed(req, spans, sil):
    out, _ = C.subtract(list(spans), [list(req)], sil)
    gone = []
    for p, q in spans:
        cur = p
        for u, v in out:
            if v <= p or u >= q:
                continue
            if u > cur:
                gone.append((cur, u))
            cur = max(cur, v)
        if cur < q:
            gone.append((cur, q))
    return gone, out


class NoOverCut(unittest.TestCase):
    def test_mid_speech_cut_is_exact(self):
        """⚠️ အနီးမှာ တိတ်ဆိတ်မှု မရှိလျှင် **တောင်းချက်အတိုင်း** ဖြတ်ရမည်"""
        gone, out = _removed((6.0, 6.4), SPANS, SIL)
        self.assertEqual(len(gone), 1)
        a, b = gone[0]
        self.assertAlmostEqual(a, 6.0, places=2)
        self.assertAlmostEqual(b, 6.4, places=2)

    def test_does_not_reach_into_speech_for_a_nearby_silence(self):
        """⚠️ **အဓိက** — တိတ်ဆိတ်မှု အနားသတ် ၅.၃၀ က ၅.၅၀ ကနေ ၀.၂၀s အကွာ
           ဖြစ်သော်လည် ကြားမှာ စကား ရှိသဖြင့် ဆွဲလို့ **မရ**"""
        gone, out = _removed((5.50, 6.00), SPANS, SIL)
        a, b = gone[0]
        self.assertGreaterEqual(a, 5.50 - 0.01,
                                "စကားထဲ ပြန်ဆွဲပြီး ဘေးက စကား ဖျက်မိသည်")

    def test_snaps_into_silence_when_the_gap_is_silent(self):
        """⚠️ ကြားက တိတ်နေလျှင် ဆွဲခွင့် ရှိသည် — ဖြတ်မှတ် ပိုညင်သာသည်"""
        gone, out = _removed((5.10, 6.00), SPANS, SIL)
        a, b = gone[0]
        self.assertLessEqual(a, 5.10 + 0.01)
        self.assertGreaterEqual(a, 4.70 - 0.01)

    def test_request_is_fully_removed(self):
        """⚠️ ပို၍ မဖျက်ဖို့ ပြင်ရာမှာ **မဖျက်ဖြစ်တာ** မဖြစ်စေရ"""
        for req in ((6.0, 6.4), (5.50, 6.00), (2.0, 3.0), (7.5, 8.9)):
            gone, out = _removed(req, SPANS, SIL)
            left = sum(max(0.0, min(req[1], q) - max(req[0], p)) for p, q in out)
            self.assertLess(left, 0.02, (req, left))

    def test_whole_gap_checked_not_just_the_point(self):
        src = io.open(SRC, encoding="utf-8").read()
        self.assertIn("def _gap_silent(x, y):", src)
        self.assertIn("_gap_silent(c, req_a)", src)
        self.assertIn("_gap_silent(req_b, c)", src)
        # ⚠️ အမှတ် တစ်ခုတည်း စစ်သော ရေးချက် ကျန်မနေရ
        self.assertNotIn("def _in_sil(t):", src)

    def test_no_silence_list_is_safe(self):
        gone, out = _removed((6.0, 6.4), SPANS, None)
        self.assertEqual(len(gone), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
