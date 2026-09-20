"""shot တစ်ခုချင်း အပြင်/အတွင်း ခွဲပြီး သင့်တော်သော grade ရွေးသည်။

ပြဿနာ — ယခု grade က **ဗီဒီယိုတစ်ခုလုံး တစ်မျိုးတည်း** ချသည်။ အပြင်ဘက်
ကျောင်းဝင်း (အလင်းပြင်းပြီး highlight ပြတ်နေ) နဲ့ အတွင်းဘက် (အဝါဓာတ်)
ကို တူညီစွာ ကိုင်လျှင် နှစ်ခုလုံး မကောင်းပါ (Zin ၂၀၂၆-၀၉-၂၀)。

⚠️ **ကိန်းတွေကို `IKKI_Premium_v2.mp4` ကနေ တိုင်းယူထားသည်**、မှန်းဆ မဟုတ်ပါ —
   အပြင်  : အလင်း ၁၇၆–၂၂၅ · p95 = **၂၅၅ (ပြတ်နေပြီး)** · R/B ၁.၀၁–၁.၁၂
   အတွင်း : အလင်း  ၉၄–၁၁၈ · p95 ၁၇၃–၁၉၇ · R/B ၁.၁၄–၁.၂၂ (tungsten)

⚠️ `curves` · `eq` · `colorlevels` တို့က **timeline `enable=` ကို ထောက်ပံ့သည်**
   (စမ်းပြီး: ၀.၅s မှာ ကွာ ၇၅.၇ · ၃.၀s မှာ ၀.၀) ⇒ ဖြတ်ပြီး concat ပြန်လုပ်စရာ
   မလိုပါ — AAC drift ထောင်ချောက် ရှောင်နိုင်သည်。
"""
import subprocess

import numpy as np

# ── တိုင်းထားသော အပိုင်းအခြား ─────────────────────────────────
BRIGHT_LUM = 150.0      # ဒီအထက် = အပြင် (တိုင်းချက်မှာ ၁၂၅↔၁၇၆ ကြားမှာ ကွက်လပ်)
CLIP_P95 = 245.0        # ဒီအထက် = highlight ပြတ်နေပြီး
WARM_RATIO = 1.10       # R/B ဒီအထက် = အဝါဓာတ် (tungsten)

OUTDOOR, INDOOR, NEUTRAL = "outdoor", "indoor", "neutral"


def stats(video, t, w=96, h=54):
    """`t` စက္ကန့်မှာ — `dict(lum, p95, warm, sky)` · မရလျှင် None"""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.2f}", "-i", video,
         "-frames:v", "1", "-vf", f"scale={w}:{h}:flags=area,format=rgb24",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    d = r.stdout
    if len(d) < w * h * 3:
        return None
    a = np.frombuffer(d, np.uint8).astype(np.float32).reshape(h, w, 3)
    g = a.mean(2)
    top = a[:max(1, h // 4)]
    sky = float(((top[..., 2] > top[..., 0] + 8) & (top[..., 2] > 110)).mean() * 100)
    return dict(lum=float(g.mean()), p95=float(np.percentile(g, 95)),
                warm=float(a[..., 0].mean() / max(1.0, a[..., 2].mean())),
                sky=sky)


def classify(s):
    """တိုင်းချက် → `outdoor` · `indoor` · `neutral`"""
    if not s:
        return NEUTRAL
    if s["lum"] >= BRIGHT_LUM or s["p95"] >= CLIP_P95:
        return OUTDOOR
    if s["warm"] >= WARM_RATIO:
        return INDOOR
    return NEUTRAL


def treatment(kind, s=None):
    """အမျိုးအစား → grade ပြင်ချက်

    ⚠️ Zin ရဲ့ တားမြစ်ချက် — 「no crushed blacks, over-saturation, fake
       cinematic teal/orange, or excessive vignette」。 ⇒ အနက်ကို မဖိရ ·
       sat ၁.၀၆ ထက် မတင်ရ · vignette ၀.၂ ထက် မတင်ရ · အရောင် မလှည့်ရ。
    """
    if kind == OUTDOOR:
        # highlight ပြန်ဆယ် — အပေါ်ပိုင်းကို ချသည်、အနက်ကို မထိ
        t = dict(lv_imin=0.00, lv_imax=1.00, lv_omin=0.00, lv_omax=0.94,
                 curve="0/0 0.25/0.245 0.55/0.545 0.85/0.83 1/0.97",
                 sat=1.03, cbal=False, vign=0.0)
        if s and s["p95"] >= 252:
            # ⚠️ တကယ် ပြတ်နေလျှင် ပိုချရသည် — ဒါပေမယ့် အလုံးစုံ မမှောင်စေရ
            t["lv_omax"] = 0.90
        return t
    if kind == INDOOR:
        # အဝါဓာတ် လျှော့ — ပူနွေးမှု အနည်းငယ် ကျန်စေသည်
        return dict(lv_imin=0.02, lv_imax=0.98, lv_omin=0.01, lv_omax=1.00,
                    curve="0/0 0.25/0.26 0.50/0.52 0.75/0.77 1/1",
                    sat=1.04, cbal=True, vign=0.0)
    return dict(sat=1.02, cbal=False, vign=0.0)


def scan(video, dur, step=3.0, log=None):
    """ဗီဒီယိုတစ်ခုလုံး စစ်ပြီး **အမျိုးအစား အပိုင်းများ** ပြန်ပေးသည်

    ပြန်ပေးသည် — `[(start, end, kind, stats)]`
    ⚠️ ဆက်တိုက် တူသော အပိုင်းများကို **ပေါင်းရမည်** — မပေါင်းလျှင်
       ၃ စက္ကန့်တိုင်း grade ပြောင်းပြီး မှိတ်တုတ်မှိတ်တုတ် ဖြစ်မည်。
    """
    if dur <= 0:
        return []
    ts = [t for t in np.arange(step / 2, dur, step)]
    marks = []
    for t in ts:
        s = stats(video, float(t))
        marks.append((float(t), classify(s), s))
    if not marks:
        return []
    segs = []
    cur_k, cur_a, cur_s = marks[0][1], 0.0, marks[0][2]
    for i, (t, k, s) in enumerate(marks[1:], 1):
        if k != cur_k:
            mid = (marks[i - 1][0] + t) / 2.0
            segs.append((round(cur_a, 2), round(mid, 2), cur_k, cur_s))
            cur_k, cur_a, cur_s = k, mid, s
    segs.append((round(cur_a, 2), round(dur, 2), cur_k, cur_s))
    # ⚠️ တိုလွန်းသော အပိုင်း (< ၁.၅s) ကို ရှေ့ကဟာနဲ့ ပေါင်းသည်
    out = []
    for a, b, k, s in segs:
        if out and (b - a) < 1.5:
            pa, pb, pk, ps = out[-1]
            out[-1] = (pa, b, pk, ps)
        else:
            out.append((a, b, k, s))
    if log:
        n = {}
        for a, b, k, _ in out:
            n[k] = n.get(k, 0) + 1
        log(f"  shotlook · အပိုင်း {len(out)} ခု · " +
            " · ".join(f"{k} {v}" for k, v in sorted(n.items())))
    return out


def grade_events(video, dur, step=3.0, log=None):
    """plan ရဲ့ `colorGrades` event များ ထုတ်ပေးသည်"""
    out = []
    for i, (a, b, k, s) in enumerate(scan(video, dur, step, log), 1):
        t = treatment(k, s)
        why = {OUTDOOR: "အပြင် အလင်းပြင်း — highlight ပြန်ဆယ်သည်",
               INDOOR: "အတွင်း အဝါဓာတ် — white balance ပြင်သည်",
               NEUTRAL: "ပုံမှန် — အနည်းငယ်သာ"}[k]
        if s and s.get("p95", 0) >= 252 and k == OUTDOOR:
            why += f" (p95 {s['p95']:.0f} — ပြတ်နေပြီး)"
        out.append(dict(
            id=f"grd{i:03d}", startTime=a, endTime=b,
            layer="grade", type="grade", props=t,
            style=dict(kind=k),
            reason=why, confidence=0.7 if k != NEUTRAL else 0.5))
    return out


def windowed(fc, a, b):
    """filter chain တစ်ခုကို `enable='between(t,a,b)'` နဲ့ ကန့်သတ်သည်

    ⚠️ filter **တစ်ခုချင်းစီ** မှာ ထည့်ရမည် — chain အဆုံးမှာ တစ်ခါတည်း
       ထည့်လျှင် နောက်ဆုံး filter တစ်ခုသာ ကန့်သတ်ခံရမည်。
    ⚠️ `curves` ရဲ့ argument ထဲ `,` ပါသဖြင့် `,` နဲ့ ခွဲလို့ မရ —
       ကွင်းပြင်ပက `,` မှာသာ ခွဲရသည်。
    """
    parts, depth, cur = [], 0, ""
    for ch in fc:
        if ch == "'":
            depth ^= 1
        if ch == "," and not depth:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)
    en = f"enable='between(t,{a:.2f},{b:.2f})'"
    return ",".join(f"{p}:{en}" if p else p for p in parts if p)
