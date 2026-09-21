#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI Mac worker — API ကို HTTPS ဖြင့် ဆွဲယူသည် (ssh မဟုတ်တော့)。

    python3 worker/run.py [--once]

⚠️ scratch ကို **Mac ထဲမှာသာ** ထားရမည် — ပြင်ပ ExFAT disk မှာ PNG သေးသေး
   ရေးတာ ၂၀ ဆ နှေးသည် (တိုင်းပြီး: ၅၀၀ ဖိုင် · ပြင်ပ 1.47s vs Mac ထဲ 0.07s)。
"""
import json, math, os, re, shutil, subprocess, sys, time, traceback, urllib.request, urllib.error

API    = os.environ.get("IKKI_API", "http://127.0.0.1:8080")
TOKEN  = os.environ.get("IKKI_WORKER_TOKEN", "dev-worker")
SCRATCH= os.path.expanduser("~/.ikki/scratch")
# ⚠️ render လုပ်နေစဉ် ရှိနေမည့် အမှတ်ဖိုင် — `deploy.sh` က ဒါကို စစ်သည်。
BUSY   = os.path.expanduser("~/.ikki/busy")
# ⚠️ motionkit ကတ်တစ်ခုရဲ့ **အတိုဆုံး သဘာဝ အရှည်** (တိုင်းထားသည်:
#    median ၂.၄s · min ၁.၈s · max ၃.၀s — j_e45a95bd33ea ရဲ့ report)。
#    ကတ် ဘယ်နှစ်ခုအထိ ထုတ်လို့ ရမလဲ တွက်ရာမှာ သုံးသည်。
CARD_NAT_MIN = 1.8
LAST_FIT = []          # `_fit_gfx` ရဲ့ မှတ်ချက် — report အတွက်
# ── ဖိုင်ကြီးများကို သီးသန့် disk မှာ ထားနိုင်သည် ──────────────
# ⚠️ **ဖိုင်ကြီး သာ** ပြင်ပ disk မှာ ထားရမည် (မူရင်း · proxy)。 PNG ထောင်ချီ
#    ရေးတဲ့ `_w/` ကို ပြင်ပ မှာ **ဘယ်တော့မှ မထားရ** — တိုင်းချက် ၂၀၂၆-၀၉-၁၉:
#      Mac ထဲ SSD   ဖိုင်ကြီး 1206 MB/s · ဖိုင်သေး 11654 ဖိုင်/s
#      ပြင်ပ ExFAT   ဖိုင်ကြီး   31 MB/s · ဖိုင်သေး   176 ဖိုင်/s
#    ⇒ ဖိုင်ကြီးက ၃၉ ဆ · ဖိုင်သေးက **၆၆ ဆ** နှေးသည်。 R2 ဆွဲချမှုက ၇ MB/s
#      ဖြစ်၍ ၃၁ MB/s က မူရင်း/proxy အတွက် လုံလောက်သည်。
# ⚠️ drive မရှိလျှင် **တိတ်တဆိတ် မကျရ** — Mac ထဲကို ပြန်သုံးသည်。
def _bigdir():
    d = os.environ.get("IKKI_BIG")
    if not d: return SCRATCH
    try:
        os.makedirs(d, exist_ok=True)
        t = os.path.join(d, ".w")
        with open(t, "wb") as f: f.write(b"1")
        os.remove(t)
        return d
    except Exception as e:
        print(f"  ⚠️ IKKI_BIG သုံးမရ ({e}) — Mac ထဲ scratch ကို သုံးသည်", flush=True)
        return SCRATCH
BIG = _bigdir()
# ⚠️ worker တစ်ခုချင်း **ကွဲပြားသော အမှတ်** ရှိရမည် — job တစ်ခုတည်းကို
#    worker ၂ ခု ယူမိခြင်း မဖြစ်စေရန် (၂၀၂၆-၀၉-၁၉)。
import socket as _sock
WORKER_ID = os.environ.get("IKKI_WORKER_ID") or f"{_sock.gethostname()}:{os.getpid()}"
MK     = os.environ.get("IKKI_MOTIONKIT",
         "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")
POLL   = int(os.environ.get("IKKI_POLL", "6"))
os.makedirs(SCRATCH, exist_ok=True)
sys.path.insert(0, MK)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))

# ⚠️ **ယာယီ အမှားကြောင့် render တစ်ခုလုံး မဆုံးရှုံးရ**。
#    ၂၀၂၆-၀၉-၂၀: deploy က API container ကို ပြန်ဆောက်နေစဉ် Caddy က
#    **404** ပြန်သည် (502 မဟုတ်)。 j_bd28f6df827f က stage 1–6 အောင်ပြီး
#    stage 7 ပို့ချိန် အဲဒီ ၂–၃ စက္ကန့် အတွင်း တိုက်မိပြီး ၂၀ မိနစ်စာ
#    အလုပ် ပျက်သွားသည် — retry မရှိလို့。
#    ⇒ ယာယီ ဖြစ်နိုင်သော အမှား (404/5xx/timeout) ကို နောက်ဆုတ်ပြီး ပြန်ကြိုးစားသည်。
#    ⚠️ `/claim` ကို **ပြန်မကြိုးစားရ** — အဖြေ ပျောက်ရုံနဲ့ ပြန်ခေါ်လျှင်
#       job နှစ်ခု ယူမိနိုင်သည်。 ၄၀၀/၄၀၁/၄၀၉/၄၁၀/၄၂၂ က တကယ့် အမှား ⇒ ချက်ချင်း ထုတ်。
RETRY_CODES = (404, 408, 429, 500, 502, 503, 504)
RETRY_WAIT  = (2, 5, 12, 25, 45)

# ⚠️ slide အရှည် ချိန်ညှိချက် — **သီးသန့် function** အဖြစ် ထားသည်
#    (စမ်းသပ်လို့ ရစေရန်)。 ၂၀၂၆-၀၉-၂၀ မှာ render ထဲ တိုက်ရိုက် ရေးထားပြီး
#    အမှားကို ဗီဒီယို တစ်ပုဒ်လုံး ထုတ်ပြီးမှသာ တွေ့ရသည်。
SLIDE_GAP = 2.0     # slide နှစ်ခုကြား အနည်းဆုံး ကွာဟချက်
SLIDE_MIN = 1.0     # `card_len` ဂိတ်ရဲ့ အနိမ့်ဆုံး

# ⚠️ **မြင်ကွင်း အပိုင်းအစ ကျန်နေခြင်း** — ၂၀၂၆-၀၉-၂၀ တွေ့ရှိချက်。
#    Zin က ဝါကျ ၄ ကြောင်း ဖျက်လိုက်ရာ တခြားနေရာမှာ ရိုက်ထားသော ၇.၃s အပိုင်းရဲ့
#    **၀.၄၁s သာ ကျန်ခဲ့**ပြီး ထွက်ဗီဒီယိုမှာ ၀.၃၃s ဖျပ်ခနဲ ပေါ်ပျောက် ဖြစ်သည် —
#    ဖြတ်ချက် ချို့ယွင်းချက် ဟု မြင်ရသည် (「cut ဖြတ်တာရော quality 0」)。
#    ⚠️ **ကိုယ်တိုင် မဖျက်ရ** — Zin ရဲ့ စည်းမျဉ်း: 「user အတည်ပြုမှ ဖျက်ပေး」。
#       ⇒ တွေ့လျှင် သတိပေးရုံသာ。
SHOT_MIN = 0.60          # ဒီထက် တိုသော မြင်ကွင်းက ဖျပ်ခနဲ ဖြစ်သည်
SHOT_SCENE = 0.22        # မြင်ကွင်း ပြောင်းမှု အနိမ့်ဆုံး


def _flash_shots(path, log=None, smin=SHOT_MIN, thr=SHOT_SCENE):
    """ဖြတ်ပြီး ဗီဒီယိုထဲက **တိုလွန်းသော မြင်ကွင်း** များ ပြန်ပေးသည် [(sec, dur)]"""
    try:
        r = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", path, "-vf",
             "select='gt(scene,%.2f)',metadata=print:file=-" % thr, "-an", "-f", "null", "-"],
            capture_output=True, text=True, timeout=300)
        ts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stdout or "")]
    except Exception as e:
        if log: log("  \u26a0\ufe0f \u1019\u103c\u1004\u103a\u1000\u103d\u1004\u103a\u1038 \u1019\u1010\u102d\u102f\u1004\u103a\u1038\u1014\u102d\u102f\u1004\u103a: %s: %s" % (type(e).__name__, e))
        return []
    if not ts: return []
    try: dur = float(probe(path)["dur"])
    except Exception: dur = ts[-1]
    edges = [0.0] + ts + [dur]
    out = []
    for i in range(len(edges) - 1):
        d = edges[i+1] - edges[i]
        # ပထမနဲ့ နောက်ဆုံး အပိုင်းကို မရေရ — ဖွင့်/ပိတ် ဖြစ်တတ်သည်
        if 0 < i < len(edges) - 2 and d < smin:
            out.append((round(edges[i], 2), round(d, 2)))
    return out


# ⚠️ ရုပ်ကို **အသက်ဝင်စေရန်** တဖြည်းဖြည်း ချုံ့/ချဲ့ခြင်း (Zin ၂၀၂၆-၀၉-၂၀:
#    「smooth zoom in zoomout」)。 reference (KCN4-2hyUBM) မှာ မြင်ကွင်း
#    **၃၀.၂/မိနစ်** ပြောင်းပြီး ငါတို့မှာ **၀** ဖြစ်ခဲ့သည် — `_zooms` က
#    **ဖြတ်ချက် နေရာမှာသာ** ပြောင်းသဖြင့် ဖြတ်စရာ မရှိလျှင် ဘာမှ မလှုပ်ပါ。
# ⚠️ ကာလ ၂ ခုကို ပေါင်းထားသည် (မတူညီသော period) — တစ်ခုတည်းဆိုလျှင်
#    စက်ဆန်ပြီး ပုံသေ ခံစားရသည်。
# ⚠️ **၁.၂၅× ထက် မကျော်ရ** (proxy 2560) — ဒီကိန်းက အများဆုံး ၁.၀၅၅。
# ⚠️ **အသံကို လုံးဝ မထိရ** (`-c:a copy`) — F2 အာမခံချက် မပျက်စေရန်。
ZOOM_P1, ZOOM_P2 = 17.0, 6.5      # စက္ကန့် — အချင်းချင်း ကိန်းပြည့် မဆ
def _breathe(cutv, out, fps, amt, w, h, log=None):
    """`cutv` ကို ချောမွေ့စွာ zoom ဝင်/ထွက် လုပ်ပြီး `out` သို့ ရေးသည်。

    ⚠️ အရွယ်ကို **argument နဲ့ ပေးရမည်**。 `TH` က `render()` ရဲ့ **local**
       ဖြစ်ပြီး module global မဟုတ်သဖြင့် ဒီထဲကနေ သုံးလျှင် `NameError`
       ဖြစ်သည် — ၂၀၂၆-၀၉-၂၀ မှာ zoom တစ်ခါမှ မလုပ်ဖြစ်ခဲ့ပြီး
       try/except ထဲ ပျောက်နေခဲ့သည်。
    """
    a1 = float(amt) * 0.64
    a2 = float(amt) * 0.36
    z = (f"1+{a1:.4f}*(0.5-0.5*cos(2*PI*on/({fps}*{ZOOM_P1})))"
         f"+{a2:.4f}*(0.5-0.5*cos(2*PI*on/({fps}*{ZOOM_P2})))")
    vf = (f"zoompan=z='min(1.25,{z})':d=1:"
          f"x='iw/2-(iw/zoom/2)':y='ih*0.42-(ih/zoom*0.42)':s={w}x{h}:fps={fps}")
    ff(["ffmpeg","-v","error","-y","-i",cutv,"-vf",vf,
        "-r",str(fps),"-c:v","libx264","-preset","veryfast","-crf","18",
        "-pix_fmt","yuv420p","-c:a","copy",out])
    if log: log(f"  ရုပ် အသက်ဝင်စေရန် zoom {1.0:.2f}–{1+a1+a2:.3f}× "
                f"(ကာလ {ZOOM_P1:.0f}s + {ZOOM_P2:.1f}s)")
    return out


def _plate_decide(video, caps, cap_top, H, rc, log=None):
    """စာတန်း နောက်ခံ တိုင်းပြီး plate လိုမလို ဆုံးဖြတ်သည် — မလိုလျှင် None

    ⚠️ **`cutv` ကို မသုံးရ** — စာတန်းကို `cutv` မဖန်တီးခင် ဆောက်သည် ⇒
       `local variable 'cutv' referenced before assignment` ဖြစ်ပြီး
       **စာတန်း တစ်ခုလုံး ပျက်**ခဲ့သည် (၂၀၂၆-၀၉-၂၁ j_d651c2ef2292)。
    ⚠️ caption အချိန်တွေက source လား cut လား မသေချာသဖြင့် **အချိန်နဲ့
       မချိတ်ဘဲ** ဗီဒီယိုတစ်ခုလုံးကနေ အညီအမျှ နမူနာ ယူသည်。
       「ဒီရုပ်က စာတန်းအတွက် လင်းလွန်းသလား」ဆိုတာ မေးခွန်းဖြစ်၍
       အချိန် တိတိကျကျ မလိုပါ (နောက်ခံက တစ်ပုံစံတည်း — ၁၃/၁၃ ကျခဲ့သည်)。
    """
    if not caps or not rc.get("plan") or not video:
        return None
    try:
        import contrast as CT
    except Exception:
        return None
    top = max(0.0, min(0.98, (cap_top - int(H * 0.06)) / float(H)))
    bot = min(1.0, top + 0.20)
    fill = rc.get("cap_fill") or "#FFFFFF"
    bad = n = 0
    # ⚠️ စာတန်း **အားလုံး** မတိုင်းပါ — ၈ ခုလောက် နမူနာ ယူသည်
    #    (တစ်ခုလျှင် ffmpeg ၉ ခါ ခေါ်သဖြင့် အားလုံးဆို အချိန်ကုန်သည်)。
    try:
        _d = float(probe(video).get("dur") or 0)
    except Exception:
        return None
    if _d <= 0:
        return None
    for k in range(8):
        _t = _d * (k + 0.5) / 8.0
        m = CT.measure(video, _t, _t + 0.4, fill=fill,
                       top_pct=top, bot_pct=bot, samples=2)
        n += 1
        if not m.get("ok"):
            bad += 1
    if not n:
        return None
    if bad * 2 < n:                       # အများစု အောင်လျှင် မလိုပါ
        if log:
            log(f"  စာတန်း ကွာဟမှု · နမူနာ {n} ခုထဲ {bad} ကျ — plate မလို")
        return None
    if log:
        log(f"  စာတန်း ကွာဟမှု · နမူနာ {n} ခုထဲ **{bad} ကျ** — "
            f"အမှောင် အကွက် (α {CT.PLATE_ALPHA}) ခံသည်")
    return dict(alpha=CT.PLATE_ALPHA)


def _fit_gfx(keep, share, dur, log=None):
    """ဂရပ်ဖစ် ကတ်များကို `share` ဘောင်ရဲ့ **အလယ်** ဆီ ချိန်သည်。

    `keep` — `track()` ပြန်ပေးသော `[(at, mov, d, y0, y1)]`
    ပြန်ပေးသည် — `(keep, [မှတ်ချက်])`

    ⚠️ `hold` က ကတ်ကို **ရှည်အောင်ပဲ လုပ်နိုင်သည်**、တိုအောင် မလုပ်နိုင်ပါ
       (`dress.track`: `if hold > gdur`)。 template ရဲ့ သဘာဝ အရှည်က
       ၁.၈–၃.၀s ဖြစ်၍ ဗီဒီယို တိုလျှင် ပစ်မှတ်ထက် ကျော်သွားသည် —
       ၂၀၂၆-၀၉-၂၀: ၇၈s ဗီဒီယိုမှာ ကတ် ၉ ခု × ၂.၄s = **၀.၂၇၈** ဖြစ်ကာ
       ဘောင် ၀.၁၇–၀.၂၅ ကို ကျော်ပြီး QC ကျသည် (j_e45a95bd33ea)。
    ⚠️ ကတ်ကို ဖြတ်၍ တိုမလုပ်ရ — animation နဲ့ house fade ပျက်မည်。
       ⇒ **အရေအတွက် လျှော့ရသည်**、ကျန်တာကို အညီအမျှ ခြားထားသည်。
    ⚠️ ဘောင် အနားကို မချိန်ရ、**အလယ်** ကို ချိန်ရမည် — render drift နဲ့
       အနားမှာ ကျတတ်သည် (slide မှာ တကယ် ဖြစ်ခဲ့ဖူး)。
    """
    why = []
    if not keep or not share or dur <= 0: return keep, why
    lo, hi = float(share[0]) * dur, float(share[1]) * dur
    mid = (lo + hi) / 2.0
    tot = sum(float(k[2]) for k in keep)
    if tot <= hi:
        return keep, why
    # အလယ်နဲ့ အနီးဆုံး ဖြစ်စေမည့် အရေအတွက်ကို ရှာသည် (အရှည် မတူညီသဖြင့်
    # ပျမ်းမျှနဲ့ မတွက်ဘဲ တစ်ခုချင်း ဖယ်ကြည့်သည်)。
    cur = sorted(keep, key=lambda x: x[0])
    best = (abs(tot - mid), list(cur))
    while len(cur) > 1:
        # အညီအမျှ ခြားနေစေရန် — **အကြာဆုံးကို မဖယ်ဘဲ** အနီးကပ်ဆုံး
        # အတွဲထဲက နောက်ကျသူကို ဖယ်သည်。
        gaps = [(cur[i + 1][0] - cur[i][0], i + 1) for i in range(len(cur) - 1)]
        _, j = min(gaps)
        cur = cur[:j] + cur[j + 1:]
        t2 = sum(float(k[2]) for k in cur)
        if abs(t2 - mid) < best[0]: best = (abs(t2 - mid), list(cur))
        if t2 <= mid: break
    out = best[1]
    t2 = sum(float(k[2]) for k in out)
    if len(out) != len(keep):
        m = (f"ဂရပ်ဖစ် {len(keep)} → {len(out)} ခု "
             f"(share {tot/dur:.3f} → {t2/dur:.3f} · ပစ်မှတ် "
             f"{share[0]:.2f}–{share[1]:.2f})")
        why.append(m)
        if log: log("  " + m)
    return out, why


def _fit_slides(slides, lo, hi, cmax, dur=0.0, log=None):
    """slide များကို `[lo, hi]` ဘောင်ရဲ့ **အလယ်** ဆီ ချိန်သည်。

    slides — `[(path, at, end, layout)]` · `at` က ဖြတ်ပြီး timeline ပေါ်。
    ပြန်ပေးသည် — `(slides, [မှတ်ချက်])`

    ⚠️ ဖုံးအုပ်မှု မပြည့်တာက **အရှည်** ပြဿနာ မဟုတ်、**နေရာ** ပြဿနာ ဖြစ်တတ်သည်。
       ၂၀၂၆-၀၉-၂၀: Gemini က ၆၂s ဗီဒီယိုရဲ့ ပထမ ၁၅s ထဲမှာ slide ၃ ခုလုံး
       ပေးလိုက်သဖြင့် ဘယ်လောက် ဆွဲဆွဲ ၀.၂၆၅ သာ ရပြီး QC ကျခဲ့သည်
       (j_bd28f6df827f)。
    ⚠️ ဘောင်ရဲ့ **အလယ်** ကို ချိန်ရသည် — အနားကို ချိန်လျှင် render drift နဲ့
       ကျသည် (j_dd56e503c95c က ၀.၀၉၉/၀.၁၀)。
    ⚠️ ဖယ်တာက **နောက်ဆုံး နည်းလမ်း** — ရွှေ့လိုက်ရင် ရတတ်သည်。

    ယန္တရား — နေရာ **ကိုယ်စားလှယ် ၃ မျိုး** တွက်ပြီး ဖုံးအုပ်မှု အလယ်နဲ့
    အနီးဆုံးကို ရွေးသည် (မူရင်း · ရှေ့သို့ ဖြန့် · နောက်ပြန် ဖြန့်)。
    ခွဲခြမ်းချက် အထပ်ထပ် ရေးလျှင် တစ်ခု ပြင်တိုင်း တစ်ခု ပျက်သည် —
    ကိုယ်စားလှယ် နှိုင်းယှဉ်ချက်က တစ်ခုတည်းသော ဆုံးဖြတ်ချက် ဖြစ်သည်。
    """
    why = []
    if not slides: return slides, why
    sl0 = sorted(slides, key=lambda x: x[1])
    n   = len(sl0)
    mid = (lo + hi) / 2.0
    per = min(cmax, max(SLIDE_MIN, mid / n))
    hard = SLIDE_MIN + SLIDE_GAP          # မဖြစ်မနေ ကွာရမည့် အနည်းဆုံး
    want = per + SLIDE_GAP                # ပြည့်ပြည့် ရှည်ဖို့ လိုသော ကွာဟချက်
    top  = dur if dur > 0 else 1e9

    def _spread(step, back):
        """anchor များကို `step` ကွာအောင် — လိုအပ်မှသာ ရွှေ့သည်"""
        if back:
            t, out = top - per, []
            for it in reversed(sl0):
                v = min(it[1], t); out.append((it[0], v, it[2], it[3])); t = v - step
            out.reverse()
            return [(p, max(0.0, x), e, l) for p, x, e, l in out]
        t, out = -1e9, []
        for it in sl0:
            v = max(it[1], t + step); out.append((it[0], v, it[2], it[3])); t = v
        return out

    def _lay(anch):
        """anchor များ → slide များ (ထပ်ခြင်း · ဖိုင်ကျော်ခြင်း မရှိ)"""
        out, prev = [], -1e9
        for i, (p, at, _e, l) in enumerate(anch):
            st = max(0.0, at, prev + SLIDE_GAP)
            cap = min(top, (anch[i+1][1] - SLIDE_GAP) if i + 1 < len(anch) else top)
            en = min(st + per, st + cmax, cap)
            if en - st < SLIDE_MIN: continue
            out.append((p, st, en, l)); prev = en
        # ကျန်နေသေးလျှင် — ကန့်သတ်ချက် ခွင့်ပြုသလောက် ထပ်ဆန့် (နောက်ကနေ ရှေ့သို့)
        for _ in range(3):
            cur = sum(y - x for _p, x, y, _l in out)
            if cur >= lo - 1e-9 or not out: break
            need, grew = mid - cur, False
            for i in range(len(out) - 1, -1, -1):
                if need <= 1e-9: break
                p, x, y, l = out[i]
                cap = min(top, (out[i+1][1] - SLIDE_GAP) if i + 1 < len(out) else top)
                ny = min(x + cmax, cap, y + need)
                if ny > y + 1e-6:
                    need -= ny - y; out[i] = (p, x, ny, l); grew = True
            if not grew: break
        # ကျော်နေလျှင် — အချိုးကျ ချုံ့
        cur = sum(y - x for _p, x, y, _l in out)
        if cur > hi and out:
            k = mid / cur
            out = [(p, x, x + max(SLIDE_MIN, (y - x) * k), l) for p, x, y, l in out]
        return out

    cands = [("မူရင်း", _lay(sl0))]
    if n > 1:
        cands.append(("ရှေ့သို့ ဖြန့်",   _lay(_spread(want, False))))
        cands.append(("နောက်ပြန် ဖြန့်", _lay(_spread(want, True))))
        cands.append(("ရှေ့သို့ (အနည်းဆုံး)", _lay(_spread(hard, False))))
        # ⚠️ **နောက်ဆုံး နည်းလမ်း** — ဗီဒီယို တစ်ခုလုံးမှာ ညီညာ ဖြန့်。
        #    slide က ကိုယ့်ဝါကျနဲ့ အများဆုံး ကွာသွားမည် ဖြစ်၍ `_score` က
        #    အခြားနည်း ဘောင်ထဲ **မဝင်မှသာ** ဒါကို ရွေးသည်。
        #    (anchor ၂ ခု အစမှာ စုပြီး ၁ ခု အဆုံးမှာ — ကျပန်း ၃၀၀၀ မှ ၁၂ ကြိမ်)
        _ev = (top - per) / float(n - 1)
        if _ev >= hard:
            cands.append(("ညီညာ ဖြန့်",
                          _lay([(p, i * _ev, e, l)
                                for i, (p, _a, e, l) in enumerate(sl0)])))

    def _score(out):
        """ဘောင်ထဲ ဝင်တာ ဦးစားပေး ⇒ အလယ်နဲ့ နီးတာ ⇒ ရွှေ့တာ နည်းတာ"""
        tot = sum(y - x for _p, x, y, _l in out)
        inb = 0 if (lo - 1e-9 <= tot <= hi + 1e-9) else 1
        return (inb, abs(tot - mid), -len(out))

    name, best = min(cands, key=lambda c: _score(c[1]))
    moved = sum(1 for (p, x, _y, _l) in best
                for (p2, a2, _e2, _l2) in sl0 if p2 == p and abs(x - a2) > 0.01)
    if name != "မူရင်း":
        why.append(f"slide နေရာ {name} — နေရာ စုနေ၍ ({moved}/{n} ရွှေ့)")
    if len(best) < n:
        why.append(f"slide ဖယ် {n - len(best)} ခု — နေရာ မလောက်၍")
    if best:
        why.append(f"slide {len(best)} ခု · အရှည် "
                   f"{min(y-x for _p,x,y,_l in best):.1f}–{max(y-x for _p,x,y,_l in best):.1f}s "
                   f"→ ဖုံးအုပ်မှု {sum(y-x for _p,x,y,_l in best)/max(dur,1e-9):.3f}")
    return best, why


# ⚠️ **overlay တိုင်းမှာ fade ပါရမည်**。 ၂၀၂၆-၀၉-၂၀: B-roll နဲ့ slide ကို
#    `enable='between(...)'` သီးသန့်နဲ့ တင်ထားသဖြင့် **ချက်ချင်း ပေါ်၊ ချက်ချင်း
#    ပျောက်** ဖြစ်ကာ ၆၂s ဗီဒီယိုမှာ ရုတ်တရက် ပြောင်းမှု ၁၆ ခု (၁၅.၅/မိနစ်)
#    ဖြစ်ခဲ့သည် — ဖြတ်ချက်က ၄ ခုပဲ ရှိသည်。 Zin: 「quality 0 · ပရီမီယံ ဆန်အောင်」。
#    တန်ဖိုးများက house စံ (`motionkit/fade.py`) — panel/card ၀.၂၂ ဝင် ၀.၁၈ ထွက် ·
#    အနည်းဆုံး ၀.၀၈ (ဘယ်တော့မှ မပေါက်ကွဲရ) · layer ကြာချိန်ရဲ့ ၄၅% ထက် မပိုရ。
FADE_IN, FADE_OUT, FADE_MIN, FADE_CAP = 0.22, 0.18, 0.08, 0.45


# ⚠️ **ဘောင်အပြည့် slide ကို မငြိမ်စေရ**。 ၂၀၂၆-၀၉-၂၀ တိုင်းချက်: ထွက်ဗီဒီယိုရဲ့
#    frame **၃၃% က လုံးဝ မလှုပ်** — slide တစ်ခု ၁၀.၅s ငြိမ်နေလို့。 Zin:
#    「Annimation Motion Effect တွေလဲ ပါမလားဘူး」。 ဖြေရှင်းချက် — အနည်းငယ်
#    ချဲ့ပြီး **တဖြည်းဖြည်း ရွှေ့** (Ken Burns)。
# ⚠️ `zoompan` ကို **မသုံးရ** — `-loop 1` နဲ့ တွဲလျှင် `on` က input frame
#    တိုင်း ပြန်စ၍ **ဘာမှ မလှုပ်**ပါ (ပထမ↔နောက်ဆုံး frame ကွာဟ ၀.၀၀ —
#    တကယ် တိုင်း၍ တွေ့)。 `crop` ရဲ့ `w`/`h` ကလည်း frame တိုင်း မတွက်နိုင် —
#    `x`/`y` သာ ရသည် ⇒ **အရင် ချဲ့ပြီး crop ကို ရွှေ့**ရသည်。
# ⚠️ **တဖြည်းဖြည်း ရွှေ့တာ (drift) က မလုံလောက်**。 ၂.၅% ကို ၁၀.၅s ခွဲလျှင်
#    frame တစ်ခုလျှင် **၀.၀၈px** သာ ရွှေ့ပြီး မျက်စိနဲ့ မမြင်ရ (တိုင်းချက်:
#    မလှုပ်သော frame ၁၀၀% → ၉၀% သာ)。 မြင်ရလောက်အောင် မြန်စေလျှင်
#    slide ရဲ့ အနားလွတ် (၁၁၈px) ကုန်သည်。
# ⇒ **ဝင်လာချိန်မှာ အောက်ကနေ တက်လာစေ**သည် — ဖတ်နေချိန် ငြိမ်နေတာက
#    ပုံမှန်、ဝင်လာချိန်မှာသာ လှုပ်ရှားမှု လိုသည် (ပရော် presentation ပုံစံ)。
RISE_PX = 44          # ဘယ်လောက် အောက်ကနေ တက်မလဲ
RISE_S  = 0.38        # ဘယ်လောက်ကြာ တက်မလဲ


def _rise(a, px=RISE_PX, d=RISE_S):
    """overlay ရဲ့ y — ဝင်လာချိန် `px` အောက်ကနေ `d` စက္ကန့်နဲ့ တက်လာသည်。"""
    if not px or px <= 0: return None
    return (f"'if(lt(t-{a:.2f},{d:.2f}),"
            f"{px}*(1-(t-{a:.2f})/{d:.2f}),0)'")


def _cap_stroke(rc, TH):
    """စာတန်း အနားသတ် အရောင် — `"brand"` ဆိုလျှင် brand theme ကနေ ယူသည်。

    ⚠️ brand ရဲ့ အနက်ရောင်ကို ရှေ့ဆုံး ဦးစားပေးသည် (NAVY → DEEP → INK)。
       မတွေ့လျှင် `None` — အနားသတ် မထည့်ဘဲ ဆက်သွားသည် (job မကျစေရန်)。
    """
    v = rc.get("cap_stroke") or rc.get("stroke")
    if not v: return None
    if str(v).strip().lower() != "brand": return v
    for k in ("NAVY", "DEEP", "INK", "BLACK"):
        c = (TH or {}).get(k)
        if isinstance(c, str) and c.startswith("#") and len(c) == 7:
            return c
    return None


# ⚠️ **ဘောင်အပြည့် B-roll က ဖြတ်ချက် ဖြစ်ရမည် — dissolve မဟုတ်**。
#    ၂၀၂၆-၀၉-၂၁ တိုင်းချက် (reference ၄ ပုဒ် · ၂၀fps) —
#      reference ရဲ့ ပြောင်းလဲမှု ကြာချိန် အလယ်တန်း **၀.၀၅s** (ဖရိမ်း ၁ ခု)
#      IKKI ရဲ့                                   **၀.၁၅s** (၃ ဆ)
#    ⇒ ပြောသူနဲ့ B-roll **နှစ်ခုလုံး တစ်ပြိုင်တည်း မြင်ရ** (double exposure)
#      ဖြစ်ပြီး amateur ဆန်သည်。 Zin ကိုယ်တိုင် ပုံမှာ တွေ့ခဲ့သည်。
# ⚠️ overlay ဂရပ်ဖစ် (ကတ်/စာသား) မှာတော့ fade **လိုသည်** — အဲဒါက
#    ချက်ချင်း ပေါက်ကွဲလျှင် ပိုဆိုးသည် (၂၀၂၆-၀၉-၂၀ Zin: 「quality 0」)。
#    ⇒ B-roll နဲ့ overlay ကို **ခွဲရမည်**。
BROLL_FADE = 0.05     # reference အတိုင်း — ဖရိမ်း ၁–၂ ခု


def _fade(src, dst, a, b, hard=False):
    """overlay input ကို fade တပ်ပြီး ပြန်ပေးသည် — `-itsoffset` သုံးထားသဖြင့်
    input ရဲ့ အချိန်မှတ်က main timeline နဲ့ တူသည် ⇒ `st` ကို တိုက်ရိုက် ပေးရသည်。"""
    d = max(0.1, float(b) - float(a))
    if hard:
        # ⚠️ ပေါက်ကွဲသံ မဖြစ်စေရန် ဖရိမ်း ၁–၂ ခု သာ ထားသည် — dissolve မဟုတ်
        fi = fo = min(BROLL_FADE, d * 0.2)
    else:
        fi = max(FADE_MIN, min(FADE_IN,  d * FADE_CAP))
        fo = max(FADE_MIN, min(FADE_OUT, d * FADE_CAP))
    if fi + fo > d: fi = fo = d / 2.0
    # ⚠️ fade-out ကို `enable` ပိတ်ချိန် **မတိုင်ခင် ပြီးအောင်** ထားရမည်。
    #    အတိအကျ `b` မှာ ဆုံးအောင် ထားလျှင် gate က alpha ၀ မရောက်ခင်
    #    ဖြတ်လိုက်ပြီး ၂၅၃ → ၁၅၁ → ၀ ဟု **ခုန်ချ**သည် (တကယ် တိုင်း၍ တွေ့)。
    TAIL = 0.10
    st_out = max(a + fi, b - fo - TAIL)
    return (f"[{src}]format=yuva420p,"
            f"fade=t=in:st={a:.2f}:d={fi:.2f}:alpha=1,"
            f"fade=t=out:st={st_out:.2f}:d={fo:.2f}:alpha=1[{dst}]")


def req(path, data=None, method=None, raw=False):
    url = API + path
    body = None if data is None else json.dumps(data).encode()
    once = "/claim" in path
    last = None
    for i in range(1 if once else len(RETRY_WAIT) + 1):
        r = urllib.request.Request(url, data=body,
                                   method=method or ("POST" if body else "GET"))
        r.add_header("Authorization", "Bearer " + TOKEN)
        if body: r.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(r, timeout=120) as f:
                return f.read() if raw else json.loads(f.read() or b"{}")
        except urllib.error.HTTPError as e:
            if e.code not in RETRY_CODES: raise
            last = e
        except (urllib.error.URLError, OSError) as e:
            last = e
        if once or i >= len(RETRY_WAIT): break
        w = RETRY_WAIT[i]
        print(f"  ⚠️ API ယာယီ မရ ({type(last).__name__}: {last}) — "
              f"{w}s နောက် ပြန်ကြိုးစားမည် ({i+1}/{len(RETRY_WAIT)}) · {path}",
              flush=True)
        time.sleep(w)
    raise last

class ReviewStop(Exception):
    """ASR + ဖြတ်မှတ် တွက်ပြီးလျှင် **ရပ်**ပြီး သုံးစွဲသူကို ပြရန်。

    ⚠️ ဗီဒီယို မထုတ်ရသေး。 ဘယ်စာလုံး ကျန်မလဲ ဆိုတာ သုံးစွဲသူသာ သိသည် —
       app က ကိုယ့်ဘာသာ ဖြတ်လျှင် "လုံးဝ အဆင်မပြေဘူး" ဖြစ်သည် (Zin)。
    """
    def __init__(self, segs, plan):
        self.segs, self.plan = segs, plan
        super().__init__("review")


def ff(args, what="ffmpeg"):
    """ffmpeg ကို ခေါ်ပြီး **ကျဘမ်းဖြစ်လျှင် အကြောင်းရင်းကို ပါလာစေသည်**。

    ⚠️ အရင်က `subprocess.run(..., check=True)` သာ သုံးခဲ့သဖြင့် ကျဘမ်းဖြစ်လျှင်
       `CalledProcessError` က **command ရှည်ကြီးကိုသာ** ပြပြီး ffmpeg ရဲ့
       အမှားစာသား လုံးဝ မပါခဲ့。 ⇒ disk ပြည့်လား · input များလွန်းလား ·
       filter မှားလား **ခွဲလို့ မရဘဲ** မှန်းရသည် (တကယ် ဖြစ်ခဲ့: exit 228)。
    """
    r = subprocess.run(args, capture_output=True)
    if r.returncode:
        err = (r.stderr or b"").decode("utf-8", "replace").strip()
        tail = " / ".join(x for x in err.splitlines()[-4:] if x.strip())[:400]
        free = free_gb()
        raise RuntimeError(f"{what} ကျဘမ်း (exit {r.returncode} · disk ကျန် "
                           f"{free:.1f} GB): {tail or 'အမှားစာသား မရ'}")
    return r


def probe(p):
    o = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height,r_frame_rate","-show_entries","format=duration",
        "-of","json",p], capture_output=True, text=True).stdout
    j = json.loads(o); s = j["streams"][0]; n,d = s["r_frame_rate"].split("/")
    return dict(w=s["width"], h=s["height"], fps=float(n)/float(d),
                dur=float(j["format"]["duration"]))

def faceband(src, W, H, log=print, n=6):
    """ရုပ်ထဲက **မျက်နှာ/အသား ဇုန်** (output pixel y0,y1) — မရလျှင် None。

    ⚠️ ဂရပ်ဖစ်က မျက်နှာပေါ် ကျလျှင် ဗီဒီယိုက ပျက်သည် (Zin: "မျက်နှာကို
       မဖုန်းစေနဲ့")。 ⇒ အသားအရောင် mask ဖြင့် တိုင်းပြီး ရှောင်ခိုင်းသည်。
    ⚠️ output က ဗဟို crop ဖြစ်၍ **crop ပြီးမှ** တိုင်းရမည် — အပြည့်တိုင်းလျှင်
       အချိုး လွဲသည်。
    """
    try:
        import numpy as np
        from PIL import Image
    except Exception:
        return None
    d = probe(src)["dur"]
    ys = []
    for i in range(n):
        t = d*(i+0.5)/n
        q = os.path.join(os.path.dirname(src), f"_fb{i}.png")
        try:
            subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{t:.2f}","-i",src,
                "-frames:v","1","-vf",
                f"crop='min(iw,ih*{W}/{H})':ih,scale=480:-1", q], check=True)
            a = np.asarray(Image.open(q).convert("RGB")).astype(np.int32)
        except Exception:
            continue
        h, w = a.shape[:2]
        R, G, B = a[:,:,0], a[:,:,1], a[:,:,2]
        mk = (R>95)&(G>45)&(B>25)&(R>G+12)&(G>B)&((R-B)>18)&(R<250)
        mk[int(h*0.62):] = False              # လက်/ခန္ဓာအောက်ပိုင်း ဖယ်
        rows = np.nonzero(mk.sum(axis=1) > w*0.02)[0]
        if len(rows) < 8: continue
        ys.append((rows.min()/h, rows.max()/h))
    if not ys: return None
    a0 = min(y[0] for y in ys); a1 = max(y[1] for y in ys)
    pad = 0.03
    y0 = max(0, int((a0-pad)*H)); y1 = min(H, int((a1+pad)*H))
    log(f"  မျက်နှာဇုန် y {y0}–{y1} ({a0:.2f}–{a1:.2f}·H) — ဂရပ်ဖစ် ရှောင်မည်")
    return (y0, y1)




def _outdur_guess(spans):
    """ဖြတ်ပြီး ထွက်မည့် အရှည် — span ပေါင်းလဒ်"""
    try:
        return float(sum(b - a for a, b in (spans or [])))
    except Exception:
        return 0.0


def _pop_ink(mov, work, idx):
    """pop clip ရဲ့ **တကယ့် အလျားလိုက် နယ်နိမိတ်** `(x0, x1)` — မရလျှင် None

    ⚠️ စာလုံးရေနဲ့ ခန့်မှန်းလျှင် မလုံလောက်ပါ — ဖောင့် · စာလုံးအရွယ် ·
       မြန်မာ ဗျည်းတွဲ အားလုံး သက်ရောက်သည်。 ထွက်လာသော alpha ကနေ တိုင်းသည်。
    ⚠️ **ငြိမ်သွားပြီးမှ** တိုင်းရမည် — ဝင်လာစ frame မှာ ချုံ့ထားသေးသဖြင့်
       အကျယ် မမှန်ပါ (animation)。 ⇒ နောက်ပိုင်း frame ကို ယူသည်。
    """
    import numpy as _np
    png = os.path.join(work, f"wink{idx:02d}.png")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.6",
                        "-i", mov, "-frames:v", "1", "-pix_fmt", "rgba", png],
                       capture_output=True)
    if r.returncode or not os.path.exists(png):
        return None
    try:
        from PIL import Image
        a = _np.asarray(Image.open(png).convert("RGBA"))
        cols = _np.nonzero((a[..., 3] > 40).any(axis=0))[0]
        return (int(cols.min()), int(cols.max())) if len(cols) else None
    finally:
        try: os.unlink(png)
        except OSError: pass


def _vbr(w, h, fps=30):
    """အရွယ်အလိုက် bitrate — `"24M"` ပုံစံ

    ⚠️ အရင်က အရွယ်တိုင်း **16M အဖြစ် ဖြစ်ခဲ့သည်**。 1080p အတွက် များပြီး
       4K (ပိုက်ဆယ် ၄ ဆ) အတွက် **လုံးဝ မလောက်** — block artifact ထွက်မည်。
       ⇒ pixel/စက္ကန့် နှုန်းနဲ့ တွက်သည် (၁၀၈၀p30 ≈ ၁၆M အဆင့် ထိန်း)。
    """
    px = float(w) * float(h) * max(1.0, float(fps or 30))
    mb = px * 16.0 / (1920.0 * 1080.0 * 30.0)
    return f"{max(8, min(60, int(round(mb))))}M"


def _pxname(jid, speed=1.0):
    """proxy ဖိုင်ရဲ့ လမ်းကြောင်း — **အရှိန် အလိုက် ကွဲပြားရမည်**。

    ⚠️ ၂၀၂၆-၀၉-၂၁: နာမည် တစ်ခုတည်း (`{jid}_px.mp4`) ဖြစ်သဖြင့် ၁.၀၀× နဲ့
       ထုတ်ပြီးသား proxy ရှိနေလျှင် သုံးစွဲသူက ပြန်ပြင်ပြီး ၁.၀၃× ရွေးလိုက်ရာ
       `_have_px` က `True` ဖြစ်ကာ **retiming ကို တိတ်တဆိတ် ကျော်**သည် —
       ရွေးထားတာက ၁.၀၃× ဖြစ်ပါလျက် ၁.၀၀× ထွက်မည်。 သုံးစွဲသူ ဘယ်တော့မှ
       မသိရ (「တိတ်တဆိတ် မကျရ」)。
    ⚠️ အတည်ပြုပြီး ပြန်ထုတ်ချိန်မှာတော့ proxy က **အဲဒီအရှိန်နဲ့** ဆောက်ထားပြီး
       ဖြစ်၍ နာမည် ကိုက်သည် ⇒ ထပ်မြှင့်မိခြင်း (double speed) မဖြစ်ပါ。
    """
    try: s = float(speed or 1.0)
    except (TypeError, ValueError): s = 1.0
    tag = "" if abs(s - 1.0) < 0.001 else "_s%d" % int(round(s * 100))
    return os.path.join(BIG, "%s_px%s.mp4" % (jid, tag))


def render(job, brand, src, out, stage, log=print, over=None):
    """တကယ့် pipeline — stage ၂–၆ က နေရာချထားရုံ မဟုတ်တော့。"""
    import theme, infogfx as IG, titles2 as T2, titles as T1
    import recipes as RC, cut as CUT, spans as SP, captions as CP, qc as QC, asr as ASR
    import clean as CL, dress as DR, music as MU, scrim as SC, topics as TP
    import broll as BR
    import measure as M2
    import formats as FM
    import sfxlib as SL
    # ⚠️ motionkit မှာလည်း render.py ရှိ၍ spans.py ဟု နာမည် ခွဲထားသည်

    # ⚠️ ပုံစံ ပြင်ချက် (Style စာမျက်နှာက) ကို ထည့်သည် — API က ဘောင်စစ်
    #    ပြီးသား ဖြစ်ပေမယ့် worker မှာလည်း **ထပ်စစ်**သည် (RC.apply ထဲ)。
    over = dict(over or {})
    # Pipeline-only controls are not recipe overrides.  Keep the recipe
    # allow-list strict while retaining source-take labels for review.
    take_map = over.pop("_take_map", None) or []
    over.pop("_sources", None)
    try: speech_speed = float(over.pop("_speech_speed", 1.0) or 1.0)
    except (TypeError, ValueError): speech_speed = 1.0
    over.pop("_speed_applied", None)
    # ⚠️ `_drop` က recipe ပြင်ချက် **မဟုတ်** — သုံးစွဲသူ ဖျက်ထားသော အချိန်
    #    အပိုင်းများ။ `RC.clean()` က မသိသော key ကို ဖြုတ်ပစ်သဖြင့် အရင် ခွဲထုတ်ရမည်。
    user_drop = over.pop("_drop", None) or []
    # ⚠️ `_drop_exact` — review မှာ **သုံးစွဲသူ လက်ခံထားသော ပြန်စ** အပိုင်း。
    #    retakes() က စကား နယ်နိမိတ် (M.speech ± edge / gap အလယ်) နဲ့ တွက်ပြီးသား
    #    ⇒ **snap မလုပ်ရ** (snap လျှင် စကား အစွန်းအထိ ရွှေ့ပြီး F2 အာမခံချက် ပျက်)。
    user_drop_exact = over.pop("_drop_exact", None) or []
    rc = RC.apply(job.get("recipe"), over)
    # ⚠️ template ရွေးချယ်မှုကို **job အလိုက် ကွဲပြားစေရန်** seed ပေးသည် —
    #    မပေးလျှင် ဗီဒီယိုတိုင်း တူညီသော template ၁၀ ခုပဲ ထွက်သည်
    #    (pool ၂၈၄ ခု ရှိပါလျက် · ၂၀၂၆-၀၉-၁၉ Zin တွေ့)。
    rc["_seed"] = job.get("id") or ""
    if over:
        log("  ပုံစံ ပြင်ချက် " + " · ".join(f"{k}={v}" for k, v in sorted(over.items())))
    import fonts as FN
    # ⚠️ ဖောင့် အစီအစဥ်: **သုံးစွဲသူ ရွေးတာ > brand ရဲ့ ဖောင့် > recipe ပုံသေ**。
    #    brand ကို ကိုယ်ပိုင် ဆောက်ထားလျှင် အဲဒီဖောင့်က recipe ကို အစားထိုးရမည် —
    #    မဟုတ်လျှင် ဘရန်း ဆောက်တာ အလကား ဖြစ်သည်。
    bmmf = ((brand or {}).get("mmf") or "").strip()
    if bmmf and FN.ok(bmmf) and (brand or {}).get("id") not in ("zae", "zjl"):
        rc["mmf"] = bmmf
    # ⚠️ ဗီဒီယိုတစ်ခုချင်း စာတန်း အရွယ် ရွေးထားလျှင် **အဲဒါက အထက်တန်း**
    jcap = (job.get("cap") or "").strip()
    if jcap and jcap in RC.CAPSIZE:
        rc["cap_pct"] = RC.CAPSIZE[jcap][0]
        log(f"  စာတန်း အရွယ် · သုံးစွဲသူ ရွေး {jcap} ({rc['cap_pct']})")
    jf = (job.get("font") or "").strip()
    if jf:
        if FN.ok(jf): rc["mmf"] = jf
        else: log(f"  ⚠️ ဖောင့် '{jf}' စာရင်းထဲ မရှိ — ပုံသေ သုံးသည်")
    # ⚠️ **render မစမီ motionkit ရဲ scratch ကို ရှင်းရမည်**。 template တစ်ခု
    #    ဆောက်တိုင်း PNG ၆၀–၂၀၀ ထွက်ပြီး ဘယ်သူမှ မဖျက်ခဲ့— ၂၀၂၆-၀၉-၂၁ မှာ
    #    **၁၁ GB** စုမိပြီး Mac ရဲ disk ပြည့်ကာ render တွေ ကျခဲ့သည်。
    try:
        import gfxcat as _GC
        _GC.gc_work(log=log)
    except Exception as _e:
        log(f"  ⚠️ motionkit work/ မရှင်းနိုင် ({type(_e).__name__})")
    m  = probe(src)
    stage(1, "ingest")
    log(f"  {m['w']}×{m['h']} · {m['fps']:.0f}fps · {m['dur']:.1f}s · {rc['label']} · ဖောင့် {rc['mmf']}")
    work = os.path.join(SCRATCH, job["id"] + "_w"); os.makedirs(work, exist_ok=True)

    # ⚠️ proxy ကို `force_original_aspect_ratio=increase` နဲ့ **မလုပ်ရ** —
    #    အဲဒါက ဘောင်ကို **ဖုံးအောင် ချဲ့**သည်。 3840×2160 ကို 2160×2880 ဘောင်
    #    ဖုံးရန် 5120×2880 ဖြစ်သွားပြီး videotoolbox ရဲ့ ကန့်သတ် (4096) ကျော်၍
    #    encoder မပွင့်ဘူး (တကယ် ဖြစ်ခဲ့ · exit 187)。
    #    ⇒ အရွယ်ကို python နဲ့ တွက်ပြီး **ချုံ့ရုံသာ** လုပ်သည်。
    import theme as _th; _th.use(rc["theme"]); _TH = _th.t()
    # ⚠️ **proxy က ထွက်အရည်အသွေးကို ကန့်သတ်သည်** — `src = px` ဖြစ်၍ pipeline
    #    တစ်ခုလုံးက proxy ပေါ်မှာ ပြေးသည်。 LONG=2560 တစ်ခုတည်း ထားလျှင်
    #    သုံးစွဲသူက **4K ရွေးထားသည့်တိုင် 2560 ကနေ ချဲထွက်**မည် — အတု 4K。
    #    ⇒ ပစ်မှတ် format ရဲ အရွယ်ကို ကြည့်ပြီး ကန့်သတ်ကို တင်သည်。
    # ⚠️ videotoolbox ရဲ အကျယ် ကန့်သတ်က **4096** — 3840 ဝင်သည်。
    _fk = (job.get("fmt") or "").strip()
    _fd = FM.FORMATS.get(_fk) or {}
    LONG = max(2560, int(_fd.get("W") or 0), int(_fd.get("H") or 0))
    LONG = min(LONG, 3840)           # videotoolbox 4096 အောက်
    heavy = (m["w"]*m["h"]*max(1,m["fps"])) > (1920*1080*30)*1.6
    if LONG > 2560:
        log(f"  4K ထွက်ရန် ({_fk}) ⇒ proxy ကန့်သတ် {LONG} "
            f"(ပုံသေ 2560 မဟုတ်)")
    if heavy and max(m["w"], m["h"]) > LONG:
        sc = LONG/float(max(m["w"], m["h"]))
        pw = int(m["w"]*sc)//2*2; ph = int(m["h"]*sc)//2*2
        # ⚠️ proxy ကို **work/ ထဲ မထားရ** — retry မှာ ပြန်သုံးလို့ရအောင်
        #    scratch ရဲ့ အပြင်မှာ ထားသည် (`handle()` က ရှာသည်)。
        px = _pxname(job["id"], speech_speed); t_px = time.time()
        subprocess.run(["ffmpeg","-v","error","-y","-i",src,
            "-vf",f"scale={pw}:{ph}","-r",str(rc["fps"]),
            "-c:v","h264_videotoolbox","-b:v",_vbr(pw, ph, rc["fps"]),
            "-c:a","aac","-b:a","192k",px],check=True)
        log(f"  proxy {m['w']}×{m['h']}@{m['fps']:.0f} → {pw}×{ph}@{rc['fps']} · {time.time()-t_px:.0f}s")
        src = px; m = probe(src)

    # ── ② စကား → စာသား ──────────────────────────────────────
    stage(2, "transcribe")
    wav = os.path.join(work, "a.wav")
    subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-vn","-ar","16000","-ac","1",wav], check=True)
    # ⚠️ **တိတ်ဆိတ်မှု မြေပုံကို တစ်ခါပဲ တွက်ရမည်**。 အရင်က ၃ နေရာ သီးသန့်
    #    တွက်ခဲ့သည် — `asr.burmese()` (band/gaps) · `cut.plan()` (speech) ·
    #    `_sil_of()` (band/gaps)。 algorithm ကိုက မတူသဖြင့် ASR က မြေပုံ A
    #    ပေါ် snap လုပ်ပြီး cut က မြေပုံ B သုံးမိနိုင်သည်。
    #    ⇒ စံ = `measure.speech()` · ASR · cut · dress သုံးခုလုံး ဤတစ်ခုကို မျှသုံး。
    import measure as _M
    MEAS = _M.speech(wav)
    # ⚠️ **စွမ်းအင် မြေပုံ** — ဖြတ်မှတ်ကို တိတ်ဆိတ်မှု မရှိရာမှာ အနိမ့်ဆုံးမှတ်ဆီ
    #    ဆွဲသွင်းရန် (`CUT.quiet_at`)。 `speech()` က ထဲမှာ `analyse()` ခေါ်ပြီးသား
    #    ဖြစ်သော်လည်း ပြန်မပေး၍ ဒီမှာ တစ်ခါ ထပ်ခေါ်ရသည် (~၁s)。
    try:
        _db, _vc, _du = _M.analyse(wav)
        _DBTRACK = (_db, (_du / len(_db)) if len(_db) else 0.0)
    except Exception as _e:
        _DBTRACK = (None, 0.0); log(f"  ⚠️ စွမ်းအင် မြေပုံ မရ: {type(_e).__name__}: {_e}")
    log(f"  တိတ်ဆိတ်မှု မြေပုံ · စကား {len(MEAS[0])} · တိတ် {len(MEAS[1])} · "
        f"{MEAS[2]:.1f}s · cls={MEAS[4]}")
    # ⚠️ စာသား ပေးလာလျှင် **ASR ပြန်မလုပ်ရ** — ဒါက "ပြန်ထုတ်တာ မြန်တယ်"
    #    ဆိုတဲ့ ကတိရဲ့ အခြေခံပါ。 Gemini call လည်း မကုန်ဘူး。
    pre_segs = job.get("segs")
    if isinstance(pre_segs, str):
        try: pre_segs = json.loads(pre_segs)
        except Exception: pre_segs = None
    if pre_segs:
        segs = pre_segs
        # ⚠️ `fix` = သုံးစွဲသူ ပြင်ထားသော **စာတန်းစာလုံး**。 အသံနဲ့ ဖြတ်မှတ်ကို
        #    မထိ — ASR မှားဖတ်တာကို ပြင်ဖို့ (မြန်မာစာမှာ မကြာခဏ)。
        _nfix = sum(1 for x in segs if isinstance(x, dict) and x.get("fix"))
        for x in segs:
            if isinstance(x, dict) and x.get("fix"):
                x["text"] = x["fix"]
        log(f"  စာသား ပေးလာသည် {len(segs)} ကြောင်း — ASR ကျော်သွားသည်"
            + (f" · စာလုံး ပြင်ချက် {_nfix} ကြောင်း" if _nfix else ""))
    else:
        lang = (job.get("lang") or "my")
        # ⚠️ ချိန်ညှိချက်ကို **calib ကနေ** ယူသည် — code ထဲ မရေးရ (R5)。
        _ac = (CUT.calib(job.get("brand_id") or rc.get("theme")) or {}).get("asr_align")
        segs = ASR.run(wav, lang=lang, log=log, meas=MEAS, align_cfg=_ac)
        # ⚠️ `bias fallback %` — ပြန်စ ရှာဖွေမှုရဲ့ တိကျမှုနဲ့ ဆက်စပ်နေသည်
        #    (၁၃%→၉၇.၁ · ၁၅%→၉၆.၇ · ၁၇%→၉၃.၃ · ၅၁%→၇၉.၆ · ၂၀၂၆-၀၉-၁၆ · n=၄)。
        #    ⚠️ **ဂိတ်အဖြစ် မသုံးရသေး** — နယ်နိမိတ် မသိ (၁၇–၅၁% ကြား ဒေတာ မရှိ)。
        #    job တိုင်း မှတ်ထားလျှင် နောက်ပိုင်း user ကို မမေးဘဲ ချိန်နိုင်မည်。
        _tm = ASR.STAT.get("timed") or 0
        REPORT["bias_pct"] = round(100.0 * (ASR.STAT.get("biased") or 0) / _tm, 1) if _tm else None
        REPORT["asr_stat"] = dict(ASR.STAT)
        if _ac:
            log(f"  ASR align · bias {_ac.get('bias_s')}s · W {_ac.get('window_s')}s "
                f"(calib) · snap {ASR.STAT.get('snapped','—')}/{ASR.STAT.get('reach','—')} "
                f"ရနိုင် (ဝါကျ {ASR.STAT.get('timed','—')}) · "
                f"bias fallback {REPORT['bias_pct']}%")
        else:
            log(f"  ⚠️ ASR align · calib မရှိ — "
                + ("ဒီဖိုင်ကနေ bias တိုင်းယူသည် "
                   f"{ASR.STAT.get('bias_s')}s (တွဲ {ASR.STAT.get('bias_pairs')})"
                   if ASR.STAT.get('bias_src') == 'measured' else
                   f"တွဲ {ASR.STAT.get('bias_pairs')} ခုသာ ရ၍ **အတည် မပြုရသေးသော** "
                   f"ကိန်း {ASR.STAT.get('bias_s')}s ကို သုံးသည်")
                + f" · snap {ASR.STAT.get('snapped','—')}/{ASR.STAT.get('reach','—')} ရနိုင်")

    # Source labels are metadata only.  The engine never assumes which Raw 1 /
    # Raw 2 attempt is better; the user sees it in the transcript and decides.
    if take_map:
        for sg in segs:
            try: mid = (float(sg.get("start", 0)) + float(sg.get("end", 0))) / 2.0
            except (TypeError, ValueError): continue
            for tk in take_map:
                try: inside = float(tk.get("start", 0)) <= mid <= float(tk.get("end", 0)) + 0.04
                except (TypeError, ValueError): inside = False
                if inside:
                    sg["take"] = int(tk.get("take") or 0) or None
                    sg["source"] = str(tk.get("source") or f"Take {sg.get('take')}")
                    break

    # ── glossary ထွက်စာလုံး — **ဆိုးကျိုးကို မမြင်ရဘဲ မထားရ** (render report) ──
    try:
        REPORT["gloss"] = ASR.gloss_audit(segs)
        _ga = REPORT["gloss"]
        if _ga:
            log("  glossary " + ("ဖွင့်" if _ga["enabled"] else "ပိတ်") + " · " +
                " · ".join(f"{k} {v['exact']}" + (f" (ကွဲ {sum(v['variants'].values())})" if v['variants'] else "")
                           for k, v in _ga["terms"].items()) +
                f" · CJK {len(_ga['cjk'])}")
    except Exception as _e:
        REPORT["gloss"] = None
        log(f"  ⚠️ glossary စစ်မရ: {_e}")

    # ── ③ ဖြတ်တောက် — တိုင်းထားသော တိတ်ဆိတ်မှုထဲမှာသာ ─────────
    stage(3, "cut")
    # ⚠️ `_bid` ကို branch နှစ်ခုလုံးအတွက် **ဒီမှာတင်** သတ်မှတ်ရမည် —
    #    အောက်မှာ (fade) ပြန်သုံးသဖြင့် (၂၀၂၆-၀၉-၁၈)。
    _bid = (job.get("brand_id") or rc["theme"])
    if rc["keep_pause"] is None:
        spans=[(0.0, m["dur"])]; cuts=[]; st={"cuts":0,"in_speech":0,"removed":0.0}
        log("  ⚠️ ဤ recipe က ဖြတ်တောက် မလုပ် (အနားယူချိန် ချန်ထားသည်)")
    else:
        spans, cuts, st = CUT.plan(wav, meas=MEAS, keep_pause=rc["keep_pause"],
                                   min_sil=rc["min_sil"], brand=_bid)
        log(f"  ဖြတ် {st['cuts']} · ဖြုတ် {st['removed']:.1f}s "
            f"({st.get('removed_ratio',0):.1%}) · စကားထဲ {st['in_speech']}/{st.get('points',0)}"
            f" · တိတ်ဆိတ်မှု {st.get('silences',0)} · thr {st.get('thr')}dB")
        _ev = st.get("ev") or {}
        log(f"  {st.get('cls','?')} · p95 {_ev.get('p95_db')} · range {_ev.get('range_db')}"
            f" · voice {_ev.get('voice_ratio')}"
            f" · ဖြတ်မှတ် {st.get('cut_threshold')}s pad {st.get('pad')}s "
            + (f"[ချိန်ညှိပြီး · {st.get('calib_src')}]" if st.get("calibrated")
               else "[**မချိန်ညှိရသေး** — recipe ကိန်း]"))
        # ── သုံးစွဲသူ ဖျက်ထားသော အပိုင်းများကို **တကယ် ဖြတ်** ──
        _ed = (CUT.calib(_bid) or {}).get("edit") or {}
        if user_drop:
            _sp2, _sil2, _d2, _e2, _c2 = M2.speech(wav)
            # ⚠️ လူ့ ဖြတ်မှတ် အလေ့အထ (calib `edit`) — အမြီး/ဦးခေါင်း ချန်ပေးသည်。
            #    မထည့်လျှင် အဆုံးသတ် အမြီး ပြတ်ပြီး 「သဘာဝ မကျ」 ဖြစ်သည်
            #    (Zin နားထောင်ပြီး ၂၀၂၆-၀၉-၁၈)。 calib မရှိလျှင် ယခင်အတိုင်း。
            if _ed:
                _n0 = len(user_drop)
                user_drop = CUT.guard(user_drop, _sp2, float(_ed.get("tail_s", 0.0)),
                                      float(_ed.get("lead_in_s", 0.0)))
                log(f"  ဖြတ်မှတ် ချုံ့ချက် — အမြီး +{_ed.get('tail_s')}s · "
                    f"ဦးခေါင်း −{_ed.get('lead_in_s')}s · {_n0} → {len(user_drop)} ခု")
            _req = [[float(a), float(b)] for a, b in user_drop]   # guard မတိုင်မီ တောင်းချက်
            # ⚠️ စွမ်းအင် မြေပုံ ပေးရမည် — တိတ်ဆိတ်မှု မရှိရာမှာ
            #    အနိမ့်ဆုံးမှတ်ဆီ ဆွဲသွင်းနိုင်ရန် (`quiet_at`)。
            spans, _rm = CUT.subtract(spans, user_drop, _sil2,
                                      db=_DBTRACK[0], hop=_DBTRACK[1])
            log(f"  သုံးစွဲသူ ဖျက်ချက် {len(user_drop)} ခု · ဖြုတ် {_rm:.1f}s"
                f" → ကျန် {sum(b-a for a,b in spans):.1f}s")
            st["user_removed"] = _rm
            st["user_cuts"] = len(user_drop)
            # ⚠️ **ဖျက်ခိုင်းတာ ၁၀၀% ဖျက်ဖြစ်မဖြစ် အမြဲ တိုင်းရမည်** (Zin ၂၀၂၆-၀၉-၁၉) —
            #    တိတ်တဆိတ် ကျော်သွားတာ ဘယ်တော့မှ လက်မခံပါ。 Habit [103] ကို ၁၀၀%
            #    မဖျက်ဘဲ ကျန်ခဲ့ပြီး ဘယ်သူမှ မသိခဲ့ (နားထောင်မှ တွေ့)。
            _left = []
            for _k, (_a, _b) in enumerate(_req):
                _rem = sum(max(0.0, min(_b, _y) - max(_a, _x)) for _x, _y in spans)
                if _rem > 0.02 and (_b - _a) > 0:
                    _left.append([_k, round(_rem, 2), round(100.0*_rem/(_b-_a), 1)])
            st["drop_left"] = _left
            if _left:
                # ⚠️ `flag_list` ထဲ ထည့်မှ UI မှာ ပေါ်မည် — log တင် ထားလျှင်
                #    သုံးစွဲသူ ဘယ်တော့မှ မမြင်ရ (တိတ်တဆိတ် ကျော်သွားခြင်း ဖြစ်မည်)。
                _fl = st.get("flag_list") or []
                for _k, _s2, _p2 in _left:
                    _fl.append(dict(kind="drop_left", at=round(_req[_k][0], 2),
                                    text=f"ဖျက်ခိုင်းထားတာ {_p2}% ကျန်နေသည် "
                                         f"({_s2:.2f}s) — အသံ ဆက်နေ၍ သပ်သပ် မဖြတ်နိုင်ပါ",
                                    score=f"{_p2}%"))
                st["flag_list"] = _fl
                st["flags"] = len(_fl)
                log(f"  ⚠️ **၁၀၀% မဖျက်နိုင်တာ {len(_left)}/{len(_req)} ခု** — "
                    + " · ".join(f"#{k+1} {p}% ကျန်" for k, _s, p in _left[:8])
                    + (" …" if len(_left) > 8 else ""))
            else:
                log(f"  ✓ ဖျက်ချက် {len(_req)} ခုလုံး ၁၀၀% ဖျက်ပြီး")
        if user_drop_exact:
            # ⚠️ **စစ်ဆေးပြီးမှ ဖြတ်ရမည်** (Cut audit P0)。 အရင်က တိုက်ရိုက်
            #    `subtract(snap=0.0)` ပို့ခဲ့သဖြင့် အစွန်းက စကားထဲ ကျနေလျှင်
            #    **စကားလုံး ဖြတ်မိသည်** (Zin အမြဲ စည်းကမ်း: F2 = 0)。
            #    ⚠️ မလုံခြုံသည်ကို **ပိတ်ပြီး အကြောင်းရင်း ပြ**ရမည် —
            #       တိတ်တဆိတ် ကျော်သွားလျှင် သုံးစွဲသူ ဘယ်တော့မှ မသိရ。
            _kept = sum(b - a for a, b in spans)
            _dok, _dbad = CUT.validate_drops(user_drop_exact, MEAS[0], m["dur"],
                                             kept=_kept)
            if _dbad:
                _fl = st.get("flag_list") or []
                for _d, _why in _dbad:
                    try: _at = round(float(_d[0]), 2)
                    except (TypeError, ValueError, IndexError): _at = 0.0
                    _fl.append(dict(kind="drop_unsafe", at=_at,
                                    text=f"ပြန်စ ဖျက်ချက် မလုံခြုံ — {_why}",
                                    score="မဖြတ်ပါ"))
                st["flag_list"] = _fl
                st["flags"] = len(_fl)
                log(f"  ⚠️ **ပြန်စ ဖျက်ချက် {len(_dbad)}/{len(user_drop_exact)} ခု ပိတ်လိုက်သည်**")
                for _d, _why in _dbad[:6]:
                    try: _a, _b = float(_d[0]), float(_d[1])
                    except (TypeError, ValueError, IndexError): _a = _b = 0.0
                    log(f"      ⊘ {_a:.2f}–{_b:.2f}s — {_why}")
            if _dok:
                spans, _rm2 = CUT.subtract(spans, _dok, None, snap=0.0)
            else:
                _rm2 = 0.0
            log(f"  ပြန်စ (သုံးစွဲသူ လက်ခံ) {len(_dok)}/{len(user_drop_exact)} ခု · ဖြုတ် {_rm2:.1f}s"
                f" → ကျန် {sum(b-a for a,b in spans):.1f}s")
            st["retake_removed"] = _rm2
            st["retake_cuts"] = len(_dok)
            st["retake_blocked"] = len(_dbad)
        # ⚠️ SKILL F6 — **ဒီစာကြောင်းကို ဖျောက်ခွင့် မရှိ**。 ဤ engine က
        #    တိတ်ဆိတ်မှုကိုသာ ဖယ်သည်。 `happiness 3` ချိန်ညှိမှုတွင် လူ
        #    တည်းဖြတ်သူက ၄၈၁s ဖယ်ခဲ့ရာ engine က ၂၀၀s (၁၉%) သာ ရှာနိုင်သည် —
        #    ကျန် ၈၁% က ဘာပြောထားလဲ နားလည်မှ ဖြတ်နိုင်သော အကြောင်းအရာ。
        #    ဒါကို ဖုံးထားပြီး "ပြီးပြည့်စုံသော edit" ဟု ပြသလျှင် လိမ်ရာ ကျသည်။
        log("  ⓘ ဖြတ်ခြင်းက **ပထမအဆင့်**သာ — တိတ်ဆိတ်မှု ဖယ်တာပဲ။ "
            "လူတည်းဖြတ်သူရဲ့ လျှော့ချမှုရဲ့ ~၁၉% (happiness 3 တိုင်းချက်)")
        # ⚠️ F1 (ဖယ်တာ များ) က ယခု **သတိပေးချက်သာ** (Zin ၂၀၂၆-၀၉-၁၆) —
        #    ground truth ၆ ခုမှာ လူကိုယ်တိုင် ၅၅.၃–၇၂.၈% ဖယ်သည် ⇒ "များသည်"
        #    ဆိုတာ ဗီဒီယို မထုတ်ရ အကြောင်း မဟုတ်။ report မှာ ထင်ရှားပြသည်။
        for _w in (st.get("warnings") or []):
            log(f"  ⚠️  {_w}")
        # ⚠️ SKILL F2/F3 — ထုတ်ခွင့် **ပိတ်**ရသည်、သတိပေးရုံ မဟုတ်
        if st.get("refusals"):
            raise RuntimeError("cut engine ငြင်းပယ်: " + " · ".join(st["refusals"]))
        # ⚠️ ဤစစ်ဆေးချက် မအောင်လျှင် **မထုတ်ရ** — ဤ product ရဲ့ ကတိပါ
        if st["in_speech"] > 0:
            raise RuntimeError(f"ဖြတ်ချက် {st['in_speech']} ခု စကားထဲ ကျနေသည် — မထုတ်ပါ")
        # ── ချောင်းဆိုးသံ · ဖြည့်စကား = အလိုအလျောက် ဖြတ်ခွင့်ရှိ ──
        #    ပြန်စ · ထပ်နေတာ = **ညွှန်ပြရုံ** (သင် အတည်ပြုမှ)
        # ⚠️ **ပုံသေက review-first** — recipe က `auto_clean` ဖွင့််မှ
        #    အလိုအလျောက် ဖြတ်သည် (Zin: 「user အတည်ပြုမှဖျက်ပေး」)。
        auto, flags = CL.plan(wav, segs, auto_ok=bool(rc.get("auto_clean")))
        # ⚠️ ZJL စည်းမျဉ်း ⑧ — **စာလုံး ဖြတ်မိတာက ချောင်းကျန်တာထက် ဆိုးသည်**。
        #    ချောင်း/ဖြည့်စကား ဖြတ်ချက်တွေက CUT.plan ရဲ့ "စကားထဲ မဖြတ်ရ"
        #    စစ်ချက်ကို **ကျော်သွားခဲ့သည်** — QC မှာ cut_in_speech=0 ပြပေမယ့်
        #    ဒီလမ်းကြောင်း မပါခဲ့ဘူး。 ⇒ ဒီမှာ ထပ်စစ်ပြီး စာလုံး ဖြတ်မိမယ့်
        #    ဖြတ်ချက်ကို ဖြုတ်ပစ်သည်。
        if auto:
            import measure as _M
            # ⚠️ CUT.plan နဲ့ **တူညီသော mask** ကို သုံးရမည် — မတူလျှင်
            #    တစ်ဖက်က စကားဟု ဆိုပြီး တစ်ဖက်က မဆိုဘဲ ကွဲသွားသည်。
            _sp, _sil, _d, _e, _c = _M.speech(wav)
            safe, cutword = [], 0
            for c in auto:
                if _sp and (_M.in_speech(c["at"], _sp) or _M.in_speech(c["to"], _sp)):
                    cutword += 1; continue
                safe.append(c)
            if cutword:
                log(f"  ⚠️ စကားထဲ ကျမယ့် ဖြတ်ချက် {cutword} ခု ဖြုတ်ပြီး "
                    f"(စာလုံး မဖြတ်ရ)")
            auto = safe
            st["auto_unsafe"] = cutword
        if auto:
            spans = _subtract(spans, auto)
            log(f"  ချောင်း/ဖြည့်စကား {len(auto)} ခု ထပ်ဖြတ်")
        if flags:
            log(f"  ⚠️ ညွှန်ပြချက် {len(flags)} ခု — သင် အတည်ပြုရန် (မဖြတ်ပါ)")
        st["auto_extra"] = len(auto); st["flags"] = len(flags)
        st["flag_list"] = [dict(kind=f["kind"], at=round(f["at"],2),
                                text=str(f.get("text",""))[:90],
                                keep=str(f.get("keep",""))[:90],
                                score=f.get("score")) for f in flags[:40]]

    # ── review — **ဗီဒီယို မထုတ်ခင် သုံးစွဲသူကို စာတမ်း ပြရန် ရပ်သည်** ──
    if (job.get("mode") or "auto") == "review":
        _kept = sum(b - a for a, b in spans)
        # ── ပြန်စ (retake) — **review စာရင်းသာ** · သုံးစွဲသူ လက်ခံမှ ဖြတ် ──
        # ⚠️ auto-cut ဂိတ် (precision ≥၉၅%) မအောင်သေး (C0736: ၉၁.၁%) ⇒ စက်က မဖြတ်ရ。
        # ⚠️ ကျဘမ်းလျှင် **review ကို မပိတ်ရ** — အကြံပြုချက် မပါဘဲ ဆက်သွား。
        _rt = []; _cl = []; _rt_off = None
        _rcal = CUT.calib(job.get("brand_id") or rc.get("theme")) or {}
        # ⚠️ **ပုံစံ ကန့်သတ်ချက်** (၂၀၂၆-၀၉-၁၆ Zin) — ဂိတ်က ဗီဒီယို ၆ ခုမှာ
        #    vlog ၅ ခု အောင် · podcast ကျ (precision ၇၉.၆% · ဂိတ် ၈၅) ⇒ သုံးစွဲသူ
        #    ပြောသော ပုံစံ `camera` (ကင်မရာကို ပြောတာ) မှသာ ပြန်စ ရှာသည်。
        _vf = (job.get("vfmt") or "").strip().lower()
        # ⚠️ brand မှာ calib မရှိလျှင် ပြန်စ ရှာဖွေမှုက **တိတ်တိတ်ပိတ်**သွားခဲ့သည် —
        #    Zin က `zae` နဲ့ တင်ပြီး "အုပ်စု ဘာလို့ မပေါ်လဲ" ဖြစ်ခဲ့ (၂၀၂၆-၀၉-၁၆)。
        #    ⇒ အကြောင်းရင်းကို **ပြရမည်**。
        if not _rcal:
            _rt_off = ("ဒီ brand အတွက် ပြန်စမှု ရှာဖွေတာကို မချိန်ညှိရသေးလို့ ပိတ်ထားပါတယ် "
                       "(ယခု ZIN JAPAN LIFE မှသာ ရပါတယ်)。 တိတ်ဆိတ်မှု ဖြတ်တာက ပုံမှန်အတိုင်း "
                       "အလုပ်ဖြစ်ပါတယ်")
            log(f"  ⓘ ပြန်စ ရှာဖွေမှု ပိတ် — brand «{job.get('brand_id')}» အတွက် calib မရှိ")
        elif not (_rcal.get("retake") or {}).get("review"):
            _rt_off = None
        elif _vf != "camera":
            _rt_off = ("ဒီပုံစံအတွက် မစမ်းသပ်ရသေးလို့ ပြန်စမှု ရှာဖွေတာကို ပိတ်ထားပါတယ် "
                       "(တိတ်ဆိတ်မှု ဖြတ်တာက ပုံမှန်အတိုင်း အလုပ်ဖြစ်ပါတယ်)")
            log(f"  ⓘ ပြန်စ ရှာဖွေမှု ပိတ် — ပုံစံ «{_vf or 'မသိ'}» · vlog/knowledge sharing မှသာ")
        elif segs:
            try:
                _rt0 = time.time()
                # ⚠️ ဆုံးဖြတ်ချက် မှတ်တမ်းမှာ job ကို ဖော်ပြရန် (~/.ikki/retake_ask.jsonl)
                # ⚠️ `jid` က ဤ function မှာ မရှိ — `job["id"]` သာ ရှိသည်。
                #    ၂၀၂၆-၀၉-၁၉: NameError ကြောင့် **ပြန်စ ရှာဖွေမှု တစ်ခါမှ မအလုပ်လုပ်ခဲ့**
                #    (log: 「ပြန်စ ရှာမရ — NameError: name 'jid' is not defined」)。
                CL.CTX.update(job=job.get("id"), video=job.get("title") or "",
                              brand=job.get("brand_id"))
                _cl, _cst = CL.retake_clusters(segs, MEAS, _rcal, log=log)
                log(f"  ပြန်စ အုပ်စု {len(_cl)} ခု · take {_cst.get('takes')} · "
                    f"ရွေးစရာ ပိတ် {_cst.get('blocked')} · Gemini {_cst.get('asked')} ကြိမ် · "
                    f"{time.time()-_rt0:.0f}s (**ဘာမှ မဖျက်ပါ** — သုံးစွဲသူ ရွေးမှ)")
            except Exception as _e:
                log(f"  ⚠️ ပြန်စ ရှာမရ — review ဆက်သွား: {type(_e).__name__}: {_e}")
        log(f"  ⏸  စာတမ်း အတည်ပြုရန် ရပ်သည် — စာကြောင်း {len(segs)} · "
            f"အကြံပြု ဖြတ်ချက် {st.get('cuts',0)} ({m['dur']-_kept:.0f}s ဖြုတ်)")
        # ⚠️ **စကား မဟုတ်သော အသံ** (ချောင်းဆိုး · ခေါက်သံ …) — သုံးစွဲသူကို
        #    「အကုန် ပြ」 ရန် (Zin ၂၀၂၆-၀၉-၁၉)。 ကျဘမ်းလျှင် review မပျက်စေရ。
        try:
            _snd = M2.sounds(wav, sp=MEAS[0])
            log(f"  အသံ ဖြစ်ရပ် (စကား မဟုတ်) {len(_snd)} ခု")
        except Exception as _e:
            _snd = []; log(f"  ⚠️ အသံ ဖြစ်ရပ် မတိုင်းနိုင်: {type(_e).__name__}: {_e}")
        # ⚠️ ဝါကျ **အတွင်း** ဖြတ်လို့ရသော နေရာ — ထပ်နေတဲ့ စကားစုကို ဝါကျ တစ်ခုလုံး
        #    မဖျက်ဘဲ ခွဲဖျက်နိုင်ရန် (Zin ၂၀၂၆-၀၉-၁၉: 「အကုန်ဖျက်မှ ရမလို ဖြစ်နေတယ်」)。
        try:
            _spl = M2.splits(segs, MEAS[1])
            log(f"  ဝါကျအတွင်း ဖြတ်မှတ် — ဝါကျ {len(_spl)}/{len(segs)} ခုမှာ ရှိ")
        except Exception as _e:
            _spl = {}; log(f"  ⚠️ ဝါကျအတွင်း ဖြတ်မှတ် မတိုင်းနိုင်: {type(_e).__name__}: {_e}")
        # ⚠️ **ဟန်ပျက်** — 「ကင်မရာရှေ့ စကားပြောနေဟန် မဟုတ်တော့တဲ့ အပိုင်း」。
        #    Zin ၂၀၂၆-၀၉-၁၉: 「မင်းကိုယ်တိုင် သိရမယ်။ ဖြတ်ရမည့် စာရင်းထဲ ထည့်ပြီး
        #    user ကို သတိပေးရမယ်」 ⇒ **အသံနဲ့ မရ · ရုပ်ပုံကနေသာ** တိုင်းရသည်。
        #    ⚠️ ကိုယ်တိုင် **မဖျက်ရ** — အနီ မှတ်ပြီး user အတည်ပြုမှသာ ဖျက်သည်。
        _pose = {}
        try:
            import pose as PZ
            if PZ.available():
                _pf = PZ.measure(src, log=log)
                _psp = PZ.spans(_pf, log=log)
                _pose = PZ.mark(
                    [dict(n=i+1, start=g["start"], end=g["end"]) for i, g in enumerate(segs)],
                    _psp)
                if _pose:
                    log(f"  ⚠️ ဟန်ပျက် ဝါကျ {len(_pose)} ကြောင်း — အနီ မှတ်ပြီး "
                        f"user ကို သတိပေးမည် (ကိုယ်တိုင် မဖျက်ပါ)")
            else:
                log("  ⚠️ ဟန်ပျက် မတိုင်းနိုင် — tools/posecheck မရှိ")
        except Exception as _e:
            _pose = {}; log(f"  ⚠️ ဟန်ပျက် မတိုင်းနိုင်: {type(_e).__name__}: {_e}")
        # ⚠️ **အသံ proxy** — Script Editor မှာ နားထောင်ရန် (၄၈ kbps mono m4a)。
        #    ဖြတ်ချက် ဆုံးဖြတ်ဖို့ စာသား ဖတ်ရုံနဲ့ မလုံလောက် — နားထောင်ရမည်。
        #    မရလည်း review **မပျက်စေရ**。
        try:
            _ap = os.path.join(work, "aud.m4a")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav,
                            "-ac", "1", "-c:a", "aac", "-b:a", "48k", _ap], check=True)
            post_audio(job["id"], _ap, log=log)
        except Exception as _e:
            log(f"  ⚠️ အသံ proxy မရ: {type(_e).__name__}: {_e}")
        raise ReviewStop(segs, dict(
            src_dur=round(float(m["dur"]), 2),
            sounds=[[a, b, d] for a, b, d in _snd],
            splits={str(k): v for k, v in _spl.items()},
            pose={str(k): v for k, v in (_pose or {}).items()},
            kept=round(_kept, 2),
            cuts=int(st.get("cuts", 0)),
            removed=round(float(m["dur"]) - _kept, 2),
            spans=[[round(a, 2), round(b, 2)] for a, b in spans],
            flags=st.get("flag_list") or [],
            takes=take_map,
            speech_speed=speech_speed,
            retakes=_rt,            # v1 (ယခု အလွတ်) — ယခင် ဒေတာနဲ့ လိုက်ဖက်ရန် ချန်
            clusters=_cl,           # v2 — အုပ်စု + ရွေးစရာ (ဖြတ်မှတ် ကြိုတွက်ပြီး)
            retake_off=_rt_off))    # ပိတ်ထားလျှင် သုံးစွဲသူကို ပြမည့် အကြောင်းရင်း

    # ⚠️ **မူရင်း အချိန် → ဖြတ်ပြီး အချိန်**。 ဂရပ်ဖစ်/SFX ကို ဖြတ်ပြီးသား
    #    ဗီဒီယိုပေါ် တင်သည် ⇒ ASR ရဲ့ မူရင်းအချိန်ကို တိုက်ရိုက် သုံးလို့ **မရ**。
    #    အရင်က တိုက်ရိုက် သုံးခဲ့သဖြင့် ဖြုတ်လိုက်သော အချိန်အတိုင်း ဂရပ်ဖစ်
    #    တစ်ခုချင်း နောက်ကျသွားပြီး (ဒီဗီဒီယိုမှာ အဆုံးပိုင်း ၂၀၂s အထိ)、
    #    အဆုံးကျော်သွားသော SFX က ဖိုင်ကို ၇၂၆s မှ ၉၁၄s သို့ ဆွဲရှည်စေခဲ့သည်。
    def omap(t, snap=False):
        """မူရင်း t → ထွက်လာမည့် ဗီဒီယိုရဲ့ အချိန်。

        `snap=False` — ဖြုတ်ထားရာ ကျလျှင် None (UI အတွက်: ဘာဖြတ်လိုက်လဲ ပြရန်)。
        `snap=True`  — ဖြုတ်ထားရာ ကျလျှင် **နောက်လာမယ့် စကားစချိန်** သို့ ရွှေ့。

        ⚠️ ဂရပ်ဖစ်မှာ `snap=True` **မဖြစ်မနေ** လိုသည်。 topics က ASR ရဲ့
           segment အစချိန်ကို ယူသည်、ASR က စကားစတာကို တိတ်ဆိတ်မှု detector
           ထက် အနည်းငယ် **စော**ပြီး မှတ်သဖြင့် အစချိန်များစွာက ဖြုတ်လိုက်သော
           တိတ်ဆိတ်မှုရဲ့ အနားစွန်းမှာ ကျသည် — ဖယ်လျှင် ၁၀ ခုမှ **၂ ခု** သာ
           ကျန်ခဲ့သည် (တကယ် တိုင်းထားသည်)。 အဲဒီ အကြောင်းအရာက ဗီဒီယိုထဲ
           ရှိနေဆဲမို့ ရွှေ့ပေးရမည်、ဖယ်လို့ မရ。
        """
        acc = 0.0
        for a, b in spans:
            if t < a:
                return acc if snap else None      # ← နောက် span ရဲ့ အစ
            if t <= b: return acc + (t - a)
            acc += b - a
        return None                                # အဆုံး ကျော်သွားပြီ

    # ── ④ စာတန်း · ⑤ ဂရပ်ဖစ် ───────────────────────────────
    # ⚠️ brand (အရောင်/ဖောင့်) နှင့် format (အရွယ်/safe zone) ကို **ခွဲ**သည်。
    #    ⇒ "ZAE style နဲ့ TikTok 9:16" လို တွဲကို လုပ်လို့ရသည်。
    #
    # ⚠️ house brand (zae · zjl) ကို native အရွယ်နှင့် သုံးလျှင် motionkit ရဲ့
    #    **တိုင်းထားသော** theme ကို အတိအကျ သုံးရမည် — အချိုးနဲ့ ပြန်တွက်လျှင်
    #    reference ဗီဒီယိုနှင့် လွဲသွားမည် (BOT 940 က တိုင်းယူထားသည်)。
    bid = (job.get("brand_id") or rc["theme"])
    house = bid in theme.THEMES
    fmt = (job.get("fmt") or "").strip()
    native = FM.NATIVE.get(bid) or (brand or {}).get("aspect") or "16:9"
    if house and ((not fmt) or fmt == native):
        theme.use(bid); TH = theme.t()
        log(f"  brand {bid} ({native}) → {TH['W']}×{TH['H']} · BOT {TH['BOT']}")
    else:
        # brand ရဲ့ အရောင်/ဖောင့် — DB မှာ ရှိလျှင် အဲဒါ၊ မရှိလျှင် house ရဲ့
        # ⚠️ **house brand (zae · zjl) က DB အရောင်ကို မယူရ** — `zae` record ထဲမှာ
        #    logo ကနေ ထုတ်ထားသော အညိုရောင် palette (#210F0F · #3D2222 · #F20000)
        #    ဝင်နေပြီး အလျားလိုက် format မှာ **ကတ်တွေ အညို/အနီ** ထွက်ခဲ့သည်
        #    (Zin ၂၀၂၆-၀၉-၁၇: "color က ZAE Themes ဖြစ်ရပါမယ်")。 house theme က
        #    reference ကနေ တိုင်းထားသည် ⇒ format ပြောင်းလည်း အဲဒါပဲ သုံးရမည်。
        if house:
            base = dict(theme.THEMES[bid])
            bd = dict(id=bid,
                      colors=[base["NAVY"], base["DEEP"], base["GOLD"],
                              base["SKY"], base["RED"]],
                      mmf=base["MMF"], latin=base["LATIN"], jp=base["JP"])
            log(f"  အရောင် · house brand {bid} ⇒ theme palette (DB အရောင် မယူ)")
        elif brand and brand.get("colors"):
            bd = dict(id=bid, colors=brand["colors"],
                      mmf=brand.get("mmf"), latin=brand.get("latin"),
                      jp=brand.get("jp"))
        else:
            base = dict(theme.THEMES.get(bid) or theme.THEMES[rc["theme"]])
            bd = dict(id=bid,
                      colors=[base["NAVY"], base["DEEP"], base["GOLD"],
                              base["SKY"], base["RED"]],
                      mmf=base["MMF"], latin=base["LATIN"], jp=base["JP"])
        use_fmt = fmt or native
        TH = FM.theme(bd, use_fmt)
        # ⚠️ `accent` — recipe က theme ရဲ့ GOLD ကို လွှမ်းနိုင်သည်。
        #    ၂၀၂၆-၀၉-၂၀: High-Retention reference (`KCN4-2hyUBM`) ရဲ့ accent က
        #    **#E5BC32** (နွေးထွေးသော ရွှေရောင်) ဖြစ်ပြီး ZJL ရဲ့ #FFE000
        #    (တောက်သော အဝါ) နဲ့ RGB ၁၁၂ ကွာသည် ⇒ override လိုသည်。
        _ac = (rc.get("accent") or "").strip()
        if _ac.startswith("#") and len(_ac) == 7:
            TH = dict(TH); TH["GOLD"] = _ac
            log(f"  accent · recipe က {_ac} (theme GOLD လွှမ်း)")
        theme.THEMES["_ikki"] = TH; theme.use("_ikki")
        f = FM.get(use_fmt, bid)
        log(f"  brand {bid} + format {use_fmt} → {TH['W']}×{TH['H']}"
            f" · BOT {TH['BOT']}" + ("" if f["measured"] else " (safe zone အချိုးတွက်)"))
    IG.OUT = work

    # ── ④ စာတန်း — ဖြတ်ပြီးအချိန်သို့ ပြန်တွက်ပြီး alpha track ဆောက် ──
    stage(4, "captions")
    _side_ok = False        # ⚠️ plan မရှိလျှင်လည်း အောက်မှာ သုံးသည် — ကြိုသတ်မှတ်
    # Browser / phone / product mockup က side overlay မဟုတ်ဘဲ full-stage
    # alpha event ဖြစ်သည်။ Side room ရှိတယ်ဆိုပြီး wide UI ကို မတော်တဆ
    # side-safe-zone စစ်ပြီး ပယ်မိခြင်း မရှိစေရန် event id ကို ကြိုစုသည်။
    _full_plan_ids = set()
    capv = None; caps = []; csize = 0; cband = 0; cap_top = TH["H"]
    if segs:
        cap_top = TH["H"]        # ⚠️ ပုံသေ — စာတန်း မဆောက်မိလျှင်ပါ လုံခြုံရန်
        caps = CP.plan(segs, spans)
        # ⚠️ cap_cover ရှိလျှင် **အလေးထားသော စာကြောင်းတွေပဲ** စာတင်သည်。
        #    Knowledge Sharing ရဲ့ reference ၂ ခုမှာ စာတန်းက frame ရဲ့
        #    ၁၀% နှင့် ၁၇% ပဲ ပါသည် (တိုင်းထားသည်)。 အားလုံး ချလျှင်
        #    ပုံစံ လုံးဝ ကွဲသည်。
        # ⚠️ cap_typo — စာတန်း တစ်စိတ်တစ်ပိုင်းကို **typography template**
        #    နဲ့ ထုတ်သည်。 အဲဒီကြောင်းတွေကို ပုံမှန် စာတန်းကနေ **ဖယ်ရမည်** —
        #    မဖယ်လျှင် စာနှစ်ထပ် ဖြစ်သည်。
        typo = []
        tp = float(rc.get("cap_typo") or 0)
        if tp > 0 and len(caps) >= 4:
            want = max(1, int(round(len(caps) * tp)))
            idx = set(TP.emphasis(caps, want, log=log))
            # ⚠️ template ရှာလို့ မရလျှင် caption ကို **မဖယ်ရ** — ဖယ်ပြီး
            #    အစားထိုး မတပ်ရလျှင် အဲဒီစာကြောင်း လုံးဝ ပျောက်သွားမည်。
            if idx and not DR.resolves(TP.templ("typo", 0, set())):
                log("  ⚠️ typography template မတွေ့ — ပုံမှန် စာတန်း ဆက်သုံးသည်")
                idx = set()
            if idx:
                typo = [caps[i] for i in sorted(idx)]
                # ⚠️ typography ဖြစ်သွားသော ကြောင်းကို caps ထဲက **မဖယ်ရတော့** —
                #    ဖယ်လျှင် အဲဒီ segment ရဲ့ ကျန်အချိန်မှာ စာတန်း လုံးဝ
                #    မရှိတော့ဘူး (Zin: "ဗီဒီယိုတစ်ပုဒ်လုံး မထိုးထားဘူး")。
                #    ယခု `hide` ရှိပြီမို့ ဂရပ်ဖစ် ပေါ်နေချိန်မှာသာ ဖျောက်သည်。
                log(f"  စာတန်း · typography {len(typo)} ကြောင်း · စာတန်း {len(caps)} ကြောင်း (ထပ်မဖယ်)")
        st["typo"] = typo
        _caps_avail = len(caps)        # ⚠️ coverage စစ်မတိုင်ခင် — report အတွက်
        cov = rc.get("cap_cover")
        # ⚠️ `cap_cover == 0` = **စာတန်း လုံးဝ မပါ**。 falsy ဖြစ်၍ အရင်က
        #    "မသတ်မှတ်" နဲ့ ရောနေပြီး ပိတ်လို့ မရခဲ့。
        if cov is not None and float(cov) <= 0.0:
            caps = []; log("  စာတန်း ပိတ်ထား (cap_cover 0)")
        if cov and caps and 0 < cov < 1:
            want = max(3, int(round(len(caps) * cov)))
            keep = set(TP.emphasis(caps, want, log=log))
            # ⚠️ `emphasis()` က **「အလေးထားထိုက်သည်」ဟု ထင်တာပဲ** ပြန်ပေးသည် —
            #    ၁၈ တောင်းလည်း ၉ ပဲ ပြန်ပေးတတ်သည် (၂၀၂၆-၀၉-၂၀ တိုင်း၍ တွေ့)。
            #    ဖုံးအုပ်မှု မြင့်လျှင် အဲဒါက **မလုံလောက်** — 「ဘယ်ကြောင်းက
            #    အရေးကြီးလဲ」မဟုတ်ဘဲ 「ဘယ်လောက် ပေါ်နေစေမလဲ」ဖြစ်သဖြင့်
            #    ကျန်ကြောင်းတွေကို **အညီအမျှ ဖြည့်**ရမည်。
            if keep and len(keep) < want:
                rest = [i for i in range(len(caps)) if i not in keep]
                need = min(want - len(keep), len(rest))
                if need > 0:
                    step = len(rest) / float(need)
                    keep |= {rest[int(k * step)] for k in range(need)}
                    log(f"  စာတန်း · အလေးထား {want - need} + ဖြည့် {need} = {len(keep)} ကြောင်း")
            if keep:
                caps = [c for i, c in enumerate(caps) if i in keep]
                log(f"  စာတန်း · {len(caps)} ကြောင်း ({cov*100:.0f}% ရည်မှန်း)")
        # ⚠️ recipe က ကိန်း ပေးထားလျှင် **အဲဒါကို** သုံးရမည် — ZAE ရဲ့
        #    ၈% အရွယ်နှင့် ၈၁% baseline က reference မှ တိုင်းယူထားသည်。
        pct = rc.get("cap_pct") or (0.046 if rc["captions"]=="big" else 0.034)
        # ⚠️ **brand ÷ format** — ZAE ရဲ့ `cap_pct` ၀.၁၀ က သူ့ native **3:4
        #    ဒေါင်လိုက်** မှာ တိုင်းထားသည် (၁၃၆px @ H=1440)。 အလျားလိုက် 16:9
        #    မှာ အဲဒါက ၂၁၆px (H=2160) ဖြစ်ပြီး band က frame ရဲ့ **၄၂%** ယူကာ
        #    **ပြောသူရဲ့ မျက်နှာကို ဖုံး**သည် — Zin ၂၀၂၆-၀၉-၁၇ (tokutei ZAE 4K)。
        #    ⇒ အလျားလိုက်မှာ ကန့်သတ်ပြီး baseline ကို အောက် ချသည်。
        #    ⚠️ baseline ကို **format ရဲ့ BOT (safe zone) အတိုင်း** ထားရမည် —
        #       ၀.၈၈ ချလိုက်တော့ QC `caption_zone` ကျခဲ့သည် (1900 > BOT 1660)。
        if TH["W"] > TH["H"] and pct > 0.06:
            _old = pct; pct = 0.045
            # ⚠️ baseline — QC ရဲ့ `cap_max` ၀.၈၃၃ အောက်မှာ ရှိရမည်。 BOT (၀.၇၆၉)
            #    က အပေါ်လွန်းသည် ⇒ Zin ၂၀၂၆-၀၉-၁၇ "subtitle ကို အောက်ကို နည်းနည်း
            #    ချချင်တယ်" ⇒ ၀.၈၀ (QC ဘောင်အတွင်း · ဘေးလွတ် ၃%)。
            rc["cap_base"] = 0.80
            # ⚠️ ဖောင့် — Zin ရွေးချယ်ချက် (၂၀၂၆-၀၉-၁၇ · နမူနာ ၄ ခုထဲက ၂)。
            #    `MyanmarHeadOne` က ဖောင့်စာရင်းမှာ «ZAE **ခေါင်းစဉ်**» အတွက်
            #    မှတ်ထားပြီး `Pyidaungsu-Bold` က «Short Video · ZAE» အတွက်。
            rc["mmf"] = "Pyidaungsu-Bold"
            log(f"  စာတန်း · အလျားလိုက် format ⇒ အရွယ် {_old} → {pct} · "
                f"baseline {rc['cap_base']} · ဖောင့် {rc['mmf']}")
            # ⚠️ **ဂရပ်ဖစ် ပိုများစေရန်** (၂၀၂၆-၀၉-၁၇ Zin: "Infography များများလေး
            #    သုံးပေးပါ")。 အလျားလိုက် frame မှာ စာတန်း band ကျဉ်းသွား၍ ကတ်
            #    တင်ဖို့ နေရာ ပိုရသည် ⇒ recipe ရဲ့ ၅ ကို ၁၀ သို့。 QC ရဲ့
            #    `gfx_share` က အလွန်အကျွံ ဖြစ်လျှင် ဖမ်းမည်。
            # ⚠️ **ကတ် အရောင် — navy + gold သာ** (Zin ၂၀၂၆-၀၉-၁၇)。 template
            #    တချို့က RED ကို accent အဖြစ် ယူသဖြင့် "တစ်နှစ် Program" ကတ်က
            #    အနီရောင် ထွက်ခဲ့သည်。 ⇒ RED/SKY ကို GOLD ဖြင့် အစားထိုး。
            try:
                _t = theme.THEMES.get("_ikki")
                if _t and _t.get("GOLD"):
                    _t["RED"] = _t["GOLD"]; _t["SKY"] = _t["GOLD"]
                    theme.use("_ikki")
                    log("  အရောင် · ကတ်များ navy + gold သာ (RED/SKY → GOLD)")
            except Exception as _e:
                log(f"  ⚠️ အရောင် မပြောင်းနိုင်: {_e}")
            _g0 = int(rc.get("gfx") or 0)
            if _g0 and _g0 < 10:
                rc["gfx"] = 10
                log(f"  ဂရပ်ဖစ် · အလျားလိုက် format ⇒ {_g0} → 10 ကတ်")
        csize = int(TH["H"] * pct)
        cband = int(csize*2.2)*2
        # ⚠️ စာတန်း band ရဲ့ **အပေါ်ဆုံး** — ဂရပ်ဖစ်က ဒီအောက် ဆင်းလျှင်
        #    စာနှစ်ထပ် ဖြစ်သည် (v32 မှာ "100%" ရဲ့ အောက်စာက စာတန်းပေါ်
        #    ထပ်နေခဲ့သည် — တကယ်)。
        _cb = rc.get("cap_base")
        cap_top = (int(TH["H"]*_cb) if _cb else TH["BOT"]) - cband
        capv = None      # ⚠️ ဂရပ်ဖစ် ပြီးမှ ဆောက်သည် (အောက်တွင်)
    else:
        log("  ⚠️ စာသား မရှိ — စာတန်း ကျော်သွားသည်")

    stage(5, "graphics")
    # ⚠️ lower third ကို **မတပ်ပါ** — Zin ကိုယ်တိုင် ငြင်းခဲ့သည်
    #    ("ဒါကြီးကကြောင်တောင်တောင်ကြီးဖြစ်နေတယ် ဖြုတ်ပေးပါ")。
    el = None
    # ⚠️ ဂရပ်ဖစ်ကို **တိတ်ဆိတ်မှုပေါ် မချရ** — အကြောင်းအရာနဲ့ ကိုက်ရမည်。
    #    လက်နဲ့ လုပ်တုန်းက "② စာမေးပွဲ" က စာမေးပွဲအကြောင်း ပြောတဲ့အခါ ပေါ်ခဲ့သည်。
    #    တိတ်ဆိတ်မှုပေါ် ချလျှင် ကျဘမ်း ဖြစ်သည် (တကယ် ဖြစ်ခဲ့)。
    gfx = []
    # ══ Headtop — plan လမ်းကြောင်း ═══════════════════════════════
    # ⚠️ `rc["plan"]` ဆိုမှသာ。 ကျန် ပုံစံ ၁၀ ခု **ယခင်အတိုင်း** —
    #    worker က ဆုံးဖြတ်နေဆဲ。 တစ်ပြိုင်နက် မပြောင်းရ (ပြောင်းလျှင်
    #    ပုံစံအားလုံး တစ်ပြိုင်နက် ပျက်နိုင်သည်)。
    # ⚠️ plan က **source အချိန်** နဲ့ ထုတ်သည် — အောက်က `omap` က
    #    ဖြတ်ပြီး timeline သို့ ပြောင်းပေးမည်。
    _PLAN = None
    if rc.get("plan") and segs:
        try:
            import planner as PLN
            import execute as EX
            # ⚠️ keyword pop ကို **မျက်နှာ ရှောင်ပြီး** ချရန် pose လိုသည်。
            #    review အဆင့်မှာ တိုင်းထားပေမယ့် **အတည်ပြုပြီး render**
            #    လမ်းကြောင်းမှာ အဲဒီအဆင့် ကျော်သွားသဖြင့် မရှိပါ ⇒ ဒီမှာ တိုင်းသည်。
            #    မရလျှင် plan က ဘောင်အလယ်ကို ရှောင်ရုံ ဆက်လုပ်သည် (မရပ်ပါ)。
            _pose_fr = None
            try:
                # ⚠️ `PZ` က review အကိုင်းထဲမှာသာ import လုပ်ထားသည် —
                #    ဒီအကိုင်းမှာ **မရှိပါ** (NameError)。 `_breathe` မှာ
                #    ဖြစ်ခဲ့သော အမှားမျိုးပင် ⇒ ဒီမှာ ကိုယ်တိုင် ယူရမည်。
                import pose as PZ2
                if PZ2.available():
                    _pose_fr = PZ2.measure(src, log=log)
                    log(f"  pose · ဖရိန် {len(_pose_fr)} · "
                        f"မျက်နှာ ပါ {sum(1 for x in _pose_fr if x.get('nf'))}")
            except Exception as _pe:
                log(f"  ⚠️ pose မရ ({type(_pe).__name__}) — ဘောင်အလယ် ရှောင်ရုံ")
            _PLAN, _pwarn = PLN.plan(
                segs, float(m["dur"]),
                dict(energy=rc.get("energy"), fps=rc["fps"],
                     aspect=f'{TH["W"]}:{TH["H"]}',
                     pose=_pose_fr, cap_base=rc.get("cap_base") or 0.92,
                     # ⚠️ SFX မူဝါဒကို **recipe ကနေ** ယူရမည် — planner ထဲ
                     #    ကိန်းသေ ရေးလျှင် ပုံစံတိုင်း တူသွားမည်。
                     sfx_on=rc.get("sfx_on"), sfx=rc.get("sfx", True),
                     sfx_per_min=rc.get("sfx_per_min"),
                     # ⚠️ **ဖြတ်ပြီး အရှည်** — SFX budget ကို ဒါနဲ့ တွက်ရမည်
                     #    (QC က ထွက်ဖိုင်ပေါ်မှာ တိုင်းသည်)。 ဖြစ်ရပ် အချိန်မှတ်က
                     #    မူရင်း timeline အတိုင်း ကျန်သည် — `omap` က ပြောင်းမည်。
                     out_dur=_outdur_guess(spans),
                     # MotionKit profile က raw template ID မဟုတ်ဘဲ
                     # manifest/safe-zone စစ်ပြီးသား visual language ဖြစ်သည်။
                     motionkit_profile=rc.get("motionkit_profile") or "premium",
                     # ⚠️ **ပုံစံ နာမည်ကို ပေးရမည်** — တိုင်းထားသော SFX
                     #    မူဝါဒ (headtop ၆.၀/min) ကို id နဲ့ ရှာသည်。
                     style=rc.get("_id"),
                     # ⚠️ **စည်းချက်** — ကွက်လပ် ရှည်လျှင် ဂရပ်ဖစ် ဖြည့်သည်
                     gfx_gap_max=rc.get("gfx_gap_max") or 0,
                     log=log),
                video_id=job["id"], log=log)
            # ⚠️ **ထပ်တင် မလုပ်တော့** — plan ရဲ့ template တွေကို အောက်က
            #    ဖြတ်ပြောင်း အကိုင်းက ကိုင်သည်。 ဒီမှာ `to_gfx()` ပေးလိုက်လျှင်
            #    ထပ်တင်အဖြစ် တစ်ခါ ကြိုးစားပြီး 「နေရာ မတည့်」နဲ့ ကျမည်
            #    (ကျန်နေရာ ၅.၆% ·H သာ) — ပြီးမှ ဖြတ်ပြောင်းအဖြစ် ထပ်လုပ်သည်。
            #    ⇒ အလုပ် နှစ်ခါ လုပ်ပြီး log ရှုပ်သည် (၂၀၂၆-၀၉-၂၁ တွေ့)。
            # ⚠️ **ဘေးနေရာ ရှိလျှင် ဖုံးစရာ မလို**。 ဤဆုံးဖြတ်ချက်ကို ရေးချိန်က
            #    ကျန်နေရာ ၃၃px သာ ဟု ယူဆခဲ့သဖြင့် plan ရဲ့ template တွေကို
            #    「ပြောသူကို ဖုံးပြီး ကတ် ပြ」 ဆီ ပို့ခဲ့သည်。 ယခု ပြောသူရဲ့
            #    ဘေးတိုက် နယ်ကို တိုင်းပြီး **၈၂၄px လွတ်နေ**ကြောင်း တွေ့သဖြင့်
            #    overlay အဖြစ် ချနိုင်သည် — reference လုပ်ထားတာ အဲဒါ。
            gfx = []
            _side_ok = False
            try:
                _sb0 = subject_box(src, TH["W"], TH["H"], log)
                _av0 = _avoid_band(src, TH, log=lambda *a: None)
                if _sb0 and _av0:
                    _av0 = (_av0[0], _av0[1], float(_sb0[0]), float(_sb0[1]))
                    _srm = DR.side_room(_av0, TH["W"])
                    if _srm >= int(TH["W"] * 0.22):
                        # ⚠️ **keyword pop ကို ဒီထဲ မထည့်ရ** — အဲဒါတွေက
                        #    ပြောသူပေါ် တိုက်ရိုက် ချရသော အလေးထားချက် ဖြစ်ပြီး
                        #    သီးသန့် အကိုင်းက ကိုင်သည်。 ထည့်လျှင် `word_pop`
                        #    က args မကိုက်ဘဲ ကျသည် (၂၀၂၆-၀၉-၂၁ ဖမ်းမိ)。
                        _pops = {e.get("id") for e in _PLAN["templateEvents"]
                                 if (e.get("style") or {}).get("kind") == "pop"}
                        _full_plan_ids = {
                            e.get("id") for e in _PLAN["templateEvents"]
                            if (e.get("style") or {}).get("layout") == "full"
                        }
                        _gp = [g for g in EX.to_gfx(_PLAN, log=None)
                               if (g.get("kind") or "")
                               and g.get("_eid") not in _pops
                               and g.get("_eid") not in _full_plan_ids]
                        if _gp:
                            gfx = _gp; _side_ok = True
                            log(f"  ↔ ဘေးနေရာ {_srm}px ⇒ ဂရပ်ဖစ် {len(gfx)} ခုကို "
                                f"**ဖုံးမဲ့အစား ဘေးမှာ** ချသည်")
            except Exception as _se0:
                log(f"  ⚠️ ဘေးနေရာ မစစ်နိုင် ({type(_se0).__name__}: {_se0})")
            _sm = EX.summary(_PLAN)
            log(f"  plan · template {_sm['templates']} · စာတန်း {_sm['captions']}"
                f" · သတိပေး {_sm['warnings']} (အတည်ပြုရန် {_sm['critical']})")
            # ⚠️ `st["plan"]` ဟု **မရေးရ** — job ထဲမှာ `plan` က ဖြတ်မှတ်
            #    အတွက် ရှိပြီးသား ဖြစ်ပြီး နာမည်တူသွားသည်。 `edit_plan` ဟု
            #    ခွဲရမည်、ပြီးတော့ `post_result` ထဲ **ထည့်မှ** သိမ်းသည်。
            st["edit_plan"] = _PLAN
        except Exception as _e:
            # ⚠️ plan မရလျှင် **အလုပ် မရပ်ရ** — ယခင်နည်းနဲ့ ဆက်သွားသည်
            log(f"  ⚠️ plan မရ ({type(_e).__name__}: {_e}) — ယခင်နည်းနဲ့ ဆက်သွားသည်")
            _PLAN = None
    if segs and not _PLAN:
        try:
            # ⚠️ **ပိုတောင်းရမည်** — မျက်နှာရှောင်ရာမှာ တချို့ ကျော်ရသည်။
            #    အတိအကျ တောင်းလျှင် နောက်ဆုံး အရေအတွက် မပြည့်。
            _wg = int(rc.get("gfx") or 0)
            # ⚠️ `gfx` က **ပုံသေ အရေအတွက်** — အတိုတွေအတွက် ချိန်ထားသည်。
            #    `gfx_share` ဘောင် (တိုင်းထားသော ၀.၁၀–၀.၁၇) ကို ရောက်ဖို့
            #    ကတ် ဘယ်နှစ်ခု လိုလဲကို **အရှည်ကနေ ပြန်တွက်**ရမည် —
            #    ကတ်တစ်ခု အများဆုံး ၁၀s ရပ်နိုင်သဖြင့် ၁၅ မိနစ် ဗီဒီယိုမှာ
            #    ၆ ခုနဲ့ share ၀.၀၈၃ ပဲ ရပြီး QC ကျခဲ့သည်。
            _shb = rc.get("gfx_share")
            if _shb:
                _od0 = sum(b - a for a, b in spans) or float(m["dur"])
                # ⚠️ ရွေးထားသမျှ အကုန် မတပ်မိ — မျက်နှာ/စာတန်းနဲ့ နေရာ
                #    မတည့်လျှင် ကျော်သည် (တစ် run မှာ ၈ → ၇)。 ၂၅% ဆုံးရှုံးမှု
                #    ခန့်မှန်းပြီး ပိုတောင်းရမည်、မဟုတ်လျှင် band အောက် ကပ်ကျမည်。
                _need = int(math.ceil(float(_shb[0]) * _od0 / 10.0 / 0.75)) + 1
                if _need > _wg:
                    log(f"  ဂရပ်ဖစ် {_wg} → {_need} ခု (share {_shb[0]:.2f} "
                        f"ရောက်ရန် · ဖြတ်ပြီး {_od0:.0f}s)")
                    _wg = _need
                # ⚠️ **အပေါ်ဘောင်လည်း လိုသည်**。 `hold` က ကတ်ကို တိုအောင်
                #    မလုပ်နိုင်သဖြင့် (`dress.track`: `if hold > gdur`) ဗီဒီယို
                #    တိုလျှင် ကတ် များများနဲ့ share ကျော်သွားသည်。 `_fit_gfx` က
                #    နောက်မှ ဖယ်ပေးပေမယ့် **ဖယ်မယ့်ကတ်ကိုပါ ထုတ်ပြီးသား**
                #    ဖြစ်နေမည် (တစ်ခု ~၂ မိနစ်)。 ⇒ မထုတ်ခင်ကတည်းက ကန့်သတ်。
                #    ၁.၈s က template ရဲ့ **တိုင်းထားသော အတိုဆုံး** သဘာဝအရှည်
                #    (median ၂.၄ · min ၁.၈ · max ၃.၀ — j_e45a95bd33ea)。
                _cap = int(float(_shb[1]) * _od0 / CARD_NAT_MIN) + 1
                if _cap < _wg:
                    log(f"  ဂရပ်ဖစ် {_wg} → {_cap} ခု (share {_shb[1]:.2f} "
                        f"မကျော်ရန် · ဖြတ်ပြီး {_od0:.0f}s)")
                    _wg = max(1, _cap)
            # ⚠️ **ပိုတောင်းရမည်** — Gemini က တောင်းသလောက် အမြဲ မပြန်ပေး
            tops = TP.ask(segs, want=int(_wg * 1.6) + 3 if _wg else 0, log=log)
            _gfxn = len(tops)              # Gemini ပြန်ပေးတဲ့ ခေါင်းစဉ် အရေအတွက်
            _gfxask = int(_wg * 1.6) + 3 if _wg else 0   # တကယ် တောင်းလိုက်တာ
            # ⚠️ role တစ်ခုလျှင် **ရေကန်** ထဲမှ ရွေးသည် — အရင်က တစ်ခုတည်း
            #    ဖြစ်၍ ဗီဒီယိုတိုင်း title_card · fact_box · locator ချည်း
            #    ထွက်ပြီး အားလုံး တစ်ပုံစံတည်း ဖြစ်ခဲ့သည်。
            # ⚠️ seed ကို **job id** ကနေ ယူသည် — ဗီဒီယိုအလိုက် ကွဲပြားပြီး
            #    တူညီသော job ကို ပြန်ထုတ်လျှင် တူညီသော ရလဒ် ရစေရန်。
            seed = sum(ord(c) for c in str(job.get("id") or ""))
            bname = (brand or {}).get("name", "IKKI")
            used = set()
            for i, t in enumerate(tops):
                # ⚠️ **ပထမ ဂရပ်ဖစ်က ခေါင်းစဉ်ကတ် ဖြစ်ရမည်** — N5 reference က
                #    ~၆s မှာ "ONLINE CLASS" ကြီးကြီး + kicker + ရွှေမျဉ်း ဖြင့်
                #    ဖွင့်သည်。 ကျပန်း ရွေးလျှင် ထောင့်က bar လေး ထွက်ပြီး
                #    ဖွင့်ခန်း အားနည်းသည်。
                # ⚠️ ပထမ ဂရပ်ဖစ်ကို **`title_card` အတိအကျ** သုံးသည် — N5 က
                #    "ONLINE CLASS" ကြီးကြီး + kicker + ရွှေမျဉ်း ဖြင့် ဖွင့်သည်。
                #    ရေကန်ထဲက ကျပန်း ရွေးလျှင် ထောင့်က bar လေး ထွက်ပြီး
                #    ဖွင့်ခန်း အားနည်းသည် (Zin: "ဒီပုံစံအတိုင်း တစ်ထပ်တည်း")。
                if i == 0 and DR.resolves("title_card"):
                    nm = "title_card"
                else:
                    nm = TP.templ(t["kind"], seed + i, used)
                used.add(nm)
                # ⚠️ **အကြောင်းအရာ စာသားကို ပါသွားစေရမည်** — template လဲရာမှာ
                #    လိုသည်。 မပါလျှင် လဲလိုက်တာက recipe နာမည် (「Headtop」)
                #    ကို မျက်နှာပြင်ပေါ် တင်မိပြီး အဓိပ္ပာယ်မဲ့ ဖြစ်သည်。
                gfx.append(dict(at=t["at"], kind=nm, text=t.get("text") or "",
                                args=TP.targs(nm, t["text"], bname)))
            # ⚠️ **explainer insert ကို ဒီမှာပါ ထည့်ရမည်** — `DR.pick()` က
            #    ပြန်ဆုတ်လမ်းသာ ဖြစ်၍ ဒီအဓိကလမ်းမှာ မထည့်လျှင် insert
            #    တစ်ခုမှ မဝင်ပါ (၂၀၂၆-၀၉-၂၀ ref-talk render မှာ တကယ် ဖြစ်)。
            if rc.get("insert_per_min") and gfx:
                _b4 = sum(1 for g in gfx if g.get("kind") in DR.INSERT_KINDS)
                gfx = DR.apply_inserts(gfx, rc, float(m["dur"]), log=log)
                _af = sum(1 for g in gfx if g.get("kind") in DR.INSERT_KINDS)
                log(f"  explainer insert {_af} ခု / ဂရပ်ဖစ် {len(gfx)} "
                    f"({_af/(float(m['dur'])/60.0):.1f}/မိနစ် · ပစ်မှတ် {rc['insert_per_min']})")
        except Exception as e:
            log(f"  ⚠️ ခေါင်းစဉ် မရ: {e}")
    # ⚠️ typography စာကြောင်းများကို ဂရပ်ဖစ် track ထဲ ထည့်သည် — သီးသန့်
    #    render လမ်းကြောင်း မဆောက်ဘဲ ရှိပြီးသား alpha track ကို သုံးသည်。
    for i, c in enumerate(st.get("typo") or []):
        nm = TP.templ("typo", sum(ord(x) for x in str(job.get("id") or "")) + i, set())
        # ⚠️ typography က **စကားလုံးနဲ့ ချိတ်**ထားသည် — မရွှေ့ရ。 ခေါင်းစဉ်
        #    ဂရပ်ဖစ်က တိတ်ဆိတ်မှုပေါ် ချထားသဖြင့် ရွှေ့လို့ ရသည်。
        gfx.append(dict(at=round(c["start"], 2), kind=nm, fixed=True,
                        args=TP.targs(nm, c["text"], "")))
    if st.get("typo"):
        gfx.sort(key=lambda g: g["at"])
    # ⚠️ **plan ရှိလျှင် ပြန်ဆုတ်လမ်း မသုံးရ**。 plan ရှိချိန်မှာ `gfx = []`
    #    ဟု တမင် ထားပြီး template တွေကို အောက်က **ဖြတ်ပြောင်း** အကိုင်းက
    #    ကိုင်သည် — ဒါပေမဲ့ `if not gfx:` က အဲဒါကို 「ဘာမှ မရှိ」ဟု မှတ်ပြီး
    #    `DR.pick()` ကို ပြေးစေသည်。 `pick()` က **အကြောင်းအရာ စာသား
    #    မပါသော** ဂရပ်ဖစ် ထုတ်သဖြင့် ဗလာ ကွက်များ ဖြစ်ခဲ့သည်
    #    (၂၀၂၆-၀၉-၂၁ — ရွှေရောင် အနားသတ်ကို ဗီဒီယိုတစ်ခုလုံးမှာ မတွေ့ရ)。
    if not gfx and not _PLAN:
        # ⚠️ `_sil_of()` ဖယ်ပြီး **မျှသုံး မြေပုံ**ကနေ ဆင်းသက်စေသည်
        gfx = DR.pick(rc, m["dur"], _M.as_gaps(MEAS[1], 0.20), segs, log)   # ပြန်ဆုတ်လမ်း
        if gfx: log("  ⚠️ အကြောင်းအရာ မရ — တိတ်ဆိတ်မှုပေါ် ချထားသည်")
    elif not gfx:
        log("  ⓘ ဂရပ်ဖစ်ကို plan ရဲ့ ဖြတ်ပြောင်း အကိုင်းက ကိုင်သည်")
    gmov = []
    if gfx:
        # ⚠️ **ဖြတ်ပြီး timeline သို့ ပြောင်းရမည်** — ဖြုတ်လိုက်သော အပိုင်းထဲ
        #    ကျသွားသော ဂရပ်ဖစ်ကို ဖယ်သည် (အဲဒီစကား ဗီဒီယိုထဲ မရှိတော့)。
        _n0 = len(gfx); _mapped = []
        for g in gfx:
            _t = omap(float(g.get("at") or 0), snap=True)
            if _t is None: continue
            g = dict(g); g["at"] = round(_t, 2); _mapped.append(g)
        gfx = _mapped
        if _n0 != len(gfx):
            log(f"  ဂရပ်ဖစ် {_n0 - len(gfx)} ခု ဗီဒီယို အဆုံးကျော်၍ ဖယ်သည်")
        log(f"  ဂရပ်ဖစ် ရွေး {len(gfx)} ခု · {', '.join(g['kind'] for g in gfx[:4])}…")
        try:
            # ⚠️ ကတ်တစ်ခု ဘယ်လောက် ရပ်ရမလဲကို **ဗီဒီယို အရှည်ကနေ တွက်**ရမည်。
            #    `gfx_share` (တိုင်းထားသော ၀.၁၀–၀.၁၇) က ပစ်မှတ်、`gfx` က
            #    အရေအတွက်。 ပုံသေ ၂.၂s ထားလျှင် ၁၅ မိနစ် ဗီဒီယိုမှာ share က
            #    ၀.၀၂၅ ပဲ ရပြီး QC ကျသည် — အရေအတွက် တိုး၍ ဖြေရှင်းလျှင်
            #    ကတ် ၅၄ ခု လိုမည်、reference နဲ့ လုံးဝ မတူတော့。
            #    ⚠️ `card_len` ဘောင် ၁.၀–၁၀.၅s ကို **မကျော်ရ** ⇒ clamp。
            _hold = None
            _sh = rc.get("gfx_share")
            if _sh and gfx:
                # ⚠️ **ဖြတ်ပြီး အရှည်** နဲ့ တွက်ရမည် — မူရင်း အရှည် မဟုတ်。
                #    QC က ထွက်လာသော ဖိုင်ပေါ်မှာ တိုင်းသည်。
                _od = sum(b - a for a, b in spans) or float(m["dur"])
                _tgt = (float(_sh[0]) + float(_sh[1])) / 2.0 * _od
                _hold = max(1.5, min(10.0, _tgt / len(gfx)))
                log(f"  ကတ် ရပ်ချိန် {_hold:.1f}s × {len(gfx)} ခု "
                    f"→ share ~{_hold*len(gfx)/_od:.3f} "
                    f"(ပစ်မှတ် {_sh[0]:.2f}–{_sh[1]:.2f} · ဖြတ်ပြီး {_od:.0f}s)")
            # ⚠️ **နေရာ မဝင်သော template ကို ကြိုလဲရမည်** — ဆောက်ပြီးမှ
            #    ပယ်လျှင် အချိန် ကုန်ပြီး ဂရပ်ဖစ် မရှိတော့。 ၁၂၀s headtop တစ်ခုမှာ
            #    ၂ ခုက 「နေရာ မတည့်」နဲ့ ပယ်ခဲ့သည် (၂၀၂၆-၀၉-၂၁)。
            _av = _avoid_band(src, TH, log)
            # ⚠️ **ဘောင်အကျယ်လုံး ပိတ်ခြင်းက ပြဿနာရဲ့ အမြစ်**。 ပြောသူရဲ့
            #    ဘေးတိုက် နယ်ကိုပါ တိုင်းပြီး box အဖြစ် ပေးလျှင် ဘေးမှာ
            #    ၈၂၄px လွတ်နေသည် ⇒ template ၀/၂၄၃ ကနေ ၂၀၆/၂၄၃ ဝင်သည်。
            try:
                _sb = subject_box(src, TH["W"], TH["H"], log)
                if _sb and _av:
                    _av = (_av[0], _av[1], float(_sb[0]), float(_sb[1]))
            except Exception as _be:
                log(f"  ⚠️ ပြောသူ ဘောင် မတိုင်းရ ({type(_be).__name__})")
            gfx, _nsw = DR.swap_fit(gfx, _av, cap_top, TH["H"],
                                    seed=rc.get("_seed") or "",
                                    fmt=(job.get("fmt") or "16:9"), log=log,
                                    W=TH["W"])
            if _nsw:
                REPORT["gfx_swapped"] = _nsw
            gmov, ng = DR.track(gfx, None, os.path.join(work,"gx"), TH["W"], TH["H"],
                                rc["fps"], T1, T2, (brand or {}).get("name","IKKI"),
                                rc["label"], log,
                                avoid=_av,
                                capy=cap_top, hold=_hold)
            # ⚠️ ထုတ်ပြီးမှ **တကယ့် အရှည်နဲ့ ပြန်တိုင်း**ရမည် — `hold` က
            #    တိုအောင် မလုပ်နိုင်သဖြင့် ပစ်မှတ်ထက် ကျော်နိုင်သည်。
            #    ဖယ်တာက ကတ်ဖိုင်ကို ပြန်မထုတ်ရ ⇒ အချိန် မကုန်ပါ。
            if _sh and gmov:
                # ⚠️ နာမည်ကို `_wg` **မသုံးရ** — အဲဒါက အပေါ်မှာ 「ဂရပ်ဖစ်
                #    ဘယ်နှစ်ခု လိုချင်လဲ」ကိန်း ဖြစ်ပြီး report က အဲဒါကို
                #    ပြသည်。 ထပ်သုံးမိ၍ report ရဲ့ 「ပစ်မှတ်」နေရာမှာ
                #    စာရင်းတစ်ခု ပေါ်ခဲ့သည် (၂၀၂၆-၀၉-၂၀ Zin ရဲ့ render)。
                gmov, _wgfit = _fit_gfx(gmov, _sh, _od, log=log)
                ng = len(gmov)
                LAST_FIT[:] = _wgfit
            # ⚠️ စာတန်းနဲ့ ဒေါင်လိုက် ထပ်တာကို **စစ်စရာ မလိုတော့** —
            #    ဂရပ်ဖစ် ပေါ်နေချိန် စာတန်းကို `hide` ဖြင့် ဖျောက်ပြီးသား。
            #    စစ်နေလျှင် စာတန်း တစ်ပုဒ်လုံး ရှိသဖြင့် ဂရပ်ဖစ် အားလုံးနီးပါး
            #    ဖျက်ခံရသည် (v35 မှာ ၅ → ၃ ကျခဲ့သည်)。
            log(f"  ဂရပ်ဖစ် တပ်ပြီး {ng} ခု")

        except Exception as e:
            log(f"  ⚠️ ဂရပ်ဖစ် မရ: {e}"); gmov=[]

    # ── full-frame slide (Knowledge Sharing) ──────────────────
    # ⚠️ lower-third အသေးလေးတွေနဲ့ **ဂရပ်ဖစ် အချိန် ၂.၅%** ပဲ ရခဲ့ပြီး
    #    Zin က "တစ်ခုမှ မမိုက်ဘူး" ဟု ဆိုသည်。 သူပေးသော reference (၉:၁၅)
    #    ကို တိုင်းကြည့်ရာ full-frame slide ၁၂ ခု · ၇၄.၅s = **၁၃.၄%**
    #    (recipe band 0.10–0.17 နဲ့ တိကျစွာ ကိုက်) · တစ်ခုချင်း ပျမ်းမျှ ၆.၂s。
    #    ⇒ အရေအတွက် တိုးတာ မဟုတ်、**မျက်နှာပြင် အပြည့်** ပြရမည်。
    slides = []
    pmov = []          # keyword pop — (at, mov, dur, dx, စာသား)
    rmov = []          # ဘေးဘောင် စာရင်း — (at, png, dur)
    # ══ ဘေးဘောင် စာရင်း (progress rail) ═══════════════════════════
    # ⚠️ reference `HJ0K1yAuGLw` ကနေ တိုင်းယူထားသည် (`docs/HEADTALK_STYLE.md` §၅)。
    #    ပုံစံက **မိနစ်ချီ ဆက်ပေါ်**ပြီး item တစ်ခုချင်း အခြေအနေ ပြောင်းသည် —
    #    IKKI ရဲ့ 「ပြ → ဖယ်」နဲ့ လုံးဝ ကွဲသည် ⇒ `gfx_share` နဲ့ မရောရ。
    # ⚠️ **plan ထဲ မထည့်သေးပါ** — `plan_schema` က template ID မဖြစ်မနေ
    #    လိုသဖြင့် ဒီအတွက် schema ချဲ့ရမည်။ v1 မှာ worker က တိုက်ရိုက်
    #    တွက်သည် (segs ရှိပြီးသား)။ ⇒ UI ကနေ ပြင်လို့ မရသေး。
    if rc.get("plan") and segs:
        try:
            import rail as RL
            _r = RL.find(segs)
            if _r:
                _ai, _head, _n = _r
                _st = RL.starts(segs, _ai + 1, _n)
                _acc = rc.get("accent") or TH.get("GOLD") or "#FFE000"
                _work_r = os.path.join(work, "rail"); os.makedirs(_work_r, exist_ok=True)
                # ⚠️ item ရဲ့ **ခေါင်းစဉ်** = အဲဒီဝါကျရဲ့ အတိုချုံး。
                #    မရှိလျှင် နံပါတ် ပြသည် (reference ရဲ့ ပထမ အခြေအနေ)。
                _lab = {}
                for _k, _j in _st.items():
                    _t = " ".join((segs[_j].get("text") or "").split())
                    # ⚠️ 「နံပါတ် ၁」ရှေ့ဆက် **ဖယ်ရမည်** — pill တိုင်းမှာ
                    #    ပါနေလျှင် နေရာ ကုန်ပြီး အဓိပ္ပာယ် မရှိပါ。
                    _lab[_k] = (RL.cut_at_space(RL._head(RL._strip_mark(_t)), 28)
                                or RL._mm(_k))
                _states = []
                _marks = sorted(_st.items())
                for _idx, (_k, _j) in enumerate(_marks):
                    _a = omap(float(segs[_j].get("start") or 0), snap=True)
                    if _a is None:
                        continue
                    _nx = None
                    if _idx + 1 < len(_marks):
                        _nx = omap(float(segs[_marks[_idx + 1][1]].get("start") or 0),
                                   snap=True)
                    _b = _nx if _nx and _nx > _a else min(_a + 12.0, _outdur_guess(spans))
                    if _b - _a < 1.0:
                        continue
                    _items = [(_lab[_m] if _m <= _k and _m in _lab else RL._mm(_m))
                              for _m in range(1, _n + 1)]
                    _states.append((_a, _b, _items, _k - 1,
                                    tuple(range(0, _k - 1))))
                for _i2, (_a, _b, _items, _act, _done) in enumerate(_states):
                    _png = os.path.join(_work_r, f"r{_i2:02d}.png")
                    RL.panel(_head, _items, active=_act, done=_done,
                             W=TH["W"], H=TH["H"], accent=_acc,
                             mmf=rc["mmf"]).save(_png)
                    rmov.append((round(_a, 2), _png, round(_b - _a, 2)))
                if rmov:
                    log(f"  ဘေးဘောင် စာရင်း ·「{_head}」· item {_n} · "
                        f"အခြေအနေ {len(rmov)} ခု · "
                        f"{rmov[0][0]:.1f}–{rmov[-1][0] + rmov[-1][2]:.1f}s")
        except Exception as _re2:
            log(f"  ⚠️ ဘေးဘောင် စာရင်း မရ: {type(_re2).__name__}: {_re2}")
    # ══ Headtop — ဘောင်အပြည့် ကတ်ကို **ဖြတ်ပြောင်း** အဖြစ် ထုတ်သည် ═══════
    # ⚠️ ထပ်တင်လို့ မရပါ。 ပြောသူက ဘောင်ရဲ့ ၆၄% (မျက်နှာဇုန် ၀–၆၉၆px) ယူပြီး
    #    စာတန်းက ၇၀% (၇၅၇px) ကနေ စသဖြင့် ကျန်နေရာက **၆၁px = ၅.၆% ·H** သာ。
    #    template တွေက ၅၀၇–၁၀၇၉px ရှိ၍ ၄ ခုလုံး 「နေရာ မတည့်」နဲ့ ပယ်ခံခဲ့သည်
    #    (၂၀၂၆-၀၉-၂၁ j_d651c2ef2292 — ဂရပ်ဖစ် တပ်ပြီး ၀ ခု)。
    #    ⇒ reference လိုပဲ **ပြောသူကို ဖုံးပြီး** ကတ် ပြရသည် (Zin အတည်ပြု)。
    if (_PLAN and _PLAN.get("templateEvents")
            and (not _side_ok or _full_plan_ids)):
        try:
            import slide as SL2
            import dress as _DR
            work_s = os.path.join(work, "sl"); os.makedirs(work_s, exist_ok=True)
            SL2.setsize(TH["W"], TH["H"])
            _bn = (brand or {}).get("name") or rc["label"]
            _nok = _nno = 0
            # ⚠️ **keyword pop ကို ဒီထဲ မထည့်ရ** — အဲဒါတွေက ထပ်တင် ဖြစ်ပြီး
            #    ဘောင်အပြည့် ဖြတ်ပြောင်း မဟုတ်ပါ。 မခွဲလျှင် စကားလုံးတစ်လုံးအတွက်
            #    ဗီဒီယိုတစ်ခုလုံး ဖုံးသွားမည် (၂၀၂၆-၀၉-၂၁ ထည့်စဉ် ဖမ်းမိ)。
            _cut_ev = [x for x in _PLAN["templateEvents"]
                       if (x.get("style") or {}).get("kind") != "pop"
                       and (not _side_ok or x.get("id") in _full_plan_ids)]
            for _i, _ev in enumerate(sorted(_cut_ev,
                                            key=lambda x: x.get("startTime") or 0)):
                _cid = _ev.get("motionKitTemplateId")
                _a0 = omap(float(_ev.get("startTime") or 0), snap=True)
                if _a0 is None:
                    continue
                _b0 = _a0 + max(1.5, min(4.5,
                                float(_ev.get("endTime") or 0) - float(_ev.get("startTime") or 0)))
                _head = (_ev.get("props") or {}).get("q") \
                    or (_ev.get("props") or {}).get("text") \
                    or (_ev.get("props") or {}).get("title") \
                    or ((_ev.get("props") or {}).get("items") or [""])[0]
                _pp = os.path.join(work_s, f"p{_i:02d}.png")
                try:
                    SL2.statement(str(_head)[:60], index=_i + 1,
                                  brand=_bn).convert("RGB").save(_pp)
                except Exception:
                    _pp = None
                _mv = None
                try:
                    _mv = _DR.slide_clip(
                        "statement", str(_head)[:60], None, None, _bn,
                        os.path.join(work_s, f"p{_i:02d}.mov"), _b0 - _a0,
                        log=log, fps=rc["fps"],
                        template=_cid, props=_ev.get("props") or {})
                except Exception as _e:
                    log(f"  ⊘ ဖြတ်ပြောင်း ဆောက်မရ: {_cid} — {type(_e).__name__}: {_e}")
                if _mv:
                    _nok += 1; slides.append((_mv, _a0, _b0, "statement"))
                elif _pp:
                    _nno += 1; slides.append((_pp, _a0, _b0, "statement"))
            # ══ keyword pop — ပြောသူပေါ် ထပ်တင် ═══════════════════
            # ⚠️ `docs/HEADTALK_STYLE.md` — reference က စာလုံးကို ပြောသူပေါ်
            #    တိုက်ရိုက် တင်ပြီး **မျက်နှာကိုသာ ရှောင်**သည် (၈–၁၆%H)。
            # ⚠️ template မှာ `x` မရှိ ⇒ ဘောင်အပြည့် alpha ကို compositor က
            #    **ဘေးတိုက် ရွှေ့**ပေးရသည် (`dx`)。
            for _i, _ev in enumerate([x for x in _PLAN["templateEvents"]
                                      if (x.get("style") or {}).get("kind") == "pop"]):
                _st = _ev.get("style") or {}
                _a0 = omap(float(_ev.get("startTime") or 0), snap=True)
                if _a0 is None:
                    continue
                _d = max(1.2, min(5.2, float(_ev.get("endTime") or 0)
                                  - float(_ev.get("startTime") or 0)))
                _pr = dict(_ev.get("props") or {})
                # ⚠️ **တိုင်းထားသော ပြောင်းလဲမှု ၂ ခု** (၂၀၂၆-၀၉-၂၁ · y=216/486/756
                #    သုံးမျိုးနဲ့ စမ်းပြီး) —
                #    ① `y` က စာလုံးရဲ့ **အပေါ်စွန်း** · ink အလယ် = y + ၁၀.၄%H
                #       ⇒ လိုချင်သော အလယ်မှတ်ကနေ ပြန်နုတ်ရမည်
                #    ② `size` က **em box** — size ၁၀၉ ⇒ ink ၈.၄%H သာ
                #       ⇒ ၁.၂၀ ဆ တင်မှ တိုင်းထားသော ၁၀.၁%H ရသည်
                #       (「em-vs-ink」ထောင်ချောက် — caption မှာလည်း ဖြစ်ဖူးသည်)
                _cy = float(_st.get("cy") or 0.5)
                _h = float(_st.get("h") or 0.101)
                _pr["size"] = int(round(_h * 1.20 * TH["H"]))
                # ⚠️ အပေါ်စွန်း↔အလယ် ကွာဟမှုက **size နဲ့ အတူ ကြီး**သည် —
                #    တိုင်းချက် (@1080): size ၁၀၉ ⇒ ၀.၁၀၄ · size ၁၃၁ ⇒ ၀.၁၄၀
                #    ⇒ မျဉ်းကြောင်း k = ၀.၀၀၁၆၃၆·size − ၀.၀၇၄၃၇
                #    ကိန်းသေ တစ်ခုတည်း သုံးလျှင် အကြီးမှာ ၄.၅% လွဲသည်。
                _k = 0.0016364 * _pr["size"] - 0.07437
                _pr["y"] = max(0, int(round((_cy - _k) * TH["H"])))
                try:
                    _pv = _DR.slide_clip(
                        "statement", str(_pr.get("text") or "")[:24], None, None,
                        _bn, os.path.join(work_s, f"w{_i:02d}.mov"), _d,
                        log=log, fps=rc["fps"],
                        template=_ev.get("motionKitTemplateId"), props=_pr)
                except Exception as _e:
                    log(f"  ⊘ pop ဆောက်မရ: {type(_e).__name__}: {_e}"); _pv = None
                if _pv:
                    # ⚠️ **အကျယ်ကို မှန်းဆ၍ မရ** — plan က စာလုံးရေနဲ့ ခန့်မှန်းသည်
                    #    (`0.024·len`)。 တကယ် render ပြီးမှ တိုင်းလျှင် 「Language
                    #    school」က ဘယ်အစွန်းမှာ **ပြတ်**နေခဲ့သည် (၂၀၂၆-၀၉-၂၁
                    #    j_ca015ef1a522 ၆.၈s)。 ⇒ ထွက်လာသော ပုံကနေ တိုင်းပြီး
                    #    ဘောင်ထဲ ဝင်အောင် ပြန်ချိန်သည်。
                    _dx = int(round((float(_st.get("cx") or 0.5) - 0.5) * TH["W"]))
                    try:
                        _ink = _pop_ink(_pv, work_s, _i)
                        if _ink:
                            _ix0, _ix1 = _ink
                            _w = _ix1 - _ix0
                            _want = float(_st.get("cx") or 0.5) * TH["W"]
                            _dx = int(round(_want - (_ix0 + _ix1) / 2.0))
                            _m = int(TH["W"] * 0.02)          # အနားကွက်
                            _dx = max(_m - _ix0, min(TH["W"] - _m - _ix1, _dx))
                            if _w > TH["W"] - 2 * _m:
                                _dx = int(round((TH["W"] - _w) / 2.0 - _ix0))
                    except Exception as _we:
                        log(f"  ⚠️ pop အကျယ် မတိုင်းနိုင် ({type(_we).__name__})")
                    pmov.append((round(_a0, 2), _pv, round(_d, 2), _dx,
                                 str(_pr.get("text") or "")[:18]))
            if pmov:
                log(f"  keyword pop · {len(pmov)} ခု · "
                    + " · ".join(f"「{t}」{a:.1f}s" for a, _m, _d, _x, t in pmov[:4]))

            log(f"  ဖြတ်ပြောင်း · motionkit {_nok} ခု"
                + (f" · စာရွက် ပြန်ဆုတ် {_nno} ခု" if _nno else ""))
            # ⚠️ **ဖုံးအုပ်မှုကို ဘောင်ထဲ ချရမည်**。 ကတ် ၃ ခု × ၂.၅s =
            #    ၇.၇s ÷ ၇၇.၆s = ၀.၀၉၉ ဖြစ်ပြီး QC `gfx_share` (၀.၁၇–၀.၂၅)
            #    ကျခဲ့သည် (၂၀၂၆-၀၉-၂၁)。 `_fit_slides()` က ဒီအတွက် ရေးထားပြီးသား
            #    — ဘောင်ရဲ့ **အလယ်** ဆီ ချိန်ပေးသည် ⇒ ပြန်ရေးစရာ မလို。
            _shb3 = rc.get("gfx_share") or (0.17, 0.25)
            _od3 = sum(b - a for a, b in spans) or float(m["dur"])
            _cmax3 = min(float(rc.get("card_max_s") or QC.CARD_MAX),
                         float(QC.CARD_MAX))
            slides, _why3 = _fit_slides(slides, float(_shb3[0]) * _od3,
                                        float(_shb3[1]) * _od3, _cmax3,
                                        dur=_od3, log=log)
            gfx = []          # ⚠️ ထပ်တင် မလုပ်တော့ — ဖြတ်ပြောင်း ဖြစ်သွားပြီ
        except Exception as _e:
            log(f"  ⚠️ ဖြတ်ပြောင်း မရ ({type(_e).__name__}: {_e})")
    if rc.get("slides") and segs:
        try:
            import slide as SL2
            if not SL2.available():
                raise RuntimeError("cttext မရှိ")
            _od2 = sum(b - a for a, b in spans) or float(m["dur"])
            _shb2 = rc.get("gfx_share") or (0.10, 0.17)
            _mid = (float(_shb2[0]) + float(_shb2[1])) / 2.0
            # reference: ပျမ်းမျှ ၆.၂s ⇒ လိုအပ်သော အရေအတွက်
            # ⚠️ **၁၀ မိနစ်လျှင် ၁၁.၆ ခု** — reference ၂ ခု (၂၃ slide) တိုင်းချက်。
            #    အရင်က ၁၈ ခု ထုတ်ခဲ့ပြီး slideshow ဖြစ်နေသည် ဟု Zin ဆိုသည်。
            # ⚠️ အောက်ဆုံး ၃ ခု ဟု **အတင်း မထားရ** — ၆၅s ဗီဒီယိုမှာ slide ၃ ခုက
            #    ၄၄.၇% ယူသွားပြီး QC `gfx_share` (band ၀.၁၀–၀.၁၇) ကျခဲ့သည်
            #    (j_62a25d9d5f43 · ၂၀၂၆-၀၉-၁၉)。 band ခွင့်ပြုတဲ့ အရေအတွက်ကို
            #    အမြင့်ဆုံး ယူသည် — slide တစ်ခု ပျမ်းမျှ ၆.၂s ဟု reference。
            # ⚠️ **အောက်ဘောင် ရောက်နိုင်လောက်အောင် တောင်းရမည်**。 slide တစ်ခုရဲ့
            #    အများဆုံး အရှည် `card_max` ဖြစ်၍ အောက်ဘောင်ကို ရဖို့
            #    အနည်းဆုံး `floor_s / card_max` ခု လိုသည် — မတောင်းလျှင်
            #    ဘယ်လောက် ဆန့်ဆန့် ဘောင် မရောက်ဘဲ QC `gfx_share` ကျမည်
            #    (၆၀၀s ဗီဒီယိုမှာ slide ၃ ခု = ၃၁s · အောက်ဘောင် ၆၀s လို)。
            # ⚠️ **ဂိတ်ထက် လျှော့လို့ ရသည်、တင်လို့ မရ**。 ၂၀၂၆-၀၉-၂၀:
            #    ref-slides က recipe မှာ ၁၇.၀ ထားပြီး render က အဲဒါ သုံး၊
            #    QC က `CARD_MAX` ၁၀.၅ သုံးသဖြင့် ၁၅.၈s slide ထုတ်ကာ
            #    `card_len` ကျခဲ့သည် (j_bd28f6df827f)。 ⇒ `min()` ဖြင့်
            #    ချည်နှောင်ထားသည် — ဂိတ်ကို ဘယ်တော့မှ မကျော်နိုင်တော့。
            #    ဂိတ်ကိုယ်တိုင် တင်ချင်လျှင် `core/qc.py` ရဲ့ CARD_MAX ကို
            #    **Zin အတည်ပြုမှ** ပြင်ရမည် ("ဂိတ် မလျှော့ရ")。
            _cmax0 = min(float(rc.get("card_max_s") or QC.CARD_MAX),
                         float(QC.CARD_MAX))
            # ⚠️ **အောက်ဘောင်ကို မချိန်ရ — အလယ်ကို ချိန်ရ**。 အောက်ဘောင်နဲ့
            #    တွက်လျှင် ၁၄၀s မှာ slide ၄ × ၁၀.၅ = ၀.၃၀၀ တိတိ ဖြစ်ပြီး
            #    render drift နည်းနည်းနဲ့ ကျသွားသည် (j_dd56e503c95c က ၀.၀၉၉/၀.၁၀)。
            #    အလယ်နဲ့ တွက်လျှင် ၅ × ၁၀.၀၈ = ၀.၃၆၀ — နှစ်ဖက်စလုံး လွတ်သည်。
            #    ⚠️ ဤနေရာက `_mid` က **အချိုး** (ဥပမာ ၀.၃၆) — စက္ကန့် မဟုတ်。
            #       `_od2` နဲ့ မမြှောက်ဘဲ သုံးလျှင် အမြဲ ၁ ထွက်သည်。
            _min_n = max(1, int(-(-(_mid * _od2) // _cmax0)))   # ceil(အလယ်s ÷ card_max)
            _cap_n = max(1, int((float(_shb2[1]) * _od2) // 6.2))
            _wantn = max(_min_n, min(_cap_n, int(round(1.16 * _od2 / 60.0)) or 1))
            specs = TP.slides(segs, want=_wantn, log=log)
            _gslides = len(specs)          # Gemini ပြန်ပေးတဲ့ အရေအတွက်
            # မူရင်း → ဖြတ်ပြီး timeline
            mp = []
            for sp in specs:
                t = omap(float(sp.get("at") or 0), snap=True)
                if t is None: continue
                sp = dict(sp); sp["at"] = round(t, 2); mp.append(sp)
            mp.sort(key=lambda z: z["at"])
            # ⚠️ reference မှာ slide တစ်ခု ၁.၅–၁၇.၀s ရှိသည် (ပျမ်းမျှ ၆.၂)。
            #    Gemini က slide နည်းနည်းပဲ ပြန်ပေးလျှင် ရှည်ရှည် ပြ၍ band ကို
            #    ရောက်နိုင်သည် — ၁၂s အထိ ခွင့်ပြုသည် (reference ရဲ့ ဘောင်အတွင်း)。
            # ⚠️ အရှည်ကို **ပုံသေ မထားရ**。 reference မှာ ၀.၅s မှ ၁၇.၀s အထိ
            #    ကွဲပြားသည် — အတို ၂၂% · အလတ် ၅၇% · အရှည် ၂၂% (တိုင်းထားသည်)。
            #    ⇒ **စာသား ပမာဏနဲ့ အချိုးကျ** ထားသည်: ဖတ်ရမယ့် စာ များလျှင်
            #      ကြာကြာ ပြရသည်、တစ်ကြောင်းတည်းဆိုလျှင် မြန်မြန် ကျော်ရသည်。
            def _hold_of(x):
                """ဖတ်ရမယ့် စာ ပမာဏနဲ့ layout အလိုက် အရှည်。

                ⚠️ စာလုံးရေ တစ်ခုတည်းနဲ့ တွက်လျှင် အားလုံး ၃–၇s အတွင်း
                   စုပြုံနေပြီး reference ရဲ့ **၀.၅–၁၇.၀s ကွဲပြားမှု** မရ。
                   ⇒ layout အလိုက် ခွဲရသည် — စာရင်းက ဖတ်ရချိန် အများကြီး လို၊
                     စကားတစ်ခွန်းက မြန်မြန် ကျော်ရသည်。
                """
                lay = x.get("layout")
                ch = len(x.get("head") or "") + sum(len(t) for t in (x.get("items") or []))
                if lay == "bignum":
                    return max(1.5, min(3.0, 1.5 + len(x.get("num") or "") * 0.15))
                if lay == "bullets":
                    return max(7.0, min(14.0, 3.0 + ch / 11.0))
                # statement — တိုလျှင် လျှပ်တပြက်、ရှည်လျှင် ဖတ်ချိန် ပေး
                if ch <= 26: return max(2.0, min(3.0, 1.6 + ch / 26.0))
                return max(3.2, min(6.5, 2.2 + ch / 16.0))
            # ⚠️ **တစ်ပြေးညီ ခြားခိုင်းလို့ မရ**。 အရင်က အနည်းဆုံး ၈s ခြားခိုင်းပြီး
            #    တစ်ပြေးညီ ဖြန့်ခဲ့သဖြင့် slideshow ဖြစ်နေခဲ့သည်。 reference မှာ
            #    အစုလိုက် (၆–၁၅s ခြား) လာပြီး ကြားထဲ ၄၀–၁၂၀s လုံးဝ မပါ。
            #    ⇒ **ထပ်နေတာကိုသာ** တားသည်、အကွာအဝေး မကန့်သတ်ရ。
            keep, lastend = [], -1e9
            for sp in mp:
                h = _hold_of(sp)
                if sp["at"] < lastend + 2.0: continue      # ထပ်နေ၍သာ ကျော်
                if sp["at"] + h > _od2 - 1.0: break
                sp = dict(sp); sp["_hold"] = h
                keep.append(sp); lastend = sp["at"] + h
            # ⚠️ slide ကို **ထွက်ဘောင်ရဲ့ အရွယ်နဲ့** ထုတ်ရမည် — မလုပ်လျှင်
            #    ၁၉၂၀×၁၀၈၀ slide က ၁၀၈၀×၁၄၄၀ ဘောင်ပေါ် ညာပြတ် ဘဝင်ကျန်
            #    ဖြစ်သည် (၂၀၂၆-၀၉-၂၀ တကယ် ဖြစ်ခဲ့)。
            _slspec = {}
            SL2.setsize(TH["W"], TH["H"])
            log(f"  slide ဘောင် {TH['W']}×{TH['H']}")
            work_s = os.path.join(work, "sl"); os.makedirs(work_s, exist_ok=True)
            acc = (brand or {}).get("colors") or []
            accent = acc[2] if len(acc) > 2 else "#FFC400"
            bname = (brand or {}).get("name", "")
            kw = dict(accent=accent, mmf=rc.get("mmf") or "Pyidaungsu-Bold",
                      lat=rc.get("latin") or "Helvetica-Bold", brand=bname,
                      total=len(keep))
            for i, sp in enumerate(keep):
                fn = SL2.LAYOUTS.get(sp["layout"], SL2.statement)
                if sp["layout"] == "bullets":
                    im = fn(sp["head"], sp.get("items") or [], index=i + 1, **kw)
                elif sp["layout"] == "bignum":
                    im = fn(sp.get("num") or "—", sp["head"], index=i + 1, **kw)
                else:
                    im = fn(sp["head"], index=i + 1, **kw)
                pp = os.path.join(work_s, f"s{i:02d}.png")
                im.convert("RGB").save(pp)
                slides.append((pp, sp["at"], sp["at"] + sp["_hold"], sp["layout"]))
                # ⚠️ နောက်ဆုံး ကြာချိန်က `_fit_slides` ပြီးမှ သိရသဖြင့်
                #    motionkit clip ကို **အဲဒီနောက်မှ** ထုတ်သည် (spec သိမ်းထား)
                _slspec[pp] = sp
            # ⚠️ **band အောက် ကျလျှင် ဆွဲတင်ရမည်**。 Gemini က slide နည်းနည်းပဲ
            #    ပြန်ပေးလျှင် ဖုံးအုပ်မှု ၀.၀၉၇ ဖြစ်ပြီး ၀.၁၀ ဘောင် လွဲသည်
            #    (တကယ် ဖြစ်ခဲ့)。 reference မှာ ၁၇.၀s slide ရှိသဖြင့် အဲဒီအထိ
            #    ဆန့်လို့ ရသည် — ရှည်ဆုံးကနေ စပြီး တိုးသည်。
            # ⚠️ **ဘောင် အလယ်ကို ချိန်ရမည် — အနားကို မချိန်ရ**。
            #    အရင်က အောက်ဘောင်ကို တင်၊ အထက်ဘောင်ကို ချုံ့ ဟု သီးသန့် ၂ ခု
            #    လုပ်ခဲ့ရာ ဖုံးအုပ်မှု ၀.၁၀၁ (ဂိတ် ၀.၁၀) ဆိုတဲ့ အနားကပ် တန်ဖိုး
            #    ဖြစ်သွားပြီး — QC က **ထွက်ဖိုင်ရဲ့ ကြာချိန်**နဲ့ ပြန်တွက်သဖြင့်
            #    drift အနည်းငယ်နဲ့ ၀.၀၉၉ ကျကာ FAIL ဖြစ်ခဲ့သည် (j_dd56e503c95c)。
            #    ⇒ ပစ်မှတ်ကို **အလယ်** ထားပြီး တစ်ခါတည်း ချိန်သည်。
            if slides:
                _cmax = min(float(rc.get("card_max_s") or QC.CARD_MAX),
                            float(QC.CARD_MAX))   # ဂိတ်ထက် မကျော်ရ
                _lo   = float(_shb2[0]) * _od2
                _hi   = float(_shb2[1]) * _od2
                slides, _why = _fit_slides(slides, _lo, _hi, _cmax, dur=_od2, log=log)
                for _m in _why: log("  " + _m)
                # ── slide ကို **motionkit template** နဲ့ ပြန်ထုတ် ──
                # ⚠️ Zin ၂၀၂၆-၀၉-၂၀: IKKI ကိုယ်ပိုင် ဖြူဖြူ slide မသုံးတော့。
                #    မရလျှင် PNG အတိုင်း ချန်သည် (job မကျစေရန်)。
                _bn = (brand or {}).get("name") or "IKKI"
                # ⚠️ **ပုံသေက စာရွက်ပုံစံ (အလင်း) slide** — ၂၀၂၆-၀၉-၂၀ Zin ရဲ့
                #    reference (`01BnhfTaQoo`) ကို တိုင်းတော့ ဘောင်အပြည့် ကတ်က
                #    **တောက်ပမှု ၂၃၆/၂၅၅** (စာရွက် · အစက်ကွက် · မှောင်သော စာ)。
                #    motionkit ရဲ့ `prem.*` က အနက် gradient ဖြစ်၍ ကွဲသည်。
                #    ⇒ `slide_src="mk"` ရွေးမှသာ အနက်ကတ် သုံးသည်。
                _use_mk = str(rc.get("slide_src") or "paper").lower() == "mk"
                _mk_ok, _mk_no = 0, 0
                _sl2 = []
                for _p, _a, _b, _l in slides:
                    _sp = _slspec.get(_p)
                    _mv = None
                    if _use_mk and _sp is not None:
                        _mv = DR.slide_clip(_l, _sp.get("head") or "", _sp.get("items"),
                                            _sp.get("num"), _bn,
                                            os.path.join(work_s, os.path.basename(_p)[:-4] + ".mov"),
                                            _b - _a, log=log, fps=rc["fps"])
                    if _mv: _mk_ok += 1; _sl2.append((_mv, _a, _b, _l))
                    else:   _mk_no += 1; _sl2.append((_p, _a, _b, _l))
                slides = _sl2
                log("  slide · " + (f"motionkit {_mk_ok} ခု"
                    + (f" · စာရွက် ပြန်ဆုတ် {_mk_no} ခု" if _mk_no else "")
                    if _use_mk else f"စာရွက်ပုံစံ {_mk_no} ခု (reference အတိုင်း)"))
            # ⚠️ ဘောင် မရောက်နိုင်လျှင် **အကြောင်းရင်း ကျယ်ကျယ် ပြောရမည်** —
            #    QC က နောက်မှ ကျမည် ဖြစ်ပြီး ဘာကြောင့်လဲ မသိရလျှင် ရှာရ ခက်သည်。
            if slides:
                _c2 = sum(b - a for _p, a, b, _l in slides)
                if _c2 < float(_shb2[0]) * _od2:
                    log(f"  ⚠️ slide ဖုံးအုပ်မှု {_c2/_od2:.3f} < ဂိတ် {_shb2[0]:.2f} — "
                        f"slide {len(slides)} ခုသာ ရ (တောင်း {_wantn} · "
                        f"အနည်းဆုံး လို {_min_n})。 QC `gfx_share` ကျနိုင်သည်。")
            if slides:
                _ln = [b - a for _p, a, b, _l in slides]
                cov = sum(_ln) / _od2
                _gp = [slides[k+1][1] - slides[k][2] for k in range(len(slides)-1)]
                log(f"  slide {len(slides)} ခု · အရှည် {min(_ln):.1f}–{max(_ln):.1f}s "
                    f"(အလယ် {sorted(_ln)[len(_ln)//2]:.1f}s) → ဖုံးအုပ်မှု {cov:.3f}")
                if _gp:
                    log(f"        အကွာအဝေး {min(_gp):.0f}–{max(_gp):.0f}s "
                        f"(အလယ် {sorted(_gp)[len(_gp)//2]:.0f}s · reference ၂၉–၄၀s)")
        except Exception as e:
            log(f"  ⚠️ slide မရ: {e}")
            slides = []

    # ── စာတန်း track (ဂရပ်ဖစ် သိပြီးမှ — ဖျောက်ရန်) ──
    capv = os.path.join(work, "caps.mov") if (caps and csize) else None
    if capv:
      try:
          # ⚠️ **စာတန်း နောက်ခံကို တိုင်းပြီးမှ** ဆုံးဖြတ်ရသည်。 IKKI ရဲ့
          #    အဖြူစာတန်းက အဖြူနံရံ/မိုးကောင်းကင်ပေါ် ပျောက်သွားသည် —
          #    `IKKI_Premium_v2.mp4` မှာ နမူနာ **၁၃/၁၃ လုံး** WCAG ၃:၁
          #    မမီခဲ့ (၂.၁၃–၂.၇၅)。 plate ခံလျှင် ၆.၅၆ ရသည် (စမ်းပြီး)。
          # ⚠️ `CP.track` က plate တစ်ခုတည်းသာ ယူသဖြင့် **စာတန်းအများစု**
          #    ကျမှ ဖွင့်သည် — တစ်ကြောင်းနှစ်ကြောင်းအတွက် တစ်ဗီဒီယိုလုံး
          #    အကွက် ခံလျှင် ပိုဆိုးသည်。
          _plate = _plate_decide(src, caps, cap_top, TH["H"], rc, log)
          CP.track(caps, capv, os.path.join(work,"cp"),
                   # ⚠️ အရောင်ကို recipe က ပြင်နိုင်သည် — မပြင်လျှင် theme ရဲ့ ပုံသေ
                   TH["W"], TH["H"], csize,
                   rc.get("cap_fill") or TH["WHITE"], rc["mmf"],
                   f'{TH["LATIN"]},{TH["JP"]}', TH["BOT"],
                   IG.ct, IG.MW, fps=rc["fps"],
                   # ⚠️ `"brand"` ဆိုလျှင် **brand ရဲ့ အရောင်** ကို ယူသည် —
                   #    ကိန်းသေ ရေးထားလျှင် logo ပြောင်းလည်း ZAE navy ပဲ
                   #    ထွက်နေသည် (Zin ၂၀၂၆-၀၉-၂၀)。 brand က logo ကနေ
                   #    အရောင် ထုတ်ပြီး `bd["colors"]` ⇒ `TH` ထဲ ဝင်ပြီးသား。
                   stroke=_cap_stroke(rc, TH),
                   stroke_w=rc.get("stroke_w") or 0.0,
                   hold=float(rc.get("cap_hold") or 4.0),
                   gap_pct=float(rc.get("cap_gap") or 0.18),
                   wide=float(rc.get("cap_wide") or 0.86),
                   fade=float(rc.get("cap_fade") or 0.14),
                   # ⚠️ ဂရပ်ဖစ် ပေါ်နေချိန် စာတန်း ဖျောက်ရသည် (Zin: "Infography
                   #    ဝင်လာရင် subtitle ဖျောက်ထားပေး") — ဒါပေမယ့် **စာတန်းဇုန်နဲ့
                   #    တကယ် ထပ်တဲ့ ဂရပ်ဖစ်မှာသာ**。 N5 reference မှာ ထောင့်က
                   #    ဂရပ်ဖစ် (chapter · id_strip) နဲ့ စာတန်း တစ်ပြိုင်နက်
                   #    ပြသည် — အကုန် ဖျောက်လျှင် စာတန်း ၂၉% ပျောက်သွားသည်。
                   # ⚠️ full-frame slide ပေါ်နေချိန် စာတန်းကို **အမြဲ ဖျောက်**ရမည် —
                   #    slide က မျက်နှာပြင် တစ်ခုလုံး ဖုံးထားသဖြင့် စာတန်းက
                   #    အဖြူပေါ် အဖြူ ဖြစ်ပြီး လုံးဝ မဖတ်ရ。
                   hide=[(at, at+d) for at, _m, d, _y0, y1 in (gmov or [])
                         if y1 > cap_top - 20]
                        + [(a, b) for _p, a, b, _l in (slides or [])],
                   plate=_plate,
                   log=log,
                   # ⚠️ `total` ကို **ပေးရမည်** — မပေးလျှင် track က နောက်ဆုံး
                   #    စာတန်းမှာ ကုန်သွားပြီး overlay ရဲ့ `repeatlast` ပုံသေက
                   #    အဲဒီ frame ကို ဗီဒီယို အဆုံးထိ ထပ်ပြနေသည်。 ZAE short
                   #    မှာ "လေ့ကျင့်ပေးပါတယ်" က ၄၀s မှ ၅၈s ထိ ငြိနေခဲ့သည်。
                   total=float(sum(b-a for a, b in spans)))
          log(f"  စာတန်း {len(caps)} ကြောင်း · {csize}px")
      except Exception as e:
          log(f"  ⚠️ စာတန်း မရ: {e}"); capv=None

    # ── ⑥ ဖြတ်ပြီး ပေါင်း ──────────────────────────────────
    # ── B-roll — စကားနဲ့ ကိုက်တဲ့ ရုပ် ──
    #    ⚠️ B-roll က **ရုပ်ကိုပဲ** အစားထိုးသည် — စကားသံက အောက်မှာ ဆက်နေရမည်。
    #    အသံ ထည့်လျှင် စကား ထပ်ပြီး ဘာမှ မကြားရ。
    #    ⚠️ ဖြတ်ပြီးနောက် အချိန် ရွှေ့သွားသဖြင့် caps (remap ပြီးသား) ကို
    #    အခြေခံရမည် — မူရင်း segs ကို မသုံးရ。
    bmov = []
    nb = int(rc.get("broll") or 0)
    if nb and caps:
        try:
            hits = BR.match(caps, nb, log=log, strict=bool(rc.get("broll_strict")))
            for si, clip, sc in hits:
                c = caps[si]
                # ⚠️ အရှည်ကို recipe က ကန့်သတ် — ၃.၂s ပုံသေက ZAE အတွက်
                #    တိုလွန်းပြီး ခွင့်ပြု ၃၆s ထဲ ၁၅s ပဲ သုံးနိုင်ခဲ့သည်。
                _bmax = rc.get("broll_max") or 3.2
                d = min(clip["dur"], max(1.2, min(_bmax, c["end"]-c["start"])))
                if d < 1.0: continue
                bp = os.path.join(work, f"b{si}.mp4")
                BR.prep(clip, TH["W"], TH["H"], d, bp, fps=rc["fps"])
                bmov.append((round(c["start"],2), bp, round(d,2),
                             " · ".join(clip.get("my") or [])[:28]))
            bmov.sort(key=lambda x: x[0])
            # ⚠️ ထပ်နေတာ မရှိစေရ — နောက်ဟာက ရှေ့ဟာ ပြီးမှ စရမည်
            # ⚠️ **ပွင့်ချင်း ၀.၈s ကို B-roll မဖုံးရ** — ပထမ စမ်းမှာ ၀.၀၀s မှ
            #    စခဲ့သဖြင့် ဗီဒီယိုက ပြောသူကို မပြဘဲ ရုပ်ကြမ်းနှင့် ပွင့်ခဲ့သည်。
            # ⚠️ B-roll စုစုပေါင်း **အရှည်၏ ၃၀% ထက် မပိုရ** — ၁၄s ဗီဒီယိုမှာ
            #    ၆.၄s (၄၆%) ဖြစ်ခဲ့ပြီး မူရင်းထက် ရုပ်ကြမ်း ပိုမြင်ခဲ့သည်。
            # ⚠️ ခွင့်ပြုချက်ကို **recipe က ဆုံးဖြတ်**ရမည် — ပုံစံအလိုက်
            #    လုံးဝ ကွာသည်。 ZAE ကြော်ငြာက ၆၂% · podcast က ၀%。
            BUD = max(3.2, sum(y-x for x,y in spans) * (rc.get("broll_pct") or 0.30))
            # ⚠️ ဖွင့်ခန်း နှင့် နိဂုံးကို **ပြောသူ ရှိရမည်** — N5 reference ကို
            #    shot အလိုက် တိုင်းတော့ ပထမ ၂.၄s က ပြောသူ၊ နောက်ဆုံး ၁၃.၅s ကလည်း
            #    ပြောသူ ဖြစ်သည်。 IKKI ထုတ်ခဲ့တာက ၁.၀s ကနေ ၁၆s ထိ ရုပ်ကြမ်း
            #    ချည်း ဖြစ်ခဲ့ပြီး ပြောသူ လုံးဝနီးပါး မပေါ်ခဲ့。
            HEAD = 2.4
            TAIL = float(rc.get("broll_tail") or 5.0)
            _tot = sum(y-x for x,y in spans)
            keep=[]; end=-1; spent=0.0
            for at,bp,d,tag in bmov:
                if at < HEAD: continue
                if at + d > _tot - TAIL: continue
                if at < end + float(rc.get('broll_gap') or 3.0): continue
                if spent + d > BUD: continue
                keep.append((at,bp,d,tag)); end = at+d; spent += d
            bmov = keep
            # ⚠️ anchor (စာတန်းကြောင်း) ပေါ်မှာပဲ ချလျှင် ခွင့်ပြုချက် မကုန် —
            #    စာတန်း ၉ ကြောင်းပဲ ရှိသဖြင့် ၃၆s ထဲ ၁၇s ပဲ သုံးနိုင်ခဲ့သည်
            #    (reference က ၆၂%)。 ⇒ **ကျန်ကွက်လပ်တွေကို ဖြည့်ရမည်**。
            # Premium talking-head မှာ budget ပြည့်အောင် context မဆိုင်သော stock
            # (ဥပမာ finance talk ထဲ road shot) ဖြည့်လိုက်တာက visual မရှိတာထက်
            # ပိုဆိုးသည်။ strict profile က exact transcript match ရသလောက်သာ သုံးသည်။
            if spent < BUD * 0.85 and not rc.get("broll_strict"):
                total = sum(y - x for x, y in spans)
                usedp = {b[1] for b in bmov}
                pool = [c for c in (BR.load().get("clips") or [])
                        if c.get("path") not in usedp]
                # ⚠️ ကျပန်း ရွေးလျှင် **မဆိုင်တဲ့ ရုပ်** ဝင်လာသည် — ဂျပန်စာ
                #    သင်တန်း ကြော်ငြာရဲ့ ပထမ ၂၀s မှာ ကားအတွင်းခန်း ၃ ခု
                #    ထွက်ခဲ့သည် (တကယ် ဖြစ်ခဲ့)。
                #    ⇒ စာတမ်းတစ်ခုလုံးနှင့် တူမှုအမှတ်ဖြင့် **အဆင့်ခွဲ**ပြီး
                #      အမှတ်ရသူကို ဦးစားပေးသည်。 အမှတ် ၀ ချည်းဖြစ်မှ ကျပန်း。
                import random as _rnd
                _rnd.Random(sum(ord(c) for c in str(job.get("id") or ""))).shuffle(pool)
                # ⚠️ စာလုံးတူမှု အမှတ်ဖြင့် **မရွေးရ** — တိုင်းကြည့်ရာ
                #    ဂျပန်စာသင်တန်း ကြော်ငြာအတွက် အမြင့်ဆုံး အမှတ်က
                #    "ဂျပန်ပုံစံ ထမင်းစားခန်း" ဖြစ်နေပြီး "ကျောင်းသား ·
                #    လက်ပ်တော့" က နိမ့်နေသည် ("ဂျပန်" စာလုံး ထပ်လို့)。
                #    ⇒ **အဓိပ္ပာယ်ကို Gemini ကို မေး**ရသည်。 မရလျှင်
                #      ကွက်လပ် မဖြည့်ဘဲ ပြောသူကို ပြထားသည်。
                try:
                    pool = BR.suitable(caps, pool, log=log)
                except Exception as e:
                    log(f"  ⚠️ B-roll ရွေးမရ: {e}"); pool = []
                import random as _rnd
                _rnd.Random(sum(ord(c) for c in str(job.get("id") or ""))).shuffle(pool)
                occ = sorted((at, at + d) for at, _, d, _ in bmov)
                # ⚠️ ဖွင့်ခန်း/နိဂုံး ကန့်သတ်ချက်ကို **ဒီမှာလည်း** သုံးရမည် —
                #    အပေါ်က keep loop မှာပဲ ထားခဲ့သဖြင့် ကွက်လပ်ဖြည့်က
                #    ၁.၀၀s မှာ ချမိပြီး ဗီဒီယိုက ရုပ်ကြမ်းနှင့် ပွင့်ခဲ့သည်
                #    (v24 မှာ တကယ် ဖြစ်ခဲ့ — guard ထည့်ပြီးမှ)。
                t = HEAD; pi = 0; added = 0
                while spent < BUD and pi < len(pool) and t < total - TAIL:
                    # ⚠️ `t` က ရှိပြီးသား clip **အတွင်း** ကျနေလျှင် ရှေ့တိုးရမည် —
                    #    မတိုးလျှင် ထပ်နေသော B-roll ၂ ခု ဖြစ်သည် (တကယ် ဖြစ်ခဲ့:
                    #    25.29s+2.4s အပေါ် 25.49s ထပ်ချမိခဲ့သည်)。
                    # ⚠️ B-roll နှစ်ခုကြား **ပြောသူကို ပြရမည်** — မပြလျှင်
                    #    ရုပ်ကြမ်း စုပြုံပြီး ပြောသူ ပျောက်သွားသည်
                    #    (frame ၆ ခုမှာ ပြောသူ ၁ ခုပဲ ကျန်ခဲ့ — တကယ် ဖြစ်ခဲ့)。
                    GAP = float(rc.get("broll_gap") or 3.0)
                    inside = [b for a, b in occ if a - GAP <= t < b + GAP]
                    if inside:
                        t = max(inside) + GAP
                        continue
                    nxt = next((a for a, b in occ if a > t), total)
                    gap = nxt - GAP - t
                    if gap < 2.2:
                        nb2 = [b for a, b in occ if a > t]
                        t = (min(nb2) + GAP) if nb2 else total
                        continue
                    d = min(rc.get("broll_max") or 3.2, gap - 0.4, BUD - spent,
                            pool[pi]["dur"], max(0.0, total - TAIL - t))
                    if d < 1.5:
                        t += 1.0; continue
                    bp = os.path.join(work, f"bg{added}.mp4")
                    try:
                        BR.prep(pool[pi], TH["W"], TH["H"], d, bp, fps=rc["fps"])
                    except Exception:
                        pi += 1; continue
                    bmov.append((round(t, 2), bp, round(d, 2),
                                 " · ".join(pool[pi].get("my") or [])[:28]))
                    occ = sorted(occ + [(t, t + d)])
                    spent += d; t += d + GAP; pi += 1; added += 1
                bmov.sort(key=lambda x: x[0])
                if added: log(f"  B-roll · ကွက်လပ် ဖြည့် {added} ခု")
            elif spent < BUD * 0.85 and rc.get("broll_strict"):
                log("  B-roll · strict semantic mode — budget ဖြည့်ရန် မဆိုင်သော clip မထည့်")
            if bmov: log(f"  B-roll စုစုပေါင်း {spent:.1f}s / ခွင့်ပြု {BUD:.1f}s")
            for at,_,d,tag in bmov: log(f"  B-roll {at:6.2f}s · {d:.1f}s · {tag}")
            log(f"  B-roll {len(bmov)} ခု တပ်ပြီး")
        except Exception as e:
            log(f"  ⚠️ B-roll မရ: {e}"); bmov=[]

    stage(6, "sound")
    cutv = os.path.join(work, "cut.mp4")
    # ⚠️ fade — calib `edit.fade_s` (Zin ၏ ဖြတ်ဆက် dip အကျယ် ၁၄၅ms · အလယ်တန်ဖိုး)。
    #    နှစ်ဖက် ခွဲသုံးသဖြင့် /2。 calib မရှိလျှင် spans.py ရဲ့ default (20ms)。
    _fd = float(((CUT.calib(_bid) or {}).get("edit") or {}).get("fade_s", 0.0))
    # ⚠️ **ဖြတ်ဆက်ကို framing နဲ့ ဖုံးသည်** (၂၀၂၆-၀၉-၂၀ · Zin: 「cut ဖြတ်တာရော …
    #    quality 0」)。 ကွက်လပ် ကြီးကြီး ဖြုတ်ပြီး တစ်နေရာတည်းက shot ဆက်လျှင်
    #    ပြောသူ ခုန်သွားသည် — ဖြတ်ဆက်တိုင်း wide ↔ punch-in အလှည့်ကျ ပြောင်းလျှင်
    #    **တမင် ဖြတ်ချက်** အဖြစ် ဖတ်ရသည်。
    # ⚠️ ကွက်လပ် သေးသေး (<၀.၄s) မှာ မပြောင်းရ — မျက်စိက မမြင်သော ဆက်မှာ
    #    framing ပြောင်းလျှင် ပိုဆိုးသည်。 span တိုတို (<၀.၈s) မှာလည်း မလုပ်ရ
    #    (မှိတ်တုတ်မှိတ်တုတ် ဖြစ်မည်)。
    _pz = float(rc.get("punch") if rc.get("punch") is not None else SP.PUNCH)
    _zooms, _cur, _nz = {}, 1.0, 0
    if _pz and _pz > 1.0:
        for _i, (_a, _b) in enumerate(spans):
            if _i > 0 and _a - spans[_i-1][1] >= 0.40:
                _cur = _pz if _cur == 1.0 else 1.0
            if _cur > 1.0 and (_b - _a) >= 0.80:
                _zooms[_i] = _cur; _nz += 1
        if _nz: log(f"  ဖြတ်ဆက် ဖုံး — span {_nz}/{len(spans)} ကို {_pz:.2f}× punch-in")
    # Plan က punch-in ကို event အဖြစ် ရေးပေးထားသော်လည်း span တစ်ခုကို crop
    # တစ်မျိုးသာချနိုင်သည်။ အောက်က adapter က event start/end မှာ source span
    # ကို ခွဲ၍ no-cut talking head မှာပါ motion တကယ်ပေါ်စေသည်။
    _render_spans = spans
    if _PLAN and _PLAN.get("cameraReframes"):
        try:
            import execute as EX3
            _render_spans, _zooms = EX3.reframe_spans(_PLAN, spans, _zooms, log=log)
        except Exception as _reframe_e:
            log(f"  ⚠️ plan punch မချနိုင် ({type(_reframe_e).__name__}) — cut framing သာ")
            _render_spans = spans
    SP.spans(src, _render_spans, cutv, os.path.join(work,"sp"), fps=rc["fps"], zooms=_zooms,
             **({"fade": _fd/2.0} if _fd > 0 else {}))
    # ⚠️ ဖြတ်ချက် မရှိသော ဗီဒီယိုမှာ `_zooms` က ဘာမှ မလုပ်နိုင် ⇒ ရုပ်က
    #    လုံးဝ မလှုပ်ဘဲ ဖြစ်သည်。 ⇒ ဆက်တိုက် ချောမွေ့သော zoom ထည့်သည်。
    _za = float(rc.get("zoom_amt") or 0.0)
    # ⚠️ **အမြဲ မှတ်တမ်းတင်ရမည်** — ၂၀၂၆-၀၉-၂၀ မှာ zoom က တိတ်တဆိတ်
    #    မလုပ်ဘဲ ဖြစ်ကာ အောင်/ရှုံး log မရှိ၍ အကြောင်းရင်း မသိခဲ့ရ。
    log(f"  zoom_amt = {_za:.3f} ({'ဖွင့်' if _za > 0.001 else 'ပိတ်'})")
    if _za > 0.001:
        _bz = os.path.join(work, "cutz.mp4")
        try:
            _breathe(cutv, _bz, rc["fps"], _za, TH["W"], TH["H"], log=log)
            os.replace(_bz, cutv)
        except Exception as _e:
            log(f"  ⚠️ zoom မရ ({type(_e).__name__}: {_e}) — မလုပ်ဘဲ ဆက်သွားသည်")
    # ⚠️ ဖြတ်ပြီးမှ **ဖျပ်ခနဲ မြင်ကွင်း** ကျန်မကျန် စစ်သည် — သုံးစွဲသူရဲ့
    #    ဝါကျ ဖျက်ချက်က တခြားနေရာက ရိုက်ထားသော အပိုင်းရဲ့ အစွန်းလေး
    #    ချန်ထားခဲ့လျှင် ၀.၃s လောက် ဖျပ်ခနဲ ပေါ်ပျောက် ဖြစ်သည်。
    #    **ကိုယ်တိုင် မဖျက်ပါ** — သတိပေးရုံသာ (Zin: 「user အတည်ပြုမှ ဖျက်ပေး」)。
    try:
        _fl_sh = _flash_shots(cutv, log=log)
        if _fl_sh:
            _lst = st.get("flag_list") or []
            for _at, _d in _fl_sh[:8]:
                # ⚠️ key က **`text`** ဖြစ်ရမည် — UI က `f.text` ကို ဖတ်သည်。
                #    `why` လို့ ရေးမိ၍ Zin ရဲ့ မျက်နှာပြင်မှာ အကြောင်းအရာ
                #    **ဗလာ** ပေါ်ခဲ့သည် (၂၀၂၆-၀၉-၂၀ သူ့ screenshot)。
                _lst.append({"at": _at, "kind": "flash_shot",
                             "text": f"မြင်ကွင်း {_d:.2f}s သာ ရှိသည် — ဖျပ်ခနဲ "
                                     f"ပေါ်ပြီး ပျောက်သွားမည်။ ဖျက်ထားသော ဝါကျရဲ့ "
                                     f"အစွန်းလေး ကျန်နေခြင်း ဖြစ်တတ်သည် — "
                                     f"အောက်က စာကြောင်း ကပ်လျက်ကိုပါ ဖျက်ပါ "
                                     f"သို့မဟုတ် ဖျက်ထားတာကို ပြန်ထားပါ။",
                             "score": f"{_d:.2f}s"})
            st["flag_list"] = _lst; st["flags"] = len(_lst)
            log(f"  ⚠️ ဖျပ်ခနဲ မြင်ကွင်း {len(_fl_sh)} ခု — "
                + " · ".join(f"{a:.1f}s ({d:.2f}s)" for a, d in _fl_sh[:5]))
            log("     (မဖျက်ပါ — script editor မှာ ပြပါမည်၊ သင် ဆုံးဖြတ်ပါ)")
    except Exception as _e:
        log(f"  ⚠️ မြင်ကွင်း စစ်၍ မရ: {type(_e).__name__}: {_e}")
    # ⚠️ grade ကို **ရုပ်ပေါ်မှာသာ** ချရသည် — overlay တင်ပြီးမှ ချလျှင်
    #    စာတန်း အဖြူက မွဲပြီး stroke ပျက်သည်。 ⇒ ဒီနေရာ (overlay မတင်ခင်)。
    # ⚠️ **အသားအရောင် ချိန်ညှိချက်** (၂၀၂၆-၀၉-၁၇ Zin: "မျက်နှာ အရမ်း မဲနေတယ်")。
    #    grade မချခင် ဖြတ်ပြီး ရုပ်ပေါ်မှာ skin Y ကို တိုင်းပြီး ပစ်မှတ် (၁၅၈) နဲ့
    #    နှိုင်းကာ `gamma` ကို တွက်သည် — **ကိန်းသေ မထားရ**、ဗီဒီယိုအလိုက် ကွာသည်
    #    (studio အဖြူနံရံ ↔ အပြင် backlit shot)。 skin mask = YCbCr。
    try:
        _sy = _skin_y(cutv, log=log)
        if _sy and _sy < 158:          # ⚠️ ပစ်မှတ်နဲ့ တူညီစွာ — grade ရဲ့ levels က
        #    ထပ် ~၁၀ Y ချသေးသည် (v5: pre-grade ၁၅၃ ⇒ ထွက် ~၁၄၃)。
            import math as _mth
            _tgt = 158.0
            _g = _mth.log(max(0.04, _sy) / 255.0) / _mth.log(_tgt / 255.0)
            rc["gamma"] = max(1.0, min(1.25, _g))
            if (rc.get("lv_imin") or 0) > 0.05: rc["lv_imin"] = 0.04
            log(f"  အသားအရောင် · skin Y {_sy:.0f} < ပစ်မှတ် {_tgt:.0f} ⇒ "
                f"gamma {rc['gamma']:.3f} · levels imin {rc.get('lv_imin')}")
        elif _sy:
            log(f"  အသားအရောင် · skin Y {_sy:.0f} — ချိန်ညှိချက် မလို")
    except Exception as e:
        log(f"  ⚠️ အသားအရောင် မတိုင်းနိုင်: {type(e).__name__}: {e}")
    try:
        import grade as GR
        gv = os.path.join(work, "graded.mp4")
        _pre = cutv
        # ⚠️ `shot_grade` ဆိုလျှင် **အပိုင်းလိုက်** ချသည် — အပြင်ဘက်
        #    (highlight ပြတ်နေ) နဲ့ အတွင်းဘက် (အဝါဓာတ်) ကို တူညီစွာ
        #    ကိုင်လျှင် နှစ်ခုလုံး မကောင်းပါ (Zin ၂၀၂၆-၀၉-၂၀)。
        #    `curves`/`eq`/`colorlevels` က `enable=` ထောက်ပံ့သဖြင့်
        #    ဖြတ်/concat ပြန်လုပ်စရာ မလိုပါ (စမ်းပြီး)。
        _sg = None
        if rc.get("shot_grade"):
            try:
                import shotlook as SH
                _segs = SH.scan(cutv, float(probe(cutv).get("dur") or 0), log=log)
                # ⚠️ **အပိုင်း တစ်ခုတည်းဆိုလည်း ကုသမှု ချရမည်**。 အရင်က
                #    `len > 1` ဆိုမှ လုပ်ရန် ရေးမိ၍ ပြောသူရဲ့ မူရင်းရုပ်
                #    (အလင်း တစ်မျိုးတည်း) မှာ source-aware ကုသမှု လုံးဝ
                #    ပစ်ပယ်ခံခဲ့သည် — highlight ပြတ်နေတာ မပြင်ဘဲ ကျန်ခဲ့
                #    (၂၀၂၆-၀၉-၂၁ j_d651c2ef2292)。 တစ်ပိုင်းဆိုလျှင်
                #    ဝင်းဒိုး မလိုဘဲ `rc` ထဲ ပေါင်းရုံ。
                if len(_segs) == 1:
                    _a1, _b1, _k1, _s1 = _segs[0]
                    rc = dict(rc); rc.update(SH.treatment(_k1, _s1))
                    log(f"  grade · အပိုင်း တစ်ခုတည်း ({_k1}) — ကုသမှု တိုက်ရိုက်")
                elif len(_segs) > 1:
                    _parts = []
                    for _a, _b, _k, _st in _segs:
                        _rc2 = dict(rc); _rc2.update(SH.treatment(_k, _st))
                        _fc = GR.chain(_rc2)
                        if _fc:
                            _parts.append(SH.windowed(_fc, _a, _b))
                    if _parts:
                        _sg = ",".join(_parts)
            except Exception as _e:
                log(f"  ⚠️ အပိုင်းလိုက် grade မရ ({type(_e).__name__}: {_e})")
        if _sg:
            ff(["ffmpeg", "-v", "error", "-y", "-i", cutv, "-vf", _sg,
                "-c:v", "h264_videotoolbox",
                "-b:v", _vbr(_TH["W"], _TH["H"], rc["fps"]), "-c:a", "copy", gv])
            cutv = gv
            log(f"  grade · အပိုင်းလိုက် {len(_segs)} ပိုင်း")
        else:
            cutv = GR.apply(cutv, gv, rc, log=log)
        if cutv != _pre: _drop(_pre)
    except Exception as e:
        log(f"  ⚠️ grade မရ: {e}")
    # ⚠️ ZAE ရဲ့ house bed ထဲမှာ SFX **ပါပြီးသား** — ထပ်ထည့်လျှင် နှစ်ထပ်
    #    ဖြစ်ပြီး ရှုပ်သည် (project မှတ်တမ်း: "ဖြတ်ချက်တိုင်း SFX ထပ်မထည့်ရ")。
    rc["_dur"] = sum(y - x for x, y in spans)     # sfx density တွက်ရန်
    # ⚠️ **SFX ပိတ်ထားလျှင် အကြောင်းရင်း မှတ်ရမည်** — 「Do not hide disabled
    #    SFX settings」。 ယခင်က တိတ်တဆိတ် ဗလာ ဖြစ်ခဲ့ပြီး သုံးစွဲသူက
    #    ဘာကြောင့် အသံ မရလဲ မသိခဲ့ပါ (၂၀၂၆-၀၉-၂၁)。
    if not rc.get("sfx", True):
        REPORT["sfx_off"] = "recipe က sfx=False"
        log("  ⓘ SFX ပိတ်ထားသည် (recipe) — အသံ ထည့်မည် မဟုတ်ပါ")
        cues = []
    else:
        cues = DR.sfx(gfx, caps, rc)
    # ══ plan ရဲ့ sfxEvents — **semantic** လမ်းကြောင်း ═══════════════
    # ⚠️ schema မှာ ရှိပြီး planner က မထုတ်、worker က မခေါ်ခဲ့ပါ ⇒
    #    semantic sound design က **လုံးဝ မဖြစ်ခဲ့**ပါ (၂၀၂၆-၀၉-၂၁)。
    # ⚠️ plan က **မူရင်း အချိန်** နဲ့ ထုတ်သည် ⇒ `omap` နဲ့ ဖြတ်ပြီး
    #    timeline သို့ ပြောင်းမှ ရမည် (ဂရပ်ဖစ်နဲ့ တစ်သဘောတည်း)。
    _plan_cues = []
    if _PLAN and rc.get("sfx", True):
        try:
            # ⚠️ `EX` က plan အကိုင်းထဲမှာသာ import — ဒီမှာ မရှိပါ
            #    (`PZ` · `_breathe` အမှားမျိုးပင်)。
            import execute as EX2
            _pc = EX2.to_sfx(_PLAN, log=log)
            for _t, _role, _db in _pc:
                _ot = omap(float(_t), snap=True)
                if _ot is None:
                    REPORT["sfx_skipped"] = REPORT.get("sfx_skipped", 0) + 1
                    continue
                _plan_cues.append((round(_ot, 2), _role, int(_db)))
            REPORT["sfx_plan_n"] = len(_plan_cues)
            # ⚠️ **တစ်ခါတည်း ပေါင်းရမည်** — ထပ်နေသော အချိန်/role ကို ဖယ်。
            #    မဖယ်လျှင် legacy နဲ့ plan က တူသော အခိုက်မှာ နှစ်ထပ် ဖြစ်မည်。
            _seen = {(round(a, 1), r) for a, r, _ in cues}
            _add = [c for c in _plan_cues if (round(c[0], 1), c[1]) not in _seen]
            REPORT["sfx_dedup"] = len(_plan_cues) - len(_add)
            cues = sorted(cues + _add, key=lambda x: x[0])
            if _plan_cues:
                log(f"  SFX plan · {len(_plan_cues)} ခု (ထပ်၍ ဖယ် "
                    f"{REPORT['sfx_dedup']}) ⇒ စုစုပေါင်း {len(cues)}")
        except Exception as _se:
            log(f"  ⚠️ plan SFX မရ ({type(_se).__name__}: {_se}) — legacy သာ")
    nsfx = 0
    if cues:
        try:
            sv = os.path.join(work, "sfx.mp4")
            _pre2 = cutv
            # ⚠️ **စကားကို မဖုံးစေရ** — cue တိုင်းကို ပုံသေ dB နဲ့ ထပ်ခဲ့သည်。
            #    တကယ့် ဖြတ်ထားသော အသံ (`cutv`) ကနေ စကားသံ အားကို တိုင်းပြီး
            #    စကားအောက် ၆ dB တွင် ထားသည်。 ⚠️ အချိန်ကို မရွှေ့ရ — ဂရပ်ဖစ်နဲ့ တွဲနေသည်。
            try:
                _dw = os.path.join(work, "_duck.wav")
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", cutv,
                                "-vn", "-ac", "1", "-ar", "16000", _dw], check=True)
                cues, _nd = DR.duck_cues(cues, _dw, log=log)
                if _nd:
                    REPORT["sfx_ducked"] = _nd
                    log(f"  SFX {_nd}/{len(cues)} ခု စကားပေါ် ကျရွေ့၍ လျှော့သည်")
                os.path.exists(_dw) and os.remove(_dw)
            except Exception as _de:
                log(f"  ⚠️ SFX duck မရ ({type(_de).__name__}) — မလျှော့ဘဲ ဆက်သည်")
            _CUE_USED.clear()
            _sd = rc.get("_seed") or job.get("id") or "ikki"
            # ⚠️ **SFX stem** — `nsfx` က ဖိုင် ရှိမရှိ ရေတွက်ချက်သာ。
            #    ဖိုင် ရှိပြီး အသံ မရှိတာ · အချိန် လွဲတာ ဘယ်တော့မှ မဖမ်းမိပါ。
            _stem = os.path.join(work, "sfx_stem.wav")
            _, nsfx = DR.mix(cutv, cues, sv,
                             lambda r, i=None: _cue(SL, r, rc["theme"], i, _sd, log),
                             log, stem=_stem)
            try:
                _ok, _bad = DR.stem_check(_stem, cues, log=log)
                REPORT["sfx_audible"] = _ok
                REPORT["sfx_silent"] = len(_bad)
                if _bad:
                    log(f"  ⚠️ **SFX {len(_bad)}/{len(cues)} ခု stem ထဲ အသံ မရှိ**")
            except Exception as _ce:
                log(f"  ⚠️ stem မစစ်နိုင် ({type(_ce).__name__})")
            finally:
                os.path.exists(_stem) and os.remove(_stem)
            REPORT["sfx_variants"] = len(set(_CUE_USED))
            REPORT["sfx_banks"] = sorted({x.split("/")[0] for x in _CUE_USED})
            REPORT["sfx_assets"] = list(_CUE_USED)
            # ⚠️ **ဖြေရှင်းချက်ကို မှတ်တမ်းတင်ရမည်** (spec §6 — 「record the exact
            #    resolved asset in a render manifest for reproducibility」)。
            #    မပြလျှင် variant ကွဲမကွဲ ပြန်စစ်လို့ မရပါ。
            for _t, _r, _d in cues[:12]:
                log(f"    SFX {_t:6.2f}s {_r:11} {_d:+d}dB")
            if _CUE_USED:
                log("    asset · " + " · ".join(_CUE_USED[:8]))
            cutv = sv; _drop(_pre2); log(f"  SFX {nsfx} cue")
        except Exception as e:
            log(f"  ⚠️ SFX မရ: {e}")

    # ── ⑦ ဂရပ်ဖစ် ထပ် + အသံ ညှိ + ထုတ် ─────────────────────
    stage(7, "render")
    pngs = []
    # ⚠️ slide ကို **အရင်ဆုံး** ထည့်ရမည် — အောက်ဆုံးအလွှာ ဖြစ်စေရန် မဟုတ်ဘဲ
    #    ဗီဒီယိုပေါ် တိုက်ရိုက် ဖုံးရန်。 ပြီးမှ တခြား ဂရပ်ဖစ် အပေါ်က တက်သည်。
    # နောက်ဆုံး အချက် = slide ဟုတ်မဟုတ် (ဟုတ်လျှင် တဖြည်းဖြည်း ရွှေ့သည်)
    for _sp, _a, _b, _lay in (slides or []):
        pngs.append((_sp, 0, 0, _a, _b, True))
    if el:
        ov = el["anim"][-1]
        pngs = [(ov[0], ov[1], ov[2], 0.6, 0.6+el["dur"], False)]
        for p,x,y,d in el["statics"]:
            pngs.append((p,x,y,0.6+d,0.6+el["dur"], False))
    ins=[]; fc=[f"[0:v]scale={TH['W']}:{TH['H']}:force_original_aspect_ratio=increase,"
               f"crop={TH['W']}:{TH['H']},format=yuv420p[v0]"]
    last="v0"; n=0
    # ⚠️ ZAE က အဖြူ studio wall (RGB ≈ 245,242,243) ပေါ် ရိုက်သည် —
    #    အဖြူစာလုံးက **လုံးဝ မမြင်ရ**。 navy gradient scrim ခံရသည်。
    # ⚠️ B-roll ကို **စာတန်းနဲ့ ဂရပ်ဖစ် အောက်မှာ** ထားရမည် — အပေါ်မှာ
    #    ထားလျှင် စာတန်းကို ဖုံးသည်。 ဒါကြောင့် ဒီနေရာမှာ အရင် ထည့်သည်。
    for at, bp, bd, _t in (bmov or [])[:10]:
        ins += ["-itsoffset", f"{at:.2f}", "-i", bp]; n += 1
        # ⚠️ B-roll က **ဘောင်အပြည့်** ⇒ ဖြတ်ချက် (hard=True)
        fc.append(_fade(f"{n}:v", f"bf{n}", at, at + bd, hard=True))
        fc.append(f"[{last}][bf{n}]overlay=0:0:eof_action=pass:"
                  f"enable='between(t,{at:.2f},{at+bd:.2f})'[v{n}]")
        last = f"v{n}"
    if rc.get("scrim") and gmov:
        try:
            # ⚠️ scrim ကို **ဂရပ်ဖစ် ရှိချိန်မှာသာ** ပေါ်စေရမည် — တစ်ခုလုံး
            #    ခံလျှင် ပြောသူ shot တွေပါ မှောင်သည် (N5 က ၁၄၉↔၂၃၆ ကြား
            #    ပြောင်းနေသည်၊ IKKI က ၁၈၇ ငြိမ်နေခဲ့သည် — တိုင်းထားသည်)。
            wins = [(at, at+d, y0, y1) for at, _m, d, y0, y1 in gmov]
            sv = SC.track(wins, os.path.join(work, "scrim.mov"),
                          os.path.join(work, "sc"), TH["W"], TH["H"], TH["NAVY"],
                          fps=rc["fps"], total=probe(cutv)["dur"])
            if sv:
                ins += ["-i", sv]; n+=1
                fc.append(f"[{last}][{n}:v]overlay=0:0:shortest=0:repeatlast=0[v{n}]")
                last=f"v{n}"
                log(f"  scrim · ဂရပ်ဖစ် {len(wins)} ခုပေါ်မှာသာ · navy {TH['NAVY']}")
        except Exception as e:
            log(f"  ⚠️ scrim မရ: {e}")
    # ⚠️ စာတန်း track က **တစ်ခုတည်း** input — PNG ၂၀၀ ထည့်လျှင် ffmpeg ပျက်သည်
    if capv:
        ins += ["-i", capv]; n+=1
        # ⚠️ စာတန်းကို BOT အထက် အနီးမှာ ချရမည် — BOT က TikTok UI နှင့်
        #    ဖုံးမခံစေရန် တိုင်းထားသော ကန့်သတ်ချက်ပါ (ZAE 940 · ZJL 830)。
        base = rc.get("cap_base")
        cy = int(TH["H"]*base) - cband if base else TH["BOT"] - cband
        cy = max(0, min(TH["H"]-cband, cy))
        # ⚠️ `repeatlast=0` မပါလျှင် စာတန်း track ကုန်သွားသည်နှင့် နောက်ဆုံး
        #    frame က အဆုံးထိ ငြိနေသည် (တကယ် ဖြစ်ခဲ့)。
        fc.append(f"[{last}][{n}:v]overlay=0:{cy}:shortest=0:repeatlast=0[v{n}]")
        last=f"v{n}"
    # ⚠️ ဂရပ်ဖစ် တစ်ခုချင်း alpha .mov ဖြစ်ပြီးသား — input အနည်းငယ်သာ
    for at, mov, d, _y0, _y1 in (gmov or [])[:12]:
        ins += ["-itsoffset",f"{at:.2f}","-i",mov]; n+=1
        fc.append(f"[{last}][{n}:v]overlay=0:0:eof_action=pass[v{n}]"); last=f"v{n}"
    # ══ keyword pop — **ဘေးတိုက် ရွှေ့ပြီး** ထပ်တင် ═══════════════
    # ⚠️ `kinetic.word_pop` မှာ `x` param မရှိ ⇒ ဘောင်အပြည့် alpha ကို
    #    `overlay=dx:0` နဲ့ ရွှေ့သည်。 alpha ဖြစ်၍ ဘေးက ကွက်လပ် မမြင်ရပါ。
    # ⚠️ စာတန်း **ပြီးမှ** ထပ်ရမည် — pop က အပေါ်ဆုံး အလွှာ ဖြစ်သင့်သည်
    #    (reference မှာ pop က ပြောသူရော နောက်ခံရော ဖုံးသည်)。
    # ══ ဘေးဘောင် စာရင်း — **အောက်ဆုံး အလွှာ** (စာတန်း/pop ရဲ့ အောက်) ══
    # ⚠️ PNG အငြိမ် ⇒ `loop=1` နဲ့ ထည့်ပြီး `enable=` နဲ့ ဝင်းဒိုး ကန့်သတ်သည်。
    #    .mov မဟုတ်၍ itsoffset မလုပ်နိုင်ပါ。
    for at, png, d in (rmov or [])[:8]:
        # ⚠️ `-t` က input ကို **၀s ကနေ** ကန့်သတ်သည် — `-t d` ပေးလျှင်
        #    ဝင်းဒိုး စချိန် (၃၄.၅s) ရောက်တော့ frame ကုန်နေပြီး
        #    `eof_action=pass` ကြောင့် **ဘာမှ မပေါ်**ပါ (ffmpeg နဲ့ စမ်းပြီး
        #    အတည်ပြု ၂၀၂၆-၀၉-၂၁: `-t 6` မပေါ် · `-t 16` ပေါ်)。
        #    ⇒ ဝင်းဒိုး **အဆုံးအထိ** ဖုံးရမည်。
        ins += ["-loop", "1", "-t", f"{at + d + 0.5:.2f}", "-i", png]; n += 1
        fc.append(f"[{last}][{n}:v]overlay=0:0:eof_action=pass"
                  f":enable='between(t,{at:.2f},{at + d:.2f})'[v{n}]")
        last = f"v{n}"
    for at, mov, d, dx, _t in (pmov or [])[:10]:
        ins += ["-itsoffset", f"{at:.2f}", "-i", mov]; n += 1
        fc.append(f"[{last}][{n}:v]overlay={dx}:0:eof_action=pass[v{n}]")
        last = f"v{n}"
    # ── ⑧ ဘရန်း logo ────────────────────────────────────────
    # ⚠️ ဂရပ်ဖစ် ပေါ်နေချိန် **ဖျောက်**ရသည် — ဂရပ်ဖစ်တွေက အပေါ်မှာ ချထားပြီး
    #    logo နဲ့ ထပ်သည်。 gmov ရဲ့ ကွက်လပ်တွေမှာသာ ပြသည်。
    # ⚠️ အရွယ်ကို H ရဲ့ ၅% — ကြီးလျှင် ရုပ်ကို စားပြီး ကြော်ငြာဆန်သည်。
    if (brand or {}).get("logo"):
        try:
            lp = os.path.join(work, "logo.png")
            if not os.path.exists(lp):
                _r = urllib.request.Request(
                    API + f"/api/brands/{(brand or {}).get('id')}/logo")
                _r.add_header("Authorization", "Bearer " + TOKEN)
                with urllib.request.urlopen(_r, timeout=60) as _f:
                    open(lp, "wb").write(_f.read())
            lh = max(24, int(TH["H"] * 0.05))
            mx = int(TH["W"] * 0.042); my = int(TH["H"] * 0.030)
            ins += ["-i", lp]; n += 1
            en = ""
            if gmov:
                en = ":enable='" + "*".join(
                    f"not(between(t,{a:.2f},{a+d:.2f}))" for a, _m, d, _y0, _y1 in gmov) + "'"
            fc.append(f"[{n}:v]scale=-1:{lh}[lg]")
            fc.append(f"[{last}][lg]overlay=W-w-{mx}:{my}{en}[v{n}]")
            last = f"v{n}"
            log(f"  logo တပ်ပြီး · အမြင့် {lh}px"
                + (f" · ဂရပ်ဖစ် {len(gmov)} ခုမှာ ဖျောက်" if gmov else ""))
        except Exception as e:
            log(f"  ⚠️ logo မရ: {e}")

    # ⚠️ `-loop 1` ကို **`-t` နဲ့ `-itsoffset` မပါဘဲ မသုံးရ**。 `enable` က
    #    ၅ စက္ကန့်ပဲ ပြပေမယ့် ffmpeg က အဲဒီပုံကို **ဗီဒီယိုတစ်ခုလုံး လျှောက်**
    #    decode + scale လုပ်နေသည်。 ပုံသေးလေးဆိုလျှင် သိပ်မကုန်ပေမယ့်
    #    full-frame slide ၁၇ ခု ဖြစ်သွားတာနဲ့ render က **၉ မိနစ် → ၈၄ မိနစ်**
    #    ဖြစ်သွားခဲ့သည် (တိုင်းထားသည်)。 B-roll က ဒီနည်းအတိုင်း လုပ်ပြီးသား。
    _nd = 0
    for p,x,y,a,b,_mv in pngs:
        d = max(0.1, float(b) - float(a))
        # ⚠️ motionkit slide က **ဗီဒီယို** (alpha .mov) — `-loop 1 -t` မသုံးရ
        _ismov = str(p).lower().endswith((".mov", ".mp4"))
        if _ismov: ins += ["-itsoffset", f"{a:.2f}", "-i", p]
        else:      ins += ["-loop","1","-t",f"{d:.2f}","-itsoffset",f"{a:.2f}","-i",p]
        n+=1
        if _ismov:
            # clip မှာ ကိုယ်ပိုင် fade (house) ပါပြီးသား ⇒ ထပ်မထည့်ရ
            fc.append(f"[{n}:v]format=yuva420p[sf{n}]")
            # ⚠️ clip က သဘာဝ ၃.၆s ပဲ ရှိပြီး ဝင်းဒိုးက ၁၀.၅s ⇒ နောက်ဆုံး
            #    frame ကို **ရပ်ထားရမည်** (`repeat`)。 `pass` သုံးလျှင်
            #    clip ကုန်တာနဲ့ slide ပျောက်သွားမည်。
        else:
            fc.append(_fade(f"{n}:v", f"sf{n}", a, b))
        _yy = f"{y}"
        _rv = _rise(a) if (_mv and not _ismov and d > RISE_S * 2) else None
        if _rv: _yy = _rv; _nd += 1
        fc.append(f"[{last}][sf{n}]overlay={x}:{_yy}:"
                  f"eof_action={'repeat' if _ismov else 'pass'}:"
                  f"enable='between(t,{a:.2f},{b:.2f})'[v{n}]")
        last=f"v{n}"
    if _nd: log(f"  slide {_nd} ခု အောက်ကနေ တက်လာ ({RISE_PX}px · {RISE_S}s)")
    mc = probe(cutv)
    raw = os.path.join(work, "raw.mp4")
    # ⚠️ -t ကို **output** မှာ ထားရမည် — -loop 1 က PNG ကို အဆုံးမရှိ ထုတ်သည်。
    ff(["ffmpeg","-v","error","-y","-i",cutv]+ins+[
        "-filter_complex",";".join(fc),"-map",f"[{last}]","-map","0:a?",
        "-t",f"{mc['dur']:.2f}","-c:v","h264_videotoolbox","-b:v","10M",
        "-c:a","aac","-b:a","192k",raw], f"ဂရပ်ဖစ် ထပ်ခြင်း ({len(ins)//2} input)")
    _drop(cutv)                       # ⚠️ raw ထွက်ပြီး — cutv နောက် မသုံးတော့
    # ⚠️ သီချင်းကို **loudnorm မလုပ်ခင်** ထပ်ရမည် — ပြီးမှ ထပ်လျှင်
    #    အသံအဆင့် ပစ်မှတ် လွဲသွားသည်。
    #    Podcast · Course မှာ music=None — reference မှာ သီချင်း မရှိ。
    pre = raw
    if rc.get("music"):
        try:
            mv = os.path.join(work, "mus.mp4")
            MU.bed(raw, mv, rc["music"], probe(raw)["dur"], log=log,
                   seed=rc.get("_seed") or job.get("id") or "")
            pre = mv; _drop(raw)
        except Exception as e:
            log(f"  ⚠️ သီချင်း မရ: {e}")
    else:
        log("  သီချင်း မထည့် (ဤ recipe မှာ မရှိ)")
    SP.loudness(pre, out, lufs=rc.get("lufs") or -14.0)   # recipe အလိုက်
    _drop(pre)                        # ⚠️ out ထွက်ပြီး — pre နောက် မသုံးတော့

    # ── အချိုး အခြား ── (ပင်မ ပြီးမှ · QC မတိုင်မီ)
    #    ⚠️ အချိုး ပြောင်းလျှင် safe zone ပြန်စစ်ရမည် — မစစ်လျှင် စာလုံး ဘေးထွက်သည်。
    #    ယခု ပင်မ အချိုးကိုသာ ထုတ်သည် — အခြားအချိုးက recipe အသစ်နဲ့ ပြန်ထုတ်ရမည်。

    # ── QC gate — မအောင်လျှင် **မပို့ရ** ──
    TH2 = dict(TH); TH2["cap_h"] = (cy + cband) if capv else 0
    if slides:
        # ⚠️ full-frame slide ရဲ့ ဘောင် — reference ၂ ခု တိုင်းချက် (၀.၅–၁၇.၀s)
        # ⚠️ အရင်က 0.5–17.0 ဖြင့် ကျော်ခဲ့သည် — house constant
        #    (core/qc.py:20 CARD_MIN 1.0 · CARD_MAX 10.5) ကို ပြန်သုံးသည်。
        pass
    TH2["lufs_target"] = rc.get("lufs") or -14.0
    TH2["cap_max"] = rc.get("cap_max")
    # ⚠️ segs ကို st ထဲ ထည့်ရမည် — handle() က render() ရဲ့ local ကို မမြင်ဘူး
    #    (တကယ် ပျက်ခဲ့သည်: NameError: name 'segs' is not defined)。
    # ⚠️ **ထွက်ပြီးသား timeline ရဲ့ အချိန်ကိုပါ သိမ်းရမည်** (`o0`/`o1`) —
    #    UI က ဖျက်လိုက်တာကို ဗီဒီယိုပေါ်မှာ ချက်ချင်း ပြပြရန် (render မလုပ်ဘဲ)。
    #    မူရင်းအချိန်ပဲ သိမ်းလျှင် ဖြတ်ပြီးသား ဗီဒီယိုနဲ့ လွဲသွားမည်。
    _omap = omap
    _sg = []
    for x in (segs or []):
        a0, b0 = float(x["start"]), float(x["end"])
        oa, ob = _omap(a0), _omap(b0)
        e = dict(text=x["text"], start=round(a0, 2), end=round(b0, 2))
        for _k in ("source", "take"):
            if x.get(_k) is not None: e[_k] = x[_k]
        if oa is not None and ob is not None and ob > oa:
            e["o0"] = round(oa, 2); e["o1"] = round(ob, 2)
        # ⚠️ **စကားလုံး အချိန်မှတ်ကို သယ်ရမည်** — ဒီမှာ ကျန်ခဲ့လျှင်
        #    `_place()` က ထိန်းထားလည်း Script Editor ဆီ **မရောက်**ပါ
        #    (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့ — ကွင်းဆက် ၂ နေရာမှာ ပြတ်နေသည်)。
        # ⚠️ အချိန်မှတ်ကို **ဖြတ်ပြီး timeline သို့လည်း** ပြောင်းပေးရမည် —
        #    UI က ထွက်ဗီဒီယိုပေါ် ပြသည်、မူရင်းပေါ် မဟုတ်。
        if x.get("words"):
            _w2 = []
            for _w in x["words"]:
                try:
                    _ws, _we = float(_w["s"]), float(_w["e"])
                except (KeyError, TypeError, ValueError):
                    continue
                _d = dict(w=_w.get("w") or "", s=round(_ws, 3), e=round(_we, 3))
                _os, _oe = _omap(_ws), _omap(_we)
                if _os is not None and _oe is not None and _oe > _os:
                    _d["o0"] = round(_os, 3); _d["o1"] = round(_oe, 3)
                _w2.append(_d)
            if _w2:
                e["words"] = _w2
        for _k in ("words_conf", "timing_src", "words_note", "place"):
            if x.get(_k) is not None:
                e[_k] = x[_k]
        _sg.append(e)
    st["segs"] = _sg
    # ⚠️ presentation layer စစ်ဆေးချက် (skill `ikki-presentation`) —
    #    ဂရပ်ဖစ် ကတ်များ · SFX သိပ်သည်းမှု。 `gfx_share` ဘောင်ကို
    #    **recipe က ပေးမှသာ** စစ်သည် (ZJL knowledge မှာသာ တိုင်းထားသည်)。
    try: mo_dur = float(probe(out)["dur"])
    except Exception: mo_dur = None
    # ⚠️ `gfx_share` က **full-frame slide** ကို တိုင်းတာ — reference ရဲ့
    #    ၁၃.၄% က အဲဒါပဲ။ lower-third အသေးလေးတွေကိုပါ ရေတွက်လျှင် ကိန်းက
    #    အဓိပ္ပာယ် မရှိတော့。 slide ရှိလျှင် slide ကိုသာ ရေတွက်သည်。
    _cards = ([(a, b - a) for _p, a, b, _l in slides] if slides
              else [(a, d) for a, _m, d, _y0, _y1 in (gmov or [])])
    # ⚠️ `DR.sfx()` က **tuple `(at, name, db)`** ပြန်ပေးသည် — dict မဟုတ်。
    #    `c.get("at")` ဟု ရေးထားခဲ့သဖြင့် SFX ရှိသော render တိုင်း ဤနေရာမှာ
    #    AttributeError နဲ့ ကျဘမ်း ဖြစ်ခဲ့သည် (render တကယ် ပြီးပြီးမှ QC မှာ)。
    #    ZAE မှာ မပေါ်ခဲ့ခြင်းက `sfx=False` ⇒ cues အလွတ် ဖြစ်၍သာ。
    _sfxt  = [(c[0] if isinstance(c, (tuple, list)) else c.get("at"))
              for c in (cues or [])]
    _sfxt  = [t for t in _sfxt if t is not None]
    # ⚠️ **report အတွက် ကိန်းများ စု** — ဂဏန်း မတီထွင်ရ、မတိုင်းရသေးတာ None。
    try:
        import gemguard as G2
        _L = locals()
        _cl = sorted(d for _a, d in _cards) if _cards else []
        _bn = len(bmov) if isinstance(bmov, list) else None
        _bs = (sum(x[2] for x in bmov) / mo_dur) if (bmov and mo_dur) else None
        _bw = rc.get("broll")
        _bp = rc.get("broll_pct")
        REPORT.update(
            style=job.get("recipe"), src_dur=round(float(m["dur"]), 1),
            w=m["w"], h=m["h"], fps=rc.get("fps"), cls=st.get("cls"),
            cuts=st.get("cuts"), removed=st.get("removed"),
            removed_ratio=st.get("removed_ratio"),
            max_removed=st.get("max_removed", CUT.MAX_REMOVED),
            cut_ok=(st.get("removed_ratio") is not None
                    and st["removed_ratio"] <= st.get("max_removed", CUT.MAX_REMOVED)),
            out_dur=round(mo_dur, 1) if mo_dur else None,
            cut_src=st.get("cut_src"),
            refusals=", ".join(st.get("refusals") or []) or None,
            cut_warnings=", ".join(st.get("warnings") or []) or None,
            slides_got=_L.get("_gslides", 0),
            slide_want=_L.get("_wantn"),
            slide_placed=len(slides) if slides else 0,
            gfx_recipe=rc.get("gfx"), gfx_want=_L.get("_wg"),
            gfx_got=_L.get("_gfxn"), gfx_ask=_L.get("_gfxask"),
            caps_avail=_L.get("_caps_avail"),
            span_sum=round(sum(b - a for a, b in spans), 1) if spans else None,
            drift=(round(mo_dur - sum(b - a for a, b in spans), 2)
                   if (mo_dur and spans) else None),
            gem={k: dict(v) for k, v in (getattr(G2, "TALLY", {}) or {}).items()},
            card=dict(DR.LAST) if getattr(DR, "LAST", None) else {},
            card_med=(round(_cl[len(_cl)//2], 1) if _cl else None),
            card_min=(round(_cl[0], 1) if _cl else None),
            card_max=(round(_cl[-1], 1) if _cl else None),
            broll_n=_bn, broll_want=_bw,
            broll_ok=(None if (_bn is None or _bw is None) else _bn <= _bw),
            broll_share=(round(_bs, 3) if _bs is not None else None),
            broll_pct=_bp,
            broll_share_ok=(None if (_bs is None or _bp is None) else _bs <= _bp),
            caps_n=len(caps) if caps else 0,
            cap_fallback=CP.FALLBACK[0],
            cap_fb_ok=(CP.FALLBACK[0] == 0),
            cap_cover=rc.get("cap_cover"),
            sfx_n=nsfx if "nsfx" in dir() else None)
    except Exception as _e:
        log(f"  ⚠️ report ကိန်း စုမရ: {type(_e).__name__}: {_e}")
    # ⚠️ **QC ဂိတ်ကို profile နဲ့ တွဲပေးရမည်** — headtop မှာ ပုံသေ
    #    ၁.၅/min ထားလျှင် ၁၂၀s ဗီဒီယိုမှာ အသံ ၁ ချက်ပဲ ထွက်မည်。
    try:
        import sfxpol as _PL2
        _qpol = _PL2.for_recipe(rc)
    except Exception:
        _qpol = None
    ok, checks = QC.run(out, st, TH2, caps=caps, cards=_cards, sfx_pol=_qpol,
                        sfx=(_sfxt if rc.get("sfx", True) else []),
                        share=rc.get("gfx_share"))
    log("  QC · " + QC.summary(checks))
    # ⚠️ skill `ikki-presentation` §10 — **REFERENCE အတန်းက မဖြစ်မနေ**。
    #    ဘာကူးလိုက်ပြီး ဘာကို တမင် မကူးဘဲ ချန်ထားလဲ ပြရသည်。
    log("  REF · REF-A 14.0% card · 1.1 SFX/min · -14.95 LUFS · TP +0.19 ✗ပြတ်"
        " | REF-B 13.4% · 0.6 SFX/min · -22.58 LUFS ✗တိုး")
    log(f"        ဤ render — ဖွဲ့စည်းပုံ လိုက်、mastering ပြင် "
        f"(lufs ပစ်မှတ် {rc.get('lufs')} · TP ≤ -1.0)"
        + ("" if rc.get("gfx_share") else " · card share ဘောင် မသတ်မှတ် (ဤ style မှာ full-frame card မရှိ)"))
    # ⚠️ **QC ဂိတ် မတိုင်ခင် work/ မဖျက်ရ**。 အရင်က ဒီနေရာမှာ
    #    `rm -rf work` ပြေးသဖြင့် QC ကျသွားချိန် သက်သေ ဖျက်ပြီးသား ဖြစ်နေခဲ့သည် —
    #    ဂိတ် အောင်ပြီးမှ အောက်မှာ ဖျက်သည် (`sweep_scratch` ရဲ့ စည်းမျဉ်း အတိုင်း)。
    # ⚠️ `gfx_share` ကို **ပိတ်ပင်ချက် မဟုတ်ဘဲ သတိပေးချက်** အဖြစ် သတ်မှတ်သည်。
    #    အကြောင်းရင်း — အဲဒီ ၀.၁၀–၀.၁၇ ဘောင်ကို reference ၂ ခုရဲ့
    #    **တည်းဖြတ်သူ ကိုယ်တိုင် ဆောက်ထားသော full-screen slide** များမှ
    #    တိုင်းယူထားသည်။ ဤ pipeline က စကားထဲက Gemini ထုတ်ပေးသော
    #    ခေါင်းစဉ်ကတ်များ ဖြစ်ပြီး **အရေအတွက်က အကြောင်းအရာပေါ် မူတည်**သည် —
    #    ဤ ၁၅ မိနစ် တစ်ယောက်တည်း စကားပြောချက်မှာ ၂၀ တောင်းလည်း
    #    ၅–၈ ခုသာ ပြန်ပေးသည် (run ၅ ခု တိုင်းထားသည်: 5 · 6 · 8 · 10 · 12)。
    #    ⇒ ဘယ်လိုမှ မရောက်နိုင်သော ဘောင်ဖြင့် ဗီဒီယို မထုတ်ပေးဘဲ ပိတ်ထားလျှင်
    #      ဒီပုံစံက **လုံးဝ သုံးမရ** ဖြစ်သွားမည်။ ကိန်းကိုတော့ အတိအလင်း ပြသည်。
    # ⚠️ **slide ၀ ခု = အဆိုးဆုံး ကျမှု** — ဂိတ်က အဲဒီအခါမှာပဲ နားနေခဲ့သည်。
    #    အရင်က `ADVISORY = set() if slides else {"gfx_share"}` ဖြစ်၍ slide
    #    လုံးဝ မထွက်လျှင် gfx_share က သတိပေးချက်သာ ဖြစ်ပြီး **ဂရပ်ဖစ် မပါတဲ့
    #    ဗီဒီယို အသံတိတ်တိတ် ထွက်သွား**သည်。 ⇒ ဂိတ်ကို ပြောင်းပြန် ပြန်လှန်。
    ADVISORY = set()
    if rc.get("slides") and not slides:
        raise RuntimeError(
            "QC မအောင်: slide ၀ ခု — ဂရပ်ဖစ် အဆင့် လုံးဝ ကျသည်။ "
            "topics.slides() နဲ့ gfxcat.catalog() log ကို ကြည့်ပါ။")
    bad  = [c["key"] for c in checks if not c["ok"] and c["key"] not in ADVISORY]
    warn = [c for c in checks if not c["ok"] and c["key"] in ADVISORY]
    for c in warn:
        log(f"  ⚠️ QC သတိပေးချက် (ပိတ်မထားပါ) · {c['key']} = {c['value']} "
            f"(ပစ်မှတ် {c['want']}) — အကြောင်းအရာက ကတ် အရေအတွက် ကန့်သတ်သည်")
    REPORT["checks"] = checks
    REPORT["qc"] = "PASS" if not bad else ("FAIL: " + ", ".join(bad))
    if bad:
        raise RuntimeError("QC မအောင်: " + ", ".join(bad))
    # ── ဂိတ် အောင်ပြီးမှ work/ ဖျက်သည် ──
    if not KEEP_WORK:
        subprocess.run(["rm","-rf",work])
    return m, probe(out), st, len(caps)

def _subtract(spans, cuts):
    """ကျန်ရှိသော span များမှ ဖြတ်ရန် အပိုင်းများ ထပ်နုတ်သည်。"""
    for c in cuts:
        a, b = c["at"], c["to"]
        out=[]
        for s,e in spans:
            if b <= s or a >= e: out.append((s,e)); continue
            if s < a: out.append((s, a))
            if b < e: out.append((b, e))
        spans = [(x,y) for x,y in out if y-x > 0.06]
    return spans

# ⚠️ `_sil_of()` ဖယ်လိုက်သည် — တိတ်ဆိတ်မှု မြေပုံကို `MEAS` (measure.speech)
#    တစ်ခုတည်းမှ ဆင်းသက်စေသည် (`_M.as_gaps(MEAS[1], 0.20)`)。 အရင်က ဤနေရာက
#    `band/threshold/gaps` ဖြင့် **သီးခြား** တွက်ခဲ့သဖြင့် cut နှင့် မြေပုံ ကွဲခဲ့သည်。

_CUE_USED = []


def _cue(SL, role, th, idx=None, seed="", log=None):
    """role → wav 。 **variant pool ကို အရင် စမ်း**。

    ⚠️ `sfxlib.ROLE` က role ၂၂ ခုလုံးကို **ဖိုင်တစ်ခုတည်း** နဲ့ ချိတ်ထားသည် —
       ဖိုင် ၂၀၀ ကျော် ရှိပာလျက်。 ထို့ကြောင့် whoosh တစ်မျိုးတည်းကို
       ဗီဒီယိုတိုင်း တိုင်း ထပ်ကာထပ်ကာ ကြားနေရသည် (P1 audit အချက် C)。
    ⚠️ `idx` မပာလျှင် အရင်အတိုင်း — လမ်းကြောင်း ပြတ်မသွားစေရန်。
    """
    if idx is not None:
        try:
            import sfxpool as SP
            p, ld, it = SP.cue(role, seed or "ikki", idx, _CUE_USED, th=th, log=log)
            if p:
                _CUE_USED.append(it["id"])
                # ⚠️ `(path, lead)` ပြန်ပေးသည် — mix က အသံ ကျယ်ချိန်ကို
                #    ဖြစ်ရပ်နဲ့ ကိုက်စေရန် စောထည့်မည်。
                return p, ld
            log and log(f"  ⚠️ SFX pool မရှိ: {role} — အရိုး ဖိုင်ကို ပြန်သုံးသည်")
        except Exception as e:
            log and log(f"  ⚠️ SFX pool မအောင် ({type(e).__name__}) — အရိုး ဖိုင်")
    try: return SL.cue(role, th)
    except Exception: return None

def transcribe(wav, log=print):
    """whisper.cpp — ဂျပန်/အင်္ဂလိပ် ရသည်。

    ⚠️ **မြန်မာလို မရ** — model ၂ ခုလုံး စမ်းပြီးသား (large-v3-turbo က
       `လလလလ…` တစ်လုံးတည်း ၂၁၉ ကြိမ်၊ large-v3 က romanised gibberish)。
       မြန်မာအတွက် Gemini လမ်းကြောင်း ဆက်တပ်ရမည်。
    """
    mdl = os.path.expanduser("~/.cache/whisper/ggml-large-v3-turbo.bin")
    if not os.path.exists(mdl):
        log("  ⚠️ whisper model မရှိ — စာသား ကျော်သွားသည်"); return []
    js = wav + ".json"
    r = subprocess.run(["whisper-cli","-m",mdl,"-f",wav,"-oj","-of",wav,"-np","-nt"],
                       capture_output=True, text=True)
    if not os.path.exists(js):
        log(f"  ⚠️ whisper မအောင် — {(r.stderr or '')[:120]}"); return []
    try:
        d = json.load(open(js, encoding="utf-8", errors="replace"))
        segs = d.get("transcription", [])
    except Exception as e:
        log(f"  ⚠️ whisper JSON ဖတ်မရ: {e}"); segs=[]
    os.path.exists(js) and os.remove(js)
    log(f"  စာသား {len(segs)} ပိုင်း")
    return segs

def put_file(url, path, chunk=1 << 20):
    """presigned URL ကို ဖိုင် တိုက်ရိုက် တင်သည် (memory ထဲ မယူဘူး)。"""
    sz = os.path.getsize(path)
    with open(path, "rb") as f:
        r = urllib.request.Request(url, data=f, method="PUT")
        r.add_header("Content-Length", str(sz))
        r.add_header("Content-Type", "video/mp4")
        # ⚠️ Authorization header **မထည့်ရ** — presigned URL မှာ လက်မှတ်
        #    ပါပြီးသား၊ header ပါလျှင် R2 က 400 ပြန်သည်。
        with urllib.request.urlopen(r, timeout=3600) as resp:
            return resp.status, resp.headers.get("ETag")

def post_meta(jid, meta):
    bnd = "----ikki" + os.urandom(8).hex()
    body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"meta\"\r\n\r\n"
            f"{json.dumps(meta)}\r\n--{bnd}--\r\n").encode()
    r = urllib.request.Request(API + f"/api/w/{jid}/result", data=body, method="POST")
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Content-Type", f"multipart/form-data; boundary={bnd}")
    with urllib.request.urlopen(r, timeout=600) as f: return json.loads(f.read())

def post_thumb(jid, out, log=print):
    """ပုံငယ် ထုတ်ပြီး API ကို တင်သည်。

    ⚠️ API image မှာ ffmpeg မပါ ⇒ **ဒီမှာ ထုတ်ရမည်**。
    ⚠️ ပထမ frame ကို မယူရ — မှောင်/ဗလာ ဖြစ်တတ်သည်。 ၁၅% နေရာက ယူသည်。
    ⚠️ မရလျှင်လည်း job တစ်ခုလုံး **မပျက်စေရ** — ပုံငယ်က အသေးအဖွဲ။
    """
    try:
        d = probe(out)["dur"]
        p = os.path.join(os.path.dirname(out), "thumb.jpg")
        subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{max(0.5,d*0.15):.2f}",
            "-i",out,"-frames:v","1","-vf","scale=480:-2","-q:v","5",p], check=True)
        raw = open(p,"rb").read()
        bnd = "----ikki" + os.urandom(8).hex()
        body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; "
                f"filename=\"t.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() \
               + raw + f"\r\n--{bnd}--\r\n".encode()
        r = urllib.request.Request(API + f"/api/w/{jid}/thumb", data=body, method="POST")
        r.add_header("Authorization", "Bearer " + TOKEN)
        r.add_header("Content-Type", f"multipart/form-data; boundary={bnd}")
        with urllib.request.urlopen(r, timeout=120) as f: f.read()
        log("  ပုံငယ် တင်ပြီး")
    except Exception as e:
        log(f"  ⚠️ ပုံငယ် မရ: {e}")


def post_audio(jid, path, log=print):
    """အသံ proxy ကို API ကို တင်သည် (Script Editor မှာ နားထောင်ရန်)。"""
    try:
        raw = open(path, "rb").read()
        bnd = "----ikki" + os.urandom(8).hex()
        body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; "
                f"filename=\"a.m4a\"\r\nContent-Type: audio/mp4\r\n\r\n").encode() \
               + raw + f"\r\n--{bnd}--\r\n".encode()
        r = urllib.request.Request(API + f"/api/w/{jid}/audio", data=body, method="POST")
        r.add_header("Authorization", "Bearer " + TOKEN)
        r.add_header("Content-Type", f"multipart/form-data; boundary={bnd}")
        with urllib.request.urlopen(r, timeout=180) as f: f.read()
        log(f"  အသံ proxy တင်ပြီး · {len(raw)/1e6:.1f} MB")
    except Exception as e:
        log(f"  ⚠️ အသံ proxy မတင်နိုင်: {e}")


def post_result(jid, out, meta):
    # ⚠️ R2 mode — ဖိုင်ကို R2 ကို **တိုက်ရိုက်** တင်ပြီး API ကို metadata ပဲ ပို့သည်。
    #    VPS ကို မဖြတ်သဖြင့် ၇၃ MB/မိနစ် output က VPS လိုင်းကို မစားဘူး。
    try:
        d = req(f"/api/w/{jid}/puturl", {})
        if d.get("url"):
            put_file(d["url"], out)
            meta = dict(meta); meta["out_key"] = d["key"]
            return post_meta(jid, meta)
    except urllib.error.HTTPError as e:
        if e.code != 409: raise      # 409 = R2 မဖွင့်ထား → local mode
    bnd = "----ikki" + os.urandom(8).hex()
    with open(out,"rb") as f: data = f.read()
    body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"meta\"\r\n\r\n{json.dumps(meta)}\r\n"
            f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{jid}.mp4\"\r\n"
            f"Content-Type: video/mp4\r\n\r\n").encode() + data + f"\r\n--{bnd}--\r\n".encode()
    r = urllib.request.Request(API + f"/api/w/{jid}/result", data=body, method="POST")
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Content-Type", f"multipart/form-data; boundary={bnd}")
    with urllib.request.urlopen(r, timeout=1800) as f: return json.loads(f.read())

def fetch_src(jid, dest, on_progress=None, path="src"):
    """source ကို chunk အလိုက် disk ပေါ် တိုက်ရိုက် ရေးသည် · ၁၀% တိုင်း အစီရင်ခံသည်。

    `path="src2"` ⇒ dual-system အသံ ဖိုင် (မရှိလျှင် 404 ⇒ ခေါ်သူက ကိုင်ရမည်)。
    """
    r = urllib.request.Request(API + f"/api/w/{path}/{jid}")
    r.add_header("Authorization", "Bearer " + TOKEN)
    # ⚠️ R2 mode — API က JSON {url:…} ပြန်ပေးသည်。 အဲဒီ URL ကို
    #    **Authorization header မပါဘဲ** ဆွဲရမည် (presigned ဖြစ်သဖြင့်)。
    with urllib.request.urlopen(r, timeout=60) as f0:
        ct = (f0.headers.get("Content-Type") or "")
        if "json" in ct:
            _j = json.loads(f0.read())
            # ⚠️ ဖိုင်က **ဤစက်ထဲမှာပဲ** ရှိပြီးသားဆို ဆွဲချစရာ မလို —
            #    R2 ကို တင်ပြီး ပြန်ဆွဲချတာ အလကား (၂၀၂၆-၀၉-၁၉)。
            _lp = _j.get("local")
            if _lp:
                if not os.path.exists(_lp):
                    raise RuntimeError(f"စက်ထဲက ဖိုင် ပျောက်နေသည်: {_lp}")
                print(f"  ✓ စက်ထဲက ဖိုင် တိုက်ရိုက် သုံးသည် — ဆွဲချစရာ မလို", flush=True)
                return _lp
            u = _j.get("url")
            if u: r = urllib.request.Request(u)
    t0 = time.time(); got = 0; nxt = 10
    with urllib.request.urlopen(r, timeout=180) as f:
        total = int(f.headers.get("Content-Length") or 0)
        with open(dest, "wb") as o:
            while True:
                b = f.read(1 << 20)
                if not b: break
                o.write(b); got += len(b)
                pc = int(got*100/total) if total else 0
                if total and pc >= nxt:
                    sp = got/1e6/max(0.1, time.time()-t0)
                    print(f"  ဆွဲချ {pc}% · {got/1e6:.0f}/{total/1e6:.0f} MB · {sp:.1f} MB/s", flush=True)
                    if on_progress:
                        try: on_progress(pc, got/1e6, sp)
                        except Exception: pass
                    nxt = pc - pc % 10 + 10
    return dest


def fetch_take(jid, n, dest, on_progress=None):
    """Fetch additional multi-take source `n` (the primary is still `src`)."""
    route = f"/api/w/src/{jid}/take/{int(n)}"
    r = urllib.request.Request(API + route)
    r.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(r, timeout=60) as f0:
        ct = (f0.headers.get("Content-Type") or "")
        if "json" in ct:
            meta = json.loads(f0.read())
            local = meta.get("local")
            if local:
                if not os.path.exists(local):
                    raise RuntimeError(f"စက်ထဲက take {n + 1} ဖိုင် ပျောက်နေသည်: {local}")
                return local
            url = meta.get("url")
            if url: r = urllib.request.Request(url)
    t0 = time.time(); got = 0; nxt = 10
    with urllib.request.urlopen(r, timeout=180) as f:
        total = int(f.headers.get("Content-Length") or 0)
        with open(dest, "wb") as o:
            while True:
                chunk = f.read(1 << 20)
                if not chunk: break
                o.write(chunk); got += len(chunk)
                pc = int(got * 100 / total) if total else 0
                if total and pc >= nxt:
                    if on_progress:
                        on_progress(pc, got / 1e6, got / 1e6 / max(0.1, time.time() - t0))
                    nxt = pc - pc % 10 + 10
    return dest


def _take_map_read(path):
    try:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def _take_map_write(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    os.replace(tmp, path)


def join_takes(jid, paths, take_rows, log=print):
    """Normalize up to four recordings into one review-safe timeline.

    We do not pretend to know which take is best.  Joining gives the user one
    transcript where every line retains a take label; repeated attempts can
    then be compared in the Script Editor before anything is deleted.
    """
    out = os.path.join(BIG, jid + "_takes.mp4")
    map_path = os.path.join(BIG, jid + "_takes.json")
    cached = _take_map_read(map_path)
    if os.path.exists(out) and os.path.getsize(out) > (1 << 20) and cached:
        log(f"  ♻️ take timeline ရှိပြီးသား — {len(cached)} takes")
        return out, cached
    if len(paths) < 2:
        return paths[0], []
    base = probe(paths[0])
    W, H = int(base["w"]) // 2 * 2, int(base["h"]) // 2 * 2
    fps = max(1.0, float(base["fps"]))
    args = ["ffmpeg", "-v", "error", "-y"]
    for p in paths: args += ["-i", p]
    fc = []
    for i in range(len(paths)):
        # Letterbox/pillarbox different framing rather than crop a user's face.
        fc.append(f"[{i}:v]fps={fps:.6f},scale={W}:{H}:force_original_aspect_ratio=decrease,"
                  f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[v{i}]")
        fc.append(f"[{i}:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
    chain = "".join(f"[v{i}][a{i}]" for i in range(len(paths)))
    fc.append(f"{chain}concat=n={len(paths)}:v=1:a=1[v][a]")
    ff(args + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
               "-c:v", "h264_videotoolbox", "-b:v", _vbr(W, H, fps),
               "-c:a", "aac", "-b:a", "192k", out], "take များ ပေါင်းခြင်း")
    # Use the actual joined duration for the final edge; codec/frame rounding
    # should never leave a transcript line apparently beyond the video.
    end = 0.0; rows = []
    for i, p in enumerate(paths):
        dur = max(0.0, float(probe(p)["dur"]))
        meta = take_rows[i] if i < len(take_rows) else {}
        rows.append(dict(take=i + 1, source=str(meta.get("name") or f"Take {i + 1}"),
                         start=round(end, 3), end=round(end + dur, 3)))
        end += dur
    try: rows[-1]["end"] = round(float(probe(out)["dur"]), 3)
    except Exception: pass
    _take_map_write(map_path, rows)
    log(f"  ✓ take {len(paths)} ခုကို review timeline တစ်ခုဖြစ်အောင် ပေါင်းသည်")
    return out, rows


def scale_take_map(rows, speed):
    if not rows or speed == 1.0: return rows
    out = []
    for r in rows:
        x = dict(r)
        x["start"] = round(float(x.get("start") or 0) / speed, 3)
        x["end"] = round(float(x.get("end") or 0) / speed, 3)
        out.append(x)
    return out


def speed_source(jid, src, speed, log=print):
    """Retimes camera video *before* ASR so captions/SFX share one timeline."""
    if abs(float(speed) - 1.0) < 0.001: return src
    out = os.path.join(BIG, jid + f"_speed_{float(speed):.2f}.mp4")
    if os.path.exists(out) and os.path.getsize(out) > (1 << 20):
        log(f"  ♻️ {speed:.2f}× speech-speed source ရှိပြီးသား")
        return out
    m = probe(src)
    # atempo changes tempo while preserving pitch.  Applying it before ASR and
    # before motion/SFX planning prevents the familiar subtitle/SFX drift.
    ff(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex",
        f"[0:v]setpts=PTS/{float(speed):.2f}[v];[0:a]atempo={float(speed):.2f}[a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "h264_videotoolbox",
        "-b:v", _vbr(m["w"], m["h"], m["fps"]), "-c:a", "aac", "-b:a", "192k", out],
       "speech speed ပြောင်းခြင်း")
    log(f"  ✓ စကားပြောအရှိန် {speed:.2f}× · pitch မပြောင်း")
    return out



def _drop(*paths):
    """မလိုတော့သော intermediate ကို ဖျက်သည်。

    ⚠️ pipeline က `cut → graded → sfx → raw → mus` ငါးဆင့်လုံးကို
       **တစ်ပြိုင်နက် သိမ်းထား**ခဲ့သည် — ၁၂ မိနစ် ဗီဒီယိုတစ်ခုအတွက် ၄.၄ GB。
       Mac ရဲ့ disk ပြည့်ပြီး render က span ကြားမှာ ကျခဲ့သည် (တကယ်)。
       ⇒ နောက်တစ်ဆင့် ရေးပြီးတာနဲ့ ရှေ့ဟာကို ချက်ချင်း ဖျက်ရမည်。
       ဖျက်မိလျှင် ပြန်မရ၍ — **နောက်တစ်ဆင့် တကယ် ရှိမှသာ** ဖျက်သည်。
    """
    for p in paths:
        try:
            if p and os.path.exists(p) and os.path.getsize(p) > 0:
                os.unlink(p)
        except OSError:
            pass


def free_gb(path=SCRATCH):
    """ဒီ disk မှာ ကျန်သော နေရာ (GB)。"""
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize / 1e9


KEEP_WORK = os.environ.get("IKKI_KEEP_WORK") == "1"
KEEP_LAST = 3          # ⚠️ နောက်ဆုံး job ဒီအရေအတွက်အထိ work/ ချန်သည်


REPORTS = os.path.expanduser("~/.ikki/reports")
REPORT = {}            # ⚠️ render() က ဖြည့် · handle() က ဖိုင်ထုတ်


def _rv(checks, key):
    """QC check တစ်ခုရဲ့ (တန်ဖိုး, ပစ်မှတ်, အောင်လား) — မရှိလျှင် (—, —, None)。"""
    for c in (checks or []):
        if c.get("key") == key:
            return c.get("value"), c.get("want"), c.get("ok")
    return "—", "—", None


def _mk(v):
    return "—" if v is None or v == "" else str(v)


def _tick(ok):
    return "" if ok is None else ("  ✓" if ok else "  ✗")


def write_report(jid, R):
    """`~/.ikki/reports/{jid}.txt` — job တိုင်း ထုတ်သည် (ကျလည်း ထုတ်)。

    ⚠️ **ဂဏန်း မတီထွင်ရ**。 မတိုင်းရသေးသော အကွက်ကို `—` ထားသည်。
    ⚠️ ကျမှုမှာမှ အသုံးဝင်ဆုံး ⇒ `finally` ကနေ ခေါ်ရမည်。
    """
    os.makedirs(REPORTS, exist_ok=True)
    p = os.path.join(REPORTS, f"{jid}.txt")
    g = R.get
    L = []
    A = L.append
    A(f"IKKI RENDER · {jid} · style={_mk(g('style'))} · "
      f"{time.strftime('%Y-%m-%d %H:%M')}")
    A("-" * 62)
    A(f"INPUT     {_mk(g('src_dur'))}s · {_mk(g('w'))}x{_mk(g('h'))} "
      f"@{_mk(g('fps'))} · cls={_mk(g('cls'))}")
    A("")
    ga = g("gloss")
    if ga is None:
        A("GLOSSARY  —")
    else:
        _fm = lambda v: (f"အတိအကျ {v['exact']}" +
                         ("".join(f" · {k} {n}" for k, n in v["variants"].items()) or ""))
        A(f"GLOSSARY  {'ဖွင့်' if ga['enabled'] else 'ပိတ်'} · term {len(ga['terms'])} · "
          f"CJK {len(ga['cjk'])} ခု   [=0]" + _tick(len(ga["cjk"]) == 0)
          + (f"  {' '.join(sorted(set(ga['cjk'])))}" if ga["cjk"] else ""))
        for k, v in ga["terms"].items():
            A(f"          term  {k:<12} {_fm(v)}")
        for k, v in ga["watch"].items():
            A(f"          watch {k:<12} {_fm(v)}")
    A("")
    # ⚠️ bias fallback % — ပြန်စ တိကျမှုနဲ့ ဆက်စပ် (n=၄ · **ဂိတ် မဟုတ်သေး**)
    _bp = g('bias_pct')
    if _bp is not None:
        _as = g('asr_stat') or {}
        # ⚠️ **`timed` နဲ့ မတိုင်းရ** — `asr._place()` ရဲ့ မှတ်ချက်: ခေတ္တရပ်
        #    မရှိသော ဝါကျကို snap မရတာ ချို့ယွင်းချက် မဟုတ်、⇒ **ရနိုင်သူ
        #    (`reach`) နဲ့သာ** တိုင်းရမည်。 `timed` နဲ့ တိုင်းလျှင် ခေတ္တရပ်
        #    မရှိသော footage မှာ 「1/26」ဟု ပေါ်ပြီး engine ပျက်နေသလို
        #    ထင်ရသည် (တကယ်က ရနိုင်တာ ၁ ခုပဲ ရှိသည် · ၂၀၂၆-၀၉-၂၁ တိုင်းချက်)。
        _rch = _as.get('reach')
        A(f"ASR align snap {_mk(_as.get('snapped'))}/{_mk(_rch)} ရနိုင် "
          f"(ဝါကျ {_mk(_as.get('timed'))}) · bias fallback {_mk(_bp)}%"
          f"   [ဂိတ် မဟုတ် — မှတ်တမ်းသာ]")
        # ⚠️ bias က **ဘယ်ကလာလဲ ပြရမည်** — ချေးယူထားတာဆိုလျှင် အဲဒါကို
        #    ဖုံးထားလို့ မရ (「Name the blocker」)。
        _bs = _as.get('bias_src')
        if _bs:
            A("          bias " + _mk(_as.get('bias_s')) + "s · " +
              ("ဒီဖိုင်ကနေ တိုင်းယူ (တွဲ " + _mk(_as.get('bias_pairs')) + ")"
               if _bs == "measured" else
               "⚠️ **အတည် မပြုရ** — တွဲ " + _mk(_as.get('bias_pairs')) +
               " ခုသာ ရ၍ ချေးယူထားသော ကိန်းကို သုံးသည်"))
    A(f"CUT       silence {_mk(g('cuts'))} ခု · ဖယ် {_mk(g('removed'))}s · "
      f"ratio {_mk(g('removed_ratio'))}   [<={_mk(g('max_removed'))}]"
      + _tick(g('cut_ok')))
    A(f"          ထွက် {_mk(g('out_dur'))}s (span ပေါင်း {_mk(g('span_sum'))}s "
      f"+ drift {_mk(g('drift'))}s) · ရင်းမြစ် {_mk(g('cut_src'))}")
    A(f"          refusals: {_mk(g('refusals')) or '—'}")
    _cw = g('cut_warnings')
    if _cw: A(f"          ⚠️  သတိပေးချက်: {_mk(_cw)}")
    A("")
    gt = g("gem") or {}
    def _gt(k):
        t = gt.get(k)
        return "—" if not t else f"{t['ok']} ok / {t['ok']+t['fail']} ကြိမ်"
    A(f"GEMINI    ask     {_gt('ask')}")
    A(f"          slides  {_gt('slides')} -> ပြန်ရ {_mk(g('slides_got'))} ခု")
    A(f"          broll   {_gt('broll')}")
    _lf = [f"{k}: {v['last']}" for k, v in gt.items() if v.get("last")]
    A(f"          ကျ {sum(v['fail'] for v in gt.values()) if gt else '—'} ကြိမ် · "
      f"နောက်ဆုံး: {_lf[0] if _lf else '—'}")
    A("")
    # ⚠️ **slide နဲ့ gfx overlay က မတူ** — အရင် report မှာ ရောပြီး
    #    "တောင်း 6 → Gemini 14 → တပ်ပြီး 6" ဆိုပြီး မဆီမဆိုင် ဖြစ်ခဲ့သည်。
    #    slide = မျက်နှာပြင်အပြည့် · gfx overlay = ထောင့်က ကတ်。
    A(f"SLIDE     တောင်း {_mk(g('slide_want'))} -> Gemini {_mk(g('slides_got'))} "
      f"-> တပ်ပြီး {_mk(g('slide_placed'))}")
    v, w, ok = _rv(g("checks"), "gfx_share")
    A(f"          share {_mk(v)} (slide ကနေ)              [{_mk(w)}]" + _tick(ok))
    v, w, ok = _rv(g("checks"), "card_len")
    A(f"          အရှည် median {_mk(g('card_med'))}s · min {_mk(g('card_min'))} · "
      f"max {_mk(g('card_max'))}  [{_mk(w)}]" + _tick(ok))
    A("")
    c = g("card") or {}
    A(f"GFX CARD  recipe {_mk(g('gfx_recipe'))} -> ပစ်မှတ် {_mk(g('gfx_want'))} "
      f"-> Gemini ကို တောင်း {_mk(g('gfx_ask'))} -> ပြန်ရ {_mk(g('gfx_got'))} "
      f"-> တပ်ပြီး {_mk(c.get('placed'))}")
    A(f"          ကျော်သွားတာ —  template မတွေ့ {_mk(c.get('no_template'))} · "
      f"ကျဘမ်း {_mk(c.get('build_fail'))}")
    A(f"                        နေရာမတည့် {_mk(c.get('no_room'))} · "
      f"ဘောင်ကျော် {_mk(c.get('out_of_frame'))} · ထပ် {_mk(c.get('overlap'))}")
    A("")
    A(f"BROLL     တပ်ပြီး {_mk(g('broll_n'))}                        "
      f"[recipe {_mk(g('broll_want'))}]" + _tick(g('broll_ok')))
    A(f"          share {_mk(g('broll_share'))}                      "
      f"[<={_mk(g('broll_pct'))}]" + _tick(g('broll_share_ok')))
    A("")
    A(f"CAPTION   ကတ် {_mk(g('caps_n'))} / ရနိုင် {_mk(g('caps_avail'))} ကြောင်း "
      f"(coverage {_mk(g('cap_cover'))})")
    A(f"          cluster fallback {_mk(g('cap_fallback'))} ကြိမ်  [=0]"
      + _tick(g('cap_fb_ok')))
    v, w, ok = _rv(g("checks"), "caption_zone")
    A(f"          baseline {_mk(v)}")
    A("")
    A(f"MOTION    card_in — မတိုင်းရသေး · card_out — မတိုင်းရသေး · "
      f"easing — မတိုင်းရသေး")
    A("")
    v, w, ok = _rv(g("checks"), "sfx_density")
    mv, _mw, _mo = _rv(g("checks"), "sfx_moments")
    # ⚠️ **ပိတ်ထားလျှင် အကြောင်းရင်း ပြရမည်** — ဗလာ ပြလျှင် ချို့ယွင်းချက်
    #    လို့ ထင်မည် (「Do not hide disabled SFX settings」)。
    if g('sfx_off'):
        A(f"SOUND     ⓘ SFX **ပိတ်ထား** — {g('sfx_off')}")
    if g('sfx_plan_n') is not None:
        A(f"          plan cue {_mk(g('sfx_plan_n'))} · ထပ်၍ ဖယ် "
          f"{_mk(g('sfx_dedup'))} · အချိန် မပြောင်းနိုင်၍ ကျော် "
          f"{_mk(g('sfx_skipped') or 0)}")
    A(f"SOUND     SFX cue {_mk(g('sfx_n'))} -> အသံဖြစ်ရပ် {_mk(mv)} · "
      f"{_mk(v)}/min       [{_mk(w)}]" + _tick(ok))
    v, w, ok = _rv(g("checks"), "sfx_spacing")
    A(f"          အနီးဆုံး အကွာ {_mk(v)}s      [{_mk(w)}]" + _tick(ok))
    # ⚠️ **variant ကွဲမကွဲ ပြရမည်** — role တစ်ခုလျှင် ဖိုင်တစ်ခုတည်း
    #    ပြန်ဖြစ်လျှင် report ကနေ တိုက်ရိုက် မြင်ရမည် (audit အချက် C)。
    if g("sfx_variants") is not None:
        A(f"          asset ကွဲပြားမှု {_mk(g('sfx_variants'))} ဖိုင် / "
          f"cue {_mk(g('sfx_n'))} · bank {', '.join(g('sfx_banks') or []) or '—'}")
    if g("sfx_audible") is not None:
        _sl = g("sfx_silent") or 0
        A(f"          stem စစ်ချက် — ကြားရ {_mk(g('sfx_audible'))} · "
          f"အသံမရှိ {_mk(_sl)}" + _tick(_sl == 0))
    if g("sfx_ducked"):
        A(f"          စကားပေါ် ကျယ်လွန်၍ လျှော့ {_mk(g('sfx_ducked'))} ခု")
    lv, lw, lok = _rv(g("checks"), "lufs")
    tv, tw, tok = _rv(g("checks"), "true_peak")
    A(f"          master {_mk(lv)} LUFS [{_mk(lw)}]{_tick(lok)} · "
      f"TP {_mk(tv)} dBTP [{_mk(tw)}]{_tick(tok)}")
    A("")
    A(f"QC        {_mk(g('qc'))}")
    A("-" * 62)
    txt = "\n".join(L)
    with open(p, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    return p, txt


def sweep_scratch(keep=None, failed=False):
    """job scratch ဖိုင်များကို ရှင်းသည်。 `keep` = မဖျက်ရမည့် job id。

    ⚠️ `broll_in`/`gxav`/`mkav` စသည့် job မဟုတ်သော directory များကို
       **မထိရ** — အဲဒါတွေက ဒီစက်ရဲ့ စာကြည့်တိုက် staging ဖြစ်သည်。
    """
    import shutil as _sh
    n = 0
    try: names = os.listdir(SCRATCH)
    except OSError: return 0
    # ⚠️ ဖိုင်ကြီးတွေက **တခြား disk** မှာ ရှိနိုင်သည် — အဲဒါလည်း ရှင်းရမည်
    _extra = []
    if BIG != SCRATCH:
        try: _extra = [(BIG, nm) for nm in os.listdir(BIG) if nm.startswith("j_")]
        except OSError: pass
    # ⚠️ **ကျမှုရဲ့ သက်သေကို မဖျက်ရ**。 အရင်က job ပြီးတိုင်း `_w` ဖျက်သဖြင့်
    #    "ဘာလို့ card နည်းလဲ" ကို ပြန်စစ်လို့ မရတော့ခဲ့ — gx/ · sl/ · b*.mp4
    #    ဖိုင် အရေအတွက်ကို ပြန်ရေလို့ မရ。
    #    ⇒ ကျလျှင် ချန် · `IKKI_KEEP_WORK=1` ဆိုလျှင် အမြဲ ချန် ·
    #      နောက်ဆုံး KEEP_LAST ခုကို ချန်ပြီး အဟောင်းသာ ဖျက်。
    wdirs = sorted((nm for nm in names if nm.startswith("j_") and nm.endswith("_w")),
                   key=lambda x: os.path.getmtime(os.path.join(SCRATCH, x)),
                   reverse=True)
    recent = set(wdirs[:KEEP_LAST])
    for _d, nm in [(SCRATCH, x) for x in names] + _extra:
        if not nm.startswith("j_"): continue
        if keep and nm.startswith(keep): continue
        if nm.endswith("_w") and (KEEP_WORK or failed or nm in recent):
            continue
        p = os.path.join(_d, nm)
        try:
            if os.path.isdir(p): _sh.rmtree(p)
            else: os.unlink(p)
            n += 1
        except OSError as e:
            print(f"  ⚠️ scratch ရှင်းမရ {nm}: {e}", flush=True)
    if n: print(f"  🧹 scratch {n} ခု ရှင်းပြီး · ကျန် {free_gb():.1f} GB", flush=True)
    _kept = [d for d in wdirs if os.path.exists(os.path.join(SCRATCH, d))]
    if _kept:
        print(f"  📦 work/ ချန်ထား {len(_kept)} ခု: {', '.join(_kept[:4])}", flush=True)
    return n




def _avoid_band(src, TH, log=print):
    """ဂရပ်ဖစ် ရှောင်ရမည့် ဒေါင်လိုက် အပိုင်း。

    ⚠️ `faceband` က **မျက်နှာ**ကိုသာ ရှောင်သည် ⇒ ကတ်တွေ **ရင်ဘတ်ပေါ်** ကျခဲ့သည်
       (Zin ၂၀၂၆-၀၉-၁၇: "လူပေါ် မကျအောင်")。 အလျားလိုက် talking-head မှာ
       အပေါ်ပိုင်း (နောက်ခံ) က လွတ်နေသဖြင့် **မျက်နှာ + ကိုယ်ထည်** ကို ရှောင်ပြီး
       ကတ်ကို အပေါ်/ဘေး ပို့သည်。 ဒေါင်လိုက် (3:4) မှာ နေရာ မလွတ်၍ မထိ。
    """
    fb = faceband(src, TH["W"], TH["H"], log)
    if not fb or TH["W"] <= TH["H"]: return fb
    y0, y1 = fb
    h = max(1, y1 - y0)
    # ⚠️ **ချဲ့လွန်းလျှင် ကတ် နေရာ လုံးဝ မကျန်** — v7 မှာ faceband က 0–1392
    #    ပြန်ပေးပြီး ၂.၂ ဆ ချဲ့တော့ 0–2160 (frame တစ်ခုလုံး) ဖြစ်ကာ ကတ်
    #    **၀ ခု** ထွက်ခဲ့သည်。 ⇒ frame ရဲ့ ၇၀% ထက် မကျော်ရ · ၆၀% ကျော်
    #    ဖုံးပြီးသားဆိုလျှင် ထပ်မချဲ့ရ。
    if (y1 - y0) > TH["H"] * 0.60:
        log(f"  ဂရပ်ဖစ် ရှောင်နယ် · {y0}–{y1} (ကျယ်ပြီးသား — မချဲ့)")
        return fb
    y1b = min(int(TH["H"] * 0.70), int(y1 + h * 0.6))
    log(f"  ဂရပ်ဖစ် ရှောင်နယ် · မျက်နှာ {y0}–{y1} → ကိုယ်ထည်အထိ {y0}–{y1b}")
    return (y0, y1b)

def _skin_y(path, n=8, log=print):
    """(float|None) — YCbCr skin mask ရဲ့ Y ပျမ်းမျှ。 ဗီဒီယို တစ်ခုလုံးမှ frame n ခု。

    ⚠️ skin မတွေ့လျှင် None — ချိန်ညှိချက် မလုပ်ရ (B-roll ချည်း ဖြစ်နိုင်)。
    """
    import subprocess as _sp
    d = probe(path).get("dur") or 0
    if d <= 0: return None
    W, H = 320, 180
    vals = []
    for k in range(n):
        t = d * (k + 0.5) / n
        p = _sp.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path,
                     "-frames:v", "1", "-vf", f"scale={W}:{H}", "-pix_fmt", "yuvj444p",
                     "-f", "rawvideo", "-"], capture_output=True)
        buf = p.stdout
        if len(buf) < W * H * 3: continue
        nn = W * H
        Y, Cb, Cr = buf[:nn], buf[nn:2*nn], buf[2*nn:3*nn]
        ys = 0; c = 0
        for i in range(0, nn, 3):
            y, cb, cr = Y[i], Cb[i], Cr[i]
            if 77 <= cb <= 127 and 133 <= cr <= 173 and 40 <= y <= 240:
                ys += y; c += 1
        if c >= (nn / 3) * 0.02:          # frame ရဲ့ ၂% ကျော် skin ဖြစ်မှ
            vals.append(ys / c)
    if not vals: return None
    vals.sort()
    return vals[len(vals) // 2]

def handle(d):
    job, brand = d["job"], d.get("brand")
    jid = job["id"]; t0 = time.time()
    print(f"▶ {jid} · {job.get('recipe')}", flush=True)
    # ⚠️ စမလုပ်ခင် **အရင်ရှင်း**ပြီး နေရာ စစ်ရမည်。 နေရာ မလုံလောက်ဘဲ စလျှင်
    #    ffmpeg က ENOSPC နဲ့ ကျပြီး အကြောင်းရင်းက log ထဲ နက်နက်မှ ပေါ်သည် —
    #    သုံးစွဲသူက "render မရဘူး" ပဲ မြင်ရသည်。 ⇒ ဒီမှာ ရှင်းရှင်း ပြောသည်。
    sweep_scratch(keep=jid)
    # ⚠️ ဂိတ်ကို **ကြာချိန်နဲ့ တွက်၍ မရ**。 4K ၄.၅ GB ဖိုင်က 1080p ဖိုင်နဲ့
    #    ကြာချိန် တူပေမယ့် နေရာ ၄ ဆ လိုသည်。 ကြာချိန်နဲ့ တွက်ခဲ့သဖြင့်
    #    ၃.၀ GB လိုတယ် ဟု ဆုံးဖြတ်ပြီး စလိုက်ရာ ၉၀% မှာ ENOSPC နဲ့ ကျခဲ့သည်
    #    (j_dd56e503c95c · ၂၀၂၆-၀၉-၁၉)。 ⇒ **မူရင်း ဖိုင် အရွယ်**ကနေ တွက်။
    take_sources = [x for x in (d.get("sources") or [d.get("upload")]) if x]
    _sz = sum(float(x.get("size") or 0) for x in take_sources) / (1024**3)
    # ⚠️ **အရှိန်ကို ဒီမှာတင် ဖတ်ရမည်** — proxy ရဲ့ နာမည်က အရှိန်ပေါ်
    #    မူတည်သဖြင့် (`_pxname`) အောက်မှာ ဖတ်လျှင် မှားသော ဖိုင်ကို
    #    「ရှိပြီးသား」ဟု မှတ်မည်。
    try: speech_speed = float((d.get("over") or {}).get("_speech_speed") or 1.0)
    except (TypeError, ValueError): speech_speed = 1.0
    if speech_speed not in (1.0, 1.03, 1.06): speech_speed = 1.0
    _pxr = _pxname(jid, speech_speed)
    _have_px = os.path.exists(_pxr) and os.path.getsize(_pxr) > 1 << 20
    # မူရင်း + proxy + ကြားဖြတ် ဖိုင်များ。 proxy ရှိပြီးသားဆို မူရင်း မလို。
    # ⚠️ **disk ၂ ခုကို သီးသန့် စစ်ရမည်** — ဖိုင်ကြီးက BIG မှာ · PNG တွေက
    #    Mac ထဲ scratch မှာ。 တစ်ခုတည်း စစ်လျှင် ကျန်တစ်ခု ပြည့်ပြီး ကျမည်。
    # Multi-take jobs temporarily need raw takes + joined timeline + proxy.
    # Reserve for all three; starting with the single-source estimate would
    # otherwise fail near the end of join on larger 4K projects.
    _need_big = 0.0 if _have_px else (_sz * (2.75 if len(take_sources) > 1 else 1.25))
    _need_w   = max(2.0, (job.get("src_dur") or 600)/600.0*2.5)   # ကြားဖြတ် ဖိုင်
    _hb, _hw = free_gb(BIG), free_gb(SCRATCH)
    _same = os.stat(BIG).st_dev == os.stat(SCRATCH).st_dev
    if _same:
        if _hw < _need_big + _need_w:
            raise RuntimeError(
                f"disk နေရာ မလုံလောက်ပါ — ကျန် {_hw:.1f} GB၊ ဒီဗီဒီယိုအတွက် "
                f"~{_need_big + _need_w:.1f} GB လိုသည် (မူရင်း {_sz:.1f} GB)။ "
                f"စက်ထဲက ဖိုင်တွေ ရှင်းပါ — သို့မဟုတ် ဖိုင်ကြီးများကို "
                f"ပြင်ပ disk မှာ ထားရန် `IKKI_BIG` သတ်မှတ်ပါ။")
    else:
        if _hb < _need_big:
            raise RuntimeError(
                f"ဖိုင်ကြီး disk ({BIG}) နေရာ မလုံလောက်ပါ — ကျန် {_hb:.1f} GB၊ "
                f"~{_need_big:.1f} GB လိုသည် (မူရင်း {_sz:.1f} GB)။")
        if _hw < _need_w:
            raise RuntimeError(
                f"Mac disk နေရာ မလုံလောက်ပါ — ကျန် {_hw:.1f} GB၊ "
                f"~{_need_w:.1f} GB လိုသည်။ စက်ထဲက ဖိုင်တွေ ရှင်းပါ။")
        print(f"  💾 ဖိုင်ကြီး → {BIG} (ကျန် {_hb:.0f} GB) · "
              f"ကြားဖြတ် → Mac ထဲ (ကျန် {_hw:.1f} GB)", flush=True)
    src = os.path.join(BIG, jid + "_src.mp4")
    # ⚠️ ဖိုင်ကြီးကို memory ထဲ တစ်ခါတည်း မယူရ၊ တိုးတက်မှုကိုလည်း **ပြရမည်**。
    #    ၄၁၉ MB ဖိုင်တစ်ခုက ၀.၆၆ MB/s နှုန်းနှင့် ၁၀ မိနစ် ကြာခဲ့ပြီး UI မှာ
    #    ဘာမှ မပြသဖြင့် "ရပ်နေတယ်" ဟု ထင်ခဲ့ရသည်。
    # ⚠️ **retry မှာ proxy ရှိပြီးသားဆို ပြန်သုံးရမည်**。 အရင်က retry တိုင်း
    #    ၄.၅ GB ကို အစကနေ ပြန်ဆွဲချ (၆၃၀s) ပြီး proxy ကို ပြန်လုပ် (၃၀၆s)
    #    နေခဲ့သည် — နှစ်ခုလုံး လုပ်ပြီးသား ဖြစ်ပါလျက် (၂၀၂၆-၀၉-၁၉)。
    # `take_map` is cached with the joined timeline.  On the post-review pass
    # it is also sent back in `over`, so a proxy retry never loses provenance.
    take_map = list((d.get("over") or {}).get("_take_map") or [])
    if _have_px:
        src = _pxr
        print(f"  ♻️  proxy ရှိပြီးသား — ဆွဲချ/ချုံ့ ကျော်သွားသည် "
              f"({os.path.getsize(_pxr)/1e6:.0f} MB)", flush=True)
    elif len(take_sources) > 1:
        joined = os.path.join(BIG, jid + "_takes.mp4")
        joined_map = os.path.join(BIG, jid + "_takes.json")
        cached = _take_map_read(joined_map)
        if os.path.exists(joined) and os.path.getsize(joined) > (1 << 20) and cached:
            src, take_map = joined, cached
            print(f"  ♻️  take timeline ရှိပြီးသား — {len(take_map)} takes", flush=True)
        else:
            paths = []
            for n in range(len(take_sources)):
                dest = os.path.join(BIG, f"{jid}_take{n + 1}.mp4")
                cb = lambda pc, mb, sp, n=n: req(
                    f"/api/w/{jid}/stage",
                    {"stage":0,"name":f"take {n + 1}/{len(take_sources)} · {pc}% ({mb:.0f} MB)",
                     "minutes":(time.time()-t0)/60})
                if n == 0: got = fetch_src(jid, dest, cb)
                else: got = fetch_take(jid, n, dest, cb)
                paths.append(got or dest)
            src, take_map = join_takes(jid, paths, take_sources,
                                       log=lambda x: print(x, flush=True))
    else:
        # ⚠️ `fetch_src` ရဲ့ **ပြန်ပေးချက်ကို ယူရမည်** — ဖိုင်က ဤစက်ထဲ ရှိပြီးသားဆို
        #    ဆွဲချစရာ မလိုဘဲ **အဲဒီ လမ်းကြောင်း**ကို ပြန်ပေးသည်。
        src = fetch_src(jid, src, lambda pc, mb, sp:
                  req(f"/api/w/{jid}/stage",
                      {"stage":0,"name":f"ဆွဲချ {pc}% ({mb:.0f} MB · {sp:.1f} MB/s)",
                       "minutes":(time.time()-t0)/60})) or src
        print(f"  ဆွဲချ {os.path.getsize(src)/1e6:.0f} MB · {time.time()-t0:.1f}s", flush=True)
    # ── dual-system — recorder အသံ ရှိလျှင် ချိန်ညှိပြီး ပေါင်း ────────────
    # ⚠️ ကင်မရာ mic က −53 LUFS ဖြစ်တတ်ပြီး သီချင်းက စကားကို ဖုံးသည်。
    #    offset ကို **တိုင်းရမည်** — ဂိတ် မအောင်လျှင် **မပေါင်းဘဲ ဆက်သွား**
    #    (မှားညှိလျှင် အသံနဲ့ ပုံ လွဲပြီး ဗီဒီယို တစ်ခုလုံး ပျက်သည်)。
    a2 = None
    if len(take_sources) == 1:
        try:
            a2 = os.path.join(SCRATCH, jid + "_aud")
            fetch_src(jid, a2, path="src2")
        except Exception:
            a2 = None
    else:
        print("  ⓘ multi-take project — recorder audio မပေါင်းပါ", flush=True)
    if a2 and os.path.exists(a2) and os.path.getsize(a2) > 4096:
        try:
            import dual as DU   # core က line 20 မှာ path ထဲ ရှိပြီးသား
            off, ok, inf = DU.offset(src, a2, log=lambda m: print(m, flush=True))
            if ok:
                mx = os.path.join(SCRATCH, jid + "_mux.mp4")
                DU.mux(src, a2, mx, off, log=lambda m: print(m, flush=True))
                os.remove(src); src = mx
                print(f"  ✓ recorder အသံ သုံးသည် (offset {off:+.2f}s)", flush=True)
            else:
                print(f"  ⚠️ **အသံ မပေါင်းပါ** — {inf.get('why','ဂိတ် မအောင်')} "
                      f"⇒ ကင်မရာ အသံ ဆက်သုံးသည်", flush=True)
        except Exception as e:
            print(f"  ⚠️ အသံ ပေါင်း၍ မရ: {type(e).__name__}: {e}", flush=True)
        finally:
            try: os.remove(a2)
            except Exception: pass
    # Retiming happens after any camera/recorder audio mux but before ASR,
    # cutting, captions, graphics and SFX.  Thus every downstream timestamp
    # is in the same (possibly sped-up) timeline.
    try: speed_applied = float((d.get("over") or {}).get("_speed_applied") or 0.0)
    except (TypeError, ValueError): speed_applied = 0.0
    if speech_speed != 1.0 and not _have_px:
        src = speed_source(jid, src, speech_speed, log=lambda x: print(x, flush=True))
        if abs(speed_applied - speech_speed) > 0.001:
            take_map = scale_take_map(take_map, speech_speed)
    elif speech_speed != 1.0:
        # ⚠️ **ကျော်တာကို ပြရမည်** — proxy က အဲဒီအရှိန်နဲ့ ဆောက်ထားပြီး ဖြစ်၍
        #    ထပ်မြှင့်စရာ မလိုပါ。 log မပြလျှင် 「အရှိန် အလုပ်မလုပ်ဘူး」ဟု
        #    ထင်စရာ ဖြစ်မည် (`_pxname` ရဲ့ မှတ်ချက် ကြည့်)。
        print(f"  ♻️ {speech_speed:.2f}× proxy ရှိပြီးသား — retiming ထပ်မလုပ်ပါ "
              f"(ထပ်မြှင့်မိခြင်း မဖြစ်စေရန်)", flush=True)
    out = os.path.join(SCRATCH, jid + ".mp4")
    def stage(n, name):
        req(f"/api/w/{jid}/stage", {"stage":n,"name":name,"minutes":(time.time()-t0)/60})
        print(f"  {n}/7 {name}", flush=True)
    REPORT.clear()
    try:
        import sys as _sys
        _cp = _sys.modules.get("captions")
        if _cp is not None: _cp.FALLBACK[0] = 0
        _gg = _sys.modules.get("gemguard")
        if _gg is not None: _gg.tally_reset()
    except Exception: pass
    _failed = False
    render_over = dict(d.get("over") or {})
    if take_map: render_over["_take_map"] = take_map
    try:
        try:
            m, mo, st, ncap = render(job, brand, src, out, stage,
                                     log=lambda s: print(s, flush=True),
                                     over=render_over)
        except ReviewStop as rs:
            # ⚠️ ကျဘမ်း **မဟုတ်** — သုံးစွဲသူ အတည်ပြုရန် ရပ်လိုက်တာ。
            #    `fail` ကို မခေါ်ရ、မိနစ်လည်း မရေတွက်ရ (ဗီဒီယို မထွက်သေး)。
            req(f"/api/w/{jid}/plan", {"segs": rs.segs, "plan": rs.plan,
                                       "src_dur": rs.plan.get("src_dur")})
            print(f"⏸  စာတမ်း တင်ပြီး · {time.time()-t0:.1f}s\n", flush=True)
            return
        post_thumb(jid, out, log=lambda x: print(x, flush=True))
        post_result(jid, out, dict(src_dur=m["dur"], out_dur=mo["dur"],
                                   cuts=st.get("cuts",0)+st.get("auto_extra",0),
                                   captions=ncap, flags=st.get("flags",0),
                                   flag_list=st.get("flag_list") or [],
                                   segs=st.get("segs") or [],
                                   # ⚠️ မပါလျှင် plan က တိတ်တဆိတ် ပျောက်သည်
                                   edit_plan=st.get("edit_plan"),
                                   minutes=round((time.time()-t0)/60, 2), note=job.get("recipe","")))
    except Exception:
        _failed = True
        raise
    finally:
        # ⚠️ **report ကို ကျလည်း ထုတ်ရမည်** — ကျမှုမှာမှ အသုံးဝင်ဆုံး。
        try:
            rp, rtxt = write_report(jid, REPORT)
            print(rtxt, flush=True)
            print(f"  📄 report · {rp}", flush=True)
        except Exception as _e:
            print(f"  ⚠️ report မထုတ်နိုင်: {type(_e).__name__}: {_e}", flush=True)
        # ⚠️ **ကျဘမ်းဖြစ်လည်း ရှင်းရမည်**。 အရင်က အောင်မြင်မှသာ src/out ဖျက်ပြီး
        #    `_w` ကို ဘယ်တော့မှ မဖျက်ခဲ့ ⇒ scratch မှာ ၃.၈ GB ပုံနေပြီး disk
        #    ပြည့်သွားကာ render က span s0077 မှာ ကျဘမ်း ဖြစ်ခဲ့သည် (တကယ်)。
        # ⚠️ ကျခဲ့လျှင် **proxy ကို ချန်ရမည်** — retry မှာ ၄.၅ GB ပြန်ဆွဲချ/
        #    ၃၀၆s ပြန်ချုံ့ စရာ မလိုတော့ (၂၀၂၆-၀၉-၁၉)。 မူရင်းကတော့ ကြီးလွန်း၍
        #    **ဖျက်**သည် — proxy ရှိရင် မလိုတော့。
        if _failed:
            try:
                _s0 = os.path.join(BIG, jid + "_src.mp4")
                if os.path.exists(_s0) and os.path.exists(
                        _pxname(jid, speech_speed)):
                    os.remove(_s0)
                    print("  🧹 မူရင်း ဖျက် — proxy ချန်ထားသည် (retry မြန်ရန်)", flush=True)
            except OSError: pass
            sweep_scratch(keep=jid, failed=True)
        else:
            sweep_scratch(keep=None, failed=_failed)
    print(f"✅ ပြီး · {time.time()-t0:.1f}s\n", flush=True)

def pull_broll():
    """UI ကနေ တင်လာသော ပုံ/ရုပ်ကြမ်းကို ဆွဲပြီး **ဒီစက်ရဲ့ စာကြည့်တိုက်ထဲ** index。

    ⚠️ စာကြည့်တိုက်က Mac ပေါ်မှာ ရှိသည် (Gemini tag တပ်ရ၍ · ဖိုင်တွေ ကြီး၍)。
       VPS က ခဏ ကိုင်ထားရုံ — index ပြီးတာနဲ့ အဲဒီက ဖျက်သည်。
    """
    try:
        d = req("/api/w/broll/pending", None)
    except Exception:
        return
    items = d.get("items") or []
    if not items: return
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "core"))
    import broll as BR, tempfile, shutil as _sh
    stage = os.path.join(SCRATCH, "broll_in"); os.makedirs(stage, exist_ok=True)
    for it in items:
        bid = it["id"]; ext = it.get("ext") or ".jpg"
        dst = os.path.join(stage, (it.get("name") or bid).replace("/", "_"))
        if not dst.lower().endswith(ext.lower()): dst += ext
        try:
            r = urllib.request.Request(API + f"/api/w/broll/{bid}")
            r.add_header("Authorization", "Bearer " + TOKEN)
            with urllib.request.urlopen(r, timeout=600) as f, open(dst, "wb") as o:
                _sh.copyfileobj(f, o)
            n0 = len(BR.load().get("clips") or [])
            BR.index(stage, limit=1, log=lambda m: print(m, flush=True))
            n1 = len(BR.load().get("clips") or [])
            ok = n1 > n0
            tags = []
            if ok:
                c = (BR.load().get("clips") or [])[-1]
                tags = (c.get("my") or [])[:4]
            req(f"/api/w/broll/{bid}/done",
                {"ok": ok, "tags": tags,
                 "note": "" if ok else "Gemini က မသုံးရ ဟု ဆိုသည် ဒါမှမဟုတ် ဖတ်မရ"})
            print(f"  📥 broll {it.get('name')} → {'✅' if ok else '✗'}", flush=True)
        except Exception as e:
            print(f"  ⚠️ broll {bid}: {e}", flush=True)
        finally:
            try:
                if os.path.exists(dst): os.unlink(dst)
            except OSError: pass



# ── စက်ထဲက ဗီဒီယို အညွှန်း ─────────────────────────────────
# ⚠️ worker က သုံးစွဲသူရဲ့ Mac ပေါ်မှာပဲ မောင်းသည်。 ဖိုင်က ဤစက်ထဲ ရှိပြီးသားဆို
#    R2 ကို တင်ပြီး ပြန်ဆွဲချစရာ မလို ⇒ upload ၁၃၇ စက္ကန့် → ၀ (၅၆၂ MB · တိုင်းပြီး)。
#    အညွှန်းက (နာမည်, အရွယ်) ကိုသာ ပေးသည် — ဖိုင် အကြောင်းအရာ မပို့ပါ。
IDX_ROOTS = [x for x in (os.environ.get("IKKI_MEDIA_ROOTS") or "").split(":") if x] or [
    os.path.expanduser("~/Movies"), os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Downloads"), "/Volumes"]
IDX_EXT = (".mp4", ".mov", ".m4v", ".mkv", ".avi", ".mts", ".m2ts")
IDX_EVERY = 600.0
IDX_MAX = 20000
_IDX_AT = [0.0]

def push_index(force=False):
    """စက်ထဲက ဗီဒီယို ဖိုင် စာရင်းကို API သို့ ပို့သည် (နာမည် + အရွယ် + လမ်းကြောင်း)"""
    if not force and time.time() - _IDX_AT[0] < IDX_EVERY: return
    _IDX_AT[0] = time.time()
    out = []
    per, errs = {}, []
    t_all = time.time()
    for root in IDX_ROOTS:
        if not os.path.isdir(root): continue
        n0, t0 = len(out), time.time()
        # ⚠️ `os.walk` က ခွင့်မရသော ဖိုဒါကို **တိတ်တဆိတ် ကျော်**သည် — launchd
        #    အောက်မှာ ~/Downloads · /Volumes တွေ ဖတ်ခွင့် မရှိလျှင် ဘာမှ မပေါ်ဘဲ
        #    「ဖိုင် ၁ ခုပဲ တွေ့」 ဖြစ်သည် (၂၀၂၆-၀၉-၁၉ တကယ် ဖြစ်ခဲ့)。 ⇒ onerror
        for dp, dns, fns in os.walk(root, onerror=lambda e: errs.append(str(e)[:80])):
            # ⚠️ အချိန် ကန့်သတ် — /Volumes က ဖိုင် ၉၀၀၀ ကျော် ရှိပြီး scan ကြာသည်
            if time.time() - t_all > 90: break
            # ⚠️ စနစ်/cache ဖိုဒါများကို ကျော် — မကျော်လျှင် scan က မိနစ်နှင့်ချီ ကြာသည်
            dns[:] = [d for d in dns if not d.startswith(".")
                      and d not in ("Library", "node_modules", "Photos Library.photoslibrary")]
            for fn in fns:
                if not fn.lower().endswith(IDX_EXT): continue
                q = os.path.join(dp, fn)
                try: sz = os.path.getsize(q)
                except OSError: continue
                if sz < 1 << 20: continue          # ၁ MB အောက် — ဗီဒီယို မဟုတ်
                out.append({"name": fn, "size": sz, "path": q})
                if len(out) >= IDX_MAX: break
            if len(out) >= IDX_MAX: break
        if len(out) >= IDX_MAX: break
        per[root] = len(out) - n0
    try:
        d = req("/api/w/index", {"files": out})
        print(f"  📇 စက်ထဲက ဗီဒီယို {d.get('n', len(out))} ဖိုင် အညွှန်း ပို့ပြီး "
              f"— ဒီထဲက ဖိုင်ဆို upload ကျော်မည်", flush=True)
        print("        " + " · ".join(f"{os.path.basename(k) or k}={v}"
                                      for k, v in per.items()), flush=True)
        if errs:
            print(f"        ⚠️ ဖတ်ခွင့် မရသော ဖိုဒါ {len(errs)} ခု — "
                  f"System Settings ▸ Privacy ▸ Full Disk Access မှာ "
                  f"worker ကို ခွင့်ပြုရန်。 ဥပမာ: {errs[0]}", flush=True)
    except Exception as e:
        print(f"  ⚠️ အညွှန်း မပို့နိုင်: {type(e).__name__}: {e}", flush=True)


def main(once=False):
    print(f"worker → {API}  ·  {POLL}s တစ်ကြိမ်", flush=True)
    # ⚠️ **သေနေသော job ကို အရင် ပြန်တန်းစီ**ရမည်。 render လုပ်နေရင်း worker
    #    ပြန်စတင်သွားလျှင် (crash · launchd · deploy · Mac အိပ်) job က
    #    `running` အတိုင်း ထာဝရ ကျန်ပြီး သုံးစွဲသူက ထာဝရ စောင့်နေရသည်。
    #    worker တစ်ခုတည်း ရှိသဖြင့် ဒီအချိန်မှာ လုပ်နေဆဲ job မရှိနိုင် —
    #    ⇒ `running` တွေ့သမျှ သေနေတာ သေချာသည်。
    try:
        d = req("/api/w/reclaim", {})
        if d.get("requeued"):
            print(f"  ♻️  သေနေသော job {len(d['requeued'])} ခု ပြန်တန်းစီပြီး: "
                  f"{', '.join(d['requeued'])}", flush=True)
    except Exception as e:
        print(f"  ⚠️ reclaim မရ: {e}", flush=True)
    # ⚠️ ရပ်သွားခဲ့သော run တွေရဲ့ scratch ကျန်နေတတ်သည် — စချင်းရှင်းသည်
    sweep_scratch(keep=None)
    print(f"  disk ကျန် {free_gb():.1f} GB", flush=True)
    push_index(force=True)
    _bt = 0.0
    while True:
        push_index()
        try:
            # ⚠️ ရုပ်ကြမ်း တင်လာတာကို **၃၀ စက္ကန့်တစ်ခါ** စစ်သည် — job poll
            #    တိုင်း စစ်လျှင် API ကို အလကား ခေါ်များသည်。
            if time.time() - _bt > 30:
                _bt = time.time(); pull_broll()
            # ⚠️ ကိုယ်ပိုင် အမှတ် ပါမှ worker အများကြီး ဘေးကင်း (claim race)
            d = req("/api/w/claim", {"worker": WORKER_ID})
            if d.get("job"):
                jid = d["job"]["id"]
                # ⚠️ **render လုပ်နေကြောင်း အမှတ် ချန်ရမည်**。 `deploy.sh` က
                #    အရင်က `pgrep -f scratch` နဲ့ စစ်ခဲ့ရာ ဂရပ်ဖစ် ၂ ခုကြားက
                #    ffmpeg မရှိသော ခဏလေးမှာ 「ပြီးပြီ」ထင်ပြီး worker ကို
                #    ပြန်စလိုက်သဖြင့် render တစ်ခုလုံး သေခဲ့သည် (၂၀၂၆-၀၉-၂၀
                #    j_e45a95bd33ea · ဒုတိယအကြိမ်)。 ⇒ ffmpeg ကို မစစ်ဘဲ
                #    **ဒီဖိုင်ကို စစ်ရမည်** — pid ပါသဖြင့် worker သေသွားလျှင်
                #    ဟောင်းနေသော အမှတ်ကို ခွဲခြားနိုင်သည်。
                try:
                    with open(BUSY, "w") as _bf:
                        _bf.write(f"{os.getpid()} {jid}\n")
                except OSError: pass
                try: handle(d)
                except Exception as e:
                    tb = traceback.format_exc(); print(f"❌ {e}\n{tb}", flush=True)
                    try: req(f"/api/w/{jid}/fail", {"err": str(e)[:800]})
                    except Exception: pass
                finally:
                    try: os.remove(BUSY)
                    except OSError: pass
                if once: return
            elif once: print("  job မရှိ"); return
        except urllib.error.URLError as e:
            print(f"⚠️  API မရ: {e}", flush=True)
        except Exception as e:
            print(f"⚠️  {e}", flush=True)
        time.sleep(POLL)

if __name__ == "__main__":
    main("--once" in sys.argv)


def subject_x(src, W, H, log=print, n=6):
    """ပြောသူရဲ့ **ဘေးတိုက် အလယ်** (၀–၁) — မရလျှင် `None`

    ⚠️ `faceband()` က ဒေါင်လိုက် (y) ကိုသာ ပြန်ပေးသည် ⇒ 「ဘယ်ဘက်ကို
       တွန်းမလဲ」 မသိပါ。 ဘေးတိုက် ရွှေ့ခြင်းက ဂရပ်ဖစ် နေရာ ရရှိရေးရဲ့
       အဓိက နည်းလမ်း ဖြစ်၍ ဒီကိန်း လိုသည်。
    ⚠️ တိုင်းနည်းက `faceband()` နဲ့ **အတူတူ** (အသား ရောင် mask) —
       မတူလျှင် တစ်ခုက မျက်နှာဟု ဆိုပြီး နောက်တစ်ခုက မဆိုဘဲ ကွဲမည်。
    """
    import numpy as np
    from PIL import Image
    d = probe(src)["dur"]
    xs = []
    for i in range(n):
        t = d * (i + 0.5) / n
        q = os.path.join(os.path.dirname(src), f"_sx{i}.png")
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}",
                            "-i", src, "-frames:v", "1", "-vf",
                            f"crop='min(iw,ih*{W}/{H})':ih,scale=480:-1", q],
                           check=True)
            a = np.asarray(Image.open(q).convert("RGB")).astype(np.int32)
        except Exception:
            continue
        finally:
            try: os.path.exists(q) and os.remove(q)
            except OSError: pass
        h, w = a.shape[:2]
        R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
        mk = (R > 95) & (G > 45) & (B > 25) & (R > G + 12) & (G > B) \
            & ((R - B) > 18) & (R < 250)
        mk[int(h * 0.62):] = False
        col = mk.sum(axis=0)
        if col.sum() < w * 2:
            continue
        # ⚠️ အလယ်မှတ်ကို **အလေးချိန်နဲ့** တွက်သည် — အများဆုံး column တစ်ခု
        #    ယူလျှင် လက်/နောက်ခံ အသားရောင်က ဆွဲသွားနိုင်သည်。
        xs.append(float((col * np.arange(w)).sum() / max(1, col.sum()) / w))
    if not xs:
        return None
    xs.sort()
    cx = xs[len(xs) // 2]
    log and log(f"  ပြောသူ ဘေးတိုက် အလယ် {cx:.2f} "
                f"({'ဘယ်' if cx < 0.45 else ('ညာ' if cx > 0.55 else 'အလယ်')})")
    return cx


def subject_box(src, W, H, log=print, n=8):
    """ပြောသူရဲ့ **ဘောင်** `(x0, x1, y0, y1)` — ၀–၁ အချိုး · မရလျှင် `None`

    ⚠️ **ဒါက ဂရပ်ဖစ် နေရာ ပြဿနာရဲ့ အဖြေ**。 `faceband()` က ဒေါင်လိုက်
       အပိုင်း (y) ကိုသာ ပြန်ပေးသဖြင့် placement က **ဘောင်အကျယ်လုံး**ကို
       ပိတ်ခဲ့သည် ⇒ ကျန်နေရာ ၃၃px。
       တကယ်တော့ ပြောသူက အကျယ်ရဲ့ ၅၇% သာ ယူပြီး ဘယ်ဘက်မှာ
       **၈၂၄ × ၆၉၆ px** လွတ်နေသည် (၂၀၂၆-၀၉-၂၁ တိုင်းချက်)。
       ⇒ box အဖြစ် ပြန်ပေးလျှင် ဘောင် ပြန်ချိန်စရာ မလိုဘဲ နေရာ ရသည်。
    ⚠️ တိုင်းနည်းက `faceband()` နဲ့ **အတူတူ** ဖြစ်ရမည်。
    """
    import numpy as np
    from PIL import Image
    d = probe(src)["dur"]
    bx, by = [], []
    for i in range(n):
        t = d * (i + 0.5) / n
        q = os.path.join(os.path.dirname(src), f"_sb{i}.png")
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}",
                            "-i", src, "-frames:v", "1", "-vf",
                            f"crop='min(iw,ih*{W}/{H})':ih,scale=480:-1", q],
                           check=True)
            a = np.asarray(Image.open(q).convert("RGB")).astype(np.int32)
        except Exception:
            continue
        finally:
            try: os.path.exists(q) and os.remove(q)
            except OSError: pass
        h, w = a.shape[:2]
        R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
        mk = (R > 95) & (G > 45) & (B > 25) & (R > G + 12) & (G > B) \
            & ((R - B) > 18) & (R < 250)
        mk[int(h * 0.62):] = False
        col = mk.sum(axis=0)
        row = mk.sum(axis=1)
        if col.sum() < w * 2:
            continue
        # ⚠️ **အားနည်းသော column ကို ဖယ်ရမည်** — နောက်ခံ သစ်သား/နံရံက
        #    အသားရောင် mask ထဲ ဝင်တတ်ပြီး ဘောင်ကို အကျယ်လုံး ဆွဲသွားမည်。
        cx = np.nonzero(col > max(2, col.max() * 0.12))[0]
        ry = np.nonzero(row > w * 0.02)[0]
        if len(cx) < 4 or len(ry) < 8:
            continue
        bx.append((cx.min() / w, cx.max() / w))
        by.append((ry.min() / h, ry.max() / h))
    if not bx:
        return None
    x0 = min(v[0] for v in bx); x1 = max(v[1] for v in bx)
    y0 = min(v[0] for v in by); y1 = max(v[1] for v in by)
    log and log(f"  ပြောသူ ဘောင် x {x0:.2f}–{x1:.2f} · y {y0:.2f}–{y1:.2f} "
                f"· လွတ်နေရာ ဘယ် {int(x0*W)}px · ညာ {int((1-x1)*W)}px")
    return (x0, x1, y0, y1)
