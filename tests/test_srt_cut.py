# -*- coding: utf-8 -*-
"""⬇ SRT ကို **ဖြတ်ပြီးသား ဗီဒီယိုရဲ့ အချိန်** နဲ့ ထုတ်ရမည်

audit ၂၀၂၆-၁၀-၀၄: `segs` (မူရင်း အချိန်) ကို တိုက်ရိုက် ရေးခဲ့ရာ
  headtop 1:07.5 ဗီဒီယိုမှာ နောက်ဆုံး cue 2:49.9 · ref-slides +15.6s လွဲပြီး
  cue ၅/၂၂ က ဗီဒီယို ပြီးမှ စ。 SRT ဒေါင်းပြီး သုံးသူတိုင်း စာတန်း လွဲသည်。
live job ၃ ခုမှာ ပြင်ပြီး: 169.9→63.8 · 77.2→69.0 · 78.0→62.5 (ဗီဒီယို 67.5/70.0/62.5)。
"""
import os
import sys
import tempfile
import unittest

_T = tempfile.mkdtemp(prefix="ikki_srt_")
os.environ["IKKI_DATA"] = _T
os.environ["IKKI_DB"] = os.path.join(_T, "t.db")
_R = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(_R, "api"))
sys.path.insert(0, os.path.join(_R, "core"))
import main as M  # noqa: E402

CM = {"spans": [[0.0, 10.0], [20.0, 30.0]], "total": 20.0}


def seg(a, b, t="x"):
    return {"start": a, "end": b, "text": t}


class SrtRows(unittest.TestCase):
    def test_shifted_after_cut(self):
        # 22–25 (မူရင်း) ⇒ 12–15 (ထွက်) — ရှေ့က 10–20 ကို ဖြုတ်ထား
        self.assertEqual(M.srt_rows([seg(22, 25)], CM), [(12.0, 15.0, "x")])

    def test_deleted_cue_dropped(self):
        self.assertEqual(M.srt_rows([seg(12, 18)], CM), [])

    def test_cue_across_cut_joins(self):
        # 8–23 ⇒ 8–10 + 20–23 ⇒ ထွက်မှာ 8–13 ဆက်တိုက်
        self.assertEqual(M.srt_rows([seg(8, 23)], CM), [(8.0, 13.0, "x")])

    def test_never_past_the_end(self):
        rows = M.srt_rows([seg(28, 35)], CM)
        self.assertTrue(rows and rows[0][1] <= 20.0, rows)

    def test_no_map_keeps_source(self):
        self.assertEqual(M.srt_rows([seg(1, 2)], None), [(1.0, 2.0, "x")])


if __name__ == "__main__":
    unittest.main()
