#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · အသံ တိုင်းတာခြင်း — zjl-podcast-edit/smoothcut.py မှ ပြန်သုံးသည်。

⚠️ ဤနေရာက ဤ product ၏ အသက်ဖြစ်သည်。 ဖြတ်မှတ်ကို **တိုင်းထားသော တိတ်ဆိတ်မှု
   အထဲမှာသာ** ချရမည် — စာသားကနေ အချိန် ခန့်မှန်းလျှင် ၉၆ ခုမှာ ၄၉ ခု (၅၁%)
   စကားပြောနေတုန်း ကျခဲ့သည်။ တိုင်းယူတော့ **၀ / ၈၈**。
"""
import os, subprocess, tempfile

WIN = 320   # ⚠️ asetnsamples ဖြင့် window ကို ကိုယ်တိုင် ပုံသေချရမည် —
            #    astats=length= က ffmpeg version အလိုက် မတူ (Alpine 6.1 → 128ms,
            #    Homebrew 9.0 → 64ms)。 ထို ကွာဟမှုက စာတန်းကို 0.36s ရွှေ့ခဲ့သည်。

def band(path, hp=180, lp=3400):
    """ဘန်းတစ်ခုအတွင်း RMS (t, dB) စာရင်း — စကားသံ ဘန်းက 180–3400 Hz"""
    fd, meta = tempfile.mkstemp(suffix=".txt"); os.close(fd)
    try:
        subprocess.run(["ffmpeg","-v","error","-i",path,"-vn","-af",
            f"highpass=f={hp},lowpass=f={lp},aresample=16000,"
            f"asetnsamples=n={WIN}:p=0,astats=metadata=1:reset=1,"
            f"ametadata=print:key=lavfi.astats.Overall.RMS_level:file={meta}",
            "-f","null","-"], capture_output=True)
        out=[]; t=None
        for line in open(meta, encoding="utf-8", errors="replace"):
            line=line.strip()
            if "pts_time:" in line:
                try: t=float(line.split("pts_time:")[1].split()[0])
                except (IndexError, ValueError): pass
            elif line.startswith("lavfi.astats.Overall.RMS_level=") and t is not None:
                try: out.append((t, float(line.split("=",1)[1])))
                except ValueError: out.append((t, -120.0))
        return out
    finally:
        try: os.unlink(meta)
        except OSError: pass

def threshold(track, over=8.0):
    """ကြမ်းပြင် အသံအဆင့် + over dB — ဖိုင်တစ်ခုချင်းစီအလိုက် ကိုယ်တိုင် ရှာသည်"""
    vals = sorted(v for _, v in track if v > -120)
    if not vals: return -60.0
    return vals[int(len(vals)*0.10)] + over

def gaps(track, thr, min_len=0.28):
    """တိတ်ဆိတ်မှုများ (start, end, mid) — ဖြတ်ခွင့်ရှိသော တစ်ခုတည်းသော နေရာ"""
    step = track[1][0]-track[0][0] if len(track)>1 else 0.02
    out=[]; s=None
    for t,v in track:
        if v < thr and s is None: s=t
        elif v >= thr and s is not None:
            if t-s >= min_len: out.append((s, t, (s+t)/2))
            s=None
    if s is not None:
        e=track[-1][0]+step
        if e-s >= min_len: out.append((s, e, (s+e)/2))
    return out

def speaking(track, thr):
    """စကားပြောနေသော ကြားကာလများ — ဖြတ်ချက် စစ်ဆေးရန်"""
    out=[]; s=None
    for t,v in track:
        if v >= thr and s is None: s=t
        elif v < thr and s is not None: out.append((s,t)); s=None
    if s is not None: out.append((s, track[-1][0]))
    return out

def in_speech(t, sp, pad=0.0):
    for a,b in sp:
        if a-pad <= t <= b+pad: return True
    return False


# ══ SKILL: ikki-cut-engine (calibrated 2026-09-13) ═══════════
# ⚠️ အောက်ပါတို့ကို `happiness 3` calibration မှ ယူသည်。 အရင် နည်းလမ်း
#    (band-pass RMS + p10+8) က **အက္ခရာကြား နိမ့်ချက်**တွေကို တိတ်ဆိတ်မှုအဖြစ်
#    မှတ်သည် — ZAE take မှာ ကွက်လပ် ၂၄၅ ခု တွေ့ပြီး အသစ်နည်းက ၅၅ ခုသာ
#    တွေ့သည် (တိုင်းပြီး)。 ၇-frame (၁၄၀ms) smoothing က အဲဒါကို ရပ်သည်。
#    **ဒီ window ကို မလျှော့ရ** — လျှော့လျှင် စကားလုံးတစ်လုံးက ၃ ပိုင်း ကွဲပြီး
#    ဖြတ်မှတ်က စကားလုံးအလယ် ကျသည်。
FRAME = 0.02

def analyse(path, frame=FRAME):
    """(db, voice, dur) — 20ms frame · full-band RMS + 300–3400Hz အချိုး。"""
    import numpy as np
    raw = subprocess.run(["ffmpeg","-v","error","-i",path,"-ac","1","-ar","16000",
                          "-f","f32le","-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    sr = 16000; h = int(sr*frame); n = len(x)//h
    if n < 2: return np.array([]), np.array([]), 0.0
    fr = x[:n*h].reshape(n, h)
    db = 20*np.log10(np.sqrt((fr**2).mean(1)+1e-12)+1e-12)
    F = np.abs(np.fft.rfft(fr*np.hanning(h), axis=1))
    f = np.fft.rfftfreq(h, 1/sr)
    voice = F[:, (f >= 300) & (f <= 3400)].sum(1) / (F.sum(1)+1e-9)
    return db, voice, len(x)/sr

AROLL_RANGE_DB = 20.0
# ⚠️ ၂၀၂၆-၀၉-၁၆ တိုင်းချက် (ဖိုင် ၂၅ ခု · Zin ဆုံးဖြတ်) —
#    p95 > −30  : **ခွဲခြားနိုင်စွမ်း မရှိ** — စကားပါသော ဖိုင်များ −၁၈.၈ … −၆၅.၃ ·
#                 စကားမပါသူ −၄၀.၉ … −၅၈.၅ ⇒ အပြည့် ထပ်。 recorder သီးသန့်
#                 သုံးလျှင် ကင်မရာအသံ တိုးနေတာ သဘာဝ ⇒ level က မှားသော ပေတံ。
#    voice > .30: **ပြောင်းပြန်** — B-roll က ပိုမြင့် (၀.၆၇–၀.၈၄ vs ၀.၄၉–၀.၇၂)。
#    range      : ခွဲနိုင်သည် — ≥၂၀ တစ်ခုတည်းနဲ့ မှန် ၂၄/၂၅ (ယခင် ၃ ခုပေါင်း ၁၇/၂၅)。
#                 ASR နဲ့ ဝါကျ အစစ် ထွက်ပြီးသား ဖိုင် ၆/၆ အောင်。
#    ⚠️ ဤကိန်းသေက calib ဖိုင်ထဲ မဟုတ် (ယခင် −၃၀/၁၃/၀.၃၀ နည်းတူ module ထဲ)。
def classify(db, voice):
    """A-roll / B-roll — **range (p95−p10)** တစ်ခုတည်းနဲ့ ခွဲသည်。"""
    import numpy as np
    if len(db) == 0: return "broll", {}
    p95, p10 = float(np.percentile(db,95)), float(np.percentile(db,10))
    vm = float(np.median(voice))
    ok = (p95-p10) >= AROLL_RANGE_DB
    return ("aroll" if ok else "broll",
            dict(p95_db=round(p95,1), range_db=round(p95-p10,1), voice_ratio=round(vm,2),
                 rule=f"range>={AROLL_RANGE_DB}"))

def thr_of(db):
    """max(p95−20, p10+7) — နှစ်ခုလုံး လိုသည်。

    p95−20 က ပြောသူရဲ့ အဆင့်ကို လိုက်သည် (တိုးတိုးပြောလျှင် တိတ်ဆိတ်မှု
    မမှတ်မိစေရန်); p10+7 က ဆူညံသော အခန်းက threshold ကို မမျိုစေရန် ကြမ်းပြင်。
    """
    import numpy as np
    if len(db) == 0: return -60.0
    return max(float(np.percentile(db,95))-20, float(np.percentile(db,10))+7)

def mask(db, voice, thr, win=7, hit=0.35):
    import numpy as np
    m = (db > thr) & (voice > 0.25)
    return np.convolve(m.astype(float), np.ones(win)/win, "same") > hit

def runs(m, want=True, frame=FRAME):
    """mask ထဲက ဆက်တိုက် အပိုင်းများ (start, end)。"""
    out=[]; cur=None
    for i, v in enumerate(m):
        if bool(v) == want and cur is None: cur = i
        elif bool(v) != want and cur is not None:
            out.append((cur*frame, i*frame)); cur = None
    if cur is not None: out.append((cur*frame, len(m)*frame))
    return out

def as_gaps(sil, min_len=0.24):
    """`speech()` ရဲ့ (start,end) → `gaps()` ပုံစံ (start,end,mid)。

    ⚠️ တိတ်ဆိတ်မှု မြေပုံကို **တစ်ခုတည်း** ထားရန်。 အရင်က `asr.burmese()` က
       `band/threshold/gaps` · `cut.plan()` က `speech()` (analyse/mask/runs) ဖြင့်
       **သီးသန့် တွက်**ခဲ့ကြသည် ⇒ ASR က မြေပုံ A ပေါ် snap လုပ်ပြီး cut က
       မြေပုံ B သုံးလျှင် transcript နယ်နိမိတ်နှင့် ဖြတ်မှတ် ကွဲသွားမည်。
       ⇒ စံ = `speech()` · ကျန်ပုံစံများကို ဤနေရာမှ ဆင်းသက်စေသည်。
    """
    return [(a, b, (a + b) / 2.0) for a, b in (sil or []) if b - a >= min_len]


def splits(segs, sil, min_gap=0.20, margin=0.15):
    """{ဝါကျ index: [ဖြတ်မှတ် အချိန်, …]} — **ဝါကျ အတွင်း** ဖြတ်လို့ရသော နေရာများ。

    ⚠️ စကားလုံး အချိန်မှတ် (ASR/forced-align) ကို **မသုံးပါ** — ၂၀၂၆-၀၉-၁၈ တိုင်းချက်:
       MMS_FA နယ်နိမိတ် ၆ ခုမှ ၅ ခု စကား run ထဲ ကျသည် (−20 dB အထိ) ⇒ ဖြတ်၍ မရ。
       ဤနေရာမှာ **တကယ့် တိတ်ဆိတ်မှု** ကိုသာ သုံးသည် ⇒ ဖြတ်လျှင် F2 = ၀ အာမခံ。
    ⚠️ `margin` — ဝါကျ အစွန်းနား ကွက်လပ်က ဝါကျကြား ကွက်လပ် ဖြစ်တတ်၍ ချန်သည်。
    """
    out = {}
    for n, s in enumerate(segs or []):
        a0 = float(s.get("start") or 0); b0 = float(s.get("end") or 0)
        if b0 - a0 <= 2*margin: continue
        pts = [round((x + y) / 2.0, 3) for x, y in (sil or [])
               if y - x >= min_gap and x > a0 + margin and y < b0 - margin]
        if pts: out[n] = pts
    return out


def sounds(path, sp=None, min_ms=80, pad=0.02):
    """[(start, end, peak_db), …] — **စကား မဟုတ်သော အသံ ဖြစ်ရပ်**。

    ချောင်းဆိုးသံ · ခေါက်သံ · ကုလားထိုင် တွန့်သံ · အသက်ရှူသံ စသည်。
    ⚠️ `db > thr` **ဖြစ်ပြီး** `voice ≤ 0.25` (စကား band မဟုတ်) ဆိုမှ ⇒
       စကားသံကို ဤနေရာမှာ မဖမ်းမိစေရ。
    ⚠️ စကား run **ထဲ ကျနေလျှင် ချန်**သည် — ပြောရင်း ထွက်တဲ့ အသံက
       သီးသန့် ဖြစ်ရပ် မဟုတ်、ဖြတ်၍လည်း မရ。
    """
    import numpy as np
    db, voice, dur = analyse(path)
    if len(db) == 0: return []
    thr = thr_of(db)
    m = (db > thr) & (voice <= 0.25)
    m = np.convolve(m.astype(float), np.ones(3)/3, "same") > 0.5
    out = []
    for a, b in runs(m, True):
        if b - a < min_ms/1000.0: continue
        mid = (a + b) / 2.0
        if sp and in_speech(mid, sp): continue
        i0, i1 = int(a/FRAME), max(int(a/FRAME)+1, int(b/FRAME))
        out.append((round(max(0.0, a-pad), 3), round(b+pad, 3),
                    round(float(db[i0:i1].max()), 1)))
    return out


def speech(path):
    """(sp, sil, dur, ev, cls) — SKILL အတိုင်း တစ်ကြိမ်တည်း တွက်သည်。"""
    db, voice, dur = analyse(path)
    if len(db) == 0: return [], [], 0.0, {}, "broll"
    cls, ev = classify(db, voice)
    thr = thr_of(db)
    m = mask(db, voice, thr)
    return runs(m, True), runs(m, False), dur, dict(ev, thr_db=round(thr,1)), cls
