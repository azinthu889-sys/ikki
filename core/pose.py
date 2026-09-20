#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · 「ကင်မရာရှေ့ စကားပြောနေဟန်」 ပျက်နေသော အပိုင်းများ ရှာခြင်း。

Zin ၂၀၂၆-၀၉-၁၉:
  「ဒီလို အမူအရာ ပုံမှန်မဟုတ်တဲ့ဟာ · စကားပြောနေတဲ့ပုံစံ မဟုတ်တဲ့ transcript တွေ
   သုံးမရဘူးဆိုတာ မင်းကိုယ်တိုင် သိရမယ်။ ပြီးတာနဲ့ မင်းက ဖြတ်ရမည့် စာရင်းထဲ
   ထည့်ပြီး user ကို သတိပေးရမယ်」

⚠️ **အသံနဲ့ တိုင်းလို့ မရပါ** — စကားသံက ပုံမှန်ပင် ဖြစ်နေသည်。 ရုပ်ပုံကနေသာ
   တိုင်းလို့ ရသည် ⇒ macOS Vision (`tools/posecheck`)。

⚠️ ဂိတ်များကို **ကိန်း မမြင်ခင်** သတ်မှတ်ပြီး ပြီးမှ တကယ့် ဗီဒီယိုနှင့် တိုက်ခဲ့သည်
   (src j_62a25d9d5f43 · ၃၅၇ ဖရိမ်း · ၂၀၂၆-၀၉-၁၉)。 ရလဒ်ကို မျက်စိနဲ့ပါ စစ်ပြီး:
     t=3.0s · 6.0s   ကိုယ်လုံး ဘောင်ဖုံး · လက် ကင်မရာဆီ လှမ်း · ခေါင်း ပြတ်  ✓
     t=12.5s · 14.0s ဖုန်း/စားပွဲ ငုံ့ကြည့် — ကင်မရာကို မဟုတ်              ✓
     t=176.0s        လူ ဘောင်ထဲက လုံးဝ ထွက်သွား                          ✓
     t=40.0s         ပုံမှန် စကားပြောနေ — flag မတက်                       ✓

⚠️ ဂိတ်ကို **ပုံသေ ကိန်း မထားရ** — ဗီဒီယိုတိုင်း ဘောင်/အကွာအဝေး မတူ。
   ⇒ `ps` ကို အဲဒီ ဗီဒီယိုရဲ့ **ကိုယ်ပိုင် အလယ်တန်း**နှင့် နှိုင်းသည်。
"""
import os, json, subprocess, tempfile, shutil

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN  = os.path.join(HERE, "tools", "posecheck")

FPS      = 2.0      # တိုင်းနှုန်း — 0.5s တစ်ခါ
PS_K     = 1.8      # လူပုံ ဖုံးအုပ်မှု — အလယ်တန်း၏ အဆ
# ⚠️ yaw ကို **ပုံသေ ဒီဂရီနဲ့ မတိုင်းရ**。 ဗီဒီယို ၂ မှာ Zin က ကင်မရာနဲ့
#    စောင်းထိုင်နေ၍ **ပုံမှန် yaw ကိုယ်တိုင် ၂၂.၄°** ဖြစ်ပြီး ပုံသေ ၂၅° ဂိတ်က
#    ဝါကျ ၄၇/၉၈ ကို အမှား မှတ်ခဲ့သည် (၂၀၂၆-၀၉-၁၉ · j_dd56e503c95c)。
#    ⇒ **အဲဒီဗီဒီယိုရဲ့ ကိုယ်ပိုင် အလယ်တန်းမှ သွေဖည်မှု**ကို တိုင်းသည် —
#      `ps` နဲ့ အတူတူ。 တိုင်းချက် (ဗီဒီယို ၂ ပုဒ် · ဖရိမ်း ၁၀၉၁):
#        ဗီဒီယို ၁ (ဖုန်း ငုံ့ကြည့် — တကယ်) သွေဖည်မှု p99 ၅၃.၈° · အများဆုံး ၅၅.၉°
#        ဗီဒီယို ၂ (ပုံမှန် စောင်းထိုင်)   သွေဖည်မှု အများဆုံး ၂၁.၂°
#      ⇒ ၂၅° က ဗီဒီယို၁ ကို ဖမ်းပြီး ဗီဒီယို၂ မှာ **အမှား ၀**。
YAW_DEV  = 25.0
MIN_RUN  = 1.0      # ဤထက် တိုလျှင် **မယူ** — ဖရိမ်း တစ်ခုတည်း အမှား ကာကွယ်
PAD      = 0.25     # အပိုင်း နှစ်ဖက် ဖြည့်


def available():
    return os.path.exists(BIN) and shutil.which("ffmpeg") is not None


def measure(path, fps=FPS, log=None):
    """[{t, nf, fa, fx, fy, yaw, roll, ps}] — ffmpeg ဖြင့် frame ထုတ်ပြီး Vision"""
    if not available():
        raise RuntimeError("posecheck မရှိ (swiftc နဲ့ တည်ဆောက်ရန်)")
    d = tempfile.mkdtemp(prefix="pose_")
    try:
        # ⚠️ `AVAssetImageGenerator` ကို **မသုံးရ** — source အချို့မှာ ဗလာ ပုံသာ
        #    ပြန်ပေးပြီး မျက်နှာ ၀ ခု ဖြစ်ခဲ့သည် (တကယ် ဖြစ်ခဲ့ · ၂၀၂၆-၀၉-၁၉)。
        subprocess.run(["ffmpeg", "-v", "error", "-i", path,
                        "-vf", f"fps={fps},scale=640:-2",
                        os.path.join(d, "f%05d.png"), "-y"], check=True)
        p = subprocess.run([BIN, d, str(fps)], capture_output=True, text=True, timeout=1800)
        out = []
        for line in (p.stdout or "").splitlines():
            line = line.strip()
            if line.startswith("{"):
                try: out.append(json.loads(line))
                except Exception: pass
        if log and not out:
            log(f"  ⚠️ posecheck ထွက်ချက် ဗလာ: {(p.stderr or '')[-160:]}")
        return out
    finally:
        shutil.rmtree(d, ignore_errors=True)


def spans(frames, log=None):
    """ဟန်ပျက် အပိုင်းများ — [(a, b, အကြောင်းရင်း)]"""
    if not frames: return []
    ps = sorted(f.get("ps", 0.0) for f in frames)
    med = ps[len(ps)//2] if ps else 0.0
    thr = med * PS_K
    # ⚠️ ဤဗီဒီယိုရဲ့ **ပုံမှန် ထိုင်ပုံ** — ဒီကနေ သွေဖည်မှုကို တိုင်းသည်
    _y = sorted(f["yaw"] for f in frames
                if f.get("nf", 0) > 0 and abs(f.get("yaw", 999.0)) < 400)
    ymed = _y[len(_y)//2] if _y else 0.0
    step = 1.0 / FPS
    hits = []
    for f in frames:
        why = None
        if f.get("nf", 0) == 0:                     why = "မျက်နှာ မတွေ့"
        elif med > 0 and f.get("ps", 0) > thr:      why = "ကိုယ်လုံး ဘောင်ဖုံး"
        elif (abs(f.get("yaw", 999.0)) < 400
              and abs(f.get("yaw", 0.0) - ymed) > YAW_DEV):
            why = "ကင်မရာကို မကြည့်"
        hits.append((f["t"], why))
    # ── စဉ်ဆက် ပေါင်း ──
    runs, cur = [], None
    for t, why in hits:
        if why:
            if cur is None: cur = [t, t, {why}]
            else: cur[1] = t; cur[2].add(why)
        elif cur:
            runs.append(cur); cur = None
    if cur: runs.append(cur)
    out = []
    for a, b, ws in runs:
        b = b + step
        # ⚠️ တိုလွန်းလျှင် **မယူ** — ဖရိမ်း တစ်ခု အမှားက ဝါကျ တစ်ခုလုံး ဖျက်စေနိုင်
        if b - a < MIN_RUN: continue
        out.append((max(0.0, a - PAD), b + PAD, " · ".join(sorted(ws))))
    if log:
        log(f"  ဟန်ပျက် {len(out)} အပိုင်း (လူပုံ အလယ် {med:.3f} · ဂိတ် {thr:.3f} · "
            f"ပုံမှန် yaw {ymed:.1f}° ± {YAW_DEV:.0f}°)")
        for a, b, w in out:
            log(f"        {a:7.1f}–{b:6.1f}s  ({b-a:4.1f}s)  {w}")
    return out


def mark(sentences, sp, cover=0.5):
    """ဝါကျ အညွှန်း → အကြောင်းရင်း。 ဝါကျ ကြာချိန်၏ `cover` အထက် ထပ်မှသာ。

    ⚠️ **ကိုယ်တိုင် မဖျက်ရ** — Zin ၏ စည်းမျဉ်း: 「user အတည်ပြုမှ ဖျက်ပေး。
       script editor မှာပဲ အနီပြထား」 ⇒ ဤ function က **အမှတ်အသားသာ** ပေးသည်。
    """
    out = {}
    for s in sentences or []:
        a, b = float(s.get("start", 0)), float(s.get("end", 0))
        if b <= a: continue
        ov, ws = 0.0, set()
        for x, y, w in sp:
            o = min(b, y) - max(a, x)
            if o > 0: ov += o; ws.add(w)
        if ov / (b - a) >= cover:
            out[int(s.get("n") or s.get("i") or 0)] = " · ".join(sorted(ws))
    return out
