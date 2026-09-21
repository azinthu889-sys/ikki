#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ဆွဲထားသော stock clip များကို IKKI ရဲ့ B-roll အညွှန်းထဲ ထည့်သည်。

⚠️ `broll.index()` က Gemini နဲ့ ဖရိမ်းကို စာဖြင့် ဖော်ပြခိုင်းပြီး ဖိုင်ကို
   `assets/broll/clips/` ထဲ **ကူးယူ**သည်。 stock အတွက် နှစ်ခုလုံး မလို —
   (၁) ဘယ်ရှာစာနဲ့ တွေ့ခဲ့လဲ သိပြီးသား ⇒ Gemini quota မကုန်စေရ
   (၂) ကူးလျှင် Mac disk မှာ ~၆ GB ထပ်ကုန်မည် (၁၁ GB ပဲ ကျန်) ⇒ **နေရာတည်းက** ညွှန်းသည်
⚠️ `style` field ထပ်ထည့်သည် — edit style အလိုက် သီးသန့် ရွေးနိုင်ရန်。
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "core"))
MK = os.environ.get("IKKI_MOTIONKIT",
     "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")
STOCK = os.path.join(MK, "assets", "stock")
INDEX = os.path.join(HERE, "assets", "broll", "index.json")

# style → (မြန်မာ keyword, kind)
QOF = {}
try:
    import importlib.util as _iu
    _sp = _iu.spec_from_file_location("_sd", os.path.join(HERE, "tools", "stockdl.py"))
    _m = _iu.module_from_spec(_sp); _sp.loader.exec_module(_m)
    QOF = {k: v[0] for k, v in _m.PLAN.items()}
except Exception:
    pass

STYLE_TAG = {
 "cinematic_vlog": (["ရုပ်ရှင်ဆန်", "သဘာဝ", "ခရီး", "နေဝင်ချိန်"], "nature"),
 "vlog":           (["လမ်းလျှောက်", "ကော်ဖီဆိုင်", "မြို့ပြ", "နေ့စဉ်ဘဝ"], "city"),
 "podcast":        (["မိုက်ခရိုဖုန်း", "စတူဒီယို", "စကားပြော", "အင်တာဗျူး"], "indoor"),
 "knowledge":      (["ဂရပ်", "လက်ပ်တော့", "သင်ကြားမှု", "စာအုပ်"], "screen"),
 "headtop_motion": (["နောက်ခံ", "အလင်း", "အရောင်စပ်", "ရွေ့လျားမှု"], "object"),
 "talking_head":   (["စကားပြောနေသူ", "အိမ်ရုံး", "စာအုပ်စင်", "မီးအိမ်"], "indoor"),
 "short_video":    (["ဒေါင်လိုက်", "နေ့စဉ်ဘဝ", "မြို့ပြ", "အစားအစာ"], "people"),
 "promotional":    (["လက်ဆွဲနှုတ်ဆက်", "ရုံး", "ကုန်ပစ္စည်း", "အဖွဲ့"], "indoor"),
 "brand_review":   (["ကုန်ပစ္စည်း", "နှိုင်းယှဉ်", "ဖုန်း", "ဆိုင်"], "object"),
 "business_short": (["ဒေါင်လိုက်", "စီးပွားရေး", "ရုံး", "ဖုန်းခေါ်"], "people"),
 "course":         (["စာသင်ခန်း", "ကျောင်းသား", "မှတ်စု", "သင်ယူမှု"], "indoor"),
}


def quality(p):
    """lum · det — `broll.quality()` နဲ့ **တူညီသော တွက်နည်း**。"""
    d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",p], capture_output=True, text=True).stdout.strip()
    try: dur = float(d)
    except Exception: return None, None, None
    lums=[]; dets=[]
    for f in (0.2, 0.5, 0.8):
        t = os.path.join("/tmp", f"stk_{os.getpid()}.jpg")
        r = subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{dur*f:.2f}","-i",p,
                            "-frames:v","1","-vf","scale=320:-2","-q:v","4",t],
                           capture_output=True)
        if r.returncode or not os.path.exists(t): continue
        # ⚠️ numpy 2.x မှာ uint8 × 299 က **OverflowError** (တကယ် ကျခဲ့)。
        #    `broll.quality()` က int32 သို့ ပြောင်းထားသည် — ဤမှာလည်း လိုသည်。
        a = np.asarray(Image.open(t).convert("RGB")).astype(np.int32)
        lum = (a[:,:,0]*299 + a[:,:,1]*587 + a[:,:,2]*114)//1000
        lums.append(float(lum.mean()))
        dets.append(float(np.abs(np.diff(lum.astype(float), axis=1)).mean()))
        os.remove(t)
    if not lums: return None, None, dur
    return round(sum(lums)/len(lums),1), round(sum(dets)/len(dets),1), dur


def main():
    cat = json.load(open(os.path.join(STOCK, "catalog.json"), encoding="utf-8"))
    try: db = json.load(open(INDEX, encoding="utf-8"))
    except Exception: db = {"clips": []}
    seen = {c["path"]: c for c in db.get("clips") or []}
    add = skip = bad = 0
    for r in cat:
        p = r["file"]
        if not os.path.exists(p): bad += 1; continue
        if p in seen and seen[p].get("lum") is not None: skip += 1; continue
        lum, det, dur = quality(p)
        if lum is None: bad += 1; print(f"  ✗ {os.path.basename(p)} ဖတ်မရ", flush=True); continue
        st = r["style"]; my, kind = STYLE_TAG.get(st, ([st], "object"))
        # ⚠️ catalog မှာ **ဘယ်ရှာစာနဲ့ တွေ့လဲ မမှတ်ထား** ⇒ style ရဲ့ ရှာစာ
        #    အားလုံးကို en tag အဖြစ် သုံးသည် (clip တွေက အဲဒီ ၆ ခုထဲက တစ်ခုမှ ဖြစ်သည်)。
        en = list(dict.fromkeys(w for q in QOF.get(st, []) for w in q.split()))
        c = dict(path=p, src=r.get("page") or r.get("url"), size=os.path.getsize(p),
                 dur=round(dur, 2), w=r.get("w"), h=r.get("h"),
                 my=list(my), en=list(dict.fromkeys(en + st.split("_"))),
                 kind=kind, lum=lum, det=det, style=st,
                 lic="stock-noship", by=r.get("by"))
        seen[p] = c; add += 1
        print(f"  ✓ {st:16s} {os.path.basename(p):26s} {r.get('w')}x{r.get('h'):<5} "
              f"{dur:5.1f}s lum {lum:5.1f} det {det:5.1f}", flush=True)
    db["clips"] = list(seen.values())
    json.dump(db, open(INDEX, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"STOCKIDXDONE အသစ် {add} · ရှိပြီး {skip} · မရ {bad} · စုစုပေါင်း {len(seen)}", flush=True)


if __name__ == "__main__":
    main()
