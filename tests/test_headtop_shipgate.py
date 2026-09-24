# -*- coding: utf-8 -*-
"""Talking Head Motion Edit — poor motion ကို final အဖြစ်မပို့ရန် regression tests."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import dress as DR  # noqa: E402
import motmeas as MM  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "worker"))
import run as W  # noqa: E402


class HeadtopShipGate(unittest.TestCase):
    def test_measured_pack_timing_passes(self):
        # 2026-09-22 pack harness: 30fps, enter 0.233 / exit 0.133 / ease .318.
        checks = MM.premium_checks(dict(n=1, in_s=.233, out_s=.133, ease=.318))
        self.assertTrue(all(c["ok"] for c in checks), checks)

    def test_old_pop_exit_cannot_ship(self):
        # j_1f9561de04b3 era output: no motion measurement; later v2 report
        # showed exit=.100 and ease=.15. Audio QC တစ်ခုတည်းနဲ့ PASS မဖြစ်ရ။
        checks = MM.premium_checks(dict(n=1, in_s=.617, out_s=.100, ease=.150))
        failed = {c["key"] for c in checks if not c["ok"]}
        self.assertEqual(failed, {"motion_exit", "motion_ease"})

    def test_pack_curve_is_ease_out(self):
        vals = [DR._pack_ease(i / 240.0, "cubic-bezier(.22,.8,.24,1)")
                for i in range(241)]
        area = 2.0 * sum(v - i / 240.0 for i, v in enumerate(vals)) / len(vals)
        self.assertGreater(area, .55, area)

    def test_pack_renderer_uses_native_source_fps_and_legacy_sequence(self):
        with open(os.path.join(ROOT, "core", "dress.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn("src_fps=fps", src)
        self.assertIn("[pin][phold][pout]concat=n=3:v=1:a=0[pfull]", src)
        self.assertIn("not _is_pack", src)

    def test_silent_sfx_plan_cannot_ship(self):
        checks = W._premium_sfx_checks(
            [(0.0, "whoosh_in", -15), (0.18, "latch", -17)],
            mixed=0, audible=0, silent=0,
            policy={"per_min": 6.0, "layer": .60}, dur=16.0)
        failed = {c["key"] for c in checks if not c["ok"]}
        self.assertEqual(failed, {"headtop_sfx_mix", "headtop_sfx_audible"})

    def test_no_sfx_moments_cannot_ship(self):
        checks = W._premium_sfx_checks([], mixed=0, audible=None, silent=None,
                                       policy={"per_min": 6.0, "layer": .60}, dur=69.0)
        failed = {c["key"] for c in checks if not c["ok"]}
        self.assertEqual(failed, {"headtop_sfx_moments", "headtop_sfx_mix",
                                  "headtop_sfx_audible"})

    def test_measured_sfx_moments_and_stem_pass(self):
        cues = [(i * 10.0, "whoosh_in", -15) for i in range(6)]
        checks = W._premium_sfx_checks(cues, mixed=6, audible=6, silent=0,
                                       policy={"per_min": 6.0, "layer": .60},
                                       dur=69.0)
        self.assertTrue(all(c["ok"] for c in checks), checks)


if __name__ == "__main__":
    unittest.main(verbosity=2)
