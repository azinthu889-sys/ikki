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
 # ⚠️ animation ဆန်သော stock — motion graphics · 3D render · particle ·
 #    gradient loop。 ၎င်းတို့က သဘာဝအားဖြင့် **အသေးစိတ် နည်း**သဖြင့်
 #    `QDET 3.2` စစ်ချက် ကျတတ်သည် (headtop_motion မှာ ၇၇% ကျခဲ့)。
 #    ⇒ နောက်ခံ/insert အဖြစ်သာ သုံးရန် — B-roll စစ်ချက်နဲ့ မတိုင်းရ。
 "animation":      (["abstract animation loop","motion graphics background",
                     "3d render animation","particles animation","geometric animation",
                     "gradient animation loop","liquid animation","digital background loop",
                     "neon animation","wave animation loop","low poly animation",
                     "hologram interface","network connection animation","cyber background"],
                    48, "land"),
 "animation_v":    (["vertical abstract animation","vertical motion graphics",
                     "vertical particles","vertical gradient loop","vertical neon",
                     "vertical 3d render"], 20, "port"),
 "course":         (["classroom students","online learning","notebook writing",
                     "lecture hall","study desk","graduation"], 28, "land"),
 # ⚠️ **ZAE ရဲ့ အကြောင်းအရာ ယခင် PLAN မှာ လုံးဝ မပါခဲ့** (၂၀၂၆-၀၉-၂၅) —
 #    ငွေလွှဲ · မိုဘိုင်းဘဏ် · ဂျပန် · ဗီဇာ · ဂျပန်စာ。 `short_video` ရဲ့
 #    ရှာစာက 「vertical lifestyle/food/gym」 ဖြစ်နေ၍ ZAE ဗီဒီယိုတွေအတွက်
 #    **သက်ဆိုင်သော clip တစ်ခုမှ မရှိ**ခဲ့ပါ ⇒ B-roll ၀ ခု。
 "zae_money":      (["mobile banking app","money transfer phone","counting cash money",
                     "atm machine using","online payment phone","bank card payment",
                     "sending money online","wallet money hand"], 32, "port"),
 "zae_japan":      (["tokyo street day","japan city walk","japanese signage street",
                     "japan train station","japan office worker","tokyo crossing",
                     "japanese restaurant kitchen","japan convenience store"], 32, "port"),
 "zae_study":      (["student studying desk","japanese language book","writing notes class",
                     "online class laptop","passport visa document","airport departure",
                     "handshake job interview","factory worker japan"], 32, "port"),
}


# ⚠️ **ထပ်ဆွဲရာမှာ ရှာစာ အတူတူ သုံးလို့ မရ** — အရင်တစ်ခေါက် ကျခဲ့တဲ့ အကြောင်းရင်းက
#    ရှာစာကြောင့်ပါ。 cinematic_vlog က det 2.3 (ပစ်မှတ် 3.2) — မြူ/ကောင်းကင် လို
#    ပြားနေတဲ့ ရုပ်တွေ ဆွဲမိသည် ⇒ **အသေးစိတ် များသော** ရုပ်ကို ရှာရမည်。
#    knowledge က lum 22 (ပစ်မှတ် 60) — မှောင်သော ဖန်သားပြင်/ကုဒ် ⇒ **လင်းသော**
#    အလုပ်ခွင်/စာသင်ခန်းကို ရှာရမည်。
TOPUP = {
 "cinematic_vlog": ["city street cinematic","forest path walking","market crowd",
                    "waterfall close","train window day","neon street night"],
 "headtop_motion": ["paint ink water","smoke swirl light","particles sparkle",
                    "glass refraction","fabric waving","liquid gold",
                    "3d abstract shapes","kaleidoscope pattern","fluid art",
                    "light rays motion","crystal refraction","holographic foil"],
 "knowledge":      ["bright office meeting","whiteboard presentation","students classroom bright",
                    "notebook writing desk","team discussion table","library daylight"],
}


# ⚠️ **အင်္ဂလိပ် ရှာစာ → မြန်မာ သော့စကားလုံး** (၂၀၂၆-၀၉-၂၅)。
#    `broll._ask()` က clip တစ်ခုချင်းကို **Gemini vision** နဲ့ ဖော်ပြပြီး
#    မြန်မာ keyword ထုတ်သည် ⇒ Gemini ကျလျှင် index လုပ်၍ မရ、တွဲ၍လည်း မရ
#    (၂၀၂၆-၀၉-၂၅ ၅၀၃ — B-roll ကွင်းဆက် တစ်ခုလုံး ရပ်သွားခဲ့)。
# ⚠️ ဒါပေမယ့် **ဘာ ရှာလို့ ရလာမှန်း ကိုယ်တိုင် သိပြီးသား** —「money transfer
#    phone」နဲ့ ရှာလို့ ရလာတာကို vision နဲ့ ပြန်မှန်းစရာ မလိုပါ。 ရှာစာကနေ
#    တိုက်ရိုက် တပ်တာက **ပိုတိကျ**ပြီး ပြင်ပ မှီခိုမှုလည်း မရှိပါ。
KW_MY = {
 "mobile banking app":      ["ဖုန်း", "ဘဏ်", "အက်ပ်", "ငွေ"],
 "money transfer phone":    ["ငွေလွှဲ", "ဖုန်း", "ငွေ"],
 "counting cash money":     ["ငွေ", "ပိုက်ဆံ", "ရေတွက်"],
 "atm machine using":       ["ဘဏ်", "ငွေထုတ်", "ငွေ"],
 "online payment phone":    ["ငွေပေးချေ", "ဖုန်း", "အွန်လိုင်း"],
 "bank card payment":       ["ကတ်", "ဘဏ်", "ငွေပေးချေ"],
 "sending money online":    ["ငွေလွှဲ", "အွန်လိုင်း", "ငွေ"],
 "wallet money hand":       ["ပိုက်ဆံအိတ်", "ငွေ"],
 "tokyo street day":        ["တိုကျို", "ဂျပန်", "လမ်း"],
 "japan city walk":         ["ဂျပန်", "မြို့", "လမ်းလျှောက်"],
 "japanese signage street": ["ဂျပန်", "ဆိုင်းဘုတ်", "လမ်း"],
 "japan train station":     ["ဂျပန်", "ဘူတာ", "ရထား"],
 "japan office worker":     ["ဂျပန်", "ရုံး", "အလုပ်သမား"],
 "tokyo crossing":          ["တိုကျို", "ဂျပန်", "လမ်းဆုံ"],
 "japanese restaurant kitchen": ["ဂျပန်", "စားသောက်ဆိုင်", "မီးဖိုချောင်"],
 "japan convenience store": ["ဂျပန်", "ဆိုင်"],
 "student studying desk":   ["ကျောင်းသား", "စာကျက်", "စားပွဲ"],
 "japanese language book":  ["ဂျပန်စာ", "စာအုပ်", "သင်ယူ"],
 "writing notes class":     ["မှတ်စု", "အတန်း"],
 "online class laptop":     ["အွန်လိုင်းအတန်း", "ကွန်ပျူတာ", "သင်တန်း"],
 "passport visa document":  ["ပတ်စ်ပို့", "ဗီဇာ", "စာရွက်စာတမ်း"],
 "airport departure":       ["လေဆိပ်", "ထွက်ခွာ", "ခရီး"],
 "handshake job interview": ["အင်တာဗျူး", "အလုပ်", "လက်ဆွဲ"],
 "factory worker japan":    ["စက်ရုံ", "အလုပ်သမား", "ဂျပန်"],
}

SIDECAR = "stock_kw.json"     # {ဖိုင်အမည်: {"q": [...], "my": [...]}}


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
        # ⚠️ အမြင့်နဲ့ပဲ ရွေးလျှင် **၆၇၁ MB** ဖိုင် ဆွဲမိသည် (1080p ဖြစ်လျက် bitrate မြင့်)。
        # ⚠️ ဒါပေမဲ့ အရွယ်နဲ့ပဲ ကန့်သတ်လျှင် **960×540 · 640×360** အထိ ကျသွားသည်
        #    (တကယ် ဖြစ်ခဲ့) — 1080p timeline အတွက် သုံးမရ。
        #    ⇒ **အမြင့် ≥720 ဖြစ်တာထဲက** အရွယ် ၄၀MB အောက် · 1080 နဲ့ အနီးဆုံး。
        #    ၄၀MB အောက် မရှိလျှင် ထိုအုပ်စုထဲက အသေးဆုံး (၁၂၀MB ကျော်ရင် ကျော်)。
        CAP, HARD = 40e6, 120e6
        good = [f for f in fs if 720 <= (f.get("height") or 0) <= 1440]
        if not good: good = fs
        small = [f for f in good if (f.get("size") or 0) and f["size"] <= CAP]
        if small:
            small.sort(key=lambda f: abs((f.get("height") or 0)-1080))
            fs = small
        else:
            good.sort(key=lambda f: (f.get("size") or 1e12))
            if not good or (good[0].get("size") or 1e12) > HARD:
                continue                      # ⚠️ ကြီးလွန်းလျှင် ဤ clip ကို လုံးဝ ကျော်
            fs = good
        # ⚠️ **ရှာစာကို ရလဒ်ထဲ မှတ်ရမည်** — sidecar က ဒါနဲ့ မြန်မာ keyword တပ်သည်
        out.append(dict(src="pexels", q=q, id=v["id"], url=fs[0]["link"],
                        dur=v.get("duration"),
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
        out.append(dict(src="pixabay", q=q, id=v.get("id"), url=f["url"], dur=v.get("duration"),
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
    topup = os.environ.get("IKKI_TOPUP") == "1"
    for st, (qs, want, orient) in PLAN.items():
        if only and st not in only: continue
        if topup:
            qs = TOPUP.get(st) or qs
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
    # ⚠️ **sidecar — ဖိုင် → မြန်မာ သော့စကားလုံး**。 `core/broll.index()` က
    #    ဒါကို တွေ့လျှင် Gemini vision (`_ask`) ကို **လုံးဝ ကျော်**သည် ⇒
    #    Gemini ကျနေလည် stock clip တွေ index လုပ်လို့ရသည်。
    # ⚠️ မြေပုံမှာ မရှိသော ရှာစာကို **မမှန်းရ** — ဗလာ ထားပြီး `_ask` ကို
    #    ပြန်သွားစေသည် (မှားတပ်တာထက် မတပ်တာ ကောင်းသည်)。
    side = {}
    for r in rows:
        q = str(r.get("q") or "").strip().lower()
        my = KW_MY.get(q)
        if not my:
            continue
        side[os.path.basename(r["file"])] = {"q": q, "my": my,
                                             "en": q.split(), "style": r["style"]}
    json.dump(side, open(os.path.join(OUT, SIDECAR), "w"),
              ensure_ascii=False, indent=1)
    print(f"  📇 sidecar {len(side)}/{len(rows)} ဖိုင် — မြန်မာ keyword တပ်ပြီး "
          f"(Gemini မလို)", flush=True)
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
