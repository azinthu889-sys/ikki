# -*- coding: utf-8 -*-
"""ဖျက်ချက်ကို **အသံရဲ့ အဆုံးထိ ချဲ့**ခြင်း — 「ဖျက်ပေမယ့် မပျောက်」 ကို ပြင်

⚠️⚠️ ၂၀၂၆-၁၀-၀၃ Zin: 「cut engine လုံး၀ အဆင်မပြေ · စကားလုံး ပြတ်/ပျောက် ·
   ရွေးထားတဲ့ ဖျက်ချက် မမှန် · ဖြုတ်တာ မမှန်」。

တကယ့် transcript (ဝါကျ ၃၁ · words ၂၉ · ၁၇၈.၇s) နဲ့ တိုင်းတော့ လက္ခဏာ
၂ ခုက **အမှား တစ်ခုတည်း** ဖြစ်သည်:
   overcut  (တောင်းချက်ထက် ပိုဖြတ်) med ၀.၀၀၀ · max **၀.၀၂၀s** ⇒ သန့်
   leftover (ဖျက်ပေမယ့် ကျန်)      med ၀.၁၂၀ · p90 ၀.၅၆ · max **၀.၈၄၀s**
                                    ⇒ **၂၂/၃၁ = ၇၁% မကောင်း**
ဖျက်ချက်က စောစော ရပ်ပြီး ဝါကျရဲ့ အမြီး ကျန်သည် — နားထောင်ရင်
「စကားလုံး ပြတ်」 လိုပဲ ကြားရသဖြင့် လက္ခဏာ ၂ ခု ဖြစ်နေခဲ့。

⚠️ **word timings က မကူညီနိုင်** — `words[-1].e − seg.end` med **−၀.၀၉၀s**
   (၂၉ ခုထဲ ၃ ခုသာ နောက်ကျ)。 အသံက ၂ ခုလုံးထက် ဆက်နေသည်。

⚠️ ဘောင်ကို **scan ၁၆ တွဲ** လုပ်ပြီး ရွေးသည် — `cap` ၀.၈၀ တင်လျှင်
   overcut max ၀.၀၂ → ၀.၃၆s (နောက်ဝါကျ မျို)。
"""
import math
import os
import struct
import sys
import tempfile
import unittest
import wave

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "core"))
SR = 16000
HOP = 0.020


def _mk(plan, path):
    """plan = [(အကြာ, အဆင့်)] — အဆင့် ၀ ဆို တိတ်"""
    import random
    random.seed(3)
    fr = []
    ph = 0.0
    for d, amp in plan:
        for _ in range(int(d * SR)):
            if amp <= 0:
                fr.append(random.gauss(0, 0.0003))
            else:
                ph += 2 * math.pi * 130.0 / SR
                fr.append(amp * (math.sin(ph) + 0.4 * math.sin(3 * ph)) / 1.4)
    w = wave.open(path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32000))
                           for v in fr))
    w.close()
    return sum(d for d, _ in plan)


def _db(path):
    import subprocess
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    h = int(SR * HOP)
    n = len(x) // h
    fr = x[:n * h].reshape(n, h)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1) + 1e-12) + 1e-12), len(x) / SR


class Grow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.w = os.path.join(cls.d, "a.wav")
        # ၀–၂ စကား · ၂–၃ တိတ် · ၃–၅ စကား · ၅–၆ တိတ် · ၆–၈ စကား
        cls.dur = _mk([(2.0, 0.30), (1.0, 0.0), (2.0, 0.30),
                       (1.0, 0.0), (2.0, 0.30)], cls.w)
        cls.db, _d = _db(cls.w)

    def test_a_short_request_grows_to_the_end_of_speech(self):
        """⚠️ **အဓိက စစ်ချက်** — ဝါကျ ၃–၅s ကို ၃.၀–၄.၅ ဟု တောင်းလျှင်
           ကျန် ၀.၅s ကို ချဲ့ပေးရမည် (ဒါက ၇၁% အမှားရဲ့ ပုံစံ)。
        """
        import cut as CUT
        a, b = CUT.grow_to_speech(3.0, 4.5, self.db, HOP, self.dur)
        self.assertGreater(b, 4.5, (a, b))
        self.assertAlmostEqual(b, 5.0, delta=0.12, msg=(a, b))

    def test_it_stops_at_the_silence_and_never_eats_the_neighbour(self):
        """⚠️ **ဒါက cap ရဲ့ အလုပ်** — ချဲ့ချက်က နောက်ဝါကျ (၆s) ကို
           မရောက်ရ。 cap ၀.၈၀ တင်လျှင် overcut max ၀.၀၂ → ၀.၃၆s。
        """
        import cut as CUT
        a, b = CUT.grow_to_speech(3.0, 4.5, self.db, HOP, self.dur)
        self.assertLess(b, 6.0, (a, b))

    def test_an_exact_request_is_left_alone(self):
        import cut as CUT
        a, b = CUT.grow_to_speech(3.0, 5.0, self.db, HOP, self.dur)
        self.assertAlmostEqual(a, 3.0, delta=0.12)
        self.assertLess(b, 6.0)

    def test_it_never_shrinks_the_request(self):
        """⚠️ ကျုံ့လျှင် ဖျက်ခိုင်းထားတာ မဖျက်ဖြစ်ဘဲ ကျန်မည်"""
        import cut as CUT
        for a0, b0 in ((3.0, 4.5), (0.5, 1.2), (6.2, 7.0), (2.2, 2.8)):
            a, b = CUT.grow_to_speech(a0, b0, self.db, HOP, self.dur)
            self.assertLessEqual(a, a0 + 1e-9, (a0, b0, a, b))
            self.assertGreaterEqual(b, b0 - 1e-9, (a0, b0, a, b))

    def test_no_energy_map_means_no_guessing(self):
        import cut as CUT
        self.assertEqual(CUT.grow_to_speech(1.0, 2.0, None, HOP, 8.0), (1.0, 2.0))
        self.assertEqual(CUT.grow_to_speech(1.0, 2.0, self.db, None, 8.0),
                         (1.0, 2.0))

    def test_subtract_applies_it(self):
        import cut as CUT
        out, rem = CUT.subtract([(0.0, self.dur)], [(3.0, 4.5)], None,
                                db=self.db, hop=HOP, grow=True, dur=self.dur)
        kept = [(x, y) for x, y in out if y > 4.5 and x < 6.0]
        left = sum(min(y, 5.0) - max(x, 4.5) for x, y in kept
                   if min(y, 5.0) > max(x, 4.5))
        self.assertLess(left, 0.15, (out, left))

    def test_subtract_can_turn_it_off(self):
        """⚠️ **ဝါကျအတွင်း ဖြတ်ချက်** (✂ ချောင်းဆိုးသံ) က ချဲ့လို့ မရ"""
        import cut as CUT
        out, _r = CUT.subtract([(0.0, self.dur)], [(3.0, 4.5)], None,
                               db=self.db, hop=HOP, grow=False, dur=self.dur)
        left = sum(min(y, 5.0) - max(x, 4.5) for x, y in out
                   if min(y, 5.0) > max(x, 4.5))
        self.assertGreater(left, 0.25, (out, left))


class Wiring(unittest.TestCase):
    def setUp(self):
        import io
        self.s = io.open(os.path.join(HERE, "..", "worker", "run.py"),
                         encoding="utf-8").read()

    def test_sentence_deletions_grow(self):
        i = self.s.find("spans, _rm = CUT.subtract(spans, user_drop,")
        self.assertGreater(i, 0)
        self.assertIn("grow=True", self.s[i:i + 300])
        self.assertIn('dur=float(m["dur"])', self.s[i:i + 300])

    def test_in_phrase_trims_do_not_grow(self):
        """⚠️⚠️ **၂ ခု မတူ** — ဝါကျ ဖျက်ချက်က တစ်ခုလုံး ဖြစ်၍ ချဲ့ရသည်၊
           ဝါကျအတွင်း ဖြတ်ချက်က ချောင်းဆိုးသံ ဖြစ်၍ ချဲ့လျှင် ဘေးက
           စကားလုံးတွေ ပါသွားမည်。
        """
        i = self.s.find("spans, _rm3 = CUT.subtract(spans, _inph,")
        self.assertGreater(i, 0)
        self.assertIn("grow=False", self.s[i:i + 300])

    def test_the_constants_record_where_they_came_from(self):
        import io
        src = io.open(os.path.join(HERE, "..", "core", "cut.py"),
                      encoding="utf-8").read()
        i = src.find("GROW_TOL")
        self.assertGreater(i, 0)
        w = src[max(0, i - 2200):i + 100]
        self.assertIn("၂၂/၃၁", w)          # ပြင်ခင် တိုင်းချက်
        self.assertIn("၁၅/၃၁", w)          # ပြင်ပြီး တိုင်းချက်
        self.assertIn("measure-distribution-rule", w)


if __name__ == "__main__":
    unittest.main(verbosity=2)
