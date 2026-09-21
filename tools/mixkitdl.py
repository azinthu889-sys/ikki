#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mixkit ရဲ့ **အခမဲ့ sound effect** များကို တရားဝင် စာမျက်နှာကနေ ဆွဲသည်。

⚠️ Mixkit စာမျက်နှာက "free to download and ready to use in your next video or
   audio project, under the Mixkit License" ဟု ဆိုသည် — **ကုန်သွယ်မှု သုံးခွင့်
   ရှိပြီး credit မလို**。 သို့သော် **ပြန်ဖြန့်/asset pack အဖြစ် ထည့်ရောင်းခွင့်
   ရှိမရှိကို အတည်ပြု၍ မရသေး** (လိုင်စင် စာမျက်နှာက JS နဲ့သာ ဖွင့်သည်)。
   ⇒ ယခုအတွက် **render ထဲ သုံးရန်သာ** မှတ်ထားသည် (`.noship`)。
⚠️ preview mp3 များသာ တိုက်ရိုက် link ရှိသည် — မူရင်း WAV အတွက် သူ့ site ကနေ
   တစ်ခုချင်း ဒေါင်းရသည်。
"""
import json, os, re, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

MK   = os.environ.get("IKKI_MOTIONKIT",
       "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")
OUT  = os.path.join(MK, "assets", "sfx", "mixkit_free")
UA   = "Mozilla/5.0"
BASE = "https://mixkit.co/free-sound-effects/"

# ရည်ညွှန်း ဗီဒီယိုတွေထဲက အသံအမျိုးအစားတွေနဲ့ ကိုက်တဲ့ category
CATS = ["cinematic","whoosh","swoosh","transition","impact","hit","boom","thud",
        "punch","sweep","swell","glitch","click","pop","tap","beep","bleep",
        "interface","notification","ding","chimes","sparkle","magic","riser" ,
        "drone","suspense-music","high-tech","technology","sci-fi","laser",
        "type","typewriter","keyboard","page","paper","zoom","spin","rewind",
        "tape-machine","static","white-noise","metal","glass","wood","bass",
        "drum","cymbal","explosion","error","correct","win","wrong","countdown"]


def page_urls(cat):
    try:
        r = urllib.request.Request(BASE + cat + "/", headers={"User-Agent": UA})
        with urllib.request.urlopen(r, timeout=40) as f:
            h = f.read().decode("utf-8", "replace")
    except Exception:
        return []
    ids = re.findall(r'https://assets\.mixkit\.co/active_storage/sfx/(\d+)/\1-preview\.mp3', h)
    # ⚠️ ခေါင်းစဉ်ကို id နဲ့ တွဲရန် — ဖိုင်အမည် နားလည်ရလွယ်စေရန်
    titles = dict(re.findall(r'data-audio-id="(\d+)"[^>]*data-name="([^"]+)"', h))
    out = []
    for i in dict.fromkeys(ids):
        out.append(dict(cat=cat, id=i,
                        url=f"https://assets.mixkit.co/active_storage/sfx/{i}/{i}-preview.mp3",
                        title=titles.get(i, "")))
    return out


def grab(u, dst, tries=3):
    last = None
    for k in range(tries):
        try:
            r = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=90) as f, open(dst, "wb") as o:
                o.write(f.read())
            return os.path.getsize(dst)
        except Exception as e:
            last = e; time.sleep(3*(k+1))
    raise last


def main():
    only = set(sys.argv[1:])
    os.makedirs(OUT, exist_ok=True)
    found = []
    for c in CATS:
        if only and c not in only: continue
        u = page_urls(c); found += u
        print(f"  {c:16s} {len(u):3d}", flush=True)
        time.sleep(0.3)
    seen = set(); uniq = []
    for r in found:
        if r["id"] in seen: continue
        seen.add(r["id"]); uniq.append(r)
    print(f"တွေ့ရှိ {len(found)} · ထပ်နေတာ ဖယ် → {len(uniq)}", flush=True)

    def one(r):
        d = os.path.join(OUT, r["cat"]); os.makedirs(d, exist_ok=True)
        p = os.path.join(d, f"mixkit_{r['id']}.mp3")
        if os.path.exists(p) and os.path.getsize(p) > 5000: return None
        try: sz = grab(r["url"], p)
        except Exception as e: return ("err", r["id"], type(e).__name__)
        return ("ok", dict(r, file=p, bytes=sz))

    rows = []; bad = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for n, fu in enumerate(as_completed([ex.submit(one, r) for r in uniq]), 1):
            try: res = fu.result()
            except Exception: res = ("err", "?", "crash")
            if not res: continue
            if res[0] == "err": bad += 1; continue
            rows.append(res[1])
            if n % 100 == 0: print(f"  ⏱ {n}/{len(uniq)}", flush=True)
    json.dump(rows, open(os.path.join(OUT, "catalog.json"), "w"), ensure_ascii=False, indent=1)
    open(os.path.join(OUT, ".noship"), "w").close()
    with open(os.path.join(OUT, "LICENSES.md"), "w") as f:
        f.write("# Mixkit — အခမဲ့ sound effects\n\n"
                "Mixkit ၏ စာမျက်နှာအရ — **ကုန်သွယ်မှုအတွက် သုံးခွင့် ရှိပြီး credit မလို**。\n\n"
                "⚠️ **ပြန်ဖြန့် / asset pack အဖြစ် ထည့်ရောင်းခွင့် ရှိမရှိ အတည်မပြုရသေး** — "
                "လိုင်စင် စာမျက်နှာကို စက်ဖြင့် ဖတ်၍ မရပါ。 ⇒ ယခုအတွက် **render ထဲ "
                "B-roll/SFX အဖြစ် သုံးရန်သာ** သတ်မှတ်ထားသည် (`.noship`)。 ထုတ်ကုန်ထဲ "
                "ထည့်မည်ဆိုလျှင် https://mixkit.co/license/ ကို လူကိုယ်တိုင် စစ်ပါ。\n\n"
                f"ဖိုင် {len(rows)} ခု · ရင်းမြစ် https://mixkit.co/free-sound-effects/\n")
    sz = sum(r.get("bytes", 0) for r in rows)
    print(f"MIXKITDONE {len(rows)} ခု · ပျက် {bad} · {sz/1e6:.0f} MB → {OUT}", flush=True)


if __name__ == "__main__":
    main()
