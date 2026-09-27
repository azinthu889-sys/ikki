# -*- coding: utf-8 -*-
"""Speech-run caption cards (short-916, Zin 2026-09-27: on as the voice starts,
off as it ends). Timing comes from the cut engine's speech runs; ASR words only
supply text, whole words only (R1)."""
import os, sys, unittest
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import captions as CP    # noqa: E402

MW = lambda t, size, font=None: len(t) * size * 0.5


def cap(text, words):
    return dict(text=text, start=words[0][1], end=words[-1][2], words=words)


class SpeechCards(unittest.TestCase):

    def test_on_off_are_run_edges(self):
        c = cap("ဂျပန်မှာ ကျောင်းတက်", [("ဂျပန်မှာ", 1.05, 1.60), ("ကျောင်းတက်", 1.62, 2.30)])
        out = CP.speech_cards([c], [(1.00, 2.40)], np.zeros(200), 40, 2000, MW, None)
        self.assertEqual(len(out), 1)
        self.assertEqual((out[0]["a"], out[0]["b"]), (1.00, 2.40))

    def test_no_caption_over_silence(self):
        c = cap("က ခ", [("က", 1.0, 1.5), ("ခ", 3.0, 3.6)])
        out = CP.speech_cards([c], [(1.0, 1.7), (3.0, 3.7)], np.zeros(300), 40, 2000, MW, None)
        self.assertEqual([(x["a"], x["b"]) for x in out], [(1.0, 1.7), (3.0, 3.7)])

    def test_short_run_merges_only_across_small_gap(self):
        c = cap("က ခ ဂ", [("က", 1.0, 1.3), ("ခ", 1.5, 2.8), ("ဂ", 4.0, 4.3)])
        runs = [(1.0, 1.3), (1.5, 2.8), (4.0, 4.3)]      # 0.3 s runs; gaps 0.2 / 1.2
        out = CP.speech_cards([c], runs, np.zeros(300), 40, 2000, MW, None)
        self.assertEqual([(x["a"], x["b"]) for x in out], [(1.0, 2.8), (4.0, 4.3)])

    def test_long_run_splits_between_words_at_energy_dip(self):
        ws = [(f"w{i}", 0.1 + i * 0.9, 0.1 + i * 0.9 + 0.8) for i in range(6)]
        c = cap(" ".join(w[0] for w in ws), ws)
        db = np.zeros(400); db[int(2.75 / 0.02)] = -60          # quiet frame between w2 and w3
        out = CP.speech_cards([c], [(0.1, 5.5)], db, 40, 2000, MW, None, max_dur=4.0)
        self.assertGreater(len(out), 1)
        self.assertAlmostEqual(out[0]["b"], out[1]["a"])        # no gap, no overlap
        for x in out:                                           # whole words only
            for t in x["lines"][0].split(" "):
                self.assertIn(t, [w[0] for w in ws])
        self.assertLessEqual(max(x["b"] - x["a"] for x in out), 4.0 + 0.3)

    def test_clumped_word_times_give_no_sliver_card(self):
        # the 17.14-20.30 run of 2026-09-27: two words stamped 17.43, cuts 40 ms apart
        ws = [("ဂျပန်မှာ", 17.43, 17.45), ("တစ်နှစ်အတွင်း", 17.43, 17.80),
              ("ဂျပန်စာရော", 17.80, 18.30), ("တစ်ခုတည်းအတွက်", 18.30, 19.10)]
        c = cap(" ".join(w[0] for w in ws), ws)
        wide = lambda t, size, font=None: 700 if " " not in t else 900   # any two words overflow
        out = CP.speech_cards([c], [(17.14, 20.30)], np.zeros(1100), 40, 778, wide, None)
        self.assertGreaterEqual(min(x["b"] - x["a"] for x in out), 0.30 - 1e-6)
        self.assertEqual(" ".join(x["lines"][0] for x in out), c["text"])   # nothing dropped
        self.assertEqual((out[0]["a"], out[-1]["b"]), (17.14, 20.30))
        for p, q in zip(out, out[1:]):
            self.assertAlmostEqual(p["b"], q["a"])

    def test_words_kept_verbatim_no_additions(self):
        c = cap("ဂျပန်မှာ ကျောင်းတက်", [("ဂျပန်မှာ", 1.05, 1.60), ("ကျောင်းတက်", 1.62, 2.30)])
        out = CP.speech_cards([c], [(1.0, 2.4)], np.zeros(200), 40, 2000, MW, None)
        self.assertLessEqual(len("".join(x["lines"][0] for x in out).encode()),
                             len(c["text"].encode()))

    def test_cut_runs_never_straddle_a_cut(self):
        runs = CP.cut_runs([(1.0, 3.0)], [(0.0, 2.0), (2.5, 5.0)])
        self.assertEqual(runs, [(1.0, 2.0), (2.0, 2.5)])


if __name__ == "__main__":
    unittest.main()
