#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · dual-system — ဗီဒီယို (ကင်မရာ) + အသံ (recorder) ပေါင်းခြင်း。

⚠️ ဘာကြောင့် လိုလဲ (၂၀၂၆-၀၉-၁၉ တိုင်းချက်) — `C2942.MP4` ရဲ့ ကင်မရာ အသံက
   **−53.3 LUFS**、recorder က **−25.4 LUFS** ⇒ **၂၈ dB ကွာ**。 ကင်မရာ အသံနဲ့
   ထုတ်လိုက်တော့ သီချင်း (−28.6 LUFS) က စကားထက် ~၂၅ dB ကျယ်ပြီး
   **「ဘာမှ မကြားရ」** ဖြစ်ခဲ့သည် (Zin)。

⚠️ offset ကို **မှန်းလို့ မရ** — cross-correlation နဲ့ တိုင်းရမည်、
   ပြီးတော့ **ဂိတ် မအောင်လျှင် ငြင်းရမည်**。 မှားညှိလျှင် အသံနဲ့ ပုံ လွဲပြီး
   ဗီဒီယို တစ်ခုလုံး ပျက်သည် — မှန်းပြီး ဆက်လုပ်တာ ဘယ်တော့မှ မလုပ်ရ。
"""
import os, subprocess

SR = 16000
FRAME = 0.02
MIN_CORR = 0.50      # ဤအောက် ⇒ အသံ ၂ ခု မတူ ⇒ ငြင်း
MAX_DRIFT = 0.10     # window အချင်းချင်း offset ကွာဟမှု ကန့်သတ် (စက္ကန့်)
WIN = 20.0           # window အရှည်


def _band(path, ss=None, t=None):
    """စကား band (300–3400Hz) dB envelope — 20ms frame。"""
    import numpy as np
    cmd = ["ffmpeg", "-v", "error"]
    if ss is not None: cmd += ["-ss", str(ss)]
    if t is not None: cmd += ["-t", str(t)]
    cmd += ["-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)
    h = int(SR*FRAME); n = len(x)//h
    if n < 4: return np.zeros(0)
    fr = x[:n*h].reshape(n, h)*np.hanning(h)
    F = np.abs(np.fft.rfft(fr, axis=1)); f = np.fft.rfftfreq(h, 1/SR)
    return 20*np.log10(F[:, (f >= 300) & (f <= 3400)].sum(1) + 1e-9)


def offset(video, audio, log=print):
    """(offset_s, ok, info) — audio က video ထက် ဘယ်လောက် စော/နောက်ကျလဲ。

    `offset_s` = video အချိန် `t` ရဲ့ အသံသည် audio ဖိုင်ရဲ့ `t + offset_s`。
    ⚠️ **ဂိတ် ၂ ခု** — corr အလယ်တန်ဖိုး ≥ MIN_CORR · drift ≤ MAX_DRIFT。
    """
    import numpy as np
    A = _band(video); B = _band(audio)
    if len(A) < 100 or len(B) < 100:
        return 0.0, False, {"why": "အသံ တိုလွန်း/မဖတ်နိုင်"}
    dur = len(A)*FRAME
    b = B - B.mean()
    res = []
    for frac in (0.15, 0.30, 0.45, 0.60, 0.75):
        t = dur*frac
        i = int(t/FRAME); w = A[i:i+int(WIN/FRAME)]
        if len(w) < 200: continue
        a = w - w.mean(); nv = np.linalg.norm(a)
        if nv < 1e-6: continue
        a = a/nv; n = len(a)
        cs = np.cumsum(np.concatenate([[0.0], b])); cs2 = np.cumsum(np.concatenate([[0.0], b*b]))
        s = cs[n:]-cs[:-n]; s2 = cs2[n:]-cs2[:-n]
        c = np.correlate(b, a, "valid")/np.sqrt(np.maximum(s2-s*s/n, 1e-9))
        k = int(np.argmax(c))
        res.append((t, k*FRAME - t, float(c[k])))
    if len(res) < 3:
        return 0.0, False, {"why": "window မလုံလောက်"}
    good = [(o, c) for _, o, c in res if c >= MIN_CORR]
    cm = float(np.median([c for _, _, c in res]))
    if len(good) < 3:
        return 0.0, False, {"why": f"အသံ ၂ ခု မကိုက် (corr အလယ် {cm:.2f} < {MIN_CORR})",
                            "corr": round(cm, 3), "windows": len(res)}
    offs = [o for o, _ in good]
    med = float(np.median(offs))
    drift = float(max(abs(o-med) for o in offs))
    info = {"corr": round(cm, 3), "drift": round(drift, 3),
            "windows": len(res), "ok_windows": len(good)}
    if drift > MAX_DRIFT:
        info["why"] = f"drift {drift:.2f}s > {MAX_DRIFT}s — နာရီ လွဲနေသည်"
        return round(med, 3), False, info
    log(f"  dual-system offset **{med:+.2f}s** · corr {cm:.2f} · drift {drift*1000:.0f}ms "
        f"· window {len(good)}/{len(res)}")
    return round(med, 3), True, info


def mux(video, audio, out, off, lufs=-18.0, log=print):
    """ဗီဒီယို + recorder အသံ ပေါင်းသည် (offset ညှိပြီး · loudnorm)。

    `off > 0` ⇒ audio ဖိုင်က နောက်ကျ ⇒ audio ကို **ရှေ့ဆုတ်** (`-ss off`)。
    `off < 0` ⇒ audio က စော ⇒ **နှောင့်** (`adelay`)。
    """
    pre = []; af = []
    if off > 0: pre = ["-ss", f"{off:.3f}"]
    elif off < 0: af.append(f"adelay={int(round(-off*1000))}|{int(round(-off*1000))}")
    af += ["aformat=sample_rates=48000:channel_layouts=stereo",
           f"loudnorm=I={lufs}:TP=-1.5:LRA=11"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video] + pre +
                   ["-i", audio, "-filter_complex", f"[1:a]{','.join(af)}[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True)
    log(f"  အသံ ပေါင်းပြီး → {os.path.basename(out)} ({lufs:+.0f} LUFS)")
    return out


def loudness(path):
    """LUFS — ဘယ်အသံ သုံးမလဲ ဆုံးဖြတ်ရန်。"""
    import json as _j, re as _re
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                        "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = _re.search(r"\{[^{}]*input_i[^{}]*\}", r.stderr, _re.S)
    try: return float(_j.loads(m.group(0))["input_i"]) if m else None
    except Exception: return None
