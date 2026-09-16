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
import os, random, subprocess

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

def pick(genre):
    if not genre or not os.path.isdir(DIR): return None
    want = GENRE.get(genre, [])
    files = sorted(f for f in os.listdir(DIR) if f.lower().endswith((".m4a",".mp3",".wav")))
    if not files: return None
    for w in want:
        for f in files:
            if w.lower() in f.lower(): return os.path.join(DIR, f)
    return os.path.join(DIR, files[0])

def bed(video, out, genre, dur, log=print, fade=1.2):
    """စကားသံပေါ် သီချင်း ထပ်ပြီး ducking လုပ်သည်。"""
    trk = pick(genre)
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
              f"aloop=loop=-1:size=2e9,atrim=0:{dur:.3f},volume={lvl}dB,"
              f"afade=t=in:st=0:d={fade},"
              f"afade=t=out:st={max(0,dur-fade):.3f}:d={fade}[mus];"
              f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo[sp];"
              f"[sp][mus]amix=inputs=2:duration=first:normalize=0,"
              f"alimiter=limit=0.94[a]")
        subprocess.run(["ffmpeg","-v","error","-y","-i",video,"-i",trk,
            "-filter_complex",fc,"-map","0:v","-map","[a]",
            "-c:v","copy","-c:a","aac","-b:a","192k",out],check=True)
        log(f"  သီချင်း {os.path.basename(trk)[:28]} · {lvl:+.0f} dB · ducking မလုပ် (ZAE)")
        return out, trk
    # ⚠️ သီချင်းက ဗီဒီယိုထက် တိုလျှင် ပြန်ကျော့ရမည် — aloop ဖြင့်
    fc = (f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,"
          f"aloop=loop=-1:size=2e9,atrim=0:{dur:.3f},"
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
    log(f"  သီချင်း {os.path.basename(trk)[:28]} · {lvl:+.0f} dB · ducking 4:1")
    return out, os.path.basename(trk)
