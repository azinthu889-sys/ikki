"""keyword pop ကို **မျက်နှာ ရှောင်ပြီး** နေရာချခြင်း。

⚠️ ဤဖိုင်ရဲ့ ကိန်းတွေကို `docs/HEADTALK_STYLE.md` ကနေ ယူထားသည် —
   reference `KCN4-2hyUBM` ရဲ့ full-res ဖရိန် ၆ ချပ်、စာလုံးအကွက် တစ်ခုချင်း
   တိုင်းချက် (၂၀၂၆-၀၉-၂၁)。 မှန်းဆ မဟုတ်ပါ。

⚠️ ယခင် ဆုံးဖြတ်ချက်ကို **ပြန်လှန်**သည် — 「ပြောသူက ၆၄% ယူသဖြင့် ထပ်တင်ရန်
   ၅.၆%H သာ ကျန်」ဟု ယူဆကာ ဖြတ်ပြောင်းသို့ ပြောင်းခဲ့သည်。 Reference က
   စာလုံးကို **ပြောသူပေါ် တိုက်ရိုက် တင်**ပြီး အနက် အနားသတ်နဲ့ ဖတ်စေသည်。
   ⇒ 「ကျန်နေရာ」ကို ဘောင်တစ်ခုလုံးနဲ့ မတွက်ရ — **မျက်နှာနဲ့သာ** တွက်ရမည်。
"""

# ── တိုင်းထားသော ဘောင် (v4 · ဖရိန် ၆ ချပ် · blob ၉ ခု) ──────────
TEXT_H = 0.101          # စာလုံး အမြင့် — အလယ်တန်း (အနည်းဆုံး ၀.၀၈၁ · အများဆုံး ၀.၁၆၃)
TEXT_H_MIN = 0.075
TEXT_H_MAX = 0.165
CX_MIN, CX_MAX = 0.12, 0.86     # အလယ်မှတ် x — တိုင်းချက်ရဲ့ အစွန်းနှစ်ဖက်
CY_MIN, CY_MAX = 0.20, 0.81     # အလယ်မှတ် y
MAX_AT_ONCE = 3                 # 284s မှာ `WHY?` ၃ ခု တစ်ပြိုင်နက်

# ⚠️ မျက်နှာ **အနားကွက်** — မျက်နှာနဲ့ ကပ်နေလျှင် ဖတ်ရခက်ပြီး ရုပ်ဆိုးသည်。
FACE_PAD = 0.045


def face_box(frames, t0, t1, ar=1.30):
    """`pose.measure()` ရဲ့ frame များကနေ ဝင်းဒိုးအတွင်း မျက်နှာ **အကုန် ဖုံးသော**
    အကွက် `(x0, y0, x1, y1)` (အချိုးဖြင့်) — မတွေ့လျှင် `None`。

    ⚠️ `fa` က **ဧရိယာ အချိုး**。 မျက်နှာက အမြင့် ≈ ၁.၃ × အကျယ် ⇒
       w = √(fa / ar) · h = w × ar (ဘောင်ရဲ့ အချိုးနဲ့ ကိုက်အောင်)。
    ⚠️ ဝင်းဒိုးအတွင်း **အကုန်** ဖုံးရမည် — frame တစ်ခုတည်းနဲ့ တွက်လျှင်
       ပြောသူ ရွေ့သွားချိန် စာလုံးက မျက်နှာပေါ် ရောက်သွားမည်。
    """
    hit = [f for f in (frames or [])
           if f.get("nf") and t0 - 0.25 <= float(f.get("t", 0)) <= t1 + 0.25]
    if not hit:
        hit = [f for f in (frames or []) if f.get("nf")]
    if not hit:
        return None
    x0 = y0 = 1.0
    x1 = y1 = 0.0
    for f in hit:
        fa = max(1e-4, float(f.get("fa") or 0.015))
        w = (fa / ar) ** 0.5
        h = w * ar
        cx, cy = float(f.get("fx") or 0.5), float(f.get("fy") or 0.45)
        x0 = min(x0, cx - w / 2); x1 = max(x1, cx + w / 2)
        y0 = min(y0, cy - h / 2); y1 = max(y1, cy + h / 2)
    return (max(0.0, x0 - FACE_PAD), max(0.0, y0 - FACE_PAD),
            min(1.0, x1 + FACE_PAD), min(1.0, y1 + FACE_PAD))


def _hit(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def slots(box, tw, th, step=0.04, avoid=()):
    """မျက်နှာနဲ့ **မထပ်သော** နေရာများ — `[(cx, cy, အမှတ်)]` အမှတ်များစဉ်。

    အမှတ်ပေးပုံ — မျက်နှာနဲ့ ဝေးလေ ကောင်းလေ、ဘောင်အစွန်းနဲ့ ကပ်လျှင် လျှော့。
    """
    out = []
    cx = CX_MIN
    while cx <= CX_MAX + 1e-9:
        cy = CY_MIN
        while cy <= CY_MAX + 1e-9:
            r = (cx - tw / 2, cy - th / 2, cx + tw / 2, cy + th / 2)
            if r[0] >= 0.02 and r[2] <= 0.98 and r[1] >= 0.02 and r[3] <= 0.98:
                if (box and _hit(r, box)) or any(_hit(r, a) for a in avoid):
                    pass
                else:
                    if box:
                        bx, by = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                        d = ((cx - bx) ** 2 + (cy - by) ** 2) ** 0.5
                    else:
                        d = abs(cx - 0.5) + abs(cy - 0.5)
                    edge = min(r[0], 1 - r[2], r[1], 1 - r[3])
                    out.append((round(cx, 3), round(cy, 3),
                                round(d + min(edge, 0.08) * 1.5, 4)))
            cy += step
        cx += step
    out.sort(key=lambda s: -s[2])
    return out


def caption_band(cap_base=0.92, cap_h=0.13):
    """စာတန်း ယူထားသော အကွက် — pop က ဒီထဲ မဝင်ရ。

    ⚠️ မရှောင်လျှင် အဝါ pop က စာတန်း အမှောင်အကွက်ပေါ် ထပ်ပြီး နှစ်ခုလုံး
       ဖတ်မရဖြစ်မည် (IKKI က `cap_base` ၀.၉၂ မှာ ချသည်)。
    """
    return (0.0, max(0.0, cap_base - cap_h), 1.0, 1.0)


def pick(frames, t0, t1, tw, th, used=(), box=None, avoid=()):
    """နေရာ တစ်ခု ရွေး — `(cx, cy)` · မရလျှင် `None`。

    `used` — ယခင် ရွေးပြီးသား `(cx, cy, tw, th)` များ。 **မထပ်ရ** —
    reference မှာ တစ်ပြိုင်နက် ၃ ခုအထိ ရှိသော်လည်း တစ်ခုနဲ့တစ်ခု မထပ်ပါ。
    """
    if box is None:
        box = face_box(frames, t0, t1)
    for cx, cy, _s in slots(box, tw, th, avoid=avoid):
        r = (cx - tw / 2, cy - th / 2, cx + tw / 2, cy + th / 2)
        if any(_hit(r, (ux - uw / 2, uy - uh / 2, ux + uw / 2, uy + uh / 2))
               for ux, uy, uw, uh in used):
            continue
        return (cx, cy)
    return None
