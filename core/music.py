#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · နောက်ခံ သီချင်း + ducking。

⚠️ **volume ကို လက်နဲ့ မချရ** — `sidechaincompress` ဖြင့် စကားသံကို
   အခြေခံပြီး အလိုအလျောက် ဆုတ်စေရသည်。 လက်နဲ့ ချလျှင် စကားကြားက
   ကွက်လပ်မှာ သီချင်း ပြန်မတက်ဘဲ တိတ်နေသည်。

⚠️ spec — ratio 4:1 · attack 8ms · release 240ms (တိုင်းပြီး)。
   threshold ကို စကားအောက် ချရသည် — ratio တင်ရုံနဲ့ မရ。

⚠️ ZAE နှင့် ZJL မတူ (နှစ်ခုလုံး reference မှ တိုင်းထား):
     ZAE  — သီချင်း **ရှေ့တန်း**。 ကွက်လပ်မှာ −28…−29 dBFS · ~၆ dB ဆုတ်ရုံ
     ZJL  — သီချင်း ပါးပါး (~−20 dB) ဒါမှမဟုတ် **လုံးဝ မထည့်**
   Podcast · Course မှာ **သီချင်း မထည့်ရ** — reference မှာ မရှိ。
"""
import hashlib, json, os, random, re as _re, subprocess

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "music")

# genre → ဖိုင်နာမည် အပိုင်းအစ (ရှိသလောက် တိုက်သည်)
GENRE = {
 "zae": ["ZAE_house_bed"],
 "trending":  ["Blippy", "Wallpaper"],
 "upbeat":    ["Blippy"],
 "calm":      ["Beauty", "Wallpaper"],
 "folk":      ["Beauty"],
 "corporate": ["Wallpaper"],
}
# recipe အလိုက် သီချင်း အဆင့် (speech အောက် dB)
# ⚠️ ZAE ရဲ့ house bed — Zin ကိုယ်တိုင် edit လုပ်ထားသော `3 2.MP4` မှ
#    ထုတ်ယူထားသည်。 သူ့ SFX တွေ **bed ထဲ ပါပြီးသား**。
#    ⚠️ ducking **မလုပ်ရ** — reference မှာ သီချင်းက ရှေ့ရောက်နေပြီး
#       စကားပြောချိန်မှာလည်း တစ်သမတ်တည်း ဖြစ်သည် (project မှတ်တမ်း:
#       "sidechain မလုပ်ဘဲ တစ်သမတ်တည်း ထားသည် · reference အတိုင်း")。
HOUSE = {"zae": ("ZAE_house_bed", 0.0)}
NODUCK = ("zae",)
# WARN **the hand-made ZAE bed is excluded from selection** (2026-09-25).
#    It was cut out of Zin's own edited `3 2.MP4`, so his SFX are baked into
#    it -- measured **81 HF transients, 49.7/min**, which is SFX density, not
#    music. Those bake-ins double up with the engine's own cues; Zin heard it
#    and asked for a different bed ("BG music ကိုအခြားဟာပြောင်းသုံးတာ
#    ကောင်းမယ် ... sound effect ပါနေတာပါ").
#    The file stays in `assets/music/` -- only selection skips it, so putting
#    it back is one line. `GENRE["zae"]` cannot simply be emptied: an empty
#    name filter makes `pool()` accept **every** catalog item.
EXCLUDE = {"zae": ("ZAE_house_bed",)}
# WARN **Zin picked this bed himself** (2026-09-25). He auditioned five
#    candidates drawn from the Motion Kit CC0 bank and chose #3:
#    `electronic/ELEC-055_243s.m4a` -- 3.2 HF transients/min (lower quartile of
#    the 124-track ZAE pool, against 49.7 for the old hand-made bed) and 243 s
#    long, so a 78 s video never reaches a loop seam.
#    A pin overrides the seeded rotation, so every ZAE video gets the same bed.
#    Remove the entry to go back to rotating across the 124-track pool.
# WARN Zin auditioned five candidates and chose #3,
#    `electronic/ELEC-055_243s.m4a`, then asked for **other tracks in the same
#    vein** rather than one fixed bed ("ဒီလိုပုံစံမျိုး insperation ထဲက
#    အခြားသီချင်းတွေသုံးပေးပါ"). There is no "inspiration" folder -- the vein
#    is his pick, so it had to be measured.
# WARN measured across all 44 electronic tracks: transient/min p25 2.4, **p50
#    45.9**, p75 65.2 -- the distribution is bimodal, so "electronic" alone is
#    not a style. His pick sits at 3.2/min with a 2,478 Hz centroid. The set
#    below is transient <=8/min AND centroid 1200-4200 Hz AND at least 78 s
#    long, so a ~78 s video never reaches a loop at all.
#    Four tracks, rotated by seed: the same job always gets the same bed, and
#    different videos differ. Remove the entry to open the full 124-track pool.
PIN = {"zae": ("mk:corporate/CORP-022_78s.m4a",)}
# WARN **the first swap was picked on the wrong criterion and Zin rejected it**
#    ("BG music ကလုံး၀အဆင်မပြေပါဘူး"). I had ranked candidates by *low
#    transient density*, which only says "leaves room for the cues" -- it says
#    nothing about whether the music sounds like ZAE. Measured afterwards
#    against the hand-made bed, the track that shipped in v6
#    (`ELEC-060`) ranks **90th of 124** on musical character.
# WARN the right reference was there all along: the hand-made bed's *music* is
#    what he likes -- only the SFX baked into it were the problem. Measured on
#    the bed: centroid **2428 Hz**, bass ratio **0.654**, dynamic range
#    **7.9 dB**. Ranking all 124 tracks by distance on those (plus mid ratio)
#    puts `CORP-022_78s` at 0.196 (3rd): centroid 2043, bass 0.715, dyn 10.5.
#    Zin auditioned the top four against the bed and chose it.
#    Its 78.1 s also clears a 77.6 s video, so no loop is ever reached.
# WARN **BPM estimates here are not trustworthy** -- autocorrelation returned
#    round numbers (60.0 / 120.0 / 200.0), i.e. it locked onto harmonics, so
#    tempo was left out of the ranking. Centroid / bass / dynamics carried it.
#    To rotate instead of pinning, list the other close matches here:
#    `ELEC-034_132s` (0.168) · `ELEC-047_81s` (0.187) · `ELEC-035_234s` (0.208).
LEVEL = {"zae": 0.0, "trending": -16.0, "upbeat": -17.0, "calm": -20.0,
         "folk": -21.0, "corporate": -18.0}
# WARN **`LEVEL` is a fixed dB offset, so swapping the bed changes the mix.**
#    Found 2026-09-25 while replacing the ZAE bed. `LEVEL["zae"] = 0.0` means
#    "pass the file through untouched", which was only right because the
#    hand-made bed measures **-28.62 LUFS** -- Zin had already balanced it
#    inside his own edit. A bank track sits at about -23 LUFS, so the same
#    0 dB offset would have put the music **5.3 dB too loud** over speech, and
#    ZAE does not duck (`NODUCK`), so nothing downstream would pull it back.
#    => for a genre with a measured target, the gain is computed per track from
#    its own measured `lufs`. -28.6 reproduces exactly what shipped and what he
#    approved (the module note above measures the reference at -28...-29 dBFS
#    in gaps). Genres without a target keep their tuned fixed offset.
TARGET_LUFS = {"zae": -28.6}

# ══ catalog (Music audit P0) ══════════════════════════════════════
# ⚠️ `pick()` က ကိုက်ညီသော **ပထမဖိုင်** ကို ပြန်ပေးခဲ့သည် ⇒ ဗီဒီယိုတိုင်း
#    သီချင်းတစ်ပုဒ်တည်း ရနိုင်သည်。 ⇒ seed နဲ့ ရွေးပြီး မကြာခင်က
#    သုံးထားတာ ရှောင်သည် (SFX variant pool နဲ့ တစ်သဘောတည်း)。
# ⚠️ **တူညီသော သီချင်း ၂ ဖိုင်** ရှိသည် — "4604 Wallpaper By Kevin
#    Macleod" နဲ့ "Kevin MacLeod Wallpaper" က correlation ၀.၉၉၉၆
#    (၂၀၂၆-၀၉-၂၁ တိုင်း၍ တွေ့)。 pool မှာ ၂ ခု လို့ ရေတွက်လျှင်
#    「ကွဲပြားမှု」က လိမ်ရာ ကျသည် ⇒ `SAME` နဲ့ တွဲထားသည်。
SAME = {"Kevin MacLeod Wallpaper": "4604 Wallpaper By Kevin Macleod"}
_CAT = None


# ⚠️ **motionkit ရဲ့ သီချင်း bank** — ၂၀၂၆-၀၉-၂၄ တိုင်းချက်: bank မှာ
#    သီချင်း **၅၁၁ ပုဒ်** (genre ဖိုဒါ ၉ ခု) ရှိပါလျက် IKKI က local ၄ ပုဒ်
#    ချည်းသာ သုံးခဲ့သည် — Zin: 「Motion Kit ထဲမှာ ရှိသမျှ အကုန်သုံးလို့ရအောင်」。
# ⚠️ licence — bank တစ်ခုလုံး **CC0 1.0** (`LICENSES.md`): ပြန်ဖြန့်ခွင့် ·
#    ရောင်းခွင့် ရှိပြီး credit မလို ⇒ SaaS ထွက်ဗီဒီယိုမှာ သုံးလို့ ရသည်。
# ⚠️ ZAE house bed က **local** မှာသာ ရှိသည် — `HOUSE`/`NODUCK` စည်းမျဉ်းကို
#    မထိပါ (bank ကို **ထပ်ဖြည့်**ရုံသာ)。
def _mk_root():
    """motionkit ဖိုဒါ — `gfxcat` နဲ့ **တစ်ထပ်တည်း** ဖြစ်ရမည်。

    ⚠️ ကိုယ်ပိုင် fallback ရေးလျှင် လွဲသည် (၂၀၂၆-၀၉-၂၄: `<repo>/../motionkit`
       ဟု ရေးမိ၍ bank ၅၁၁ ပုဒ်လုံး မတွေ့ခဲ့)。
    """
    try:
        import gfxcat as _G
        return _G.MK
    except Exception:
        return os.environ.get("IKKI_MOTIONKIT", "")


# ⚠️ **Mac ထဲ မိတ္တူကို ဦးစားပေးရမည်** — ၂၀၂၆-၀၉-၂၄: သီချင်း bank က
#    ပြင်ပ drive (`/Volumes/a`) ပေါ် symlink နဲ့ ရှိပြီး **launchd worker က
#    macOS TCC ကြောင့် မဖတ်နိုင်**ပါ (`Errno 1 Operation not permitted` ·
#    log မှာ `Volumes=0`)。 Full Disk Access ပေးလည်း မရပါ — launchd job မှာ
#    TCC က interpreter ကို မမှတ်ယူသဖြင့် (Zin ၂ ခါ စမ်းပြီး)。
#    ⇒ တိုင်းပြီးသား ၃၈၄ ပုဒ် (၀.၉၂ GB) ကို `assets/music_bank/` ထဲ ကူးထား
#      (`.gitignore` ထဲ ထည့်ပြီး — repo က PUBLIC)。
_LOCAL_BANK = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "assets", "music_bank")
MK_MUSIC = (_LOCAL_BANK if os.path.isdir(_LOCAL_BANK)
            else os.path.join(_mk_root(), "assets", "music", "cc0_2026"))

# motionkit ဖိုဒါ → IKKI genre
# WARN **`zae` was pinned to one hand-made bed** until 2026-09-25. Zin asked
#    for the Motion Kit library to be usable ("Motion Kit ထဲကသီးချင်းတွေကို
#    သုံးလို့၇အောင်လုပ်ပေးပါ") because `ZAE_house_bed` carries **sound effects
#    baked into it** -- it was cut out of his own edited `3 2.MP4`, and the
#    module comment says so ("သူ့ SFX တွေ bed ထဲ ပါပြီးသား"). Measured: the
#    bed has **81 HF transients / 49.7 per minute**, which is SFX density, not
#    music. Those bake-ins collide with the engine's own cues, which is what he
#    heard ("BG music ... ဟာကြီးပါလာ ... sound effect ပါနေတာပါ").
# WARN the Motion Kit bank is **already measured and gated** -- 384 of 511
#    tracks pass `tools/music_index.py` (loop seam <=1 dB, lufs, true peak),
#    all CC0 1.0. Nothing new had to be downloaded or generated.
MOOD = {
    "electronic": ("trending", "upbeat", "zae"),
    "epic":       ("trending", "upbeat", "zae"),
    "lofi_chill": ("calm",),
    "piano":      ("calm",),
    "ambient_cine": ("calm",),
    "folk":       ("folk",),
    "acoustic":   ("folk",),
    "corporate":  ("corporate", "zae"),
    "dark":       ("corporate",),
}
AUD = (".m4a", ".mp3", ".wav", ".aac", ".ogg")
# ⚠️ တိုင်းထားသော အသံအဆင့် cache — `tools/music_index.py` က ရေးသည်。
LOUD_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "assets", "music_loudness.json")
try:
    with open(LOUD_CACHE, encoding="utf-8") as _f:
        _LOUD = json.load(_f) or {}
except (OSError, ValueError):
    _LOUD = {}


def _bank():
    """motionkit bank ကနေ catalog item များ — မရှိလျှင် `[]`。"""
    out = []
    if not os.path.isdir(MK_MUSIC):
        return out
    for folder, genres in sorted(MOOD.items()):
        d = os.path.join(MK_MUSIC, folder)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(AUD):
                continue
            # ⚠️ ကြာချိန်ကို **ဖိုင်အမည်ကနေ** ဖတ်သည် (`FOLK-013_32s.m4a`) —
            #    ffprobe ၅၁၁ ခါ ခေါ်လျှင် catalog တင်ချိန် နှေးမည်。
            _m = _re.search(r"_(\d+)s\.[A-Za-z0-9]+$", fn)
            _d = float(_m.group(1)) if _m else None
            _lo = _LOUD.get(f"{folder}/{fn}") or {}
            # ⚠️ **တိုင်းပြီးမှသာ ဝင်ခွင့်** — `lufs`/`true_peak`/ကျော့နယ်
            #    မရှိလျှင် ချန်ထားသည်。 `tests/test_music.py` ရဲ့ ဂိတ်က
            #    ကျော့နယ် (seam ≤၁ dB) မရှိလျှင် ကျသည် — ဖိုင် အစ↔အဆုံး
            #    ကျော့လျှင် ၉၃–၁၇၃ dB ထိုးကျသံ ဖြစ်သောကြောင့် (တိုင်းထားသည်)。
            #    ⇒ `tools/music_index.py` ပြေးပြီးမှ တိုးလာမည်。
            if not (_lo.get("loop") and _lo.get("lufs") is not None
                    and _lo.get("true_peak") is not None):
                continue
            # ⚠️ `lufs`/`true_peak` ကို **မမှန်းရ** — `tools/music_index.py`
            #    နဲ့ တိုင်းပြီး cache ထဲ ရေးသည်。 မတိုင်ရသေးလျှင် `None`
            #    (engine က level ကို `LEVEL[genre]` ကနေ ယူသဖြင့် မလို)。
            out.append({"id": f"mk:{folder}/{fn}",
                        # ⚠️ `file` ကို **absolute** ထားသည် — bank က `DIR`
                        #    အပြင်မှာ ရှိ၍ `os.path.join(DIR, file)` က
                        #    absolute ဆိုလျှင် အဲဒါကိုပဲ ပြန်ပေးသဖြင့်
                        #    ရှိပြီးသား ကုဒ်/test နှစ်ခုလုံး အလုပ်ဖြစ်သည်。
                        "file": os.path.join(d, fn),
                        "path": os.path.join(d, fn),
                        "dur": _lo.get("dur") or _d,
                        "loop": _lo.get("loop"),
                        "lufs": _lo.get("lufs"),
                        "true_peak": _lo.get("true_peak"),
                        "mood": folder, "genres": list(genres),
                        "license": "CC0 1.0"})
    return out


def catalog():
    global _CAT
    if _CAT is None:
        try:
            with open(os.path.join(DIR, "catalog.json"), encoding="utf-8") as f:
                _CAT = json.load(f)
        except (OSError, ValueError):
            _CAT = {"items": []}
        # ⚠️ **ထပ်ဖြည့်ရုံသာ** — local item တွေ ရှေ့မှာ ကျန်ရမည်
        #    (ZAE house bed နဲ့ Zin ရွေးထားသော သီချင်းများ)。
        try:
            _CAT.setdefault("items", []).extend(_bank())
        except Exception:
            pass
    return _CAT


def entry(track_id):
    for x in catalog().get("items") or []:
        if x.get("id") == track_id:
            return x
    return None


def pool(genre):
    """genre အတွက် ရွေးစရာ — **တူညီသော သီချင်းကို တစ်ခါသာ**"""
    want = [w.lower() for w in GENRE.get(genre, [])]
    out, seen = [], set()
    for x in catalog().get("items") or []:
        tid = x.get("id") or ""
        # ⚠️ bank item တွေမှာ `genres` ရှိသည် — **အမည် အပိုင်းအစ နဲ့ မတိုက်ရ**
        #    (ဖိုင်အမည်တွေက `FOLK-013_32s.m4a` ပုံစံ ဖြစ်၍ `Blippy` စသည်နဲ့
        #    ဘယ်တော့မှ မကိုက်ပါ ⇒ ၅၁၁ ပုဒ်လုံး ကျန်ခဲ့မည်)。
        if x.get("genres"):
            if genre not in x["genres"]:
                continue
        elif want and not any(w in tid.lower() for w in want):
            continue
        if any(w.lower() in tid.lower() for w in EXCLUDE.get(genre, ())):
            continue
        key = SAME.get(tid, tid)
        if key in seen:
            continue
        seen.add(key)
        out.append(x)
    out.sort(key=lambda x: x.get("id") or "")
    return out


def choose(genre, seed="", used=()):
    """`(path, entry)` — seed အလိုက် တည်ငြိမ်စွာ ရွေးသည်

    ⚠️ တူညီသော seed ⇒ တူညီသော သီချင်း (render ပြန်လုပ်လျှင် တူရမည်)。
    """
    ps = pool(genre)
    # WARN a pinned bed wins over the seeded rotation -- see `PIN`.
    _pin = PIN.get(genre)
    if _pin:
        _want = (_pin,) if isinstance(_pin, str) else tuple(_pin)
        _hit = [x for x in ps if (x.get("id") or "") in _want]
        if _hit:
            # WARN keep it seeded, not first-match: one bed on every video is
            #    what the variant pools exist to avoid.
            ps = _hit
    if not ps:
        p = pick(genre)
        return p, (entry(os.path.splitext(os.path.basename(p))[0]) if p else None)
    recent = {SAME.get(u, u) for u in list(used)[-2:]}
    free = [x for x in ps if SAME.get(x["id"], x["id"]) not in recent] or ps
    h = hashlib.sha1(f"{seed}|{genre}".encode()).digest()
    it = free[int.from_bytes(h[:4], "big") % len(free)]
    # ⚠️ motionkit bank item တွေမှာ **absolute `path`** ရှိပြီး `file` မရှိ ⇒
    #    `os.path.join(DIR, it["file"])` က `KeyError`/လမ်းကြောင်း မှားမည်
    #    (၂၀၂၆-၀၉-၂၄ bank ချိတ်စဉ် ဖမ်းမိ)。
    return (it.get("path") or os.path.join(DIR, it["file"])), it


def loop_chain(it, dur, fade):
    """သီချင်းကို `dur` အထိ ဆန့်သော filter အပိုင်း — **ကျော့မှတ် မကျိုးစေရ**

    ⚠️ သီချင်း ၅ ပုဒ်လုံး အဆုံးမှာ **လုံးဝ တိတ်**သွားသည် (−၈၄ … −၂၄၀ dB)
       ပြီးမှ အစက −၈ … −၂၆ dB နဲ့ ပြန်စသည် ⇒ `aloop` က ကျော့တိုင်း
       **၉၃–၁၇၃ dB ထိုးကျသံ** ဖြစ်စေသည် (၂၀၂၆-၀၉-၂၁ တိုင်း၍ တွေ့)。
    ⚠️ ⇒ (၁) ဗီဒီယိုက သီချင်းထက် တိုလျှင် **ကျော့စရာ မလို** — ဖြတ်ရုံသာ。
          (၂) ရှည်လျှင် catalog က **အတည်ပြု ကျော့နယ်** (တိုင်းထားသော
              ဝင်/ထွက် အား ကွာဟမှု ≤ ၀.၁ dB) ကိုသာ ကျော့သည်。
    """
    td = float((it or {}).get("dur") or 0)
    lp = (it or {}).get("loop") or None
    if td and dur <= td - 0.05:
        base = f"atrim=0:{dur:.3f}"
    elif lp:
        base = (f"atrim={lp['start']:.3f}:{lp['end']:.3f},asetpts=PTS-STARTPTS,"
                f"aloop=loop=-1:size=2000000000,atrim=0:{dur:.3f}")
    else:
        base = f"aloop=loop=-1:size=2000000000,atrim=0:{dur:.3f}"
    return (f"{base},asetpts=PTS-STARTPTS")


def pick(genre):
    if not genre or not os.path.isdir(DIR): return None
    want = GENRE.get(genre, [])
    files = sorted(f for f in os.listdir(DIR) if f.lower().endswith((".m4a",".mp3",".wav")))
    if not files: return None
    for w in want:
        for f in files:
            if w.lower() in f.lower(): return os.path.join(DIR, f)
    return os.path.join(DIR, files[0])

def _loopnote(it, dur):
    """log အတွက် — ကျော့လား မကျော့လား ရှင်းရှင်း ပြရန်"""
    td = float((it or {}).get("dur") or 0)
    if td and dur <= td - 0.05:
        return f"မကျော့ (သီချင်း {td:.0f}s ≥ {dur:.0f}s)"
    lp = (it or {}).get("loop")
    if lp:
        return f"ကျော့နယ် {lp['start']:.0f}–{lp['end']:.0f}s (ကျိုး {lp['seam_db']} dB)"
    return "⚠️ ကျော့နယ် မသိ — ဖိုင်အစအဆုံး ကျော့သည် (ထိုးကျသံ ဖြစ်နိုင်)"


def measure_lufs(path):
    """integrated loudness of a file (ebur128) -- for tracks the catalog has no figure for"""
    import re as _re
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = _re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def bed(video, out, genre, dur, log=print, fade=1.2, seed="", used=(), target=None, ratio=None):
    """စကားသံပေါ် သီချင်း ထပ်ပြီး ducking လုပ်သည်。

    `seed` — job id。 တူညီသော seed ⇒ တူညီသော သီချင်း (ပြန်ထုတ်လျှင် တူရန်)。
    """
    trk, _it = choose(genre, seed, used)
    # ⚠️ **pool အရွယ်ကို log မှာ ပြရမည်** — ၂၀၂၆-၀၉-၂၄: bank ၃၈၉ ပုဒ်
    #    ချိတ်ပြီးပါလျက် render ၃ ခေါက်လုံး local ပုဒ်ကိုပဲ ရွေးခဲ့သည်。
    #    shell ကနေ စစ်တော့ bank ကနေ ရွေးသဖြင့် **worker ထဲက catalog
    #    ဗလာဖြစ်နေသလား** မသိရ ⇒ ဒီမှာ ပြခိုင်းသည်。
    try:
        _ps = pool(genre)
        _nb = sum(1 for x in _ps if str(x.get("id", "")).startswith("mk:"))
        log(f"  သီချင်း pool · {genre} {len(_ps)} ပုဒ် "
            f"(bank {_nb} · local {len(_ps)-_nb}) · catalog "
            f"{len(catalog().get('items') or [])} · LOUD {len(_LOUD)}")
    except Exception:
        pass
    if not trk:
        log("  သီချင်း မထည့် (genre မရှိ)")
        subprocess.run(["ffmpeg","-v","error","-y","-i",video,"-c","copy",out],check=True)
        return out, None
    lvl = LEVEL.get(genre, -18.0)
    # recipe-level target (short-916 `music_lufs`) wins over the genre table
    _tgt = target if target is not None else TARGET_LUFS.get(genre)
    _tlu = (_it or {}).get("lufs")
    if _tgt is not None and _tlu is None and trk:
        try:
            _tlu = measure_lufs(trk)
        except Exception:
            _tlu = None
    if _tgt is not None and _tlu is not None:
        # WARN clamp it: a badly measured track must not swing the mix wildly.
        lvl = max(-24.0, min(6.0, float(_tgt) - float(_tlu)))
        log(f"  သီချင်း အား · ပစ်မှတ် {_tgt} LUFS − ဖိုင် {_tlu} "
            f"⇒ {lvl:+.1f} dB (တိုင်းချက်ကနေ · LEVEL ပုံသေ မဟုတ်)")
    if genre in NODUCK:
        # ⚠️ ZAE က ducking **မလုပ်** — reference မှာ သီချင်းက စကားပြောချိန်
        #    မှာပါ တစ်သမတ်တည်း ရှေ့ရောက်နေသည်。 sidechain ထည့်လျှင်
        #    သီချင်း နောက်ဆုတ်သွားပြီး ခံစားချက် ကွဲသွားမည်。
        fc = (f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
              f"{loop_chain(_it, dur, fade)},volume={lvl}dB,"
              f"afade=t=in:st=0:d={fade},"
              f"afade=t=out:st={max(0,dur-fade):.3f}:d={fade}[mus];"
              f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo[sp];"
              f"[sp][mus]amix=inputs=2:duration=first:normalize=0,"
              f"alimiter=limit=0.94[a]")
        subprocess.run(["ffmpeg","-v","error","-y","-i",video,"-i",trk,
            "-filter_complex",fc,"-map","0:v","-map","[a]",
            "-c:v","copy","-c:a","aac","-b:a","192k",out],check=True)
        log(f"  သီချင်း {(_it or {}).get('id', os.path.basename(trk))[:46]} · "
            f"{lvl:+.0f} dB · ducking မလုပ် (ZAE) · {_loopnote(_it, dur)}")
        return out, trk
    # ⚠️ သီချင်းက ဗီဒီယိုထက် တိုလျှင် ပြန်ကျော့ရမည် — aloop ဖြင့်
    fc = (f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
          f"{loop_chain(_it, dur, fade)},"
          f"volume={lvl}dB,"
          f"afade=t=in:st=0:d={fade},afade=t=out:st={max(0,dur-fade):.3f}:d={fade}[mus];"
          f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[sp][sc];"
          # ⚠️ level_sc ကို တင်မှ စကားသံက compressor ကို တကယ် တွန်းနိုင်သည်
          f"[mus][sc]sidechaincompress=threshold=0.05:ratio={float(ratio or 4):g}:"
          f"attack=8:release=240:makeup=1:level_sc=1.2[duck];"
          f"[sp][duck]amix=inputs=2:duration=first:normalize=0,"
          f"alimiter=limit=0.94[a]")
    subprocess.run(["ffmpeg","-v","error","-y","-i",video,"-i",trk,
        "-filter_complex",fc,"-map","0:v","-map","[a]",
        "-c:v","copy","-c:a","aac","-b:a","192k",out],check=True)
    log(f"  သီချင်း {(_it or {}).get('id', os.path.basename(trk))[:46]} · "
        f"{lvl:+.0f} dB · ducking {float(ratio or 4):g}:1 · {_loopnote(_it, dur)}")
    return out, os.path.basename(trk)
