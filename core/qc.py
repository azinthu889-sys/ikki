#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · QC gate — မအောင်လျှင် **မပို့ရ**。

⚠️ ဤ gate က product ရဲ့ ရောင်းချက်ပါ။ CapCut မှာ မရှိ。
   UI မှာ ကတိပေးထားသဖြင့် ကုဒ်ထဲ တကယ် ရှိရမည် — ပြောရုံ မဟုတ်。
"""
import json, re, subprocess

# ⚠️ ပစ်မှတ်တွေက ခန့်မှန်းချက် မဟုတ် — တိုင်းထားပြီးသား house standard
# ⚠️ tp_max ကို −0.5 မှ **−1.0** သို့ တင်းလိုက်သည် — skill `ikki-presentation`
#    P5。 REF-A ကိုယ်တိုင် +0.19 dBTP ဖြင့် ကပ်နေသည် (ပြတ်သည်) — reference ရဲ့
#    mastering ကို မကူးရ、ဖွဲ့စည်းပုံကိုသာ ကူးရမည်。
T = dict(lufs=(-16.0, -12.0), tp_max=-1.0, cut_in_speech=0, min_dur=1.0)

# ── skill `ikki-presentation` ရဲ့ တိုင်းထားသော ဘောင်များ ──
SFX_MAX_PER_MIN = 1.5      # P3 — REF-A 1.1 · REF-B 0.6
SFX_MIN_GAP     = 8.0      # P3 — ၈ စက္ကန့်အတွင်း နှစ်ခု မရှိရ
SFX_LAYER_W     = 0.60     # ⚠️ ဒီအတွင်း ကပ်နေတဲ့ cue = **အသံတစ်ခု၏ အထပ်**
CARD_MIN, CARD_MAX = 1.0, 10.5   # P2
LUFS_LO, LUFS_HI   = -15.5, -13.5   # integrated (ပစ်မှတ် −14.5)

def _lufs(p):
    # ⚠️ ebur128 က **peak=true မပါလျှင် True peak မတိုင်း** — None ပြန်လာပြီး
    #    QC က သူ့ကိုယ်သူ့ bug နဲ့ ရှုံးသည် (တကယ် ဖြစ်ခဲ့)。
    r = subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",p,
        "-af","ebur128=peak=true:framelog=quiet","-f","null","-"],
        capture_output=True, text=True).stderr
    def g(k):
        m = re.search(rf"{k}:\s*(-?[\d.]+)", r)
        return float(m.group(1)) if m else None
    return g("I"), g("Peak")

def _probe(p):
    o = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height,nb_read_packets",
        "-show_entries","format=duration","-of","json","-count_packets",p],
        capture_output=True, text=True).stdout
    j = json.loads(o); s = j["streams"][0]
    return dict(w=s["width"], h=s["height"], dur=float(j["format"]["duration"]))

# WARN **the eleven gates never looked at the picture.** 2026-09-25 two
#    renders passed QC while being visibly broken: a near-black full-frame
#    card holding one line of text for 6.1 s (the speaker gone), and 4.5 s of
#    unkeyed green screen B-roll.
# WARN **my first `black_frames` threshold was wrong and Zin caught it.**
#    I gated on MEAN luminance over a run, which also fires on any deliberate
#    dark card -- it cannot tell "the render broke" from "this design is
#    dark". His spec instead: a真 render failure is `p99 < 16 AND max < 32`,
#    i.e. nothing bright anywhere in the frame. The 6.1 s card has max 255
#    and p99 245, so `render_black` correctly does NOT fire on it -- whether
#    that card should exist at all is a separate question, measured in group B.
# WARN `subject_gone` is **measured only, never failed** -- Zin has not set a
#    limit and will not until the reference figures are in. A check that fails
#    on a number nobody has justified is a guess with a red cross on it.
# WARN both colour/luma detectors were validated on files whose answer was
#    known BEFORE being wired in:
#      TH  OP6Nl6TC7SJSYkRhPC6O3A.mp4  green 0.1%
#      ZAE yrbcSfMrjsrmSwCh92ibgg.mp4  green 61.6% over 4.5 s
RENDER_BLACK_S = 0.3    # တကယ့် render ပျက်ချက် ကြာချိန် ကန့်သတ်
RENDER_BLACK_P99 = 16   # frame တစ်ခုလုံး p99 ဒီအောက် **နှင့်**
RENDER_BLACK_MAX = 32   # အမြင့်ဆုံး pixel ဒီအောက် ⇒ ဘာမှ မမြင်ရ
GREEN_SHARE = 0.20      # G−R>40 pixel ၂၀% ကျော် ⇒ key မလုပ်ရသေး
GREEN_MIN_S = 0.5       # ဒီထက် ကြာမှ ကျသည် (frame တစ်ခု ကြောင့် မကျရ)
GREEN_DELTA = 40


def _look(p, fps=2.0, w=160):
    """(render_black ကြာချိန်, အစိမ်း ကြာချိန်, အစိမ်း အမြင့်ဆုံး)

    ⚠️ ffmpeg တစ်ကြိမ်တည်း — frame တစ်ခုချင်း ဆွဲလျှင် ၇၀s ဗီဒီယိုမှာ
       ၁၄၀ ကြိမ် ခေါ်ရမည်。 ၁၆၀px ချုံ့တာက အချိုးကို မထိပါ。
    """
    import numpy as _np
    try:
        o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", p],
                           capture_output=True, text=True).stdout.strip().split(",")
        W0, H0 = int(o[0]), int(o[1])
        hh = int(round(w * H0 / W0 / 2)) * 2
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf",
                            f"fps={fps},scale={w}:-2", "-pix_fmt", "rgb24",
                            "-f", "rawvideo", "-"], capture_output=True)
        n = w * hh * 3
        k = len(r.stdout) // n
        if k < 2:
            return None, None, None
        a = _np.frombuffer(r.stdout[:k * n], _np.uint8)
        a = a.reshape(k, hh, w, 3).astype(_np.int16)
    except Exception:
        return None, None, None
    lum = 0.299 * a[:, :, :, 0] + 0.587 * a[:, :, :, 1] + 0.114 * a[:, :, :, 2]
    # ⚠️ **ပျမ်းမျှ မသုံးရ** — တမင် အမှောင် ကတ်ကိုပါ ဖမ်းမိမည်。
    #    p99 နဲ့ max ၂ ခုလုံး နိမ့်မှ 「ဘာမှ မမြင်ရ」 ဟု ဆိုနိုင်သည်。
    p99 = _np.percentile(lum, 99, axis=(1, 2))
    mx = lum.max(axis=(1, 2))
    blk = (p99 < RENDER_BLACK_P99) & (mx < RENDER_BLACK_MAX)
    # ⚠️ `G−R` တစ်ခုတည်းက စိမ်းပြာ ရုပ်ရှင်ကိုပါ ဖမ်းမိသည် (library ၄၃၂ ခု
    #    စကင်ရာ ၂၄ ခု ဖမ်းပြီး ၁၉ ခုက မှား)。 chroma key က R နှင့် B ၂ ခုလုံး
    #    နိမ့်သည် ⇒ `G−B` ပါ ထပ်စစ်သည် (၂၄ → ၅)。
    grn = (((a[:, :, :, 1] - a[:, :, :, 0]) > GREEN_DELTA)
           & ((a[:, :, :, 1] - a[:, :, :, 2]) > GREEN_DELTA)).mean(axis=(1, 2))
    gflag = grn >= GREEN_SHARE

    def _longest(mask):
        run = best = 0
        for v in mask:
            run = run + 1 if v else 0
            best = max(best, run)
        return best / float(fps)
    return _longest(blk), _longest(gflag), float(grn.max())


def _subject_gone(p, fps=2.0):
    """ပြောသူ မမြင်ရသော အဆက်မပြတ် အကြာဆုံး (s) — မရလျှင် None

    ⚠️ **တိုင်းရုံသာ** — Zin က ကန့်သတ်ချက် မချမှတ်ရသေးပါ。
    """
    try:
        import pose as _P
    except ImportError:
        try:
            from core import pose as _P
        except ImportError:
            return None
    try:
        if not _P.available():
            return None
        fr = _P.measure(p, fps=fps)
    except Exception:
        return None
    if not fr:
        return None
    run = best = 0
    for f in fr:
        run = run + 1 if int(f.get("nf") or 0) == 0 else 0
        best = max(best, run)
    return best / float(fps)


def run(out, cut_stats, theme, caps=None, cards=None, sfx=None, share=None,
        sfx_pol=None):
    """(ok, checks) — checks က UI ရဲ့ QC ကတ်တွေအတွက်"""
    m = _probe(out)
    I, tp = _lufs(out)
    C=[]
    def add(key, ok, val, want):
        C.append(dict(key=key, ok=bool(ok), value=val, want=want))

    # ① စကားပြောနေတုန်း ဖြတ်မိတာ — ဤ product ရဲ့ အဓိက ကတိ
    add("cut_in_speech", cut_stats.get("in_speech",0) == T["cut_in_speech"],
        cut_stats.get("in_speech",0), "0")
    # ② အသံ အဆင့်
    # ⚠️ ပစ်မှတ်က recipe အလိုက် ကွာသည် — ZAE −17.7 · ZJL −14 (နှစ်ခုလုံး တိုင်းထား)
    # ⚠️ ဘောင်က **ပုံသေ −15.5 … −13.5** (work order နောက်ဆက်တွဲ က)。
    #    အရင်က `tgt ± 2` ဖြစ်၍ −16.0 အထိ ခွင့်ပြုခဲ့ · ပြီးတော့ ±1.5 က
    #    အထက်ဘက်မှာ −12.5 အထိ ဖွင့်ပေးမိသေးသည် (မှား)。
    add("lufs", I is not None and LUFS_LO <= I <= LUFS_HI,
        None if I is None else round(I,1), f"{LUFS_LO:+.1f} … {LUFS_HI:+.1f}")
    add("true_peak", tp is not None and tp <= T["tp_max"],
        None if tp is None else round(tp,1), f"≤ {T['tp_max']}")
    # ③ အရွယ်အစား — theme နဲ့ ကိုက်ရမည်
    add("frame", m["w"]==theme["W"] and m["h"]==theme["H"],
        f"{m['w']}×{m['h']}", f"{theme['W']}×{theme['H']}")
    # ④ ဗလာ ဗီဒီယို မဖြစ်ရ
    add("duration", m["dur"] >= T["min_dur"], round(m["dur"],1), f"≥ {T['min_dur']}s")
    # ⑤ စာတန်း safe zone — ⚠️ ဘောင်ပြင် ထွက်လျှင် TikTok UI က ဖုံးသည်
    if caps is not None:
        # ⚠️ BOT နဲ့ မစစ်ရ — BOT က **ဂရပ်ဖစ်** အတွက် ကန့်သတ်ချက်ပါ
        #    (စာတမ်းပေါ် မတက်စေရန်)。 စာတန်းက အဲဒီအောက် ရှိရမှာပဲ。
        #    တကယ် စစ်ရမှာ — TikTok ရဲ့ UI ဖုံးတဲ့ အောက်ခြေ 320/1920 = 16.7%
        #    ကို ကျော်မကျော် (tiktok-safe-area မှ တိုင်းထား)。
        lim = theme.get("cap_max") or 0.833
        band = int(theme.get("cap_h", 0))
        maxy = int(theme["H"] * lim)
        add("caption_zone", band == 0 or band <= maxy,
            band or "—", f"≤ {maxy} ({lim*100:.0f}% of H)")
    # ⑥ ─ presentation layer (skill `ikki-presentation`) ─────────
    # ⚠️ P1 ရဲ့ ဘောင် 0.10–0.17 ဟာ **ZJL knowledge reference ၂ ခု**မှ。
    #    ZAE short မှာ full-frame card လုံးဝ မသုံး (ထောင့် overlay သာ) ⇒
    #    `share` မပေးလျှင် **မစစ်ရ**。 ZJL grade အတွက် တွက်ထားသော
    #    "luma median > 110" detector ကလည်း ZAE ရဲ့ အလင်း A-roll (၂၁၅) မှာ
    #    အလုပ် မဖြစ် — ဘောင်ရော detector ရော ချန်နယ်အလိုက် ဖြစ်သည်。
    if cards is not None and m["dur"] > 0:
        tot = sum(float(d) for _a, d in cards)
        sh = tot/m["dur"]
        if share:
            add("gfx_share", share[0] <= sh <= share[1], round(sh,3),
                f"{share[0]:.2f}–{share[1]:.2f}")
        # ⚠️ ၁.၀–၁၀.၅s ဘောင်က **motion card** အတွက် တိုင်းထားတာ。
        #    full-frame slide က မတူ — reference ၂ ခုရဲ့ slide ၂၃ ခုကို
        #    တိုင်းကြည့်ရာ **၀.၅s မှ ၁၇.၀s** အထိ ရှိသည် (စာရင်း ရှည်လျှင်
        #    ဖတ်ချိန် ပေးရ၍)。 ⇒ theme က ဘောင် ပေးလျှင် အဲဒါကို သုံးသည်。
        cmin = float(theme.get("card_min") or CARD_MIN)
        cmax = float(theme.get("card_max_s") or CARD_MAX)
        bad = [round(float(d),1) for _a, d in cards
               if not (cmin <= float(d) <= cmax)]
        add("card_len", not bad, bad or "—", f"{cmin}–{cmax}s")
    if sfx is not None and m["dur"] > 0:
        # ⚠️ **အထပ်ကို တစ်ခုလို့ ရေတွက်ရမည်**。 `dress.sfx()` က ဂရပ်ဖစ်
        #    တစ်ခုအတွက် `whoosh_in` (0.22s အလို) နဲ့ `click` ကို တွဲထုတ်သည် —
        #    နားထောင်သူ ကြားရတာက **အသံ တစ်ခု**、နှစ်ခု မဟုတ်。 ခွဲရေလျှင်
        #    ဘယ်တော့မှ 8s ဘောင်ကို မကျော်နိုင်ဘဲ QC က အမြဲ ကျမည် —
        #    တိုင်းထားသော ပစ်မှတ် (REF-A 1.1/min) ကလည်း **အသံဖြစ်ရပ်** ကို
        #    ရေတွက်ထားခြင်း ဖြစ်သည်、track အရေအတွက် မဟုတ်。
        ts = sorted(float(t) for t in sfx)
        moments = []
        for t in ts:
            if not moments or t - moments[-1] > SFX_LAYER_W:
                moments.append(t)
        # ⚠️ **အောက်ခြေကို ံ၀ စက္ကန့္ အနည်းဆုံး ထားရမည်**。 ၁၆s ကနေ
        #    「မိနစ်လွှင် ဘယ်နှစ်ချက်」 ကို တွက်လွှင် ၁ ချက်ပင် ၃.၇၅/min
        #    ဖြစ်သွားသည် ⇒ **၄၀s အောက် ဗီဒီယိုတိုင်းမှာ သုည သာ ဖြတ်နိုင်**
        #    (တိုင်းပြီး တွေ့ · ၂၀၂၆-၀၉-၂၁)。 ZAE short ၃၀–၆၀s နဲ့ headtop
        #    ၁၆s အားလုံး အကျုံး၀င်သဖြင့် SFX က သီအိုရီအရ SFX မဖြစ်နိုင်ခဲ့。
        #    ⚠️ **ဂိတ် ကိန်း (၁.၅) ကို မလျှော့ပာ** — reference (REF-A ၁.၁ ·
        #    REF-B ၀.၆) ကို မိနစ် အများအပြားကနေ တိုင်းထားသဖြင့် နမူနာ ၁၆s
        #    ကို မိနစ်အဖြစ် **ချဲတွက်လို့ မရ**ခြင်း ဖြစ်သည်。
        #    ⚠️ ထပ်ခွေမှုကို တားသော ဂိတ်က `sfx_spacing` (≥၈s) — **အတိအကျ
        #    ကျန်နေသည်** ⇒ ၁၆s မှာ ဖြစ်ရပ် ၂ ခု ဆိုလျှင် ၂.၀/min ⇒ ကျမည်。
        # ⚠️ **ဂိတ်က profile အလိုက်** — အောက်က ပုံသေ。 headtop ရဲ
        #    reference ၁ ပုဒ် (၂၄၀s စီ) တိုင်းရာ **၆.၂၅–၈.၅၀/min**
        #    ရှိသည် — ပုံသေ ၁.၅ က **၅ ဆ တင်း**သဖြင့် ၁၂၀s render တစ်ခုမှာ
        #    အသံ **တစ်ချက်တည်း** ပါပြီး Zin တစ်ချက်မှ မကြားရပါ (၂၀၂၆-၀၉-၂၁)。
        #    ⚠️ ပုံသေကို **မလျှော့ပါ** — တိုင်းထားသော profile ကိုသာ
        #       ကိုယ်ပိုင် ကိန်း ခွင့်ပြုသည် (`src` မှာ မှတ်ရမည်)。
        _pol = sfx_pol or {}
        _pm = float(_pol.get("per_min") or SFX_MAX_PER_MIN)
        _gp = float(_pol.get("gap") or SFX_MIN_GAP)
        per = len(moments)/(max(60.0, m["dur"])/60.0)
        add("sfx_density", per <= _pm, round(per,2), f"≤ {_pm}/min")
        gaps = [round(b-a, 1) for a, b in zip(moments, moments[1:])]
        close = [g for g in gaps if g < _gp]
        # ⚠️ အရင်က မကျလျှင် "—" ပြသဖြင့် **မတိုင်းရသေးသလို** မြင်ရသည်。
        #    ⇒ တကယ့် အနီးဆုံး အကွာကို ပြသည် — ✓ က အဓိပ္ပာယ် ရှိစေရန်。
        add("sfx_spacing", not close,
            (min(gaps) if gaps else "—"), f"≥ {_gp}s ခြား")
        add("sfx_moments", True, len(moments), f"cue {len(ts)} → အသံဖြစ်ရပ်")
    # ── မြင်ရသော ပျက်စီးမှု (၂၀၂၆-၀၉-၂၅ ထပ်ထည့်) ──────────────────
    _blk, _gdur, _gmax = _look(out)
    if _blk is not None:
        add("render_black", _blk <= RENDER_BLACK_S, round(_blk, 2),
            f"≤ {RENDER_BLACK_S}s (p99<{RENDER_BLACK_P99} · max<{RENDER_BLACK_MAX})")
    if _gdur is not None:
        add("chroma_green", _gdur <= GREEN_MIN_S,
            f"{_gdur:.1f}s @ {_gmax:.0%}",
            f"≤ {GREEN_MIN_S}s (G−R>{GREEN_DELTA} ≥{GREEN_SHARE:.0%})")
    # ⚠️ **တိုင်းရုံ — FAIL မလုပ်ရ**。 Zin: ကန့်သတ်ချက် မချမှတ်ရသေး。
    _sg = _subject_gone(out)
    if _sg is not None:
        add("subject_gone", True, round(_sg, 2), "တိုင်းရုံ (ကန့်သတ် မချရသေး)")
    ok = all(c["ok"] for c in C)
    return ok, C

def summary(C, my=True):
    return " · ".join(f"{c['key']}={c['value']}{'' if c['ok'] else ' ✗'}" for c in C)
