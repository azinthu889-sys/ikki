# -*- coding: utf-8 -*-
"""`_breathe()` must keep proportions when the job format differs from the source.

2026-09-26: a 16:9 source rendered as 9:16 (short-916) came out squeezed about
3x horizontally, because zoompan's `s=` resizes to the target without cropping.
A square in the source must still be a square in the output.
"""
import os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "worker"))
sys.path.insert(0, os.path.join(ROOT, "core"))
import run as W          # noqa: E402


def _box(png):
    """(w, h) of the white square in a mostly-black frame"""
    from PIL import Image
    import numpy as np
    a = np.asarray(Image.open(png).convert("L")) > 128
    ys, xs = np.nonzero(a)
    return xs.max() - xs.min() + 1, ys.max() - ys.min() + 1


class BreatheAspect(unittest.TestCase):

    def test_169_to_916_keeps_square(self):
        with tempfile.TemporaryDirectory() as d:
            src, out, png = (os.path.join(d, n) for n in ("s.mp4", "o.mp4", "f.png"))
            # 640x360 black frame with a 100x100 white square in the middle
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                            "color=c=black:s=640x360:d=1:r=30",
                            "-vf", "drawbox=x=270:y=130:w=100:h=100:c=white:t=fill",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", src], check=True)
            W._breathe(src, out, 30, 0.0001, 270, 480)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out,
                            "-frames:v", "1", png], check=True)
            bw, bh = _box(png)
            self.assertLess(abs(bw / bh - 1.0), 0.08,
                            f"square became {bw}x{bh} -- frame was stretched")


if __name__ == "__main__":
    unittest.main()
