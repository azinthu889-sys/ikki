#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S-Log3 / S-Gamut3 -> Rec.709 .cube LUT, built from Sony's published maths.

Copied into IKKI from zjl-e02/make_lut.py (2026-09-26) for the Cinematic Vlog
engine.  `sat_ceil` was added: the podcast look capped pixel saturation at
0.34, which holds a vlog's mean saturation near 0.20 against the 0.41-0.54
measured on Zin's own vlogs.

No LUT downloaded: the S-Log3 curve and the gamut primaries are public
specifications, so the transform is computed here and can be checked.
"""
import math, sys

# ── 1. S-Log3 electro-optical transfer function (Sony official) ──────────
BREAK = 171.2102946929
def slog3_to_linear(x):
    c = x * 1023.0
    if c >= BREAK:
        return (10.0 ** ((c - 420.0) / 261.5)) * 0.19 - 0.01
    return (c - 95.0) * 0.01125000 / (BREAK - 95.0)

# ── 2. gamut: primaries -> RGB->XYZ matrix ──────────────────────────────
def rgb_to_xyz(prim, wp):
    (xr,yr),(xg,yg),(xb,yb) = prim
    Xr,Yr,Zr = xr/yr, 1.0, (1-xr-yr)/yr
    Xg,Yg,Zg = xg/yg, 1.0, (1-xg-yg)/yg
    Xb,Yb,Zb = xb/yb, 1.0, (1-xb-yb)/yb
    xw,yw = wp
    Xw,Yw,Zw = xw/yw, 1.0, (1-xw-yw)/yw
    M = [[Xr,Xg,Xb],[Yr,Yg,Yb],[Zr,Zg,Zb]]
    S = solve(M,[Xw,Yw,Zw])
    return [[M[r][c]*S[c] for c in range(3)] for r in range(3)]

def solve(M, v):
    a=[row[:]+[v[i]] for i,row in enumerate(M)]
    for i in range(3):
        p=max(range(i,3), key=lambda r: abs(a[r][i])); a[i],a[p]=a[p],a[i]
        d=a[i][i]
        a[i]=[x/d for x in a[i]]
        for r in range(3):
            if r!=i:
                f=a[r][i]; a[r]=[a[r][c]-f*a[i][c] for c in range(4)]
    return [a[r][3] for r in range(3)]

def inv3(M):
    """true inverse: solve() returns a column, so assemble columns properly"""
    cols=[solve(M,[1 if i==j else 0 for i in range(3)]) for j in range(3)]
    return [[cols[c][r] for c in range(3)] for r in range(3)]

def transpose(M): return [[M[r][c] for r in range(3)] for c in range(3)]
def matmul(A,B): return [[sum(A[r][k]*B[k][c] for k in range(3)) for c in range(3)] for r in range(3)]

D65 = (0.3127, 0.3290)
SGAMUT3      = ((0.730,0.280),(0.140,0.855),(0.100,-0.050))
SGAMUT3_CINE = ((0.766,0.275),(0.225,0.800),(0.089,-0.087))
REC709       = ((0.640,0.330),(0.300,0.600),(0.150,0.060))

def gamut_matrix(src):
    """src RGB -> Rec.709 RGB, both linear"""
    M = matmul(inv3(rgb_to_xyz(REC709,D65)), rgb_to_xyz(src,D65))
    for row in M:                       # white must stay white
        assert abs(sum(row)-1.0) < 1e-6, "matrix row does not sum to 1: %r" % row
    return M

# ── 3. display side ─────────────────────────────────────────────────────
def rec709_oetf(v):
    v = max(0.0, v)
    return 4.5*v if v < 0.018 else 1.099*(v**0.45) - 0.099

def tonemap(x, white):
    """extended Reinhard: rolls the S-Log3 highlight range into 0..1
    instead of clipping it.  white = how many stops of highlight to keep."""
    x = max(x, 0.0)
    return (x * (1.0 + x/(white*white))) / (1.0 + x)

def contrast_curve(v, k, pivot=0.41):
    """gentle S around 18% grey; k=1 is a no-op"""
    if k == 1.0: return v
    v = min(max(v, 0.0), 1.0)
    d = v - pivot
    return min(max(pivot + d*k - (d**3)*(k-1)*1.2, 0.0), 1.0)


SAT_CEIL = 0.34
SKIN_HUE = 18.0      # skin+lips span roughly 340°..40°, so centre low
SKIN_WIDTH = 34.0

def hue_sat_of(r, g, b):
    mx, mn = max(r,g,b), min(r,g,b)
    d = mx - mn
    if d < 1e-9 or mx < 1e-9: return 0.0, 0.0
    if mx == r:   h = ((g-b)/d) % 6
    elif mx == g: h = (b-r)/d + 2
    else:         h = (r-g)/d + 4
    return h*60.0, d/mx

def creative(rgb, lift, sh_tint, hi_tint, sat, mid_tint=(0,0,0),
             skin_protect=0.0, skin_warm=(0,0,0), sat_ceil=SAT_CEIL,
             skin_hue=SKIN_HUE, skin_width=SKIN_WIDTH,
             sh_pow=2.2, hi_pow=2.4):
    """Hue-qualified look, the way a colourist would build it.

    The environment tint is weighted by luminance AND gated by hue, so it
    lands on the wall (grey/green) and stays off the face (orange).  Grading
    on luminance alone cannot separate them — the face and the wall sit at
    similar brightness, which is exactly why a flat tint kills skin.
    """
    y = 0.2126*rgb[0] + 0.7152*rgb[1] + 0.0722*rgb[2]
    y = min(max(y, 0.0), 1.0)
    ws = (1.0 - y) ** sh_pow
    wh = y ** hi_pow
    wm = 4.0 * y * (1.0 - y)

    h, s = hue_sat_of(*rgb)
    dh = abs(h - skin_hue); dh = min(dh, 360.0 - dh)
    skin = math.exp(-(dh/skin_width)**2) * min(s/0.18, 1.0)   # 0..1 skin key
    keep = 1.0 - skin_protect*skin        # how much of the tint may land here

    out = []
    for i, c in enumerate(rgb):
        c = lift + c*(1.0 - lift)
        c = c + (sh_tint[i]*ws + hi_tint[i]*wh + mid_tint[i]*wm) * keep
        # warm only the DESATURATED part of skin (cheeks, forehead).
        # lips are already a strong red — pushing them further reads magenta
        c = c + skin_warm[i] * skin * max(0.0, 1.0 - s/0.40)
        out.append(c)

    # skin keeps its saturation even when the rest is pulled down
    sat_here = sat + (1.0 - sat)*skin*skin_protect
    y2 = 0.2126*out[0] + 0.7152*out[1] + 0.0722*out[2]
    out = [min(max(y2 + (c-y2)*sat_here, 0.0), 1.0) for c in out]

    # soft ceiling on saturation: nothing should end up more saturated than
    # SAT_CEIL, so strong reds roll off instead of screaming
    h2, s2 = hue_sat_of(*out)
    if s2 > sat_ceil:
        k = (sat_ceil + (s2 - sat_ceil)/(1.0 + (s2 - sat_ceil)/0.10)) / s2
        y3 = 0.2126*out[0] + 0.7152*out[1] + 0.0722*out[2]
        out = [min(max(y3 + (c-y3)*k, 0.0), 1.0) for c in out]
    return out

def gamut_compress(lin, limit=0.88, start=0.80):
    """S-Gamut3 → Rec.709 တွင် ဘောင်ကျော်သော အရောင်များကို **ဖြတ်မယ့်အစား**
    ညင်သာစွာ ချုံ့သည် (ACES gamut-compress ရဲ့ ရိုးရှင်းသော ပုံစံ)။

    ⚠️ ဤအဆင့် မပါလျှင် ဘာဖြစ်သလဲ — S-Gamut3 က Rec.709 ထက် များစွာ ကျယ်၍
    အနီပြင်းများ (နှုတ်ခမ်း၊ မီးအလင်း၊ ပန်း) က matrix ပြီးလျှင် **အနုတ်**
    ဖြစ်သွားပြီး `min(max(v,0),1)` က သုညသို့ ဖြတ်ချသည်။ တိုင်းကြည့်ရာ
    LUT သက်သက်ဖြင့်ပင် နှုတ်ခမ်း RGB(180,20,56) — G/R = 0.11 ဖြစ်နေသည်။
    Zin: "နှုတ်ခမ်းကဘာလို့အရမ်းနီနေတာလဲ … color အရမ်းကြမ်းနေတယ်" (2026-09-10)။

    နည်းလမ်း — အလင်းတန်ဖိုး (luminance) ကို **အတိအကျ ထိန်း**ထားပြီး
    အရောင်ကို ဗဟိုသို့ ဆွဲသည်။ ချုံ့မှုက start မှ စ၍ limit ကို ဘယ်တော့မှ
    မကျော်အောင် asymptotic ဖြစ်သဖြင့် အနားသတ်မှာ အဖြတ်အတောက် မမြင်ရ။

    limit — အနက်ဆုံး channel က luminance ရဲ့ (1−limit) အောက် မကျရ
    start  — ဤအကွာအဝေးအထိ လုံးဝ မထိ (သဘာဝ အရောင်များ မပြောင်း)
    """
    y = 0.2126*lin[0] + 0.7152*lin[1] + 0.0722*lin[2]
    if y <= 1e-9:
        return [max(v, 0.0) for v in lin]
    mn = min(lin)
    d = (y - mn) / y                      # 1.0 = channel သုည ; >1 = အနုတ်
    if d <= start:
        return lin
    L, t = limit, start
    dc = t + (L - t) * (1.0 - 1.0/(1.0 + (d - t)/(L - t)))
    k = dc / d
    return [y + (v - y)*k for v in lin]


def build(path, gamut, size=33, exposure=1.0, contrast=1.0, sat=1.0, white=6.0,
          lift=0.0, sh_tint=(0,0,0), hi_tint=(0,0,0), wb=(1.0,1.0,1.0),
          mid_tint=(0,0,0), skin_protect=0.0, skin_warm=(0,0,0),
          log_in=True, gc_limit=0.88, gc_start=0.80, sat_ceil=SAT_CEIL,
          shoulder=None):
    """`shoulder=(knee, ceiling)` rolls display values above `knee` softly
    into `ceiling`.  Reinhard alone cannot do it for clipped camera
    highlights: an overcast sky already at the sensor's top code maps to 1.0
    whatever `white` is (measured: white 3/6/10 all left p99 at 251-253,
    against 198-238 on Zin's published vlogs)."""
    M = gamut_matrix(gamut)
    out = ["# S-Log3 -> Rec.709   built by make_lut.py",
           "LUT_3D_SIZE %d" % size, ""]
    for b in range(size):
        for g in range(size):
            for r in range(size):
                if log_in:
                    rgb = [slog3_to_linear(r/(size-1)),
                           slog3_to_linear(g/(size-1)),
                           slog3_to_linear(b/(size-1))]
                    lin = [sum(M[i][j]*rgb[j] for j in range(3))*exposure
                           for i in range(3)]
                    # ဘောင်ကျော် အရောင်များကို ဖြတ်မခံရမီ ချုံ့သည်
                    if gc_limit < 1.0:
                        lin = gamut_compress(lin, gc_limit, gc_start)
                else:
                    # already Rec.709 display: undo the OETF so the look
                    # still runs in linear light, then it is re-applied below
                    e = [ (v/4.5 if v < 0.081 else ((v+0.099)/1.099)**(1/0.45))
                          for v in (r/(size-1), g/(size-1), b/(size-1)) ]
                    lin = [v*exposure for v in e]
                # Work out the skin key BEFORE touching white balance, then
                # hold the WB off skin.  A global WB that lowers red and lifts
                # blue turns lips magenta — they are red-dominant, so the same
                # shift that cools a grey wall pushes them toward purple.
                probe = [rec709_oetf(tonemap(v, white)) for v in lin]
                hp, sp_ = hue_sat_of(*probe)
                dhp = abs(hp - SKIN_HUE); dhp = min(dhp, 360.0 - dhp)
                skin_k = math.exp(-(dhp/SKIN_WIDTH)**2) * min(sp_/0.18, 1.0)
                gate = 1.0 - skin_protect*skin_k
                lin = [lin[i]*(1.0 + (wb[i]-1.0)*gate) for i in range(3)]
                lin = [tonemap(v, white) for v in lin]
                # contrast on LUMA, not per channel: a per-channel S-curve
                # pulls R and B apart and inflates saturation — that is what
                # made the lips scream
                base = [rec709_oetf(v) for v in lin]
                yb = 0.2126*base[0] + 0.7152*base[1] + 0.0722*base[2]
                yc = contrast_curve(yb, contrast)
                k  = (yc/yb) if yb > 1e-6 else 1.0
                disp = [min(max(v*k, 0.0), 1.0) for v in base]
                disp = creative(disp, lift, sh_tint, hi_tint, sat, mid_tint,
                                skin_protect, skin_warm, sat_ceil=sat_ceil)
                if shoulder:
                    kn, ce = shoulder
                    disp = [v if v <= kn else
                            kn + (ce - kn) * (1.0 - math.exp(-(v - kn) / (ce - kn)))
                            for v in disp]
                out.append("%.6f %.6f %.6f" % tuple(disp))
    open(path,"w").write("\n".join(out)+"\n")
    return path

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--gamut", default="s-gamut3")
    ap.add_argument("--exposure", type=float, default=1.0)
    ap.add_argument("--contrast", type=float, default=1.0)
    ap.add_argument("--sat", type=float, default=1.0)
    ap.add_argument("--size", type=int, default=33)
    ap.add_argument("--white", type=float, default=6.0)
    ap.add_argument("--lift", type=float, default=0.0)
    ap.add_argument("--sh", default="0,0,0")
    ap.add_argument("--hi", default="0,0,0")
    ap.add_argument("--wb", default="1,1,1")
    ap.add_argument("--input", default="slog3")
    ap.add_argument("--mid", default="0,0,0")
    ap.add_argument("--skin-protect", type=float, default=0.0)
    ap.add_argument("--skin-warm", default="0,0,0")
    ap.add_argument("--gc-limit", type=float, default=0.88)
    ap.add_argument("--gc-start", type=float, default=0.80)
    a = ap.parse_args()
    g = SGAMUT3_CINE if "cine" in a.gamut.lower() else SGAMUT3
    sh=tuple(float(x) for x in a.sh.split(','))
    hi=tuple(float(x) for x in a.hi.split(','))
    wb=tuple(float(x) for x in a.wb.split(','))
    mid=tuple(float(x) for x in a.mid.split(','))
    sw=tuple(float(x) for x in a.skin_warm.split(','))
    build(a.out, g, a.size, a.exposure, a.contrast, a.sat, a.white, a.lift, sh, hi, wb,
          mid, a.skin_protect, sw, a.input.lower().startswith('slog'),
          a.gc_limit, a.gc_start)
    print("written", a.out)
