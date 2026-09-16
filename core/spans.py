#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · span အလိုက် ဖြတ်ပြီး ပေါင်းခြင်း。

⚠️ filtergraph တစ်ခုတည်းနဲ့ **မလုပ်ရ** — [0:v] ကို trim ၄၄ ခု ခွဲလျှင်
   ffmpeg က 4K frame တွေကို တစ်ပြိုင်တည်း ကိုင်ထားပြီး kernel က သတ်သည်
   (**exit -9 · stderr ဗလာ** — ဘာမှ မဖြစ်သလို မြင်ရသည်)。
   ⇒ span တစ်ခုချင်း သီးသန့် ထုတ်ပြီး concat demuxer နဲ့ ပေါင်းရသည်。
"""
import os, subprocess

FADE = 0.02   # ⚠️ select/concat ချည်းသုံးလျှင် ဆက်တိုင်း "ကလစ်" ဆိုသည်

def spans(src, spans, out, work, fps=30, vcodec="h264_videotoolbox", vb="10M"):
    os.makedirs(work, exist_ok=True)
    parts=[]
    for i,(a,b) in enumerate(spans):
        d=b-a
        if d <= 0.05: continue
        p=os.path.join(work, f"s{i:04d}.mp4")
        subprocess.run(["ffmpeg","-v","error","-y",
            "-ss",f"{a:.3f}","-i",src,"-t",f"{d:.3f}",
            "-af",f"afade=t=in:st=0:d={FADE},afade=t=out:st={max(0,d-FADE):.3f}:d={FADE}",
            "-r",str(fps),"-c:v",vcodec,"-b:v",vb,"-c:a","aac","-b:a","192k",
            "-avoid_negative_ts","make_zero",p], check=True)
        parts.append(p)
    if not parts: raise RuntimeError("span မရှိ")
    lst=os.path.join(work,"parts.txt")
    with open(lst,"w") as f:
        for p in parts: f.write("file '%s'\n" % p.replace("'","'\\''"))
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",lst,
                    "-c","copy",out], check=True)
    for p in parts: os.remove(p)
    os.remove(lst)
    return out

def loudness(inp, out, lufs=-14.0, tp=-1.0, lra=11.0):
    """⚠️ −14 LUFS · −1.0 dBTP — YouTube/TikTok က ဒီအဆင့်ကို မျှော်သည်。

    ⚠️ **နှစ်ကြိမ် တိုင်းရမည်**。 loudnorm ကို တစ်ကြိမ်တည်း သုံးလျှင် ခန့်မှန်းရုံသာ —
       တကယ် တိုင်းကြည့်တော့ ပစ်မှတ် −14.0 အစား **−15.9** ထွက်ခဲ့သည် (1.9 LUFS လွဲ)。
       ပထမအကြိမ် တိုင်း၊ ရလာသော ကိန်းကို ဒုတိယအကြိမ်မှာ ထည့်ပေးမှ တိကျသည်。
    """
    import json as _j, re as _re
    r = subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",inp,
        "-af",f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:print_format=json",
        "-f","null","-"], capture_output=True, text=True)
    m = _re.search(r"\{[^{}]*input_i[^{}]*\}", r.stderr, _re.S)
    af = f"loudnorm=I={lufs}:TP={tp}:LRA={lra}"
    if m:
        try:
            d = _j.loads(m.group(0))
            af = (f"loudnorm=I={lufs}:TP={tp}:LRA={lra}"
                  f":measured_I={d['input_i']}:measured_TP={d['input_tp']}"
                  f":measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}"
                  f":offset={d['target_offset']}:linear=true")
        except Exception:
            pass
    # ⚠️ **+faststart မရှိလျှင် browser မှာ မပေါ်ဘူး**。 moov atom က ဖိုင်အဆုံး
    #    ရောက်နေသဖြင့် player က ဖိုင်တစ်ခုလုံး ဆွဲပြီးမှ ပြနိုင်သည် —
    #    ၇၂.၈ MB ဖိုင်က ၆ Mbps လိုင်းနှင့် ~၁၀၀s အမဲကွက် ဖြစ်ခဲ့သည် (တကယ်)。
    # ⚠️ **loudnorm ရဲ့ TP= တစ်ခုတည်းနဲ့ မလုံလောက်**。 QC မှာ true peak
    #    −0.7 ထွက်ခဲ့သည် (လို −1.0)。 `linear=true` က gain တစ်ခုတည်း တင်သဖြင့်
    #    crest factor မြင့်လျှင် LUFS နဲ့ TP နှစ်ခုလုံး မကိုက်နိုင်、AAC encode
    #    ကလည်း ထပ်ကျော်စေသည်。 ⇒ limiter တစ်ခု နောက်က ထပ်ထားရသည်。
    # ⚠️ `alimiter` က **sample peak** ကိုသာ ကန့်သတ်သည်၊ true peak (inter-sample)
    #    က ~၀.၆ dB ပိုမြင့်သည် — တိုင်းထားသည်:
    #        limit −1.2 dBFS → TP −0.64 ✗ |  −1.8 → −1.10 ✓ (margin ၀.၁ သာ)
    #        **−2.0 dBFS → TP −1.25 ✓** (margin ၀.၂၅) ← ဒါကို သုံးသည်
    # ⚠️ `level=disabled` **မဖြစ်မနေ** — မထည့်လျှင် alimiter က makeup gain
    #    ထည့်ပြီး LUFS ကို −14.18 မှ −12.68 သို့ တင်ပစ်သည် (တိုင်းထားသည်)。
    af += ",alimiter=limit=0.7943:level=disabled:attack=5:release=50"
    subprocess.run(["ffmpeg","-v","error","-y","-i",inp,"-af",af,
        "-c:v","copy","-c:a","aac","-b:a","192k",
        "-movflags","+faststart",out], check=True)
    return out
