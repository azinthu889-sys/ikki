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
        return CP.word_pop_cards([cap(self.ws)], self.runs, self.db, 40, 2000, MW, None, min_read=0.0)

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


class Readable(unittest.TestCase):
    """cards shorter than min_read join the next word (Zin: "a little too fast")"""

    def test_short_cards_join_next_word_on_time_kept(self):
        ws = [("က", 1.00, 1.18), ("ခ", 1.20, 1.38), ("ဂ", 1.40, 2.20)]
        c = CP.word_pop_cards([cap(ws)], [(1.0, 2.2)], np.zeros(200), 40, 2000, MW, None)
        self.assertTrue(all(x["b"] - x["a"] >= 0.40 - 1e-6 for x in c))
        self.assertEqual(c[0]["a"], 1.0)                         # still on at the first word
        self.assertEqual(" ".join(x["lines"][0] for x in c), "က ခ ဂ")

    def test_never_joins_across_a_silence(self):
        ws = [("က", 1.00, 1.20), ("ခ", 2.00, 2.60)]
        c = CP.word_pop_cards([cap(ws)], [(1.0, 1.25), (2.0, 2.6)], np.zeros(200), 40, 2000, MW, None)
        self.assertEqual([x["lines"][0] for x in c], ["က", "ခ"])

    def test_join_may_shrink_to_the_floor_but_not_below(self):
        ws = [("ကက", 1.00, 1.18), ("ခခ", 1.20, 2.20)]            # joined: 5 chars -> 100 px at 40
        c = CP.word_pop_cards([cap(ws)], [(1.0, 2.2)], np.zeros(200), 40, 95, MW, None)
        self.assertEqual([(x["lines"][0], x["sz"]) for x in c], [("ကက ခခ", 38)])
        c = CP.word_pop_cards([cap(ws)], [(1.0, 2.2)], np.zeros(200), 40, 75, MW, None)
        self.assertEqual([x["lines"][0] for x in c], ["ကက", "ခခ"])   # would need 30 px < 36


class CardsPreEmpty(unittest.TestCase):
    """cards_pre ဗလာ ⇒ စာတန်း **မပျောက်ရ** (၂၀၂၆-၀၉-၂၈)

    ⚠️ `captions.track()` က `cards_pre is not None` နဲ့ စစ်ခဲ့ရာ **ဗလာ list**
       ဝင်သွားပြီး unit ၀ ⇒ **စာတန်း လုံးဝ မပါသော ဗီဒီယို** ထွက်ခဲ့သည်。
       approve က segment ကို text/start/end ချည်း ပြန်ဆောက်၍ စကားလုံးအချိန်
       ပျောက်ကာ `word_pop_cards()` က [] ပြန်ခြင်းကြောင့် ဖြစ်သည်。
    ⚠️ ထုတ်သူ ၂ နေရာ ပြင်ရုံနဲ့ **အမျိုးအစား ပွင့်နေဆဲ** — လက်ခံသူက []
       ကို လက်ခံနေသရွေ့ နောက် ခေါ်သူ အသစ်တိုင်း ထပ်ဖြစ်နိုင်သည် ⇒
       ဆုံးဖြတ်သည့် **တစ်နေရာတည်း**မှာ ဖြေထားသည်。
    ⚠️ ဤဖိုင်ရဲ့ အောက်ဆုံးမှာ `unittest.main()` ရှိသဖြင့် အဲဒီနောက် ရေးလျှင်
       **ဘယ်တော့မှ မပြေး** — ပထမ ရေးတုန်းက အဲလို ဖြစ်ခဲ့သည် (တိတ်တဆိတ်
       အောင်နေသော စစ်ချက်)。 ⇒ TestCase အဖြစ်သာ ရေးရမည်。
    """

    def test_empty_cards_pre_falls_back(self):
        import inspect
        src = inspect.getsource(CP.track)
        self.assertIn("cards_pre is not None and not cards_pre", src)
        self.assertIn("if cards_pre else", src)
        self.assertNotIn("if cards_pre is not None else", src)


if __name__ == "__main__":
    unittest.main()

