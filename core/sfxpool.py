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
           "riser": 3.20, "sub": 2.00, "air": 4.00}
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
    for x in catalog().get("items") or []:
        if x.get("role") != role:
            continue
        if ship and not x.get("ship", False):
            continue
        if x.get("dur", 9) > lim:
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
    free = [x for x in ps if x["id"] not in recent] or ps
    h = hashlib.sha1(f"{seed}|{role}|{idx}".encode()).digest()
    n = int.from_bytes(h[:4], "big")
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
        v = sorted(x["loud_db"] for x in (catalog().get("items") or [])
                   if x.get("role") == fam and x.get("loud_db") is not None
                   and (not ship or x.get("ship")))
        _TGT[k] = v[len(v) // 2] if v else LOUD_DB
    return _TGT[k]


LOUD_DB = -16.0         # ပစ်မှတ် အရီးခံ (role မသိလျှင်သာ)
PEAK_CEIL = -3.0        # peak အမြင့်ဆုံး
NORM_DB = -6.0          # (အရိုး · loud_db မရှိသော catalog v1 အတွက်)


LOUD_TOL = 4.0          # ပစ်မှတ်အောက် ခွင့်ပြုသော dB


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
    ps = [x for x in pool(fam, bright=br, ship=ship)
          if x.get("dur", 0) >= lo and _reach(x, tg) >= -LOUD_TOL]
    # ⚠️ ဘောင် တင်းလွန်း၍ ဗလာ ဖြစ်လျှင် **အလင်း ဘောင်ကို အရင် လျှော့**သည် —
    #    အသံ မပါတာက variant မကွဲတာ ထက် ဆိုးသည်。 ကြာချိန် အနည်းဆုံးက
    #    အဓိပ္ပာယ် ရှိသဖြင့် **နောက်ဆုံးမှ** လျှော့သည်。
    if not ps:
        ps = [x for x in pool(fam, ship=ship)
              if x.get("dur", 0) >= lo and _reach(x, tg) >= -LOUD_TOL]
    if not ps:
        ps = [x for x in pool(fam, ship=ship) if x.get("dur", 0) >= lo]
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
    free = [x for x in ps if x["id"] not in recent] or ps
    h = hashlib.sha1(f"{seed}|{role}|{idx}".encode()).digest()
    it = free[int.from_bytes(h[:4], "big") % len(free)]
    src = path(it)
    if not src or not os.path.exists(src):
        return None, None
    out = _cue_dir()
    os.makedirs(out, exist_ok=True)
    tag = it["id"].replace("/", "_")
    p = os.path.join(out, f"{th}_{role}_{tag}.wav")
    if os.path.exists(p) and os.path.getmtime(p) >= os.path.getmtime(src):
        return p, it
    d = float(it.get("dur") or 0.5)
    lim = DUR_MAX.get(fam, 2.0)
    d = min(d, lim)
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


def lead(it):
    """variant တစ်ခုအတွက် **စောသင့်သော အချိန်** s — cue က landing ဖြစ်ရန်"""
    if not it:
        return 0.0
    pt = it.get("peak_t")
    if pt is None:
        return 0.0
    return max(0.0, min(LEAD_MAX, float(pt)))


def cue(role, seed, idx=0, used=(), th="zae", ship=True, log=None):
    """`(path, lead, item)` — mix ဆင့်အတွက် တစ်ခုတည်း ခေါ်ရန်"""
    p, it = wav(role, seed, idx, used, th=th, ship=ship, log=log)
    return p, lead(it), it
