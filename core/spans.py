#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · span အလိုက် ဖြတ်ပြီး ပေါင်းခြင်း。

⚠️ filtergraph တစ်ခုတည်းနဲ့ **မလုပ်ရ** — [0:v] ကို trim ၄၄ ခု ခွဲလျှင်
   ffmpeg က 4K frame တွေကို တစ်ပြိုင်တည်း ကိုင်ထားပြီး kernel က သတ်သည်
   (**exit -9 · stderr ဗလာ** — ဘာမှ မဖြစ်သလို မြင်ရသည်)。
   ⇒ span တစ်ခုချင်း သီးသန့် ထုတ်ပြီး concat demuxer နဲ့ ပေါင်းရသည်。
"""
import os, subprocess
try:
    from video_codec import h264_args
except ImportError:  # Allows direct package imports in development tools.
    from core.video_codec import h264_args

FADE = 0.02   # ⚠️ select/concat ချည်းသုံးလျှင် ဆက်တိုင်း "ကလစ်" ဆိုသည်

# ⚠️ **ဖြတ်ချက်ကို framing နဲ့ ဖုံးရသည်**。 ၂၀၂၆-၀၉-၂၀: ၈ စက္ကန့် ဖြုတ်ပြီး
#    တစ်နေရာတည်းက shot ကို ဆက်လိုက်သဖြင့် ပြောသူက **ခုန်သွားတာ မြင်ရ**ပြီး
#    「cut ဖြတ်တာရော ... quality 0」 ဟု Zin ပြောခဲ့သည်。 ပရော် editor တွေက
#    ဖြတ်ဆက်တိုင်း framing ပြောင်းပြီး ခုန်မှုကို **တမင် ဖြတ်ချက်** အဖြစ်
#    ဖတ်စေသည်。 ⇒ ဖြတ်ဆက်တိုင်း wide ↔ punch-in အလှည့်ကျ。
# ⚠️ **၁.၂၅× ထက် မကျော်ရ** — proxy က 2560 ဖြစ်၍ ကျော်လျှင် အရည်အသွေး ကျသည်
#    (BRIEF_ref2_ref3 §၂)。 ယခု ၁.၁၀ — ခုန်မှု ဖုံးလောက်ပြီး သိသာမနေ。
# ⚠️ ပြောသူရဲ့ ခေါင်း မပြတ်စေရန် **အလယ်ထက် အနည်းငယ် အပေါ်** ကို ချိန်သည်。
PUNCH = 1.10
PUNCH_Y = 0.42        # ဖြတ်ယူရာ အကွက်ရဲ့ အလယ် (၀.၅ = အလယ်ကွက်တိ)


def _dim(src):
    """ဗီဒီယိုရဲ့ အကျယ်×အမြင့် — punch-in အတွက် **အတိအကျ** လိုသည်。"""
    r = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
                        "-show_entries","stream=width,height","-of","csv=p=0:s=x",src],
                       capture_output=True, text=True)
    try:
        w, h = (r.stdout or "").strip().split("\n")[0].split("x")[:2]
        return int(w), int(h)
    except Exception:
        return 0, 0


def _punch(z, w, h, y=PUNCH_Y, x=0.5):
    """z ဆ punch-in အတွက် ffmpeg filter — မလိုလျှင် None

    `x` — ဘေးတိုက် ချိန်မှတ် (၀ = ဘယ်စွန်း · ၀.၅ = အလယ် · ၁ = ညာစွန်း)

    ⚠️ **scale ကို `iw*z` နဲ့ မရေးရ** — crop ပြီးနောက် ပိုင်းစား အကြွင်းကြောင့်
       ၁၉၂၀ က ၁၉၁၉ ဖြစ်သွားသည် (တကယ် တိုင်း၍ တွေ့)。 span တစ်ခုချင်း အရွယ်
       မတူလျှင် concat က ပျက်မည် ⇒ မူရင်း အရွယ်ကို **ကိန်းသေနဲ့** ပေးရသည်。
    ⚠️ **ဘေးတိုက် ရွှေ့ခြင်းက ဂရပ်ဖစ် နေရာ ရရှိရေးရဲ့ အဓိက နည်းလမ်း**。
       ပြောသူက ဘောင်ရဲ့ အပေါ် ၆၄% ယူပြီး စာတန်းက အောက် ၃၀% ယူသဖြင့်
       ကျန်နေရာက **၃၃px** သာ ဖြစ်သည် (၂၀၂၆-၀၉-၂၁ တိုင်းချက် · template
       ၂၄၃ ခုထဲက တစ်ခုမှ မဝင်)。 ပြောသူကို ဘေးတွန်းလျှင် ကျန်တစ်ဖက်မှာ
       ဘောင်ရဲ့ **တစ်ဝက်နီးပါး** ရသည် — reference တွေ လုပ်ထားတာ အဲဒါ。
    """
    if (not z or abs(z - 1.0) < 1e-3) and abs(float(x) - 0.5) < 1e-3:
        return None
    if w <= 0 or h <= 0:
        return None
    z = max(1.0, min(1.25, float(z or 1.0)))
    cw, ch = int(w / z) // 2 * 2, int(h / z) // 2 * 2
    # ⚠️ ဘောင်ပြင်ပ မထွက်ရ — ကျန်နေရာအတွင်းသာ ရွှေ့သည်
    ox = int(round((w - cw) * max(0.0, min(1.0, float(x)))))
    ox = max(0, min(w - cw, ox)) // 2 * 2
    return (f"crop={cw}:{ch}:{ox}:{int((h - ch) * y)},scale={w}:{h}")


XFADE = 0.025   # ⚠️ ဆက်မှတ် ထပ်ချိန် — လူတည်းဖြတ်သူ သုံးသော ၂၀–၃၀ms


def xfade_audio(src, spans, out, d=XFADE, log=None):
    """ဖြတ်မှတ်များကို **crossfade** နဲ့ ဆက်သော အသံ လမ်းကြောင်း

    ⚠️⚠️ **ဘာကြောင့် လိုလဲ** — ယခင်က အပိုင်းတိုင်းကို သုညဆီ `afade`
       လုပ်ပြီး `concat` လုပ်ခဲ့သည် ⇒ ဆက်မှတ်တိုင်းမှာ ၄၀ms **အသံ ပြတ်**သည်。
       အဲဒါ မကြားရတာက ဖြတ်မှတ် အားလုံး တိတ်ဆိတ်မှုထဲ ရှိနေလို့ ဖြစ်သည်
       (ထွက်ဖိုင် တိုင်းချက်: ချိုင့် ၀ ခု)。 ⇒ **တိတ်ဆိတ်မှုထဲ ဖြတ်ရတာက
       crossfade မရှိလို့**、တိတ်ဆိတ်မှုဆီ ဆွဲရလို့ user ရဲ့ ဖျက်ချက်
       နယ်နိမိတ် ရွေ့ရသည် (ဘေးက စကား ၀.၂၂s ပါသွားခဲ့သည်)。
       crossfade ရှိလျှင် **စကားလုံးအလယ် ဖြတ်လည် မကြားရ** ⇒ user ရဲ့
       နယ်နိမိတ်အတိုင်း တိတိကျကျ ဖြတ်နိုင်သည် (Zin ရွေးချယ်ချက် 「က」)。

    ⚠️⚠️ **ကြာချိန် မရွေ့စေရ**。 `acrossfade=d` က အပိုင်း ၂ ခုကို `d` ကြာ
       ထပ်စေသဖြင့် ဆက်မှတ် ၄၃ ခု ဆိုလျှင် **၁.၀၇s တို**သွားမည် ⇒ ဗီဒီယိုနဲ့
       မကိုက်တော့ (တိုင်းပြီး: handle မပါလျှင် −၀.၁၀၀s / ဆက်မှတ် ၄ ခု)。
       ⇒ အပိုင်းတိုင်းကို `d/2` စီ **ပိုဆွဲ** (handle) ပြီး ထပ်ချက်က အဲဒါကို
         စားစေသည်。 ⚠️ **ပထမရဲ့ အစ · နောက်ဆုံးရဲ့ အဆုံး** မှာ handle
         မထည့်ရ — ထပ်ချက် မရှိ၍ စားမခံရဘဲ ကျန်မည် (တိုင်းပြီး: +၀.၀၂၅s)。
       တိုင်းချက် — handle မှန်မှန် ထည့်လျှင် ရွေ့ **+၀.၀၀၀s**。
    ⚠️ handle က **ဖျက်လိုက်သော အပိုင်း**ကနေ ၁၂.၅ms ယူသည် — မကြားနိုင်သော
       အရှည် ဖြစ်ပြီး လူတည်းဖြတ်သူရဲ့ 「handle」 နဲ့ အတူတူ。
    """
    n = len(spans)
    if n == 0:
        raise RuntimeError("span မရှိ")
    work = os.path.dirname(out) or "."
    parts = []
    for i, (a, b) in enumerate(spans):
        hl = (d / 2.0) if i > 0 else 0.0
        hr = (d / 2.0) if i < n - 1 else 0.0
        a2 = max(0.0, float(a) - hl); b2 = float(b) + hr
        q = os.path.join(work, "_xa%04d.wav" % i)
        # ⚠️ `-ss` ကို `-i` **နောက်မှာ** ထားသည် — တိကျသော ရှာဖွေမှု
        #    (keyframe မဟုတ်)。 အသံသာ ဖြစ်၍ နှေးမှု သိပ် မရှိ。
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src,
                        "-ss", "%.4f" % a2, "-t", "%.4f" % (b2 - a2),
                        "-vn", "-ac", "2", "-ar", "48000", q], check=True)
        parts.append(q)
    if n == 1:
        os.replace(parts[0], out)
        return out
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for q in parts:
        cmd += ["-i", q]
    fc = []; last = "0:a"
    for i in range(1, n):
        lab = "x%d" % i
        fc.append("[%s][%d:a]acrossfade=d=%.4f:c1=tri:c2=tri[%s]" % (last, i, d, lab))
        last = lab
    cmd += ["-filter_complex", ";".join(fc), "-map", "[%s]" % last, out]
    subprocess.run(cmd, check=True)
    for q in parts:
        try:
            os.remove(q)
        except OSError:
            pass
    return out


def spans(src, spans, out, work, fps=30, vcodec=None, vb="10M",
          fade=FADE, zooms=None, scale=None):
    """ဖြတ်မှတ်အတိုင်း ဖြတ်ပြီး ပြန်ဆက်သည်。

    `scale` = အမြင့် (px)。 ပေးလျှင် အရွယ် ချုံ့သည် — **clean-cut preview**
    အတွက် (540p · 1.5M) ဖြစ်ပြီး နောက်ဆုံး render မှာ မသုံးပါ。
    """
    os.makedirs(work, exist_ok=True)
    # A caller may explicitly request a codec for an experiment.  Normal IKKI
    # renders must use the platform-safe default: VideoToolbox on macOS and
    # libx264 on Linux.
    enc = (["-c:v", vcodec, "-b:v", vb] if vcodec else
           h264_args(vb, crf=20 if scale else 18))
    parts=[]
    _w, _h = _dim(src) if zooms else (0, 0)
    for i,(a,b) in enumerate(spans):
        d=b-a
        if d <= 0.05: continue
        p=os.path.join(work, f"s{i:04d}.mp4")
        # ⚠️ zoom တန်ဖိုးက ကိန်းတစ်ခု (ယခင်) **သို့မဟုတ်** dict (zoom+x+y)
        _zv = (zooms or {}).get(i)
        if isinstance(_zv, dict):
            vf = _punch(_zv.get("zoom"), _w, _h,
                        y=_zv.get("y", PUNCH_Y), x=_zv.get("x", 0.5))
        else:
            vf = _punch(_zv, _w, _h)
        # ⚠️⚠️ **အသံကို ဒီမှာ မထည့်တော့ပါ** (၂၀၂၆-၁၀-၀၂)。 ယခင်က အပိုင်း
        #    တိုင်းကို သုညဆီ `afade` လုပ်ပြီး concat လုပ်ခဲ့ရာ ဆက်မှတ်တိုင်းမှာ
        #    အသံ ၄၀ms ပြတ်သည် ⇒ ဖြတ်မှတ်ကို တိတ်ဆိတ်မှုထဲ ထားရသည် ⇒
        #    user ရဲ့ ဖျက်ချက် နယ်နိမိတ် ရွေ့ရသည်。 ယခု အသံကို
        #    `xfade_audio()` နဲ့ **crossfade** လုပ်ပြီး နောက်မှ mux သည်。
        cmd = ["ffmpeg","-v","error","-y",
            "-ss",f"{a:.3f}","-i",src,"-t",f"{d:.3f}","-an"]
        if scale:
            _sc = f"scale=-2:{int(scale)}"
            vf = f"{vf},{_sc}" if vf else _sc
        if vf: cmd += ["-vf", vf]
        cmd += ["-r",str(fps),*enc,
                "-avoid_negative_ts","make_zero",p]
        subprocess.run(cmd, check=True)
        parts.append(p)
    if not parts: raise RuntimeError("span မရှိ")
    lst=os.path.join(work,"parts.txt")
    with open(lst,"w") as f:
        for p in parts: f.write("file '%s'\n" % p.replace("'","'\\''"))
    _v = os.path.join(work, "_vonly.mp4")
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",lst,
                    "-c","copy",_v], check=True)
    # ── အသံကို crossfade နဲ့ ဆောက်ပြီး mux ───────────────────────────
    # ⚠️ ကြာချိန် မရွေ့ကြောင်း `xfade_audio` မှာ handle နဲ့ အာမခံထားသည်。
    #    ⚠️ ကျဆုံးလျှင် **တိတ်တဆိတ် မကျော်ရ** — ယခင် နည်း (အသံပါ concat)
    #      ကို ပြန်သုံးပြီး အကြောင်း ပြရမည်。
    _a = os.path.join(work, "_axf.wav")
    try:
        xfade_audio(src, spans, _a)
        subprocess.run(["ffmpeg","-v","error","-y","-i",_v,"-i",_a,
                        "-map","0:v:0","-map","1:a:0","-c:v","copy",
                        "-c:a","aac","-b:a","192k","-shortest",out], check=True)
    except Exception as _xe:
        print(f"  ⚠️ အသံ crossfade မရ ({type(_xe).__name__}: {_xe}) — "
              f"ယခင်နည်း (fade+concat) သို့ ပြန်သွားသည်", flush=True)
        _p2 = []
        for i, (a, b) in enumerate(spans):
            d = b - a
            if d <= 0.05: continue
            q = os.path.join(work, f"a{i:04d}.m4a")
            subprocess.run(["ffmpeg","-v","error","-y","-i",src,
                "-ss",f"{a:.3f}","-t",f"{d:.3f}","-vn",
                "-af",f"afade=t=in:st=0:d={fade:.4f},"
                      f"afade=t=out:st={max(0,d-fade):.3f}:d={fade:.4f}",
                "-c:a","aac","-b:a","192k",q], check=True)
            _p2.append(q)
        l2 = os.path.join(work,"aparts.txt")
        with open(l2,"w") as f:
            for q in _p2: f.write("file '%s'\n" % q.replace("'","'\\''"))
        subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0",
                        "-i",l2,"-c","copy",_a+".m4a"], check=True)
        subprocess.run(["ffmpeg","-v","error","-y","-i",_v,"-i",_a+".m4a",
                        "-map","0:v:0","-map","1:a:0","-c","copy",
                        "-shortest",out], check=True)
        for q in _p2 + [l2, _a+".m4a"]:
            try: os.remove(q)
            except OSError: pass
    for p in parts: os.remove(p)
    for q in (lst, _v, _a):
        try: os.remove(q)
        except OSError: pass
    return out

def _solve_ceiling(got_tp, tp, applied, lo=-12.0, hi=-1.0):
    """နောက်တစ်ကြိမ် သုံးရမည့် limiter ခေါင်း (dBFS)

    ⚠️⚠️ `alimiter` က **နမူနာ အထွတ်** ကိုသာ ကန့်သတ်ပြီး **true peak** က
       inter-sample နဲ့ AAC ကြောင့် ပိုမြင့်နိုင်သည်。 ၂၀၂၆-၁၀-၀၂ j_s41 —
       ခေါင်း −၂.၀၀ dBFS မှာ TP **+၁.၀၀** dBTP ထွက်ခဲ့သည် (ကျော်မှု ၃.၀ dB)。
    ⇒ ခေါင်း `C` နဲ့ TP `T` ရလျှင် ကျော်မှု `O = T − C` ⇒ ပစ်မှတ် `tp`
      ရဖို့ **`C = tp − O`**。 ချိုးဖြတ်ခြင်း (တစ်လမ်းသာ ချ) က တုန်ခါစေပြီး
      headroom ကို အမြဲ ဆုံးရှုံးစေသည်。
    ⚠️ ပထမအကြိမ်မှာ ခေါင်း မသုံးရသေး ⇒ ကျော်မှု မသိ ⇒ −၂.၀ ကနေ စသည်。
    """
    if applied is None:
        return max(lo, min(hi, min(-2.0, tp - max(0.0, got_tp - tp))))
    over = got_tp - applied
    return max(lo, min(hi, tp - max(0.0, over)))


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

    # ⚠️ **ရလဒ်ကို တိုင်းပြီး မကိုက်မချင်း ပြန်ချိန်ရမည်**。
    #    ၂၀၂၆-၀၉-၂၀: true peak −0.1 dBTP ထွက်ခဲ့သည် (ဂိတ် ≤ −1.0)。
    #    ⚠️ ပထမ ပြင်ချက်မှာ **dB ချရုံ** ချခဲ့ရာ TP ပြေပေမယ့် LUFS −15.5 → −16.7
    #    ဖြစ်ပြီး **LUFS ဂိတ် ပြန်လွဲ**ခဲ့သည်。 ⇒ ချရုံ မဟုတ်ဘဲ **limiter ထဲ
    #    gain တင်သွင်း**ရမည် — limiter က TP ကို ထိန်းပြီး loudness တက်သည်
    #    (mastering ရဲ့ အခြေခံ)。 ဂိတ် နှစ်ခုလုံး ကိုက်မချင်း ၃ ကြိမ် ချိန်သည်。
    #    ⚠️ ဂိတ်ကို **မလျှော့ပါ** — ဂိတ်ထဲ ဝင်အောင် mastering ကို လုပ်ခိုင်းသည်。
    # ⚠️ ceiling ကို **ကြိမ်တိုင်း −2.0 ကနေ ပြန်မစရ** — အရင်က အဲဒီလို ရေးမိပြီး
    #    −2.9 → −2.5 → −2.6 ဟု **တုန်ခါ**နေခဲ့သည် (စမ်းစဉ် ဖမ်းမိ · ၂၀၂၆-၀၉-၂၀)。
    #    ⇒ state အဖြစ် ချန်ပြီး **အဆင့်လိုက် ချသွား**ရမည်。
    # ⚠️ **gain ကို စုပေါင်းပြီး မထည့်ရ** (၂၀၂၆-၀၉-၂၁ j_1f9561de04b3)。
    #    `out` က ကြိမ်တိုင်း ပြောင်းပြီးသား ဖြစ်သဖြင့် စုပေါင်း gain ကို
    #    ပြန်ထည့်လျှင် **နှစ်ထပ်** ဖြစ်သည် — ကြိမ် ၂ မှာ +1.40 ပါပြီးသား ဖိုင်ပေါ်
    #    +2.00 ထပ်ထည့်၍ တကယ် +3.40 ဖြစ်ကာ တုန်ခါခဲ့သည်:
    #        −15.4 → −14.6 → −13.6 → −13.4  ⇒ loop ကုန်ပြီး −13.0 ထွက်
    #    ⇒ **ကြိမ်တိုင်း ကွာချက် (delta) ကိုသာ** ထည့်သည် — loop ကိုယ်တိုင်
    #      တိုင်းပြီး ပြန်ချိန်သဖြင့် feedback က စုပေါင်းပေးပြီးသား。
    # ⚠️ **နောက်ဆုံး ရေးချက်ကို မတိုင်းဘဲ မထွက်ရ** — အရင်က loop ကုန်တာနဲ့
    #    ပြန်မတိုင်းသဖြင့် log ရဲ့ နောက်ဆုံးလိုင်းက **ဟောင်းနေ**ခဲ့ပြီး
    #    တကယ့် ထွက်ကိန်းကို QC မှာမှ တွေ့ရသည်。
    ITER = 5
    tot = 0.0
    ceil_db = -2.0
    applied = None          # ⚠️ နောက်ဆုံး တကယ် သုံးခဲ့သော limiter ခေါင်း
    best = None             # ⚠️ (ဒဏ်မှတ်, ဖိုင်) — အကောင်းဆုံး အခြေအနေ
    bestp = out + ".best.mp4"
    ok = False
    # ⚠️ **ITER + ၁ ပတ်** — နောက်ဆုံး ချိန်ချက်ရဲ့ ရလဒ်ကိုပါ တိုင်းရမည်
    #    (ယခင်က မတိုင်းဘဲ ထွက်သွားသည်)。
    for _it in range(ITER + 1):
        got_tp, got_i = _tp(out), _lufs(out)
        if got_tp is None or got_i is None:
            print("  ⚠️ mastering ကိန်း မတိုင်းနိုင် — ဆက်သွားသည်", flush=True); break
        d_tp = got_tp - tp                  # >0 = ပြင်းလွန်း
        d_i  = lufs - got_i                  # >0 = တိတ်လွန်း
        # ⚠️⚠️ **အကောင်းဆုံးကို မှတ်ထားရမည်**。 loop က `out` ကို နေရာတွင်း
        #    လဲနေပြီး မပြေလည်လျှင် **နောက်ဆုံး (အဆိုးဆုံး ဖြစ်နိုင်) ဟာကို**
        #    ပို့ပေးခဲ့သည် (၂၀၂၆-၁၀-၀၂ j_s41)。 TP ကျော်တာက ဂိတ် ပျက်ခြင်း
        #    ဖြစ်၍ ၂ ဆ ဒဏ်ပေးသည်; TP နိမ့်တာက ဂိတ် မပျက်ပါ。
        _pen = max(0.0, d_tp) * 2.0 + abs(d_i)
        if best is None or _pen < best[0] - 1e-9:
            try:
                import shutil as _sh
                _sh.copyfile(out, bestp); best = (_pen, bestp)
            except OSError:
                pass
        if d_tp <= 0.0 and abs(d_i) <= 0.4:
            ok = True
            print(f"  mastering · I {got_i:+.1f} LUFS · TP {got_tp:+.2f} dBTP "
                  f"[≤ {tp}] ✓{' · ချိန် '+str(_it)+' ကြိမ်' if _it else ''}", flush=True)
            break
        if _it >= ITER:
            break
        # ⚠️⚠️ **ခေါင်းကို တစ်လမ်းသာ ချတာ မှား**ခဲ့သည်。 `alimiter` က
        #    နမူနာ အထွတ်ကိုသာ ကန့်သတ်ပြီး **true peak** က AAC/inter-sample
        #    ကြောင့် ပိုမြင့်နိုင်သည် ⇒ ခေါင်း −၂.၀၀ မှာ TP **+၁.၀၀** ထွက်ခဲ့ ⇒
        #    ကုဒ်က ခေါင်းကို ချလိုက်ပြီး **ပြန်မတင်**သဖြင့် −၂.၀၀ → −၄.၂၅ →
        #    −၅.၂၀ ဆင်းကာ TP က −၂.၆ ⇄ −၀.၃ ⇄ −၃.၆ တုန်ခါပြီး ၅ ကြိမ်လုံး
        #    မပြေလည်ခဲ့ (j_s41: I −14.70 · TP −3.97 နဲ့ ထွက်သွားသည်)。
        # ⇒ **ချိုးဖြတ်မယ့်အစား တွက်သည်** — ခေါင်း `C` သုံးပြီး TP `T` ရလျှင်
        #   ကျော်မှု `O = T − C` ဖြစ်၍ ပစ်မှတ် `tp` ရဖို့ `C = tp − O`。
        ceil_db = _solve_ceiling(got_tp, tp, applied)
        # ⚠️ တစ်ကြိမ်လျှင် ±၃ dB ထက် မခုန်ရ — တုန်ခါမှု တားရန်
        step = max(-3.0, min(3.0, d_i))
        tot = max(-9.0, min(9.0, tot + step))
        lim = 10 ** (ceil_db / 20.0)
        applied = ceil_db
        tmp = out + ".fix.mp4"
        subprocess.run(["ffmpeg","-v","error","-y","-i",out,
            "-af", f"volume={step:+.2f}dB,"
                   f"alimiter=limit={lim:.4f}:level=disabled:attack=5:release=50",
            "-c:v","copy","-c:a","aac","-b:a","192k",
            "-movflags","+faststart",tmp], check=True)
        os.replace(tmp, out)
        print(f"  🔧 ချိန် {_it+1} — I {got_i:+.1f}→ပစ်မှတ် {lufs} · TP {got_tp:+.2f} "
              f"· ဒီကြိမ် {step:+.2f} dB (စုစုပေါင်း {tot:+.2f}) · "
              f"ceiling {ceil_db:.2f} dBFS", flush=True)
    if not ok:
        # ⚠️⚠️ **အကောင်းဆုံးကို ပြန်သုံးရမည်** — နောက်ဆုံး ချိန်ချက်က
        #    အဆိုးဆုံး ဖြစ်နိုင်သည်。
        if best:
            try:
                os.replace(best[1], out)
            except OSError:
                pass
        # ⚠️ မကိုက်ဘဲ ထွက်လျှင် **တကယ့် ကိန်းကို ပြရမည်** — QC က ပိတ်မည်、
        #    ဒါပေမယ့် ဘာလို့ ပိတ်လဲ log ကနေ ချက်ချင်း မြင်ရစေရန်。
        f_tp, f_i = _tp(out), _lufs(out)
        print(f"  ⚠️ mastering ချိန် {ITER} ကြိမ် ပြီးလည်း မကိုက် — "
              f"I {f_i if f_i is None else round(f_i,1)} LUFS (ပစ်မှတ် {lufs}) · "
              f"TP {f_tp if f_tp is None else round(f_tp,2)} dBTP (≤ {tp})",
              flush=True)
    return out


def _lufs(path):
    """ဖိုင်ရဲ့ integrated loudness (LUFS) — မတိုင်းနိုင်လျှင် None。"""
    import re as _re
    r = subprocess.run(["ffmpeg","-v","info","-i",path,"-af","ebur128=peak=true",
                        "-f","null","-"], capture_output=True, text=True)
    m = _re.findall(r"I:\s*([-\d.]+)\s*LUFS", r.stderr)
    try: return float(m[-1])
    except Exception: return None


def _tp(path):
    """ဖိုင်ရဲ့ true peak (dBTP) — မတိုင်းနိုင်လျှင် None。"""
    import re as _re
    r = subprocess.run(["ffmpeg","-v","info","-i",path,"-af","ebur128=peak=true",
                        "-f","null","-"], capture_output=True, text=True)
    m = _re.findall(r"True peak:\s*\n?\s*Peak:\s*([-\d.]+)", r.stderr)
    if not m:
        m = _re.findall(r"Peak:\s*([-\d.]+)\s*dBFS", r.stderr)
    try: return float(m[-1])
    except Exception: return None
