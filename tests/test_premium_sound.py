# -*- coding: utf-8 -*-
"""Premium headtop sound (Zin ၂၀၂၆-၁၀-၀၆ 「SFX ၄/၁၀ ⇒ ၁၀/၁၀ · music ထည့်」)

  · SFX policy — cap ၁၈/min · floor ၈/min (ယခင် floor = cap ⇒ အတိအကျ မီမှ အောင်)
  · recipe — music lock · accent SFX · role gain · camera push-in ပါးပါး
"""
import os
import sys
import unittest

R = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(R, "core"))
import recipes as RC  # noqa: E402
import sfxpol as SP   # noqa: E402
import camove as CM   # noqa: E402


class PremiumSound(unittest.TestCase):
    def test_policy_floor_below_cap(self):
        q = SP.clamp({"per_min": 1.5}, style="headtop")
        self.assertGreater(q["per_min"], q["floor"])
        self.assertEqual(q["floor"], 8.0)
        self.assertLessEqual(q["gap"], 1.0)

    def test_other_styles_unchanged(self):
        self.assertNotIn("floor", SP.clamp({"per_min": 1.5}, style="short-916"))

    def test_recipe_sound(self):
        r = RC.get("headtop")
        self.assertTrue(r.get("music"))
        self.assertTrue(r.get("music_lock"))
        self.assertTrue(-40 <= r["music_lufs"] <= -20)
        self.assertTrue(r.get("sfx_accents"))
        self.assertGreater(r["sfx_role_gain"]["latch"], 0)

    def test_camera_moves_with_soft_gfx(self):
        # ဘေးကတ် window မထည့် ⇒ move ရရမည် (ယခင် ၀ ခု)
        caps = [{"start": t} for t in (0.5, 6.0, 12.0, 18.5, 25.0, 31.0, 38.0, 45.0, 52.0)]
        mv = CM.plan(60.0, caps, [], gap=4.5, z_in=1.08, budget=0.30)
        self.assertGreaterEqual(len([m for m in mv if m[3] > m[2]]), 3)
        self.assertTrue(all(max(m[2], m[3]) <= 1.081 for m in mv))


if __name__ == "__main__":
    unittest.main()
