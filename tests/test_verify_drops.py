# -*- coding: utf-8 -*-
"""ဖျက်ချက် တစ်ခုချင်း **အတည်ပြုချက်** — ၂ ဖက်လုံး စစ်သည်

⚠️⚠️ Zin ၂၀၂၆-၁၀-၀၃: 「တိကျအောင်လုပ်ပေးဖိ့」。 ယခင် စစ်ချက်က တောင်းချက်နဲ့
   ချန်ထားချက်ရဲ့ **အချိန် ထပ်မှု**ကိုသာ တိုင်းသည် ⇒ ချို့ယွင်းချက် ၂ ခု:
     · တိတ်ဆိတ်မှု ကျန်တာကိုပါ 「မဖျက်ဖြစ်」 ဟု သတိပေး (အန္တရာယ် မရှိ)
     · **ပိုဖြတ်မိမှု လုံးဝ မစစ်** — ဘေးဝါကျရဲ့ စကားလုံး ပါသွားတာက
       「စကားလုံး ပြတ်」 ဖြစ်ပြီး ပိုဆိုးသည် (Zin ရဲ့ လက္ခဏာ ①)

⚠️ **မီးမလောင်ဖူးသေးသော စစ်ချက်ကို မယုံရ** — `Fires` က ဖမ်းနိုင်ကြောင်း
   ပြရန် ဖြစ်သည် (ikki-measure-the-real-path)。

⚠️ တိုင်းနည်း ၂ ခု စမ်းပြီး ပြင်ခဲ့သည် — ပြန်မမှားမိစေရန်:
   ✗ **တောင်းချက်**နဲ့ တိုင်း → ဝါကျရဲ့ ကိုယ်ပိုင် အမြီး ဖြတ်တာကို
     「ပိုဖြတ်မိ」 ဟု မှားခေါ် (ဝါကျ ၂၇ မှာ ၀.၁၅s) — မှန်ကန်သော အပြုအမူကို
     အမှား အဖြစ် သတ်မှတ်ရာ ကျသည်
   ✗ ဖျက်ချက် တစ်ခုချင်း **သီးသန့်** စစ် → ကပ်လျက် ဖျက်လျှင် အပြန်အလှန်
     အပြစ်တင်မိ (၄၆ ခုထဲ ၄ ခု · ပိုဖြတ်မိ max ၂.၇၃s)
   ✓ **ဘောင် အားလုံး ပေါင်းစု** ပြင်ပ ဖြုတ်မိမှသာ အမှား
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
HOP = 0.010


def _mk(plan, path):
    import random
    random.seed(5)
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


def _db(path, hop=HOP):
    import subprocess
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    h = int(SR * hop)
    n = len(x) // h
    fr = x[:n * h].reshape(n, h)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1) + 1e-12) + 1e-12), len(x) / SR


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.w = os.path.join(cls.d, "v.wav")
        # A ၀–၂ · တိတ် ၂–၃ · B ၃–၅ · တိတ် ၅–၆ · C ၆–၈
        cls.dur = _mk([(2.0, 0.30), (1.0, 0.0), (2.0, 0.30),
                       (1.0, 0.0), (2.0, 0.30)], cls.w)
        cls.db, _x = _db(cls.w)

    def _v(self, reqs, spans, bounds=None):
        import cut as CUT
        return CUT.verify_drops(reqs, spans, self.db, HOP, self.dur,
                                bounds=bounds)


class Clean(Base):
    def test_a_perfect_cut_is_clean(self):
        v = self._v([(3.0, 5.0)], [(0.0, 2.5), (5.5, self.dur)],
                    bounds=[(2.0, 6.0)])
        self.assertEqual(v, [(0.0, 0.0)], v)

    def test_silence_left_behind_is_not_an_error(self):
        """⚠️ ယခင် စစ်ချက်က အချိန် ထပ်မှုကို တိုင်း၍ ဒါကို သတိပေးခဲ့သည်"""
        v = self._v([(2.2, 5.0)], [(0.0, 2.6), (5.2, self.dur)],
                    bounds=[(2.0, 6.0)])
        self.assertLess(v[0][0], 0.02, v)

    def test_the_sentences_own_tail_is_not_overcut(self):
        """⚠️⚠️ ဝါကျရဲ့ အမြီးက `seg.end` ပြင်ပမှာ ရှိတတ်သည် — အဲဒါ ဖြတ်တာက
           **မှန်**သည်。 တောင်းချက်နဲ့ တိုင်းလျှင် မှားခေါ်မည်。
        """
        v = self._v([(3.0, 4.5)], [(0.0, 2.5), (5.5, self.dur)],
                    bounds=[(2.0, 6.0)])
        self.assertLess(v[0][1], 0.02, v)


class Fires(Base):
    """⚠️ **ဖမ်းနိုင်ကြောင်း ပြရန်** — ၀ တွေ့တာက ၂ မျိုး ဖြစ်နိုင်သည်"""

    def test_it_catches_speech_left_behind(self):
        """ဝါကျ B ကို ဖျက်ခိုင်းပြီး ပထမ ၁s ပဲ ဖြတ် ⇒ ၁s ကျန်"""
        v = self._v([(3.0, 5.0)], [(0.0, 2.5), (4.0, self.dur)],
                    bounds=[(2.0, 6.0)])
        self.assertGreater(v[0][0], 0.80, v)

    def test_it_catches_the_neighbour_being_cut(self):
        """⚠️ **အရေးကြီးဆုံး** — ဘေးဝါကျ C ရဲ့ အစ ၀.၅s ပါသွားတာကို ဖမ်းရမည်。
           ဒါက Zin ရဲ့ 「စကားလုံး ပြတ်」。
        """
        v = self._v([(3.0, 5.0)], [(0.0, 2.5), (6.5, self.dur)],
                    bounds=[(2.0, 6.0)])
        self.assertGreater(v[0][1], 0.40, v)

    def test_it_catches_the_previous_sentence_being_cut(self):
        v = self._v([(3.0, 5.0)], [(0.0, 1.5), (5.5, self.dur)],
                    bounds=[(2.0, 6.0)])
        self.assertGreater(v[0][1], 0.40, v)


class Adjacent(Base):
    """⚠️⚠️ ကပ်လျက် ဖျက်ချက် ၂ ခု — အပြန်အလှန် အပြစ် မတင်ရ"""

    def test_two_adjacent_deletions_do_not_blame_each_other(self):
        """A နဲ့ B ကို ၂ ခုလုံး ဖျက် ⇒ ၂ ခုလုံး သန့်ရမည်。
           တစ်ခုချင်း သီးသန့် စစ်လျှင် ၄၆ ခုထဲ ၄ ခု မှားခဲ့သည်
           (ပိုဖြတ်မိ max ၂.၇၃s)。
        """
        v = self._v([(0.0, 2.0), (3.0, 5.0)], [(5.5, self.dur)],
                    bounds=[(0.0, 3.0), (2.0, 6.0)])
        for kept, over in v:
            self.assertLess(kept, 0.05, v)
            self.assertLess(over, 0.05, v)

    def test_three_in_a_row_stay_clean(self):
        v = self._v([(0.0, 2.0), (3.0, 5.0), (6.0, 8.0)], [],
                    bounds=[(0.0, 3.0), (2.0, 6.0), (5.0, self.dur)])
        for kept, over in v:
            self.assertLess(kept, 0.05, v)
            self.assertLess(over, 0.05, v)


class Shape(Base):
    def test_no_track_means_none(self):
        import cut as CUT
        self.assertIsNone(CUT.verify_drops([(1, 2)], [], None, HOP, 8.0))
        self.assertIsNone(CUT.verify_drops([], [], self.db, HOP, 8.0))

    def test_the_floor_is_the_grid_limit(self):
        """⚠️ ၁၀ms grid ကို ၂ ဖက် သုံးရာက လာသော ကိရိယာရဲ့ ကန့်သတ်ချက် —
           ဒီအောက်ကို အမှား ဟု မခေါ်နိုင်。"""
        import cut as CUT
        self.assertAlmostEqual(CUT.VERIFY_FLOOR, 0.050, places=3)
        self.assertGreaterEqual(CUT.VERIFY_FLOOR, 2 * CUT.GROW_FRAME * 2)


class Wiring(unittest.TestCase):
    def setUp(self):
        import io
        self.s = io.open(os.path.join(HERE, "..", "worker", "run.py"),
                         encoding="utf-8").read()

    def test_the_worker_verifies_with_bounds_and_the_fine_track(self):
        i = self.s.find("_vf = CUT.verify_drops(")
        self.assertGreater(i, 0)
        w = self.s[i:i + 300]
        self.assertIn("_FINETRACK[0]", w)
        self.assertIn("bounds=_bounds", w)

    def test_both_directions_reach_the_user(self):
        """⚠️ `flag_list` ထဲ မထည့်လျှင် သုံးစွဲသူ ဘယ်တော့မှ မမြင်ရ"""
        self.assertIn('kind="drop_left"', self.s)
        self.assertIn('kind="drop_over"', self.s)
        self.assertIn('st["drop_over"] = _over', self.s)

    def test_a_verification_failure_is_announced(self):
        i = self.s.find("_vf = CUT.verify_drops(")
        w = self.s[max(0, i - 200):i + 700]
        self.assertIn("ဖျက်ချက် အတည်ပြုချက် မရ", w)

    def test_success_reports_the_numbers(self):
        """⚠️ 「ပြီးပြီ」 တင် ပြလျှင် ဘယ်လောက် တိကျလဲ မသိရ"""
        self.assertIn("ကျန်နေ အများဆုံး", self.s)
        self.assertIn("ပိုဖြတ်မိ အများဆုံး", self.s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
