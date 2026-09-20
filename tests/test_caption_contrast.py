"""စာတန်း ဖတ်ရလွယ်မှု — plate က တကယ် ကူညီမကူညီ တိုင်းသည်။

⚠️ **စာလုံးကို နောက်ခံနဲ့ တိုက်ရိုက် မနှိုင်းရ**。 plate က စာလုံးကို မထိဘဲ
   **ပတ်ဝန်းကျင်** ကို မှောင်စေခြင်း ဖြစ်သည် — စာလုံးချင်း နှိုင်းလျှင်
   ဘာမှ မပြောင်းဟု လွဲမည် (ဒီ project မှာ cttext အရိပ် တိုင်းရာ တကယ်
   ဖြစ်ခဲ့သော အမှား)。 ⇒ **ink ↔ ink ရဲ့ ပတ်ဝန်းကျင်** ကို တိုင်းသည်。

⚠️ နောက်ခံ RGB (၁၇၆,၁၇၃,၁၆၅) က မှန်းထားတာ မဟုတ်ပါ —
   `IKKI_Premium_v2.mp4` ကို တိုင်းယူထားသော တကယ့်ကိန်း。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import captions as CP      # noqa: E402
import contrast as CT      # noqa: E402

try:
    from PIL import Image, ImageDraw
    import numpy as np
except Exception:
    Image = None

BG = (176, 173, 165)       # တိုင်းထားသော တကယ့် နောက်ခံ
FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def fake_ct(d):
    """cttext အစား — အဖြူ စာလုံး ပုံစံ ဆွဲပေးသည်"""
    for fr in d["frames"]:
        w, h = int(d["w"]), int(d["h"])
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        txt = (d.get("text") or "").strip()
        if txt:
            sz = int(d.get("size") or 40)
            n = max(1, len(txt))
            tw = min(int(w * 0.70), n * int(sz * 0.62))
            x0 = (w - tw) // 2
            y0 = (h - sz) // 2
            # စာလုံး အစား တုံး — alpha နဲ့ နေရာက အရေးကြီး၊ ပုံသဏ္ဌာန် မဟုတ်
            for i in range(n):
                cx = x0 + int(i * tw / n)
                dr.rectangle([cx + 2, y0, cx + int(tw / n) - 3, y0 + sz],
                             fill=(255, 255, 255, 255))
        im.save(fr["out"])


def fake_mw(word, size, font=None):
    return len(word) * size * 0.62


def ink_vs_surround(png):
    """composite ပြီးနောက် ink ↔ ပတ်ဝန်းကျင် ကွာဟမှု"""
    im = Image.open(png).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    al = a[..., 3] / 255.0
    bg = np.array(BG, np.float32)
    comp = a[..., :3] * al[..., None] + bg * (1 - al[..., None])

    ink = al > 0.85
    if ink.sum() < 50:
        return None
    # ⚠️ ပတ်ဝန်းကျင် = ink မဟုတ်သော pixel、ဒါပေမယ့် **ink ရဲ့ အနီးအနား**သာ。
    #    ဘောင်တစ်ခုလုံး ယူလျှင် plate မဖုံးသော အပိုင်း ရောပြီး လွဲမည်。
    ys, xs = np.nonzero(ink)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    pad = 24
    sub_ink = ink[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]
    sub_px = comp[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]
    sur = ~sub_ink
    if sur.sum() < 50:
        return None
    fg = sub_px[sub_ink].mean(0)
    bgm = sub_px[sur].mean(0)
    return CT.ratio(tuple(fg), tuple(bgm)), tuple(round(x) for x in bgm)


def render(work, plate):
    os.makedirs(work, exist_ok=True)
    caps = [dict(text="ဂျပန်မှာ အလုပ်လုပ်ချင်တယ်", start=0.0, end=2.0)]
    out = os.path.join(work, "caps.mov")
    CP.track(caps, out, work, 1920, 1080, 54, "#FFFFFF", "Pyidaungsu",
             None, 0.78, fake_ct, fake_mw, fps=30, total=3.0,
             stroke="#000000", stroke_w=0.06, plate=plate)
    # ⚠️ PNG **နှစ်မျိုး** ရှိသည် — စာကြောင်းတစ်ခုချင်း `c0000_0.png` နဲ့
    #    ထပ်ပြီးသား `c0000.png`。 plate က **ထပ်ပြီးသား**ထဲမှာသာ ရှိသည်
    #    (`_stack()` ထဲ ဆွဲသဖြင့်)。 အက္ခရာစဉ်အရ `_0` က နောက်မှာ ဖြစ်၍
    #    `[-1]` ယူလျှင် မှားသော ဖိုင် ရမည် (ဒီ test ကိုယ်တိုင် အဲဒီလို
    #    မှားခဲ့ပြီး 「plate အလုပ်မလုပ်」ဟု လွဲပြခဲ့သည်)。
    pngs = [os.path.join(work, f) for f in sorted(os.listdir(work))
            if re.fullmatch(r"c\d{4}\.png", f)]
    return [q for q in pngs if ink_vs_surround(q)]


def main():
    if Image is None:
        print("  ⚠️ PIL မရှိ — test ကျော်သည်")
        return 0

    import tempfile
    base = tempfile.mkdtemp(prefix="capct_")

    print("── နောက်ခံ RGB", BG, "(တိုင်းထားသော တကယ့်ကိန်း) ──\n")

    a = render(os.path.join(base, "plain"), None)
    b = render(os.path.join(base, "plate"),
               dict(alpha=0.62, pad_x=24, pad_y=12, radius=16))

    check("plate မပါဘဲ ပုံထွက်သည်", len(a) > 0)
    check("plate ပါဘဲ ပုံထွက်သည်", len(b) > 0)
    if not (a and b):
        print("  ✗ ပုံ မထွက်၍ ဆက်မတိုင်းနိုင်")
        return 1

    ra, bga = ink_vs_surround(a[-1])
    rb, bgb = ink_vs_surround(b[-1])
    print(f"  plate မပါ : ကွာဟမှု {ra:5.2f}:1 · ပတ်ဝန်းကျင် {bga}")
    print(f"  plate ပါ  : ကွာဟမှု {rb:5.2f}:1 · ပတ်ဝန်းကျင် {bgb}")
    print()

    check("plate မပါလျှင် ဂိတ် မမီပါ (ပြဿနာ ပြန်ဖြစ်သည်)",
          ra < CT.MIN_RATIO, f"{ra:.2f}")
    check("plate ထည့်လျှင် ကွာဟမှု တက်သည်", rb > ra, f"{ra:.2f} → {rb:.2f}")
    check("plate ထည့်လျှင် ဂိတ် ၃:၁ မီသည်", rb >= CT.MIN_RATIO, f"{rb:.2f}")
    check("ပတ်ဝန်းကျင် မှောင်သွားသည်", sum(bgb) < sum(bga),
          f"{bga} → {bgb}")

    print("\n── ဆုံးဖြတ်ချက် ယုတ္တိ ──")
    d = CT.decide(dict(ok=False, needPlate=True, ratio=1.7))
    check("ကွာဟမှု ၂ အောက် → plate", d["mode"] == "plate")
    d = CT.decide(dict(ok=False, needPlate=False, ratio=2.4))
    check("ကွာဟမှု ၂–၃ → stroke ထူထူ", d["mode"] == "stroke" and d["strokePx"] >= 4)
    d = CT.decide(dict(ok=True, needPlate=False, ratio=8.0))
    check("ကွာဟမှု လုံလောက် → plain", d["mode"] == "plain")
    d = CT.decide(dict(measured=False, ok=False, needPlate=True, ratio=None))
    check("တိုင်းလို့ မရလျှင် ဘေးကင်းဘက် (plate)", d["mode"] == "plate")

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
