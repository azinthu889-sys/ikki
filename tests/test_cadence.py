"""core/cadence.py — source cadence detection and the 3:2 de-duplication plan.

Synthetic frame-difference tracks at talking-head scale (new pictures 0.2–0.6 grey
levels, duplicates 0.01–0.05), so the tests hit the same range that made fixed
thresholds unreliable. The ways a detector can do harm are attacked directly:
full-rate 60p, 30p, 12p holds, a still picture and a 3:2 → 60p change point must
never be de-duplicated. One end-to-end run pushes a real ffmpeg graph through.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import numpy as np          # noqa: E402
import cadence as C         # noqa: E402

FAILED = []
FPS = 60.0


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def track(holds, rng, lo=0.2, hi=0.6):
    """d[i] for a picture sequence held `holds` frames each; returns d and the set of
    frame indices that start a new picture."""
    d = []; starts = [0]
    for h in holds:
        d += list(rng.uniform(0.01, 0.05, h - 1)) + [rng.uniform(lo, hi)]
        starts.append(starts[-1] + h)
    return np.asarray(d[:-1], np.float32), set(starts[:-1])


def pulldown(sec, rng, slip_every=4.0):
    """3:2 at 60p with the phase slipping every few seconds (as in tokutei.mp4)."""
    holds = []; t = 0; nxt = slip_every * FPS
    while t < sec * FPS:
        h = 2 if len(holds) % 2 == 0 else 3
        if t > nxt:
            holds.append(h); nxt += slip_every * FPS      # repeat → 2,2 or 3,3
            t += h
        holds.append(h); t += h
    return holds


def spans_of(d):
    segs = C.segments(C.windows(d, FPS))
    return segs, C.pulldown_spans(segs, (len(d) + 1) / FPS)


def main():
    rng = np.random.default_rng(3)

    print("3:2 with phase slips, talking-head levels")
    d, starts = track(pulldown(20, rng), rng)
    segs, sp = spans_of(d)
    check("one 3:2 segment", [s["pattern"] for s in segs] == ["3:2"], segs)
    check("span covers the file", sp and sp[0][0] == 0 and sp[0][1] >= 19.9, sp)
    k = C.keep(d, FPS, *sp[0])
    hit = len(set(k) & starts) / len(k)
    check("kept frames are picture starts ≥ 98%", hit >= 0.98, f"{hit:.3f}")
    check("≈24 pictures/s kept", abs(len(k) / (sp[0][1] - sp[0][0]) - 24) < 0.5, len(k))

    print("3:2 at very low motion (0.08–0.2) — still relative, still found")
    d, _ = track(pulldown(10, rng), rng, lo=0.08, hi=0.2)
    segs, sp = spans_of(d)
    check("found", bool(sp), segs)

    print("things that must NOT be de-duplicated")
    for name, holds in [("60p full rate", [1] * 1200), ("30p (2:2)", [2] * 600),
                        ("12p holds of 5", [5] * 240)]:
        d, _ = track(holds, rng)
        segs, sp = spans_of(d)
        check(f"{name}: no span", sp == [], f"{sp} {[s['pattern'] for s in segs]}")
    d = rng.uniform(0.01, 0.05, 1200).astype(np.float32)
    check("still picture: no span", spans_of(d)[1] == [])

    print("change point 3:2 → 60p at 30 s")
    a, _ = track(pulldown(30, rng), rng)
    b, _ = track([1] * 1200, rng)
    d = np.concatenate([a, [0.4], b]).astype(np.float32)
    segs, sp = spans_of(d)
    cp = len(a) / FPS
    check("span stops before the change", sp and sp[-1][1] <= cp, f"{sp} change {cp:.2f}")
    check("change point within 1 s", any(abs(s["t0"] - cp) <= 1.0 for s in segs[1:]),
          [(s["t0"], s["pattern"]) for s in segs])

    print("plan covers the file on the output grid")
    segs_p = C.plan(d, FPS, 30, sp)
    dur = (len(d) + 1) / FPS
    tot = sum(int(round((s[2] - s[1]) * 30)) for s in segs_p)
    # an odd 60p frame count is a half output frame; rounding either way is fine
    check("frame count = duration × 30 (±½)", abs(tot - dur * 30) <= 0.5 + 1e-9, f"{tot} vs {dur*30}")
    check("contiguous", all(abs(x[2] - y[1]) < 1e-9 for x, y in zip(segs_p, segs_p[1:])))

    print("expression depth — ffmpeg refuses a flat 200-term sum")
    e = C._sum([f"eq(n,{i})" for i in range(1400)])
    depth = mx = 0
    for ch in e:
        depth += ch == "("; depth -= ch == ")"; mx = max(mx, depth)
    check("nesting ≤ 16", mx <= 16, mx)

    print("end to end through ffmpeg (6 s testsrc, 64×36)")
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "s.mp4"); out = os.path.join(td, "o.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                        "testsrc=s=64x36:r=60:d=6", "-f", "lavfi", "-i", "sine=d=6",
                        "-pix_fmt", "yuv420p", "-shortest", src], check=True)
        dd, _ = track(pulldown(6, rng, slip_every=99), rng)
        dd = np.concatenate([dd, rng.uniform(0.01, 0.05, 359 - len(dd))])[:359].astype(np.float32)
        info = dict(d=dd, fps=FPS, spans=[(0.0, 6.0)])
        C.proxy(src, out, 64, 36, 30, info, ["-c:v", "libx264", "-preset", "ultrafast"],
                os.path.join(td, "g.fg"), log=lambda *_: None)
        n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v",
                            "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out],
                           capture_output=True, text=True).stdout.strip()
        check("180 frames out", n == "180", n)

    print("FAILED: " + ", ".join(FAILED) if FAILED else "all passed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
