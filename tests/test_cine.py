#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cinematic Vlog engine (core/cinevlog.py) — planner rules on synthetic clips.

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
    CI = importlib.import_module("cinevlog")
    sys.path.pop(0)
    sys.path.insert(0, ROOT)
    for m in [k for k in list(sys.modules) if k in ("cinevlog", "measure", "video_codec")]:
        del sys.modules[m]
    importlib.import_module("core.cinevlog")
    check(True, "imports flat (worker) and as core.cinevlog (API)")

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
    # the exact leak on the published town vlog (8:10)
    check(CI.clean_line("even if you do not have a bank cardSubtitle")
          == "even if you do not have a bank card", "glued 'cardSubtitle' is stripped")
    check(CI.clean_line("Captioned photos are fine") == "Captioned photos are fine",
          "a real word containing 'caption' survives")
    # motionkit ships its own cine.py — the worker must never import that name
    src = open(os.path.join(ROOT, "worker", "run.py"), encoding="utf-8").read()
    check("import cine " not in src and "import cine\n" not in src
          and ", cine as" not in src, "worker imports cinevlog, not motionkit's cine")
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

    # 10 · ① cutaways — face first, B-roll cover, voice continuous
    import numpy as np
    cl2 = []
    for i in range(12):
        talk = [(1.0, 12.0)] if i == 5 else []
        cl2.append(clip(f"D{i}", 14.0, talk, created=f"2020-12-19T02:{i:02d}:00Z"))
    e2, r2 = CI.plan(cl2, seed="c", teaser="off")
    e2 = CI.cutaways(e2, r2.pop("usable_clips"), random.Random(1), log=lambda *_: None)
    CI.quantise(e2); CI.sync_spans(e2)
    sp = [s for s in e2 if s.get("sid")]
    check(len(sp) >= 3 and sp[0]["kind"] == "talk" and any(s["kind"] == "cover" for s in sp)
          and sp[-1]["kind"] == "talk", f"talk split face→cover→face ({[s['kind'] for s in sp]})")
    check(all(not CI._has_talk(s["clip"], s["a"], s["b"]) for s in sp if s["kind"] == "cover"),
          "cover shots carry no on-camera speech")
    last = sp[-1]
    check(abs((last["a"] - sp[0]["sa"]) - (last["o0"] - sp[0]["o0"])) < 1e-6,
          "closing face piece is in lip sync with the running voice")
    ev = CI.audio_events(e2)
    tev = [x for x in ev if x.get("sid")]
    check(len(tev) == 1 and abs(tev[0]["d"] - sum(s["n"] / CI.FPS for s in sp)) < 1e-6,
          "one continuous audio event spans every piece")

    # 11 · ② voice-over: long pauses shortened, levelled, phrases found
    import tempfile, wave as _w
    sr = 48000; d = tempfile.mkdtemp()
    # voice-band "speech": 600–1400 Hz, syllable-rate amplitude wobble
    def tone(L):
        t = np.arange(int(L * sr)) / sr
        return (0.2 * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * t)) *
                np.sin(2 * np.pi * (1000 + 400 * np.sin(2 * np.pi * 0.7 * t)) * t)).astype(np.float32)
    sil = lambda L: np.zeros(int(L * sr), np.float32)
    x = np.concatenate([sil(2.0), tone(3.0), sil(0.8), tone(2.0), sil(4.0), tone(3.0), sil(3.0)])
    vp = os.path.join(d, "vo.wav")
    with _w.open(vp, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes((x * 32767).astype("<i2").tobytes())
    p_, ph, L = CI.prepare_vo(vp, d, log=lambda *_: None)
    gaps = [ph[i + 1][0] - ph[i][1] for i in range(len(ph) - 1)]
    check(ph and ph[0][0] == 0.0, "leading silence removed")
    check(gaps and max(gaps) <= CI.VO_GAP_MAX + 0.01, f"pauses ≤ {CI.VO_GAP_MAX}s ({[round(g,2) for g in gaps]})")
    # 8 s of voice + pauses (0.8 kept, 4.0→1.0) + the 0.12/0.25 pads ≈ 10.2 s
    check(9.3 <= L <= 11.0, f"VO {x.size/sr:.1f}s → {L:.1f}s (voice kept, only silence cut)")

    # 12 · ② fill the picture to exactly the voice length
    cl3 = [clip(f"E{i}", 12.0, created=f"2020-12-19T03:{i:02d}:00Z") for i in range(20)]
    e3, r3 = CI.plan(cl3, seed="v", vo=True)
    us = r3.pop("usable_clips")
    T = 60.0
    e3 = CI.fill_to(e3, T, us, random.Random(2), log=lambda *_: None)
    tot = CI.quantise(e3)
    check(abs(tot - T) < 0.6, f"picture {tot:.2f}s fits VO {T}s")
    check(not any(s["kind"] == "teaser" for s in e3), "no teaser in voice-over mode")
    try:
        CI.fill_to(CI.plan(cl3[:2], seed="v", vo=True)[0], 300.0, us[:2], random.Random(2),
                   log=lambda *_: None)
        check(False, "too-long VO must be refused")
    except RuntimeError:
        check(True, "VO longer than the footage is refused with a reason")

    print(f"\n{len(fails)} failed" if fails else "\nall passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
