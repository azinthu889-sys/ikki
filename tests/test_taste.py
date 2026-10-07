# -*- coding: utf-8 -*-
"""User taste memory (Zin ၂၀၂၆-၁၀-၀၇ 「ခဏခဏ ပြင်တာ မှတ်ပြီး နောက်ဗီဒီယိုမှာ လိုက်လုပ်」)"""
import os
import sys
import unittest

R = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(R, "core"))
import taste as T     # noqa: E402
import recipes as RC  # noqa: E402


class Taste(unittest.TestCase):
    def test_single_edit_not_learned(self):
        s = T.observe({}, "j1", look={"sfx_per_min": 0.5}, removed=["beat.timeline"])
        d = T.aggregate(s)
        self.assertEqual(T.look_defaults(d), {})
        self.assertEqual(T.avoid_types(d), [])

    def test_repeated_edits_learned(self):
        s = {}
        for i, v in enumerate((0.6, 0.4, 0.5)):
            s = T.observe(s, f"j{i}", look={"sfx_per_min": v, "cam_moves": False, "music": None},
                          removed=["beat.timeline", "modern.mt_counter"])
        d = T.aggregate(s)
        lk = T.look_defaults(d, RC.clean)
        self.assertAlmostEqual(lk["sfx_per_min"], 0.5, places=2)     # EMA 0.6→0.5→0.5 (နောက်ဆုံးကို ပိုအလေး)
        self.assertIs(lk["cam_moves"], False)
        self.assertIsNone(lk["music"])
        self.assertEqual(T.avoid_types(d), ["timeline"])               # beat.* သာ director ဆီ

    def test_rerender_same_job_counts_once(self):
        s = T.observe({}, "j1", look={"gfx": 4})
        s = T.observe(s, "j1", look={"gfx": 4})
        self.assertEqual(T.look_defaults(T.aggregate(s)), {})

    def test_swap_likes_new(self):
        s = {}
        for i in range(2):
            s = T.observe(s, f"j{i}", swaps=[("beat.stat", "beat.ring")])
        d = T.aggregate(s)
        self.assertEqual(T.avoid_types(d), ["stat"])
        self.assertNotIn("ring", T.avoid_types(d))

    def test_apply_never_overrides_job(self):
        s = {}
        for i in range(2):
            s = T.observe(s, f"j{i}", look={"gfx": 3}, removed=["beat.vs"])
        over, applied = T.apply(T.aggregate(s), {"gfx": 9}, RC.clean)
        self.assertEqual(over["gfx"], 9)
        self.assertEqual(over["_avoid_types"], ["vs"])
        self.assertIn("_avoid_types", over["_taste"])

    def test_bounds_clamped(self):
        s = {}
        for i in range(2):
            s = T.observe(s, f"j{i}", look={"gfx": 999})
        lk = T.look_defaults(T.aggregate(s), RC.clean)
        self.assertLessEqual(lk.get("gfx", 0), RC.BOUNDS["gfx"][2])

    def test_summary_burmese(self):
        s = {}
        for i in range(2):
            s = T.observe(s, f"j{i}", look={"cam_moves": False}, removed=["beat.timeline"])
        out = T.summary(T.aggregate(s), {"timeline": "Timeline"})
        self.assertIn("ကင်မရာ ပိတ်", out)
        self.assertIn("「Timeline」 မသုံး", out)

    def test_keep_last_jobs(self):
        s = {}
        for i in range(T.KEEP_JOBS + 5):
            s = T.observe(s, f"j{i}", look={"gfx": 2})
        self.assertEqual(len(s["by_job"]), T.KEEP_JOBS)


if __name__ == "__main__":
    unittest.main()
