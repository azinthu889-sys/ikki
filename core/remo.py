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
