#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mixkit ရဲ့ **အခမဲ့ stock video** ကို API key မလိုဘဲ ဆွဲသည်

    python3 tools/mixkitvid.py plan [group ...]     # လိုအပ်ချက် + ရနိုင်မှု
    python3 tools/mixkitvid.py get  [group ...]     # ဒေါင်း + catalog ရေး

⚠️⚠️ **ဘာကြောင့် ဒီဟာ လိုလဲ** — `tools/stockdl.py` (pexels · pixabay) က
   API key မပါဘဲ **မရ**ပါ (တိုင်းပြီး: pexels 401 · pixabay 400 · coverr 401)。
   ⇒ `zae_japan` · `zae_study` ရှာစာတွေ ရေးထားပြီး **တစ်ခုမှ မဒေါင်းခဲ့** ⇒
   B-roll index ၄၃၂ ခုမှာ ဂျပန်/ဗီဇာ/စာသင်ခန်း ပုံ **သုည** ⇒ render မှာ
   「match 0」 ဖြစ်ခဲ့သည် ([[ikki-broll-window]])。
   Mixkit က **key မလို**ဘဲ ရသည် (`tools/mixkitdl.py` က SFX အတွက် သုံးပြီးသား)。

⚠️ **လိုင်စင်** — item စာမျက်နှာကိုယ်တိုင် ဆိုသည်:
   「Download this free stock video clip for **commercial or personal use**,
     under the Mixkit Stock Video Free License」· credit မလို。
   `robots.txt` က `Allow: /` ဖြစ်ပြီး `sitemap-video.xml.gz` ပါ ထုတ်ထားသည်。
   ⚠️ **ဖိုင်များကို ပြန်ဖြန့်/ရောင်းခွင့် မရှိ** ⇒ `lic="mixkit-free-noship"`
      နဲ့ မှတ်ထားသည် — render ထဲ သုံးရန်သာ、asset pack အဖြစ် မပါရ。
   ⚠️ SaaS ရဲ့ asset pool အဖြစ် သုံးခြင်းက လိုင်စင်စာကြောင်း အတိအကျ
      မဖတ်ရသေး (license စာမျက်နှာက JS နဲ့သာ ဖွင့်သည်) ⇒ **Zin အတည်ပြုရန်**。

⚠️ **alt စာသားကို မယူရ** — listing HTML ကို item link နဲ့ ခွဲရာ `alt`/preview
   mp4 က **နောက် item** ရဲ့ markup ထဲမှာ ရှိသည် (တိုင်းပြီး: slug
   `quiet-tokyo-street-at-night` ⇒ alt「Neon signs…」 = တစ်ခု လွဲ)。
   ⇒ **slug ကိုသာ** ခေါင်းစဉ် အဖြစ် ယူသည် (slug ကိုယ်တိုင် ဖော်ပြချက် ဖြစ်သည်)。
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MK = os.environ.get("IKKI_MOTIONKIT",
     "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")
STOCK = os.path.join(MK, "assets", "stock")
CAT = os.path.join(STOCK, "catalog.json")
# ⚠️⚠️ **ဖိုင်ကြီးတွေကို Mac ထဲ မထားရ** — တိုင်းချက် (၂၀၂၆-၁၀-၀၂):
#    Mixkit ရဲ့ Full HD clip တစ်ခု **၂၀–၈၇ MB** (၃၂ Mbps အထိ) ⇒ ၅၀ ခု
#    ဆိုလျှင် ၂ GB ကျော်ပြီး Mac မှာ ၇ GB ပဲ ကျန်သည်。
#    ⇒ ပြင်ပ drive (`IKKI_BROLL_DEST`) ဆီ ထားပြီး `assets/broll_bank/mixkit`
#      ကနေ symlink ချိတ်သည် (B-roll က **ဖိုင်ကြီး sequential** ဖတ်မှု ⇒
#      ExFAT ရဲ့ ၃၁ MB/s နဲ့ လုံလောက်သည်; PNG ထောင်ချီ မဟုတ်)。
#    ⚠️ drive မတပ်ထားလျှင် index ထဲ လမ်းကြောင်း ပျက်မည် — `stockindex.py` က
#      `os.path.exists` စစ်ပြီး ကျော်သဖြင့် **တိတ်တဆိတ် မကျ**ပါ。
_LOCAL = os.path.join(HERE, "assets", "broll_bank", "mixkit")
DEST = os.environ.get("IKKI_BROLL_DEST") or _LOCAL
BASE = "https://mixkit.co/free-stock-video/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
CAP_MB = int(os.environ.get("MIXKIT_CAP_MB", "600"))   # disk ကာကွယ်

# ══ လိုအပ်ချက် ကြေညာ ([[sourcing-first-rule]]) ══════════════════════
# ⚠️ **စာရင်းကို အရင် ကြေညာရမည်** — ရှိတာနဲ့ အစားထိုးလျှင် 「match 0」 ပြန်ဖြစ်မည်。
#    group → (Mixkit keyword များ, group တစ်ခုလျှင် ယူမည့် အရေအတွက်, style)
NEED = {
 # ZAE ဂျပန် ပညာရေး — index ထဲ **သုည** ရှိသော အကြောင်းအရာ
 "zae_japan": (["tokyo", "japan", "japanese", "train-station", "subway",
                "street-sign"], 22, "course"),
 "zae_study": (["student", "classroom", "studying", "university",
                "notebook", "library"], 18, "course"),
 "zae_travel": (["airport", "passport", "suitcase", "airplane"], 10, "course"),
}

# ══ slug → မြန်မာ tag ══════════════════════════════════════════════
# ⚠️⚠️ **မြန်မာ tag က အရေးကြီးဆုံး**。 `broll._score()` က စာသားနဲ့ ရှစ်ထပ်
#    (lexical overlap) တွက်ပြီး IKKI ရဲ့ transcript က **မြန်မာ** ဖြစ်သည် ⇒
#    English tag တွေက တစ်ခါမှ မကိုက်ပါ。 `stockindex.py` ရဲ့ `STYLE_TAG` က
#    style တစ်ခုလျှင် မြန်မာ ၄ လုံးသာ ပေးသည် (clip တိုင်း အတူတူ) ⇒
#    clip တစ်ခုချင်းရဲ့ slug ကနေ တိကျသော tag ထုတ်ရမည်。
MY = {
 "tokyo": "တိုကျို", "japan": "ဂျပန်", "japanese": "ဂျပန်", "osaka": "အိုစာကာ",
 "kyoto": "ကျိုတို", "shrine": "ဘုရားကျောင်း", "temple": "ဘုရားကျောင်း",
 "street": "လမ်း", "city": "မြို့", "cityscape": "မြို့ပြ", "night": "ည",
 "neon": "နီယွန်", "sign": "ဆိုင်းဘုတ်", "signs": "ဆိုင်းဘုတ်",
 "train": "ရထား", "station": "ဘူတာ", "subway": "ဘူတာ", "traffic": "ယာဉ်",
 "crowd": "လူစု", "crowds": "လူစု", "people": "လူ", "pedestrian": "လမ်းသွား",
 "walk": "လမ်းလျှောက်", "walking": "လမ်းလျှောက်",
 "student": "ကျောင်းသား", "students": "ကျောင်းသား", "school": "ကျောင်း",
 "classroom": "စာသင်ခန်း", "class": "အတန်း", "study": "စာလေး",
 "studying": "စာကြိုးစား", "university": "တက္ကသိုလ်", "teacher": "ဆရာ",
 "lecture": "သင်တန်း", "library": "စာကြည့်တိုက်", "book": "စာအုပ်",
 "books": "စာအုပ်", "notebook": "မှတ်စု", "writing": "ရေး", "desk": "စားပွဲ",
 "laptop": "လက်ပ်တော့", "computer": "ကွန်ပျူတာ", "exam": "စာမေးပွဲ",
 "graduation": "ဘွဲ့", "learning": "သင်ယူ", "online": "အွန်လိုင်း",
 "airport": "လေဆိပ်", "airplane": "လေယာဉ်", "plane": "လေယာဉ်",
 "passport": "ပတ်စပို့", "suitcase": "ခရီးအိတ်", "luggage": "ခရီးအိတ်",
 "travel": "ခရီး", "departure": "ထွက်ခွာ", "flight": "ပျံသန်း",
 "cherry": "ချယ်ရီ", "blossom": "ပန်း", "spring": "နွေဦး", "rain": "မိုး",
 "snow": "ဆီးနှင်း", "food": "အစားအစာ", "office": "ရုံး", "work": "အလုပ်",
 "working": "အလုပ်", "money": "ငွေ", "shop": "ဆိုင်", "store": "ဆိုင်",
}
STOP = {"a", "an", "the", "of", "in", "on", "at", "to", "and", "with", "is",
        "are", "shot", "view", "time", "lapse", "full", "medium", "wide",
        "close", "up", "static", "from", "side", "front", "back", "his",
        "her", "their", "it", "its", "by", "for", "over", "out", "into"}


# ⚠️⚠️ **အမှားကို တိတ်တဆိတ် မမြိုရ**。 ပထမ ရေးချက်က ဘယ်အမှားမဆို `""`
#    ပြန်ပေးသဖြင့် rate-limit ခံရချိန်မှာ 「clip မရှိ」 ဟု ထင်ရသည် —
#    တကယ် ဖြစ်ခဲ့သည်: `airport` က ၇၂ ကနေ **၀** ဖြစ်သွားပြီး
#    「မလုံလောက်」 ဟု မှားတင်ပြမိခဲ့ (၂၀၂၆-၁၀-၀၂)。
#    ⇒ အကြောင်းရင်းကို `LAST_ERR` မှာ မှတ်ပြီး ခေါ်သူက ပြရမည်。
# ⚠️ ယဉ်ကျေးစွာ ဆွဲရမည် — တောင်းဆိုမှု ကြား နှေးချက် ထည့်သည်。
LAST_ERR = []
PAUSE = float(os.environ.get("MIXKIT_PAUSE", "1.2"))
_LASTREQ = [0.0]


def get(u, tries=4):
    for k in range(tries):
        _w = PAUSE - (time.time() - _LASTREQ[0])
        if _w > 0:
            time.sleep(_w)
        _LASTREQ[0] = time.time()
        try:
            r = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=60) as f:
                return f.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""
            if k == tries - 1:
                LAST_ERR.append("%s HTTP %s" % (u[-40:], e.code))
                return ""
        except Exception as e:
            if k == tries - 1:
                LAST_ERR.append("%s %s" % (u[-40:], type(e).__name__))
                return ""
        time.sleep(3.0 * (k + 1))        # backoff — rate limit ဖြစ်နိုင်သည်
    return ""


def listing(kw, pages=3):
    """keyword စာမျက်နှာကနေ `[(id, slug)]` — ⚠️ alt/mp4 မယူရ (တစ်ခု လွဲသည်)"""
    out, seen = [], set()
    for pg in range(1, pages + 1):
        u = BASE + kw + "/" + ("?page=%d" % pg if pg > 1 else "")
        h = get(u)
        if not h:
            break
        got = re.findall(r'href="/free-stock-video/([a-z0-9\-]+)-(\d+)/"', h)
        new = 0
        for slug, vid in got:
            if vid in seen:
                continue
            seen.add(vid); out.append((vid, slug)); new += 1
        if not new:
            break
    return out


def best_url(vid):
    """⚠️ ပုံစံ ၂ မျိုး ရှိသည် — `/videos/<id>/<id>-1080.mp4` (အများစု) နဲ့
       `/active_storage/video_items/<id>/<ts>/<id>-video-1080.mp4` (အသစ်)。
       ဒုတိယက `ts` လိုသဖြင့် item စာမျက်နှာကနေ ဖတ်ပြီး ကြည်လင်မှု တင်သည်。"""
    for res in ("1080", "720"):
        u = "https://assets.mixkit.co/videos/%s/%s-%s.mp4" % (vid, vid, res)
        try:
            r = urllib.request.Request(u, headers={"User-Agent": UA},
                                       method="HEAD")
            with urllib.request.urlopen(r, timeout=30) as f:
                return u, int(f.headers.get("Content-Length") or 0), res
        except Exception:
            pass
    return None, 0, ""


def item_url(vid, slug):
    """item စာမျက်နှာကနေ mp4 (active_storage ပုံစံ အတွက်)"""
    h = get("%s%s-%s/" % (BASE, slug, vid))
    if not h:
        return None, 0, ""
    us = sorted(set(re.findall(
        r'https://assets\.mixkit\.co/[^"\'\s]+?\.mp4', h)))
    if not us:
        return None, 0, ""
    for res in ("1080", "720", "360"):
        for u in us:
            cand = re.sub(r'-(360|720|1080)\.mp4$', '-%s.mp4' % res, u)
            try:
                r = urllib.request.Request(cand, headers={"User-Agent": UA},
                                           method="HEAD")
                with urllib.request.urlopen(r, timeout=30) as f:
                    return cand, int(f.headers.get("Content-Length") or 0), res
            except Exception:
                continue
    return None, 0, ""


# ══ ဒိုမိန်း ဝေါဟာရ — **ဆိုင်မဆိုင် အမျက်ပေးရန်** ═══════════════════
# ⚠️⚠️ Mixkit ရဲ့ keyword စာမျက်နှာက **အကြောင်းအရာအလိုက်** ဖြစ်ပြီး
#    စာသား အတိအကျ မကိုက်ပါ — တိုင်းချက် (၂၀၂၆-၁၀-၀၂): `tokyo` စာမျက်နှာ
#    ၇၂ ခုမှာ slug ထဲ 「tokyo」 ပါတာ ၂၈ (၃၉%) သာ。 ဒါပေမယ့် မပါသူများက
#    「neon-signs-with-japanese-letters」·「large-paper-lamp-in-the-street」
#    ⇒ **ဆိုင်သည်**。 ⇒ စာသား အတိအကျ မစစ်ရ、**ဝေါဟာရ** နဲ့ စစ်ရမည်。
# ⚠️ စာမျက်နှာ ၃ ဆီ သွားတော့ လျော့သွားတတ်သည် (`subway` ⇒
#    「sunset-over-train-tracks」) ⇒ အမျက် မြင့်သူကို **ရှေ့တန်း တင်**သည်。
VOCAB = {
 "zae_japan": set("""tokyo japan japanese osaka kyoto shrine temple street
   city cityscape urban night neon sign signs lantern lamp train station
   subway metro traffic crowd crowds pedestrian walk walking crossing
   junction cherry blossom shibuya"""        .split()),
 "zae_study": set("""student students school classroom class study studying
   university college teacher lecture library book books notebook writing
   write desk laptop computer exam graduation learning homework notes
   mathematical pencil reading read""".split()),
 "zae_travel": set("""airport airplane plane passport suitcase luggage travel
   departure arrival flight terminal boarding gate corridor runway baggage
   check""".split()),
}


def score_of(slug, g):
    """slug ရဲ့ ဒိုမိန်း အမျက် — ၀ ဆိုလျှင် **မယူရ**"""
    v = VOCAB.get(g) or set()
    w = [x for x in slug.split("-") if x and x not in STOP]
    return sum(1 for x in w if x in v)


def tags_of(slug):
    w = [x for x in slug.split("-") if x and x not in STOP]
    my = list(dict.fromkeys(MY[x] for x in w if x in MY))
    return w, my


def do_plan(groups):
    print("── လိုအပ်ချက် (ကြေညာ) ───────────────────────────────────")
    tot = 0
    for g in groups:
        kws, n, st = NEED[g]
        print("  %-11s %-5s ယူမည် %2d · ရှာစာ %s" % (g, st, n, ", ".join(kws)))
        tot += n
    print("  ⇒ စုစုပေါင်း လိုအပ် %d clip\n" % tot)
    print("── Mixkit မှာ ရနိုင်မှု ─────────────────────────────────")
    del LAST_ERR[:]
    for g in groups:
        kws, n, st = NEED[g]
        ids = {}
        for kw in kws:
            L = listing(kw, pages=3)
            for vid, slug in L:
                ids.setdefault(vid, slug)
            print("    %-14s %3d" % (kw, len(L)), flush=True)
        rel = {v: sl for v, sl in ids.items() if score_of(sl, g) > 0}
        print("  %-11s ထူးခြား %d · **ဆိုင်သူ %d** (လို %d)%s"
              % (g, len(ids), len(rel), n,
                 "  ⚠️ မလုံလောက်" if len(rel) < n else ""))
    if LAST_ERR:
        # ⚠️ **မရသော အကြောင်း ပြရမည်** — 「၀」 က 「မရှိ」 မဟုတ်နိုင်
        print("  ⚠️ တောင်းဆိုမှု မရ %d ခု — %s"
              % (len(LAST_ERR), " · ".join(LAST_ERR[-3:])))
    return 0


def _note(cat, dst, slug, vid, st, g, mb):
    """catalog entry ရေးသည် — ⚠️ အရွယ်ကို **ffprobe** နဲ့ တိုင်းရမည်、
       URL ရဲ့「1080」က အမြင့်သာ ဖြစ်ပြီး အကျယ်က clip အလိုက် မတူ。"""
    import subprocess
    en, my = tags_of(slug)
    pr = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", dst],
        capture_output=True, text=True).stdout.strip()
    try:
        W, H = [int(x) for x in pr.split(",")[:2]]
    except (ValueError, IndexError):
        W = H = 0
    for i, c in enumerate(cat):
        if c.get("file") == dst:
            cat.pop(i); break
    cat.append(dict(file=dst, style=st, w=W, h=H,
                    page="%s%s-%s/" % (BASE, slug, vid),
                    by="Mixkit", title=slug.replace("-", " "),
                    tags=en, my=my, group=g, lic="mixkit-free-noship"))
    return cat


def do_get(groups):
    os.makedirs(DEST, exist_ok=True)
    if DEST != _LOCAL and not os.path.exists(_LOCAL):
        try:
            os.makedirs(os.path.dirname(_LOCAL), exist_ok=True)
            os.symlink(DEST, _LOCAL)
            print("  ⇒ symlink %s → %s" % (_LOCAL, DEST))
        except OSError as e:
            print("  ⚠️ symlink မရ (%s) — လမ်းကြောင်း တိုက်ရိုက် သုံးသည်" % e)
    try:
        cat = json.load(open(CAT, encoding="utf-8"))
    except (OSError, ValueError):
        cat = []
    have = {c.get("file") for c in cat}
    used = 0
    add = 0
    for g in groups:
        kws, n, st = NEED[g]
        ids = {}
        for kw in kws:
            for vid, slug in listing(kw, pages=3):
                ids.setdefault(vid, slug)
        # ⚠️ အမျက် မြင့်သူ အရင် — `dict` အစီအစဉ် (စာမျက်နှာ အစီ) က
        #    ဆိုင်မဆိုင် မဆိုလိုပါ。 အမျက် ၀ ကို **လုံးဝ မယူ**。
        rank = sorted(((score_of(sl, g), vid, sl) for vid, sl in ids.items()),
                      key=lambda x: -x[0])
        rank = [(v, sl) for sc, v, sl in rank if sc > 0]
        print("── %s · ရနိုင် %d · ဆိုင်သူ %d · ယူမည် %d ──"
              % (g, len(ids), len(rank), n), flush=True)
        k = 0
        for vid, slug in rank:
            if k >= n:
                break
            dst = os.path.join(DEST, "%s_%s.mp4" % (vid, slug[:44]))
            # ⚠️⚠️ **ဖိုင် ရှိပြီးသားကို ရေတွက်ရုံ မလုပ်ရ** — catalog ထဲ
            #    မရေးဘဲ ကျော်ခဲ့ရာ ဒေါင်းပြီးသား clip ၁၂ ခု
            #    `stockindex.py` ဆီ **ဘယ်တော့မှ မရောက်**ခဲ့ (၂၀၂၆-၁၀-၀၂)。
            if os.path.exists(dst) and os.path.getsize(dst) > 1000:
                if dst not in have:
                    _note(cat, dst, slug, vid, st, g,
                          os.path.getsize(dst) / 1e6)
                    add += 1
                k += 1
                continue
            u, sz, res = best_url(vid)
            if not u:
                u, sz, res = item_url(vid, slug)
            if not u:
                print("    ✖ %-6s %s (mp4 မရ)" % (vid, slug[:40]), flush=True)
                continue
            mb = sz / 1e6
            if used + mb > CAP_MB:
                print("    ⊘ disk ကန့်သတ် %d MB ပြည့် — ရပ်သည်" % CAP_MB)
                break
            try:
                r = urllib.request.Request(u, headers={"User-Agent": UA})
                with urllib.request.urlopen(r, timeout=180) as f, \
                        open(dst, "wb") as o:
                    o.write(f.read())
            except Exception as e:
                print("    ✖ %-6s %s" % (vid, str(e)[:40]), flush=True)
                continue
            used += mb
            k += 1
            _note(cat, dst, slug, vid, st, g, mb)
            _c = cat[-1]
            add += 1
            # ⚠️ **clip တစ်ခုပြီးတိုင်း သိမ်း** — ရပ်သွားလည် မပျောက်ရ
            json.dump(cat, open(CAT, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print("    ✓ %-6s %-44s %4dx%-4d %5.1f MB · my %s"
                  % (vid, slug[:42], _c.get("w") or 0, _c.get("h") or 0, mb,
                     " ".join((_c.get("my") or [])[:4])), flush=True)
        json.dump(cat, open(CAT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print("\nMIXKITDONE အသစ် %d · %.0f MB · catalog %d · %s"
          % (add, used, len(cat), CAT))
    print("⇒ နောက်တစ်ဆင့်: python3 tools/stockindex.py")
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] not in ("plan", "get"):
        print(__doc__)
        return 2
    groups = [a for a in argv[2:] if not a.startswith("-")] or list(NEED)
    bad = [g for g in groups if g not in NEED]
    if bad:
        print("group မရှိ: %s (ရှိသည်: %s)" % (bad, list(NEED)))
        return 2
    return do_plan(groups) if argv[1] == "plan" else do_get(groups)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
