#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · Cinematic Vlog engine — footage-led, many clips in, one film out.

The talking-head pipeline (`worker/run.py: render`) starts from one recording
and removes what should not be there.  A cinematic vlog is the opposite: it
starts from dozens of camera clips and has to *choose*.  Everything here is
built from Zin's own ZIN JAPAN LIFE vlogs (five measured, all 4K/24/16:9):

  ① cutting is bimodal — median shot 1.5–5.6 s depending on the video, but
    **shots over 10 s stay at 12–18 %** in every one.  That fraction is the
    signature; the median is a per-video choice (`cine_pace`).
  ② the first minute runs fastest (camping 3.4 s/cut) and the edit slows as
    the day goes on.
  ③ skin is held constant, only the location moves — so the grade corrects
    exposure and never pushes a global warm look.
  ④ ambience (fire, water, wind) leads the mix; music sits underneath.
  ⑤ text is almost absent — captions are chosen per audience (none / my / en /
    ja+en), single line, white, no stroke, no panel, bottom at 92.5 %.

⚠️ named `cinevlog`, not `cine`: motionkit (on the worker's sys.path) already
   has a `cine.py`, and whichever was imported first won — the captioner got
   motionkit's module and died on `clean_line`.

The module is pure numpy + ffmpeg and knows nothing about the IKKI API; the
worker (`run.py: cine_handle`) downloads the clips, calls `run()`, and posts
the result.
"""
import os, re, json, math, time, wave, hashlib, random, subprocess
import numpy as np

try:
    from video_codec import h264_args
except ImportError:
    from core.video_codec import h264_args
try:
    import measure as M
except ImportError:
    from core import measure as M

HERE = os.path.dirname(os.path.abspath(__file__))

# ── measured targets (zjl-study FINDINGS 1–5) ──────────────────────────────
LONG_S = 10.0                 # "long take" boundary used in every measurement
LONG_BAND = (0.12, 0.18)      # fraction of shots ≥ LONG_S — the invariant
SHORT_S = 2.0
PACE = {                      # median shot per pace, from the five videos
    "fast": 1.6,              # day-in-the-life 1.5
    "normal": 3.0,            # camping 3.0 · town 3.4
    "calm": 4.5,              # baby 3.9 · year-end 5.6
}
OPEN_S = 60.0                 # the fast opening minute (②)
OPEN_K = 0.70
SR = 48000
FPS = 24
FADE_S = 1.0                  # fade from/to black at the very start and end

# audio levels (dBFS RMS) — ambience ~8 dB under speech (④); music is left to
# `music.bed`, whose ducking already sits it ~20 dB under voice.
TALK_DB = -20.0
AMB_DB = -28.0
GAIN_CAP = 15.0

# caption spec measured on the ZJL vlogs — block 5.3 % of H, bottom 92.5 %
CAP_BOTTOM = 0.925
CAP_BLOCK = 0.053
# ⚠️ an editor's label leaked into a published caption ("…bank cardSubtitle",
#    town vlog 8:10).  Scan every line for these before burning in.
#    ⚠️ the real leak was GLUED ("cardSubtitle") — a `\b` on the left never
#       matches there, so a capitalised token right after a lowercase letter is
#       caught separately.
STRAY = re.compile(r"(?i)(?<![a-z])(subtitles?|captions?|text here|lorem ipsum)\b"
                   r"|(?<=[a-z])(Subtitles?|Captions?)\b|\[\d+\]|^\d+$")

VIDEO_EXT = (".mp4", ".mov", ".m4v", ".mts", ".avi", ".mkv")


# ═══════════════════════════════════════════════════════════════════════════
# probing
# ═══════════════════════════════════════════════════════════════════════════
def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                        "-of", "json", path], capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = d.get("format", {})
    try:
        n, dn = (v.get("r_frame_rate") or "0/1").split("/")
        fps = float(n) / float(dn or 1)
    except Exception:
        fps = 0.0
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    rot = 0
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = int((v.get("tags") or {}).get("rotate") or rot)
    if abs(rot) % 180 == 90:
        w, h = h, w
    tags = dict(fmt.get("tags") or {})
    tags.update(v.get("tags") or {})
    ct = (tags.get("com.apple.quicktime.creationdate") or tags.get("creation_time")
          or "")
    return dict(dur=float(fmt.get("duration") or v.get("duration") or 0.0),
                w=w, h=h, fps=fps, codec=v.get("codec_name") or "",
                pix=v.get("pix_fmt") or "", audio=a is not None,
                created=ct, size=int(fmt.get("size") or 0))


def _ts(ct):
    """creation time → epoch seconds (0 when unknown)."""
    if not ct:
        return 0.0
    import datetime as _dt
    s = ct.strip().replace("Z", "+00:00")
    for f in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
        try:
            return _dt.datetime.strptime(s, f).timestamp()
        except ValueError:
            continue
    return 0.0


def _natkey(p):
    b = os.path.basename(p)
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", b)]


# ═══════════════════════════════════════════════════════════════════════════
# per-clip analysis
# ═══════════════════════════════════════════════════════════════════════════
SAMPLE_FPS = 4.0
SW, SH = 160, 90              # analysis frame (letterboxed to 16:9)


def _frames(path, dur, fps=SAMPLE_FPS):
    """RGB uint8 frames (n, SH, SW, 3) at `fps`, plus their times."""
    vf = (f"fps={fps},scale={SW}:{SH}:force_original_aspect_ratio=decrease,"
          f"pad={SW}:{SH}:(ow-iw)/2:(oh-ih)/2,format=rgb24")
    cmd = ["ffmpeg", "-v", "error", "-hwaccel", "videotoolbox", "-i", path,
           "-an", "-vf", vf, "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    if not raw:        # hwaccel is optional — retry in software
        raw = subprocess.run([c for c in cmd if c not in ("-hwaccel", "videotoolbox")],
                             capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8)
    n = len(fr) // (SW * SH * 3)
    fr = fr[: n * SW * SH * 3].reshape(n, SH, SW, 3)
    t = (np.arange(n) + 0.5) / fps
    return fr, t


def _luma(x):
    x = x.astype(np.float32)
    return 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]


def _sat(x):
    x = x.astype(np.float32)
    mx, mn = x.max(-1), x.min(-1)
    return (mx - mn) / (mx + 1e-6)


def _sharp(g):
    """variance of a 4-neighbour Laplacian, per frame."""
    lap = (-4 * g[:, 1:-1, 1:-1] + g[:, :-2, 1:-1] + g[:, 2:, 1:-1]
           + g[:, 1:-1, :-2] + g[:, 1:-1, 2:])
    return lap.reshape(len(g), -1).var(1)


def analyse(path, cache_dir=None, log=print):
    """Everything the planner needs about one clip.  Cached per file."""
    st = os.stat(path)
    key = hashlib.sha1(f"{os.path.abspath(path)}|{st.st_size}|{int(st.st_mtime)}|v1"
                       .encode()).hexdigest()[:16]
    cp = os.path.join(cache_dir, f"cine_{key}.npz") if cache_dir else None
    if cp and os.path.exists(cp):
        z = np.load(cp, allow_pickle=True)
        c = z["meta"].item()
        c["thumbs"] = z["thumbs"]
        return c
    m = probe(path)
    fr, t = _frames(path, m["dur"])
    if len(fr) == 0:
        return dict(path=path, ok=False, why="no video frames", **m)
    g = _luma(fr)
    luma = np.median(g.reshape(len(g), -1), 1)
    sat = _sat(fr).reshape(len(fr), -1).mean(1)
    sharp = _sharp(g)
    motion = np.r_[0.0, np.abs(np.diff(g, axis=0)).reshape(len(g) - 1, -1).mean(1)]
    clip = ((g < 4) | (g > 251)).reshape(len(g), -1).mean(1)
    allg = g.reshape(-1)
    stats = dict(p1=float(np.percentile(allg, 1)), p2=float(np.percentile(allg, 2)),
                 p50=float(np.median(allg)), p99=float(np.percentile(allg, 99)),
                 low24=float((allg < 24).mean()), sat=float(sat.mean()))
    # ── audio ──
    talk, cls, adb = [], "silent", -90.0
    if m["audio"]:
        db, voice, _ad = M.analyse(path)
        if len(db):
            adb = float(np.percentile(db, 95))
            cls, _info = M.classify(db, voice)
            thr = M.thr_of(db)
            mk = M.mask(db, voice, thr)
            talk = [(round(a, 2), round(b, 2)) for a, b in M.runs(mk, True)
                    if b - a >= 0.25]
    # keep ~1 thumbnail per second for grading measurements (small)
    step = max(1, int(round(SAMPLE_FPS)))
    thumbs = fr[::step, ::2, ::2].copy()
    c = dict(path=path, ok=True, t=t.tolist(), luma=luma.tolist(), sat=sat.tolist(),
             sharp=sharp.tolist(), motion=motion.tolist(), clip=clip.tolist(),
             stats=stats, talk=talk, acls=cls, adb=round(adb, 1), **m)
    if cp:
        os.makedirs(cache_dir, exist_ok=True)
        meta = {k: v for k, v in c.items() if k != "thumbs"}
        np.savez_compressed(cp, meta=np.array(meta, dtype=object), thumbs=thumbs)
    c["thumbs"] = thumbs
    return c


def is_log_like(st):
    """Flat camera profile (S-Log3 / Cine) from pixel percentiles.

    ⚠️ never from YMIN/YMAX — single outlier pixels put log footage at 0/255
       (zjl-podcast-grade trap 1).  S-Log3 has almost nothing below code 24,
       a median of 85–100 and a 99th percentile well short of white.
    """
    return (st["low24"] < 0.015 and st["p99"] < 236 and st["sat"] < 0.30
            and st["p2"] >= 18)


def camera_groups(clips):
    """Majority vote per camera (resolution · fps · codec): one clip of a dark
    river must not flip the whole camera's decision."""
    groups = {}
    for c in clips:
        if not c.get("ok"):
            continue
        k = (c["w"], c["h"], round(c["fps"], 2), c["codec"])
        groups.setdefault(k, []).append(c)
    for k, cs in groups.items():
        votes = sum(1 for c in cs if is_log_like(c["stats"]))
        log_cam = votes >= max(1, math.ceil(len(cs) * 0.6))
        for c in cs:
            c["log"] = bool(log_cam)
            c["cam"] = f"{k[0]}x{k[1]}@{k[2]:.2f} {k[3]}"
    return groups


# ═══════════════════════════════════════════════════════════════════════════
# LUT (S-Log3 → Rec.709) with per-clip exposure in linear light
# ═══════════════════════════════════════════════════════════════════════════
LUT_EVS = (-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0)
LUT_DIR = os.path.expanduser(os.environ.get("IKKI_LUT_DIR", "~/.ikki/lut"))
# measured on 201 frames of the 40-clip river camp against camp/baby/day refs:
#   sat 1.3 · ceil 0.80        → mean sat 0.41 · green p90 0.87 · p99 251 (neon trees, hot sky)
#   sat 1.7 · ceil 0.60 · knee → mean sat 0.40 · green p90 0.73 · p99 230
#   refs: mean sat 0.40–0.54 · green p90 0.62–0.80 · p99 198–238
LUT_KW = dict(contrast=1.05, white=3.0, sat=1.7, sat_ceil=0.60, skin_protect=0.6,
              shoulder=(0.80, 0.94))


WB_G = (0.97, 1.0, 1.03, 1.06, 1.09, 1.12)   # green gain, linear, gated off skin


def lut_path(ev, wg=1.0):
    """Build once, cache forever.  ~2.4 s per LUT (7 EV × 6 WB = 42 max)."""
    tag = hashlib.sha1(json.dumps(LUT_KW, sort_keys=True).encode()).hexdigest()[:8]
    p = os.path.join(LUT_DIR, f"slog3_vlog_{tag}_ev{ev:+.1f}_g{wg:.2f}.cube")
    if not os.path.exists(p):
        try:
            import slog3lut as L
        except ImportError:
            from core import slog3lut as L
        os.makedirs(LUT_DIR, exist_ok=True)
        tmp = p + ".part"
        L.build(tmp, L.SGAMUT3_CINE, 33, exposure=2.0 ** ev, wb=(1.0, wg, 1.0), **LUT_KW)
        os.replace(tmp, p)
    return p


def neutral_cast(img):
    """(R+B)/2 − G on near-grey pixels: + = magenta, − = green."""
    x = img.astype(np.float32)
    mx, mn = x.max(-1), x.min(-1)
    g = ((mx - mn) / (mx + 1e-6) < 0.25) & (mx > 50)
    if g.mean() < 0.05:
        return 0.0
    return float(((x[..., 0][g] + x[..., 2][g]) / 2 - x[..., 1][g]).mean())


_LUT_CACHE = {}


def _read_cube(p):
    if p in _LUT_CACHE:
        return _LUT_CACHE[p]
    rows, n = [], 0
    for ln in open(p):
        ln = ln.strip()
        if ln.startswith("LUT_3D_SIZE"):
            n = int(ln.split()[1])
        elif ln and (ln[0].isdigit() or ln[0] == "-"):
            rows.append([float(v) for v in ln.split()])
    a = np.array(rows, np.float32).reshape(n, n, n, 3)     # [b][g][r]
    _LUT_CACHE[p] = a
    return a


def apply_lut_np(img, lut):
    """trilinear lookup — good enough to *measure* what ffmpeg's lut3d gives."""
    n = lut.shape[0]
    x = img.astype(np.float32) / 255.0 * (n - 1)
    i0 = np.clip(np.floor(x).astype(int), 0, n - 2)
    f = x - i0
    r0, g0, b0 = i0[..., 0], i0[..., 1], i0[..., 2]
    fr, fg, fb = f[..., 0:1], f[..., 1:2], f[..., 2:3]
    out = 0
    for db, wb in ((0, 1 - fb), (1, fb)):
        for dg, wg in ((0, 1 - fg), (1, fg)):
            for dr, wr in ((0, 1 - fr), (1, fr)):
                out = out + lut[b0 + db, g0 + dg, r0 + dr] * (wb * wg * wr)
    return np.clip(out * 255.0, 0, 255)


# exposure policy — correct only what is broken; brightness follows the
# subject (camping median 34 · baby 82 are both right).
LUMA_FLOOR = 30.0      # the camping night section sits at 26–32
LUMA_CEIL = 165.0


def choose_grade(c, a=None, b=None):
    """(ev, eq) for the window [a, b] of clip c — measured, not guessed."""
    th = c["thumbs"]
    if a is not None and len(th):
        i0 = max(0, int(a)); i1 = max(i0 + 1, int(math.ceil(b)))
        th = th[i0:i1] if len(th[i0:i1]) else th
    if not len(th):
        return 0.0, None, {}
    th = th[:: max(1, len(th) // 6)]
    if c.get("log"):
        best = None
        for ev in LUT_EVS:
            y = np.median(_luma(apply_lut_np(th, _read_cube(lut_path(ev)))))
            score = 0.0 if LUMA_FLOOR <= y <= LUMA_CEIL else min(
                abs(y - LUMA_FLOOR), abs(y - LUMA_CEIL))
            # prefer EV 0 whenever it is already in band
            key = (score, abs(ev))
            if best is None or key < best[0]:
                best = (key, ev, y)
        ev, y = best[1], best[2]
        # ⚠️ neutral balance — the LUT's saturation (1.7) also amplifies the
        #    camera's own slight cast: river rocks came out +10 magenta.  A
        #    global WB would turn lips magenta (zjl-podcast-grade), so the
        #    correction is a green gain inside the LUT, gated off skin.
        o = apply_lut_np(th, _read_cube(lut_path(ev)))
        cast0 = neutral_cast(o)
        wg = 1.0
        if abs(cast0) > 3.0:
            best_w = (abs(cast0), 1.0)
            for g_ in WB_G:
                if g_ == 1.0:
                    continue
                cc = neutral_cast(apply_lut_np(th, _read_cube(lut_path(ev, g_))))
                if abs(cc) + 0.5 < best_w[0]:
                    best_w = (abs(cc), g_)
            wg = best_w[1]
            o = apply_lut_np(th, _read_cube(lut_path(ev, wg)))
        return ev, None, dict(luma=round(float(y), 1), sat=round(float(_sat(o).mean()), 3),
                              lut=True, wg=wg, cast=round(cast0, 1),
                              cast_after=round(neutral_cast(o), 1))
    # Rec.709 camera/phone: a gentle gamma only when out of band
    y = float(np.median(_luma(th)))
    eq = None
    if y < LUMA_FLOOR - 4:
        gm = min(1.45, max(1.0, math.log(max(y, 4) / 255.0) / math.log(LUMA_FLOOR / 255.0)))
        eq = f"eq=gamma={gm:.3f}"
    elif y > LUMA_CEIL + 10:
        gm = max(0.80, math.log(y / 255.0) / math.log(LUMA_CEIL / 255.0))
        eq = f"eq=gamma={1.0 / gm:.3f}"
    return 0.0, eq, dict(luma=round(y, 1), sat=round(float(_sat(th).mean()), 3), lut=False)


# ═══════════════════════════════════════════════════════════════════════════
# planning
# ═══════════════════════════════════════════════════════════════════════════
HEAD_SKIP = 0.5       # camera start/stop wobble
TAIL_SKIP = 0.35


def _norm(v, ref):
    return np.asarray(v, np.float32) / (ref + 1e-6)


def score_curve(c, sharp_ref, motion_ref):
    """per-sample quality: sharp, steady, not clipped."""
    s = np.clip(_norm(c["sharp"], sharp_ref), 0, 3)
    mo = np.clip(_norm(c["motion"], motion_ref), 0, 6)
    cl = np.asarray(c["clip"], np.float32)
    return s - 0.45 * mo - 4.0 * cl


def best_window(c, L, q, avoid=(), fps=SAMPLE_FPS):
    """start time of the best window of length L inside the usable range."""
    t = np.asarray(c["t"])
    lo, hi = HEAD_SKIP, c["dur"] - TAIL_SKIP
    if hi - lo < L:
        return None
    k = max(1, int(round(L * fps)))
    cs = np.convolve(q, np.ones(k) / k, "valid")          # window means
    starts = t[: len(cs)] - 0.5 / fps
    ok = (starts >= lo) & (starts + L <= hi)
    for a0, b0 in avoid:                                  # keep windows apart
        ok &= (starts + L <= a0 - 1.0) | (starts >= b0 + 1.0)
    if not ok.any():
        return None
    i = int(np.argmax(np.where(ok, cs, -1e9)))
    return float(max(lo, starts[i])), float(cs[i])


def talk_spans(c, keep_gap=1.2, pre=0.15, post=0.30, min_len=1.0):
    """speech runs → kept spans (silence > keep_gap removed).

    ⚠️ 1.2 s, the Cinematic Vlog recipe's `min_sil`: at 0.7 s C2339 fell apart
       into five 0.8–2.6 s pieces — a jump cut every second.  In a vlog the
       pauses between phrases are part of the take.
    """
    out = []
    for a, b in c.get("talk") or []:
        a, b = max(0.0, a - pre), min(c["dur"], b + post)
        if out and a - out[-1][1] <= keep_gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out if b - a >= min_len]


def role_of(c):
    """talk / broll.

    ⚠️ not `measure.classify` alone — its range ≥ 20 dB rule was built on
       talking-head files, and river or wind noise pushes a speaking clip under
       it (C2339: 6.7 s of speech in 23 s, classified B-roll).  Real speech
       here = at least 2 s and a quarter of the clip.
    """
    sp = talk_spans(c)
    tot = sum(b - a for a, b in sp)
    if tot >= max(2.0, 0.25 * c["dur"]):
        return "talk", sp
    return "broll", []


def _in_talk(c, t, pad=0.05):
    for a, b in c.get("talk") or []:
        if a - pad < t < b + pad:
            return (a, b)
    return None


def speech_safe(c, a, b, max_grow=2.5, min_len=0.9):
    """move B-roll window edges out of any speech run — a cut must never land
    inside a word.  Grows the window to finish a phrase when it can, shrinks it
    when it cannot."""
    lo, hi = HEAD_SKIP * 0.5, c["dur"] - TAIL_SKIP * 0.5
    r = _in_talk(c, a)
    if r:
        a = r[0] - 0.12 if r[0] - 0.12 >= lo else r[1] + 0.12
    r = _in_talk(c, b)
    if r:
        b = r[1] + 0.20 if (r[1] + 0.20 <= hi and r[1] + 0.20 - b <= max_grow) \
            else r[0] - 0.12
    return (a, b) if b - a >= min_len else None


def _has_talk(c, a, b):
    return any(x < b and y > a for x, y in c.get("talk") or [])


def plan(clips, pace="normal", teaser="auto", seed="", target=None, log=print):
    """Order, choose and time every shot.  Returns (edl, report)."""
    rng = random.Random(hashlib.sha1(str(seed).encode()).hexdigest())
    med = PACE.get(pace, PACE["normal"])
    ok = [c for c in clips if c.get("ok") and c["dur"] >= 1.0]
    bad = [os.path.basename(c["path"]) for c in clips if c not in ok]
    # ① order — the day as it happened
    ok.sort(key=lambda c: (_ts(c.get("created")) or 9e18, _natkey(c["path"])))
    sharp_ref = float(np.median(np.concatenate([np.asarray(c["sharp"]) for c in ok])))
    motion_ref = float(np.median(np.concatenate([np.asarray(c["motion"]) for c in ok]))) or 1.0
    for c in ok:
        c["q"] = score_curve(c, sharp_ref, motion_ref)
        c["role"], c["tspans"] = role_of(c)
        u = np.asarray(c["t"]); qq = c["q"]
        inner = (u > HEAD_SKIP) & (u < c["dur"] - TAIL_SKIP)
        c["qmed"] = float(np.median(qq[inner])) if inner.any() else float(np.median(qq))
        c["steady"] = float(np.median(np.asarray(c["motion"])[inner] / motion_ref)) \
            if inner.any() else 9.0
    # ② reject the unusable — but never more than a third, and say which
    broll = [c for c in ok if c["role"] == "broll"]
    ranked = sorted(broll, key=lambda c: c["qmed"])
    reject = [c for c in ranked if c["qmed"] < -0.8][: len(broll) // 3]
    for c in reject:
        c["reject"] = "blurred or shaking"
    usable = [c for c in ok if not c.get("reject")]
    n_b = sum(1 for c in usable if c["role"] == "broll")
    # ③ one (sometimes two) moments per clip, in time order
    def lognorm(hi=7.5):
        return float(np.clip(rng.lognormvariate(math.log(med), 0.45), 1.0, hi))
    shots = []
    for c in usable:
        if c["role"] == "talk":
            for a, b in c["tspans"]:
                shots.append(dict(clip=c, a=a, b=b, kind="talk"))
            continue
        avail = c["dur"] - HEAD_SKIP - TAIL_SKIP
        L = min(lognorm(), avail)
        if L < 0.9:
            c["reject"] = "too short"
            continue
        w = best_window(c, L, c["q"])
        if w is None:
            continue
        ss = speech_safe(c, w[0], w[0] + L)
        if not ss:
            continue
        shots.append(dict(clip=c, a=ss[0], b=ss[1], kind="broll", q=w[1]))
        if avail >= 3 * L + 4.0 and avail >= 12.0:
            L2 = lognorm(6.0)
            w2 = best_window(c, L2, c["q"], avoid=[ss])
            ss2 = speech_safe(c, w2[0], w2[0] + L2) if w2 else None
            if ss2 and w2[1] >= 0.7 * w[1]:
                shots.append(dict(clip=c, a=ss2[0], b=ss2[1], kind="broll", q=w2[1]))
    def _key(s):
        return (_ts(s["clip"].get("created")) or 9e18, _natkey(s["clip"]["path"]), s["a"])
    shots.sort(key=_key)
    # ④ teaser — the best moments of the whole day, spread evenly, no speech
    use_teaser = (teaser is True or teaser == "on"
                  or (teaser == "auto" and n_b >= 15))
    tz = []
    if use_teaser:
        pool = [c for c in usable if c["role"] == "broll"]
        good = sorted(pool, key=lambda c: -c["qmed"])[: max(10, int(len(pool) * 0.6))]
        order_ = {id(c): i for i, c in enumerate(usable)}
        good.sort(key=lambda c: order_[id(c)])
        idx = sorted({int(round(x)) for x in np.linspace(0, len(good) - 1, min(10, len(good)))})
        for c in (good[i] for i in idx):
            used = [(s["a"], s["b"]) for s in shots if s["clip"] is c]
            w = best_window(c, 1.1, c["q"], avoid=used)
            if w and not _has_talk(c, w[0], w[0] + 1.1):
                tz.append(dict(clip=c, a=w[0], b=w[0] + 1.1, kind="teaser", q=w[1]))
    # ⑤ the opening runs faster (②) — teaser counts toward it.
    #    ⚠️ 60 s is the camping video's first minute out of 13:50.  For a short
    #       film the same 60 s would swallow half of it (a 136 s cut had 44 %
    #       marked "opening", which also barred every long take from it).
    est = sum(s["b"] - s["a"] for s in shots) + sum(s["b"] - s["a"] for s in tz)
    open_s = min(OPEN_S, 0.12 * est)
    tt = sum(s["b"] - s["a"] for s in tz)
    for s in shots:
        if tt >= open_s:
            break
        if s["kind"] == "broll":
            nb = s["a"] + max(0.9, (s["b"] - s["a"]) * OPEN_K)
            if not _in_talk(s["clip"], nb):
                s["b"] = nb
        s["opening"] = True
        tt += s["b"] - s["a"]
    # ⑥ long takes — promote the steadiest clips until 15 % of the FINAL list
    #    is ≥ 10 s.  Never inside the opening minute.
    edl = tz + shots
    def long_frac():
        return sum(1 for s in edl if s["b"] - s["a"] >= LONG_S) / max(1, len(edl))
    cands = [c for c in usable if c["role"] == "broll"
             and c["dur"] - HEAD_SKIP - TAIL_SKIP >= LONG_S + 0.6
             and not any(s.get("opening") for s in shots if s["clip"] is c)]
    cands.sort(key=lambda c: (c["steady"], -c["qmed"]))
    promoted = 0
    for c in cands:
        if long_frac() >= 0.15:
            break
        mine = [s for s in shots if s["clip"] is c]
        if not mine:
            continue
        # ⚠️ no `avoid` for teaser windows: a teaser previews moments that come
        #    later, so overlapping is the point — and a 1.1 s teaser window in
        #    the middle of an 18 s clip left no 10 s gap (5 of 8 promoted).
        L = min(c["dur"] - HEAD_SKIP - TAIL_SKIP, rng.uniform(LONG_S + 0.5, 15.0))
        w = best_window(c, L, c["q"])
        ss = speech_safe(c, w[0], w[0] + L) if w else None
        if not ss or ss[1] - ss[0] < LONG_S:
            continue
        keep = mine[0]
        for s in mine[1:]:
            edl.remove(s); shots.remove(s)
        keep.update(a=ss[0], b=ss[1], kind="long", q=w[1])
        promoted += 1
    want_long = int(math.ceil(0.12 * len(edl)))
    # ⑦ optional length target — drop the weakest short B-roll first
    if target:
        while sum(s["b"] - s["a"] for s in edl) > target:
            drop = [s for s in edl if s["kind"] == "broll"]
            if not drop:
                break
            edl.remove(min(drop, key=lambda s: s.get("q", 0)))
    rep = dict(clips=len(clips), usable=len(usable), talk_clips=sum(
        1 for c in usable if c["role"] == "talk"), broll_clips=n_b,
        rejected=[(os.path.basename(c["path"]), c["reject"]) for c in ok
                  if c.get("reject")] + [(b, "unreadable") for b in bad],
        teaser=len(tz), long_promoted=promoted, long_wanted=want_long,
        long_possible=len(cands) + sum(1 for s in edl if s["kind"] == "talk"
                                       and s["b"] - s["a"] >= LONG_S))
    return edl, rep


# ═══════════════════════════════════════════════════════════════════════════
# music beats (cut B-roll on the beat)
# ═══════════════════════════════════════════════════════════════════════════
def beats(path, max_s=240.0):
    """(period, phase, dur) of the track — onset flux + autocorrelation."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-t", str(max_s), "-i", path,
                          "-ac", "1", "-ar", "22050", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    if len(x) < 22050 * 8:
        return None
    hop, win = 512, 1024
    n = (len(x) - win) // hop
    fr = np.lib.stride_tricks.as_strided(x, (n, win), (x.strides[0] * hop, x.strides[0]))
    S = np.abs(np.fft.rfft(fr * np.hanning(win), axis=1))
    S = np.log1p(S * 10)
    flux = np.maximum(0, np.diff(S, axis=0)).sum(1)
    flux = flux - np.convolve(flux, np.ones(16) / 16, "same")
    flux = np.maximum(flux, 0)
    fps_ = 22050 / hop
    lo, hi = int(fps_ * 60 / 160), int(fps_ * 60 / 70)
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lag = lo + int(np.argmax(ac[lo:hi]))
    period = lag / fps_
    ph = [flux[p::lag].sum() for p in range(lag)]
    phase = int(np.argmax(ph)) / fps_
    dur = float(probe(path)["dur"] or 0)
    return dict(period=period, phase=phase, bpm=60.0 / period, dur=dur)


def snap(edl, bt, tol=0.30):
    """move each B-roll cut onto the nearest beat (talk and long takes keep
    their own timing — speech is never cut to music)."""
    if not bt:
        return 0
    P, ph = bt["period"], bt["phase"]
    t, moved = 0.0, 0
    for s in edl:
        L = s["b"] - s["a"]
        if s["kind"] in ("broll", "teaser"):
            end = t + L
            k = round((end - ph) / P)
            nb = ph + k * P
            if nb - t < 0.8:
                nb += P
            room = s["clip"]["dur"] - TAIL_SKIP - s["a"]
            if (abs(nb - end) <= tol and 0.8 <= nb - t <= room
                    and not _in_talk(s["clip"], s["a"] + (nb - t))):
                s["b"] = s["a"] + (nb - t)
                moved += 1
        t += s["b"] - s["a"]
    return moved


# ═══════════════════════════════════════════════════════════════════════════
# frame grid
# ═══════════════════════════════════════════════════════════════════════════
def quantise(edl, fps=FPS):
    """snap every shot to whole output frames — the video concat and the
    numpy audio mix must agree to the sample."""
    for s in edl:
        s["n"] = max(1, int(round((s["b"] - s["a"]) * fps)))
        s["b"] = s["a"] + s["n"] / fps
    t = 0.0
    for s in edl:
        s["o0"] = t
        t += s["n"] / fps
        s["o1"] = t
    return t


def stats(edl):
    L = np.array([s["b"] - s["a"] for s in edl]) if edl else np.zeros(0)
    if not len(L):
        return {}
    return dict(shots=len(L), total=round(float(L.sum()), 2),
                median=round(float(np.median(L)), 2), mean=round(float(L.mean()), 2),
                long_frac=round(float((L >= LONG_S).mean()), 3),
                short_frac=round(float((L < SHORT_S).mean()), 3),
                max=round(float(L.max()), 2))


# ═══════════════════════════════════════════════════════════════════════════
# render
# ═══════════════════════════════════════════════════════════════════════════
def _vf(s, W, H, fps):
    """scale FIRST, then the 16-bit LUT.

    ⚠️ the LUT on the 4K source cost ~15 s per shot (50 shots ≈ 12 min for a
       3-minute film).  A LUT is per-pixel, so running it on the 1080p frame
       gives the same picture at a quarter of the pixels.  The 16-bit hop
       stays (8-bit S-Log3 bands — zjl-podcast-grade).
    """
    c = s["clip"]
    look = []
    if c.get("log"):
        look += ["format=gbrp16le",
                 f"lut3d=file='{lut_path(s['ev'], (s.get('look') or {}).get('wg', 1.0))}'"
                 f":interp=tetrahedral"]
    if s.get("eq"):
        look.append(s["eq"])
    tail = [f"fps={fps}"] + _fades(s, fps) + ["format=yuv420p", "setsar=1"]
    ar_in = (c["w"] / c["h"]) if c["h"] else W / H
    if abs(ar_in - W / H) / (W / H) > 0.15:
        # vertical phone clip in a 16:9 film: blurred fill, never crop a face
        lk = ("," + ",".join(look)) if look else ""
        return (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos"
                f"{lk},split=2[fg][bg0];"
                f"[bg0]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},boxblur=40:2,eq=brightness=-0.06[bg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2," + ",".join(tail) + "[v]")
    parts = [f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos",
             f"crop={W}:{H}"] + look + tail
    return "[0:v]" + ",".join(parts) + "[v]"


def _fades(s, fps):
    """fade from/to black lives inside the first/last shot, so the joined film
    never needs a second 4K encode just for two fades."""
    d = s["n"] / fps
    out = []
    if s.get("fin"):
        out.append(f"fade=t=in:st=0:d={min(FADE_S, d / 2):.3f}")
    if s.get("fout"):
        f = min(FADE_S, d / 2)
        out.append(f"fade=t=out:st={d - f:.3f}:d={f:.3f}")
    return out


def render_shots(edl, W, H, work, fps=FPS, log=print, progress=None):
    """one video-only file per shot, identical encoder settings (concat copy)."""
    os.makedirs(work, exist_ok=True)
    br = "40M" if W * H > 1920 * 1080 else "14M"
    if edl:
        edl[0]["fin"] = True
        edl[-1]["fout"] = True
    outs = []
    t0 = time.time()
    for i, s in enumerate(edl):
        o = os.path.join(work, f"s{i:04d}.mp4")
        if not (os.path.exists(o) and os.path.getsize(o) > 1000):
            fc = _vf(s, W, H, fps)
            cmd = ["ffmpeg", "-v", "error", "-y", "-hwaccel", "videotoolbox",
                   "-ss", f"{s['a']:.3f}", "-i", s["clip"]["path"], "-filter_complex", fc, "-map", "[v]",
                   "-frames:v", str(s["n"]), "-an", *h264_args(br, crf=17),
                   "-g", str(fps * 2), "-video_track_timescale", "24000", o]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:     # hwaccel is optional (Linux worker)
                r = subprocess.run([x for x in cmd if x not in ("-hwaccel", "videotoolbox")],
                                   capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"shot {i} ({os.path.basename(s['clip']['path'])} "
                                   f"{s['a']:.2f}s): {r.stderr.strip()[-300:]}")
        outs.append(o)
        if progress and (i % 5 == 4 or i == len(edl) - 1):
            progress(i + 1, len(edl), time.time() - t0)
    return outs


def concat_video(files, out, work):
    lst = os.path.join(work, "concat.txt")
    with open(lst, "w") as f:
        for p in files:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", out], check=True)
    return out


def _read_audio(path, a, d):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, a):.4f}",
                          "-i", path, "-t", f"{d:.4f}", "-vn", "-ac", "2", "-ar",
                          str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2)
    n = int(round(d * SR))
    if len(x) < n:
        x = np.vstack([x, np.zeros((n - len(x), 2), np.float32)])
    return x[:n].copy()


def _rms_db(x):
    return 20 * math.log10(float(np.sqrt((x.astype(np.float64) ** 2).mean())) + 1e-9)


def mix(edl, total, work, log=print):
    """dialogue+ambience track and a talk-only track (for ASR), in numpy.

    ⚠️ numpy, not an ffmpeg graph: a 100-shot amix hits the input limit, and a
       concat of AAC segments drifts (zjl-render-spans).  Every shot is placed
       at its exact sample with a short overlap so no cut clicks.
    """
    N = int(round(total * SR)) + SR
    full = np.zeros((N, 2), np.float32)
    talk = np.zeros((N, 2), np.float32)
    for s in edl:
        c = s["clip"]
        if not c.get("audio"):
            continue
        xf = 0.02 if s["kind"] == "talk" else 0.25       # crossfade half-width
        pre = min(xf, s["a"])
        post = min(xf, max(0.0, c["dur"] - s["b"]))
        d = (s["b"] - s["a"]) + pre + post
        x = _read_audio(c["path"], s["a"] - pre, d)
        if not len(x):
            continue
        if s["kind"] == "talk":
            ref = _rms_db(x) if len(x) else -60
            g = max(-GAIN_CAP, min(GAIN_CAP, TALK_DB - ref))
        else:
            g = max(-GAIN_CAP, min(GAIN_CAP, AMB_DB - _rms_db(x)))
        x *= 10 ** (g / 20.0)
        nf = min(len(x), max(1, int(round((pre + xf) * SR))))
        nb = min(len(x), max(1, int(round((post + xf) * SR))))
        x[:nf] *= (0.5 - 0.5 * np.cos(np.linspace(0, math.pi, nf)))[:, None]
        x[len(x) - nb:] *= (0.5 + 0.5 * np.cos(np.linspace(0, math.pi, nb)))[:, None]
        i0 = int(round((s["o0"] - pre) * SR))
        j0 = max(0, i0)
        seg = x[j0 - i0:]
        seg = seg[: max(0, N - j0)]
        full[j0: j0 + len(seg)] += seg
        if s["kind"] == "talk":
            talk[j0: j0 + len(seg)] += seg
    n_out = int(round(total * SR))
    fl = int(FADE_S * SR)
    env = np.ones(n_out, np.float32)
    env[:fl] = np.linspace(0, 1, fl)
    env[-fl:] = np.linspace(1, 0, fl)
    full = full[:n_out] * env[:, None]
    talk = talk[:n_out]
    pk = float(np.abs(full).max() or 1.0)
    if pk > 0.98:
        full *= 0.98 / pk
    pa = os.path.join(work, "mix.wav"); pt = os.path.join(work, "talk.wav")
    _wav(pa, full); _wav(pt, talk)
    return pa, pt


def _wav(p, x):
    y = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(p, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(y.tobytes())


def _rm(p):
    """drop an intermediate as soon as the next one exists.

    ⚠️ every stage is a full-length film (≈340 MB per 3 min at 1080p, ~3× at
       4K); kept together they filled the Mac to 0.5 GB during testing.
    """
    try:
        if p and os.path.exists(p):
            os.remove(p)
    except OSError:
        pass


def mux(video, audio, out, total):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "256k", "-t", f"{total:.3f}", out], check=True)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# captions — language per audience
# ═══════════════════════════════════════════════════════════════════════════
SUB_LANGS = ("none", "my", "en", "ja_en")


def compact_talk(talk_wav, windows, out, gap=0.5):
    """only the talk windows, back to back → (wav, map).

    ⚠️ never send the full talk track: it is digital silence between talk
       shots, and Gemini writes plausible sentences into silence (river camp:
       "as an actress… thanks to the fans" over 0–50 s of nothing).
    `map` = [(compact_start, out_start, dur)] to turn ASR times back.
    """
    with wave.open(talk_wav) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, ch)
    parts, mp, t = [], [], 0.0
    g = np.zeros((int(gap * sr), ch), np.int16)
    for a, b in windows:
        seg = x[int(a * sr): int(b * sr)]
        if not len(seg):
            continue
        mp.append((t, a, len(seg) / sr))
        parts += [seg, g]
        t += len(seg) / sr + gap
    y = np.concatenate(parts) if parts else np.zeros((sr, ch), np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(y.tobytes())
    return out, mp


def uncompact(segs, mp):
    """ASR times on the compact wav → film times; anything that lands in a
    gap (i.e. outside every talk window) is dropped, not guessed."""
    out = []
    for x in segs:
        a, b = float(x["start"]), float(x["end"])
        mid = (a + b) / 2
        for c0, o0, d in mp:
            if c0 - 0.05 <= mid <= c0 + d + 0.05:
                a2 = o0 + max(0.0, a - c0); b2 = o0 + min(d, b - c0)
                if b2 - a2 >= 0.3:
                    out.append(dict(x, start=round(a2, 2), end=round(b2, 2)))
                break
    return out


def clean_line(t):
    t = STRAY.sub("", str(t or "")).strip()
    return re.sub(r"\s{2,}", " ", t)


def translate(lines, target, log=print):
    """Burmese/Japanese lines → target language, one output per input line."""
    if not lines:
        return []
    try:
        import gemguard as G
    except ImportError:
        from core import gemguard as G
    import urllib.request
    model = os.environ.get("IKKI_GEMINI_TEXT_MODEL", "gemini-3.1-flash-lite")
    name = {"en": "natural spoken English", "ja": "natural spoken Japanese"}[target]
    prompt = (f"Translate each numbered vlog subtitle line into {name}. Keep it "
              "short enough to read in the time it is on screen. Return ONLY a JSON "
              "array of strings, same count and order.\n\n"
              + "\n".join(f"{i + 1}. {t}" for i, t in enumerate(lines)))
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2,
                                 "responseMimeType": "application/json"}}
    for i in range(3):
        G.throttle()
        try:
            r = urllib.request.Request(G.endpoint(model), data=json.dumps(body).encode(),
                                       headers={"Content-Type": "application/json"},
                                       method="POST")
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
            arr = json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
            if len(arr) == len(lines):
                G.tally("cine_translate", True)
                return [clean_line(x) for x in arr]
            log(f"  ⚠️ ဘာသာပြန် အရေအတွက် မကိုက် ({len(arr)} ≠ {len(lines)}) — ထပ်ကြိုး")
        except Exception as e:
            G.log_fail("cine_translate", i + 1, 3, None, f"{type(e).__name__}: {e}")
            time.sleep(4 * (i + 1))
    G.tally("cine_translate", False)
    raise RuntimeError(f"ဘာသာပြန်ခြင်း မအောင်မြင် ({target})")


def split_line(text, max_chars):
    """long ASR sentences → single-line cards (the spec is one line)."""
    words = text.split()
    if len(text) <= max_chars or len(words) < 2:
        return [text]
    out, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


def timed_cards(segs, max_chars):
    """split each seg's time across its pieces by character share."""
    cards = []
    for s in segs:
        parts = split_line(s["text"], max_chars)
        tot = sum(len(p) for p in parts) or 1
        t = s["start"]
        for p in parts:
            d = (s["end"] - s["start"]) * len(p) / tot
            cards.append(dict(text=p, start=round(t, 2), end=round(t + d, 2)))
            t += d
    return cards


# ═══════════════════════════════════════════════════════════════════════════
# QC
# ═══════════════════════════════════════════════════════════════════════════
def qc(edl, out, rep, caps=None, lufs_target=-14.0, log=print):
    st = stats(edl)
    checks = []
    lf = st.get("long_frac", 0)
    ok_long = LONG_BAND[0] - 0.03 <= lf <= LONG_BAND[1] + 0.03
    why = ""
    if not ok_long and rep.get("long_possible", 0) < rep.get("long_wanted", 0):
        why = (f" — 10s ကျော် တည်ငြိမ်သော clip {rep.get('long_possible')} ခုသာ ရှိ "
               f"(လို {rep.get('long_wanted')})")
    checks.append(("long_takes", ok_long,
                   f"10s ကျော် shot {lf * 100:.0f}% (ပစ်မှတ် 12–18%){why}"))
    checks.append(("median_shot", 1.2 <= st.get("median", 0) <= 6.0,
                   f"shot အလယ် {st.get('median')}s (reference 1.5–5.6s)"))
    # loudness
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", out, "-af",
                        "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    mI = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    lu = float(mI[-1]) if mI else None
    checks.append(("loudness", lu is not None and abs(lu - lufs_target) <= 1.0,
                   f"{lu} LUFS (ပစ်မှတ် {lufs_target})"))
    # black frames outside the planned fades
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-vf",
                        "blackdetect=d=0.5:pix_th=0.06", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    blk = [(float(a), float(b)) for a, b in re.findall(
        r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    total = st.get("total", 0)
    blk = [x for x in blk if x[0] > FADE_S + 0.2 and x[1] < total - FADE_S - 0.2]
    checks.append(("black", not blk, f"အမည်း ကွက် {len(blk)} ခု"))
    if caps is not None:
        bad = [c["text"] for c in caps if STRAY.search(c["text"])]
        checks.append(("caption_tokens", not bad, f"စာတန်းထဲ label ပေါက် {len(bad)} ခု"))
    for k, ok, msg in checks:
        log(f"  {'✓' if ok else '⚠️'} QC {k} · {msg}")
    return dict(stats=st, checks=[dict(k=k, ok=bool(ok), msg=m) for k, ok, m in checks],
                lufs=lu)


# ═══════════════════════════════════════════════════════════════════════════
# the whole job
# ═══════════════════════════════════════════════════════════════════════════
def run(paths, out, work, W=1920, H=1080, pace="normal", teaser="auto",
        music=None, seed="", lufs=-14.0, sub_lang="none", captioner=None,
        target=None, log=print, stage=None, cache_dir=None):
    """paths → out.  `captioner(talk_wav, total, work, windows) → ([(mov, y)], caps) | None`
    is supplied by the worker (it owns ASR, fonts and the text renderer)."""
    stage = stage or (lambda n, name: None)
    t0 = time.time()
    os.makedirs(work, exist_ok=True)
    # ── ① analyse ──
    stage(1, "ingest")
    clips = []
    for i, p in enumerate(paths):
        c = analyse(p, cache_dir=cache_dir or work, log=log)
        clips.append(c)
        if c.get("ok"):
            log(f"  [{i + 1}/{len(paths)}] {os.path.basename(p)} · {c['dur']:.1f}s · "
                f"{c['w']}×{c['h']}@{c['fps']:.2f} · luma {c['stats']['p50']:.0f} · "
                f"talk {sum(b - a for a, b in c['talk']):.1f}s")
        else:
            log(f"  [{i + 1}/{len(paths)}] ⚠️ {os.path.basename(p)} — {c.get('why')}")
    groups = camera_groups(clips)
    for k, cs in groups.items():
        log(f"  camera {cs[0]['cam']} · {len(cs)} clip · "
            f"{'S-Log/flat ⇒ LUT' if cs[0]['log'] else 'Rec.709 ⇒ LUT မသုံး'}")
    log(f"  ① analyse {time.time() - t0:.0f}s")
    # ── ② plan ──
    stage(2, "plan")
    edl, rep = plan(clips, pace=pace, teaser=teaser, seed=seed, target=target, log=log)
    if not edl:
        raise RuntimeError("သုံးလို့ရသော shot မရှိပါ — clip များ တိုလွန်း သို့ မှုန်လွန်းသည်")
    for r_ in rep["rejected"]:
        log(f"  ✗ {r_[0]} — {r_[1]}")
    bed = None
    if music:
        try:
            try:
                import music as MU
            except ImportError:
                from core import music as MU
            trk, _it = MU.choose(music, seed)
            if trk:
                bed = beats(trk)
                if bed:
                    n = snap(edl, bed)
                    log(f"  ♪ {os.path.basename(trk)[:40]} · {bed['bpm']:.0f} BPM · "
                        f"B-roll ဖြတ်မှတ် {n} ခု beat ပေါ် ချ")
        except Exception as e:
            log(f"  ⚠️ beat မတွက်နိုင် ({type(e).__name__}: {e}) — beat မချိန်ဘဲ ဆက်")
    total = quantise(edl)
    st = stats(edl)
    log(f"  ② shot {st['shots']} · {total:.1f}s · အလယ် {st['median']}s · "
        f"10s+ {st['long_frac'] * 100:.0f}% · 2s- {st['short_frac'] * 100:.0f}% · "
        f"teaser {rep['teaser']}")
    # ── ③ grade decisions ──
    for s in edl:
        s["ev"], s["eq"], s["look"] = choose_grade(s["clip"], s["a"], s["b"])
    evs = [s["ev"] for s in edl if s["clip"].get("log")]
    if evs:
        from collections import Counter
        log("  ③ exposure (linear, LUT မတိုင်မီ) · " + " · ".join(
            f"{k:+.1f}EV×{v}" for k, v in sorted(Counter(evs).items())))
    # ── ④ render shots ──
    stage(3, "shots")
    sw = os.path.join(work, "shots")
    files = render_shots(edl, W, H, sw, log=log, progress=lambda i, n, dt: (
        stage(3, f"shot {i}/{n}"), log(f"  ④ shot {i}/{n} · {dt:.0f}s")))
    vid = concat_video(files, os.path.join(work, "video.mp4"), work)
    # ── ⑤ sound ──
    stage(4, "sound")
    amix, atalk = mix(edl, total, work, log=log)
    base = mux(vid, amix, os.path.join(work, "base.mp4"), total)
    _rm(vid)
    for f in files:
        try: os.remove(f)
        except OSError: pass
    # ── ⑥ captions ──
    caps = None
    stage(5, "captions")
    if sub_lang != "none" and captioner and any(s["kind"] == "talk" for s in edl):
        wins = [(s["o0"], s["o1"]) for s in edl if s["kind"] == "talk"]
        res = captioner(atalk, total, work, wins)
        if res:
            layers, caps = res            # [(alpha_mov, y_px), …]
            ov = os.path.join(work, "capd.mp4")
            ins, fc, last = [], [], "0:v"
            for i, (mov, y) in enumerate(layers):
                ins += ["-i", mov]
                fc.append(f"[{last}][{i + 1}:v]overlay=0:{int(y)}:eof_action=pass[c{i}]")
                last = f"c{i}"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, *ins,
                            "-filter_complex", ";".join(fc), "-map", f"[{last}]",
                            "-map", "0:a", *h264_args("40M" if W > 1920 else "14M", crf=17),
                            "-c:a", "copy", ov], check=True)
            _rm(base)
            base = ov
    elif sub_lang != "none":
        log("  ⓘ စကားပြော clip မရှိ ⇒ စာတန်း မထည့်")
    # ── ⑦ music + loudness ──
    stage(6, "music")
    pre = base
    if music:
        try:
            try:
                import music as MU
            except ImportError:
                from core import music as MU
            mv = os.path.join(work, "mus.mp4")
            MU.bed(base, mv, music, total, log=log, seed=seed)
            _rm(base)
            pre = mv
        except Exception as e:
            log(f"  ⚠️ သီချင်း မရ: {e}")
    try:
        import spans as SP
    except ImportError:
        from core import spans as SP
    stage(7, "render")
    SP.loudness(pre, out, lufs=lufs)
    _rm(pre)
    q = qc(edl, out, rep, caps=caps, lufs_target=lufs, log=log)
    log(f"  ✓ cinematic · {total:.1f}s · {time.time() - t0:.0f}s")
    shots = [dict(src=os.path.basename(s["clip"]["path"]), a=round(s["a"], 2),
                  b=round(s["b"], 2), o0=round(s["o0"], 2), o1=round(s["o1"], 2),
                  kind=s["kind"], ev=s.get("ev"), look=s.get("look"))
             for s in edl]
    return dict(dur=total, shots=shots, report=rep, qc=q,
                src_dur=round(sum(c.get("dur", 0) for c in clips), 2),
                caps=caps or [], secs=round(time.time() - t0, 1))
