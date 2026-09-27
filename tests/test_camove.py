# -*- coding: utf-8 -*-
"""Designed camera moves (short-916 · reference r3 · Zin 2026-09-27:
"now and then", never "staying zoomed")."""
import os, sys, unittest
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import camove as CM    # noqa: E402

CAPS = [dict(start=t, end=t + 2) for t in (0.2, 3.0, 7.1, 12.4, 18.0, 25.3, 31.0, 38.2, 44.0, 52.5, 61.0, 70.2)]
DUR = 77.6


def zseq(m, fps=30):
    t = np.arange(0, DUR, 1 / fps)
    return t, np.array([CM.zoom_at(x, m) for x in t])


class Plan(unittest.TestCase):

    def test_G10_every_move_returns_to_1(self):
        m = CM.plan(DUR, CAPS, [])
        self.assertTrue(m)
        for a, b in zip(m[0::2], m[1::2]):
            self.assertEqual((a[2], b[3]), (1.0, 1.0))                # in from 1.00, back to 1.00
            self.assertAlmostEqual(CM.zoom_at(b[0] + b[1] + 0.01, m), 1.0, delta=0.005)

    def test_G11_G12_short_and_rare(self):
        t, z = zseq(CM.plan(DUR, CAPS, []))
        hi = z > 1.02
        run = best = 0
        for h in hi:
            run = run + 1 if h else 0; best = max(best, run)
        self.assertLessEqual(best / 30, 3.0)
        self.assertLessEqual(hi.mean(), 0.20)

    def test_never_inside_broll_or_graphic(self):
        avoid = [(6.5, 9.0), (17.5, 21.0)]
        span = CM.IN_D + CM.HOLD + CM.OUT_D
        for t, d, z0, z1, _ in CM.plan(DUR, CAPS, avoid):
            if z1 > z0:
                for a, b in avoid:
                    self.assertTrue(t + span + 0.3 <= a or t - 0.3 >= b, (t, a, b))

    def test_opens_with_push_in(self):
        m = CM.plan(DUR, CAPS, [])
        self.assertEqual((m[0][0], m[0][4]), (0.0, "expo"))

    def test_cap(self):
        self.assertTrue(all(max(z0, z1) <= CM.ZMAX for _, _, z0, z1, _ in CM.plan(DUR, CAPS, [])))

    def test_ease_out_front_loaded(self):
        mv = [(1.0, 1.0, 1.0, 1.2, "cubic")]
        self.assertAlmostEqual((CM.zoom_at(1.5, mv) - 1.0) / 0.2, 0.875, places=3)

    def test_pivot_from_pose_maps_to_crop(self):
        fr = [dict(nf=1, fx=0.5, fy=0.35)] * 10
        self.assertAlmostEqual(CM.pivot_from_pose(fr)[0], 0.5, places=3)
        self.assertEqual(CM.pivot_from_pose([]), (0.5, 0.40))


if __name__ == "__main__":
    unittest.main()
