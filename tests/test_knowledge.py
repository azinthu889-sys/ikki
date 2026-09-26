# -*- coding: utf-8 -*-
"""Knowledge Sharing engine (`core/knowledge.py`) — Gemini **မခေါ်**။

① AI အဖြေ စစ်ခြင်း (ဖန်လာသော number/jp/panel ဖယ်)
② scheduler — ref 「အသစ် ၄ ပုဒ်」 ကိန်း (share 0.34 · gap ≥6s · cold open)
③ bake — frame ရေ မပြောင်း · **အသံ byte တူ** · panel pixel · B-roll အစားထိုး
"""
import hashlib, os, subprocess, sys, tempfile

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, "core"))
import knowledge as K  # noqa: E402

OK = FAIL = 0


def ck(name, cond, extra=""):
    global OK, FAIL
    if cond:
        OK += 1
    else:
        FAIL += 1
        print(f"  ✗ {name}  {extra}")


def lines_every(dur, step=3.0):
    out, t, i = [], 0.4, 0
    while t + step <= dur:
        out.append(dict(start=round(t, 2), end=round(t + step - 0.3, 2),
                        text=f"စာကြောင်း {i} ဂျပန်မှာ နေထိုင်ခြင်း"))
        t += step; i += 1
    return out


# ① validate
L = lines_every(60)
notes, bad = K.validate_notes([
    {"line": 1, "kind": "panel", "text": "ပိုက်ဆံ စုခြင်းရဲ့ ရည်ရွယ်ချက်"},
    {"line": 2, "kind": "number", "num": "အများကြီး"},          # ဂဏန်းမဲ့ ⇒ ဖယ်
    {"line": 3, "kind": "number", "num": "၂၀၂၂"},                # ⇒ 2022
    {"line": 4, "kind": "jp", "jp": "omotenashi"},             # ဂျပန်စာမဲ့ ⇒ ဖယ်
    {"line": 5, "kind": "jp", "jp": "おもてなし", "romaji": "omotenashi"},
    {"line": 6, "kind": "chart", "text": "x"},                 # စာရင်းပြင်ပ ⇒ ဖယ်
    {"line": 999, "kind": "panel", "text": "abc"},             # index မှား ⇒ ဖယ်
    {"line": 1, "kind": "no", "text": "dup"},                  # ထပ် ⇒ ဖယ်
], L)
ck("validate keeps 3", set(notes) == {0, 2, 4}, notes)
ck("validate bad 5", bad == 5, bad)
ck("burmese digits → ascii", notes.get(2, {}).get("num") == "2022", notes.get(2))

h = K.heuristic_notes([dict(start=0, end=2, text="おもてなし ဆိုတာ"),
                       dict(start=2, end=4, text="၂၀၂၂ ခုနှစ်မှာ"),
                       dict(start=4, end=6, text="ပုံမှန် စကား")])
ck("heuristic jp", h.get(0, {}).get("kind") == "jp", h)
ck("heuristic number", h.get(1, {}).get("num", "").startswith("2022"), h)
ck("heuristic no panel", all(v["kind"] != "panel" for v in h.values()), h)

# ② schedule — ၈ မိနစ် · B-roll hit ၆၀%
DUR = 480.0
L = lines_every(DUR)
clips = [dict(path=f"/x/c{i}.mp4", dur=8.0) for i in range(400)]
hits = {i: [(clips[i], 9.0)] for i in range(len(L)) if i % 5 in (0, 1, 3)}
notes = {i: dict(kind="panel", text="အဓိက အချက် တစ်ခု ဖြစ်ပါတယ်") for i in range(20, len(L), 25)}
notes[40] = dict(kind="number", num="2022")
notes[70] = dict(kind="jp", jp="めいし", romaji="meishi")
ev = K.schedule(L, DUR, notes, hits)
st = K.stats(ev, DUR)
ck("share ≈ target", 0.28 <= st["share"] <= K.SPEC["share_max"], st)
ck("rate in ref band", 1.2 <= st["rate"] <= 4.0, st)
ck("max talk ≤ gap_max", st["max_talk"] <= K.SPEC["gap_max"], st)
ck("cold open at 0", ev[0]["at"] == 0.0 and ev[0].get("cold") and ev[0]["dur"] >= 8.0, ev[0])
ck("panels scheduled", st["n_panel"] >= 3, st)
ck("overlays scheduled", st["n_over"] >= 1, st)
cut = [e for e in ev if e["kind"] in K.CUTAWAY]
gaps = [cut[i + 1]["at"] - (cut[i]["at"] + cut[i]["dur"]) for i in range(len(cut) - 1)]
ck("no overlap + gap_min", all(g >= K.SPEC["gap_min"] - 1e-6 for g in gaps), min(gaps))
ck("tail kept", all(e["at"] + e["dur"] <= DUR - K.SPEC["tail"] + 1e-6 for e in cut))
ck("event len in band", all(e["dur"] <= K.SPEC["broll_len"][1] + 1e-6 for e in cut if e["kind"] == "broll" and not e.get("cold")))
paths = [c["path"] for e in ev if e["kind"] == "broll" for c, _d in e["clips"]]
ck("clip used once", len(paths) == len(set(paths)))
ck("deterministic", K.schedule(L, DUR, notes, hits) == ev)
# B-roll လုံးဝ မရ — panel ပဲ · မပျက်
ev0 = K.schedule(L, DUR, notes, {})
st0 = K.stats(ev0, DUR)
ck("no hits → panels only", st0["n_broll"] == 0 and st0["n_panel"] >= 3, st0)
ck("checks advisory low share", any(c["key"] == "kn_share_min" and c.get("advisory")
                                    for c in K.checks(dict(stats=st0, dur=DUR))))
ck("checks max share blocks", not next(c for c in K.checks(dict(stats=dict(st, share=0.6), dur=DUR))
                                       if c["key"] == "kn_share_max")["ok"])
# ကြာချိန်တို — cold open မလုပ်
evs = K.schedule(lines_every(60), 60.0, {}, {i: [(clips[i], 9)] for i in range(18)})
ck("short: no cold open", not any(e.get("cold") for e in evs), evs[:1])
# hide_caps
P = dict(events=[dict(kind="panel", at=10.0, dur=5.0, text="x")])
kept = K.hide_caps([dict(start=9, end=11, text="a"), dict(start=16, end=18, text="b")], P)
ck("hide caps under panel", [c["text"] for c in kept] == ["b"], kept)


# ③ bake (ffmpeg · cttext)
def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def nframes(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0",
                        "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return int(r.stdout.strip().split(",")[0])


def amd5(p):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-map", "0:a", "-c", "copy",
                        "-f", "md5", "-"], capture_output=True, text=True)
    return r.stdout.strip()


def frame_at(p, t, W, H):
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", p, "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(H, W, 3).astype(int)


if os.path.exists(K.SL.CTBIN):
    W, H, FPS = 640, 360, 30
    d = tempfile.mkdtemp(prefix="kn_")
    cutv = os.path.join(d, "cut.mp4")
    # 「ပြောသူ」 = မီးခိုးရောင် + အလယ်မှာ အပြာ ပုံ · အသံ sine
    ff("-f", "lavfi", "-i", f"color=c=0x606060:s={W}x{H}:r={FPS}:d=40",
       "-f", "lavfi", "-i", "sine=f=440:d=40",
       "-vf", f"drawbox=x={W//2-60}:y=60:w=120:h=240:color=0x2040C0:t=fill",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", cutv)
    cps = []
    for i, col in enumerate(("red", "green", "yellow")):
        p = os.path.join(d, f"b{i}.mp4")
        ff("-f", "lavfi", "-i", f"color=c={col}:s=1280x720:r=30:d=6", "-c:v", "libx264",
           "-pix_fmt", "yuv420p", p)
        cps.append(dict(path=p, dur=6.0))
    P = dict(dur=40.0, stats={}, events=[
        dict(kind="broll", at=0.0, dur=7.0, clips=[(cps[0], 3.5), (cps[1], 3.5)], cold=True),
        dict(kind="panel", at=14.0, dur=5.0, text="ပိုက်ဆံ စုတာက ရည်ရွယ်ချက် မဟုတ်ဘူး"),
        dict(kind="number", at=24.0, dur=3.0, num="2022"),
        dict(kind="jp", at=29.0, dur=3.0, jp="おもてなし", romaji="omotenashi"),
        dict(kind="broll", at=33.0, dur=4.0, clips=[(cps[2], 2.0)]),   # clip တို → tpad
    ])
    out = K.bake(P, cutv, d, dict(W=W, H=H), dict(fps=FPS, mmf="Pyidaungsu-Bold"),
                 log=lambda *_: None)
    ck("bake frame count", nframes(out) == nframes(cutv), (nframes(out), nframes(cutv)))
    ck("bake audio untouched", amd5(out) == amd5(cutv) and amd5(out))
    f = frame_at(out, 2.0, W, H)
    ck("cold open = broll red", f[H // 2, W // 2, 0] > 180 and f[H // 2, W // 2, 1] < 80, f[H // 2, W // 2])
    f = frame_at(out, 5.5, W, H)
    ck("montage 2nd clip green", f[H // 2, W // 2, 1] > 90 and f[H // 2, W // 2, 0] < 80, f[H // 2, W // 2])
    f = frame_at(out, 16.0, W, H)
    pw = int(W * K.PAPER_W)
    paper = f[20:H - 20, 10:pw - 10].reshape(-1, 3)
    ck("panel paper colour", abs(paper.mean(0) - K.PAPER_RGB).max() < 22, paper.mean(0))
    ck("panel has ink", (paper.mean(1) < 90).mean() > 0.004, (paper.mean(1) < 90).mean())
    blue = f[:, pw:][..., 2] - f[:, pw:][..., 0]
    xs = (blue > 80).any(0).nonzero()[0]
    ck("speaker in right half", len(xs) and abs((pw + xs.mean()) - (pw + (W - pw) / 2)) < W * 0.08,
       (pw + xs.mean()) if len(xs) else None)
    f = frame_at(out, 11.0, W, H)
    ck("talk untouched", abs(f[5, 5] - 0x60).max() < 12, f[5, 5])
    f = frame_at(out, 25.2, W, H)
    ck("number overlay drawn", (f[..., 0] - f[..., 2] > 80).mean() > 0.01)
    f = frame_at(out, 36.5, W, H)
    ck("short clip padded (yellow)", f[H // 2, W // 2, 0] > 180 and f[H // 2, W // 2, 1] > 180, f[H // 2, W // 2])
else:
    print("  (cttext မရှိ — bake test ကျော်)")

print(f"knowledge: {OK} ok · {FAIL} fail")
sys.exit(1 if FAIL else 0)
