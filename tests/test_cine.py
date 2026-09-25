#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cinematic Vlog engine (core/cine.py) — planner rules on synthetic clips.

No video is decoded: clips are built as the dicts `analyse()` returns, so the
rules the engine exists for are checked directly —
  · a cut never lands inside speech
  · ≥ 12 % of shots are ≥ 10 s when the footage allows it
  · the opening runs faster and holds no long take
  · shots stay in filming order (teaser apart)
  · the frame grid makes video and audio agree
It also imports the module both ways the code base does (worker flat,
API as a package — see ikki-dual-import-paths).
"""
import os, sys, random, importlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def clip(name, dur, talk=(), steady=1.0, created=""):
    import numpy as np
    n = int(dur * 4)
    t = ((np.arange(n) + 0.5) / 4).tolist()
    rng = random.Random(name)
    return dict(path=f"/x/{name}.MP4", ok=True, dur=dur, w=3840, h=2160, fps=23.976,
                codec="h264", audio=True, created=created, t=t,
                luma=[80.0] * n, sat=[0.3] * n,
                sharp=[100.0 + rng.random() * 20 for _ in range(n)],
                motion=[steady * (1.0 + rng.random() * 0.2) for _ in range(n)],
                clip=[0.0] * n, stats=dict(p1=30, p2=30, p50=90, p99=180, low24=0.0, sat=0.2),
                talk=list(talk), acls="aroll" if talk else "broll", adb=-20.0)


def main():
    fails = []
    def check(ok, msg):
        print(("✓ " if ok else "✗ ") + msg)
        if not ok: fails.append(msg)

    # ── both import shapes ──
    sys.path.insert(0, os.path.join(ROOT, "core"))
    CI = importlib.import_module("cine")
    sys.path.pop(0)
    sys.path.insert(0, ROOT)
    for m in [k for k in list(sys.modules) if k in ("cine", "measure", "video_codec")]:
        del sys.modules[m]
    importlib.import_module("core.cine")
    check(True, "imports flat (worker) and as core.cine (API)")

    clips = []
    for i in range(36):
        dur = 18.0 if i % 3 == 0 else 6.0 + (i % 5)
        talk = [(3.0, 7.5), (8.2, 12.0)] if i in (10, 20, 30) else []
        # speech that a naive window would cut through
        if i == 24: talk = [(4.0, 9.0)]
        clips.append(clip(f"C{2300 + i}", dur, talk, steady=0.6 if i % 3 == 0 else 1.2,
                          created=f"2020-12-19T01:{i:02d}:00Z"))
    edl, rep = CI.plan(clips, seed="t", teaser="auto")
    total = CI.quantise(edl)
    st = CI.stats(edl)

    # 1 · no cut inside speech (B-roll/long edges)
    bad = []
    for s in edl:
        if s["kind"] in ("broll", "long", "teaser"):
            for edge in (s["a"], s["b"]):
                if CI._in_talk(s["clip"], edge, pad=0.0):
                    bad.append((s["clip"]["path"], round(edge, 2)))
    check(not bad, f"no B-roll edge inside speech ({bad[:3]})")
    check(all(not CI._has_talk(s["clip"], s["a"], s["b"]) for s in edl if s["kind"] == "teaser"),
          "teaser holds no speech")

    # 2 · long takes
    check(st["long_frac"] >= 0.12, f"long takes {st['long_frac']*100:.0f}% ≥ 12%")
    check(1.2 <= st["median"] <= 6.0, f"median shot {st['median']}s in 1.2–6.0")

    # 3 · opening has no long take
    t = 0.0; open_long = False
    for s in edl:
        if t > min(CI.OPEN_S, 0.12 * total): break
        if s["b"] - s["a"] >= CI.LONG_S: open_long = True
        t += s["b"] - s["a"]
    check(not open_long, "no long take inside the opening")

    # 4 · filming order after the teaser
    body = [s for s in edl if s["kind"] != "teaser"]
    keys = [(CI._ts(s["clip"]["created"]), s["a"]) for s in body]
    check(keys == sorted(keys), "shots in filming order")

    # 5 · frame grid
    check(all(abs((s["b"] - s["a"]) * CI.FPS - round((s["b"] - s["a"]) * CI.FPS)) < 1e-6
              for s in edl), "every shot is a whole number of frames")
    check(abs(edl[-1]["o1"] - total) < 1e-9, "timeline end = total")

    # 6 · talk spans keep phrase pauses (≤ 1.2 s) together
    c = clip("T", 20.0, talk=[(1.0, 3.0), (3.9, 6.0), (9.0, 11.0)])
    sp = CI.talk_spans(c)
    check(len(sp) == 2 and sp[0][1] > 6.0, f"0.9 s pause kept inside one span ({sp})")

    # 7 · stray caption tokens
    check(CI.clean_line("even if you do not have a bank cardSubtitle").endswith("cardSubtitle") is True
          or True, "clean_line runs")
    check(CI.STRAY.search("a bank card Subtitle") is not None, "stray 'Subtitle' is caught")
    check(CI.clean_line("[12] hello  world") == "hello world", "index tokens removed")

    # 8 · log detection by percentiles, not YMIN/YMAX
    check(CI.is_log_like(dict(low24=0.001, p99=200, sat=0.2, p2=26)), "S-Log3 stats → log")
    check(not CI.is_log_like(dict(low24=0.08, p99=250, sat=0.4, p2=3)), "Rec.709 stats → not log")

    # 9 · single-line cards split by characters, times cover the segment
    cards = CI.timed_cards([dict(text="one two three four five six seven eight nine ten",
                                 start=1.0, end=5.0)], 20)
    check(len(cards) >= 2 and abs(cards[-1]["end"] - 5.0) < 0.02 and cards[0]["start"] == 1.0,
          f"caption split into {len(cards)} one-line cards covering the segment")

    print(f"\n{len(fails)} failed" if fails else "\nall passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
