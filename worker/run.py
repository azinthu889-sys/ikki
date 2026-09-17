#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI Mac worker — API ကို HTTPS ဖြင့် ဆွဲယူသည် (ssh မဟုတ်တော့)。

    python3 worker/run.py [--once]

⚠️ scratch ကို **Mac ထဲမှာသာ** ထားရမည် — ပြင်ပ ExFAT disk မှာ PNG သေးသေး
   ရေးတာ ၂၀ ဆ နှေးသည် (တိုင်းပြီး: ၅၀၀ ဖိုင် · ပြင်ပ 1.47s vs Mac ထဲ 0.07s)。
"""
import json, math, os, shutil, subprocess, sys, time, traceback, urllib.request, urllib.error

API    = os.environ.get("IKKI_API", "http://127.0.0.1:8080")
TOKEN  = os.environ.get("IKKI_WORKER_TOKEN", "dev-worker")
SCRATCH= os.path.expanduser("~/.ikki/scratch")
MK     = os.environ.get("IKKI_MOTIONKIT",
         "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")
POLL   = int(os.environ.get("IKKI_POLL", "6"))
os.makedirs(SCRATCH, exist_ok=True)
sys.path.insert(0, MK)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))

def req(path, data=None, method=None, raw=False):
    url = API + path
    body = None if data is None else json.dumps(data).encode()
    r = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"))
    r.add_header("Authorization", "Bearer " + TOKEN)
    if body: r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=120) as f:
        return f.read() if raw else json.loads(f.read() or b"{}")

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
    # ⚠️ `_drop` က recipe ပြင်ချက် **မဟုတ်** — သုံးစွဲသူ ဖျက်ထားသော အချိန်
    #    အပိုင်းများ။ `RC.clean()` က မသိသော key ကို ဖြုတ်ပစ်သဖြင့် အရင် ခွဲထုတ်ရမည်。
    user_drop = over.pop("_drop", None) or []
    # ⚠️ `_drop_exact` — review မှာ **သုံးစွဲသူ လက်ခံထားသော ပြန်စ** အပိုင်း。
    #    retakes() က စကား နယ်နိမိတ် (M.speech ± edge / gap အလယ်) နဲ့ တွက်ပြီးသား
    #    ⇒ **snap မလုပ်ရ** (snap လျှင် စကား အစွန်းအထိ ရွှေ့ပြီး F2 အာမခံချက် ပျက်)。
    user_drop_exact = over.pop("_drop_exact", None) or []
    rc = RC.apply(job.get("recipe"), over)
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
    LONG = 2560                      # long edge ကန့်သတ် — 4K ရဲ့ ၂/၃
    heavy = (m["w"]*m["h"]*max(1,m["fps"])) > (1920*1080*30)*1.6
    if heavy and max(m["w"], m["h"]) > LONG:
        sc = LONG/float(max(m["w"], m["h"]))
        pw = int(m["w"]*sc)//2*2; ph = int(m["h"]*sc)//2*2
        px = os.path.join(work, "proxy.mp4"); t_px = time.time()
        subprocess.run(["ffmpeg","-v","error","-y","-i",src,
            "-vf",f"scale={pw}:{ph}","-r",str(rc["fps"]),
            "-c:v","h264_videotoolbox","-b:v","16M",
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
            log("  ⚠️ ASR align · calib မရှိ — module ပုံသေ သုံးသည်")

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
    if rc["keep_pause"] is None:
        spans=[(0.0, m["dur"])]; cuts=[]; st={"cuts":0,"in_speech":0,"removed":0.0}
        log("  ⚠️ ဤ recipe က ဖြတ်တောက် မလုပ် (အနားယူချိန် ချန်ထားသည်)")
    else:
        # ⚠️ calib ကို **ချန်နယ်အလိုက်** ရွေးရသဖြင့် ဒီမှာတင် brand လိုသည်
        _bid = (job.get("brand_id") or rc["theme"])
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
        if user_drop:
            _sp2, _sil2, _d2, _e2, _c2 = M2.speech(wav)
            spans, _rm = CUT.subtract(spans, user_drop, _sil2)
            log(f"  သုံးစွဲသူ ဖျက်ချက် {len(user_drop)} ခု · ဖြုတ် {_rm:.1f}s"
                f" → ကျန် {sum(b-a for a,b in spans):.1f}s")
            st["user_removed"] = _rm
            st["user_cuts"] = len(user_drop)
        if user_drop_exact:
            spans, _rm2 = CUT.subtract(spans, user_drop_exact, None, snap=0.0)
            log(f"  ပြန်စ (သုံးစွဲသူ လက်ခံ) {len(user_drop_exact)} ခု · ဖြုတ် {_rm2:.1f}s"
                f" → ကျန် {sum(b-a for a,b in spans):.1f}s")
            st["retake_removed"] = _rm2
            st["retake_cuts"] = len(user_drop_exact)
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
        auto, flags = CL.plan(wav, segs)
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
                CL.CTX.update(job=jid, video=job.get("title") or "", brand=job.get("brand_id"))
                _cl, _cst = CL.retake_clusters(segs, MEAS, _rcal, log=log)
                log(f"  ပြန်စ အုပ်စု {len(_cl)} ခု · take {_cst.get('takes')} · "
                    f"ရွေးစရာ ပိတ် {_cst.get('blocked')} · Gemini {_cst.get('asked')} ကြိမ် · "
                    f"{time.time()-_rt0:.0f}s (**ဘာမှ မဖျက်ပါ** — သုံးစွဲသူ ရွေးမှ)")
            except Exception as _e:
                log(f"  ⚠️ ပြန်စ ရှာမရ — review ဆက်သွား: {type(_e).__name__}: {_e}")
        log(f"  ⏸  စာတမ်း အတည်ပြုရန် ရပ်သည် — စာကြောင်း {len(segs)} · "
            f"အကြံပြု ဖြတ်ချက် {st.get('cuts',0)} ({m['dur']-_kept:.0f}s ဖြုတ်)")
        raise ReviewStop(segs, dict(
            src_dur=round(float(m["dur"]), 2),
            kept=round(_kept, 2),
            cuts=int(st.get("cuts", 0)),
            removed=round(float(m["dur"]) - _kept, 2),
            spans=[[round(a, 2), round(b, 2)] for a, b in spans],
            flags=st.get("flag_list") or [],
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
        theme.THEMES["_ikki"] = TH; theme.use("_ikki")
        f = FM.get(use_fmt, bid)
        log(f"  brand {bid} + format {use_fmt} → {TH['W']}×{TH['H']}"
            f" · BOT {TH['BOT']}" + ("" if f["measured"] else " (safe zone အချိုးတွက်)"))
    IG.OUT = work

    # ── ④ စာတန်း — ဖြတ်ပြီးအချိန်သို့ ပြန်တွက်ပြီး alpha track ဆောက် ──
    stage(4, "captions")
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
    if segs:
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
                gfx.append(dict(at=t["at"], kind=nm,
                                args=TP.targs(nm, t["text"], bname)))
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
    if not gfx:
        # ⚠️ `_sil_of()` ဖယ်ပြီး **မျှသုံး မြေပုံ**ကနေ ဆင်းသက်စေသည်
        gfx = DR.pick(rc, m["dur"], _M.as_gaps(MEAS[1], 0.20), segs)   # ပြန်ဆုတ်လမ်း
        if gfx: log("  ⚠️ အကြောင်းအရာ မရ — တိတ်ဆိတ်မှုပေါ် ချထားသည်")
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
            gmov, ng = DR.track(gfx, None, os.path.join(work,"gx"), TH["W"], TH["H"],
                                rc["fps"], T1, T2, (brand or {}).get("name","IKKI"),
                                rc["label"], log,
                                avoid=_avoid_band(src, TH, log),
                                capy=cap_top, hold=_hold)
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
            _wantn = max(3, int(round(1.16 * _od2 / 60.0)))
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
            # ⚠️ **band အောက် ကျလျှင် ဆွဲတင်ရမည်**。 Gemini က slide နည်းနည်းပဲ
            #    ပြန်ပေးလျှင် ဖုံးအုပ်မှု ၀.၀၉၇ ဖြစ်ပြီး ၀.၁၀ ဘောင် လွဲသည်
            #    (တကယ် ဖြစ်ခဲ့)。 reference မှာ ၁၇.၀s slide ရှိသဖြင့် အဲဒီအထိ
            #    ဆန့်လို့ ရသည် — ရှည်ဆုံးကနေ စပြီး တိုးသည်。
            if slides:
                _need = float(_shb2[0]) * 1.06 * _od2
                _cur = sum(b - a for _p, a, b, _l in slides)
                if _cur < _need and slides:
                    _k = min(1.6, _need / max(_cur, 0.1))
                    _new = []
                    for _p, a, b, _l in slides:
                        nb = a + min(17.0, (b - a) * _k)
                        _new.append((_p, a, nb, _l))
                    # ထပ်သွားလျှင် ပြန်ဖြတ်
                    _fix = []
                    for i, (_p, a, b, _l) in enumerate(_new):
                        if i + 1 < len(_new): b = min(b, _new[i+1][1] - 2.0)
                        if b - a >= 1.0: _fix.append((_p, a, b, _l))
                    slides = _fix
                    log(f"  slide အရှည် ×{_k:.2f} ဆွဲတင် → band ၀.{int(_shb2[0]*100):02d} ရောက်ရန်")
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
          CP.track(caps, capv, os.path.join(work,"cp"),
                   # ⚠️ အရောင်ကို recipe က ပြင်နိုင်သည် — မပြင်လျှင် theme ရဲ့ ပုံသေ
                   TH["W"], TH["H"], csize,
                   rc.get("cap_fill") or TH["WHITE"], rc["mmf"],
                   f'{TH["LATIN"]},{TH["JP"]}', TH["BOT"],
                   IG.ct, IG.MW, fps=rc["fps"],
                   stroke=rc.get("cap_stroke") or rc.get("stroke"),
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
            hits = BR.match(caps, nb, log=log)
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
            if spent < BUD * 0.85:
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
            if bmov: log(f"  B-roll စုစုပေါင်း {spent:.1f}s / ခွင့်ပြု {BUD:.1f}s")
            for at,_,d,tag in bmov: log(f"  B-roll {at:6.2f}s · {d:.1f}s · {tag}")
            log(f"  B-roll {len(bmov)} ခု တပ်ပြီး")
        except Exception as e:
            log(f"  ⚠️ B-roll မရ: {e}"); bmov=[]

    stage(6, "sound")
    cutv = os.path.join(work, "cut.mp4")
    SP.spans(src, spans, cutv, os.path.join(work,"sp"), fps=rc["fps"])
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
        cutv = GR.apply(cutv, gv, rc, log=log)
        if cutv != _pre: _drop(_pre)
    except Exception as e:
        log(f"  ⚠️ grade မရ: {e}")
    # ⚠️ ZAE ရဲ့ house bed ထဲမှာ SFX **ပါပြီးသား** — ထပ်ထည့်လျှင် နှစ်ထပ်
    #    ဖြစ်ပြီး ရှုပ်သည် (project မှတ်တမ်း: "ဖြတ်ချက်တိုင်း SFX ထပ်မထည့်ရ")。
    rc["_dur"] = sum(y - x for x, y in spans)     # sfx density တွက်ရန်
    cues = DR.sfx(gfx, caps, rc) if rc.get("sfx", True) else []
    nsfx = 0
    if cues:
        try:
            sv = os.path.join(work, "sfx.mp4")
            _pre2 = cutv
            _, nsfx = DR.mix(cutv, cues, sv, lambda r: _cue(SL, r, rc["theme"]), log)
            cutv = sv; _drop(_pre2); log(f"  SFX {nsfx} cue")
        except Exception as e:
            log(f"  ⚠️ SFX မရ: {e}")

    # ── ⑦ ဂရပ်ဖစ် ထပ် + အသံ ညှိ + ထုတ် ─────────────────────
    stage(7, "render")
    pngs = []
    # ⚠️ slide ကို **အရင်ဆုံး** ထည့်ရမည် — အောက်ဆုံးအလွှာ ဖြစ်စေရန် မဟုတ်ဘဲ
    #    ဗီဒီယိုပေါ် တိုက်ရိုက် ဖုံးရန်。 ပြီးမှ တခြား ဂရပ်ဖစ် အပေါ်က တက်သည်。
    for _sp, _a, _b, _lay in (slides or []):
        pngs.append((_sp, 0, 0, _a, _b))
    if el:
        ov = el["anim"][-1]
        pngs = [(ov[0], ov[1], ov[2], 0.6, 0.6+el["dur"])]
        for p,x,y,d in el["statics"]: pngs.append((p,x,y,0.6+d,0.6+el["dur"]))
    ins=[]; fc=[f"[0:v]scale={TH['W']}:{TH['H']}:force_original_aspect_ratio=increase,"
               f"crop={TH['W']}:{TH['H']},format=yuv420p[v0]"]
    last="v0"; n=0
    # ⚠️ ZAE က အဖြူ studio wall (RGB ≈ 245,242,243) ပေါ် ရိုက်သည် —
    #    အဖြူစာလုံးက **လုံးဝ မမြင်ရ**。 navy gradient scrim ခံရသည်。
    # ⚠️ B-roll ကို **စာတန်းနဲ့ ဂရပ်ဖစ် အောက်မှာ** ထားရမည် — အပေါ်မှာ
    #    ထားလျှင် စာတန်းကို ဖုံးသည်。 ဒါကြောင့် ဒီနေရာမှာ အရင် ထည့်သည်。
    for at, bp, bd, _t in (bmov or [])[:10]:
        ins += ["-itsoffset", f"{at:.2f}", "-i", bp]; n += 1
        fc.append(f"[{last}][{n}:v]overlay=0:0:eof_action=pass:"
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
    for p,x,y,a,b in pngs:
        d = max(0.1, float(b) - float(a))
        ins += ["-loop","1","-t",f"{d:.2f}","-itsoffset",f"{a:.2f}","-i",p]; n+=1
        fc.append(f"[{last}][{n}:v]overlay={x}:{y}:eof_action=pass:"
                  f"enable='between(t,{a:.2f},{b:.2f})'[v{n}]")
        last=f"v{n}"
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
            MU.bed(raw, mv, rc["music"], probe(raw)["dur"], log=log)
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
        if oa is not None and ob is not None and ob > oa:
            e["o0"] = round(oa, 2); e["o1"] = round(ob, 2)
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
    ok, checks = QC.run(out, st, TH2, caps=caps, cards=_cards,
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

def _cue(SL, role, th):
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

def fetch_src(jid, dest, on_progress=None):
    """source ကို chunk အလိုက် disk ပေါ် တိုက်ရိုက် ရေးသည် · ၁၀% တိုင်း အစီရင်ခံသည်。"""
    r = urllib.request.Request(API + f"/api/w/src/{jid}")
    r.add_header("Authorization", "Bearer " + TOKEN)
    # ⚠️ R2 mode — API က JSON {url:…} ပြန်ပေးသည်。 အဲဒီ URL ကို
    #    **Authorization header မပါဘဲ** ဆွဲရမည် (presigned ဖြစ်သဖြင့်)。
    with urllib.request.urlopen(r, timeout=60) as f0:
        ct = (f0.headers.get("Content-Type") or "")
        if "json" in ct:
            u = json.loads(f0.read()).get("url")
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
        A(f"ASR align bias fallback {_mk(_bp)}% · snap {_mk(_as.get('snapped'))}/"
          f"{_mk(_as.get('timed'))} ဝါကျ   [ဂိတ် မဟုတ် — မှတ်တမ်းသာ]")
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
    A(f"SOUND     SFX cue {_mk(g('sfx_n'))} -> အသံဖြစ်ရပ် {_mk(mv)} · "
      f"{_mk(v)}/min       [{_mk(w)}]" + _tick(ok))
    v, w, ok = _rv(g("checks"), "sfx_spacing")
    A(f"          အနီးဆုံး အကွာ {_mk(v)}s      [{_mk(w)}]" + _tick(ok))
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
    # ⚠️ **ကျမှုရဲ့ သက်သေကို မဖျက်ရ**。 အရင်က job ပြီးတိုင်း `_w` ဖျက်သဖြင့်
    #    "ဘာလို့ card နည်းလဲ" ကို ပြန်စစ်လို့ မရတော့ခဲ့ — gx/ · sl/ · b*.mp4
    #    ဖိုင် အရေအတွက်ကို ပြန်ရေလို့ မရ。
    #    ⇒ ကျလျှင် ချန် · `IKKI_KEEP_WORK=1` ဆိုလျှင် အမြဲ ချန် ·
    #      နောက်ဆုံး KEEP_LAST ခုကို ချန်ပြီး အဟောင်းသာ ဖျက်。
    wdirs = sorted((nm for nm in names if nm.startswith("j_") and nm.endswith("_w")),
                   key=lambda x: os.path.getmtime(os.path.join(SCRATCH, x)),
                   reverse=True)
    recent = set(wdirs[:KEEP_LAST])
    for nm in names:
        if not nm.startswith("j_"): continue
        if keep and nm.startswith(keep): continue
        if nm.endswith("_w") and (KEEP_WORK or failed or nm in recent):
            continue
        p = os.path.join(SCRATCH, nm)
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
    need = max(3.0, (job.get("src_dur") or 600) / 600.0 * 2.5)
    have = free_gb()
    if have < need:
        raise RuntimeError(
            f"disk နေရာ မလုံလောက်ပါ — ကျန် {have:.1f} GB၊ ဒီဗီဒီယိုအတွက် "
            f"~{need:.1f} GB လိုသည်။ စက်ထဲက ဖိုင်တွေ ရှင်းပြီးမှ ပြန်လုပ်ပါ။")
    src = os.path.join(SCRATCH, jid + "_src.mp4")
    # ⚠️ ဖိုင်ကြီးကို memory ထဲ တစ်ခါတည်း မယူရ၊ တိုးတက်မှုကိုလည်း **ပြရမည်**。
    #    ၄၁၉ MB ဖိုင်တစ်ခုက ၀.၆၆ MB/s နှုန်းနှင့် ၁၀ မိနစ် ကြာခဲ့ပြီး UI မှာ
    #    ဘာမှ မပြသဖြင့် "ရပ်နေတယ်" ဟု ထင်ခဲ့ရသည်。
    fetch_src(jid, src, lambda pc, mb, sp:
              req(f"/api/w/{jid}/stage",
                  {"stage":0,"name":f"ဆွဲချ {pc}% ({mb:.0f} MB · {sp:.1f} MB/s)",
                   "minutes":(time.time()-t0)/60}))
    print(f"  ဆွဲချ {os.path.getsize(src)/1e6:.0f} MB · {time.time()-t0:.1f}s", flush=True)
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
    try:
        try:
            m, mo, st, ncap = render(job, brand, src, out, stage,
                                     log=lambda s: print(s, flush=True),
                                     over=d.get('over') or {})
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
    _bt = 0.0
    while True:
        try:
            # ⚠️ ရုပ်ကြမ်း တင်လာတာကို **၃၀ စက္ကန့်တစ်ခါ** စစ်သည် — job poll
            #    တိုင်း စစ်လျှင် API ကို အလကား ခေါ်များသည်。
            if time.time() - _bt > 30:
                _bt = time.time(); pull_broll()
            d = req("/api/w/claim", {})
            if d.get("job"):
                jid = d["job"]["id"]
                try: handle(d)
                except Exception as e:
                    tb = traceback.format_exc(); print(f"❌ {e}\n{tb}", flush=True)
                    try: req(f"/api/w/{jid}/fail", {"err": str(e)[:800]})
                    except Exception: pass
                if once: return
            elif once: print("  job မရှိ"); return
        except urllib.error.URLError as e:
            print(f"⚠️  API မရ: {e}", flush=True)
        except Exception as e:
            print(f"⚠️  {e}", flush=True)
        time.sleep(POLL)

if __name__ == "__main__":
    main("--once" in sys.argv)
