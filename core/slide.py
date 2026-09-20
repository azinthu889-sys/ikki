#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · **full-frame slide** — Knowledge Sharing ရဲ့ အဓိက ဂရပ်ဖစ်。

⚠️ အရင်က lower-third အသေးလေးတွေ (၂.၂s) ပဲ ထုတ်ခဲ့သဖြင့် ဂရပ်ဖစ် အချိန်
   **၂.၅%** သာ ရခဲ့ပြီး ဗီဒီယိုက "မမိုက်ဘူး" ဖြစ်ခဲ့သည်。 Zin ပေးသော
   reference (၉:၁၅) ကို တိုင်းကြည့်ရာ —

     full-frame slide   ၁၂ ခု · ၇၄.၅s = **၁၃.၄%**  ← recipe band 0.10–0.17 နဲ့ ကိုက်
     တစ်ခုချင်း အရှည်   ၁.၅–၁၇.၀s · ပျမ်းမျှ ၆.၂s
     အကြိမ်ရေ          ~၄၆s လျှင် တစ်ခါ
     နောက်ခံ           အဖြူ ၂၅၅/၂၅၅ · ရောင်စဉ် ၀.၀၀–၀.၀၆ (အရောင် မရှိသလောက်)
     မင် ဖုံးအုပ်မှု     ၀.၈–၃.၈%
     အနား              အလယ်ထား ၀.၃၀–၀.၃၈ · နှစ်တိုင် ၀.၁၅

⚠️ **အဖြူ နောက်ခံက အကြောင်းရှိသည်** — footage နဲ့ ကွာဟမှု ရစေရန်。
   reference footage ၆၉/၂၅၅ ⇒ ကွာဟမှု ၁၈၆。 ငါတို့ footage ၁၀၁/၂၅၅ ⇒
   အဖြူဆိုလျှင် ၁၅၄၊ အမှောင်ဆိုလျှင် ၈၁ သာ ⇒ **အဖြူက ပိုအားကောင်း**。

⚠️ မြန်မာစာကို **PIL နဲ့ မရေးရ** — ဒီစက်ရဲ့ Pillow မှာ raqm မပါ၍
   shaping မလုပ်ဘဲ ဆွဲသည် ("တစ်ယောက်" → "တစ်ယေကာ")。 CoreText (`cttext`)
   ကိုသာ သုံးရမည်。
"""
import json, os, subprocess, tempfile

MK = os.environ.get(
    "MOTIONKIT",
    "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")
CTBIN = os.path.join(MK, "cttext")

# ⚠️ **ထွက်ဘောင်ရဲ့ အရွယ်ကို လိုက်ရမည်**。 ၂၀၂၆-၀၉-၂၀: ဤနေရာမှာ
#    ၁၉၂၀×၁၀၈၀ သေချာ ရေးထားပြီး ထွက်ဗီဒီယိုက ၁၀၈၀×၁၄၄၀ (3:4) ဖြစ်သဖြင့်
#    slide ရဲ့ **ညာဘက် ၄၄% ပြတ်**ကာ ခေါင်းစဉ်နဲ့ bullet တွေ စာလုံးအလယ်မှာ
#    ဖြတ်ခံရပြီး、အောက်မှာလည်း ၃၆၀px ချောင်းကြီး ကျန်ခဲ့သည် (j_bd28f6df827f —
#    Zin: 「quality 0」)。 ⇒ render မလုပ်ခင် `setsize()` ခေါ်ရမည်。
W, H = 1920, 1080


def setsize(w, h):
    """slide ဘောင်ကို ထွက်ဗီဒီယိုရဲ့ အရွယ်နဲ့ ကိုက်အောင် ချိန်သည်。

    module ထဲ အရာအားလုံးက `W`/`H` ရဲ့ **အချိုး**နဲ့ ဆွဲထားသဖြင့်
    ဒါတစ်ခု ပြောင်းရုံနှင့် အလျားလိုက် · ဒေါင်လိုက် နှစ်မျိုးလုံး ရသည်。
    """
    global W, H
    W, H = int(w), int(h)
    return W, H
PAPER  = (255, 255, 255)
INK    = (18, 20, 24)
MUTE   = (122, 128, 138)
DOT    = (232, 233, 236)          # ⚠️ အလွန် ဖျော့ရမည် — ပေါ်လျှင် ညစ်သည်
FALLBACK = "Helvetica,HiraginoSans-W3"

_MEAS = {}


def available():
    return os.path.exists(CTBIN)


def _run(sp):
    if not os.path.exists(CTBIN):
        raise RuntimeError(f"cttext မတွေ့: {CTBIN}")
    r = subprocess.run([CTBIN], input=json.dumps(sp).encode(), capture_output=True)
    if r.returncode:
        raise RuntimeError("cttext: " + r.stderr.decode()[:300])
    return json.loads(r.stdout.decode() or "{}")


def measure(text, px, font):
    """စာသား အကျယ် (px)。 **အက္ခရာရေနဲ့ မမှန်းရ** — မြန်မာစာမှာ ၂ ဆ လွဲသည်。"""
    k = (text, px, font)
    if k not in _MEAS:
        r = _run(dict(text="", font=font, fallback=FALLBACK, size=px, w=10, h=10,
                      fill="#000000", frames=[], measure=[text]))
        _MEAS[k] = float(r[0]) if isinstance(r, list) and r else 0.0
    return _MEAS[k]


def _text_png(text, px, font, color, align="left"):
    """စာသားတစ်ကြောင်း → RGBA numpy (မင်အတိုင်း ဖြတ်ပြီး)。"""
    import numpy as np
    from PIL import Image
    w = max(64, int(measure(text, px, font) * 1.15 + px))
    h = int(px * 2.4)
    fd, p = tempfile.mkstemp(suffix=".png"); os.close(fd)
    try:
        _run(dict(text=text, font=font, fallback=FALLBACK, size=px, w=w, h=h,
                  fill="#%02X%02X%02X" % tuple(color), unit="cluster", align=align,
                  frames=[{"out": p, "words": []}]))
        a = np.asarray(Image.open(p).convert("RGBA")).copy()
    finally:
        try: os.unlink(p)
        except OSError: pass
    ys, xs = np.nonzero(a[..., 3] > 6)
    if len(xs) == 0:
        return np.zeros((2, 2, 4), np.uint8)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _wrap(text, px, font, maxw):
    """မြန်မာစာကို **တိုင်းပြီးမှ** ခွဲသည်。 space မရှိလျှင် cluster အလိုက်。"""
    if measure(text, px, font) <= maxw:
        return [text]
    out, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if cur and measure(t, px, font) > maxw:
            out.append(cur); cur = w
        else:
            cur = t
    if cur: out.append(cur)
    # space မရှိသော ရှည်လျားစာကြောင်း — အက္ခရာအလိုက် ဖြတ်ရသည်
    fixed = []
    for line in out:
        while measure(line, px, font) > maxw and len(line) > 1:
            lo, hi = 1, len(line)
            while lo < hi:
                mid = (lo + hi) // 2
                if measure(line[:mid], px, font) <= maxw: lo = mid + 1
                else: hi = mid
            fixed.append(line[:max(1, lo - 1)]); line = line[max(1, lo - 1):]
        if line: fixed.append(line)
    return fixed


def _paste(im, arr, x, y):
    """RGBA numpy ကို canvas ပေါ် alpha နဲ့ ထပ်သည်。"""
    from PIL import Image
    if arr is None or arr.shape[0] < 2: return
    im.alpha_composite(Image.fromarray(arr), (int(x), int(y)))


# ══ chrome — slide တိုင်းမှာ တူညီသော ဖွဲ့စည်းပုံ ═══════════════
# ⚠️ ပထမဗားရှင်းက **စာသားချည်းပဲ** ဖြစ်ပြီး အလွတ်နေရာ များလွန်းသဖြင့်
#    "ပရော် မဟုတ်ဘူး" ဖြစ်ခဲ့သည်。 ပရော်ဖက်ရှင်နယ် slide မှာ စာသားအပြင် —
#      · အပေါ်မှာ မျဉ်းပါးနဲ့ အညွှန်း (ဘယ်နှစ်ခုမြောက်လဲ သိစေရန်)
#      · အောက်မှာ ဘရန်း စာတန်းသေး
#      · နောက်ခံမှာ **ကိန်းကြီး ဖျော့ဖျော့** — အလွတ်နေရာကို ဖွဲ့စည်းပေးသည်
#    ဒါတွေက ပုံလှအောင် ထည့်တာ မဟုတ်ဘဲ **နေရာလွတ်ကို အဓိပ္ပာယ် ရှိစေ**သည်。
HAIR  = (230, 231, 234)
GHOST = (243, 244, 246)
ML    = 0.115                      # ဘယ်/ညာ အနား (တိုင်းထားသော ၀.၁၄ ထက် နည်းနည်း ကျဲ)
TOPR  = 0.118                      # အပေါ် မျဉ်း
BOTR  = 0.882                      # အောက် မျဉ်း

_MM = {}


def _mmnum(n):
    """1 → '၀၁' (မြန်မာ ဂဏန်း)。"""
    d = "၀၁၂၃၄၅၆၇၈၉"
    return "".join(d[int(c)] for c in f"{int(n):02d}")


def _canvas(accent, index=None, total=None, brand="", lat="Helvetica-Bold",
            mmf="Pyidaungsu-Bold", ghost=None):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(im)
    # အလွန်ဖျော့သော အစက်ကွက် — နောက်ခံ တစ်သားတည်း မဖြစ်စေရန်
    for y in range(46, H, 48):
        for x in range(46, W, 48):
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=DOT + (255,))
    L, R = int(W * ML), int(W * (1 - ML))
    # ⚠️ နောက်ခံ ကိန်းကြီးကို **အရင် ဆွဲရမည်** — စာသားက အပေါ်က တက်ရန်
    if ghost:
        gb = _text_png(str(ghost), int(H * 0.62), lat, GHOST)
        if gb.shape[1] > 0:
            _paste(im, gb, R - gb.shape[1] + int(W * 0.035),
                   int(H * 0.30))
    d.line([L, int(H * TOPR), R, int(H * TOPR)], fill=HAIR + (255,), width=2)
    d.line([L, int(H * BOTR), R, int(H * BOTR)], fill=HAIR + (255,), width=2)
    if index and total:
        t = f"{_mmnum(index)} / {_mmnum(total)}"
        ib = _text_png(t, int(H * 0.024), mmf, MUTE)
        _paste(im, ib, L, int(H * TOPR) - ib.shape[0] - int(H * 0.018))
        # အညွှန်းဘေးက တိုတောင်းသော accent
        d.rounded_rectangle([R - int(W * 0.030), int(H * TOPR) - 9,
                             R, int(H * TOPR) - 3], radius=3, fill=accent)
    if brand:
        bb = _text_png(brand.upper(), int(H * 0.021), lat, MUTE)
        _paste(im, bb, L, int(H * BOTR) + int(H * 0.020))
    return im


def _fit(text, font, maxw, hi, lo, maxlines):
    """အရွယ်ကို **အမြင့်ဆုံးကနေ လျှော့ရင်း** ကိုက်အောင် ရှာသည်。

    ⚠️ စာသားကို ဖြတ်ပစ်၍ **မရ** — Zin တွေ့ခဲ့သော "…ကျန်ခဲ" မျိုး ဖြစ်မည်。
       အရွယ် လျှော့ပြီး စာကြောင်း ခွဲရသည်。
    """
    px = hi
    while px > lo:
        ls = _wrap(text, px, font, maxw)
        if len(ls) <= maxlines: return px, ls
        px = int(px * 0.94)
    return lo, _wrap(text, lo, font, maxw)[:maxlines]


def statement(text, kicker="", accent="#FFC400", mmf="Pyidaungsu-Bold",
              mmr="Pyidaungsu", lat="Helvetica-Bold", index=None, total=None,
              brand=""):
    """မှတ်သားဖွယ် စကားတစ်ခွန်း — အလယ်ထား · ဖွင့်ကိုးကားအမှတ် ကြီးကြီးနှင့်。"""
    from PIL import ImageDraw
    im = _canvas(accent, index, total, brand, lat, mmf,
                 ghost=_mmnum(index) if index else None)
    d = ImageDraw.Draw(im)
    L, R = int(W * ML), int(W * (1 - ML))
    maxw = R - L - int(W * 0.06)
    px, lines = _fit(text, mmf, maxw, int(H * 0.085), int(H * 0.044), 3)
    blocks = [_text_png(l, px, mmf, INK) for l in lines]
    gap = int(px * 0.30)
    tot = sum(b.shape[0] for b in blocks) + gap * (len(blocks) - 1)
    y = (H - tot) // 2
    # ကြီးမားသော ဖွင့်ကိုးကားအမှတ် — စကားတစ်ခွန်းဆိုတာ ပြသည်
    q = _text_png("“", int(H * 0.20), lat, (accent if isinstance(accent, tuple)
                                                 else _hex2rgb(accent)))
    _paste(im, q, L, y - int(H * 0.085))
    for b in blocks:
        _paste(im, b, L + int(W * 0.045), y)
        y += b.shape[0] + gap
    d.rounded_rectangle([L + int(W * 0.045), y + int(H * 0.030),
                         L + int(W * 0.045) + int(W * 0.055),
                         y + int(H * 0.030) + 7], radius=4, fill=accent)
    return im


def _hex2rgb(h):
    h = str(h).lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def bullets(head, items, accent="#FFC400", mmf="Pyidaungsu-Bold",
            mmr="Pyidaungsu", lat="Helvetica-Bold", index=None, total=None,
            brand=""):
    """ခေါင်းစဉ် + အချက် ၂–၃ ခု — အချက်တိုင်းကို ဂဏန်းနဲ့ အမှတ်ပြု。"""
    from PIL import ImageDraw
    im = _canvas(accent, index, total, brand, lat, mmf,
                 ghost=_mmnum(index) if index else None)
    d = ImageDraw.Draw(im)
    L, R = int(W * ML), int(W * (1 - ML))
    maxw = R - L
    hpx, hl = _fit(head, mmf, maxw, int(H * 0.066), int(H * 0.040), 2)
    items = [str(i).strip() for i in (items or []) if str(i).strip()][:3]
    ipx = int(H * 0.040)
    # ⚠️ **ဂဏန်းရဲ့ အကျယ်အစစ်နဲ့ တွက်ရမည်** — `W` ရဲ့ ၆% ဟု သတ်မှတ်ထားရာ
    #    ၁၉၂၀ မှာ ၁၁၅px ရပြီး ၁၀၈၀ (ဒေါင်လိုက်) မှာ ၆၅px သာ ရ၍ ဂဏန်းနဲ့
    #    စာသား **ကပ်သွား**သည် (「၀၁COE」 — ၂၀၂၆-၀၉-၂၀ တကယ် ဖြစ်ခဲ့)。
    _nbs = [_text_png(_mmnum(k + 1), int(ipx * 0.86), mmf,
                      accent if isinstance(accent, tuple) else _hex2rgb(accent))
            for k in range(len(items))]
    _ind = (max([b.shape[1] for b in _nbs] or [0]) + int(W * 0.028)) if _nbs else 0
    rows = []
    for it in items:
        _p, ls = _fit(it, mmr, maxw - _ind, ipx, int(H * 0.028), 2)
        rows.append((_p, [_text_png(l, _p, mmr, INK) for l in ls]))
    hb = [_text_png(l, hpx, mmf, INK) for l in hl]
    hgap = int(hpx * 0.28); igap = int(ipx * 0.34); rgap = int(ipx * 1.15)
    htot = sum(b.shape[0] for b in hb) + hgap * (len(hb) - 1)
    itot = sum(sum(b.shape[0] for b in r) + igap * (len(r) - 1) for _p, r in rows)
    itot += rgap * max(0, len(rows) - 1)
    tot = htot + int(H * 0.090) + itot
    y = (H - tot) // 2
    for b in hb:
        _paste(im, b, L, y); y += b.shape[0] + hgap
    d.rounded_rectangle([L, y + int(H * 0.026), L + int(W * 0.055),
                         y + int(H * 0.026) + 7], radius=4, fill=accent)
    y += int(H * 0.090) - hgap
    for k, (_p, r) in enumerate(rows):
        nb = _nbs[k]
        _paste(im, nb, L + 2, y + (r[0].shape[0] - nb.shape[0]) // 2)
        for b in r:
            _paste(im, b, L + _ind, y); y += b.shape[0] + igap
        y += rgap - igap
    return im


def bignum(num, label="", accent="#FFC400", mmf="Pyidaungsu-Bold",
           mmr="Pyidaungsu", lat="Helvetica-Black", index=None, total=None,
           brand=""):
    """ကြီးမားသော ကိန်း + အညွှန်း — အလေးပေး slide。"""
    from PIL import ImageDraw
    im = _canvas(accent, index, total, brand, lat, mmf)
    d = ImageDraw.Draw(im)
    L, R = int(W * ML), int(W * (1 - ML))
    npx = int(H * 0.34)
    nb = _text_png(str(num), npx, lat, INK)
    if nb.shape[1] > (R - L):
        npx = max(int(H * 0.12), int(npx * (R - L) / nb.shape[1]))
        nb = _text_png(str(num), npx, lat, INK)
    lb = []
    if label:
        lpx, ll = _fit(label, mmf, R - L, int(H * 0.048), int(H * 0.030), 2)
        lb = [_text_png(l, lpx, mmf, MUTE) for l in ll]
    gap = int(H * 0.040)
    tot = nb.shape[0] + (gap + sum(b.shape[0] for b in lb) + 12 * (len(lb) - 1)
                         if lb else 0)
    y = (H - tot) // 2
    _paste(im, nb, L, y); y += nb.shape[0]
    d.rounded_rectangle([L, y + int(H * 0.018), L + int(W * 0.075),
                         y + int(H * 0.018) + 8], radius=4, fill=accent)
    y += gap
    for b in lb:
        _paste(im, b, L, y); y += b.shape[0] + 12
    return im


LAYOUTS = {"statement": statement, "bullets": bullets, "bignum": bignum}
