"""စာတန်း နောက်ခံ ကွာဟမှု တိုင်းပြီး ဖတ်ရလွယ်အောင် ဆုံးဖြတ်သည်။

ပြဿနာ — ငါတို့ စာတန်းက အဖြူ ပါးပါး ဖြစ်ပြီး **မိုးကောင်းကင် · အဖြူနံရံ ·
အဖြူအင်္ကျီ** ပေါ်မှာ ပျောက်သွားသည် (Zin ၂၀၂၆-၀၉-၂၀)。

⚠️ **frame တစ်ချပ်တည်းနဲ့ မဆုံးဖြတ်ရ**。 ပြောသူ လှုပ်သည် · B-roll ဝင်သည် ⇒
   caption ကြာချိန် တစ်လျှောက် နမူနာ အများကြီး ယူပြီး **အဆိုးဆုံး** ကို
   ယူရမည်。 ပျမ်းမျှ ယူလျှင် တစ်စက္ကန့်လောက် ပျောက်တာကို လွတ်သွားမည်。

⚠️ ပုံကို ffmpeg နဲ့ **s16/gray raw** ထုတ်ပြီး ဖတ်သည် — PIL/ffprobe မလို。
   (၂၄-bit wav ကို ၁၆-bit အဖြစ် ဖတ်မိပြီး တိုင်းချက် တစ်ခုလုံး မှားခဲ့ဖူး ⇒
   format ကို **အတိအလင်း** သတ်မှတ်ရမည်。)
"""
import subprocess

# WCAG — ၄.၅:၁ က ပုံမှန်စာ、၃:၁ က စာလုံးကြီး。 စာတန်းက ကြီးသဖြင့် ၃:၁ သုံးသည်
MIN_RATIO = 3.0
# ဒီအောက် ဆိုလျှင် plate မဖြစ်မနေ (stroke နဲ့ မလုံလောက်)
PLATE_RATIO = 2.0

PLATE_ALPHA = 0.62          # ၅၅–၇၀% အကြား (Zin ရဲ့ spec)
SAMPLES = 9                 # caption တစ်ခုလျှင် နမူနာ frame


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def ratio(fg, bg):
    """WCAG ကွာဟမှု အချိုး — ၁:၁ (တူ) မှ ၂၁:၁ (အဖြူ/အမည်း)"""
    a, b = luminance(fg), luminance(bg)
    hi, lo = (a, b) if a >= b else (b, a)
    return (hi + 0.05) / (lo + 0.05)


def _hex(c):
    c = (c or "#FFFFFF").lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def band_rgb(video, t, top_pct, bot_pct, w=64, h=16):
    """`t` စက္ကန့်မှာ စာတန်း ဘန်း၏ **ပျမ်းမျှ အရောင်** — မရလျှင် None

    အကွက်ကို ၆၄×၁၆ သို့ ချုံ့ပြီး ယူသည် (ပိုက်စာ မလို · လျင်မြန်)。
    """
    y0 = max(0.0, min(1.0, top_pct))
    hh = max(0.01, min(1.0 - y0, bot_pct - top_pct))
    vf = (f"crop=iw:ih*{hh:.4f}:0:ih*{y0:.4f},"
          f"scale={w}:{h}:flags=area,format=rgb24")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", video,
         "-frames:v", "1", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True)
    d = r.stdout
    if len(d) < w * h * 3:
        return None
    n = w * h
    rs = sum(d[0::3]) / n
    gs = sum(d[1::3]) / n
    bs = sum(d[2::3]) / n
    return (rs, gs, bs)


def measure(video, start, end, fill="#FFFFFF",
            top_pct=0.78, bot_pct=0.95, samples=SAMPLES):
    """caption တစ်ခုအတွက် **အဆိုးဆုံး** ကွာဟမှု

    ပြန်ပေးသည် — `dict(ratio, worstAt, bg, ok, needPlate)`
    """
    n = max(2, int(samples))
    span = max(0.0, (end or start) - start)
    ts = [start + span * i / (n - 1) for i in range(n)] if span > 0 else [start]
    fg = _hex(fill)
    worst, worst_t, worst_bg = None, start, None
    for t in ts:
        bg = band_rgb(video, t, top_pct, bot_pct)
        if bg is None:
            continue
        rr = ratio(fg, bg)
        if worst is None or rr < worst:
            worst, worst_t, worst_bg = rr, t, bg
    if worst is None:
        # ⚠️ တိုင်းလို့ မရလျှင် **ဘေးကင်းသောဘက် ယူရမည်** — plate ထည့်သည်。
        #    「တိုင်းလို့ မရ = အဆင်ပြေ」ဟု ယူဆလျှင် ပျောက်နေတာ မသိရ。
        return dict(ratio=None, worstAt=start, bg=None,
                    ok=False, needPlate=True, measured=False)
    return dict(ratio=round(worst, 2), worstAt=round(worst_t, 2),
                bg=tuple(round(x) for x in worst_bg),
                ok=worst >= MIN_RATIO,
                needPlate=worst < PLATE_RATIO, measured=True)


def decide(m, fill="#FFFFFF"):
    """တိုင်းချက် → ဘာလုပ်ရမလဲ

    ပြန်ပေးသည် — `dict(mode, plateAlpha, strokePx, note)`
      `mode` ∈ `plain` · `stroke` · `plate`
    """
    if m.get("ok"):
        # ⚠️ ကွာဟမှု လုံလောက်လျှင်လည်း **အရိပ် ပါးပါး ထားသင့်** —
        #    ရုပ်က လှုပ်နေသဖြင့် တစ်ချိန်ချိန် ကပ်နိုင်သည်。
        return dict(mode="plain", plateAlpha=0.0, strokePx=2,
                    note="ကွာဟမှု လုံလောက်သည်")
    if m.get("needPlate"):
        return dict(mode="plate", plateAlpha=PLATE_ALPHA, strokePx=2,
                    note=f"ကွာဟမှု {m.get('ratio')} — အမှောင် အကွက် ခံသည်")
    return dict(mode="stroke", plateAlpha=0.0, strokePx=4,
                note=f"ကွာဟမှု {m.get('ratio')} — အနားသတ် ထူထူ")


def plan_captions(video, captions, top_pct=0.78, bot_pct=0.95, samples=SAMPLES):
    """caption စာရင်းတစ်ခုလုံးကို တိုင်းပြီး `props` ထဲ ဖြည့်ပေးသည်

    caption event တိုင်းမှာ `props.contrast` နဲ့ `props.backing` ဝင်လာမည်。
    QC သတိပေးချက် (`low_contrast`) ကိုလည်း ပြန်ပေးသည်。
    """
    warns = []
    for ev in captions or []:
        p = ev.setdefault("props", {})
        m = measure(video, ev.get("startTime") or 0.0,
                    ev.get("endTime") or 0.0,
                    fill=p.get("color") or "#FFFFFF",
                    top_pct=top_pct, bot_pct=bot_pct, samples=samples)
        d = decide(m, p.get("color") or "#FFFFFF")
        p["contrast"] = m
        p["backing"] = d
        if not m.get("ok"):
            warns.append(dict(code="low_contrast", eventId=ev.get("id"),
                              message=(f"{m.get('worstAt')}s မှာ ကွာဟမှု "
                                       f"{m.get('ratio')} — {d['note']}")))
    return captions, warns
