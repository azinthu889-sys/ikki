# -*- coding: utf-8 -*-
"""Script-assisted spelling (Zin 2026-09-28): suggestions only, never deletes speech."""
import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import scriptfix as SF    # noqa: E402


def seg(words, text=None):
    ws = [dict(w=w, s=i * 0.5, e=i * 0.5 + 0.45) for i, w in enumerate(words)]
    return dict(text=text or " ".join(words), start=0.0, end=len(words) * 0.5, words=ws)


class Suggest(unittest.TestCase):
    def test_misheard_name_gets_the_script_spelling(self):
        s = [seg(["ကျောင်းက", "သက္ခာလာနိုဘာဘာ", "အနီးနားမှာ", "ရှိပါတယ်။"])]
        L = SF.suggest(s, "ကျောင်းက Takadanobaba အနီးနားမှာ ရှိပါတယ်။")
        self.assertEqual(len(L), 1)
        self.assertIn("Takadanobaba", L[0]["new"])
        self.assertIn("Takadanobaba", L[0]["text"])
        self.assertTrue(L[0]["text"].endswith("။"))

    def test_space_kept_between_burmese_and_latin(self):
        s = [seg(["ဂျပန်မှာ", "တက်ပြီး", "တိုခုတဲ", "ပရိုဂရမ်", "နဲ့", "အလုပ်ဝင်တယ်"])]
        L = SF.suggest(s, "ဂျပန်မှာ တက်ပြီး Tokutei Program နဲ့ အလုပ်ဝင်တယ်")
        self.assertTrue(L)
        self.assertNotIn("ပြီးTokutei", "".join(x["new"] for x in L))

    def test_never_suggests_dropping_spoken_words(self):
        # the speaker said more than the script ("အောင်လက်မှတ်") -> no suggestion
        s = [seg(["အထက်တန်း", "အောင်ထားပြီး", "N5", "အောင်လက်မှတ်", "ရှိထား", "ရပါမယ်"])]
        L = SF.suggest(s, "အထက်တန်း အောင်ထားပြီး N5 ရှိထား ရပါမယ်")
        self.assertEqual(L, [])

    def test_mark_order_only_is_not_a_suggestion(self):
        s = [seg(["ရှိပေမယ့်", "ဒီရွေးချယ်မှု", "ကတော့"])]
        L = SF.suggest(s, "ရှိပေမယ့် ဒီရွေးချယ်မှု ကတော့")
        self.assertEqual(L, [])

    def test_no_script_no_suggestions(self):
        self.assertEqual(SF.suggest([seg(["က", "ခ"])], ""), [])


class AutoFix(unittest.TestCase):
    def test_script_applied_only_when_both_orders_pick_it(self):
        s = [seg(["ကျောင်းက", "သက္ခာလာနိုဘာဘာ", "အနီးနားမှာ", "ရှိပါတယ်"])]
        sc = "ကျောင်းက Takadanobaba အနီးနားမှာ ရှိပါတယ်"
        calls = []
        def fake(clip, prev, opts, nxt, model, endpoint):   # always answers "A"
            calls.append(opts); return "A"
        orig, SF._ask = SF._ask, fake
        orig_run = SF.subprocess.run
        SF.subprocess.run = lambda *a, **k: None               # no ffmpeg in tests
        try:
            out, rep = SF.fix([dict(x) for x in s], sc, "/dev/null", log=lambda m: None,
                              model="m", endpoint=lambda m: "")
        finally:
            SF._ask = orig; SF.subprocess.run = orig_run
        self.assertEqual(len(calls), 2)                        # asked in both orders
        self.assertEqual(rep["script"], 0)                     # "A" twice = contradiction
        self.assertNotIn("Takadanobaba", out[0]["text"])

    def test_user_edited_lines_are_left_alone(self):
        s = [dict(seg(["ကျောင်းက", "သက္ခာလာနိုဘာဘာ", "အနီးနားမှာ"]), fix="ကျောင်းက ...")]
        out, rep = SF.fix(s, "ကျောင်းက Takadanobaba အနီးနားမှာ", "/dev/null",
                          log=lambda m: None, model="m", endpoint=lambda m: "")
        self.assertEqual(rep["candidates"], 0)


if __name__ == "__main__":
    unittest.main()


class Retext(unittest.TestCase):
    """a user fix must reach the timed words (word-pop reads words, not text)"""

    def test_fix_text_lands_in_words_with_times_kept(self):
        ws = [dict(w="ကျောင်းက", s=1.0, e=1.4), dict(w="သက္ခာလာနိုဘာဘာ", s=1.4, e=2.2),
              dict(w="အနီးနားမှာ", s=2.2, e=2.8)]
        out = SF.retext(ws, "ကျောင်းက Takadanobaba အနီးနားမှာ")
        self.assertEqual([w["w"] for w in out], ["ကျောင်းက", "Takadanobaba", "အနီးနားမှာ"])
        self.assertEqual([(w["s"], w["e"]) for w in out], [(1.0, 1.4), (1.4, 2.2), (2.2, 2.8)])

    def test_list_shaped_words_stay_lists(self):
        out = SF.retext([["က", 0.0, 0.3], ["ခ", 0.3, 0.6]], "က ဂ")
        self.assertEqual(out, [["က", 0.0, 0.3], ["ဂ", 0.3, 0.6]])

    def test_a_word_emptied_by_the_fix_gives_its_time_away(self):
        ws = [dict(w="Tokutei", s=0.0, e=0.5), dict(w="program", s=0.5, e=1.0), dict(w="တွေနဲ့", s=1.0, e=1.4)]
        out = SF.retext(ws, "Tokutei programနဲ့")
        self.assertEqual(out[-1]["e"], 1.4)                  # no time lost at the end
        self.assertEqual("".join(w["w"] for w in out).replace(" ", ""), "Tokuteiprogramနဲ့")
