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
import hashlib, json, os, random, subprocess

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
LEVEL = {"zae": 0.0, "trending": -16.0, "upbeat": -17.0, "calm": -20.0,
         "folk": -21.0, "corporate": -18.0}

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


def catalog():
    global _CAT
    if _CAT is None:
        try:
            with open(os.path.join(DIR, "catalog.json"), encoding="utf-8") as f:
                _CAT = json.load(f)
        except (OSError, ValueError):
            _CAT = {"items": []}
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
        if want and not any(w in tid.lower() for w in want):
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
    if not ps:
        p = pick(genre)
        return p, (entry(os.path.splitext(os.path.basename(p))[0]) if p else None)
    recent = {SAME.get(u, u) for u in list(used)[-2:]}
    free = [x for x in ps if SAME.get(x["id"], x["id"]) not in recent] or ps
    h = hashlib.sha1(f"{seed}|{genre}".encode()).digest()
    it = free[int.from_bytes(h[:4], "big") % len(free)]
    return os.path.join(DIR, it["file"]), it


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


def bed(video, out, genre, dur, log=print, fade=1.2, seed="", used=()):
    """စကားသံပေါ် သီချင်း ထပ်ပြီး ducking လုပ်သည်。

    `seed` — job id。 တူညီသော seed ⇒ တူညီသော သီချင်း (ပြန်ထုတ်လျှင် တူရန်)。
    """
    trk, _it = choose(genre, seed, used)
    if not trk:
        log("  သီချင်း မထည့် (genre မရှိ)")
        subprocess.run(["ffmpeg","-v","error","-y","-i",video,"-c","copy",out],check=True)
        return out, None
    lvl = LEVEL.get(genre, -18.0)
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
        log(f"  သီချင်း {(_it or {}).get('id', os.path.basename(trk))[:28]} · "
            f"{lvl:+.0f} dB · ducking မလုပ် (ZAE) · {_loopnote(_it, dur)}")
        return out, trk
    # ⚠️ သီချင်းက ဗီဒီယိုထက် တိုလျှင် ပြန်ကျော့ရမည် — aloop ဖြင့်
    fc = (f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
          f"{loop_chain(_it, dur, fade)},"
          f"volume={lvl}dB,"
          f"afade=t=in:st=0:d={fade},afade=t=out:st={max(0,dur-fade):.3f}:d={fade}[mus];"
          f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[sp][sc];"
          # ⚠️ level_sc ကို တင်မှ စကားသံက compressor ကို တကယ် တွန်းနိုင်သည်
          f"[mus][sc]sidechaincompress=threshold=0.05:ratio=4:"
          f"attack=8:release=240:makeup=1:level_sc=1.2[duck];"
          f"[sp][duck]amix=inputs=2:duration=first:normalize=0,"
          f"alimiter=limit=0.94[a]")
    subprocess.run(["ffmpeg","-v","error","-y","-i",video,"-i",trk,
        "-filter_complex",fc,"-map","0:v","-map","[a]",
        "-c:v","copy","-c:a","aac","-b:a","192k",out],check=True)
    log(f"  သီချင်း {(_it or {}).get('id', os.path.basename(trk))[:28]} · "
        f"{lvl:+.0f} dB · ducking 4:1 · {_loopnote(_it, dur)}")
    return out, os.path.basename(trk)
