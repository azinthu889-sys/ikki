# -*- coding: utf-8 -*-
"""ဗီဒီယိုက **စကားစတဲ့ နေရာ**ကနေ စရမည်

⚠️⚠️ ၂၀၂၆-၁၀-၀၄ Zin (preview ကြည့်ပြီး): 「အစဦးဆုံး တစ်စက္ကန့်က မလိုတဲ့
   အရုပ်တွေ ထည့်ထားတယ်။ စကားစပြောတဲ့ နေရာကနေ စထည့်ပေးလို့ ရမလား」。

   ဖရိမ်း ကြည့်တော့ ပထမ ၀.၈s က သူ မိုက်/ကင်မရာကို လက်နဲ့ ချိန်နေတာ。
   `mask` က အဲဒီ လက်ထိသံကို **စကား** ဟု မှတ်သဖြင့် `plan()` က ခေါင်းကို
   အခြား အနားယူချိန်လိုပဲ ဆက်ဆံပြီး မဖြတ်ဖြစ်ခဲ့ပါ。

တိုင်းထားချက် (ဖိုင် ၈ ခု · peak ကို ဖိုင်ကိုယ်တိုင်ရဲ့ စကား p95 နဲ့ နှိုင်း):

    လက်ထိသံ ၄ ခု    ကြာ ၀.၀၈–၀.၁၂s · Δp95 −၁၈.၈ … −၂၁.၀ · voice/med ၀.၅၁–၀.၇၅
    တကယ့် စကား ၆ ခု  ကြာ ၀.၃၄–၃.၃၈s · Δp95  −၈.၈ …   ၀.၀ · voice/med ၀.၉၃–၁.၃၅

⇒ ကြားထဲ **၁၀ dB** ကွာ ⇒ `HEAD_NEAR_DB = 14.0` (အလယ်)。

⚠️ **ဆွေမျိုး တိုင်းချက် ဖြစ်ရမည်** — C0088 ဖိုင်က peak −၅၃ dB ဖြစ်ပြီး
   ပုံသေ dB ဂိတ်ဆိုလျှင် အဲဒီဖိုင် တစ်ခုလုံးကို ဖြတ်ပစ်မည်。

⚠️ သီးခြား စစ်ချက်: Zin ရဲ့ မူရင်းဖိုင်မှာ ASR ရဲ့ **ပထမဝါကျ စချိန်** = ၂၂.၅၂s၊
   acoustic `first_speech` = ၂၂.၅၂s — နည်းလမ်း ၂ ခု သီးခြားစီက ကိန်း **တူ**သည်。
"""
import math
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))

SR = 16000


def _wav(path, parts):
    """parts = [(ကြာချိန်, 'sil'|'click'|'talk')] — ရိုးရှင်းသော စမ်းသပ်အသံ"""
    fr = []
    for dur, kind in parts:
        n = int(dur * SR)
        for i in range(n):
            t = i / SR
            if kind == "sil":
                v = 0.0005 * math.sin(2 * math.pi * 60 * t)
            elif kind == "click":
                # ⚠️ တိုပြီး တိုး — လက်ထိသံ ပုံစံ
                v = 0.030 * math.sin(2 * math.pi * 300 * t) * math.exp(-t * 40)
            else:
                # ⚠️ ကျယ်ပြီး ရှည် — စကား ပုံစံ (500/1500/2500 Hz)
                v = 0.30 * (math.sin(2 * math.pi * 500 * t)
                            + 0.6 * math.sin(2 * math.pi * 1500 * t)
                            + 0.4 * math.sin(2 * math.pi * 2500 * t)) / 2.0
                v *= 0.6 + 0.4 * math.sin(2 * math.pi * 5 * t)
            fr.append(max(-1.0, min(1.0, v)))
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(v * 32000)) for v in fr))
    return path


class Constants(unittest.TestCase):
    def test_the_gate_sits_between_the_two_measured_groups(self):
        """⚠️ ဆူညံသံ အများဆုံး −၁၈.၈ · စကား အနည်းဆုံး −၈.၈ ⇒ ကြားထဲ ထားရမည်"""
        import measure as M
        self.assertGreater(M.HEAD_NEAR_DB, 8.8, "စကားကို ပယ်မည်")
        self.assertLess(M.HEAD_NEAR_DB, 18.8, "ဆူညံသံကို လက်ခံမည်")

    def test_the_run_floor_sits_between_them_too(self):
        """ဆူညံသံ ကြာ ≤၀.၁၂s · တကယ့် စကား ≥၀.၃၄s"""
        import measure as M
        self.assertGreater(M.HEAD_RUN_MIN, 0.12)
        self.assertLess(M.HEAD_RUN_MIN, 0.34)

    def test_the_lead_leaves_a_breath(self):
        """⚠️ စကားစချိန် အတိအကျမှာ စလျှင် ပထမ ဗျည်း ပြတ်တတ်သည်"""
        import cut as C
        self.assertGreater(C.HEAD_LEAD, 0.0)
        self.assertLessEqual(C.HEAD_LEAD, 0.30)


class Detect(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp(prefix="ikki_head_")

    def _t0(self, parts):
        import measure as M
        p = _wav(os.path.join(self.d, "a%d.wav" % len(parts)), parts)
        return M.speech(p)[3].get("speech_t0")

    def test_a_click_before_the_first_word_is_not_the_start(self):
        """⚠️⚠️ **အဓိက** — Zin ဖြစ်ခဲ့တဲ့ ပုံစံ အတိအကျ"""
        t0 = self._t0([(0.4, "sil"), (0.1, "click"), (0.9, "sil"), (2.0, "talk"),
                       (0.6, "sil"), (2.0, "talk")])
        self.assertIsNotNone(t0)
        self.assertGreater(t0, 1.0, "လက်ထိသံကို စကား ဟု ယူမိသည်")

    def test_speech_from_the_very_beginning_is_kept(self):
        """⚠️ ဖိုင်က အစကတည်းက ကောင်းလျှင် **ဘာမှ မဖြတ်ရ**"""
        t0 = self._t0([(2.0, "talk"), (0.6, "sil"), (2.0, "talk")])
        self.assertIsNotNone(t0)
        self.assertLess(t0, 0.30)


class Plan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp(prefix="ikki_headp_")
        cls.lead = _wav(os.path.join(cls.d, "lead.wav"),
                        [(0.4, "sil"), (0.1, "click"), (1.4, "sil"),
                         (2.2, "talk"), (0.9, "sil"), (2.2, "talk"),
                         (0.9, "sil"), (2.2, "talk")])
        cls.clean = _wav(os.path.join(cls.d, "clean.wav"),
                         [(2.2, "talk"), (0.9, "sil"), (2.2, "talk"),
                          (0.9, "sil"), (2.2, "talk")])

    def _plan(self, p):
        import cut as C
        return C.plan(p, keep_pause=0.30, min_sil=0.55)

    def test_the_output_starts_at_the_first_word(self):
        spans, cuts, st = self._plan(self.lead)
        self.assertGreater(st.get("head_trim", 0), 0.5, st.get("head_trim"))
        self.assertAlmostEqual(spans[0][0], st["head_trim"], places=3)

    def test_the_head_removal_is_listed_as_a_cut(self):
        """⚠️ စာရင်းထဲ မပါလျှင် ဖယ်လိုက်တာ ဘယ်လောက်လဲ သုံးစွဲသူ မသိ"""
        spans, cuts, st = self._plan(self.lead)
        h = [c for c in cuts if c.get("kind") == "head"]
        self.assertEqual(len(h), 1)
        self.assertEqual(h[0]["at"], 0.0)
        self.assertAlmostEqual(h[0]["to"], st["head_trim"], places=3)

    def test_a_clean_start_is_left_alone(self):
        """⚠️⚠️ မလိုဘဲ ဖြတ်လျှင် **ပထမ စကားလုံး ပျောက်**မည် — အဆိုးဆုံး အမှား"""
        spans, cuts, st = self._plan(self.clean)
        self.assertEqual(st.get("head_trim", 0), 0.0)
        self.assertEqual(spans[0][0], 0.0)
        self.assertEqual([c for c in cuts if c.get("kind") == "head"], [])

    def test_no_span_starts_before_the_head(self):
        spans, cuts, st = self._plan(self.lead)
        for a, b in spans:
            self.assertGreaterEqual(a, st["head_trim"] - 1e-6)

    def test_the_spans_stay_in_order_and_do_not_overlap(self):
        """⚠️ ခေါင်းဖြတ်ချက်က `pos` ကို ရွှေ့သည် — loop ပျက်လွယ်သည်"""
        for p in (self.lead, self.clean):
            spans, _, _ = self._plan(p)
            for i, (a, b) in enumerate(spans):
                self.assertLess(a, b, (p, i))
                if i: self.assertGreaterEqual(a, spans[i - 1][1] - 1e-6)

    def test_removed_counts_the_head(self):
        """⚠️ ခေါင်းကို မရေလျှင် ခန့်မှန်းချက် (Script Editor) က မှားမည်"""
        spans, cuts, st = self._plan(self.lead)
        self.assertAlmostEqual(st["removed"], sum(c["removed"] for c in cuts),
                               places=2)

    def test_the_stats_say_where_speech_began(self):
        spans, cuts, st = self._plan(self.lead)
        self.assertIn("speech_t0", st)
        self.assertGreater(st["speech_t0"], st["head_trim"])


_ZIN = "/Users/zinthuaung/Downloads/pYoIvgBmehsqlgS5zK0TDA.mp4"


@unittest.skipUnless(os.path.isfile(_ZIN), "Zin ရဲ့ မူရင်းဖိုင် မရှိ")
class Real(unittest.TestCase):
    """⚠️ တကယ့် ဖိုင် — ASR နဲ့ acoustic နှစ်ခု သဘောတူရမည်"""

    def test_the_measured_head_matches_the_first_sentence(self):
        import measure as M, cut as C
        me = M.speech(_ZIN)
        self.assertAlmostEqual(me[3]["speech_t0"], 22.52, delta=0.10)
        spans, cuts, st = C.plan(_ZIN, keep_pause=0.30, min_sil=0.55, meas=me)
        self.assertAlmostEqual(st["head_trim"], 22.40, delta=0.15)

    def test_nothing_louder_than_a_click_is_inside_the_head(self):
        """⚠️⚠️ ဖယ်လိုက်တဲ့ ခေါင်းထဲမှာ တကယ့် စကား **မပါရ**"""
        import numpy as np
        import measure as M, cut as C
        db, voice, dur = M.analyse(_ZIN)
        me = M.speech(_ZIN); sp = me[0]
        spans, cuts, st = C.plan(_ZIN, keep_pause=0.30, min_sil=0.55, meas=me)
        head = st["head_trim"]
        pk = [float(db[int(a / M.FRAME):max(int(a / M.FRAME) + 1,
                                            int(b / M.FRAME))].max()) for a, b in sp]
        p95 = float(np.percentile(pk, 95))
        inside = [p for (a, b), p in zip(sp, pk) if b <= head]
        self.assertTrue(inside, "ခေါင်းထဲ ဘာမှ မရှိ — စမ်းချက် အဓိပ္ပာယ် မရှိ")
        self.assertLess(max(inside), p95 - M.HEAD_NEAR_DB,
                        "တကယ့် စကားကို ဖယ်မိနေသည်")


if __name__ == "__main__":
    unittest.main(verbosity=2)
