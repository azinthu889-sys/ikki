"""SFX variant pool — role တစ်ခုအတွက် **ဖိုင် အမျိုးမျိုး** ရွေးသည် (P1)

⚠️ `sfxlib.ROLE` က role ၂၂ ခုစလုံးကို **ဖိုင်တစ်ခုတည်း** ညွှန်းထားသည် —
   ၄၉၇ ဖိုင် ရှိပါလျက် (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。 တူညီသော whoosh/click
   ထပ်ကာထပ်ကာ ကြားရလျှင် asset ကောင်းပေမယ့် အတုဆန်သည်。

⚠️ ရွေးချယ်မှုက **deterministic** ဖြစ်ရမည် — 「Re-rendering the same plan
   resolves identical assets and timings」(spec §12)。 ⇒ seed + အညွှန်းနဲ့
   တွက်သည်、ကျပန်း မဟုတ်。
⚠️ **မကြာခင်က သုံးထားတာ ပြန်မသုံးရ** — no-repeat ဝင်းဒိုး。
"""
import hashlib
import json
import os

_CAT = None

# ⚠️ role တစ်ခုချင်းရဲ့ **ကြာချိန် ဘောင်** — ရှည်လွန်းသော whoosh က
#    စကားကို ဖုံးသည် (catalog ရဲ့ dur p10 ၀.၁၂ · အလယ်တန်း ၀.၄၁ · p90 ၃.၁၉)
DUR_MAX = {"click": 0.35, "pop": 0.45, "latch": 0.60, "swipe": 0.70,
           "whoosh": 1.20, "shimmer": 1.50, "impact": 1.50,
           "riser": 3.20, "sub": 2.00, "air": 4.00,
           # ⚠️ `bed` — **စကား band ပြင်ပ** cue သာ ဝင်သည် (အောက်က
           #    `BED_GAP` ကြည့်) ⇒ ရှည်ပေမယ့် စကားကို မဖုံးပါ。
           "bed": 6.00}
# ⚠️ **`bed` ရဲ့ ဂိတ်က ကြာချိန် မဟုတ် — `mask_gap`**。 ၂၀၂၆-၀၉-၂၅ တိုင်းချက်
#    (နမူနာ ၁၅၆ ခု · role ၁၂ မျိုး အညီအမျှ): ကွာဟမှု အလယ်တန်း **၃.၁ dB** ·
#    p75 ၅.၇ · **p90 ၁၀.၇** · p95 ၁၄.၂。 ⇒ ၁၀.၅ dB ဆိုလျှင် အထက် ~၁၀%。
#    အဲဒီ cue တွေက စွမ်းအင်ကို စကား band ပြင်ပ (အများစု ၂၅၀ Hz အောက်)
#    ထားသဖြင့် ၄ စက္ကန့် ရှည်လည် စကားကို မဖုံးပါ —
#    `CINEMATIC-028` ၁၁.၂ · `HIGH_TECH-002` ၁၅.၅ (Zin ကြိုက်သော ၂ ခု)。
#    ⚠️ brightness နဲ့ အစားထိုး၍ **မရ** — `BLEEP-003` က centroid ၈,၂၀၄ Hz
#    ဖြစ်ပါလျက် ကွာ ၄.၃ dB သာ。
BED_GAP = 10.5
BED_MIN = 1.50          # တိုလွန်းလျှင် bed မဟုတ် — cue သာ
NOREPEAT = 6            # နောက်ဆုံး N ခုထဲ ပြန်မပါရ


def _mk():
    try:
        import gfxcat as GC
    except ImportError:
        from core import gfxcat as GC
    return GC.MK


def _cue_dir():
    """Writable normalized-SFX cache.

    Motion Kit is mounted read-only in production so that a render cannot
    mutate the template library.  Keep generated WAV cues in the job scratch
    volume instead; on a Mac the historical Motion Kit cache remains the
    default.
    """
    return os.environ.get("IKKI_SFX_CACHE") or os.path.join(_mk(), "audio", "cue")


def catalog():
    global _CAT
    if _CAT is None:
        p = os.path.join(_mk(), "audio", "catalog.json")
        try:
            with open(p, encoding="utf-8") as f:
                _CAT = json.load(f)
        except (OSError, ValueError):
            _CAT = {"items": []}
    return _CAT


def pool(role, bright=None, max_dur=None, ship=True):
    """role တစ်ခုရဲ့ ရွေးစရာများ — `[item]` · အချိန်တိုဆုံးက ရှေ့

    `bright` — `(lo, hi)` Hz · ပုံစံအလိုက် တောက်/မှိန် ရွေးရန်
    `ship`   — **ပုံသေ `True`** ⇒ ရောင်းခွင့်ရှိသော အသံသာ。 IKKI က SaaS ဖြစ်၍
               customer ရဲ့ ဗီဒီယိုထဲ ထည့်သည် ⇒ youtubesfx pack (ship=False) ကို
               မသုံးရ。 `ship=None` ဆိုလျှင် လိုင်စင် မကြည့်ဘဲ အားလုံး。
    """
    lim = max_dur if max_dur is not None else DUR_MAX.get(role, 2.0)
    out = []
    # ⚠️ **`bed` က role တစ်ခု မဟုတ်** — catalog ရဲ့ `role` ကို ပြောင်းလျှင်
    #    ရှိပြီးသား pool (whoosh/impact …) ကနေ cue ပျောက်မည် ⇒ `bed` ကို
    #    **တိုင်းချက်နဲ့ ရွေးသော အခွဲ** အဖြစ်သာ ထားသည် (role မထိ)。
    _bed = (role == "bed")
    for x in catalog().get("items") or []:
        if _bed:
            if float(x.get("mask_gap") or 0) < BED_GAP:
                continue
            _d = float(x.get("dur_eff") or x.get("dur") or 0)
            if not (BED_MIN <= _d <= lim):
                continue
        elif x.get("role") != role:
            continue
        if ship and not x.get("ship", False):
            continue
        # ⚠️ **ကြားရသော အရှည် (`dur_eff`) နဲ့ စစ်ရမည်** — ဖိုင်အရှည် မဟုတ်
        #    (၂၀၂၆-၀၉-၂၅)。 ဂိတ်ရဲ့ ရည်ရွယ်ချက်က 「cue က စကားကို မဖုံးရ」
        #    ဖြစ်ရာ ဖုံးတာက **ကြားရသော အပိုင်း**သာ — reverb အမြီးက မဖုံးပါ。
        #    `SWOOSH-005` က ဖိုင် ၃.၁၈s ဒါပေမယ့် ကြားရ **၀.၉၇s** ·
        #    `CLICK-004` က ၁.၃၇s → **၀.၁၅s** ⇒ ဖိုင်အရှည်နဲ့ စစ်ခဲ့သဖြင့်
        #    Zin ကြိုက်သော cue ၁၁ ခုလုံး ပယ်ခံခဲ့သည်。
        #    ⚠️ ဒါက **ဂိတ် လျှော့တာ မဟုတ်** — ကြားရသော အရှည် ကျော်လျှင်
        #    ပယ်ဆဲ ဖြစ်သည်。 `dur_eff` မရှိသော အဟောင်း row က `dur` သို့ ဆုတ်။
        _de = float(x.get("dur_eff") or x.get("dur", 9))
        if _de > lim:
            # ⚠️ **ဂိတ်ထက် အနည်းငယ် ရှည်လျှင် ဖြတ်ပြီး သုံးနိုင်သည်** —
            #    `wav()` က `min(dur_eff, lim)` အထိ ဖြတ်ပြီး ၆၀ms fade
            #    ထည့်သည် ⇒ **အသံ ကျယ်ချိန် (`peak_t`) က ဖြတ်မျဉ်းအတွင်း**
            #    ရှိလျှင် cue ရဲ့ ဇာတိ မပျက်ပါ。 ဒါက ဂိတ် လျှော့တာ မဟုတ် —
            #    ထွက်လာသော cue က တကယ် `lim` သာ ရှည်သည်。
            #    တိုင်းချက် (၂၀၂၆-၀၉-၂၅ · Zin ကြိုက်သော cue):
            #      BLEEP-003 ကျယ်ချိန် ၀.၂၀s · ဂိတ် ၀.၄၅ ⇒ ဖြတ်လို့ရ
            #      GLITCH-030 ကျယ်ချိန် **၂.၈၀s** · ဂိတ် ၂.၀၀ ⇒ **မရ**
            #      (အကျယ်ဆုံး အပိုင်းက ဖြတ်မျဉ်း နောက်မှာ ⇒ ဇာတိ ပျက်မည်)
            _pt = x.get("peak_t")
            if _pt is None or float(_pt) + 0.06 > lim:
                continue
            # ⚠️ ၂ ဆ အထက် ရှည်လျှင် မယူ — ဖြတ်ချက်က cue ကို အပိုင်းအစ
            #    ဖြစ်စေပြီး တိတ်သလို ခံစားရသည်。
            if _de > lim * 2.0:
                continue
        if bright:
            b = x.get("brightness") or 0
            if not (bright[0] <= b <= bright[1]):
                continue
        # A catalog row is not a usable cue until its audio file is present in
        # this runtime.  The Mac-only legacy bank is intentionally skipped on
        # the VPS when it was not deployed.
        if not path(x):
            continue
        out.append(x)
    out.sort(key=lambda x: (x.get("dur", 9), x.get("id", "")))
    return out


_FAV = None


def fav():
    """**Zin ကြိုက်သော cue** id set — `assets/sfx_fav.txt`

    ⚠️ ဖိုင် မရှိလျှင် **ဗလာ** ပြန်သည် (ဦးစားပေးမှု မရှိ) — ခန့်မှန်းပြီး
       ရွေးလျှင် သူ မကြိုက်သော အသံ ထွက်မည်。
    """
    global _FAV
    if _FAV is None:
        q = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "assets", "sfx_fav.txt")
        try:
            with open(q, encoding="utf-8") as f:
                _FAV = {l.strip() for l in f
                        if l.strip() and not l.startswith("#")}
        except OSError:
            _FAV = set()
    return _FAV


# ⚠️ **ကြိုက်သော cue ကို ၁၀၀% မထားရ**。 အလုံးစုံ ထားလျှင် seed မတူပေမယ့်
#    ရလဒ် တူသွားပြီး (`tests/test_sfxpool.py` ရဲ့ 「seed မတူ ⇒ ရလဒ် ကွဲ」
#    ကျသည်) ဗီဒီယိုတစ်ပုဒ်လုံးမှာ click တစ်မျိုးတည်း ထွက်ကာ **အတုဆန်**မည် —
#    variant pool ဆောက်ခဲ့ခြင်းရဲ့ ရည်ရွယ်ချက် ပျက်သည်。 ⇒ **အချိုး**နဲ့သာ。
# ⚠️ **ပထမ cue တွေကို ကြိုက်သူ ဖြစ်ရမည်**。 ၂၀၂၆-၀၉-၂၅ render
#    (j_3d16ef298c02) မှာ အသံဖြစ်ရပ် **၁ ခု / cue ၂ ခု**သာ ရှိသဖြင့်
#    ၆၅% အချိုးနဲ့ Zin ရဲ့ အမည်တပ် cue ရောက်ခြင်း မရခဲ့ပါ
#    (`mixkit_free/click_2867` ရခဲ့ — pack က မှန်ပေမယ့် သူ ရွေးထားတာ မဟုတ်)。
#    ⇒ role တစ်ခုရဲ့ **ပထမ ၂ ခု**ကို ကြိုက်သူ ဖြစ်စေသည် (ZAE ဗီဒီယို
#    အများစုမှာ cue ၂–၃ ခုသာ ရှိ ⇒ အမြဲ သူ့အသံ)。 ကျန်တာကို အချိုးနဲ့
#    ခွဲသဖြင့် ရှည်သော ဗီဒီယိုမှာ ကွဲပြားမှု ကျန်သည်
#    (`tests/test_sfxpool.py` ရဲ့ 「seed မတူ ⇒ ရလဒ် ကွဲ」 ကို မဖျက်ပါ)。
FAV_FIRST = 2
FAV_SHARE = 0.50


def prefer_fav(free, n=0, idx=None):
    """ကြိုက်သော cue ရှိလျှင် အဲဒါတွေထဲကသာ ရွေးစေသည်

    ⚠️ `pool()` ရဲ့ sort နဲ့ မရပါ — ရွေးချယ်မှုက **hash နဲ့ တူညီစွာ** ဖြစ်၍
       ရှေ့ဆုံး ထားရုံနဲ့ ရွေးခံရမှု မတိုးပါ ⇒ ခွဲထုတ်ရသည်。
    ⚠️ **ရွေးစရာ ၂ နေရာ ရှိသည်** — `pick()` (manifest) နဲ့ `wav()`
       (တကယ့် render)。 တစ်နေရာသာ ထည့်လျှင် render မှာ မထွက်ပါ。
    """
    _fv = fav()
    if not _fv:
        return free
    _p = [x for x in free if x.get("id") in _fv]
    if not _p:
        return free
    # ⚠️ hash ရဲ့ ကိန်းကနေ **အချိုး** ဆုံးဖြတ်သည် ⇒ တူညီစွာ ပြန်ရသည်
    #    (reproducible) ဒါပေမယ့် seed မတူလျှင် ကွဲသည်。
    _rest = [x for x in free if x.get("id") not in _fv]
    if not _rest:
        return _p
    if idx is not None and int(idx) < FAV_FIRST:
        return _p
    return _p if (n % 100) < int(FAV_SHARE * 100) else _rest


def path(item):
    """catalog item → တကယ့် ဖိုင် လမ်းကြောင်း (root အလိုက်)"""
    rs = catalog().get("roots") or {}
    r = rs.get(item.get("root"))
    candidate = os.path.join(r, item["path"]) if r else ""
    if candidate and os.path.isfile(candidate):
        return candidate

    # The catalog is measured on the Mac and records its original absolute
    # paths.  Production mounts the owned Motion Kit at IKKI_MOTIONKIT, so
    # resolve only assets which actually exist in that runtime.  This avoids
    # selecting an otherwise `ship=true` cue that becomes silent on Linux.
    mk_root = os.path.join(_mk(), "assets", "sfx")
    fallback = os.path.join(mk_root, item.get("path", ""))
    return fallback if os.path.isfile(fallback) else None


def pick(role, seed, idx=0, used=(), bright=None, ship=True):
    """variant တစ်ခု ရွေးသည် — `item` · pool ဗလာဆိုလျှင် `None`

    ⚠️ **တူညီသော (seed, idx) ⇒ တူညီသော ရလဒ်** (reproducible render)。
    ⚠️ `used` ထဲက နောက်ဆုံး `NOREPEAT` ခုကို ရှောင်သည် — ရှောင်လို့ မရလျှင်
       (pool သေးလျှင်) **အနီးဆုံးကို ယူ**သည်、မပေးဘဲ မနေရ。
    """
    ps = pool(role, bright=bright, ship=ship)
    if not ps:
        return None
    recent = {x for x in list(used)[-NOREPEAT:]}
    h = hashlib.sha1(f"{seed}|{role}|{idx}".encode()).digest()
    n = int.from_bytes(h[:4], "big")
    free = prefer_fav([x for x in ps if x["id"] not in recent] or ps, n, idx)
    return free[n % len(free)]


def resolve(cues, seed="ikki", bright=None, ship=True):
    """`[(at, role, db)]` → `[(at, role, db, item)]` — **manifest အတွက်**

    ⚠️ ဖြေရှင်းချက်ကို မှတ်တမ်းတင်ရမည် (spec §6: 「record the exact resolved
       asset in a render manifest for reproducibility」)。
    """
    out, used = [], []
    for i, c in enumerate(cues or []):
        at, role, db = (list(c) + [None, None, None])[:3]
        it = pick(role, seed, i, used, bright, ship=ship)
        if it:
            used.append(it["id"])
        out.append((at, role, db, it))
    return out


def stats(ship=True):
    """role တစ်ခုချင်း ရွေးစရာ ဘယ်နှစ်ခု ရှိလဲ — report အတွက်"""
    return {r: len(pool(r, ship=ship)) for r in sorted(
        {x.get("role") for x in catalog().get("items") or []} - {None})}


# ══ role အမည် ချိတ်ဆက်ခြင်း ═════════════════════════════════════════
# ⚠️ planner/dress က `whoosh_in` · `riser_soft` စသည် **၂၂ မျိုး** ထုတ်သည် ·
#    catalog က `whoosh` · `riser` စသည် **မိသားစု အမည်**သာ ⇒ ချိတ်ရမည်。
# ⚠️ `bright` က variant ရွေးချယ်မှုကို **အဓိပ္ပာယ် ရှိစေသည်** — `deep_whoosh`
#    ဟု တောင်းပြီး ၁၀kHz တောက်ပသော whoosh ရလျှင် အလကား。 catalog ရဲ့
#    brightness အလယ်တန်း ၄၈၇၆ Hz · p10 ၇၈၇ · p90 ၁၀၅၃၀ ကို တိုင်းပြီး ခွဲသည်。
MAP = {
    "whoosh_in":   ("whoosh",  (3000, 99999), 0),
    "whoosh_out":  ("whoosh",  (3000, 99999), 0),
    "whoosh_std":  ("whoosh",  (1500, 99999), 0),
    "deep_whoosh": ("whoosh",  (0, 3000),     0),
    "swipe":       ("swipe",   (2000, 99999), 0),
    "swipe_metal": ("swipe",   (4000, 99999), +3),
    "click":       ("click",   (2000, 99999), -2),
    "click2":      ("click",   (2000, 99999), -1),
    "type_tick":   ("click",   (4000, 99999), -3),
    "type_key":    ("click",   (2000, 99999), 0),
    "pop":         ("pop",     (1000, 99999), -2),
    "snap":        ("latch",   (3000, 99999), -2),
    "latch":       ("latch",   (0, 99999),     0),
    "impact":      ("impact",  (0, 99999),     0),
    "deep_hit":    ("impact",  (0, 2000),      0),
    "subdrop":     ("sub",     (0, 1500),      0),
    "riser":       ("riser",   (0, 99999),    -3),
    "riser_soft":  ("riser",   (1000, 99999), -3),
    "riser_air":   ("riser",   (4000, 99999), -3),
    "shimmer":     ("shimmer", (4000, 99999), -1),
    "glitch":      ("glitch",  (1000, 99999), -2),
    "radio":       ("glitch",  (0, 99999),    -2),
    "shutter":     ("shutter", (0, 99999),    -2),
    # ⚠️ `bed` ကို **နိမ့်နိမ့်** ရောရမည် (-၆ dB) — စကားအောက်မှာ ရှိရမည်
    "bed":         ("bed",     (0, 99999),    -6),
}
# ⚠️ ZJL အတွက် **နိမ့်ဘန်း ကန့်သတ်** — reference (Bhone) ကို တိုင်းရာ
#    graphic ဝင်ချိန်တွင် နိမ့်ဘန်း ၂၃ dB **ကျ**သည် (တက်တာ မဟုတ်)。
#    ဖုန်း စပီကာမှာ ၅၀၀Hz အောက် မကြားရသဖြင့် sub သက်သက်က ဘာမှ မဖြစ်。
ZJL_MIN_BRIGHT = 900
# ⚠️ **အနည်းဆုံး ကြာချိန်** — ဘောင် အပေါ်သာ ထားလျှင် `deep_whoosh` တောင်းရာ
#    ၈၀ ms ဖိုင် ရသည် (တကယ် ဖြစ်ခဲ့ · cine_2026/whoosh_fast_03)。 role ရဲ့
#    **အလုပ်**က အနည်းဆုံးကို ဆုံးဖြတ်သည် — ဂရပ်ဖစ် ဝင်ချိန် ၀.၄၆၇ s ကို
#    ဖုံးရမည်ဆိုလျှင် ၈၀ ms whoosh က ဘာမှ မဖုံး。
DUR_MIN = {"whoosh_in": 0.25, "whoosh_out": 0.25, "whoosh_std": 0.30,
           "deep_whoosh": 0.50, "riser": 0.80, "riser_soft": 0.80,
           "riser_air": 0.80, "shimmer": 0.40, "subdrop": 0.50,
           "deep_hit": 0.30, "swipe": 0.15, "swipe_metal": 0.15}
# ⚠️ **peak နဲ့ normalise လုပ်လျှင် အား မညှိ**。 variant ၅ ခုကို mix ထဲ ထည််
#    တိုင်းကြည့်ရာ ၁၂ dB ကွာခဲ့သည် (-၃၅ … -၄၇ dB RMS · ၂၀၂၆-၀၉-၂၁)。
#    အကြောင်းက transient တစ်ချက်က peak တူပေမယ့် အား နည်းခြင်း。
#    ⇒ **အကျယ်ဆုံး ၃၀၀ ms ရဲ RMS (`loud_db`)** ကို ပစ်မှတ် ထားသည်。
#    ⚠️ peak ကိုလည်း အမိုးခံရမည် — မရှိလျှင် latch (-၂၆ dB) ကို အားတင်ရာ
#    peak ၀ dBFS ကျော်ပြီး ပဲက်မည် ⇒ နှစ်ခုထဲ နိမ့်တာကို ယူသည်。
# ⚠️ ပစ်မှတ်ကို **role တစ်ခုတည်းမှ မထားရ**。 click က whoosh လောက် ကျယ်ရန်
#    မလို — အတင်တူစေလျှင် peak မှာ နေရာ မလုံလောက်ပြီး transient ပျက်သည်。
#    **variant ချင်း တူရမည်** ဆိုတာက အရေးကြီးတာ ⇒ role တစ်ခုခြင်းရဲ
#    **ကိုယ်ပိုင် အလယ်တန်း** (catalog ကနေ တိုင်း) ကို ပစ်မှတ် ထားသည်。
_TGT = {}


def target(fam, ship=True):
    """role မိသားစုရဲ **အလယ်တန်း loud_db** — ထိုသို့ နှိုင်းသည်"""
    k = (fam, bool(ship))
    if k not in _TGT:
        # ⚠️ `bed` က catalog `role` မဟုတ်သဖြင့် `role == fam` က **ဗလာ**
        #    ဖြစ်ပြီး ပစ်မှတ်က `LOUD_DB` (-၁၆) ကို ပြန်ဆုတ်မည် — bed တွေက
        #    နိမ့်ဘန်း အသံဖြစ်၍ တိုင်းချက်နဲ့ မတူပါ ⇒ pool ကနေ တွက်သည်。
        if fam == "bed":
            v = sorted(x["loud_db"] for x in pool("bed", ship=ship)
                       if x.get("loud_db") is not None)
        else:
            v = sorted(x["loud_db"] for x in (catalog().get("items") or [])
                       if x.get("role") == fam and x.get("loud_db") is not None
                       and (not ship or x.get("ship")))
        _TGT[k] = v[len(v) // 2] if v else LOUD_DB
    return _TGT[k]


LOUD_DB = -16.0         # ပစ်မှတ် အရီးခံ (role မသိလျှင်သာ)
PEAK_CEIL = -3.0        # peak အမြင့်ဆုံး
NORM_DB = -6.0          # (အရိုး · loud_db မရှိသော catalog v1 အတွက်)


LOUD_TOL = 4.0          # ပစ်မှတ်အောက် ခွင့်ပြုသော dB
# WARN **Zin FAV cue: tolerance is wider** (2026-09-25). All three of his
#    clicks were dropped by `role_pool()` -- `CLICK-004` is still 5.6 dB
#    below the family target and its peak is -0.7 (ceiling -3.0), so it
#    cannot be lifted any further. That is normal for a high-transient,
#    low-average file. => allow up to 8.0 dB for a cue he asked for by
#    name (`CLICK-004` -5.6, `CLICK-012` -7.1 both pass).
#    WARN **no QC gate is relaxed** -- the per-cue audibility check
#    (`stem`) still runs and fails the render if a cue is inaudible.
#    `LOUD_TOL` is a pool filter, not QC. Applies only to ids in
#    `assets/sfx_fav.txt`; everything else keeps 4.0.
LOUD_TOL_FAV = 8.0


def _reach(x, tg):
    """ဖိုင်တစ်ခု ပစ်မှတ်အထိ မှ ဘယ်လောက် တင်နိုင်လဲ (dB · ၀ = ပြည့်)"""
    ld, pk = x.get("loud_db"), x.get("peak_db")
    if ld is None or pk is None:
        return 0.0
    return min(0.0, (float(ld) + min(tg - float(ld), PEAK_CEIL - float(pk))) - tg)


def role_pool(role, th="zae", ship=True):
    """sfxlib role အမည် → `[item]`"""
    fam, br, _g = MAP.get(role, (role, None, 0))
    if th == "zjl" and br:
        br = (max(br[0], ZJL_MIN_BRIGHT), br[1])
    lo = DUR_MIN.get(role, 0.0)
    # ⚠️ **အား မတက်နိုင်သော ဖိုင်ကို ပဲ ထုတ်ရမည်**。 peak ထပ်ပြီး
    #    loud နွဲးနေသော ဖိုင် (transient ထြား) ကို ပစ်မှတ်အထိ မတင်နိုင် —
    #    ထိုဖိုင်ကို ထည့်လျှင် variant တစ်ခုပဲ တိတ်နေပြီး အား မတော် မတျ (click
    #    မှာ ၁၁.၂ dB ကွာခဲ့ · ၂၀၂၆-၀၉-၂၁)。 ⇒ ပစ်မှတ်ကို မီး မကိုင်လျှင် ဖျက်သည်。
    tg = target(fam, ship)
    _fv = fav()
    
    def _loud_ok(x):
        _t = LOUD_TOL_FAV if x.get("id") in _fv else LOUD_TOL
        return _reach(x, tg) >= -_t
    
    # ⚠️ **ဖိုင်အရှည်နဲ့ မစစ်ရ** (၂၀၂၆-၀၉-၂၅)。 `wav()` က `render_dur()`
    #    အထိ ဖြတ်သဖြင့် ဖိုင် ၀.၅s ရှိပါလျက် ထွက်တာ ၀.၂၆s ဖြစ်နိုင်သည် ⇒
    #    `whoosh_std` ရဲ့ အနိမ့်ဆုံး ၀.၃၀s (ဂရပ်ဖစ် ဝင်ချိန် ဖုံးရန်) မပြည့်ဘဲ
    #    ခံခဲ့သည် (`mixkit_free/SWOOSH-024` = ၀.၂၈s)。
    ps = [x for x in pool(fam, bright=br, ship=ship)
          if render_dur(x, fam) >= lo and _loud_ok(x)]
    # ⚠️ ဘောင် တင်းလွန်း၍ ဗလာ ဖြစ်လျှင် **အလင်း ဘောင်ကို အရင် လျှော့**သည် —
    #    အသံ မပါတာက variant မကွဲတာ ထက် ဆိုးသည်。 ကြာချိန် အနည်းဆုံးက
    #    အဓိပ္ပာယ် ရှိသဖြင့် **နောက်ဆုံးမှ** လျှော့သည်。
    if not ps:
        ps = [x for x in pool(fam, ship=ship)
              if render_dur(x, fam) >= lo and _loud_ok(x)]
    if not ps:
        ps = [x for x in pool(fam, ship=ship) if render_dur(x, fam) >= lo]
    if not ps:
        ps = pool(fam, bright=br, ship=ship) or pool(fam, ship=ship)
    return ps


def wav(role, seed, idx=0, used=(), th="zae", ship=True, log=None):
    """role → **normalise ပြီးသော** wav လမ်းကြောင်း · variant ကွဲသည်

    `(path, item)` ပြန်ပေးသည် · pool ဗလာဆိုလျှင် `(None, None)`

    ⚠️ peak ကို `catalog` ကနေ **တိုင်းပြီးသား** ယူသည် ⇒ ffmpeg
       `volumedetect` pass မလို (ဖိုင် ၇၄၁ ခုအတွက် subprocess ၇၄၁ ခါ ကင်း)。
    ⚠️ cache နာမည်ထဲ **item id ပါရမည်** — မပါလျှင် variant ကွဲပါလျက်
       ဖိုင်တစ်ခုတည်းကို ထပ်ရေးပြီး အားလုံး တူသွားမည်。
    """
    import subprocess
    fam, br, g = MAP.get(role, (role, None, 0))
    ps = role_pool(role, th, ship)
    if not ps:
        return None, None
    recent = {x for x in list(used)[-NOREPEAT:]}
    h = hashlib.sha1(f"{seed}|{role}|{idx}".encode()).digest()
    _n = int.from_bytes(h[:4], "big")
    free = prefer_fav([x for x in ps if x["id"] not in recent] or ps, _n, idx)
    it = free[_n % len(free)]
    src = path(it)
    if not src or not os.path.exists(src):
        return None, None
    out = _cue_dir()
    os.makedirs(out, exist_ok=True)
    tag = it["id"].replace("/", "_")
    p = os.path.join(out, f"{th}_{role}_{tag}.wav")
    if os.path.exists(p) and os.path.getmtime(p) >= os.path.getmtime(src):
        return p, it
    # ⚠️ ဖြတ်ရာမှာလည် **ကြားရသော အရှည်** ကို သုံးသည် — ဖိုင်အရှည် သုံးလျှင်
    #    တိတ်သော အမြီးကို ထည့်ပြီး cue က နောက်ကျသလို ခံစားရသည်。
    lim = DUR_MAX.get(fam, 2.0)
    d = render_dur(it, fam)
    fo = min(0.06, d * 0.4)
    # ⚠️ **အား နဲ့ peak နှစ်ခုလုံး စစ်ရမည်** — နှစ်ခုထဲ နိမ့်တာ。
    _ld = it.get("loud_db")
    _pk = float(it.get("peak_db") or NORM_DB)
    if _ld is None:
        trim = NORM_DB - _pk
    else:
        trim = min(target(fam, ship) - float(_ld), PEAK_CEIL - _pk)
    trim = max(-24.0, min(24.0, trim))
    af = (f"volume={trim + g:.2f}dB,afade=t=in:st=0:d=0.004,"
          f"afade=t=out:st={max(0, d - fo):.3f}:d={fo:.3f},"
          f"alimiter=limit=0.92,"
          f"aformat=sample_rates=48000:channel_layouts=stereo")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", f"{d:.3f}",
                        "-i", src, "-af", af, p], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(p):
        log and log(f"  ⚠️ SFX {role} ဖြတ်မရ: {(r.stderr or '')[:90]}")
        return None, None
    return p, it


# ⚠️ **cue အချိန်က 「အသံ ကျယ်သည့် အချိန်」 ဖြစ်ရမည်** — ဖိုင် အစ မဟုတ်。
#    riser က ဖိုင်ရဲ့ ၅၀% (p90 ၈၇%) မှာ ကျယ်သည် ⇒ cue အစား ထည့်လျှင်
#    ဂရပ်ဖစ် လာချိန်က ၁.၇s နောက်ကျမှ အသံ ရောက်သည် (တကယ် တိုင်းတွေ့)。
#    ⇒ `peak_t` စောပြီး ထည့်သည် ⇒ အသံ ကျယ်ချိန်က ဖြစ်ရပ်နဲ့ ကိုက်။
#    ⚠️ transient (impact ၇% · shutter ၄%) မှာ ဤတန်ဖိုး သုညနီးပါး ⇒ ဘာမှ
#       မပြောင်း。 riser/latch/swipe မှာသာ အဓိပ္ပာယ် ရှိသည်。
# ⚠️ ကန့်သတ်ကို ၁.၂s ထားခဲ့ရာ riser (peak_t ၁.၄၈s) က ၀.၁၆s လွဲခဲ့သည်。
#    riser ဆိုတာက ဖြစ်ရပ်ဆီ တက်ᄁက်ပြီး **ဝင်ရောက်**တာ — စောတာက သဘာဝတိ。
#    `peak_t` က ဖိုင်အရှည်ကို မကျော်နိုင်သဖြင့် role အလိုက် ကန့်သတ်ပြီးသား
#    (DUR_MAX) ⇒ ဒီကိန်းက အမြင့်ဆုံး riser အရှည်ပဲ。
LEAD_MAX = 3.20


def render_dur(it, fam):
    """cue က **တကယ် ထွက်မည့် အရှည်** s — `wav()` ဖြတ်သည့် အတိုင်း

    ⚠️ `dur` (ဖိုင်အရှည်) နဲ့ မတူ。 test နဲ့ QC က ဒီကိန်းကို ကြည့်ရမည် —
       ဖိုင်အရှည်ကို ကြည့်လျှင် reverb အမြီး ရှည်သော cue ကို
       「ဂိတ်ကျော်」ဟု မှားစွပ်စွဲမည်。 `wav()` နဲ့ **တစ်ထပ်တည်း** ရှိရမည်
       ⇒ ၂ နေရာမှာ တွက်ချက် မရေးဘဲ ဒီ helper ကိုသာ သုံးသည်。
    """
    lim = DUR_MAX.get(fam, 2.0)
    d = min(float(it.get("dur_eff") or it.get("dur") or 0.5), lim)
    pt = it.get("peak_t")
    if pt is not None:
        d = max(d, min(float(pt) + 0.10, lim))
    return d


def lead(it, fam=None):
    """variant တစ်ခုအတွက် **စောသင့်သော အချိန်** s — cue က landing ဖြစ်ရန်

    ⚠️ **`bed` ကို စောပြီး မထည့်ရ** (၂၀၂၆-၀၉-၂၅)。 bed တွေက ၄ စက္ကန့်
       ရှည်ပြီး အသံ ကျယ်ချိန်က ၃.၇s လောက်မှာ ရှိသည် ⇒ အဲဒီအတိုင်း စောလျှင်
       ဖွင့်ချက် (t≈၀.၅s) မှာ **ဗီဒီယို အစမတိုင်ခင်** ရောက်မည်。
       bed ရဲ့ အလုပ်က ဖြစ်ရပ်ပေါ် ကွက်တိ ကျခြင်း မဟုတ် — ခံပေးခြင်း ဖြစ်သည်。
    """
    if not it or fam == "bed":
        return 0.0
    pt = it.get("peak_t")
    if pt is None:
        return 0.0
    return max(0.0, min(LEAD_MAX, float(pt)))


def cue(role, seed, idx=0, used=(), th="zae", ship=True, log=None):
    """`(path, lead, item)` — mix ဆင့်အတွက် တစ်ခုတည်း ခေါ်ရန်"""
    p, it = wav(role, seed, idx, used, th=th, ship=ship, log=log)
    return p, lead(it, MAP.get(role, (role, None, 0))[0]), it
