#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · မြန်မာ စာတန်း。

⚠️ **ffmpeg မှာ input ၁၄၀ ခန့်ရောက်လျှင် ပျက်သည်** — scaler/decoder ကုန်သည်
   ("Resource temporarily unavailable" / "Error while opening decoder")。
   ဗီဒီယို ၁၀ မိနစ်မှာ စာတန်း ~၂၀၀ ရှိသဖြင့် PNG အားလုံးကို input အဖြစ်
   **တစ်ပြိုင်တည်း ထည့်၍ မရ**。
   ⇒ concat demuxer ဖြင့် **alpha overlay ဗီဒီယို တစ်ခု** အရင်ဆောက်ပြီး
     အဲဒါ တစ်ခုတည်းကို overlay လုပ်သည် (input ၂ ခုသာ)。

⚠️ မြန်မာစာ **စကားလုံးအလယ် မပိုင်းရ**。 အက္ခရာအရေအတွက်ဖြင့် အကျယ် မမှန်းရ —
   IG.MW() ဖြင့် တိုင်းရသည် (ခန့်မှန်းလျှင် ၂ ဆ လွဲသည်)。

⚠️ **cttext ကို newline ပါသော စာသား ပို့၍ မရ** — သူက input စာသားကို
   output JSON ထဲ escape မလုပ်ဘဲ ပြန်ထည့်သဖြင့် `json.loads` ပျက်သည်
   ("Invalid control character")。 ⇒ စာတန်း **တစ်ကြောင်းတည်း**သာ ရေးရသည်。
   ဒါက house spec နှင့်လည်း ကိုက်သည် — "one line, ~28 clusters"。
   ရှည်လျှင် အရွယ် ချုံ့၊ မလုံလျှင် စာတန်း ၂ ခု ခွဲသည်。
"""
import os, re, subprocess

# မြန်မာ cluster — အခြေအက္ခရာ + ပေါင်းစပ် သင်္ကေတများ
_CL = re.compile(r"[\u1000-\u102A\u103F\u104C-\u104F\u0020-\u007E]"
                 r"[\u102B-\u103E\u1039\u1040-\u104B\uFE00-\uFE0F]*")

# ⚠️ regex က စာကြောင်းကို မကုန်စားနိုင်လျှင် `list(t)` — **အက္ခရာလိုက် ခွဲ**သည်။
#    အဲဒီအခါ ေ ာ ် ြ ွ ပြုတ်နိုင်သည်။ ဘယ်နှစ်ကြိမ် ဖြစ်လဲ ရေတွက်ထားမှ
#    render report မှာ ပြနိုင်မည် (ပစ်မှတ် = ၀)။
FALLBACK = [0]

def clusters(t):
    out = _CL.findall(t)
    # findall က မိမသော အက္ခရာများ ကျန်စေရန် အရှည် စစ်သည်
    if sum(len(x) for x in out) == len(t):
        return out
    FALLBACK[0] += 1
    return list(t)

def wrap(text, size, maxw, MW, font=None):
    """စကားလုံးအလယ် **မပိုင်း**ဘဲ ကြောင်းခွဲသည်。

    ⚠️ space ဖြင့်သာ ခွဲလျှင် မလုံလောက် — မြန်မာစာမှာ စကားလုံးရှည်တွေ
       space မပါ ("ဘာသာကိုယ်လေ့လာခိုင်းတာမျိုးမဟုတ်" = ၁၁၅px မှာ 1766px
       တစ်လုံးတည်း၊ ဘောင်က 928px သာ)。 ⇒ အဲဒီအခါ **cluster နယ်နိမိတ်**မှာ
       ခွဲရသည် — အက္ခရာ အလယ် မပိုင်းရ (မာတ်တွေ ပြုတ်သွားမည်)。
    """
    out=[]
    for w in [x for x in text.replace(" ", " ").split(" ") if x]:
        if MW(w, size, font) <= maxw:
            out.append(w); continue
        cur=""
        for c in clusters(w):
            if cur and MW(cur+c, size, font) > maxw:
                out.append(cur); cur=c
            else:
                cur += c
        if cur: out.append(cur)
    # တစ်လုံးချင်းကို ကြောင်းအလိုက် ပြန်ပေါင်း
    lines=[]; cur=""
    for w in out:
        t=(cur+" "+w).strip()
        if cur and MW(t, size, font) > maxw:
            lines.append(cur); cur=w
        else:
            cur=t
    if cur: lines.append(cur)
    return lines

def cards(c, size, maxw, MW, font, max_lines=2, hold=4.0):
    """စာတန်းတစ်ခုကို ကတ်အလိုက် ခွဲသည် — ကတ်တစ်ခုမှာ **အများဆုံး ၂ ကြောင်း**。

    ⚠️ ZAE spec: "တစ်ကြောင်း ဒါမှမဟုတ် ၂ ကြောင်း၊ **၃ ကြောင်း မရ**"。
    ⚠️ ၈% အရွယ် (၁၁၅px) မှာ တစ်ကြောင်းတည်းဆို **ဘယ်ဟာမှ မဝင်** —
       တိုင်းကြည့်ရာ ရှည်တာက 3278px လိုပြီး ဘောင်က 928px သာ ရှိသည်。
       ⇒ ၂ ကြောင်းနဲ့လည် မလုံလျှင် **အချိန် ခွဲ**ရသည် (စာအရင်၊ ပြီးမှ အချိန်)。
    ⚠️ စကားလုံးအလယ် **မပိုင်းရ** — wrap() က စကားလုံးနယ်နိမိတ်ကိုပဲ သုံးသည်。
    """
    ls = wrap(c["text"], size, maxw, MW, font)
    if not ls: return []
    # ⚠️ ကြောင်း အလွန်များလျှင် (၆ ကြောင်းထက်) စာတန်းက မြန်လွန်း ဖတ်မရ —
    #    အရွယ် နည်းနည်း ချုံ့ပြီး ကြောင်းရေ လျှော့သည် (spec ရဲ့ ၇၅% ထိ)。
    sz = size
    # ⚠️ ကြောင်း အလွန်များလျှင် အရွယ် ချုံ့သည် — **ချုံ့ထားတဲ့ အရွယ်ကို
    #    ပြန်ပေးရမည်**。 မပေးလျှင် track() က မူရင်းအရွယ်နဲ့ ဆွဲပြီး
    #    ဘောင် ကျော်ထွက်သည် (တကယ် ဖြစ်ခဲ့)。
    # ⚠️ ရှည်လျှင် အရွယ် ချုံ့တာကို **ရပ်လိုက်ပြီ** — ကတ် အရေအတွက် တိုးပေး
    #    ပြီးဖြစ်၍ မလိုတော့。 ချုံ့လျှင် စာတန်း အရွယ် တစ်ခုနဲ့တစ်ခု မတူဘဲ
    #    ၃၀px ↔ ၄၄px ကြား ခုန်နေသည် (N5 က အမြဲ တစ်အရွယ်တည်း)。
    if len(ls) > 14:
        while sz > int(size*0.86) and len(ls) > 12:
            sz -= 3; ls = wrap(c["text"], sz, maxw, MW, font)
    # ⚠️ **ဘောင် မကျော်စေရ** — မြန်မာစကားလုံး တစ်လုံးတည်းက `maxw` ထက်
    #    ရှည်လျှင် wrap က ခွဲလို့ မရ (စကားလုံးအလယ် မပိုင်းရ) ⇒ ကြောင်းက
    #    ဘောင်ကျော်ပြီး cttext က ဖြတ်ပစ်သည်。 ⇒ အဲဒီကတ်အတွက်သာ ချုံ့သည်。
    HARD = int(maxw/0.63*0.90) if maxw else 0        # ≈ ဘောင်၏ ၉၀%
    if HARD:
        for _ in range(12):
            if max((MW(x, sz, font) for x in ls), default=0) <= HARD: break
            sz -= 4
            if sz < int(size*0.55): break
            ls = wrap(c["text"], sz, maxw, MW, font)
    dur = max(0.4, c["end"]-c["start"])
    groups = [ls[i:i+max_lines] for i in range(0, len(ls), max_lines)]
    # ⚠️ `hold` ကို **ကတ်ရဲ့ အချိန်ကို ဖြတ်ပြီး ကန့်သတ်၍ မရ** — ဖြတ်လိုက်လျှင်
    #    ကျန်အချိန်မှာ စာတန်း **လုံးဝ မရှိ**တော့ဘူး。 ASR က ၁၀s+ segment
    #    ပေးတတ်၍ ဗီဒီယိုရဲ့ ၂၀% မှာ စာတန်း ပျောက်ခဲ့သည် (Zin: "ဗီဒီယို
    #    တစ်ပုဒ်လုံး မထိုးထားဘူး")。
    #    ⇒ ရှည်လျှင် **ကတ် အရေအတွက် တိုးပေး** (တစ်ကြောင်းစီ ခွဲ) ပြီး
    #      အချိန်ကို အချိုးကျ ခွဲသည် — ကွက်လပ် လုံးဝ မကျန်စေရ。
    if len(groups) and dur/len(groups) > hold and max_lines > 1:
        groups = [ls[i:i+1] for i in range(len(ls))]
    tot = sum(sum(len(x) for x in g) or 1 for g in groups)
    out=[]; pos=c["start"]
    for g in groups:
        w = (sum(len(x) for x in g) or 1)/tot
        # ⚠️ ကတ်တစ်ခုကို **ဘယ်လောက်ပဲ ကြာကြာ မထားရ**。 ASR က စာပိုဒ်လုံး
        #    တစ်ခုတည်း ပေးတတ်သည် (segment တစ်ခု ၂၁.၄s · ၁၀.၇s — တကယ်
        #    ဖြစ်ခဲ့)。 အဲဒါကို ကတ်တစ်ခုအဖြစ် ချလျှင် စာတန်းက ဆယ်စက္ကန့်
        #    ကျော် ရပ်နေပြီး ပြောနေတဲ့ စကားနှင့် လုံးဝ မကိုက်တော့ဘူး。
        d = max(0.45, dur*w)
        out.append((g, pos, pos+d, sz)); pos += d
    if out:                         # ⚠️ segment ရဲ့ အဆုံးထိ ဖြည့်ရမည်
        g, a, _b, z = out[-1]; out[-1] = (g, a, max(_b, c["end"]), z)
    return out

def plan(segs, spans, max_lines=2):
    """ဖြတ်ပြီးနောက် အချိန်သို့ စာတန်းများကို ပြောင်းသည်。

    ⚠️ ဖြတ်တောက်ပြီးလျှင် အချိန်တွေ ရွှေ့သွားသည် — မူရင်းအချိန်ကို
       ကျန်ရှိသော span များပေါ် ပြန်တွက်ရမည်။ မတွက်လျှင် စာတန်းက
       ဗီဒီယိုနှင့် လွဲသွားသည်。
    """
    # မူရင်းအချိန် → ဖြတ်ပြီးအချိန် map
    def remap(t):
        acc=0.0
        for a,b in spans:
            if t < a: return None            # ဖြတ်ပစ်လိုက်သော အပိုင်း
            if t <= b: return acc + (t-a)
            acc += b-a
        return None
    out=[]
    for s in segs:
        a=remap(s["start"]); b=remap(s["end"])
        if a is None or b is None or b-a < 0.25: continue
        out.append(dict(text=s["text"], start=round(a,2), end=round(b,2)))
    return out

def track(caps, out, work, W, H, size, fill, font, fallback, bot,
          ct, MW, fps=30, total=None, stroke=None, stroke_w=0.0, hold=4.0,
          gap_pct=0.18, fade=0.14, hide=None, log=None, wide=0.86):
    """စာတန်းများကို alpha overlay ဗီဒီယို တစ်ခု အဖြစ် ဆောက်သည်。

    ⚠️ ကြောင်းနှစ်ကြောင်း အကွာအဝေးကို **ink ဖြတ်ပြီးမှ** သတ်မှတ်ရသည်。
       cttext ရဲ့ canvas က size×2.2 ဖြစ်၍ အတိုင်းအတာအတိုင်း ထပ်လျှင်
       ကြားက ၀.၆၅×size လောက် ကွာသွားသည် — N5 reference ထက် ၃ ဆကျော်
       ကွာပြီး Zin က "အကွာအဝေးက အရမ်းဝေးလွန်းနေတယ်" ဟု ပြောခဲ့သည်。
       ⇒ ကြောင်းတစ်ခုချင်းကို alpha bbox အတိုင်း ဖြတ်ပြီး `gap_pct×size`
         ဖြင့် ထပ်သည်。
    ⚠️ `hide` — ဂရပ်ဖစ် ပေါ်နေချိန် စာတန်း **ဖျောက်**ရသည် (စာနှစ်ထပ် မဖြစ်စေရန်)。
    ⚠️ `fade` — ကတ်တိုင်း alpha ၃ ဆင့်ဖြင့် ပွင့်လာသည် (ရုတ်တရက် မပေါ်စေရန်)。
    """
    os.makedirs(work, exist_ok=True)
    band_h = int(size*2.2)*2
    blank = os.path.join(work, "_blank.png")
    ct(dict(text=" ", font=font, fallback=fallback, size=size, w=W, h=band_h,
            fill="#00000000", unit="cluster", align="center",
            frames=[{"out":blank, "words":[]}]))

    def _sp(txt, sz, outp, h=None):
        d = dict(text=txt, font=font, fallback=fallback, size=sz, w=W, h=h or band_h,
                 fill=fill, unit="cluster", align="center",
                 # ⚠️ အရိပ်က **ဖတ်ရလွယ်မှုအတွက်** — အလှအတွက် မဟုတ်。
                 #    ၂၀၂၆-၀၉-၂၀ တိုင်းချက်: အလင်းများသော B-roll ပေါ်မှာ
                 #    စာလုံး/နောက်ခံ ကွာခြားမှု **၃.၄၀:၁** သာ ရှိပြီး ဖတ်ရလွယ်သော
                 #    စံ (၄.၅:၁) အောက် ကျနေသည် (stroke မပါသော style များ)。
                 #    ⇒ alpha ၀.၅၅→၀.၇၂ · blur ၀.၁၁→၀.၁၄ (ဒီဇိုင်း မပြောင်း၊
                 #    အောက်ခံ မှောင်ပေးရုံ)。 stroke ရှိသော style မှာ သက်ရောက်မှု နည်း。
                 shadow=dict(dx=0, dy=max(1, int(sz*0.055)), blur=max(2, int(sz*0.14)),
                             alpha=0.72),
                 frames=[{"out":outp, "words":[]}])
        if stroke and stroke_w:
            d["stroke"] = stroke; d["strokeWidth"] = max(2, int(sz*stroke_w))
        return d

    try:
        from PIL import Image
        import numpy as _np
    except Exception:
        Image = None

    def _ink(p, pad=3):
        """PNG ကို alpha bbox အတိုင်း ဖြတ်သည် (ဒေါင်လိုက်သာ)。"""
        if Image is None: return None
        im = Image.open(p).convert("RGBA")
        a = _np.asarray(im)[:, :, 3]
        ys = _np.nonzero(a.max(axis=1) > 6)[0]
        if len(ys) == 0: return None
        y0 = max(0, int(ys.min())-pad); y1 = min(im.size[1], int(ys.max())+1+pad)
        return im.crop((0, y0, im.size[0], y1))

    def _stack(parts, sz, outp):
        """ink ဖြတ်ပြီး gap ဖြင့် ထပ် → band_h ထဲ အောက်ခြေ ကပ်ထား。"""
        if Image is None: return False
        ims = [_ink(q) for q in parts]
        ims = [x for x in ims if x is not None]
        if not ims: return False
        gap = int(sz*gap_pct)
        tot = sum(x.size[1] for x in ims) + gap*(len(ims)-1)
        canvas = Image.new("RGBA", (W, band_h), (0,0,0,0))
        y = band_h - tot
        if y < 0: y = 0
        for x in ims:
            canvas.alpha_composite(x, (0, y)); y += x.size[1] + gap
        canvas.save(outp)
        return True

    _fcache = {}
    def _faded(p, k):
        """alpha ကို k ဆ လျှော့ထားသော မိတ္တူ (fade-in ထစ်)。"""
        if Image is None: return p
        q = _fcache.get((p, k))
        if q: return q
        q = p[:-4] + f"_f{int(k*100):03d}.png"
        if not os.path.exists(q):
            im = Image.open(p).convert("RGBA")
            a = _np.asarray(im).copy()
            a[:, :, 3] = (a[:, :, 3].astype(_np.float32)*k).astype(_np.uint8)
            Image.fromarray(a, "RGBA").save(q)
        _fcache[(p, k)] = q
        return q

    # ⚠️ **ကြောင်းအကျယ်ကို ကျဉ်းထားရမည်** — N5 reference ကို တိုင်းတော့
    #    ကြောင်းတစ်ခုက ဘောင်ရဲ့ ၀.၄၈ သာ ကျယ်ပြီး **တစ်ကြောင်းတည်း**များသည်;
    #    စာလုံးက ၀.၁၂၄·H (၁၄၄၀ ဘောင်တွင် ၁၇၈px) ရှိသည်。
    #    ကျယ်ကျယ် (၀.၈၆) ထားလျှင် ဝါကျရှည်က ၂ ကြောင်း ဖြစ်ပြီး စာလုံး
    #    ချုံ့ရသဖြင့် **N5 ရဲ့ တစ်ဝက်** သာ ကြီးသည် (Zin: "လုံးဝ အဆင်မပြေဘူး")。
    maxw = int(W*wide)
    line_h = int(size*2.2)
    timed=[]; k=0
    for c in caps:
        for lines, a, b, sz in cards(c, size, maxw, MW, font, hold=hold):
            parts=[]
            for j,txt in enumerate(lines):
                q = os.path.join(work, f"c{k:04d}_{j}.png")
                ct(_sp(txt, sz, q, h=line_h)); parts.append(q)
            p = os.path.join(work, f"c{k:04d}.png"); k += 1
            if not _stack(parts, sz, p):
                # ⚠️ PIL မရလျှင် ယခင်နည်း (ဘောင်အပြည့် ထပ်) ကို ပြန်သုံးသည်
                if len(parts) == 1:
                    subprocess.run(["ffmpeg","-v","error","-y","-i",parts[0],
                        "-vf",f"pad={W}:{band_h}:0:{band_h-line_h}:color=black@0",
                        "-frames:v","1","-pix_fmt","rgba",p],check=True)
                else:
                    subprocess.run(["ffmpeg","-v","error","-y","-i",parts[0],"-i",parts[1],
                        "-filter_complex",
                        f"[0][1]vstack=2,pad={W}:{band_h}:0:{band_h-line_h*2}:color=black@0",
                        "-frames:v","1","-pix_fmt","rgba",p],check=True)
            timed.append([float(a), float(b), p])

    # ── ဂရပ်ဖစ် ပေါ်နေချိန် ဖျောက် ──
    if hide:
        cut=[]
        for a,b,p in timed:
            segs=[(a,b)]
            for ha,hb in hide:
                nx=[]
                for x,y in segs:
                    if hb <= x or ha >= y: nx.append((x,y)); continue
                    if x < ha: nx.append((x,ha))
                    if hb < y: nx.append((hb,y))
                segs=nx
            for x,y in segs:
                if y-x > 0.20: cut.append([x,y,p])
        n_hid = len(timed)-len(cut)
        if log and n_hid: log(f"  စာတန်း · ဂရပ်ဖစ်ပေါ်လို့ ဖျောက် {n_hid} ကတ်")
        timed = cut
    timed.sort(key=lambda x: x[0])

    # ── timeline → concat ──
    items=[]; t=0.0
    FSTEP = 3
    for a,b,p in timed:
        if a > t + 0.04: items.append((blank, a-t))
        elif a < t: a = t
        if b - a < 0.12: continue
        f = min(fade, (b-a)*0.45)
        st = f/FSTEP if FSTEP else 0
        for i in range(1, FSTEP+1):
            items.append((_faded(p, i/float(FSTEP)), st))
        items.append((p, (b-a) - f))
        t = b
    if total and total > t: items.append((blank, total-t))
    if not items: return None
    lst = os.path.join(work, "caps.txt")
    with open(lst, "w") as f:
        for p,d in items:
            f.write("file '%s'\nduration %.3f\n" % (p.replace("'","'\\''"), max(0.02,d)))
        f.write("file '%s'\n" % items[-1][0].replace("'","'\\''"))
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",lst,
        "-r",str(fps),"-c:v","qtrle","-pix_fmt","argb",out], check=True)
    return out
