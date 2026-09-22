# -*- coding: utf-8 -*-
"""Reference Video **Style DNA** — sample ဗီဒီယိုကနေ ပုံစံ သွင်ပြင် တိုင်းသည်。

⚠️ **လမ်းကြောင်းသာ · ပုံတူ မဟုတ်** (Zin ၂၀၂၆-၀၉-၂၁)。 reference ရဲ့ ရုပ်ပုံ ·
   တီးလုံး · အသံ · စာတန်း စာသား · logo · graphic ကို **ဘယ်တော့မှ မယူရ**。
   ဤ module က **ကိန်းဂဏန်း**သာ ထုတ်သည် — media တစ်ခုမှ မကူးပါ。
⚠️ **မသိတာကို မသိဟု ပြရမည်**。 တိုင်းလို့ မရသော အချက်ကို `None` ထားပြီး
   label က `"unknown"` ဖြစ်ရမည် — ခန့်မှန်းပြီး တိကျသလို ပြခြင်းက
   သုံးစွဲသူကို လိမ်ရာ ကျသည်。
⚠️ **ဂိတ် မလျှော့ရ** — `apply_to()` က `recipes.BOUNDS` ဘောင်အတွင်းသာ
   ပြောင်းသည်。 brand · format · ဖောင့် · စာတန်း ဖတ်ရလွယ်မှု · အတည်ပြုပြီးသော
   ဖြတ်ချက် တွေကို **မထိရ**。
"""
import json, math, os, subprocess, tempfile

RANGE_MIN = 15.0          # ဤအောက် ⇒ တိုင်းလို့ မလုံလောက်
RANGE_MAX = 180.0         # ဤအထက် ⇒ သုံးစွဲသူ အပိုင်း ရွေးရမည် (တိတ်တဆိတ် မယူရ)
SAMPLE_W, SAMPLE_H = 192, 108
MOT_W, MOT_H = 96, 54
CAP_LO, CAP_HI = 0.68, 0.96      # စာတန်း ရှိတတ်သော အကွက် (frame အမြင့်၏)
MID_LO, MID_HI = 0.25, 0.60      # နှိုင်းယှဉ်ဖို့ အလယ် အကွက်


def _run(args):
    return subprocess.run(args, capture_output=True, text=True)


def probe(path):
    """ကြာချိန် · fps · အရွယ် · အချိုး。"""
    o = _run(["ffprobe", "-v", "error", "-select_streams", "v:0",
              "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
              "-show_entries", "format=duration", "-of", "json", path]).stdout
    j = json.loads(o or "{}")
    st = (j.get("streams") or [{}])[0]
    w, h = int(st.get("width") or 0), int(st.get("height") or 0)
    fps = None
    try:
        n, d = str(st.get("r_frame_rate") or "0/1").split("/")
        fps = round(float(n) / float(d), 3) if float(d) else None
    except Exception:
        fps = None
    dur = None
    try: dur = round(float((j.get("format") or {}).get("duration")), 2)
    except Exception: dur = None
    asp = None
    if w and h:
        r = w / float(h)
        # ⚠️ အနီးစပ်ဆုံး စံ အချိုး — မကိုက်လျှင် **မှန်းမပြရ**
        for key, val in (("16:9", 16/9), ("9:16", 9/16), ("4:5", 4/5),
                         ("1:1", 1.0), ("3:4", 3/4), ("4:3", 4/3), ("21:9", 21/9)):
            if abs(r - val) / val < 0.04: asp = key; break
    return dict(w=w, h=h, fps=fps, dur=dur, aspect=asp, ratio=round(w/h, 4) if h else None)


def _gray(path, a, b, w, h):
    """[frame] — grayscale numpy array စာရင်း (fps ၂)。"""
    import numpy as np
    cmd = ["ffmpeg", "-v", "error"]
    if a: cmd += ["-ss", f"{a:.3f}"]
    cmd += ["-i", path]
    if b and a is not None: cmd += ["-t", f"{max(0.1, b - a):.3f}"]
    cmd += ["-vf", f"fps=2,scale={w}:{h}", "-pix_fmt", "gray",
            "-f", "rawvideo", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode or not r.stdout: return []
    buf = np.frombuffer(r.stdout, dtype=np.uint8)
    n = len(buf) // (w * h)
    if n < 1: return []
    return buf[:n * w * h].reshape(n, h, w).astype(np.float32) / 255.0


def shots(path, a=None, b=None):
    """မြင်ကွင်း ပြောင်းနှုန်း (တစ်မိနစ်) — ffmpeg scene detect。"""
    cmd = ["ffmpeg", "-v", "info", "-nostats"]
    if a: cmd += ["-ss", f"{a:.3f}"]
    cmd += ["-i", path]
    if b and a is not None: cmd += ["-t", f"{max(0.1, b - a):.3f}"]
    cmd += ["-vf", "select='gt(scene,0.30)',metadata=print:file=-",
            "-an", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    n = (r.stdout or "").count("lavfi.scene_score")
    dur = (b - a) if (a is not None and b) else (probe(path)["dur"] or 0)
    if not dur: return None, None
    return n, round(n / (dur / 60.0), 2)


def motion(path, a=None, b=None):
    """ရုပ် လှုပ်ရှားမှု — frame အချင်းချင်း ကွာဟမှု အလယ်တန်ဖိုး (၀–၁)。"""
    import numpy as np
    fr = _gray(path, a, b, MOT_W, MOT_H)
    if len(fr) < 4: return None
    d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    return round(float(np.median(d)), 5)


def band_text(path, a=None, b=None):
    """စာတန်း **ရှိ/မရှိ** ကို အနားသတ် သိပ်သည်းမှုနဲ့ ခန့်မှန်းသည်。

    ⚠️ စာတန်း **စာသားကို မဖတ်ပါ** — ရှိမရှိ · ဘယ်ဘက် · အတိုင်းအတာသာ。
    ⚠️ **မရေရာလျှင် `None`** ပြန်ရမည် (「Off」ဟု မှားပြလျှင် စာတန်း
       ပါသော reference ကို စာတန်း မပါဟု သွန်သင်မိမည်)。
    """
    import numpy as np
    fr = _gray(path, a, b, SAMPLE_W, SAMPLE_H)
    if len(fr) < 6: return None
    H = fr.shape[1]
    def edens(y0, y1):
        seg = fr[:, int(H * y0):int(H * y1), :]
        if seg.shape[1] < 3: return None
        # အလျားလိုက် အနားသတ် — စာလုံးက ဒီမှာ ထူးထူးကဲကဲ များသည်
        e = np.abs(np.diff(seg, axis=2)).mean(axis=(1, 2))
        return e
    lo = edens(CAP_LO, CAP_HI)
    mid = edens(MID_LO, MID_HI)
    if lo is None or mid is None: return None
    # ⚠️ အချိုးနဲ့ တိုင်းရမည် — မြင်ကွင်း အလိုက် အနားသတ် အတိုင်းအတာ
    #    လုံးဝ မတူသဖြင့် (အထွေထွေ သိပ်သည်းမှုနဲ့ စာတန်းကို မခွဲနိုင်)。
    rel = lo / np.maximum(mid, 1e-6)
    hot = rel > 1.35                       # အောက်ဘက်က အလယ်ထက် ၃၅% ပို
    cover = float(hot.mean())
    # စာတန်းက **ပြောင်းသည်** — အနားသတ် အတိုင်းအတာ အတက်အကျ ရှိရမည်。
    #    ပုံမှန် ရှုပ်ပွသော အောက်ခံ (မြေပြင် · စားပွဲ) က တည်နေမည်。
    var = float(np.std(rel) / max(1e-6, np.mean(rel)))
    # ⚠️ **မရေရာလျှင် မသိဟု ပြောရမည်**。 ဤ တိုင်းချက်က resolution ·
    #    ကြာချိန် · အောက်ခံ ရှုပ်ပွမှု အပေါ် မူတည်သည် — 640×360 · ၂၀s clip
    #    မှာ `cover` ၀.၂၂၅ ရပြီး 「စာတန်း မရှိ」ဟု **မှားပြခဲ့သည်**
    #    (1280×720 · ၄၀s တူညီသော clip မှာ ၀.၃၇၅)。 ⇒ ကြားထဲက တန်ဖိုးကို
    #    「မရှိ」ဟု မဆုံးဖြတ်ဘဲ **unknown** ထားသည် — မှားပြီး 「စာတန်း
    #    မပါ」ဟု သွန်သင်လျှင် reference ရဲ့ အဓိက သွင်ပြင် ပျောက်မည်。
    HI, LO = 0.30, 0.08
    if cover >= HI:
        present = True
    elif cover <= LO:
        present = False
    else:
        present = None
    if present is None:
        return dict(cover=round(cover, 3), var=round(var, 3), conf=0.0,
                    present=None, band="bottom",
                    why=f"cover {cover:.2f} က {LO}–{HI} ကြား ⇒ မရေရာ")
    conf = min(1.0, 0.45 + 1.6 * (cover - HI if present else LO - cover)
               + 1.2 * min(var, 0.5))
    # ⚠️ `rel_size` — band အတွင်း အနားသတ် အထူ ⇒ စာလုံး အရွယ် **ကြမ်း**
    #    ခန့်မှန်းချက်。 တိကျသော px မဟုတ် ⇒ label အဖြစ်သာ သုံးသည်。
    rows = np.abs(np.diff(fr[:, int(H*CAP_LO):int(H*CAP_HI), :], axis=2)).mean(axis=(0, 2))
    thick = float((rows > rows.mean() * 1.2).mean()) if rows.size else None
    return dict(cover=round(cover, 3), var=round(var, 3),
                conf=round(max(0.0, min(1.0, conf)), 2), present=present,
                band="bottom", rel_thick=(round(thick, 3) if thick is not None else None))


def audio(path, a=None, b=None, log=None):
    """စကား အရှိန် · နားချိန် စည်း · အသံ စွမ်းအင် · တီးလုံး ရှိနိုင်ခြေ。"""
    import numpy as np
    d = tempfile.mkdtemp(prefix="refdna_")
    wav = os.path.join(d, "a.wav")
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if a: cmd += ["-ss", f"{a:.3f}"]
    cmd += ["-i", path]
    if b and a is not None: cmd += ["-t", f"{max(0.1, b - a):.3f}"]
    cmd += ["-vn", "-ar", "16000", "-ac", "1", wav]
    if subprocess.run(cmd, capture_output=True).returncode:
        return None
    try:
        import measure as M
        sp, sil, dur, ev, cls = M.speech(wav)
        if not dur: return None
        spk = sum(y - x for x, y in sp)
        gaps = [y - x for x, y in sil if y - x >= 0.28]
        out = dict(dur=round(dur, 2),
                   speak_ratio=round(spk / dur, 3),
                   gaps_per_min=round(len(gaps) / (dur / 60.0), 2) if dur else None,
                   gap_med=round(float(np.median(gaps)), 3) if gaps else None,
                   cls=cls)
        # ── စွမ်းအင် ──
        r = _run(["ffmpeg", "-v", "info", "-nostats", "-i", wav,
                  "-af", "loudnorm=print_format=json", "-f", "null", "-"])
        txt = (r.stderr or "")
        try:
            blob = txt[txt.rindex("{"):txt.rindex("}") + 1]
            ln = json.loads(blob)
            out["lufs"] = round(float(ln.get("input_i")), 1)
            out["lra"] = round(float(ln.get("input_lra")), 1)
        except Exception:
            out["lufs"] = out["lra"] = None
        # ── တီးလုံး ရှိနိုင်ခြေ — **ရှိနိုင်ခြေသာ**、အတည် မဟုတ် ──
        # ⚠️ နားချိန်ထဲမှာ အသံက တကယ့် အောက်ဆုံးထက် များစွာ မြင့်နေလျှင်
        #    တစ်ခုခု တီးနေသည် ⇒ ဒါပေမယ့် ရုံးခန်း ဆူညံသံလည်း ဖြစ်နိုင်
        #    ⇒ label က "likely" သာ。
        try:
            db, voice, _du = M.analyse(wav)
            db = np.asarray(db, dtype=np.float32)
            floor = float(np.percentile(db, 5))
            hop = _du / max(1, len(db))
            gi = []
            for x, y in sil:
                i0, i1 = int(x / hop), int(y / hop)
                if i1 - i0 >= 3: gi.extend(range(i0 + 1, i1 - 1))
            if len(gi) >= 20:
                gm = float(np.median(db[[i for i in gi if i < len(db)]]))
                out["gap_db"] = round(gm, 1)
                out["floor_db"] = round(floor, 1)
                out["music_like"] = round(max(0.0, min(1.0, (gm - floor) / 18.0)), 2)
            else:
                out["music_like"] = None
        except Exception:
            out["music_like"] = None
        return out
    finally:
        try:
            os.remove(wav); os.rmdir(d)
        except OSError:
            pass


def person(path, a=None, b=None, log=None):
    """လူ ပေါ်နေသော frame အချိုး — talking-head ÷ B-roll。

    ⚠️ posecheck မရှိလျှင် **`None`** — ခန့်မှန်း၍ မရ。
    """
    try:
        import pose as PZ
        if not PZ.available(): return None
    except Exception:
        return None
    src = path
    d = None
    try:
        if a is not None and b:
            d = tempfile.mkdtemp(prefix="refseg_")
            src = os.path.join(d, "s.mp4")
            if subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}",
                               "-i", path, "-t", f"{max(0.1, b - a):.3f}",
                               "-an", "-c:v", "libx264", "-preset", "ultrafast",
                               "-crf", "30", src], capture_output=True).returncode:
                return None
        fr = PZ.measure(src, log=log)
        if not fr: return None
        have = sum(1 for f in fr if int(f.get("nf") or 0) >= 1)
        ratio = have / float(len(fr))
        # ⚠️ frame နမူနာ နည်းလျှင် **ယုံကြည်မှု နိမ့်** ဖြစ်ရမည်
        conf = min(1.0, len(fr) / 60.0)
        # ⚠️ **မျက်နှာ ၀ ခု ဆိုတာ ကတိ မဟုတ်**。 「လူ မပါ (B-roll)」လည်း
        #    ဖြစ်နိုင် · 「detector မအောင်」လည်း ဖြစ်နိုင် — ခွဲလို့ **မရ**。
        #    (၂၀၂၆-၀၉-၂၁: နမူနာ ဗီဒီယိုမှာ ၀ တွေ့ပြီး 「B-roll အများ」ဟု
        #     မှားပြခဲ့သည် — မျက်နှာ လုံးဝ မရှိသော synthetic clip မို့。)
        #    ⇒ တစ်ခုမှ မတွေ့လျှင် **ယုံကြည်မှု ၀** ⇒ label က unknown。
        if have == 0:
            conf = 0.0
        return dict(head_ratio=round(ratio, 3), frames=len(fr),
                    faces=have, conf=round(conf, 2))
    finally:
        if d:
            import shutil as _sh
            _sh.rmtree(d, ignore_errors=True)


def colour(path, a=None, b=None):
    """အရောင် အနှစ်ချုပ် — **ဘောင်ခံ အရိပ်အမြွက်သာ**、grade ကူးယူခြင်း မဟုတ်။"""
    cmd = ["ffmpeg", "-v", "info", "-nostats"]
    if a: cmd += ["-ss", f"{a:.3f}"]
    cmd += ["-i", path]
    if b and a is not None: cmd += ["-t", f"{max(0.1, b - a):.3f}"]
    cmd += ["-vf", "fps=1,signalstats,metadata=print:file=-", "-an", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    sat, yavg = [], []
    for line in (r.stdout or "").splitlines():
        if "lavfi.signalstats.SATAVG" in line:
            try: sat.append(float(line.split("=")[-1]))
            except ValueError: pass
        elif "lavfi.signalstats.YAVG" in line:
            try: yavg.append(float(line.split("=")[-1]))
            except ValueError: pass
    if not sat or not yavg: return None
    import numpy as np
    return dict(sat=round(float(np.mean(sat)), 1),
                luma=round(float(np.mean(yavg)), 1),
                luma_sd=round(float(np.std(yavg)), 1))


def measure(path, a=None, b=None, log=print):
    """reference တစ်ခုရဲ့ **ကြမ်းထမ်း တိုင်းချက်** အားလုံး。"""
    def _l(m):
        if log: log(m)
    pr = probe(path)
    out = dict(probe=pr)
    _l(f"  ref · {pr.get('w')}×{pr.get('h')} · {pr.get('fps')}fps · "
       f"{pr.get('dur')}s · {pr.get('aspect') or 'အချိုး မသိ'}")
    n, per = shots(path, a, b)
    out["shots"] = dict(n=n, per_min=per)
    _l(f"  ref · မြင်ကွင်း ပြောင်း {n} ({per}/မိနစ်)")
    out["motion"] = motion(path, a, b)
    _l(f"  ref · လှုပ်ရှားမှု {out['motion']}")
    out["captions"] = band_text(path, a, b)
    _l(f"  ref · စာတန်း {out['captions']}")
    out["audio"] = audio(path, a, b, log=log)
    _l(f"  ref · အသံ {out['audio']}")
    out["person"] = person(path, a, b, log=None)
    _l(f"  ref · လူ ပေါ်မှု {out['person']}")
    out["colour"] = colour(path, a, b)
    _l(f"  ref · အရောင် {out['colour']}")
    out["range"] = [a, b] if a is not None else None
    return out


# ══════════════════════════════════════════════════════════════════════
# တိုင်းချက် → **label** (သုံးစွဲသူ ဖတ်ရန်)
# ══════════════════════════════════════════════════════════════════════
# ⚠️ တိုင်းလို့ မရသော အချက် ⇒ `"unknown"`。 ခန့်မှန်းပြီး တိကျသလို ပြခြင်းက
#    လိမ်ရာ ကျသည် (Zin: 「Unknown must remain unknown」)。

UNK = "unknown"

def _bucket(v, lo, hi, names):
    if v is None: return UNK
    return names[0] if v < lo else (names[2] if v > hi else names[1])


def labels(meas):
    """တိုင်းချက် → `{pace, cut, captions, motion, graphics, broll, audio, …}`。"""
    pr = meas.get("probe") or {}
    au = meas.get("audio") or {}
    sh = meas.get("shots") or {}
    ca = meas.get("captions") or {}
    pe = meas.get("person") or {}
    mo = meas.get("motion")
    out, conf = {}, {}

    # ── စကား အရှိန် — ပြောချိန် အချိုးနဲ့ နားချိန် ကြာချိန် ──
    sr = au.get("speak_ratio")
    out["pace"] = _bucket(sr, 0.58, 0.78, ("calm", "balanced", "fast"))
    conf["pace"] = 0.0 if sr is None else 0.8

    # ── ဖြတ်ချက် စည်း — မြင်ကွင်း ပြောင်းနှုန်း ──
    pm = sh.get("per_min")
    out["cut"] = _bucket(pm, 6.0, 20.0, ("long_takes", "mixed", "tight"))
    conf["cut"] = 0.0 if pm is None else 0.75

    # ── စာတန်း ──
    if not ca or ca.get("present") is None:
        out["captions"] = UNK; conf["captions"] = 0.0
    else:
        cv = ca.get("cover") or 0.0
        out["captions"] = ("off" if cv < 0.30 else
                           ("occasional" if cv < 0.62 else "frequent"))
        out["caption_band"] = ca.get("band") or UNK
        # ⚠️ **ကြမ်းထမ်း** အရွယ် — px မဟုတ် ⇒ label သာ
        rt = ca.get("rel_thick")
        out["caption_size"] = (UNK if rt is None else
                               ("small" if rt < 0.25 else
                                ("medium" if rt < 0.45 else "large")))
        conf["captions"] = float(ca.get("conf") or 0.0)

    # ── လှုပ်ရှားမှု ──
    out["motion"] = _bucket(mo, 0.012, 0.045, ("minimal", "balanced", "dynamic"))
    conf["motion"] = 0.0 if mo is None else 0.7

    # ── ဂရပ်ဖစ် သိပ်သည်းမှု ──
    # ⚠️ **တိုင်းလို့ မရပါ** — စာတန်း · B-roll · overlay ကို အနားသတ်
    #    သိပ်သည်းမှုတစ်ခုတည်းနဲ့ **ခွဲလို့ မရ**。 ⇒ မသိဟု ပြောရမည်。
    out["graphics"] = UNK; conf["graphics"] = 0.0

    # ── B-roll ယူမှု ──
    hr = pe.get("head_ratio") if pe else None
    if hr is None or (pe or {}).get("conf", 0) < 0.35:
        out["broll"] = UNK; conf["broll"] = 0.0
    else:
        out["broll"] = ("low" if hr > 0.80 else
                        ("medium" if hr > 0.55 else "high"))
        conf["broll"] = float(pe.get("conf") or 0.0)

    # ── အသံ စွမ်းအင် ──
    lu = au.get("lufs")
    out["audio"] = _bucket(lu, -20.0, -14.0, ("quiet", "standard", "energetic"))
    conf["audio"] = 0.0 if lu is None else 0.8
    ml = au.get("music_like")
    out["music"] = (UNK if ml is None else
                    ("likely" if ml >= 0.55 else
                     ("unlikely" if ml <= 0.25 else "uncertain")))
    conf["music"] = 0.0 if ml is None else 0.5   # ⚠️ ယုံကြည်မှု **နိမ့်**

    out["aspect"] = pr.get("aspect") or UNK
    out["fps"] = pr.get("fps")
    out["dur"] = pr.get("dur")
    out["_conf"] = {k: round(v, 2) for k, v in conf.items()}
    # ── စုစုပေါင်း ယုံကြည်မှု — တိုင်းရသော အချက် အချိုး ──
    known = [k for k in ("pace", "cut", "captions", "motion", "broll", "audio")
             if out.get(k) not in (None, UNK)]
    out["confidence"] = round(len(known) / 6.0, 2)
    return out


def compat(dna, fmt=None, dur=None):
    """`(state, why, why_en)` — Compatible / Adapted / Not suitable。

    ⚠️ **ပုံတူ ဖြစ်ကြောင့် မကြားရ** — အချိုး မတူလျှင် 「Adapted」ဟု
       ရှင်းရှင်း ပြောရမည်。
    """
    a = dna.get("aspect")
    c = float(dna.get("confidence") or 0.0)
    if c < 0.34:
        return ("unsuitable",
                "တိုင်းလို့ရတဲ့ အချက် အလွန် နည်းပါတယ် — sample က တိုလွန်းတာ "
                "ဒါမှမဟုတ် စကား/မြင်ကွင်း ကွဲပြားမှု မရှိတာ ဖြစ်နိုင်ပါတယ်။",
                "Too few reliable measurements to use as direction.")
    if a in (None, UNK):
        return ("adapted",
                "အချိုးကို မခွဲနိုင်ပါ — အရှိန်၊ စာတန်း စည်းနဲ့ လှုပ်ရှားမှုကိုသာ "
                "ယူပြီး ခင်ဗျား ရွေးထားတဲ့ အရွယ်အတိုင်း ချိန်ပါမယ်။",
                "Aspect unclear — pacing and rhythm applied, your format kept.")
    if fmt and a != fmt:
        return ("adapted",
                f"reference က {a} · ခင်ဗျား ဗီဒီယိုက {fmt} — အရွယ်ကို "
                "မပြောင်းပါ။ အရှိန်၊ စာတန်း စည်းနဲ့ လှုပ်ရှားမှုကို ချိန်ပါမယ်။",
                f"Reference is {a}, your project is {fmt} — pacing adapted, "
                "format unchanged.")
    return ("compatible",
            "ခင်ဗျား ဗီဒီယိုနဲ့ ကိုက်ပါတယ် — အရှိန်၊ စာတန်း စည်း၊ လှုပ်ရှားမှုနဲ့ "
            "အသံ စွမ်းအင်ကို ယူပါမယ်။",
            "Compatible — pacing, caption rhythm, motion and audio energy applied.")


# ══════════════════════════════════════════════════════════════════════
# label → **ဘောင်ခံ override** (QC ဂိတ် မထိ)
# ══════════════════════════════════════════════════════════════════════
# ⚠️ ခွင့်ပြုသော key များသာ。 brand · fmt · font · cap ဖတ်ရလွယ်မှု နယ်နိမိတ် ·
#    အတည်ပြုပြီးသော ဖြတ်မှတ် တွေကို **လုံးဝ မထိရ**。
# ⚠️ `keep_pause` · `min_sil` က **override ဘောင်ထဲ မရှိပါ** — `recipes` က
#    `cut` (choice) ဒါမှမဟုတ် `silence_ms` ကနေသာ လက်ခံသည်。 ဒါကြောင့်
#    နားချိန်/ဖြတ်ချက် အထိမခံမှုကို **`cut` နာမည်**နဲ့ ပေးရသည်
#    (၂၀၂၆-၀၉-၂၁: raw တန်ဖိုး ပေးခဲ့ရာ `clean()` က တိတ်တဆိတ် ပယ်ခဲ့သည် —
#     ဒီ module ရဲ့ note က ဖော်ပြသဖြင့် ဖမ်းမိသည်)。
ALLOW = ("cut", "gfx", "broll", "broll_pct", "broll_freq",
         "sfx_per_min", "zoom_amt", "cap_cover", "music",
         "energy", "motion", "motionkit_profile")

# label → အကြံပြု တန်ဖိုး (BOUNDS က နောက်ဆုံး ကန့်သတ်သည်)
_PACE = {"calm": "gentle", "balanced": "normal", "fast": "tight"}
_CUTN = {"long_takes": "gentle", "mixed": "normal", "tight": "snappy"}
_CUT = {"long_takes": 0.0, "mixed": 0.030, "tight": 0.060}
# ⚠️ Motion Kit **အထွေထွေ profile** သာ — template တစ်ခုချင်း မရွေးရ
#    (template ရွေးချယ်မှုက Visual Plan ရဲ့ အလုပ် · ဂိတ်လည်း ရှိသည်)。
_MKP = {"minimal": "clean", "balanced": "premium", "dynamic": "bold"}
_MOT = {"minimal": 0.0, "balanced": 0.045, "dynamic": 0.075}
_BROLL = {"low": (2, 0.10), "medium": (4, 0.18), "high": (7, 0.30)}
_AUD = {"quiet": 0.5, "standard": 1.0, "energetic": 1.4}
_CAP = {"off": None, "occasional": 0.45, "frequent": 0.85}


def apply_to(dna, base, fmt=None, min_conf=0.45):
    """`(over, notes)` — `base` recipe ကနေ **ဘောင်ခံ** override ဆောက်သည်。

    ⚠️ ယုံကြည်မှု နိမ့်သော အချက်ကို **မသုံးရ** — IKKI Smart ရဲ့ ပုံသေ ကျန်ရမည်
       (Zin ရဲ့ §「missing, incompatible, low confidence, out of bounds」)。
    ⚠️ `recipes.BOUNDS` က နောက်ဆုံး စစ်သည် ⇒ ဘောင်ပြင် တန်ဖိုး **တိတ်တဆိတ်
       ဝင်လို့ မရ**。
    """
    import recipes as RC
    cf = dna.get("_conf") or {}
    over, notes = {}, []

    def _use(field):
        v = dna.get(field)
        if v in (None, UNK):
            notes.append(f"{field}: မတိုင်းရ ⇒ IKKI ပုံသေ"); return None
        if float(cf.get(field, 0.0)) < min_conf:
            notes.append(f"{field}: ယုံကြည်မှု {cf.get(field)} < {min_conf} "
                         f"⇒ IKKI ပုံသေ"); return None
        return v

    # ── နားချိန်/ဖြတ်ချက် အထိမခံမှု ──
    # ⚠️ ဖြတ်ချက် **စည်း**က ပိုတိကျသည် (မြင်ကွင်း ပြောင်းနှုန်းကနေ တိုင်း) ⇒
    #    ရှိလျှင် အဲဒါ · မရှိလျှင် စကား အရှိန်ကနေ。
    c = _use("cut")
    p = _use("pace")
    if c and c in _CUTN:
        over["cut"] = _CUTN[c]
    elif p and p in _PACE:
        over["cut"] = _PACE[p]
    if c and c in _CUT:
        # ⚠️ **ဖြတ်ချက် မဟုတ်** — punch-in စွမ်းအင်သာ。 တကယ့် ဖြတ်မှတ်ကို
        #    သုံးစွဲသူ အတည်ပြုသည် (reference က မဖြတ်ရ)。
        over["zoom_amt"] = max(over.get("zoom_amt", 0.0), _CUT[c])
    m = _use("motion")
    if m and m in _MOT:
        over["zoom_amt"] = max(over.get("zoom_amt", 0.0), _MOT[m])
        if m in _MKP: over["motionkit_profile"] = _MKP[m]
        if m == "dynamic":
            over["gfx"] = int(round((base.get("gfx") or 8) * 1.35))
            over["energy"] = "dynamic"
        elif m == "minimal":
            over["gfx"] = max(1, int(round((base.get("gfx") or 8) * 0.6)))
            over["energy"] = "minimal"
    br = _use("broll")
    if br and br in _BROLL:
        over["broll"], over["broll_pct"] = _BROLL[br]
        over["broll_freq"] = {"low": "low", "medium": "normal", "high": "high"}[br]
    ad = _use("audio")
    if ad and ad in _AUD:
        over["sfx_per_min"] = round((base.get("sfx_per_min") or 1.0) * _AUD[ad], 3)
    cp = _use("captions")
    if cp and cp in _CAP:
        # ⚠️ 「off」ဆိုလည်း **စာတန်း မဖြုတ်ရ** — မြန်မာစာ ဖတ်ရလွယ်မှုက
        #    ညှိနှိုင်းမရသော အချက် (Zin ရဲ့ safeguard #6) ⇒ အနည်းဆုံးသာ。
        if _CAP[cp] is None:
            over["cap_cover"] = 0.25
            notes.append("captions: reference မှာ မရှိ — မြန်မာစာ ဖတ်ရလွယ်မှု "
                         "အတွက် စာတန်း **မဖြုတ်ပါ** · အနည်းဆုံးသာ ထားသည်")
        else:
            over["cap_cover"] = _CAP[cp]
    mu = dna.get("music")
    if mu == "unlikely" and float(cf.get("music", 0)) >= 0.45:
        over["music"] = None
        notes.append("music: reference မှာ မရှိဟု ခန့်မှန်း ⇒ တီးလုံး ပိတ်")
    elif mu in (UNK, "uncertain", "likely"):
        notes.append("music: မရေရာ ⇒ IKKI ရဲ့ ရွေးချက် (AI ကိုက်)")

    # ── ✦ **ဂိတ်** — `recipes.BOUNDS` နဲ့ စစ်ပြီး ခွင့်ပြုသော key သာ ──
    over = {k: v for k, v in over.items() if k in ALLOW}
    before = dict(over)
    over = RC.clean(over)
    for k, v in before.items():
        if k not in over:
            notes.append(f"{k}={v}: ဘောင်ပြင် ⇒ ပယ်ပြီး IKKI ပုံသေ")
        elif over[k] != v:
            notes.append(f"{k}: {v} ⇒ {over[k]} (ဘောင်အတွင်း ချ)")
    # ⚠️ **ဘယ်တော့မှ မပါရ** — အထက်က မထည့်ပေမယ့် ထပ်စစ်သည်
    for bad in ("brand_id", "fmt", "font", "cap", "cap_pct", "cap_base",
                "lufs", "_spans", "_cuthash", "mmf", "latin", "captions"):
        if bad in over:
            del over[bad]; notes.append(f"{bad}: reference က မထိရ ⇒ ဖယ်")
    return over, notes
