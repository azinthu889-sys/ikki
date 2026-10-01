# -*- coding: utf-8 -*-
"""ဗီဒီယိုထဲ **ကင်မရာ zoom** ဘယ်လောက် ရှိလဲ တိုင်းသည်

နည်းလမ်း — ဖရိမ်း အတွဲ တစ်ခုချင်းအတွက် candidate scale အများနဲ့ ကြိုးစားပြီး
အကိုက်ဆုံး scale ကို ရှာသည်。 1.0 ကနေ ကွာလျှင် 「zoom အတွဲ」 ဟု ရေတွက်သည်。

⚠️⚠️ **detector ကို အရင် အတည်ပြုရမည်** — အဖြေ သိပြီးသား ဖိုင်နဲ့ စမ်းရမည်
   ([[measure-distribution-rule]] · SFX မှာ ၄ ခါ လွဲခဲ့သော သင်ခန်းစာ)。
   `--selftest` က (၁) လုံးဝ မလှုပ်သော clip ⇒ ~၀% (၂) 1.15× zoom ⇒ ~၁၀၀%
   ထွက်ရမည်。 မထွက်လျှင် corpus ပေါ် မပြေးရ。

⚠️ **ပျံ့နှံ့မှု ပြရမည်** — မှန် တစ်ခုတည်း မပြရ。 zoom က bimodal ဖြစ်ကြောင်း
   ယခင် တိုင်းချက်မှာ တွေ့ထားပြီး (ဖိုင် ၃ ခု ၀% · ၂ ခု ၄၁%)。
"""
import os
import subprocess
import sys

import numpy as np

W = 192                      # တိုင်းသည့် အကျယ် (မြန်ရန်)
STEP = 0.5                   # ဖရိမ်း နမူနာ ကြားကာလ (စက္ကန့်)
SCALES = (0.94, 0.96, 0.98, 1.0, 1.02, 1.04, 1.06)
THR = 0.012
# s=1.0 ရဲ့ error ကနေ ဒီရာခိုင်နှုန်း အနည်းဆုံး ပိုကောင်းမှ zoom ဟု ရေတွက်သည်
GAIN = 0.12                  # ဒီထက် ကွာမှ 「zoom」 (1.2% ≈ သိသာသော ရွေ့)


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height",
                        "-show_entries", "format=duration",
                        "-of", "default=nw=1", path],
                       capture_output=True, text=True)
    d = {}
    for ln in r.stdout.splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1)
            try:
                d[k] = float(v)
            except ValueError:
                pass
    return d


def frames(path, dur, step=STEP, w=W, t0=0.0, t1=None):
    """[(t, gray 2-D float32)] — ffmpeg တစ်ခါတည်း ဖြတ်ပြီး ဆွဲသည်"""
    t1 = dur if t1 is None else t1
    span = max(0.1, t1 - t0)
    fps = 1.0 / step
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error",
                        "-ss", "%.2f" % t0, "-t", "%.2f" % span, "-i", path,
                        "-vf", "fps=%.4f,scale=%d:-2,format=gray" % (fps, w),
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True)
    if not r.stdout:
        return []
    # အမြင့်ကို ပထမ ဖရိမ်း ကနေ မှန်းသည်
    pr = probe(path)
    h = int(round(w * (pr.get("height", 1080) / max(1.0, pr.get("width", 1920)))))
    h -= h % 2
    n = len(r.stdout) // (w * h)
    if n < 2:
        return []
    a = np.frombuffer(r.stdout[:n * w * h], np.uint8).astype(np.float32)
    a = a.reshape(n, h, w)
    return [(t0 + i * step, a[i]) for i in range(n)]


def _crop_scale(img, s):
    """img ကို အလယ်ကနေ s ဆ zoom (s>1 = ပိုနီး) ⇒ အရွယ် တူတူ ပြန်ပေး"""
    h, w = img.shape
    if abs(s - 1.0) < 1e-9:
        return img
    ch, cw = int(round(h / s)), int(round(w / s))
    ch = max(8, min(h, ch)); cw = max(8, min(w, cw))
    y0 = (h - ch) // 2; x0 = (w - cw) // 2
    c = img[y0:y0 + ch, x0:x0 + cw]
    yi = (np.linspace(0, ch - 1, h)).astype(np.int32)
    xi = (np.linspace(0, cw - 1, w)).astype(np.int32)
    return c[yi][:, xi]


def best_scale(a, b):
    """a → b ရဲ့ scale ရွေ့ — `(s, gain)`。 s>1 = zoom in · s<1 = zoom out

    ⚠⚠ `_crop_scale` က **s<1 ကို လုပ်မရ** — `min(h, ch)` clamp က
       s<1 အားလုံးကို s=1 ဖြစ်စေသည် (debug မှာ 0.94…1.00 error အတူတူ
       ထွက်ခဲ့သည်)。 crop နဲ့ zoom out မရ — pad လိုသည်。
       ⇒ **လမ်း ၂ ဖက် တိုင်း**သည်: a ကို crop ၍ b နဲ့ ကိုက်လျှင် zoom in ·
         b ကို crop ၍ a နဲ့ ကိုက်လျှင် zoom out。 crop တစ်ခုတည်းနဲ့ ၂ ဖက် ရသည်。
    """
    def inner(x):
        h, w = x.shape
        return x[h // 8: h - h // 8, w // 8: w - w // 8]

    def scan(src, tgt):
        ti = inner(tgt)
        err = {}
        for s in SCALES:
            if s < 1.0:
                continue
            d = inner(_crop_scale(src, s))
            if d.shape != ti.shape:
                continue
            err[s] = float(np.abs(d - ti).mean())
        if 1.0 not in err:
            return 1.0, 0.0
        bs = min(err, key=err.get)
        if bs == 1.0 or err[1.0] <= 1e-9:
            return 1.0, 0.0
        return bs, (err[1.0] - err[bs]) / err[1.0]

    s_in, g_in = scan(a, b)          # b က a ကို zoom in လုပ်ထားလား
    s_out, g_out = scan(b, a)        # a က b ကို zoom in ⇒ zoom out
    if g_in >= g_out:
        return (s_in, g_in)
    return (1.0 / s_out, g_out)


def measure(path, t0=0.0, t1=None, step=STEP):
    pr = probe(path)
    dur = pr.get("duration") or 0.0
    if dur <= 0:
        return None
    fr = frames(path, dur, step=step, t0=t0, t1=t1)
    if len(fr) < 4:
        return None
    pairs, rates = 0, []
    for (ta, a), (tb, b) in zip(fr, fr[1:]):
        s, gain = best_scale(a, b)
        if abs(s - 1.0) >= THR and gain >= GAIN:
            pairs += 1
            rates.append(abs(s - 1.0) / max(1e-6, tb - ta))
    n = len(fr) - 1
    q = lambda v, p: (sorted(v)[min(len(v) - 1, int(round(p * (len(v) - 1))))]
                      if v else 0.0)
    return dict(dur=round(dur, 1), n=n,
                pct=round(100.0 * pairs / max(1, n), 1),
                rate_med=round(q(rates, .5), 4),
                rate_p90=round(q(rates, .9), 4))


# ══ detector အတည်ပြုချက် ═══════════════════════════════════════
def selftest(tmp):
    """① မလှုပ်သော clip ⇒ ~၀%  ② တကယ့် zoom in ⇒ ၀၅% အထက်

    ⚠️ `zoompan` နဲ့ ဆောက်ခဲ့ရာ zoom **မဖြစ်**ခဲ့ (error curve က
       ပြားနေသည်) ⇒ `crop` ကို `t` နဲ့ မောင်းပြီး တကယ့် zoom ဆောက်သည်。
    ⚠️ စမ်းသပ်ပုံက **အသေးစိတ် ရှိရမည်** — ပြားသော ပုံမှာ scale ကွာမှု
       မပေါ်ပါ (mandelbrot သုံးသည်)。
    """
    src = os.path.join(tmp, "_still.png")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y",
                    "-f", "lavfi", "-i", "mandelbrot=size=1280x720",
                    "-frames:v", "1", src], check=True)
    flat = os.path.join(tmp, "_flat.mp4")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-loop", "1",
                    "-i", src, "-t", "12", "-r", "25", "-vf", "scale=640:360",
                    "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18",
                    flat], check=True)
    zoom = os.path.join(tmp, "_zoom.mp4")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-loop", "1",
                    "-i", src, "-t", "12", "-r", "25",
                    # ⚠️ `crop` ရဲ့ w/h မှာ `t` သုံးလျှင် ffmpeg ကျသည်
                    #    (exit 234) · `zoompan` က zoom မဖြစ်ခဲ့ ⇒ `scale`
                    #    ကို `eval=frame` နဲ့ မောင်းပြီး crop သည် (စမ်းပြီး)。
                    "-vf", "scale=w='2*round(iw*(1+0.02*t)/2)':h=-2:"
                           "eval=frame,crop=640:360",
                    "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18",
                    zoom], check=True)
    a = measure(flat)
    b = measure(zoom)
    print("  ① မလှုပ်သော clip   pct %5.1f%%  (≤ ၅ ဖြစ်ရမည်)" % a["pct"])
    print("  ② တကယ့် zoom in   pct %5.1f%%  (≥ ၅၀ ဖြစ်ရမည်) · "
          "rate အလယ် %.4f" % (b["pct"], b["rate_med"]))
    ok = a["pct"] <= 5.0 and b["pct"] >= 50.0
    print("  ⇒ detector", "✓ အတည်ပြုပြီး" if ok else "⛔ မယုံရ — corpus မပြေးရ")
    return ok


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--selftest"]
    if "--selftest" in sys.argv[1:]:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            sys.exit(0 if selftest(td) else 1)
    print("  %-26s %7s %5s %7s %9s %9s" %
          ("ဖိုင်", "ကာလ", "n", "zoom%", "rate အလယ်", "rate p90"))
    rows = []
    for p in args:
        d = measure(p)
        if d is None:
            print("  %-26s (မရ)" % os.path.basename(p)[:26])
            continue
        rows.append(d)
        print("  %-26s %6.0fs %5d %6.1f%% %9.4f %9.4f"
              % (os.path.basename(p)[:26], d["dur"], d["n"], d["pct"],
                 d["rate_med"], d["rate_p90"]))
    if len(rows) > 1:
        v = sorted(r["pct"] for r in rows)
        q = lambda p: v[min(len(v) - 1, int(round(p * (len(v) - 1))))]
        print("  %-26s %13s %6.1f%%  (p10 %.1f · p90 %.1f)"
              % ("── အလယ်", "", q(.5), q(.1), q(.9)))
