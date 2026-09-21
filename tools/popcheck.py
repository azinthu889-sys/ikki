#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""keyword pop template များကို **တစ်ခုချင်း ဆောက်ပြီး တိုင်း**သည်。

⚠️ `planner` က `kinetic.word_pop` **တစ်ခုတည်း** hardcode ထားသဖြင့် pop
   အားလုံး တူတူ ဖြစ်သည် (တိုင်းချက်: ဝါကျ ၁၀ ကြောင်းမှာ `word_pop` ၃ ခါ)。
⚠️ props ပုံစံ တူတာ ၃၅ ခု ရှိသည် — ဒါပေမယ့် exit animation · quote mark ·
   အရောင် ၂ ခု လိုတာတွေ ပါသဖြင့် **မြင်မကြည့်ဘဲ ရွေးလျှင် မှန်းဆ**ဖြစ်သည်。
   ⇒ တစ်ခုချင်း မြန်မာ စကားလုံးနဲ့ ဆောက်ပြီး ink box တိုင်းသည်。

ဂိတ် —
  ① ဆောက်လို့ ရရမည် (ကျဘမ်း မဖြစ်ရ)
  ② နောက်ဆုံး frame မှာ ink **ရှိရမည်** (ဗလာ မဖြစ်ရ)
  ③ ink က ဘောင်ထဲ ရှိရမည် (အနား ၂% ကျော် မထွက်ရ)
  ④ ink အမြင့် က `word_pop` ရဲ့ အမြင့်နဲ့ **±၁၅% အတွင်း** ရှိရမည် —
     လဲလိုက်လျှင် အရွယ် မပြောင်းစေရန် (`punch` ၂၁.၄%H က `word_pop`
     ၁၆.၉%H ထက် ၂၇% ကြီးသည် ⇒ ပယ်)
  ⑤ ပထမ frame နဲ့ နောက်ဆုံး frame **မတူရ** — မတူမှ animation ရှိသည်

    python3 tools/popcheck.py [--out assets/pop_ok.txt]
"""
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))

W, H = 1920, 1080
KW = "အရေးကြီး"          # မြန်မာ — ဗျည်းတွဲ ပါသည်
TEXT_H = 0.101            # planner ရဲ့ ပစ်မှတ် (tools/../core/pose.py)
SIZE = int(round(TEXT_H * 1.20 * H))
FILL = "#F5D000"


def ink(png):
    """alpha ရဲ့ နယ်နိမိတ် `(x0, x1, y0, y1, ratio)` — မရှိလျှင် None"""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGBA"))[:, :, 3]
    ys = np.nonzero(a.max(axis=1) > 8)[0]
    xs = np.nonzero(a.max(axis=0) > 8)[0]
    if not len(ys) or not len(xs):
        return None
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()),
            float((a > 8).mean()))


def check(tid, log=print):
    import dress as DR
    fn = DR._fn(tid)
    if fn is None:
        return None, "template မတွေ့"
    props = dict(text=KW, size=SIZE, y=int(H * 0.45), dur=2.0, fill=FILL)
    # ⚠️ **frame PNG က motionkit ရဲ့ cwd နဲ့ relative** (`work/kt/pc_000.png`)
    #    ⇒ တိုင်းချက်ကိုပါ အဲဒီ cwd ထဲမှာပဲ လုပ်ရမည် (`slide_clip` နည်းတူ)。
    cwd = os.getcwd()
    try:
        import gfxcat as GC
        if GC.MK not in sys.path:
            sys.path.insert(0, GC.MK)
        os.chdir(GC.MK)
        el = DR._call_template(fn, tid, "pc", props)
        if not isinstance(el, dict) or not el.get("anim"):
            return None, "anim မရ"
        seq = [q for q, _x, _y in el["anim"]]
        a0, a1 = ink(seq[0]), ink(seq[-1])
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        os.chdir(cwd)
    if a1 is None:
        return None, "နောက်ဆုံး frame ဗလာ"
    x0, x1, y0, y1, cov = a1
    m = int(W * 0.02)
    if x0 < m or x1 > W - m:
        return None, f"ဘောင် ဘေး ကျော် (x {x0}–{x1})"
    if y0 < 0 or y1 > H:
        return None, f"ဘောင် အပေါ်/အောက် ကျော် (y {y0}–{y1})"
    hp = (y1 - y0) / float(H)
    if not (0.04 <= hp <= 0.30):
        return None, f"အမြင့် {hp*100:.1f}%H — ဘောင် ပြင်ပ"
    same = (a0 is not None and a0[:4] == a1[:4])
    if same:
        return None, "ပထမ/နောက်ဆုံး frame တူ — animation မရှိ"
    return dict(id=tid, h_pct=round(hp, 4), w_px=x1 - x0, cov=round(cov, 5),
                frames=len(seq)), None


def main(out=None):
    import dress as DR, gfxcat as GC
    need = {"text", "size", "y"}
    cands = []
    for e in GC.catalog():
        pm = {(p.get("name") or ""): p for p in (e.get("params") or [])
              if isinstance(p, dict)}
        if not need <= set(pm):
            continue
        req = {n for n, p in pm.items()
               if p.get("required") and p.get("default") is None and not p.get("auto")}
        if req - {"text", "size", "y", "fill", "col", "dur"}:
            continue
        cands.append(e["id"])
    print(f"  ပုံစံ တူညီသော template {len(cands)} ခု — တစ်ခုချင်း ဆောက်မည်")
    ok, bad = [], []
    for tid in cands:
        r, why = check(tid)
        if r:
            ok.append(r); print(f"  ✓ {tid:<26} အမြင့် {r['h_pct']*100:5.1f}%H · "
                                f"အကျယ် {r['w_px']:>4}px · frame {r['frames']}")
        else:
            bad.append((tid, why)); print(f"  ✗ {tid:<26} {why}")
    # ⚠️ **`word_pop` ရဲ့ အမြင့်ကို စံ** ထားပြီး ±၁၅% အတွင်းသာ ယူသည် —
    #    လဲလိုက်လျှင် pop ရဲ့ အရွယ် မပြောင်းစေရန်。
    base = next((r["h_pct"] for r in ok if r["id"] == "kinetic.word_pop"), None)
    if base:
        keep, off = [], []
        for r in ok:
            if abs(r["h_pct"] - base) / base <= 0.15:
                keep.append(r)
            else:
                off.append((r["id"], r["h_pct"]))
        for i, h in off:
            print(f"  ⊘ {i:<26} အမြင့် {h*100:.1f}%H — စံ {base*100:.1f}% နဲ့ "
                  f"{abs(h-base)/base*100:.0f}% ကွာ")
        ok = keep
    # ⚠️ **အဓိပ္ပာယ် ပြောင်းသော template ကို ပယ်ရမည်** — တိုင်းချက်နဲ့ မဖမ်းမိပါ。
    #    `strike_in` က မျဉ်းဖြတ် (= ပယ်ဖျက်) · `quote_marks` က စကားထည့်
    #    ⇒ ကျပန်း စကားလုံးပေါ် သုံးလျှင် အကြောင်းအရာကို **လွဲမှားစွာ ပြ**မည်。
    SEM_NO = {"kinetic2.strike_in", "kinetic2.quote_marks"}
    for r in list(ok):
        if r["id"] in SEM_NO:
            ok.remove(r)
            print(f"  ⊘ {r['id']:<26} အဓိပ္ပာယ် ပြောင်းသည် (မျဉ်းဖြတ်/စကားထည့်)")
    print(f"\n  ⇒ အောင် {len(ok)}/{len(cands)}")
    p = out or os.path.join(ROOT, "assets", "pop_ok.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("# keyword pop — တစ်ခုချင်း ဆောက်ပြီး တိုင်းထားသည် "
                "(tools/popcheck.py)\n")
        f.write(f"# မြန်မာ「{KW}」· size {SIZE} · ဘောင် {W}x{H}\n")
        f.write(f"# အောင် {len(ok)}/{len(cands)}\n")
        for r in sorted(ok, key=lambda x: x["id"]):
            f.write(f"{r['id']}  # {r['h_pct']*100:.1f}%H {r['w_px']}px\n")
    print(f"  📄 {p}")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(a[a.index("--out") + 1] if "--out" in a else None))
