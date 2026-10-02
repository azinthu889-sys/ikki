# -*- coding: utf-8 -*-
"""ဖြတ်ချက် စစ်ဆေးမှု — **mask ကို မယုံဘဲ** ဖြုတ်လိုက်တဲ့ အသံကို တိုင်းသည်

⚠️⚠️ **ဘာကို ပြင်တာလဲ** — `cut_in_speech` စစ်ချက်က `measure.speech()` ရဲ့
   mask နဲ့ စစ်ပြီး၊ ဖြတ်မှတ် ချတဲ့ engine ကလည်း **အဲဒီ mask အတိုင်းပဲ**
   ဖြတ်သည်。 ⇒ mask က စကားကို လွတ်သွားလျှင် engine က ဖြတ်မိပြီး
   စစ်ချက်ကလည်း 「တိတ်ဆိတ်မှုပဲ」 ဟု အတည်ပြုမည် —
   **ဘယ်တော့မှ မကျနိုင်သော စစ်ချက်** (ikki-measure-the-real-path)。

⚠️ **မီးမလောင်ဖူးသေးသော စစ်ချက်ကို မယုံရ** — အောက်က `test_it_fires_on_*`
   တွေက ဖမ်းနိုင်ကြောင်း ပြရန် ဖြစ်သည်。 「၀ တွေ့တယ်」 တစ်ခုတည်းက
   「ကောင်းတယ်」 သို့မဟုတ် 「ဘယ်တော့မှ မမိဘူး」 နှစ်မျိုးလုံး ဖြစ်နိုင်。

⚠️ ကိန်းဘောင်တွေက **ဖိုင် ၁ ခု** ကနေ တိုင်းထားသည် (၁၇၈.၇s · aroll ·
   နမူနာ စကား ၂၀၀ · တိတ် ၂၀၀) ⇒ **ဂိတ် မလုပ်ရသေး**。 ဖိုင် အများနဲ့
   တိုင်းပြီးမှ ဘောင် ချရမည် (measure-distribution-rule)。
"""
import math
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "core"))


def _tone(path, plan, sr=16000):
    """plan = [(အကြာ, အဆင့်)] — အဆင့် ၀ ဆို တိတ်"""
    import wave
    import struct
    import random
    random.seed(11)
    fr = []
    ph = 0.0
    for d, amp in plan:
        for i in range(int(d * sr)):
            if amp <= 0:
                v = random.gauss(0, 0.0004)       # အခန်း ဆူညံသံ
            else:
                # စကားနဲ့ တူအောင် — ၁၂၀Hz မူလ + harmonic + အနည်းငယ် ဆူညံ
                ph += 2 * math.pi * 120.0 / sr
                v = amp * (math.sin(ph) + 0.5 * math.sin(2 * ph)
                           + 0.3 * math.sin(3 * ph)) / 1.8
                v += random.gauss(0, amp * 0.05)
            fr.append(max(-1.0, min(1.0, v)))
    w = wave.open(path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(b"".join(struct.pack("<h", int(x * 32000)) for x in fr))
    w.close()
    return sum(d for d, _ in plan)


class Fires(unittest.TestCase):
    """ဖမ်းနိုင်ကြောင်း — **အဖြေ သိထားသော** ဖြတ်ချက်များနဲ့"""

    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.d = tempfile.mkdtemp()
        cls.w = os.path.join(cls.d, "t.wav")
        # ၀–၂ စကား · ၂–၃ တိတ် · ၃–၅ စကား · ၅–၆ တိတ် · ၆–၈ စကား
        cls.dur = _tone(cls.w, [(2.0, 0.30), (1.0, 0.0), (2.0, 0.30),
                                (1.0, 0.0), (2.0, 0.30)])

    def _lr(self, spans):
        import cut as CUT
        return CUT.loud_removed(self.w, spans, self.dur)

    def test_cutting_only_silence_is_clean(self):
        """တိတ်ဆိတ်မှု ၂ ခုကို ဖြုတ် ⇒ ဂိတ်ကျော် **၀**"""
        r = self._lr([(0.0, 2.0), (3.0, 5.0), (6.0, 8.0)])
        self.assertIsNotNone(r)
        self.assertEqual(r["n"], 0, r)
        self.assertLess(r["pct"], 20.0, r)

    def test_it_fires_on_a_half_second_of_speech(self):
        """⚠️ **အဓိက စစ်ချက်** — စကား ၀.၅၆s ဖြုတ်လျှင် မိရမည်

        ဒါက `in_speech` မမိခဲ့သော အမျိုးအစား အတိအကျ。
        """
        r = self._lr([(0.0, 3.50), (4.06, 8.0)])
        self.assertIsNotNone(r)
        self.assertGreaterEqual(r["n"], 1, r)
        a, b = r["regions"][0][0], r["regions"][0][1]
        self.assertAlmostEqual(a, 3.50, delta=0.05)
        self.assertAlmostEqual(b, 4.06, delta=0.05)

    def test_it_fires_on_a_whole_sentence(self):
        r = self._lr([(0.0, 3.0), (5.0, 8.0)])
        self.assertGreaterEqual(r["n"], 1, r)

    def test_a_click_is_not_flagged(self):
        """⚠️ ၆၀ms ဖြတ်ချက်က ကလစ်သံ — စကား မဟုတ် ⇒ မပယ်ရ"""
        r = self._lr([(0.0, 3.50), (3.56, 8.0)])
        self.assertEqual(r["n"], 0, r)

    def test_nothing_removed_is_clean(self):
        r = self._lr([(0.0, self.dur)])
        self.assertEqual(r["n"], 0, r)
        self.assertEqual(r["loud_s"], 0.0, r)


class Shape(unittest.TestCase):
    def test_a_missing_file_does_not_raise(self):
        """⚠️ တိုင်းချက် မရတာက render မထွက်ရလောက်အောင် မဟုတ်"""
        import cut as CUT
        self.assertIsNone(CUT.loud_removed("/no/such.wav", [(0, 1)], 1.0))

    def test_empty_spans_give_none(self):
        import cut as CUT
        self.assertIsNone(CUT.loud_removed("/no/such.wav", [], 10.0))

    def test_the_constants_are_documented_as_uncalibrated(self):
        """⚠️ ဖိုင် ၁ ခုကနေ ဘောင် မချရ — ဂိတ် မလုပ်ကြောင်း ရေးထားရမည်"""
        import io
        src = io.open(os.path.join(HERE, "..", "core", "cut.py"),
                      encoding="utf-8").read()
        i = src.find("LOUD_NEAR_DB")
        self.assertGreater(i, 0)
        w = src[max(0, i - 900):i + 200]
        self.assertIn("ဂိတ် မလုပ်သေး", w)


class Wiring(unittest.TestCase):
    def setUp(self):
        import io
        self.s = io.open(os.path.join(HERE, "..", "worker", "run.py"),
                         encoding="utf-8").read()

    def test_the_worker_calls_it(self):
        self.assertIn("CUT.loud_removed(wav, spans, float(m[\"dur\"]))", self.s)

    def test_it_runs_after_every_cut_source(self):
        """⚠️⚠️ **အရေးကြီးဆုံး** — engine ဖြတ်ချက်ပဲ စစ်လျှင် auto-clean
           လမ်းကြောင်း လွတ်သွားမည်。 အဲဒါက `in_speech` လွတ်ခဲ့သော
           လမ်းကြောင်း အတိအကျ (ZJL စည်းမျဉ်း ⑧)。
        """
        i = self.s.find("_lr = CUT.loud_removed(")
        self.assertGreater(i, 0)
        for earlier in ("spans = _subtract(spans, auto)",      # auto-clean
                        "spans = _fz",                          # အေးခဲ
                        "CUT.stabilize_visible_spans("):        # user ဖြတ်ချက်
            j = self.s.find(earlier)
            self.assertGreater(j, 0, earlier)
            self.assertLess(j, i, earlier)

    def test_a_failure_is_logged_not_swallowed(self):
        i = self.s.find("_lr = CUT.loud_removed(")
        w = self.s[i:i + 1600]
        self.assertIn("ဖြုတ်ချက် စစ်ဆေးမှု မရ", w)

    def test_it_is_kept_in_the_stats(self):
        i = self.s.find("_lr = CUT.loud_removed(")
        w = self.s[i:i + 900]
        self.assertIn('st["loud_removed"] = _lr', w)


if __name__ == "__main__":
    unittest.main(verbosity=2)
