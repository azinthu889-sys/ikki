# -*- coding: utf-8 -*-
"""Word-pop captions (short-916 · reference r1/r3, Zin 2026-09-28)."""
import os, sys, unittest
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import captions as CP    # noqa: E402
MW = lambda t, size, font=None: len(t) * size * 0.5


def cap(ws):
    return dict(text=" ".join(w[0] for w in ws), start=ws[0][1], end=ws[-1][2], words=ws)


class WordPop(unittest.TestCase):

    def setUp(self):
        self.ws = [("ဂျပန်မှာ", 1.05, 1.5), ("Tokutei", 1.52, 2.0), ("ဗီဇာနဲ့", 2.02, 2.5), ("အလုပ်", 3.2, 3.6)]
        self.runs = [(1.00, 2.60), (3.10, 3.70)]
        self.db = np.zeros(300); self.db[int(1.56 / 0.02)] = -40      # a syllable dip near 1.56 s

    def cards(self):
        return CP.word_pop_cards([cap(self.ws)], self.runs, self.db, 40, 2000, MW, None)

    def test_one_word_per_card_text_whole(self):
        c = self.cards()
        self.assertEqual([x["lines"][0] for x in c], [w[0] for w in self.ws])

    def test_first_word_on_at_run_start_and_snapped_onset(self):
        c = self.cards()
        self.assertEqual(c[0]["a"], 1.00)
        self.assertAlmostEqual(c[1]["a"], 1.56, places=2)             # snapped to the dip (Gemini said 1.52)
        self.assertEqual(c[3]["a"], 3.10)

    def test_contiguous_inside_run_and_ends_at_run_end(self):
        c = self.cards()
        self.assertAlmostEqual(c[0]["b"], c[1]["a"]); self.assertAlmostEqual(c[1]["b"], c[2]["a"])
        self.assertEqual(c[2]["b"], 2.60); self.assertEqual(c[3]["b"], 3.70)

    def test_never_spans_a_silence_and_min_card(self):
        for x in self.cards():
            self.assertTrue(any(a - 1e-6 <= x["a"] and x["b"] <= b + 1e-6 for a, b in self.runs))
            self.assertGreaterEqual(x["b"] - x["a"], 0.15 - 1e-6)


class ChunkWord(unittest.TestCase):
    """ASR "words" that are whole phrases -> chunks at Burmese word boundaries"""

    def test_roundtrip_fits_and_never_inside_a_syllable(self):
        W = lambda t, size, font=None: len(t) * size * 0.35
        for t in ["အသေးစိတ်ဆွေးနွေးချင်တယ်ဆိုရင်တော့", "အခမဲ့တိုင်ပင်ဆွေးနွေးပေးသွားပါမယ်နော်",
                  "ကိုယ့်ရဲ့အခြေအနေနဲ့ကိုက်မကိုက်"]:
            ch = CP.chunk_word(t, 80, 400, W, None)
            self.assertEqual("".join(c for c, _ in ch), t)
            sy = CP.syllables(t); bounds = set(); pos = 0
            for p in sy: pos += len(p); bounds.add(pos)
            pos = 0
            for c, _ in ch[:-1]:
                pos += len(c); self.assertIn(pos, bounds)       # break only at a syllable boundary

    def test_short_word_is_one_chunk(self):
        self.assertEqual(len(CP.chunk_word("ဂျပန်", 80, 778, MW, None)), 1)


if __name__ == "__main__":
    unittest.main()
