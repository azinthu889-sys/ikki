# -*- coding: utf-8 -*-
"""Word-timed caption cards (short-916).

2026-09-26, Zin: captions split words apart and did not match the speech.
`cards()` splits a segment by character share and, for long unspaced runs,
at cluster boundaries -- so it guesses both where to cut and when.
`word_cards()` must only cut between ASR words and start each card on its
first word's onset.
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import captions as CP    # noqa: E402

MW = lambda t, size, font=None: len(t) * size * 0.5      # simple width model


class WordCards(unittest.TestCase):

    def seg(self):
        words = [("ဂျပန်မှာ", 0.00, 0.50), ("ကျောင်းတက်ပြီး", 0.55, 1.30),
                 ("အလုပ်", 1.70, 2.00), ("တန်းဝင်", 2.02, 2.60),
                 ("ရပါတယ်", 2.62, 3.10)]
        return dict(text="ဂျပန်မှာ ကျောင်းတက်ပြီး အလုပ်တန်းဝင် ရပါတယ်",
                    start=0.0, end=3.2, words=words)

    def test_cuts_only_between_words(self):
        c = self.seg()
        out = CP.word_cards(c, 40, 400, MW, None, hold=1.6)
        joined = [w for w, _s, _e in c["words"]]
        for lines, _a, _b, _sz in out:
            txt = lines[0].replace(" ", "")
            # every card is a run of whole words
            self.assertTrue(any("".join(joined[i:j]) == txt
                                for i in range(len(joined))
                                for j in range(i + 1, len(joined) + 1)), txt)

    def test_starts_on_word_onsets(self):
        c = self.seg()
        onsets = {s for _w, s, _e in c["words"]}
        for _l, a, _b, _sz in CP.word_cards(c, 40, 400, MW, None, hold=1.6):
            self.assertIn(a, onsets)

    def test_pause_starts_new_card(self):
        c = self.seg()
        starts = [a for _l, a, _b, _sz in CP.word_cards(c, 40, 2000, MW, None, hold=9)]
        self.assertIn(1.70, starts, "0.40 s pause before အလုပ် must open a card")

    def test_keeps_transcript_spacing(self):
        c = self.seg()
        texts = [l[0] for l, _a, _b, _sz in CP.word_cards(c, 40, 2000, MW, None, hold=9)]
        self.assertIn("အလုပ်တန်းဝင် ရပါတယ်", texts)

    def test_card_does_not_hold_through_a_pause(self):
        c = dict(text="တစ်ခုတည်းအတွက် ဂျပန်မှာ", start=0.0, end=6.0,
                 words=[("တစ်ခုတည်းအတွက်", 0.0, 0.9), ("ဂျပန်မှာ", 5.5, 6.0)])
        out = CP.word_cards(c, 40, 2000, MW, None, hold=9)
        self.assertLessEqual(out[0][2], 0.9 + 0.46, "card held through the 4.6 s pause")

    def test_no_words_falls_back(self):
        self.assertIsNone(CP.word_cards(dict(text="x", start=0, end=1), 40, 400, MW, None))


if __name__ == "__main__":
    unittest.main()
