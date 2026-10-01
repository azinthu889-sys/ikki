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



class Settle(unittest.TestCase):
    """off-time after the voice (Zin 2026-09-27: speech-edge off was "too fast")"""

    def cards(self):
        return [dict(lines=["က"], a=1.0, b=1.8, sz=40), dict(lines=["ခ"], a=2.1, b=2.4, sz=40),
                dict(lines=["ဂ"], a=4.0, b=5.0, sz=40)]

    def test_trail_never_past_next_card(self):
        out = CP.settle(self.cards(), trail=0.5)
        self.assertAlmostEqual(out[0]["b"], 2.1)          # 1.8 + 0.5 capped at the next on
        self.assertAlmostEqual(out[1]["b"], 2.9)
        self.assertAlmostEqual(out[2]["b"], 5.5)

    def test_bridge_holds_small_gaps_only(self):
        out = CP.settle(self.cards(), bridge=0.5)
        self.assertAlmostEqual(out[0]["b"], 2.1)          # gap 0.3 < 0.5 -> held
        self.assertAlmostEqual(out[1]["b"], 2.4)          # gap 1.6 -> blank

    def test_bridge_all(self):
        out = CP.settle(self.cards(), bridge=99, trail=0.5)
        self.assertEqual([round(c["b"], 2) for c in out], [2.1, 4.0, 5.5])

    def test_min_dur_rolls_up_and_never_shows_a_word_early(self):
        cs = [dict(lines=["က"], a=1.0, b=1.3, sz=40), dict(lines=["ခ"], a=1.3, b=1.6, sz=40),
              dict(lines=["ဂ"], a=1.6, b=2.6, sz=40)]
        out = CP.settle(cs, min_dur=0.9)
        # every on-time is still a card's own on-time (G1 / G13: nothing early)
        self.assertEqual([c["a"] for c in out], [1.0, 1.3, 1.6])
        self.assertEqual(out[1]["lines"], ["က", "ခ"])        # "က" stays up as the top line
        self.assertEqual(out[2]["lines"], ["ခ", "ဂ"])
        self.assertTrue(all(len(c["lines"]) <= 2 for c in out))

    def test_roll_up_needs_touching_cards(self):
        cs = [dict(lines=["က"], a=1.0, b=1.3, sz=40), dict(lines=["ခ"], a=2.0, b=2.4, sz=40)]
        self.assertEqual([c["lines"] for c in CP.settle(cs, min_dur=0.9)], [["က"], ["ခ"]])

    def test_defaults_unchanged(self):
        self.assertEqual([(c["a"], c["b"]) for c in CP.settle(self.cards())],
                         [(1.0, 1.8), (2.1, 2.4), (4.0, 5.0)])

    def test_split_card_is_never_broken_by_roll_up(self):
        cs = [dict(lines=["က", "ခ"], a=1.0, b=1.3, sz=40, split=True), dict(lines=["ဂ"], a=1.3, b=2.4, sz=40)]
        out = CP.settle(cs, min_dur=0.9)
        self.assertEqual([c["lines"] for c in out], [["က", "ခ"], ["ဂ"]])

    def test_split_join_respects_width(self):
        ws = [(f"w{i}", 0.1 + i * 0.35, 0.1 + i * 0.35 + 0.3) for i in range(8)]
        c = cap(" ".join(w[0] for w in ws), ws)
        wide = lambda t, size, font=None: 300 * (t.count(" ") + 1)     # > 2 words overflow 778
        out = CP.speech_cards([c], [(0.1, 3.0)], np.zeros(200), 40, 778, wide, None, min_piece=0.9)
        self.assertTrue(all(wide(x["lines"][0], 40) <= 778 for x in out), [x["lines"][0] for x in out])



class Syllables(unittest.TestCase):

    def test_roundtrip_and_known_breaks(self):
        for t in ["တစ်နှစ်", "ကျောင်းတက်", "သက္ခာလာနိုဘာဘာ", "comment မှာ Tokutei", "အခမဲ့တိုင်ပင်ဆွေးနွေးပေးသွားပါမယ်နော်"]:
            self.assertEqual("".join(CP.syllables(t)), t)
        self.assertEqual(CP.syllables("တစ်နှစ်"), ["တစ်", "နှစ်"])
        self.assertEqual(CP.syllables("ကျောင်း"), ["ကျောင်း"])
        self.assertIn("သက္ခာ", CP.syllables("သက္ခာလာ"))                # virama stack kept whole
        self.assertEqual(CP.syllables("ကိုယ့်ခြေ"), ["ကိုယ့်", "ခြေ"])   # dot-below before the asat

    def test_split_two_balances_and_fits(self):
        MW = lambda t, size, font=None: len(t) * 20
        two = CP.split_two("အခမဲ့တိုင်ပင်ဆွေးနွေးပေးသွားပါမယ်နော်", MW, 40, None, 500)
        self.assertEqual(len(two), 2)
        self.assertEqual("".join(two), "အခမဲ့တိုင်ပင်ဆွေးနွေးပေးသွားပါမယ်နော်")
        self.assertTrue(all(MW(l, 40) <= 500 for l in two))


class OverflowSplit(unittest.TestCase):
    """2026-10-02 j_71ca78a46acc: a one-token Burmese phrase too wide even at the
    0.6x floor ran off both frame edges. It must become several cards that fit,
    with the text unchanged when joined."""
    def test_too_wide_phrase_splits_and_fits(self):
        txt = "ရှည်စိတ်ကျေနပ်မှုအပြည့်ရှိနိုင်မယ့်နည်းလမ်း"
        c = CP.speech_cards([cap(txt, [(txt, 1.0, 3.0)])], [(1.0, 3.0)], np.zeros(400),
                            40, 300, MW, None, max_lines=1)
        self.assertGreater(len(c), 1)
        self.assertEqual("".join(x["lines"][0] for x in c), txt)
        for x in c:
            self.assertLessEqual(MW(x["lines"][0], x["sz"]), 300 + 1e-6, x)
        self.assertAlmostEqual(c[0]["a"], 1.0, places=2)
        for p_, q in zip(c, c[1:]): self.assertLessEqual(p_["b"], q["a"] + 1e-6)


if __name__ == "__main__":
    unittest.main()
