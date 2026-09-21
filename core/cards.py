"""Headtop Premium — semantic card template များ (Motion Kit Step 4)

⚠️ `assets/calib/refboard_2026.json` ကနေ **တိုင်းယူထားသော** ပုံစံများသာ
   ဆောက်သည် — ကျွန်တော့် အထင်နဲ့ မဟုတ်ပါ (spec: 「Do not use broad
   statements such as 'premium' as a design specification」)。

   `concept_card`   ၅ ခု (v2 6kGBZ) — ဘောင်အပြည့် · အမှောင် နောက်ခံပုံ +
                    အလယ်ထား အဖြူ မြန်မာ ခေါင်းစဉ် + ဒုတိယကြောင်း
   `outline_title`  ၃ ခု (v5 HJ0K1) — ရွှေ **အနားသတ်သာ** ခေါင်းစဉ်၊
                    ပြောသူပေါ် ထပ်တင် (အတွင်း မဖြည့်)

⚠️ token ကနေသာ ကိန်း ယူသည် — ကုဒ်ထဲ ကိန်းသေ မရေးရ。
"""
import os

try:
    import pack as PK
    import slide as SL
except ImportError:
    from core import pack as PK, slide as SL

_T = None


def _tok():
    global _T
    if _T is None:
        _, _T = PK.load("headtop-premium")
        _T = _T or {}
    return _T


def _rgb(h, d=(255, 255, 255)):
    h = str(h or "").lstrip("#")
    if len(h) != 6:
        return d
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return d


def concept_card(head, sub="", W=1920, H=1080, bg=None, mmf=None, dim=0.62):
    """ဘောင်အပြည့် concept card — RGBA

    `bg` — နောက်ခံပုံ လမ်းကြောင်း (မရှိလျှင် အမှောင် ပြား)
    ⚠️ နောက်ခံကို **မှောင်အောင် ဖိရမည်** — reference မှာ ရုပ်က အလွန်
       မှိန်ပြီး စာသားက ထွက်နေသည်。 မဖိလျှင် စာ မဖတ်ရ。
    """
    from PIL import Image, ImageDraw, ImageFilter
    t = _tok()
    mmf = mmf or PK.tok(t, "type", "display", default="MyanmarHeadOne")
    im = Image.new("RGBA", (W, H), _rgb(PK.tok(t, "color", "ink"), (11, 12, 16)) + (255,))
    if bg and os.path.exists(bg):
        try:
            b = Image.open(bg).convert("RGB")
            r = max(W / b.width, H / b.height)
            b = b.resize((int(b.width * r) + 1, int(b.height * r) + 1))
            x = (b.width - W) // 2; y = (b.height - H) // 2
            b = b.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(1.2))
            im.alpha_composite(b.convert("RGBA"))
            d = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * dim)))
            im.alpha_composite(d)
        except Exception:
            pass
    # ── ခေါင်းစဉ် — အလယ်ထား ──
    px = int(H * float(PK.tok(t, "size", "headingText", default=0.0898)))
    maxw = int(W * 0.80)
    hpx, lines = SL._fit(str(head or "").strip(), mmf, maxw, px, int(px * 0.45), 2)
    lh = int(hpx * 1.22)
    spx = int(hpx * 0.46)
    subs = []
    if sub:
        _, subs = SL._fit(str(sub).strip(), mmf, maxw, spx, int(spx * 0.6), 2)
    tot = lh * len(lines) + (int(spx * 1.5) + int(spx * 1.25) * len(subs) if subs else 0)
    y = (H - tot) // 2
    tc = _rgb(PK.tok(t, "color", "text"), (255, 255, 255))
    for ln in lines:
        a = SL._text_png(ln, hpx, mmf, tc)
        SL._paste(im, a, (W - a.shape[1]) // 2, y); y += lh
    if subs:
        y += int(spx * 0.5)
        mc = _rgb(PK.tok(t, "color", "muted"), (175, 182, 196))
        for ln in subs:
            a = SL._text_png(ln, spx, mmf, mc)
            SL._paste(im, a, (W - a.shape[1]) // 2, y); y += int(spx * 1.25)
    return im


def outline_title(text, W=1920, H=1080, mmf=None, accent=None,
                  cx=0.5, cy=0.5, width=0.055, halo=0.0):
    """ရွှေ **အနားသတ်သာ** ခေါင်းစဉ် — အတွင်း ပွင့်လင်း · RGBA

    ⚠️ အတွင်း ဖြည့်လျှင် ပြောသူကို ဖုံးသည် — reference မှာ အနားသတ်သာ
       ဆွဲပြီး မျက်နှာ မြင်နေရသည် (v5 ၃ ခု)。
    """
    from PIL import Image
    import numpy as np
    t = _tok()
    mmf = mmf or PK.tok(t, "type", "display", default="MyanmarHeadOne")
    acc = _rgb(accent or PK.tok(t, "color", "accent"), (255, 224, 0))
    px = int(H * float(PK.tok(t, "size", "headingText", default=0.0898)))
    maxw = int(W * 0.86)
    hpx, lines = SL._fit(str(text or "").strip(), mmf, maxw, px, int(px * 0.5), 2)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lh = int(hpx * 1.2)
    y = int(cy * H) - lh * len(lines) // 2
    bw = max(2, int(hpx * float(width) * 0.5))
    for ln in lines:
        a = SL._text_png(ln, hpx, mmf, acc)
        if a is None or a.shape[0] < 2:
            continue
        al = a[..., 3].astype(np.int16)
        # ⚠️ အနားသတ် = မင် − ကျုံ့ထားသော မင် (morphological erosion)
        er = al.copy()
        for _ in range(bw):
            e = np.minimum.reduce([
                np.roll(er, 1, 0), np.roll(er, -1, 0),
                np.roll(er, 1, 1), np.roll(er, -1, 1), er])
            er = e
        ring = np.clip(al - er, 0, 255).astype(np.uint8)
        px = int(cx * W) - a.shape[1] // 2
        # ⚠️ **အလင်းနောက်ခံပေါ် အနားသတ်က ပျောက်သည်** — v5 က အမှောင်ပေါ်
        #    ဆွဲထားသည်。 IKKI ရဲ့ footage က အဖြူ မိုးကောင်းကင် ဖြစ်တတ်၍
        #    `halo` နဲ့ အမှောင် အရိပ် ခံရသည် (caption ရဲ့ plate နည်းတူ ·
        #    ၂၀၂၆-၀၉-၂၁ ဖရိန်နဲ့ တွေ့)。
        if halo > 0:
            from PIL import ImageFilter
            sh = np.zeros(a.shape, np.uint8)
            sh[..., 3] = (ring.astype(np.float32) * float(min(1.0, halo))
                          ).astype(np.uint8)
            shi = Image.fromarray(sh).filter(
                ImageFilter.GaussianBlur(max(2, int(hpx * 0.10))))
            SL._paste(im, np.asarray(shi), px, y)
            SL._paste(im, np.asarray(shi), px, y)
        out = a.copy(); out[..., 3] = ring
        SL._paste(im, out, px, y)
        y += lh
    return im


def halo_for(video, t, W, H, cx, cy, box=0.30):
    """နောက်ခံ အလင်းကို တိုင်းပြီး ဘယ်လောက် အရိပ် ခံရမလဲ ပြန်ပေးသည် (၀–၁)

    ⚠️ 「အမြဲ ခံ」လျှင် အမှောင်နောက်ခံမှာ ညစ်သည်、「မခံ」လျှင် အလင်းမှာ
       ပျောက်သည် ⇒ **တိုင်းပြီးမှ** ဆုံးဖြတ်ရမည် (contrast.py နည်းတူ)。
    """
    import subprocess
    import numpy as np
    x0 = max(0.0, cx - box / 2); y0 = max(0.0, cy - box / 2)
    vf = (f"crop={int(W*box)}:{int(H*box)}:{int(W*x0)}:{int(H*y0)},"
          f"scale=16:16,format=gray")
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0,t):.2f}",
                        "-i", video, "-frames:v", "1", "-vf", vf,
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True)
    if len(r.stdout) < 256:
        return 0.55
    lum = float(np.frombuffer(r.stdout[:256], np.uint8).mean())
    # ⚠️ အလင်း ၁၂၀ အထက် ⇒ အပြည့် · ၆၀ အောက် ⇒ မလို
    return round(max(0.0, min(1.0, (lum - 60.0) / 60.0)), 2)


# ══ ပြောသူပေါ် တင်နိုင်သော infographic (audit P1) ══════════════════
# ⚠️ Zin: 「Infographic နည်းနေတယ်」(၂၀၂၆-၀၉-၂၁)。 တိုင်းကြည့်ရာ အရေအတွက်က
#    ၄.၂/min ဖြစ်ပြီး reference ရဲ့ ဂရပ်ဖစ် နှုန်း (v4 median ၁၅s ⇒ ၄/min)
#    နဲ့ ကိုက်သည် — ပြဿနာက **အမျိုးအစား**。 ၅ ခုထဲ ၃ ခုက keyword pop
#    (အဝါ စာသား သက်သက်) ဖြစ်ပြီး တကယ့် infographic မဟုတ်ပါ。
# ⚠️ headtop framing မှာ ကျန်နေရာက ၃၃px သာ ⇒ **ဘေးဘက် ကပ်ပြီး
#    အတွင်း တစ်ပိုင်း ပွင့်လင်း** ဖြစ်မှ ပြောသူ မြင်နေရမည်。
SIDE_W = 0.34           # ဘေးဘောင် အကျယ် (ဘောင်ရဲ့ အချိုး)
SCRIM_A = 0.72          # နောက်ခံ မှိန်မှု — စာဖတ်လို့ရပြီး ပြောသူ မြင်ရဆဲ


def _panel(W, H, side="left", w=SIDE_W, a=SCRIM_A, pad=0.045):
    """ဘေးဘက် မှိန်သော အကွက် — `(im, x0, y0, x1, y1)`

    ⚠️ **ဘောင်အပြည့် မဖုံးရ** — ပြောသူက အလယ်/တစ်ဖက်မှာ ရှိသည်。
    """
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bw = int(W * w)
    x0 = int(W * pad) if side == "left" else W - bw - int(W * pad)
    y0, y1 = int(H * 0.20), int(H * 0.78)
    t = _tok()
    bg = _rgb(PK.tok(t, "color", "cardFill"), (14, 16, 24))
    d.rounded_rectangle([x0, y0, x0 + bw, y1], radius=int(H * 0.022),
                        fill=bg + (int(255 * a),))
    return im, x0, y0, x0 + bw, y1


def stat_ring(value, label="", W=1920, H=1080, mmf=None, accent=None,
              side="right"):
    """ဂဏန်း တစ်ခု + ရွှေကွင်း — `number` အတွက် · ဘေးဘက် ကပ်"""
    from PIL import Image, ImageDraw
    t = _tok()
    mmf = mmf or PK.tok(t, "type", "display", default="MyanmarHeadOne")
    acc = _rgb(accent or PK.tok(t, "color", "accent"), (255, 224, 0))
    im, x0, y0, x1, y1 = _panel(W, H, side, w=0.26)
    d = ImageDraw.Draw(im)
    cx, cy = (x0 + x1) // 2, int(y0 + (y1 - y0) * 0.40)
    r = int(min(x1 - x0, y1 - y0) * 0.30)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=acc + (255,),
              width=max(3, int(H * 0.007)))
    px = int(r * 0.85)
    a = SL._text_png(str(value or "")[:5], px, mmf, acc)
    if a is not None and a.shape[0] > 1:
        s = Image.fromarray(a, "RGBA")
        im.alpha_composite(s, (cx - s.width // 2, cy - s.height // 2))
    if label:
        lp = int(H * 0.034)
        hpx, lines = SL._fit(str(label), mmf, x1 - x0 - int(W * 0.02), lp,
                             int(lp * 0.6), 3)
        yy = cy + r + int(H * 0.04)
        for ln in lines:
            b = SL._text_png(ln, hpx, mmf, (255, 255, 255))
            if b is None or b.shape[0] < 2:
                continue
            s2 = Image.fromarray(b, "RGBA")
            im.alpha_composite(s2, ((x0 + x1) // 2 - s2.width // 2, yy))
            yy += int(hpx * 1.25)
    return im


def check_list(items, W=1920, H=1080, mmf=None, accent=None, side="left",
               tick=True):
    """စာရင်း — ရွှေ အမှတ်အသားနဲ့ · `checklist`/`steps` အတွက်

    ⚠️ **၅ ခုထက် မပိုရ** — ဖတ်ချိန် မလောက်ဘဲ ဖုံးသွားမည်。
    """
    from PIL import Image, ImageDraw
    t = _tok()
    mmf = mmf or PK.tok(t, "type", "display", default="MyanmarHeadOne")
    acc = _rgb(accent or PK.tok(t, "color", "accent"), (255, 224, 0))
    it = [str(x).strip() for x in (items or []) if str(x).strip()][:5]
    if not it:
        return None
    im, x0, y0, x1, y1 = _panel(W, H, side)
    d = ImageDraw.Draw(im)
    px = int(H * 0.040)
    pad = int(W * 0.018)
    yy = y0 + int((y1 - y0 - len(it) * px * 1.9) / 2)
    for s in it:
        m = int(px * 0.34)
        if tick:
            d.line([(x0 + pad, yy + px * 0.58), (x0 + pad + m * 0.6, yy + px * 0.86),
                    (x0 + pad + m * 1.6, yy + px * 0.22)],
                   fill=acc + (255,), width=max(3, int(px * 0.13)))
        else:
            d.ellipse([x0 + pad, yy + px * 0.35, x0 + pad + m, yy + px * 0.35 + m],
                      fill=acc + (255,))
        hpx, lines = SL._fit(s, mmf, x1 - x0 - pad * 2 - m * 2, px,
                             int(px * 0.62), 2)
        ty = yy
        for ln in lines[:2]:
            b = SL._text_png(ln, hpx, mmf, (255, 255, 255))
            if b is None or b.shape[0] < 2:
                continue
            s2 = Image.fromarray(b, "RGBA")
            im.alpha_composite(s2, (x0 + pad + int(m * 2.2), ty))
            ty += int(hpx * 1.18)
        yy = ty + int(px * 0.7)
    return im


def compare_two(left, right, W=1920, H=1080, mmf=None, accent=None):
    """နှိုင်းယှဉ်ချက် ၂ ခု — အောက်ခြေမှာ · `compare` အတွက်

    ⚠️ မျက်နှာဇုန် (အပေါ် ၆၄%) ကို ရှောင်ပြီး **အောက်ပိုင်း** မှာသာ。
    """
    from PIL import Image, ImageDraw
    t = _tok()
    mmf = mmf or PK.tok(t, "type", "display", default="MyanmarHeadOne")
    acc = _rgb(accent or PK.tok(t, "color", "accent"), (255, 224, 0))
    bg = _rgb(PK.tok(t, "color", "cardFill"), (14, 16, 24))
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y0, y1 = int(H * 0.60), int(H * 0.74)
    x0, x1 = int(W * 0.08), int(W * 0.92)
    d.rounded_rectangle([x0, y0, x1, y1], radius=int(H * 0.018),
                        fill=bg + (int(255 * SCRIM_A),))
    mid = (x0 + x1) // 2
    d.line([(mid, y0 + int(H * 0.012)), (mid, y1 - int(H * 0.012))],
           fill=acc + (220,), width=max(2, int(H * 0.004)))
    px = int(H * 0.044)
    for txt, cx in ((left, (x0 + mid) // 2), (right, (mid + x1) // 2)):
        hpx, lines = SL._fit(str(txt or "").strip(), mmf,
                             (mid - x0) - int(W * 0.03), px, int(px * 0.6), 2)
        ty = (y0 + y1) // 2 - int(hpx * 0.6 * len(lines))
        for ln in lines[:2]:
            b = SL._text_png(ln, hpx, mmf, (255, 255, 255))
            if b is None or b.shape[0] < 2:
                continue
            s2 = Image.fromarray(b, "RGBA")
            im.alpha_composite(s2, (cx - s2.width // 2, ty))
            ty += int(hpx * 1.2)
    return im
