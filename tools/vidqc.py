#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ထွက်လာသော ဗီဒီယိုကို **တိုင်း**သည် — မှန်းဆချက် မဟုတ်。

    python3 tools/vidqc.py <out.mp4> [--h-cap 0.060] [--json]

⚠️ Zin ၂၀၂၆-၀၉-၂၂ ရဲ့ လိုအပ်ချက်: 「premium · fixed · done」ဟု
   **တိုင်းချက် မရှိဘဲ မဆိုရ**。 ဒါကြောင့် ဒီ tool က ထွက်ဖိုင်ကနေ
   တိုက်ရိုက် တိုင်းသည်。
⚠️ တိုင်းသည်:
     ကြာချိန် · frame · အရွယ်
     **စာသား ဘောင်ပြင် ထွက်မှု** (ink က အစွန် ထိသလား) — ၂၀၂၆-၀၉-၂၂ မှာ
        「Casper Mobile」·「account level」ဘယ်ဘက် ပြတ်ခဲ့သည်
     စာတန်း ဇုန်ရဲ့ ink အမြင့် (H ရဲ့ %) — 「စာတန်း သေးနေတယ်」စစ်ရန်
     အလင်း · ကွဲပြားမှု (grade)
     LUFS · true peak
"""
import json, os, subprocess, sys

EDGE = 0.012          # ဘောင် အစွန်ကနေ ဒီအတွင်း ink ရှိလျှင် **ပြတ်နိုင်**
SAMPLE_FPS = 2.0
CAP_LO, CAP_HI = 0.62, 0.98     # စာတန်း ရှိတတ်သော ဇုန်


def _sh(a):
    return subprocess.run(a, capture_output=True, text=True)


def probe(p):
    o = _sh(["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
             "-show_entries", "format=duration,bit_rate", "-of", "json", p]).stdout
    j = json.loads(o or "{}")
    st = (j.get("streams") or [{}])[0]
    n, d = str(st.get("r_frame_rate") or "0/1").split("/")
    return dict(w=int(st.get("width") or 0), h=int(st.get("height") or 0),
                fps=round(float(n) / float(d), 2) if float(d) else 0,
                dur=round(float((j.get("format") or {}).get("duration") or 0), 2),
                kbps=round(float((j.get("format") or {}).get("bit_rate") or 0) / 1000))


def _gray(p, w, h, fps=SAMPLE_FPS):
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", p,
                        "-vf", f"fps={fps},scale={w}:{h}", "-pix_fmt", "gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    if r.returncode or not r.stdout: return None
    b = np.frombuffer(r.stdout, dtype=np.uint8)
    n = len(b) // (w * h)
    if n < 1: return None
    return b[:n * w * h].reshape(n, h, w).astype(np.float32) / 255.0


def edge_text(p, w=480, h=270):
    """ဘောင် အစွန်မှာ **ခြစ်ထွက်နေသော စာသား/ဂရပ်ဖစ်** ရှာသည်。

    ⚠️ တိုက်ရိုက် 「ပြတ်တယ်」ဟု မဆိုနိုင် — နောက်ခံ ဗီဒီယိုက အစွန်အထိ
       ရှိပြီးသား。 ⇒ **အလျားလိုက် အနားသတ် အလွန်များသော ကော်လံ** က
       အစွန် ၁.၂% အတွင်း ရှိလျှင် အလံပြသည် (စာလုံးက အနားသတ် ထူသည်)。
    """
    import numpy as np
    fr = _gray(p, w, h)
    if fr is None: return None
    e = np.abs(np.diff(fr, axis=2))           # (n, h, w-1)
    col = e.mean(axis=(0, 1))                 # ကော်လံအလိုက် ပျမ်းမျှ
    k = max(2, int(w * EDGE))
    mid = float(np.median(col[k:-k])) or 1e-6
    lo = float(col[:k].max() / mid)
    hi = float(col[-k:].max() / mid)
    return dict(left_ratio=round(lo, 2), right_ratio=round(hi, 2),
                left_flag=lo > 2.2, right_flag=hi > 2.2,
                px=k, note="အစွန် အနားသတ် / အလယ် အနားသတ် အချိုး")


def cap_ink(p, w=960, h=540):
    """စာတန်း ဇုန်ရဲ့ **ink အမြင့်** (H ရဲ့ %)。

    ⚠️ **အနားသတ် သိပ်သည်းမှုနဲ့ တိုင်း၍ မရ** — နောက်ခံ ဗီဒီယိုက အဲဒီဇုန်မှာ
       အနားသတ် ရှိပြီးသား ⇒ ၂၉.၇% ဟု မှားတိုင်းခဲ့သည် (band တစ်ခုလုံးနီးပါး ·
       ၂၀၂၆-၀၉-၂၂ ဒီ tool ကိုယ်တိုင် ဖမ်းမိ)。
    ⚠️ ⇒ စာတန်းက **အလွန် လင်းသော** (white + shadow) စာလုံး ဖြစ်သဖြင့်
       luma ≥ `BRIGHT` ပစ်ဇယ် များသော **အတန်း**များကိုသာ ရေတွက်သည်。
       နောက်ခံ လင်းနေလျှင် မှားနိုင်သဖြင့် အတန်းတိုင်းမှာ ပစ်ဇယ် အနည်းဆုံး
       `MINPX` လိုသည် (စာလုံး အလျားလိုက် ဆက်နေသည်)。
    """
    import numpy as np
    BRIGHT, MINPX = 0.86, 0.04        # luma · အတန်းရဲ့ အကျယ် အနည်းဆုံး အချိုး
    fr = _gray(p, w, h)
    if fr is None: return None
    y0, y1 = int(h * CAP_LO), int(h * CAP_HI)
    seg = fr[:, y0:y1, :]
    nrow = seg.shape[1]
    per = []
    for i in range(seg.shape[0]):
        m = seg[i] >= BRIGHT
        cnt = m.sum(axis=1)
        idx = np.nonzero(cnt >= max(3, int(w * MINPX)))[0]
        if len(idx) >= 2:
            per.append((idx.max() - idx.min() + 1) / float(h))
    if not per:
        return dict(frames=0, ink_pct=None,
                    note="လင်းသော စာတန်း မတွေ့ (အရောင် မှိန်/scrim ဖြစ်နိုင်)")
    per = np.asarray(per)
    return dict(frames=int(len(per)),
                ink_pct=round(float(np.median(per)) * 100, 2),
                p90_pct=round(float(np.percentile(per, 90)) * 100, 2),
                coverage=round(len(per) / max(1, seg.shape[0]), 3),
                note="luma≥0.86 အတန်းများ (em မဟုတ် · ink)")


def loud(p):
    r = _sh(["ffmpeg", "-v", "info", "-nostats", "-i", p,
             "-af", "loudnorm=print_format=json", "-f", "null", "-"])
    t = r.stderr or ""
    try:
        j = json.loads(t[t.rindex("{"):t.rindex("}") + 1])
        return dict(lufs=round(float(j["input_i"]), 1),
                    tp=round(float(j["input_tp"]), 1),
                    lra=round(float(j["input_lra"]), 1))
    except Exception:
        return None


def grade(p):
    r = _sh(["ffmpeg", "-v", "info", "-nostats", "-i", p,
             "-vf", "fps=1,signalstats,metadata=print:file=-",
             "-an", "-f", "null", "-"])
    import numpy as np
    y, s = [], []
    for ln in (r.stdout or "").splitlines():
        if "YAVG" in ln:
            try: y.append(float(ln.split("=")[-1]))
            except ValueError: pass
        elif "SATAVG" in ln:
            try: s.append(float(ln.split("=")[-1]))
            except ValueError: pass
    if not y: return None
    return dict(luma=round(float(np.mean(y)), 1), luma_sd=round(float(np.std(y)), 1),
                sat=round(float(np.mean(s)), 1) if s else None)


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    p = argv[1]
    if not os.path.exists(p):
        print(f"  ✖ ဖိုင် မရှိ: {p}"); return 2
    cap_lim = 0.060
    for i, a in enumerate(argv):
        if a == "--h-cap" and i + 1 < len(argv): cap_lim = float(argv[i + 1])
    out = dict(file=os.path.basename(p), probe=probe(p))
    out["edge"] = edge_text(p)
    out["caption"] = cap_ink(p)
    out["loud"] = loud(p)
    out["grade"] = grade(p)
    if "--json" in argv:
        print(json.dumps(out, ensure_ascii=False, indent=1)); return 0
    pr = out["probe"]
    print(f"  ── {out['file']} ──")
    print(f"   {pr['w']}×{pr['h']} @ {pr['fps']}fps · {pr['dur']}s · {pr['kbps']} kbps")
    e = out["edge"] or {}
    _f = []
    if e.get("left_flag"): _f.append("ဘယ်")
    if e.get("right_flag"): _f.append("ညာ")
    print(f"   စာသား ဘောင်ပြင်: " + ("**" + "·".join(_f) + " အစွန်မှာ ခြစ်ထွက်နိုင်**"
          if _f else "မတွေ့ ✓")
          + f"  (ဘယ် {e.get('left_ratio')}× · ညာ {e.get('right_ratio')}×)")
    c = out["caption"] or {}
    print(f"   စာတန်း ink အမြင့်: {c.get('ink_pct')}% of H "
          f"(p90 {c.get('p90_pct')}%) · ပေါ်ချိန် {c.get('coverage')}")
    if c.get("ink_pct") is not None:
        print(f"      ⇒ ceiling {cap_lim*100:.1f}% နဲ့ နှိုင်းယှဉ်: "
              + ("ဘောင်ထဲ ✓" if c["ink_pct"] <= cap_lim * 100 * 1.35
                 else "**ကျော်နေ**"))
    l = out["loud"] or {}
    print(f"   LUFS {l.get('lufs')} · TP {l.get('tp')} · LRA {l.get('lra')}")
    g = out["grade"] or {}
    print(f"   အလင်း {g.get('luma')} (±{g.get('luma_sd')}) · sat {g.get('sat')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
