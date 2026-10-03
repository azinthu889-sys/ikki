# -*- coding: utf-8 -*-
"""ဖျက်ချက် **၁၀၀% တိကျမှု** — ကျန်လည်း မကျန်ရ · ပိုလည်း မဖြတ်ရ

⚠️⚠️ ၂၀၂၆-၁၀-၀၃ Zin: 「cut engine လုံး၀ အဆင်မပြေ · စကားလုံး ပြတ်/ပျောက် ·
   ရွေးထားတဲ့ ဖျက်ချက် မမှန်」 ⇒ 「ကျန်တဲ့ ၁၅/၃၁ ကိုပါ သုညဖြစ်အောင်」。

တကယ့် transcript (ဝါကျ ၃၁ · ၁၇၈.၇s) နဲ့ တိုင်းချက် — **ကုဒ်လမ်းကြောင်း အစစ်**:
   ပြင်မခင် : ပိုဖြတ်မိ max ၀.၀၁၀ · ကျန်နေ max ၀.၃၁၀s · **၅/၃၁**
   ပြင်ပြီး : ပိုဖြတ်မိ max ၀.၀၅၀ · ကျန်နေ max ၀.၀၅၀s · **၀/၃၁**

ပြင်ချက် ၃ ခု ပေါင်းမှ သုည ဖြစ်သည် — တစ်ခုချင်းက မလုံလောက်:
   ① ချဲ့ချက်ကို **ဘေးဝါကျ နယ်နိမိတ်**နဲ့ ကန့်သတ် (ပုံသေ cap မဟုတ်)
   ② ချဲ့ချက်အတွက် **၁၀ms** track (၂၀ms က ကိုယ်တိုင် ±၀.၀၄s အမှား ပေး)
   ③ `snapto` ကို **ကျုံ့ခွင့် မပေး**

⚠️ စမ်းပြီး **ပယ်ထားသော** နည်း ၄ ခု — ပြန်မထည့်မိစေရန်:
   ✗ ပုံသေ cap ၀.၄၀s     → ပိုဖြတ်မိ max ၀.၇၆s (၉/၃၁) — ဘေးဝါကျ မကြည့်၍
   ✗ အနီးဆုံး အသံ အနားသတ် → ပိုဖြတ်မိ max ၀.၆၂s — အနားသတ်က ဝါကျအတွင်း များ
   ✗ ဝါကျ အလယ်မှတ်        → ပိုဖြတ်မိ p90 ၀.၆၈s
   ✗ 「စကားလုံး အလယ်မှာ မရပ်ရ」 → ၂/၃၁ → ၆/၃၁ · ပိုဖြတ်မိ max ၀.၃၅s。
     မြန်မာစကားမှာ အသံထွက်မှုက **ဝါကျကြားမှာလည်း ဆက်နေ**သဖြင့်
     「အသံ ဆက် = စကားလုံး တစ်လုံးတည်း」 မဟုတ် (ဘောင် ၀.၀၄–၀.၃၀ အားလုံး ဆိုး)
   ✗ word timings — `words[-1].e − seg.end` med **−၀.၀၉၀s** (၂၉ ထဲ ၃ ခုသာ
     နောက်ကျ)。 အသံက ၂ ခုလုံးထက် ဆက်နေသည် ⇒ မကူညီနိုင်
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


class Bounded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.w = os.path.join(cls.d, "a.wav")
        # ဝါကျ A ၀–၂ · တိတ် ၂–၃ · ဝါကျ B ၃–၅ · တိတ် ၅–၆ · ဝါကျ C ၆–၈
        cls.dur = _mk([(2.0, 0.30), (1.0, 0.0), (2.0, 0.30),
                       (1.0, 0.0), (2.0, 0.30)], cls.w)
        cls.db, _x = _db(cls.w)

    def test_a_short_request_grows_to_the_end_of_speech(self):
        """⚠️ **အဓိက** — B ကို ၃.၀–၄.၅ တောင်းလျှင် ၅.၀ ထိ ချဲ့ပေးရမည်"""
        import cut as CUT
        a, b = CUT.grow_to_speech(3.0, 4.5, self.db, HOP, self.dur,
                                  lo=2.0, hi=6.0)
        self.assertAlmostEqual(b, 5.0, delta=0.08, msg=(a, b))

    def test_the_bound_is_absolute(self):
        """⚠️⚠️ **ဒါက ပုံသေ cap ကို အစားထိုးသော အရာ**。 ဘောင် ကျော်လျှင်
           ဘေးဝါကျ ပါသွားမည် — ပုံသေ cap နဲ့ ပိုဖြတ်မိ max ၀.၇၆s ဖြစ်ခဲ့。
        """
        import cut as CUT
        a, b = CUT.grow_to_speech(3.0, 4.5, self.db, HOP, self.dur,
                                  lo=2.9, hi=4.6)
        self.assertLessEqual(b, 4.6 + 1e-9, (a, b))
        self.assertGreaterEqual(a, 2.9 - 1e-9, (a, b))

    def test_without_a_bound_it_does_nothing(self):
        """⚠️ နယ်နိမိတ် မသိဘဲ မချဲ့ရ"""
        import cut as CUT
        self.assertEqual(CUT.grow_to_speech(3.0, 4.5, self.db, HOP, self.dur),
                         (3.0, 4.5))

    def test_no_energy_map_means_no_guessing(self):
        import cut as CUT
        self.assertEqual(
            CUT.grow_to_speech(1.0, 2.0, None, HOP, 8.0, lo=0.0, hi=8.0),
            (1.0, 2.0))

    def test_it_never_shrinks(self):
        import cut as CUT
        for a0, b0 in ((3.0, 4.5), (0.5, 1.2), (6.2, 7.0), (2.2, 2.8)):
            a, b = CUT.grow_to_speech(a0, b0, self.db, HOP, self.dur,
                                      lo=0.0, hi=self.dur)
            self.assertLessEqual(a, a0 + 1e-9, (a0, b0, a, b))
            self.assertGreaterEqual(b, b0 - 1e-9, (a0, b0, a, b))


class Subtract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.w = os.path.join(cls.d, "b.wav")
        cls.dur = _mk([(2.0, 0.30), (1.0, 0.0), (2.0, 0.30),
                       (1.0, 0.0), (2.0, 0.30)], cls.w)
        cls.db, _x = _db(cls.w)

    def _left(self, out, a, b):
        return sum(min(y, b) - max(x, a) for x, y in out
                   if min(y, b) > max(x, a))

    def test_bounds_make_the_deletion_complete(self):
        import cut as CUT
        out, _r = CUT.subtract([(0.0, self.dur)], [(3.0, 4.5)], None,
                               bounds=[(2.0, 6.0)], gdb=self.db, ghop=HOP,
                               dur=self.dur)
        self.assertLess(self._left(out, 4.5, 5.0), 0.10, out)

    def test_no_bounds_means_no_growth(self):
        """⚠️ ဝါကျ**အတွင်း** ✂ ဖြတ်ချက် (ချောင်းဆိုးသံ) က ချဲ့လို့ မရ"""
        import cut as CUT
        out, _r = CUT.subtract([(0.0, self.dur)], [(3.0, 4.5)], None,
                               db=self.db, hop=HOP, dur=self.dur)
        self.assertGreater(self._left(out, 4.5, 5.0), 0.25, out)

    def test_the_cut_never_shrinks_the_request(self):
        """⚠️⚠️ `snapto` က ဦးစားပေး ဘက်မှာ ရွေးစရာ မရှိလျှင် တောင်းချက်
           **အတွင်းသို့** ဝင်သွားပြီး ဖျက်ခိုင်းထားတာ ကျန်ခဲ့သည် —
           ကျန်သေးသော အမှား ၂/၃၁ လုံးက ဒါကြောင့် (၂ → ၀)。
        """
        import cut as CUT
        for req in ((3.0, 5.0), (3.2, 4.8), (0.4, 1.9), (6.1, 7.4)):
            out, _r = CUT.subtract([(0.0, self.dur)], [req], None,
                                   db=self.db, hop=HOP, dur=self.dur)
            self.assertLess(self._left(out, req[0], req[1]), 0.02, (req, out))

    def test_bounds_track_their_own_drop_after_sorting(self):
        """⚠️ `subtract` က `drop` ကို စဉ်သည် ⇒ `bounds` ကိုပါ **အတူတွဲ၍**
           စဉ်ရမည်。 မတွဲလျှင် ဖျက်ချက် တစ်ခုက တခြားတစ်ခုရဲ့ နယ်နိမိတ် ရမည်。
        """
        import cut as CUT
        out_a, _1 = CUT.subtract([(0.0, self.dur)], [(6.2, 7.0), (3.0, 4.5)],
                                 None, bounds=[(6.0, 8.0), (2.0, 6.0)],
                                 gdb=self.db, ghop=HOP, dur=self.dur)
        out_b, _2 = CUT.subtract([(0.0, self.dur)], [(3.0, 4.5), (6.2, 7.0)],
                                 None, bounds=[(2.0, 6.0), (6.0, 8.0)],
                                 gdb=self.db, ghop=HOP, dur=self.dur)
        self.assertEqual([(round(x, 2), round(y, 2)) for x, y in out_a],
                         [(round(x, 2), round(y, 2)) for x, y in out_b])


class Wiring(unittest.TestCase):
    def setUp(self):
        import io
        self.s = io.open(os.path.join(HERE, "..", "worker", "run.py"),
                         encoding="utf-8").read()

    def test_sentence_deletions_get_bounds_and_the_fine_track(self):
        i = self.s.find("spans, _rm = CUT.subtract(spans, user_drop,")
        self.assertGreater(i, 0)
        w = self.s[i:i + 400]
        self.assertIn("bounds=_bounds", w)
        self.assertIn("gdb=_FINETRACK[0]", w)

    def test_in_phrase_trims_get_no_bounds(self):
        """⚠️⚠️ **၂ ခု မတူ** — ဝါကျ ဖျက်ချက်က တစ်ခုလုံး ဖြစ်၍ ချဲ့ရသည်၊
           ဝါကျအတွင်း ဖြတ်ချက်က ချောင်းဆိုးသံ ဖြစ်၍ ချဲ့လျှင် ဘေးက
           စကားလုံးတွေ ပါသွားမည်。
        """
        i = self.s.find("spans, _rm3 = CUT.subtract(spans, _inph,")
        self.assertGreater(i, 0)
        w = self.s[i:i + 300]
        self.assertNotIn("bounds=", w)
        self.assertNotIn("gdb=", w)

    def test_the_fine_track_is_built(self):
        self.assertIn("_M.analyse(wav, frame=CUT.GROW_FRAME)", self.s)
        self.assertIn("_FINETRACK", self.s)

    def test_bounds_come_from_the_adjacent_sentences(self):
        """⚠️ ဝါကျ ကပ်နေလျှင် `segs[i-1].end == segs[i].start` ဖြစ်၍
           ကိန်းစာရင်းကနေ မခွဲနိုင် — ခေါ်သူက တိုက်ရိုက် တွက်ရသည်。
        """
        i = self.s.find("def _bnd_for(")
        self.assertGreater(i, 0)
        w = self.s[i:i + 600]
        self.assertIn("lo = max(lo, _y)", w)
        self.assertIn("hi = min(hi, _x)", w)


class Provenance(unittest.TestCase):
    def test_the_rejected_approaches_are_recorded(self):
        """⚠️ ပယ်ထားသော နည်းတွေကို မှတ်မထားလျှင် နောက်တစ်ယောက်က
           ပြန်ထည့်မိမည် (ပုံသေ cap က ပိုဆိုးစေသည်)。"""
        import io
        src = io.open(os.path.join(HERE, "..", "core", "cut.py"),
                      encoding="utf-8").read()
        i = src.find("GROW_TOL")
        self.assertGreater(i, 0)
        w = src[max(0, i - 2600):i + 800]
        self.assertIn("၀.၇၆၀", w)                     # ပုံသေ cap ရဲ့ အမှား
        self.assertIn("ဘေးဝါကျ", w)
        self.assertIn("ဝါကျကြားမှာလည်း ဆက်နေ", w)     # ပယ်ထားသော စည်းမျဉ်း


if __name__ == "__main__":
    unittest.main(verbosity=2)
