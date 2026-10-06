#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI ⇒ Remotion cinematic scenes (Zin ၂၀၂၆-၁၀-၀၆ 「ဒီထက် ပိုမိုက်ချင်」 · အဆင့် ၂)

IKKI ထွက်ဖိုင် (ဖြတ် · grade · B-roll · camera · စာတန်း · အသံ) ကို **base** အဖြစ် ယူပြီး
reference r3 ပုံစံ scene များ (title · neon blur explainer · white list · subscribe) ကို
`~/ikki-remotion` ရဲ့ `Auto` composition နဲ့ အပေါ်က ဆောက်သည်。 အသံကို base ကနေ
ပြန် mux သည် (Remotion က muted)。

⚠️ Remotion မရှိ/မအောင်လျှင် **base ကို မထိ** (job မကျစေရ)。
⚠️ scene က IKKI ဂရပ်ဖစ် ဖြစ်ရပ် (`gmov` အချိန်) ပေါ်မှာသာ ⇒ SFX ↔ ရုပ် ချိတ်ချက် မပျက်。
"""
import hashlib
import json
import os
import re
import shutil
import subprocess

REMO = os.environ.get("IKKI_REMOTION", os.path.expanduser("~/ikki-remotion"))
BRANDS = (("western union", "WESTERN UNION"), ("kbz pay", "KBZ PAY"), ("kbzpay", "KBZ PAY"),
          ("kpay", "KBZ PAY"), ("wave pay", "WAVE PAY"), ("aya pay", "AYA PAY"))
_NUM = re.compile(r"[0-9၀-၉][0-9၀-၉,\.]*\s*(?:သိန်း|သောင်း|ထောင်|ကျပ်|ကြိမ်|%|ရက်)?\S*")


def available():
    return (os.path.isdir(os.path.join(REMO, "node_modules", "remotion"))
            and shutil.which("npx") is not None)


def _brand(t):
    k = " ".join(str(t or "").lower().split())
    for b, d in BRANDS:
        if b in k:
            return d
    return None


def _sentence(caps, t):
    best = None
    for c in caps or []:
        a, b = float(c.get("start") or 0), float(c.get("end") or 0)
        if a - 0.3 <= t <= b + 0.3:
            return str(c.get("text") or "").strip()
        if a > t and best is None:
            best = str(c.get("text") or "").strip()
    return best or ""


def _short(s, n=7):
    w = [x for x in str(s).replace("။", " ").split() if x]
    return " ".join(w[:n])


def plan_scenes(events, caps, dur, gap=3.0):
    """`events` [(at, d, kind, props)] (ထွက်ဖိုင် အချိန်) ⇒ Remotion scene စာရင်း。

    ⚠️ rule-based director — AI director (Claude) ချိတ်သည်အထိ ယာယီ。
    """
    out, last = [], -99.0
    titled = False
    for at, d, kind, props in sorted(events, key=lambda x: x[0]):
        props = props or {}
        if at - last < gap or at > dur - 2.5:
            continue
        line = _short(_sentence(caps, at))
        k = str(kind or "")
        if k.endswith("mt_pill_list") and props.get("items"):
            out.append(dict(type="list", start=round(at - 0.1, 2), dur=3.2,
                            head=str(props.get("head") or "")[:40],
                            items=[str(x)[:28] for x in props["items"][:4]]))
        elif k.endswith("mt_neon_box") or k.endswith("mt_counter"):
            br = _brand(props.get("text")) or _brand(line)
            if not titled and br and at >= 1.5:
                out.append(dict(type="title", start=round(at - 0.1, 2), dur=2.8,
                                title=br, sub=_short(line, 4)))
                titled = True
            else:
                m = _NUM.search(line)
                out.append(dict(type="neon", start=round(at - 0.1, 2), dur=3.4,
                                title=br or "", line1=line, hi=(m.group(0).strip() if m else ""),
                                line2=""))
        else:
            continue
        last = at + out[-1]["dur"]
    if dur > 20:
        out.append(dict(type="subscribe", start=round(dur - 3.4, 2), dur=3.0))
    return out


def compose(base, scenes, work, log=print, timeout=3600):
    """`base` (IKKI ထွက်ဖိုင်) ⇒ scene ထပ် · အသံ ပြန် mux ⇒ `base` ကို အစားထိုး。 OK ⇒ True"""
    if not scenes or not available():
        log("  ⓘ Remotion · scene မရှိ/မတပ်ဆင်ရ ⇒ ကျော်")
        return False
    pub = os.path.join(work, "remo_pub")
    os.makedirs(pub, exist_ok=True)
    # ⚠️ symlink ကို Remotion ရဲ့ file server က မဖတ် (readFile ကျ) ⇒ hardlink · မရလျှင် copy
    def _put(src, dst):
        if os.path.lexists(dst):
            os.remove(dst)
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
    for f in os.listdir(os.path.join(REMO, "public")):
        if f.endswith((".ttf", ".otf", ".jpg", ".png")):
            _put(os.path.join(REMO, "public", f), os.path.join(pub, f))
    bl = os.path.join(pub, "base.mp4")
    _put(os.path.abspath(base), bl)
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "csv=p=0", base], capture_output=True, text=True).stdout.strip())
    except ValueError:
        return False
    props = os.path.join(work, "remo_props.json")
    json.dump(dict(base="base.mp4", dur=round(dur, 3), scenes=scenes), open(props, "w"),
              ensure_ascii=False)
    fps = 30
    log(f"  🎬 Remotion · scene {len(scenes)} ခု · "
        + " · ".join(f"{s['type']}@{s['start']:.1f}s" for s in scenes))
    # ⚠️ **scene အပိုင်းသာ render** (ဗီဒီယို တစ်ခုလုံး မဟုတ်) — 60s တစ်ခုလုံး ~19 မိနစ် ⇒
    #    scene ~16s သာ ⇒ ~4× မြန် · ffmpeg နဲ့ အချိန်တိတိ ပြန်ထပ် (base ပါပြီးသား frame)
    segs = []
    for i, sc in enumerate(scenes):
        a = max(0, int(round(sc["start"] * fps)))
        b = min(int(dur * fps) - 1, int(round((sc["start"] + sc["dur"]) * fps)) - 1)
        if b <= a:
            continue
        seg = os.path.join(work, f"remo_s{i}.mp4")
        r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "Auto", seg,
                            f"--props={props}", f"--public-dir={pub}", f"--frames={a}-{b}",
                            "--codec=h264", "--crf=16", "--log=error"],
                           cwd=REMO, capture_output=True, text=True, timeout=timeout)
        if r.returncode or not os.path.exists(seg):
            log(f"  ⚠️ Remotion scene {i} မအောင် ({(r.stderr or r.stdout or '')[-200:]}) ⇒ ကျော်")
            continue
        segs.append((a / fps, (b + 1) / fps, seg))
    if not segs:
        log("  ⚠️ Remotion · scene တစ်ခုမှ မရ ⇒ IKKI ထွက်ဖိုင် အတိုင်း")
        return False
    ins, fc, last = ["-i", base], [], "0:v"
    for k, (ta, tb, seg) in enumerate(segs):
        ins += ["-itsoffset", f"{ta:.3f}", "-i", seg]
        fc.append(f"[{last}][{k + 1}:v]overlay=0:0:eof_action=pass:"
                  f"enable='between(t,{ta:.3f},{tb - 0.001:.3f})'[r{k}]")
        last = f"r{k}"
    tmp = base + ".remo.mp4"
    r2 = subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc),
                         "-map", f"[{last}]", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "medium",
                         "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy",
                         "-movflags", "+faststart", tmp])
    if r2.returncode or not os.path.exists(tmp):
        log("  ⚠️ Remotion · ပြန်ဆက် မရ ⇒ IKKI ထွက်ဖိုင် အတိုင်း")
        return False
    os.replace(tmp, base)
    log("  🎬 Remotion · cinematic scene တပ်ပြီး")
    return True


# ══ Beats (AI director ⇒ word-synced infographic · Zin ၂၀၂၆-၁၀-၀၇ roadmap ①②④⑤) ══════════
#    beat ဝင်းဒိုးသာ render (`--frames`) ⇒ ffmpeg overlay · SFX ကို registry `sfx` + တိုင်းထားသော
#    `hit` နဲ့ base အသံပေါ် ffmpeg ဖြင့် ရော (Remotion audio မသုံး ⇒ segment render မြန်)。
PRE = 4 / 30.0


def _windows(beats, dur, pad=0.15, join=0.6):
    w = []
    for b in sorted(beats, key=lambda x: x["at"]):
        a = max(0.0, b["at"] - PRE - pad)
        e = min(dur, b["at"] + float(b.get("dur") or 3.0) + PRE + pad)
        if w and a - w[-1][1] <= join:
            w[-1][1] = max(w[-1][1], e)
        else:
            w.append([a, e])
    return w


def sfx_events(beats, gain=1.0):
    """[(file, start_s, vol)] — transient (`hit`) က beat.at + offset မှာ ကျ"""
    try:
        import director as _D
    except ImportError:  # pragma: no cover
        from core import director as _D
    R = _D.registry()
    hit, T = R["hit"], R["types"]
    out = []
    for b in beats:
        for role, off, vol in (T.get(b["type"]) or {}).get("sfx") or []:
            t = float(b["at"]) + float(off) / 30.0 - float(hit.get(role, 0.0))
            out.append((os.path.join(REMO, "public", "sfx", role + ".wav"), max(0.0, round(t, 3)),
                        min(1.0, float(vol) * gain)))
    return [e for e in out if os.path.exists(e[0])]


def compose_beats(base, beats, work, brand=None, sfx_gain=1.0, log=print, timeout=1800, qc=True, report=None):
    """`base` ⇒ beat infographic ထပ် + SFX ရော ⇒ **auto-QC** (မျက်နှာ · caption · edge) ⇒ ပြဿနာ
    ရှိလျှင် pos လှန်/ဖယ်ပြီး တစ်ကြိမ် ပြန်ဆောက် ⇒ `base` အစားထိုး。 OK ⇒ True (မအောင် ⇒ base မထိ)"""
    if not beats or not available():
        log("  ⓘ beats · beat မရှိ/Remotion မတပ်ဆင်ရ ⇒ ကျော်")
        return False
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                    "-of", "csv=p=0", base], capture_output=True, text=True).stdout.strip())
    except ValueError:
        return False
    pub = os.path.join(work, "remo_pub")
    os.makedirs(pub, exist_ok=True)

    def _put(src, dst):
        if os.path.lexists(dst):
            os.remove(dst)
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
    for f in os.listdir(os.path.join(REMO, "public")):
        if f.endswith((".ttf", ".otf")):
            _put(os.path.join(REMO, "public", f), os.path.join(pub, f))
    src = os.path.join(pub, "base.mp4")
    _put(os.path.abspath(base), src)
    rep = report if report is not None else {}
    tmp, ok_beats, nev = _build_beats(src, beats, work, pub, dur, brand, sfx_gain, log, timeout, tag="")
    if not tmp:
        return False
    if qc:
        try:
            import beatqc as _Q
        except ImportError:  # pragma: no cover
            from core import beatqc as _Q
        try:
            import director as _D
        except ImportError:  # pragma: no cover
            from core import director as _D
        zones = {k: v["zone"] for k, v in _D.types().items()}
        iss, fixes, rows = _Q.check(src, tmp, ok_beats, zones, work)
        rep["qc1"] = iss
        if iss:
            log("  🔎 beat QC · " + " · ".join(f"{x['type']}@{x['at']:.1f} {x['kind']}={x['value']}" for x in iss))
        if fixes:
            b2 = _Q.apply_fixes(ok_beats, fixes)
            log(f"  🔧 beat QC ပြင် · {len(fixes)} ခု (pos လှန်/ဖယ်) ⇒ ပြန်ဆောက်")
            tmp2, ok2, nev2 = _build_beats(src, b2, work, pub, dur, brand, sfx_gain, log, timeout, tag="r")
            if tmp2:
                iss2, fx2, _ = _Q.check(src, tmp2, ok2, zones, work)
                rep["qc2"] = iss2
                if fx2:   # ⚠️ ဒုတိယအကြိမ်ပါ မရ ⇒ အဲဒီ beat ကို ဖယ် (ပုံမပျက်စေ)
                    b3 = _Q.apply_fixes(ok2, {i: "drop" for i in fx2})
                    tmp3, ok3, nev3 = _build_beats(src, b3, work, pub, dur, brand, sfx_gain, log, timeout, tag="d") \
                        if b3 else (None, [], 0)
                    if tmp3:
                        tmp2, ok2, nev2 = tmp3, ok3, nev3
                os.replace(tmp2, tmp)
                ok_beats, nev = ok2, nev2
        rep["critic"] = _Q.critic(tmp, ok_beats, work, log=log)
    rep["beats"] = ok_beats
    os.replace(tmp, base)
    log(f"  🎬 beats · {len(ok_beats)} ခု တပ်ပြီး · SFX {nev} ချက်")
    return True


def _build_beats(src, beats, work, pub, dur, brand, sfx_gain, log, timeout, tag=""):
    """beat window render + overlay + SFX mix ⇒ (tmp ဖိုင်, render အောင်သော beat, sfx အရေ) · မရ ⇒ (None, [], 0)"""
    props = os.path.join(work, f"beats_props{tag}.json")
    json.dump(dict(base="base.mp4", dur=round(dur, 3), beats=beats, brand=brand or {}, sfx=False),
              open(props, "w"), ensure_ascii=False)
    fps = 30
    log(f"  🎬 beats{tag} · {len(beats)} ခု · " + " · ".join(f"{b['type']}@{b['at']:.1f}" for b in beats))
    segs = []
    for i, (a, e) in enumerate(_windows(beats, dur)):
        fa, fb = int(a * fps), min(int(dur * fps) - 1, int(round(e * fps)) - 1)
        if fb <= fa:
            continue
        # ⚠️ QC ပြင်ပြီး ပြန်ဆောက်ချိန် မပြောင်းသော window ကို ထပ် render မလုပ် (cache)
        inw = [b for b in beats if a <= b["at"] <= e]
        key = hashlib.sha1(json.dumps([fa, fb, inw, brand or {}], sort_keys=True, ensure_ascii=False)
                           .encode()).hexdigest()[:12]
        seg = os.path.join(work, f"beats_{key}.mp4")
        if os.path.exists(seg) and os.path.getsize(seg) > 0:
            segs.append((fa / fps, (fb + 1) / fps, seg))
            continue
        # ⚠️ TMPDIR ကို exFAT (/Volumes/a) သို့ ပြောင်းလျှင် OffthreadVideo က **ဗီဒီယို မဖတ်နိုင်ဘဲ
        #    နောက်ခံ အမည်း** ထွက်သည် (၂၀၂၆-၁၀-၀၇ တိုင်း: env ⇒ luma 5 · default ⇒ 105)。
        #    ⇒ default ထား · `IKKI_REMO_TMP` (APFS ဖြစ်ရမည်) ပေးမှသာ ပြောင်း。 writeFile ကျ ⇒ ၁ ကြိမ် ပြန်ကြိုး
        env = dict(os.environ)
        if os.environ.get("IKKI_REMO_TMP"):
            env["TMPDIR"] = os.environ["IKKI_REMO_TMP"]
        r = None
        for _try in range(2):
            r = subprocess.run(["npx", "remotion", "render", "src/index.ts", "Beats", seg,
                                f"--props={props}", f"--public-dir={pub}", f"--frames={fa}-{fb}", "--muted",
                                "--codec=h264", "--crf=16", "--log=error"],
                               cwd=REMO, capture_output=True, text=True, timeout=timeout,
                               env=env)
            if not r.returncode and os.path.exists(seg):
                break
        if r.returncode or not os.path.exists(seg):
            log(f"  ⚠️ beats window {i} မအောင် ({(r.stderr or r.stdout or '')[-200:]}) ⇒ ကျော်")
            continue
        segs.append((fa / fps, (fb + 1) / fps, seg))
    if not segs:
        log("  ⚠️ beats · window တစ်ခုမှ မရ ⇒ IKKI ထွက်ဖိုင် အတိုင်း")
        return None, [], 0
    # ⚠️ render အောင်သော window ထဲက beat SFX သာ (ရုပ်မပါဘဲ အသံ မထွက်စေ)
    ok_beats = [b for b in beats if any(ta <= b["at"] <= tb for ta, tb, _ in segs)]
    ev = sfx_events(ok_beats, sfx_gain)
    ins, fc, last = ["-i", src], [], "0:v"
    for k, (ta, tb, seg) in enumerate(segs):
        ins += ["-itsoffset", f"{ta:.3f}", "-i", seg]
        fc.append(f"[{last}][{k + 1}:v]overlay=0:0:eof_action=pass:"
                  f"enable='between(t,{ta:.3f},{tb - 0.001:.3f})'[r{k}]")
        last = f"r{k}"
    n0 = 1 + len(segs)
    amap = ["-map", "0:a:0?", "-c:a", "copy"]
    if ev:
        mix = []
        for j, (f, t, vol) in enumerate(ev):
            ins += ["-i", f]
            ms = int(round(t * 1000))
            fc.append(f"[{n0 + j}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                      f"volume={vol:.3f},adelay={ms}|{ms}[s{j}]")
            mix.append(f"[s{j}]")
        fc.append("[0:a]aformat=sample_rates=48000:channel_layouts=stereo[a0]")
        fc.append(f"[a0]{''.join(mix)}amix=inputs={len(mix) + 1}:normalize=0:duration=first,"
                  f"alimiter=limit=0.95[aout]")
        amap = ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    tmp = os.path.join(work, f"beats_out{tag}.mp4")
    r2 = subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc),
                         "-map", f"[{last}]", *amap, "-c:v", "libx264", "-preset", "medium",
                         "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp],
                        capture_output=True, text=True)
    if r2.returncode or not os.path.exists(tmp):
        log(f"  ⚠️ beats · ပြန်ဆက် မရ ({(r2.stderr or '')[-200:]}) ⇒ IKKI ထွက်ဖိုင် အတိုင်း")
        return None, [], 0
    return tmp, ok_beats, len(ev)
