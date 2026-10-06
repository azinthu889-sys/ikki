#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Beat auto-QC (Zin ၂၀၂၆-၁၀-၀၇ roadmap ⑥) — **ထွက်ပြီးသား ပုံကို တိုင်း**သည် (ခန့်မှန်း မဟုတ်)

beat တစ်ခုချင်း (ဝင်ပြီး ~1s) မှာ base ↔ ထွက်ဖိုင် frame ကို နှိုင်းပြီး ဂရပ်ဖစ် bbox ရ ⇒
  · face    — macOS Vision (`tools/posecheck`) မျက်နှာ အကွက်နဲ့ ထပ်မှု (side/top/bottom beat သာ;
              center = scrim ပါ cutaway ⇒ ခွင့်ပြု)
  · caption — စာတန်း ဇုန် (y ≥ cap_top) ထဲ ကျော်ဝင်မှု
  · edge    — ဘောင်အစွန်း ထိ (Burmese overflow / ကျော်ထွက်)
  · empty   — ဘာမှ မပေါ် (render မအောင်)
ပြဿနာ ⇒ `fixes` (pos လှန် · ဖယ်) ပြန်ပေး ⇒ `remo.compose_beats` က တစ်ကြိမ် ပြန်ဆောက်。

vision critic (ရွေးချယ်) — `IKKI_VISION_CRITIC=1` ⇒ contact sheet ကို Gemini vision နဲ့
rubric (readability · premium · clutter · face) အမှတ်ပေး။ မရ ⇒ ကျော် (job မကျ)。
"""
import base64
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request

try:
    import numpy as np
    from PIL import Image
except ImportError:  # pragma: no cover
    np = None

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSE = os.path.join(HERE, "tools", "posecheck")
W = 640
CAP_TOP = 0.80
FACE_MAX = 0.12      # မျက်နှာ ဧရိယာ၏ ၁၂% ထက် ပိုဖုံးလျှင် ပြဿနာ
DIFF_T = 28          # pixel ကွာခြားချက် (0-255) — grade/encode noise ထက် မြင့်
DIFF_CORE = 70       # panel/စာ ကိုယ်ထည် (shadow မပါ)


def _frame(path, t, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, t):.3f}", "-i", path,
                    "-frames:v", "1", "-vf", f"scale={W}:-2", out], check=False)
    return os.path.exists(out)


def bbox(a_png, b_png):
    """base ↔ ထွက် ကွာခြားသော အကွက် (အချိုး) — မရှိ ⇒ None"""
    if np is None:
        return None
    a = np.asarray(Image.open(a_png).convert("L"), dtype=np.int16)
    b = np.asarray(Image.open(b_png).convert("L"), dtype=np.int16)
    if a.shape != b.shape:
        return None
    dd = np.abs(a - b)
    h, w = dd.shape
    # ⚠️ panel ရဲ့ box-shadow (blur 80px) က ဘေးပတ်လည်ကို မှောင်စေ ⇒ threshold နိမ့်လျှင် bbox
    #    ပွပြီး မျက်နှာ ထပ်သည်ဟု **အမှား** ဖမ်းသည် (WU v9 · ၂၀၂၆-၁၀-၀၇ တွေ့)。
    #    ⇒ ပြင်း (DIFF_CORE) ကွာခြားမှုနဲ့ core bbox ⇒ 1.5% margin。
    for thr in (DIFF_CORE, DIFF_T):
        m = dd > thr
        rows = np.where(m.sum(1) > w * 0.012)[0]
        cols = np.where(m.sum(0) > h * 0.012)[0]
        if len(rows) >= 3 and len(cols) >= 3:
            e = 0.015
            return (max(0.0, cols[0] / w - e), max(0.0, rows[0] / h - e),
                    min(1.0, (cols[-1] + 1) / w + e), min(1.0, (rows[-1] + 1) / h + e))
    return None


def faces(pngs):
    """{png: (x0,y0,x1,y1)} — posecheck (Vision)"""
    if not os.path.exists(POSE) or not pngs:
        return {}
    d = tempfile.mkdtemp(prefix="bqc_")
    try:
        names = []
        for i, p in enumerate(pngs):
            q = os.path.join(d, f"f{i + 1:05d}.png")
            shutil.copy(p, q)
            names.append(p)
        r = subprocess.run([POSE, d, "1"], capture_output=True, text=True, timeout=300)
        out = {}
        rows = [json.loads(x) for x in (r.stdout or "").splitlines() if x.strip().startswith("{")]
        for i, f in enumerate(rows[:len(names)]):
            if not f.get("nf"):
                continue
            fa = max(1e-4, float(f.get("fa") or 0.015))
            w = (fa / 1.3) ** 0.5
            h = w * 1.3
            cx, cy = float(f.get("fx") or 0.5), float(f.get("fy") or 0.45)
            out[names[i]] = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        return out
    except Exception:
        return {}
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _inter(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def check(base, out, beats, zones, work, cap_top=CAP_TOP):
    """⇒ (issues [{i, type, at, kind, value}], fixes {i: 'flip'|'drop'}, rows)"""
    d = os.path.join(work, "beatqc")
    os.makedirs(d, exist_ok=True)
    rows, pairs = [], []
    for i, b in enumerate(beats):
        t = float(b["at"]) + min(1.1, 0.45 * float(b.get("dur") or 3))
        pa, pb = os.path.join(d, f"a{i}.png"), os.path.join(d, f"b{i}.png")
        if _frame(base, t, pa) and _frame(out, t, pb):
            pairs.append((i, pa, pb))
    fz = faces([pa for _, pa, _ in pairs])
    issues, fixes = [], {}
    for i, pa, pb in pairs:
        b = beats[i]
        z = "center" if b.get("pos") == "center" else zones.get(b["type"], "side")
        if np is not None:
            la = float(np.asarray(Image.open(pa).convert("L")).mean())
            lb = float(np.asarray(Image.open(pb).convert("L")).mean())
            if la > 30 and lb < la * 0.35:   # base ဗီဒီယို ပျောက် (နောက်ခံ အမည်း)
                issues.append(dict(i=i, type=b["type"], at=b["at"], kind="blackout", value=round(lb / la, 3)))
                fixes[i] = "drop"
                rows.append(dict(i=i, type=b["type"], at=b["at"], blackout=True))
                continue
        bb = bbox(pa, pb)
        row = dict(i=i, type=b["type"], at=b["at"], zone=z, bbox=bb, face=fz.get(pa))
        rows.append(row)
        if bb is None:
            issues.append(dict(i=i, type=b["type"], at=b["at"], kind="empty", value=0))
            fixes[i] = "drop"
            continue
        if bb[0] < 0.006 or bb[2] > 0.994:
            issues.append(dict(i=i, type=b["type"], at=b["at"], kind="edge", value=round(min(bb[0], 1 - bb[2]), 3)))
        if z != "center" and bb[3] > cap_top + 0.02:
            issues.append(dict(i=i, type=b["type"], at=b["at"], kind="caption", value=round(bb[3], 3)))
        f = fz.get(pa)
        if f and z != "center":
            fa = max(1e-6, (f[2] - f[0]) * (f[3] - f[1]))
            ov = _inter(bb, f) / fa
            row["face_cover"] = round(ov, 3)
            if ov > FACE_MAX:
                issues.append(dict(i=i, type=b["type"], at=b["at"], kind="face", value=round(ov, 3)))
                fixes[i] = "flip" if z == "side" and fixes.get(i) != "drop" else "drop"
    return issues, fixes, rows


def apply_fixes(beats, fixes, tried=()):
    out = []
    for i, b in enumerate(beats):
        f = fixes.get(i)
        if f == "drop" or (f == "flip" and i in tried):
            continue
        if f == "flip":
            b = dict(b, pos="left" if b.get("pos") != "left" else "right")
        out.append(b)
    return out


# ── vision critic (ရွေးချယ်) ────────────────────────────────────────────
RUBRIC = """You are a senior motion designer reviewing a 2026 talking-head edit. The image is a contact sheet;
each tile is the frame ~1s after an infographic appears. Score 1-10 for: readability (text size/contrast,
Burmese text not clipped), premium (looks like a high-end creator edit, not template-y), clutter, face
(graphics never cover the speaker's face). Return ONLY JSON:
{"readability":n,"premium":n,"clutter":n,"face":n,"notes":["short actionable fix", ...]}"""


def critic(out, beats, work, log=print):
    if os.environ.get("IKKI_VISION_CRITIC", "0") != "1" or not beats:
        return None
    try:
        import gemguard as G
    except ImportError:  # pragma: no cover
        from core import gemguard as G
    d = os.path.join(work, "beatqc")
    os.makedirs(d, exist_ok=True)
    tiles = []
    for i, b in enumerate(beats[:12]):
        p = os.path.join(d, f"c{i:02d}.jpg")
        if _frame(out, float(b["at"]) + 1.0, p):
            tiles.append(p)
    if not tiles:
        return None
    sheet = os.path.join(d, "sheet.jpg")
    cols = 3 if len(tiles) > 4 else 2
    rows = (len(tiles) + cols - 1) // cols
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", os.path.join(d, "c*.jpg"),
                    "-vf", f"tile={cols}x{rows}:padding=6", "-frames:v", "1", sheet], check=False)
    if not os.path.exists(sheet):
        return None
    img = base64.b64encode(open(sheet, "rb").read()).decode()
    body = {"contents": [{"parts": [{"text": RUBRIC}, {"inline_data": {"mime_type": "image/jpeg", "data": img}}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}}
    model = os.environ.get("IKKI_GEMINI_MODEL", "gemini-flash-latest")
    try:
        G.throttle()
        r = urllib.request.Request(G.endpoint(model), data=json.dumps(body).encode(),
                                   headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(r, timeout=120) as f:
            dd = json.loads(f.read())
        txt = "".join(p.get("text", "") for p in dd["candidates"][0]["content"]["parts"])
        res = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        log(f"  👁 vision critic · " + " · ".join(f"{k} {res.get(k)}" for k in ("readability", "premium", "clutter", "face")))
        return res
    except Exception as e:
        log(f"  ⓘ vision critic မရ ({type(e).__name__}) ⇒ ကျော်")
        return None
