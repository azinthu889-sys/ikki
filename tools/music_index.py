#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motionkit သီချင်း bank ကို **တိုင်းပြီး** catalog ဝင်ခွင့် ပေးသည်။

    python3 tools/music_index.py [--limit N] [--force]

⚠️ **ဂိတ် မလျှော့ရ** — `tests/test_music.py` က catalog item တိုင်းမှာ
   `lufs` · `true_peak` · **အတည်ပြုထားသော ကျော့နယ် (seam ≤ ၁ dB)** ရှိရမည်
   ဟု တောင်းသည်。 အကြောင်းရင်း (တိုင်းထားသည်) — သီချင်းတွေက အဆုံးမှာ တိတ်ပြီး
   အစက ကျယ်သဖြင့် ဖိုင် အစ↔အဆုံး ကျော့လျှင် **၉၃–၁၇၃ dB ထိုးကျသံ** ဖြစ်သည်。
⚠️ ⇒ ကိန်း **မမှန်းရ**。 တိုင်းပြီးသော သီချင်းကိုသာ `music._bank()` က
   catalog ထဲ ထည့်မည် — မတိုင်ရသေးသူ **အလိုအလျောက် ကျန်ခဲ့**သည်。
⚠️ ရလဒ်ကို `assets/music_loudness.json` မှာ သိမ်းသည် — တစ်ခါ တိုင်းပြီး
   နောက်တစ်ခါ ကျော်သည် (`--force` နဲ့ အတင်း ပြန်တိုင်းနိုင်)。
"""
import json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "core"))
OUT = os.path.join(HERE, "assets", "music_loudness.json")

SEAM_MAX = 1.0       # ကျော့ဆက် အသံ ခုန်မှု အများဆုံး (dB)
WIN_MIN = 20.0       # ကျော့နယ် အတိုဆုံး (စက္ကန့်)
EDGE = 0.35          # အစ/အဆုံး တိုင်းမည့် အကွာ (စက္ကန့်)


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def loud(path):
    """`(lufs, true_peak)` — `ebur128` နဲ့ တိုင်းသည်。"""
    r = _run(["ffmpeg", "-v", "info", "-nostats", "-i", path,
              "-af", "ebur128=peak=true", "-f", "null", "-"])
    txt = (r.stderr or "")
    i = txt.rfind("Integrated loudness")
    lu = tp = None
    if i >= 0:
        m = re.search(r"I:\s*(-?\d+\.?\d*)\s*LUFS", txt[i:])
        if m:
            lu = float(m.group(1))
    j = txt.rfind("True peak")
    if j >= 0:
        m = re.search(r"Peak:\s*(-?\d+\.?\d*)\s*dBFS", txt[j:])
        if m:
            tp = float(m.group(1))
    return lu, tp


def rms_at(path, t, dur=EDGE):
    """`t` စက္ကန့်မှ `dur` အတွင်း RMS (dBFS) — မရလျှင် `None`。"""
    # ⚠️ `-v error` သုံးလျှင် astats ရဲ့ စာကြောင်းတွေ **ဖုံးသွား**သည်
    #    (၂၀၂၆-၀၉-၂၄: RMS အမြဲ `None` ပြန်ခဲ့)。 `-v info` လိုသည်。
    r = _run(["ffmpeg", "-hide_banner", "-nostats", "-v", "info",
              "-ss", f"{max(0.0, t):.3f}",
              "-t", f"{dur:.3f}", "-i", path,
              "-af", "astats=metadata=1:reset=0", "-f", "null", "-"])
    m = re.findall(r"RMS level dB:\s*(-?\d+\.?\d*|-?inf)", r.stderr or "")
    if not m:
        return None
    v = m[-1]
    return -120.0 if "inf" in v else float(v)


def dur_of(path):
    r = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "csv=p=0", path])
    try:
        return float((r.stdout or "0").strip())
    except ValueError:
        return 0.0


def loop_of(path, d):
    """`{a, b, seam_db}` — အသံအဆင့် ကိုက်သော ကျော့နယ်; မတွေ့လျှင် `None`。

    ⚠️ သီချင်း အစ/အဆုံးက တိတ်တတ်သဖြင့် **အတွင်းပိုင်း**မှာ ရှာသည်。
    ⚠️ RMS ကို **တစ်ခါတည်း အမှတ် ၁၂ ခု** တိုင်းပြီး အတွဲ အားလုံးကို
       တွက်သည် — အတွဲတိုင်း ffmpeg ခေါ်လျှင် ၅၁၁ ပုဒ်အတွက် အချိန် မလောက်
       (တိုင်းပြီး: အတွဲလိုက် ~၈s ↔ profile ~၅s)。
    """
    if d < WIN_MIN + 2.0:
        return None
    starts = [x for x in (0.5, 1.0, 2.0, 4.0, 6.0, 8.0) if x + WIN_MIN < d]
    ends = [d - x for x in (0.5, 1.0, 2.0, 4.0, 6.0, 8.0) if d - x > WIN_MIN]
    ra = {a: rms_at(path, a) for a in starts}
    rb = {b: rms_at(path, b - EDGE) for b in ends}
    best = None
    for a, va in ra.items():
        if va is None:
            continue
        for b, vb in rb.items():
            if vb is None or b - a < WIN_MIN:
                continue
            seam = abs(va - vb)
            if best is None or seam < best["seam_db"]:
                # ⚠️ key အမည်က ရှိပြီးသား catalog နဲ့ **တူရမည်** —
                #    `{"start","end","seam_db"}` (test က `lp["start"]` ဖတ်သည်)。
                best = {"start": round(a, 2), "end": round(b, 2),
                        "seam_db": round(seam, 2)}
    return best if (best and best["seam_db"] <= SEAM_MAX) else None


def main():
    import music as MU
    force = "--force" in sys.argv
    lim = 0
    if "--limit" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--limit") + 1])
    try:
        cache = json.load(open(OUT, encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}

    jobs = []
    for folder in sorted(MU.MOOD):
        d = os.path.join(MU.MK_MUSIC, folder)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith(MU.AUD):
                jobs.append((f"{folder}/{fn}", os.path.join(d, fn)))
    if not force:
        jobs = [j for j in jobs if j[0] not in cache]
    if lim:
        jobs = jobs[:lim]
    print(f"တိုင်းမည် {len(jobs)} ပုဒ် · cache {len(cache)} ·"
          f" ကျော့နယ် seam ≤{SEAM_MAX} dB", flush=True)

    t0, ok = time.time(), 0
    for i, (key, path) in enumerate(jobs, 1):
        d = dur_of(path)
        lu, tp = loud(path)
        lp = loop_of(path, d)
        rec = {"lufs": lu, "true_peak": tp, "dur": round(d, 2), "loop": lp}
        cache[key] = rec
        ok += 1 if (lu is not None and tp is not None and lp) else 0
        print(f"  [{i:3d}/{len(jobs)}] {'✓' if (lu is not None and tp is not None and lp) else '✖'} "
              f"{key:34s} {d:6.1f}s  LUFS {lu if lu is not None else '—'}  "
              f"TP {tp if tp is not None else '—'}  "
              f"loop {'seam ' + str(lp['seam_db']) if lp else '—'}", flush=True)
        if i % 25 == 0:
            json.dump(cache, open(OUT, "w"), ensure_ascii=False, indent=1)
    json.dump(cache, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"\nအသုံးပြုနိုင် {ok}/{len(jobs)} · {time.time()-t0:.0f}s")
    print(f"ရေးပြီး — {OUT} ({len(cache)} ပုဒ်)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
