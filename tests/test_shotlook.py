"""shotlook — အပြင်/အတွင်း ခွဲခြင်းနဲ့ အပိုင်းလိုက် grade test

⚠️ `windowed()` ရဲ့ ထွက်လာသော chain ကို **ffmpeg နဲ့ တကယ် စမ်း**သည် —
   စာသား မှန်ယုံနဲ့ မလုံလောက်ပါ、ffmpeg က လက်ခံမှ အလုပ်ဖြစ်သည်。
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import shotlook as SL      # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def main():
    print("── ၁ · အမျိုးအစား ခွဲခြင်း ──")
    check("အလင်းပြင်း → အပြင်",
          SL.classify(dict(lum=222, p95=255, warm=1.01, sky=0)) == SL.OUTDOOR)
    check("highlight ပြတ် → အပြင် (အလင်း နည်းလည်း)",
          SL.classify(dict(lum=125, p95=255, warm=1.14, sky=17)) == SL.OUTDOOR)
    check("မှောင် + အဝါ → အတွင်း",
          SL.classify(dict(lum=95, p95=195, warm=1.17, sky=1)) == SL.INDOOR)
    check("မှောင် + အရောင်မဲ့ → ပုံမှန်",
          SL.classify(dict(lum=117, p95=194, warm=1.02, sky=4)) == SL.NEUTRAL)
    check("တိုင်း၍ မရလျှင် ပုံမှန်", SL.classify(None) == SL.NEUTRAL)

    print("\n── ၂ · ကုသမှု ──")
    o = SL.treatment(SL.OUTDOOR, dict(lum=222, p95=255, warm=1.01, sky=0))
    i = SL.treatment(SL.INDOOR)
    check("အပြင် — အပေါ်ပိုင်း ချသည်", o["lv_omax"] < 1.0, o["lv_omax"])
    check("ပြတ်နေလျှင် ပိုချသည်", o["lv_omax"] <= 0.90, o["lv_omax"])
    check("အပြင် — အနက် မဖိပါ", o["lv_omin"] <= 0.0 + 1e-6, o["lv_omin"])
    check("အတွင်း — colorbalance ဖွင့်သည်", i["cbal"] is True)
    for k, t in (("outdoor", o), ("indoor", i)):
        check(f"{k} — sat ၁.၀၆ မကျော်", t["sat"] <= 1.06, t["sat"])
        check(f"{k} — vignette မသုံး", t["vign"] == 0.0, t["vign"])

    print("\n── ၃ · အပိုင်း ပေါင်းခြင်း ──")
    segs = SL.scan.__doc__ is not None
    check("scan မှာ မှတ်ချက် ပါသည်", segs)

    print("\n── ၄ · windowed() ──")
    fc = ("colorlevels=rimin=0.03:rimax=0.97,"
          "curves=all='0/0 0.5/0.52 1/1',eq=saturation=1.03")
    w = SL.windowed(fc, 1.0, 5.0)
    check("filter တစ်ခုချင်း enable ရသည်", w.count("enable=") == 3, w.count("enable="))
    check("curves ထဲက , မခွဲမိပါ", "0/0 0.5/0.52 1/1" in w, w[:80])

    # ⚠️ ffmpeg နဲ့ တကယ် စမ်း — လက်ခံမှ အလုပ်ဖြစ်သည်
    d = tempfile.mkdtemp(prefix="shotlook_")
    src = os.path.join(d, "s.mp4")
    out = os.path.join(d, "o.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                    "-i", "color=c=0x8899AA:s=160x90:r=30:d=3",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", src], check=True)
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", w,
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", out],
                       capture_output=True, text=True)
    check("ffmpeg က လက်ခံသည်", r.returncode == 0 and os.path.exists(out),
          (r.stderr or "")[:120])

    if r.returncode == 0:
        import numpy as np

        def px(p, t):
            q = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", p,
                                "-frames:v", "1", "-vf", "scale=8:8,format=rgb24",
                                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                               capture_output=True)
            a = np.frombuffer(q.stdout, np.uint8).astype(float)
            return a.reshape(-1, 3).mean(0) if len(a) >= 192 else None

        a_in = px(out, 2.0)      # ဝင်းဒိုး အတွင်း (၁–၅s)
        a_out = px(out, 0.3)     # ဝင်းဒိုး ပြင်ပ
        base = px(src, 0.3)
        if a_in is not None and a_out is not None and base is not None:
            d_in = float(np.abs(a_in - base).mean())
            d_out = float(np.abs(a_out - base).mean())
            print(f"    ဝင်းဒိုးအတွင်း ကွာ {d_in:.1f} · ပြင်ပ ကွာ {d_out:.1f}")
            check("ဝင်းဒိုးအတွင်းမှာ grade ဝင်သည်", d_in > 2.0, d_in)
            check("ဝင်းဒိုးပြင်ပမှာ မဝင်ပါ", d_out < 1.0, d_out)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
