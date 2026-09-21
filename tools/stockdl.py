#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI edit style တစ်ခုချင်းအတွက် **အခမဲ့ stock video** ဆွဲသည်。

    PEXELS_KEY=xxx [PIXABAY_KEY=yyy] python3 tools/stockdl.py search
    PEXELS_KEY=xxx [PIXABAY_KEY=yyy] python3 tools/stockdl.py build [style ...]

⚠️ **လိုင်စင် မျဉ်း** — IKKI ကို ရောင်းသည်。 Pexels · Pixabay · Coverr · Mixkit
   အားလုံးက **ဗီဒီယိုထဲ ထည့်သုံးခွင့်** (ကူးယူပြီး edit လုပ်၊ ကုန်သွယ်မှုအတွက်ပါ)
   ပေးသည် — ဒါပေမဲ့ ဖိုင်တွေကို **stock library အဖြစ် ပြန်ဖြန့်ခွင့် မပေး**。
   ⇒ IKKI က B-roll အဖြစ် ရိုက်ထည့်ရန် ✅ · သုံးစွဲသူကို ဖိုင်အတိုင်း ဒေါင်းခိုင်းရန် ❌
   (SFX pack နဲ့ အတူတူ မျဉ်းပါပဲ — [[sfx-library]])。
⚠️ ဖိုင်ကြီးတွေကို **Mac ထဲ မထားရ** — ပြင်ပ disk သို့。 Mac က ၁၁ GB ပဲ ကျန်သည်。
⚠️ API key မပါဘဲ ရသော ရင်းမြစ် **မရှိ**ပါ (တိုင်းပြီး: pexels 401 · pixabay 400 ·
   coverr 401 · wikimedia 200 သာ ဖြစ်ပြီး ၎င်းမှာ B-roll အသုံးဝင်တာ မရှိသလောက်)。
"""
import json, os, sys, time, urllib.parse, urllib.request

# ⚠️ **တစ်နေရာတည်း** — motionkit ထဲက `assets/stock/`。 ၎င်းသည် symlink ဖြစ်ပြီး
#    တကယ့် bytes က `/Volumes/i/ikki_big/stock` မှာ ရှိသည် (Mac မှာ ၁၁ GB ပဲ ကျန်)。
#    drive မတပ်ထားလျှင် symlink ပျက်နေမည် ⇒ **တိတ်တဆိတ် မကျရ**、အကြောင်း ပြောရမည်。
MK    = os.environ.get("IKKI_MOTIONKIT",
        "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")
OUT   = os.environ.get("IKKI_STOCK", os.path.join(MK, "assets", "stock"))
PEX = os.environ.get("PEXELS_KEY", "").strip()
PIX = os.environ.get("PIXABAY_KEY", "").strip()
UA  = "ikki-stock/1.0"

# style → (ရှာစာများ, ယူမည့်အရေအတွက်, အလျားလိုက်/ဒေါင်လိုက်)
# ⚠️ style တစ်ခုချင်း **ရုပ်ပုံသဘော မတူ** — Podcast က အခန်းတွင်း/စားပွဲ ·
#    Cinematic Vlog က သဘာဝ/ခရီး · Business က ရုံး/လက်ဆွဲ。
#    ရှာစာ တစ်ခုတည်းနဲ့ အားလုံးကို ဖုံးလို့ မရ。
PLAN = {
 "cinematic_vlog": (["cinematic landscape","slow motion nature","golden hour city",
                     "mountain fog","travel drone","rain window mood"], 28, "land"),
 "vlog":           (["street walking pov","cafe lifestyle","friends laughing",
                     "morning routine","city crosswalk","handheld travel"], 28, "land"),
 "podcast":        (["podcast studio","microphone closeup","two people talking",
                     "studio lighting","headphones desk","interview setup"], 24, "land"),
 "knowledge":      (["data charts screen","office whiteboard","typing laptop code",
                     "library books","teacher explaining","abstract network"], 28, "land"),
 "headtop_motion": (["abstract gradient motion","light leaks","bokeh particles",
                     "geometric loop","ink drop","soft studio backdrop"], 24, "land"),
 "talking_head":   (["person speaking camera","home office desk","bookshelf background",
                     "warm lamp interior","creator recording","desk setup"], 24, "land"),
 "short_video":    (["vertical lifestyle","vertical city walk","vertical food",
                     "vertical portrait","vertical nature","vertical gym"], 28, "port"),
 "promotional":    (["business handshake","product closeup","modern office",
                     "team meeting","logo reveal background","shopping payment"], 28, "land"),
 "brand_review":   (["product unboxing","comparison table screen","hands holding phone",
                     "retail shelf","star rating graphic","studio product"], 24, "land"),
 "business_short": (["vertical business","vertical office","vertical phone call",
                     "vertical handshake","vertical presentation","vertical laptop"], 24, "port"),
 "course":         (["classroom students","online learning","notebook writing",
                     "lecture hall","study desk","graduation"], 28, "land"),
}


def _get(url, hdr=None):
    for k in range(4):
        try:
            r = urllib.request.Request(url, headers={"User-Agent": UA, **(hdr or {})})
            with urllib.request.urlopen(r, timeout=45) as f:
                return json.loads(f.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503): time.sleep(8*(k+1)); continue
            raise
        except Exception:
            if k == 3: raise
            time.sleep(3)


def pexels(q, n, orient):
    if not PEX: return []
    d = _get("https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
        dict(query=q, per_page=min(40, n), orientation="portrait" if orient == "port" else "landscape",
             size="medium")), {"Authorization": PEX})
    out = []
    for v in d.get("videos", []):
        # ⚠️ Pexels ရဲ့ `video_files` မှာ `url` **မရှိ** — `link` ဖြစ်သည် (တကယ် ကျခဲ့:
        #    KeyError: 'url')。 API အဖြေကို မမှန်းဘဲ ကြည့်ပြီးမှ ရေးရသည်。
        fs = [f for f in v.get("video_files", [])
              if f.get("file_type") == "video/mp4" and f.get("width") and f.get("link")]
        if not fs: continue
        # ⚠️ ၄K/uhd ယူလျှင် ဖိုင် ၁၀၀ MB ကျော် — B-roll အတွက် မလို。 ~1080p ရွေးသည်
        fs.sort(key=lambda f: abs((f.get("height") or 0)-1080))
        out.append(dict(src="pexels", id=v["id"], url=fs[0]["link"], dur=v.get("duration"),
                        w=fs[0].get("width"), h=fs[0].get("height"),
                        by=(v.get("user") or {}).get("name"), page=v.get("url")))
    return out


def pixabay(q, n, orient):
    if not PIX: return []
    d = _get("https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
        dict(key=PIX, q=q, per_page=min(50, max(3, n)), safesearch="true")))
    out = []
    for v in d.get("hits", []):
        vs = v.get("videos") or {}
        f = vs.get("large") or vs.get("medium") or vs.get("small")
        if not f or not f.get("url"): continue
        if orient == "port" and (f.get("width", 0) >= f.get("height", 1)): continue
        if orient == "land" and (f.get("height", 0) > f.get("width", 1)): continue
        out.append(dict(src="pixabay", id=v.get("id"), url=f["url"], dur=v.get("duration"),
                        w=f.get("width"), h=f.get("height"),
                        by=v.get("user"), page=v.get("pageURL")))
    return out


def grab(url, dst):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(r, timeout=180) as f, open(dst, "wb") as o:
        while True:
            b = f.read(1 << 20)
            if not b: break
            o.write(b)
    return os.path.getsize(dst)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "search"
    only = set(sys.argv[2:])
    if not (PEX or PIX):
        raise SystemExit("PEXELS_KEY (သို့) PIXABAY_KEY မရှိ — "
                         "https://www.pexels.com/api/  ·  https://pixabay.com/api/docs/")
    if os.path.islink(OUT) and not os.path.isdir(OUT):
        raise SystemExit(f"stock လမ်းကြောင်း ပျက်နေသည် (drive မတပ်ထား?): {OUT} → "
                         f"{os.readlink(OUT)}")
    os.makedirs(OUT, exist_ok=True)
    found = {}
    for st, (qs, want, orient) in PLAN.items():
        if only and st not in only: continue
        got = []; seen = set()
        for q in qs:
            if len(got) >= want: break
            for r in (pexels(q, want-len(got), orient) + pixabay(q, want-len(got), orient)):
                k = (r["src"], r["id"])
                if k in seen: continue
                seen.add(k); got.append(r)
                if len(got) >= want: break
            time.sleep(0.4)
        found[st] = got
        print(f"  {st:16s} {len(got):3d}/{want}", flush=True)
    json.dump(found, open(os.path.join(OUT, "found.json"), "w"), ensure_ascii=False, indent=1)
    print(f"တွေ့ရှိ {sum(len(v) for v in found.values())} ခု", flush=True)
    if mode != "build": print("SEARCHDONE"); return

    rows = []; tot = 0
    for st, lst in found.items():
        d = os.path.join(OUT, st); os.makedirs(d, exist_ok=True)
        for i, r in enumerate(lst):
            p = os.path.join(d, f"{r['src']}_{r['id']}.mp4")
            if os.path.exists(p) and os.path.getsize(p) > 10000:
                rows.append(dict(style=st, file=p, **r)); continue
            try:
                sz = grab(r["url"], p); tot += sz
                rows.append(dict(style=st, file=p, bytes=sz, **r))
                print(f"  ✅ {st:16s} {r['src']:8s} {r.get('w')}x{r.get('h'):<5} "
                      f"{sz/1e6:6.1f} MB  {str(r.get('by'))[:18]}", flush=True)
            except Exception as e:
                print(f"  ❌ {st:16s} {r['src']} {r['id']} {type(e).__name__}", flush=True)
    json.dump(rows, open(os.path.join(OUT, "catalog.json"), "w"), ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "LICENSES.md"), "w") as f:
        f.write("# Stock video — လိုင်စင်\n\n"
                "Pexels · Pixabay လိုင်စင်: **ဗီဒီယိုထဲ ထည့်သုံးခွင့်** (ကုန်သွယ်မှုပါ) ရှိသည်၊\n"
                "credit မလိုအပ်。 ⚠️ ဖိုင်များကို **stock library အဖြစ် ပြန်ဖြန့်ခွင့် မရှိ** —\n"
                "IKKI က B-roll အဖြစ် ရိုက်ထည့်ရန်သာ သုံးရမည်。\n\n"
                "| style | ဖိုင် | ဇစ်မြစ် | ဖန်တီးသူ | မူလနေရာ |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['style']} | `{os.path.basename(r['file'])}` | {r['src']} | "
                    f"{r.get('by')} | {r.get('page')} |\n")
    print(f"STOCKDONE {len(rows)} ခု · {tot/1e9:.2f} GB → {OUT}", flush=True)


if __name__ == "__main__":
    main()
