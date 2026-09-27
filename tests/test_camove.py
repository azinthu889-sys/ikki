# -*- coding: utf-8 -*-
"""Designed camera moves (short-916 · reference r3, 2026-09-27)."""
import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import camove as CM    # noqa: E402

CAPS = [dict(start=t, end=t + 2) for t in (0.2, 3.0, 7.1, 12.4, 18.0, 25.3, 31.0, 38.2, 44.0, 52.5)]


class Plan(unittest.TestCase):

    def test_open_push_in_and_close_pull_out(self):
        m = CM.plan(60.0, CAPS, [])
        self.assertEqual((m[0][0], m[0][2], m[0][4]), (0.0, 1.0, "expo"))
        self.assertGreater(m[0][3], 1.0)
        self.assertEqual(m[-1][3], 1.0)                     # ends as framed
        self.assertLessEqual(m[-1][0] + m[-1][1], 60.0)

    def test_never_inside_broll_or_graphic(self):
        avoid = [(6.5, 9.0), (17.5, 21.0)]
        for t, d, *_ in CM.plan(60.0, CAPS, avoid):
            for a, b in avoid:
                self.assertTrue(t + d + 0.3 <= a or t - 0.3 >= b, (t, d, a, b))

    def test_spacing_and_cap(self):
        m = CM.plan(60.0, CAPS, [])
        for p, q in zip(m, m[1:]):
            self.assertGreaterEqual(q[0] - (p[0] + p[1]), 0.0)
        self.assertTrue(all(max(z0, z1) <= CM.ZMAX for _, _, z0, z1, _ in m))

    def test_levels_chain(self):
        m = CM.plan(60.0, CAPS, [])
        for p, q in zip(m, m[1:]):
            self.assertAlmostEqual(p[3], q[2])               # each move starts where the last ended

    def test_ease_out_front_loaded(self):
        mv = [(1.0, 1.0, 1.0, 1.2, "cubic")]
        half = CM.zoom_at(1.5, mv) - 1.0
        self.assertAlmostEqual(half / 0.2, 0.875, places=3)  # r3 measured 0.80-0.97
        self.assertAlmostEqual(CM.zoom_at(0.5, mv), 1.0)
        self.assertAlmostEqual(CM.zoom_at(3.0, mv), 1.2)

    def test_pivot_from_pose_maps_to_crop(self):
        fr = [dict(nf=1, fx=0.5, fy=0.35)] * 10
        self.assertAlmostEqual(CM.pivot_from_pose(fr)[0], 0.5, places=3)
        self.assertEqual(CM.pivot_from_pose([]), (0.5, 0.40))


if __name__ == "__main__":
    unittest.main()
