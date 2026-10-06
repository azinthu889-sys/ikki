# -*- coding: utf-8 -*-
"""MMS forced-alignment merge (core/asr.py mms_refine) — Zin ၂၀၂၆-၁၀-၀၆ B
fake aligner ⇒ score နိမ့် / ဘောင်ကျော် / အစဉ်ပြောင်း ⇒ Gemini ထား · romanize မရ (၅) ⇒ ကျော်ရုံ"""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import asr as A  # noqa: E402

FAKE = r'''
import json, sys
out = {"0": [{"w": "က", "s": 1.10, "e": 1.30, "score": 0.9},
             {"w": "ခ", "s": 1.60, "e": 1.80, "score": 0.2},
             {"w": "ဂ", "s": 2.00, "e": 2.30, "score": 0.8},
             {"w": "ဃ", "s": 9.00, "e": 9.40, "score": 0.9}]}
json.dump(out, open(sys.argv[3], "w"))
'''


class Merge(unittest.TestCase):
    def test_merge(self):
        td = tempfile.mkdtemp()
        fk = os.path.join(td, "fake.py"); open(fk, "w").write(FAKE)
        old = A.MMS_PY, A.MMS_TOOL
        A.MMS_PY, A.MMS_TOOL = sys.executable, fk
        try:
            segs = [dict(start=1.0, end=3.0, text="က ၅ ခ ဂ ဃ",
                         words=[dict(w="က", s=1.0, e=1.2), dict(w="၅", s=1.3, e=1.4),
                                dict(w="ခ", s=1.5, e=1.6), dict(w="ဂ", s=1.8, e=2.0),
                                dict(w="ဃ", s=2.4, e=2.8)])]
            A.mms_refine(segs, "x.wav", log=lambda *a: None)
            w = segs[0]["words"]
            self.assertEqual(w[0]["s"], 1.10)          # replaced
            self.assertEqual(w[1]["s"], 1.3)           # ၅ — not aligned, kept, no break
            self.assertEqual(w[2]["s"], 1.5)           # low score ⇒ kept
            self.assertEqual(w[3]["s"], 2.00)          # replaced after a skipped word
            self.assertEqual(w[4]["s"], 2.4)           # outside sentence ±0.4 ⇒ kept
        finally:
            A.MMS_PY, A.MMS_TOOL = old

    def test_disabled(self):
        os.environ["IKKI_MMS"] = "0"
        try:
            segs = [dict(start=0, end=1, words=[dict(w="က", s=0.1, e=0.2)])]
            self.assertIs(A.mms_refine(segs, "x.wav", log=lambda *a: None), segs)
            self.assertEqual(segs[0]["words"][0]["s"], 0.1)
        finally:
            os.environ.pop("IKKI_MMS", None)


if __name__ == "__main__":
    unittest.main()
