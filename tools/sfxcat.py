#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SFX asset catalog ဆောက်ခြင်း (SFX spec P1)

⚠️ `sfxlib.ROLE` က role ၂၂ ခုစလုံးကို **ဖိုင်တစ်ခုတည်း** ညွှန်းထားသည် —
   ၄၉၇ ဖိုင် ရှိပါလျက် (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。 ⇒ တူညီသော whoosh/click
   ထပ်ကာထပ်ကာ ကြားရပြီး အတုဆန်သည်。

⚠️ tag တိုင်းကို **တိုင်းယူသည်** — ဖိုင်နာမည်ကနေ မှန်းဆတာ မဟုတ်ပါ。
   (နာမည်က role အကြံပြုချက်သာ · `role_src` မှာ မှတ်ထားသည်)
"""
import json
import os
import re
import sys
import wave

import numpy as np

# ⚠️ နာမည်ကနေ role ခန့်မှန်း — **အတည်ပြုချက် မဟုတ်**
HINT = [
    (r"whoosh|swoosh|sweep|swish", "whoosh"),
    (r"impact|hit|boom|slam|thud", "impact"),
    (r"click|mouse|tick|tap", "click"),
    (r"pop|blip|bubble", "pop"),
    (r"riser|rise|build|swell", "riser"),
    (r"latch|lock|snap|clasp", "latch"),
    (r"swipe|slide|drag", "swipe"),
    (r"key|type|keyboard", "type"),
    (r"shimmer|sparkle|chime|bell|glimmer", "shimmer"),
    (r"glitch|digital|error", "glitch"),
    (r"sub|drop|deep|low", "sub"),
    (r"air|texture|amb|room|noise", "air"),
    (r"shutter|camera", "shutter"),
    (r"success|correct|win|positive", "success"),
    (r"wrong|fail|negative|denied", "error"),
    # ── ၂၀၂၆-၀၉-၂၁ ထပ်ထည့် — unknown ၁၄၄ ခုကို တိုင်းထားသော
    #    dur/brightness/loud_db နဲ့ တိုက်စစ်ပြီး ခွဲသည် (reclass)。
    #    ⚠️ ဒီစာရင်း မရှိလျှင် catalog ပြန်ဆောက်တာနဲ့ `unknown` ပြန်ဖြစ်မည်。
    (r"^metal(_\d+)?$", "sub"),                                # br 153–156Hz — အလွန် နိမ့်
    (r"focus_beep", "pop"),                                     # 0.14s blip
    (r"braam|punch|knock|stomp|clap|heartbeat|^wood(_\d+)?$", "impact"),  # loud −12.2 ≈ impact −12.4
    (r"glass|ting|star_ping|glitter|magic_dust|kalimba|ding", "shimmer"),  # br 8.5–12k
    (r"downer|down_tonal|power_down", "sub"),                   # br 153–1993Hz
    # ⚠️ `^page` ကို ထပ်ထည့် — `PAGE-001.mp3` က normalise ပြီး `page_001`
    #    ဖြစ်ရာ `page_flip` နဲ့ မကိုက်ဘဲ `unknown` ၈ ခု ကျန်ခဲ့သည်。
    (r"paper|^page|page_flip|card_deal|flip_card|zipper|scribble", "swipe"),
    # ── ၂၀၂၆-၀၉-၂၅ `mixkit_free` pack (၁,၇၀၇ ဖိုင် · မိသားစု ၅၃ ခု) ──
    #    ⚠️ **role အသစ် မတီထွင်ရ** — `sfxpool.DUR_MAX` နဲ့ `sfxlib.ROLE` က
    #       ရှိပြီးသား ၁၂ ခုကိုသာ သိသည် ⇒ မိသားစုအားလုံးကို အဲဒီပေါ် ချသည်。
    (r"^bleep|^beep|^ding|^notification|^interface|^technology|"
     r"^high_?tech|^sci_?fi|^laser", "pop"),
    (r"^tap|^keyboard|^typewriter", "click"),
    (r"^swoosh|^sweep|^spin|^zoom|^transition", "whoosh"),
    (r"^boom|^hit|^punch|^thud|^explosion|^drum|^cymbal", "impact"),
    # ⚠️ `^cinematic` — mixkit ရဲ့ ၃၆ ဖိုင်။ ရှည်သော swell/boom များ ⇒
    #    `riser`。 ကြားရသော အရှည် ဂိတ် (၃.၂s) ကျော်သူများကို `bed` pool
    #    (`mask_gap ≥ 10.5`) က ယူသည် — `CINEMATIC-028` က အဲဒီလမ်းကြောင်း。
    (r"^swell|^countdown|^suspense|^cinematic", "riser"),
    (r"^chimes|^sparkle|^magic|^win|^correct", "shimmer"),
    (r"^bass|^drone", "sub"),
    (r"^static|^wrong|^rewind|^tape", "glitch"),
    (r"^white_?noise", "air"),
    (r"vinyl|static|crackle|projector|breath|dream_wash", "air"),
    (r"data_|radio_scan|vintage_flash|radio_adjustment", "glitch"),
    (r"doppler|suck_reverse", "whoosh"),
    (r"reverse_cym|lift_bright", "riser"),
    (r"notify|alert|message_in|reminder|level_up", "pop"),      # br 1.8–2.2k ≈ pop 2124Hz
    (r"toggle|button|select|hover|menu_open|foley|beep", "click"),  # loud −20.2 ≈ click −19.6
]

# ⚠️ **MAP က မညွှန်သော family ကို မထားရ** (၂၀၂၆-၀၉-၂၁)。 `sfxpool.MAP` က
#    family ၁၁ ခုသာ ညွှန်သဖြင့် `type`(၇) · `success`(၄) · `error`(၁) တွေ
#    catalog ထဲ ရှိပါလျက် **ထာဝရ မရွေးခံရ**ခဲ့သည်。 ⇒ ညွှန်ပြီးသား family သို့။
#    `air` ကို ချန်ထားသည် — ၃.၅s ambient bed ကို IKKI ရဲ့ cue role တွေ မလိုပါ。
ORPHAN = {"type": "click", "success": "pop", "error": "glitch"}


def role_of(name):
    # ⚠️ **နာမည်ကို normalise ရမည်** (၂၀၂၆-၀၉-၂၅ တွေ့ခဲ့သော အမှား)。
    #    HINT ရဲ့ pattern တွေက `^metal(_\d+)?$` · `radio_adjustment` ·
    #    `vintage_flash` စသဖြင့် **extension ဖြုတ်ပြီး space/dash ကို
    #    underscore ပြောင်းထားသော** နာမည်အတွက် ရေးထားသည် — ဒါပေမယ့်
    #    `role_of` က `.lower()` သာ လုပ်ခဲ့သဖြင့် `metal_01.wav` (`$` က
    #    `.wav` ကြောင့် မကိုက်) · `Radio Adjustment.mp3` (space) ·
    #    `WOOD-001.mp3` (dash) အားလုံး **`unknown`** ဖြစ်ခဲ့သည်。
    #    `mixkit_free` pack ထည့်ရာမှာ ဒါက unknown ၉၉ ခု ဖြစ်စေခဲ့ပြီး
    #    `tests/test_sfxrole.py` က မှန်မှန် ဖမ်းခဲ့သည်。
    n = re.sub(r"[\s\-]+", "_", os.path.splitext(name)[0].lower())
    for pat, r in HINT:
        if re.search(pat, n):
            return ORPHAN.get(r, r)
    return "unknown"


def read_wav(path, max_s=12.0):
    """RIFF ကို **ကိုယ်တိုင် ဖတ်**သည် → `(samples, sr, ch, sw, nframes)`

    ⚠️ Python ရဲ့ `wave` က **WAVE_FORMAT_EXTENSIBLE (0xFFFE)** ကို ငြင်းသည် —
       「unknown format: 65534」。 motionkit ရဲ့ ၄၉၇ ဖိုင်လုံး အဲဒီပုံစံ
       ဖြစ်နေသဖြင့် `wave` နဲ့ **တစ်ဖိုင်မှ မဖတ်နိုင်**ပါ (၂၀၂၆-၀၉-၂၁)。
    ⚠️ ffmpeg နဲ့ ဖတ်လျှင် subprocess ၄၉၇ ခါ — အလွန်ကြာသည် ⇒ ကိုယ်တိုင် ဖတ်。
    """
    import struct
    with open(path, "rb") as f:
        if f.read(4) != b"RIFF":
            return None
        f.read(4)
        if f.read(4) != b"WAVE":
            return None
        fmt = None
        while True:
            h = f.read(8)
            if len(h) < 8:
                return None
            cid, sz = struct.unpack("<4sI", h)
            if cid == b"fmt ":
                d = f.read(sz)
                tag, ch, sr, _br, _ba, bits = struct.unpack("<HHIIHH", d[:16])
                if tag == 0xFFFE and len(d) >= 40:
                    tag = struct.unpack("<H", d[24:26])[0]
                fmt = (tag, ch, sr, bits)
            elif cid == b"data":
                if not fmt:
                    return None
                tag, ch, sr, bits = fmt
                sw = bits // 8
                want = min(sz, int(sr * ch * sw * max_s))
                raw = f.read(want)
                n = sz // max(1, ch * sw)
                return raw, sr, ch, sw, n, tag
            else:
                f.seek(sz + (sz & 1), 1)


# ⚠️ **`.wav` သာ ဖတ်တာက မလုံလောက်** (၂၀၂၆-၀၉-၂၅)。 Zin ကြိုက်သော cue
#    ၁၁ ခု (`BLEEP-003` · `CLICK-004` · `GLITCH-004` · `HIGH_TECH-002` ·
#    `SWOOSH-005` …) က `mixkit_free` pack ရဲ့ **`.mp3`** ဖိုင်များ ဖြစ်ပြီး
#    catalog ၇၄၁ ခုထဲ **တစ်ခုမှ မပါ**ခဲ့ပါ ⇒ ရွေးလို့ မရခဲ့。
#    ⇒ wav မဟုတ်လျှင် ffmpeg နဲ့ s16 wav ပြောင်းပြီး တိုင်းသည် (မူရင်း
#      ဖိုင်ကို **မပြောင်း** · scratch ထဲသာ)。
_DEC = (".mp3", ".m4a", ".aac", ".ogg", ".flac", ".aiff", ".aif")


def _to_wav(path):
    """ffmpeg နဲ့ scratch wav — မရလျှင် None"""
    import subprocess
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        p = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path,
                            "-c:a", "pcm_s16le", tmp],
                           capture_output=True, timeout=60)
        if p.returncode == 0 and os.path.getsize(tmp) > 44:
            return tmp
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        os.unlink(tmp)
    except OSError:
        pass
    return None


def measure(path):
    """အသံဖိုင်တစ်ခု — တိုင်းချက် dict · မရလျှင် None"""
    if path.lower().endswith(_DEC):
        _t = _to_wav(path)
        if not _t:
            return None
        try:
            return measure(_t)
        finally:
            try:
                os.unlink(_t)
            except OSError:
                pass
    r = read_wav(path)
    if not r:
        return None
    raw, sr, ch, sw, n, tag = r
    if n <= 0 or sw not in (2, 3, 4) or tag not in (1, 3):
        return None
    if tag == 3 and sw == 4:                      # IEEE float32
        a = np.frombuffer(raw[:len(raw) // 4 * 4], "<f4").astype(np.float32)
    elif sw == 2:
        a = np.frombuffer(raw[:len(raw) // 2 * 2], "<i2").astype(np.float32) / 32768.0
    elif sw == 4:
        a = np.frombuffer(raw[:len(raw) // 4 * 4], "<i4").astype(np.float32) / 2147483648.0
    else:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
        a = ((b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
              | -((b[:, 2] & 0x80) << 17)).astype(np.float32) / 8388608.0)
    if not len(a):
        return None
    if ch > 1:
        a = a[:len(a) // ch * ch].reshape(-1, ch)
        L, R = a[:, 0], a[:, 1] if ch > 1 else a[:, 0]
        # ⚠️ width — L/R ကွာဟမှု。 mono ဆိုလျှင် ၀
        width = float(np.abs(L - R).mean() / max(1e-6, np.abs(L + R).mean() / 2))
        m = a.mean(1)
    else:
        width = 0.0
        m = a
    dur = n / float(sr)
    # ⚠️ peak ကို **channel တစ်ခုချင်း** ကနေ ယူရမည် — `m` (mono ပေါင်းချက်)
    #    ကနေ ယူလျှင် Haas stereo ဖိုင်များမှာ ၁.၃ dB အထိ **နိမ့်**သွားသည်
    #    (cine_2026/whoosh_fast_03 — ကိုယ်တိုင် -2.8 · ffmpeg -1.5 · ၂၀၂၆-၀၉-၂၁)。
    #    ⇒ အဲဒီ peak နဲ့ normalise လျှင် ကျယ်သော channel က ကျော်လွန်ပြီး
    #      limiter ကို အားကိုးရသည် ⇒ 「peak ပြန့်ကျဲ」 ဖြစ်ရာ。
    peak = float(np.abs(a).max())
    peak_mid = float(np.abs(m).max())
    # ⚠️ **အကျယ်ဆုံး ၃၀၀ ms ဗိန်ဒိုး ရဲ RMS** — အသံ အားကို တိုင်းရန်。
    #    peak နဲ့ normalise လျှင် variant တွေ ၁၂ dB ကွာနေသည် (တိုင်းပြီး
    #    တွေ့ · ၂၀၂၆-၀၉-၂၁) — transient တစ်ချက်က peak တူပေမယ့် အား နည်းသည်。
    #    ⚠️ ဖိုင်တစ်ခုလုံးရဲ RMS ကို မသုံးရ — click မှာ အစောက်ပိုင်းက
    #    များသဖြင့် RMS ကျပြီး အလွန် ကြယ်သွားမည်。 ငှော့ ဗိန်ဒိုးက LUFS-S နဲ့ နီးသည်。
    _w = max(1, int(sr * 0.3))
    if len(m) <= _w:
        loud = float(np.sqrt((m.astype(np.float64) ** 2).mean()))
        peak_t = float(int(np.argmax(np.abs(m))) / sr)
    else:
        _c = np.cumsum(np.concatenate(([0.0], m.astype(np.float64) ** 2)))
        _e = (_c[_w:] - _c[:-_w]) / _w
        loud = float(np.sqrt(_e.max()))
        # ⚠️ **အသံ က ဘယ်အချိန်မှာ ဆိုက်မိတ်လဲ**。 riser က နောက်ဆုံးမှ ကျယ်သည် —
        #    ဂရပ်ဖစ် လာချိန်က cue အစား ထည့်လျှင် ၁.၇s နောက်ကျမှ ကျယ်သည်
        #    (တကန် တိုင်းတွေ့ · ၂၀၂၆-၀၉-၂၁)。 ⇒ အသံ ကျယ်ချိန်ကို မှတ်ထားသည် —
        #    `sfxpool.lead()` က ဒီကို သုံးပြီး **အချိန်ကိုက်အောင် အစား ထည့်**သည်。
        peak_t = float((int(np.argmax(_e)) + _w / 2.0) / sr)
    rms = float(np.sqrt((m ** 2).mean()))
    # ⚠️ brightness — spectral centroid (Hz)。 「တောက်」「မှိန်」ခွဲရန်
    k = min(len(m), 1 << 15)
    F = np.abs(np.fft.rfft(m[:k] * np.hanning(k)))
    f = np.fft.rfftfreq(k, 1.0 / sr)
    cen = float((F * f).sum() / max(1e-9, F.sum()))
    # ⚠️ **စကား band ကွာဟမှု (`mask_gap`)** — ၂၀၂၆-၀၉-၂၅ ထပ်ထည့်。
    #    cue က စကားကို ဖုံးမဖုံး ဆုံးဖြတ်သည်: စုစုပေါင်း စွမ်းအင် ÷
    #    **စကား band (၂၅၀–၃၅၀၀ Hz)** စွမ်းအင်。 ကွာ **ကြီး** ⇒ စွမ်းအင်က
    #    စကား band ပြင်ပ ⇒ ဖုံးမှု **နည်း**。
    #    ⚠️ brightness (spectral centroid) နဲ့ **အစားထိုးလို့ မရ** — `BLEEP-003`
    #       က centroid ၈,၂၀၄ Hz (တောက်) ဖြစ်ပါလျက် ကွာ ၄.၃ dB သာ ရှိသည်
    #       (စွမ်းအင်က စကား band ထဲ ရှိနေ)、`HIGH_TECH-002` က centroid
    #       ၂,၈၈၉ (မှိန်) ဖြစ်ပါလျက် ကွာ ၁၅.၅ dB (စကားအောက် နိမ့်ဘန်း)。
    #    ⚠️ **ဖိုင်တစ်ခုလုံးနဲ့ တွက်ရမည်** — brightness ရဲ့ FFT က ရှေ့
    #       ၃၂,၇၆၈ sample (၀.၆၈s) သာ ယူသည် ⇒ ရှည်သော bed မှာ မှားမည်。
    _FF = np.abs(np.fft.rfft(m.astype(np.float64)))
    _ff = np.fft.rfftfreq(len(m), 1.0 / sr)
    _tot = float((_FF ** 2).sum())
    _sp = float((_FF[(_ff >= 250) & (_ff <= 3500)] ** 2).sum())
    _gap = (10 * np.log10(max(_tot, 1e-12) / max(_sp, 1e-12))
            if _tot > 0 and _sp > 0 else 0.0)
    # ⚠️ impact — အစ ၅၀ms ရဲ့ စွမ်းအင် ÷ စုစုပေါင်း。 「ထိုးကွင်း」ခွဲရန်
    h = max(1, int(sr * 0.05))
    imp = float((m[:h] ** 2).sum() / max(1e-12, (m ** 2).sum()))
    # ⚠️ **ကြားရသော အရှည် (`dur_eff`)** — ၂၀၂၆-၀၉-၂၅ ထပ်ထည့်。
    #    `sfxpool.DUR_MAX` က **ဖိုင်အရှည်**ကို ကန့်သတ်ခဲ့သည်。 ဂိတ်ရဲ့
    #    ရည်ရွယ်ချက်က 「ရှည်လွန်းသော cue က စကားကို ဖုံးသည်」 ဖြစ်ရာ ဖုံးတာက
    #    **ကြားရသော အပိုင်း**သာ ဖြစ်သည် — reverb အမြီးက မဖုံးပါ。
    #    တိုင်းချက် (Zin ကြိုက်သော cue ၁၁ ခု): `SWOOSH-005` ဖိုင် ၃.၁၈s
    #    ဒါပေမယ့် ကြားရ **၀.၉၇s** · `CLICK-004` ၁.၃၇s → **၀.၁၅s** ⇒
    #    ဖိုင်အရှည်နဲ့ ကန့်သတ်ခဲ့တာက ကောင်းသော cue ကို အလဟဿ ပယ်မိခဲ့သည်
    #    (၁၁ ခုလုံး ပယ်ခံခဲ့ပါ)。 ⚠️ ဒါက **ဂိတ် လျှော့တာ မဟုတ်** —
    #    ကြားရသော အရှည် ကျော်လျှင် ပယ်ဆဲ ဖြစ်သည်、တိုင်းတဲ့ ကိန်း ပြောင်းတာ。
    _hop = max(1, int(sr * 0.010))
    _k = len(m) // _hop
    if _k >= 2:
        _rm = np.sqrt((m[:_k * _hop].astype(np.float64) ** 2)
                      .reshape(_k, _hop).mean(axis=1))
        _db = 20 * np.log10(np.maximum(_rm, 1e-7))
        # ⚠️ ၂၅ dB က peak ကနေ ကျသည့်အထိ 「ကြားရ」ဟု တွက်သည် ·
        #    −၅၀ dBFS အောက် ဆိုလျှင် ဘယ်လိုမှ မကြားပါ ⇒ ၂ ခုလုံး
        _on = np.nonzero(_db >= max(float(_db.max()) - 25.0, -50.0))[0]
        _de = (float(int(_on[-1]) + 1) * 0.010) if len(_on) else dur
    else:
        _de = dur
    return dict(dur=round(dur, 3), dur_eff=round(min(_de, dur), 3), sr=sr, ch=ch,
                peak_db=round(20 * np.log10(max(1e-6, peak)), 1),
                peak_mid_db=round(20 * np.log10(max(1e-6, peak_mid)), 1),
                loud_db=round(20 * np.log10(max(1e-6, loud)), 1),
                peak_t=round(peak_t, 3),
                rms_db=round(20 * np.log10(max(1e-6, rms)), 1),
                brightness=int(cen), width=round(min(2.0, width), 3),
                mask_gap=round(float(_gap), 1), impact=round(imp, 3))

# ⚠️ **လိုင်စင် မျဉ်း — ဒါက စီးပွားရေး ကိစ္စ、အသံ ကိစ္စ မဟုတ်။**
#    youtubesfx / Mixkit တို့က 「ဗီဒီယိုထဲ သုံးခွင့်」ပေးသည် —
#    **ဖိုင်ကို product ထဲ ထည့်ဖြန့်ခြင်း ကို တားသည်**。 IKKI က SaaS ဖြစ်၍
#    render ထွက်တာ **customer ရဲ့ ဗီဒီယို** — Zin ရဲ့ မဟုတ် ⇒ ထို pack ကို
#    ပုံသေအနေနဲ့ **မသုံးပါ**。 ကိုယ်ပိုင် synthesis နဲ့ CC0 သာ ship လုပ်သည်。
BANK = {
    # legacy root — <root>/assets/sfx
    "cue":        ("youtubesfx-pack", False, "ဗီဒီယိုထဲသာ · product ထဲ ဖြန့်ခွင့် မရ"),
    "zjl":        ("youtubesfx-pack", False, "cue ရဲ့ highpass ဗားရှင်း — လိုင်စင် တူ"),
    "youtubesfx": ("youtubesfx-pack", False, "မူရင်း ဒေါင်းထား"),
    "gen":        ("own-synthesis",   True,  "sfxgen.py — ကိုယ်တိုင် ဆောက်"),
    "premium":    ("own-synthesis",   True,  "ကိုယ်တိုင် ဆောက်"),
    # motionkit root — <mk>/assets/sfx
    "gen2026":         ("own-synthesis", True, "sfx2026.py — ကိုယ်တိုင် ဆောက်"),
    "gen2026_creator": ("own-synthesis", True, "sfx2026.py creator profile"),
    "hybrid_2026":     ("own-synthesis", True, "hybrid26.py — gen + cc0 ရွေးချယ်"),
    "cine_2026":       ("own-synthesis", True, "ကိုယ်တိုင် ဆောက်"),
    "cc0_2026":        ("cc0",          True, "Openverse/Freesound CC0 — အသံသွင်းချက်"),
    # ⚠️ **လိုင်စင် မျဉ်း ၂ မျိုး ခွဲရမည်** — Mixkit ရဲ့ မှတ်တမ်း
    #    (`assets/sfx/mixkit_free/LICENSES.md`) က 「ကုန်သွယ်မှုအတွက်
    #    သုံးခွင့်ရ · credit မလို」 ဟု ဆိုသည် ⇒ **render ထဲ သုံးတာ ခွင့်ပြု**
    #    ထားပြီး `ship=True` သင့်သည်。 မစစ်ရသေးတာက 「**pack အဖြစ်
    #    ပြန်ဖြန့်/ထည့်ရောင်း**」 ခြင်းသာ ⇒ ဖိုင်များကို repo (public!) သို့
    #    ဒေါင်းလုပ် pack ထဲ **ဘယ်တော့မှ မထည့်ရ**。
    #    Zin ၂၀၂၆-၀၉-၂၅: 「ဒါငါကြိုက်တဲ့ sound effect တွေပါ · သေချာသုံးပေးပါ」
    "mixkit_free": ("mixkit-free", True,
                    "render ထဲ သုံးခွင့်ရ (ကုန်သွယ်မှု · credit မလို) · "
                    "pack အဖြစ် ပြန်ဖြန့်ခွင့် မစစ်ရသေး ⇒ ဖိုင် မဖြန့်ရ"),
}
# ⚠️ ဤဖိုလ်ဒါများက **ထုတ်ယူပြီးသား cache** — မူရင်း မဟုတ် ⇒ မထည့်ရ
SKIP = {"role", "role_gen", "bed"}


def build(roots, out):
    """catalog v2 — root အများအပြား · လိုင်စင် အမှတ်အသား ပါ"""
    items, rmap = [], {}
    for rid, root in roots:
        rmap[rid] = root
        for dp, _dn, fn in os.walk(root):
            bank = os.path.relpath(dp, root).split(os.sep)[0]
            if bank in SKIP or bank == ".":
                continue
            for f in sorted(fn):
                if not f.lower().endswith((".wav",) + _DEC):
                    continue
                p = os.path.join(dp, f)
                m = measure(p)
                if not m:
                    continue
                lic, ship, note = BANK.get(bank, ("unknown", False, "မသိ"))
                m.update(id=f"{bank}/{os.path.splitext(f)[0]}", bank=bank,
                         root=rid, path=os.path.relpath(p, root),
                         role=role_of(f), role_src="filename",
                         license=lic, ship=ship, lic_note=note)
                items.append(m)
    doc = dict(version=2, roots=rmap,
               _doc="⚠️ `role` က **ဖိုင်နာမည်ကနေ ခန့်မှန်း**ထားသည် "
                    "(`role_src: filename`) — နားထောင်ပြီး အတည်ပြုရသေး。 "
                    "ကျန် tag အားလုံးကို sample ကနေ တိုင်းယူထားသည်。 "
                    "⚠️ `ship: false` = ရောင်းသော product ထဲ **မသုံးရ** "
                    "(youtubesfx pack က ဖိုင် ဖြန့်ခွင့် မပေး)。",
               n=len(items), items=items)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    return doc


if __name__ == "__main__":
    out = sys.argv[1]
    rs = [tuple(a.split("=", 1)) for a in sys.argv[2:]]
    d = build(rs, out)
    import collections
    print(f"catalog v{d['version']} · {d['n']} ဖိုင်")
    c = collections.Counter((x["license"], x["ship"]) for x in d["items"])
    for (lic, sh), n in sorted(c.items()):
        print(f"  {lic:16} ship={str(sh):5} {n:4}")
