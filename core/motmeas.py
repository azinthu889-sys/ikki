# -*- coding: utf-8 -*-
"""overlay clip ရဲ့ **လှုပ်ရှားမှု** ကို တိုင်းသည် — `card_in` · `card_out` · easing。

⚠️ **ဤနေရာက render report ရဲ့ တစ်ခုတည်းသော အမှောင်ကွက် ဖြစ်ခဲ့သည်**。
   `MOTION    card_in — မတိုင်းရသေး · card_out — မတိုင်းရသေး · easing —
   မတိုင်းရသေး` ဟု **hardcode** ထားခဲ့သည် ⇒ ကတ်တွေ ပေါ်တာ သိပေမယ့်
   **ဘယ်လို ပေါ်တာ** ဘယ်တော့မှ မသိရ。 「premium မဆန်ဘူး」ဆိုတာ ဒီနေရာမှာ
   ပုန်းနေနိုင်ခြေ အမြင့်ဆုံး ဖြစ်သည်。

ပစ်မှတ် — `packs/headtop-premium/tokens.json` (reference ၂ ပုဒ် · ဖြစ်ရပ် ၂၁
ခုကနေ **တိုင်းယူထား**) —
    enter  ၀.၄၆၇s  (p25 ၀.၂၃၃ · p75 ၀.၇၃၃)
    exit   ၀.၂၀၀s  (p25 ၀.၁၃၃ · p75 ၀.၂၆၇)
    easing `cubic-bezier(.22,.8,.24,1)` — **spec သာ** (မတိုင်းရသေး)

⚠️ **ထွက်လာသော ဖိုင်ကနေ တိုင်းရမည်** — element frame ကနေ မဟုတ်。 v2 renderer
   (motion blur · look pass) က curve ကို ပြောင်းနိုင်သဖြင့် တကယ် ship သွားသော
   clip ကိုသာ တိုင်းရသည် (ဖြတ်ပြီး ဗီဒီယိုပေါ် တင်မတိုင်ခင်)。
"""
import os, subprocess

# ⚠️ **ဂိတ်ကို peak နဲ့ အချိုးကျ ထားရမည် — ကိန်းသေ မထားရ**。 alpha ပျမ်းမျှက
#    ဘောင် တစ်ခုလုံးအပေါ် ဖြစ်သဖြင့် စာလုံးလေး တစ်လုံးဆိုလျှင် ~၁–၃% သာ
#    ရှိသည် ⇒ ကိန်းသေ ၀.၀၆ နဲ့ စစ်လျှင် **pop အားလုံး ပယ်ခံ**မည်
#    (၂၀၂၆-၀၉-၂၁ စမ်းစဉ် ဖမ်းမိ — clip ၃ ခုလုံး `None` ပြန်ခဲ့)。
ON = 0.06              # peak ရဲ့ ၆% — ဒီအောက်က 「မပေါ်」
FULL = 0.94            # peak ရဲ့ ၉၄% — ဒီအထက်က 「ပြီးပြည့်စုံ ပေါ်」
FLOOR = 1e-3           # peak ဒီအောက်ဆို alpha မရှိ ဟု သတ်မှတ်
# ⚠️ **အရွယ်ကို ကိန်းသေ ထားရမည်** — `scale=64:-1` က အမြင့်ကို အချိုးကျ
#    ပေးသဖြင့် raw buffer ကို ပြန်ခွဲရာမှာ မှန်းရသည် ⇒ ၂s clip ကို
#    frame ၂၁၉၆ ဟု ဖတ်မိခဲ့သည် (တကယ် ၆၀)。 mean သာ လိုသဖြင့်
#    ပုံသဏ္ဌာန် ပျက်တာ အရေး မကြီးပါ ⇒ စတုရန်း ကိန်းသေ။
SMALL = 32


def alpha_series(mov, small=SMALL):
    """`(vals, fps)` — frame တစ်ခုချင်းရဲ့ alpha ပျမ်းမျှ (၀–၁)

    ⚠️ ProRes 4444 / qtrle နှစ်ခုလုံး alpha ပါသည် — `alphaextract` က
       alpha ကို gray အဖြစ် ထုတ်ပေးသည်。
    """
    try:
        import numpy as np
    except ImportError:
        return [], 0.0
    if not mov or not os.path.exists(mov):
        return [], 0.0
    fps = 30.0
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=r_frame_rate",
                            "-of", "csv=p=0", mov], capture_output=True, text=True)
        n, d = (r.stdout or "30/1").strip().split("/")
        fps = float(n) / float(d or 1)
    except Exception:
        pass
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", mov, "-vf",
                        f"format=yuva420p,alphaextract,scale={small}:{small}",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True)
    buf = r.stdout or b""
    if not buf:
        return [], fps
    a = np.frombuffer(buf, dtype=np.uint8).astype(np.float32) / 255.0
    px = small * small
    n_fr = len(a) // px
    if n_fr < 2:
        return [], fps
    return a[:n_fr * px].reshape(n_fr, px).mean(axis=1).tolist(), fps


def _bezier_area(p1x, p1y, p2x, p2y, n=200):
    """cubic-bezier ရဲ့ **ease area** — ၀ = မျဉ်းဖြောင့် · +၁ = ease-out အပြည့်"""
    tot = 0.0
    for i in range(n + 1):
        t = i / float(n)
        mt = 1 - t
        x = 3 * mt * mt * t * p1x + 3 * mt * t * t * p2x + t ** 3
        y = 3 * mt * mt * t * p1y + 3 * mt * t * t * p2y + t ** 3
        tot += (y - x)
    return round(2.0 * tot / (n + 1), 3)


# spec ရဲ့ easing — နှိုင်းယှဉ်ရန် ပစ်မှတ်
SPEC_EASE = _bezier_area(0.22, 0.8, 0.24, 1.0)

# Headtop Premium pack ရဲ့ measured timing band။ `SPEC_EASE` က curve spec
# ဖြစ်ပြီး alpha-only metric နဲ့ တိုက်ရိုက်တူမည်မဟုတ်သဖြင့် 0.30 ကို
# ship gate အဖြစ် သတ်မှတ်သည် — ဒီအောက်ဆို report မှာလည်း 「စက်ဆန်」ဟု
# ပြပြီးသား ဖြစ်သည်။
ENTER_BAND = (0.233, 0.733)
EXIT_BAND = (0.133, 0.267)
EASE_MIN = 0.30


def premium_checks(measured):
    """Headtop overlay အတွက် ship/no-ship QC checks ပြန်ပေးသည်。

    ယခင်က motion number ကို report မှာပြရုံသာပြပြီး QC gate မထဲထည့်ခဲ့လို့
    exit 0.1s, ease 0.15 ရှိသော render ကို `PASS` လို့ပို့မိခဲ့သည်။
    """
    m = measured or {}
    n = int(m.get("n") or 0)
    ins, outs, ease = m.get("in_s"), m.get("out_s"), m.get("ease")
    def _inside(v, band):
        return v is not None and band[0] <= float(v) <= band[1]
    return [
        dict(key="motion_measured", ok=n > 0, value=n or "—", want="≥ 1 overlay"),
        dict(key="motion_enter", ok=_inside(ins, ENTER_BAND), value=ins,
             want=f"{ENTER_BAND[0]:.3f}–{ENTER_BAND[1]:.3f}s"),
        dict(key="motion_exit", ok=_inside(outs, EXIT_BAND), value=outs,
             want=f"{EXIT_BAND[0]:.3f}–{EXIT_BAND[1]:.3f}s"),
        dict(key="motion_ease", ok=ease is not None and float(ease) >= EASE_MIN,
             value=ease, want=f"≥ {EASE_MIN:.2f} (ease-out)"),
    ]


def measure(mov):
    """`dict(in_s, out_s, hold_s, ease, frames, fps)` — မရလျှင် `None`

    `ease` — ဝင်ချိန်ရဲ့ **ease area**: ၀ = မျဉ်းဖြောင့် · အပေါင် = ease-out
             (အစမှာ သွက် · အဆုံးမှာ ငြိမ်) · အနုတ် = ease-in。
    """
    vals, fps = alpha_series(mov)
    if not vals or fps <= 0:
        return None
    n = len(vals)
    pk = max(vals)
    if pk <= FLOOR:
        return None
    on = ON * pk
    full = FULL * pk
    # ဝင်ချိန် — ပထမ မပေါ်သေးသည့်မှ ပြီးပြည့်စုံ ရောက်သည်အထိ
    i0 = next((i for i, v in enumerate(vals) if v > on), 0)
    i1 = next((i for i in range(i0, n) if vals[i] >= full), None)
    # ထွက်ချိန် — နောက်ဆုံး ပြီးပြည့်စုံမှ မပေါ်တော့သည်အထိ
    j1 = next((i for i in range(n - 1, -1, -1) if vals[i] > on), n - 1)
    j0 = next((i for i in range(j1, -1, -1) if vals[i] >= full), None)
    in_s = ((i1 - i0) / fps) if i1 is not None else None
    out_s = ((j1 - j0) / fps) if j0 is not None else None
    hold_s = ((j0 - i1) / fps) if (i1 is not None and j0 is not None
                                   and j0 > i1) else 0.0
    ease = None
    if i1 is not None and i1 - i0 >= 3:
        seg = vals[i0:i1 + 1]
        lo, hi = seg[0], seg[-1]
        if hi - lo > 1e-6:
            m = len(seg) - 1
            # normalise ပြီး မျဉ်းဖြောင့်နဲ့ ကွာဟမှု ဧရိယာ
            acc = 0.0
            for k, v in enumerate(seg):
                acc += ((v - lo) / (hi - lo)) - (k / float(m))
            ease = round(2.0 * acc / len(seg), 3)
    return dict(in_s=None if in_s is None else round(in_s, 3),
                out_s=None if out_s is None else round(out_s, 3),
                hold_s=round(hold_s, 3), ease=ease, frames=n,
                fps=round(fps, 2))


def summary(movs, log=None, cap=6):
    """clip များကို တိုင်းပြီး **အလယ်တန်း** ပြန်ပေးသည် — report အတွက်

    ⚠️ အားလုံး မတိုင်းပါ — clip တစ်ခုလျှင် ffmpeg တစ်ခါ ⇒ `cap` ခုသာ。
    """
    import statistics as st
    got = []
    for q in list(movs or [])[:cap]:
        r = measure(q)
        if r:
            got.append(r)
    if not got:
        return None
    def med(k):
        v = [x[k] for x in got if x.get(k) is not None]
        return round(st.median(v), 3) if v else None
    out = dict(n=len(got), in_s=med("in_s"), out_s=med("out_s"),
               hold_s=med("hold_s"), ease=med("ease"), spec_ease=SPEC_EASE)
    log and log(f"  လှုပ်ရှားမှု တိုင်းချက် · clip {out['n']} · "
                f"ဝင် {out['in_s']}s · ထွက် {out['out_s']}s · "
                f"ease {out['ease']} (spec {SPEC_EASE})")
    return out
