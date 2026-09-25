#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · စာသားကနေ ဂရပ်ဖစ် ခေါင်းစဉ် ထုတ်ခြင်း。

⚠️ **ဂရပ်ဖစ်ကို တိတ်ဆိတ်မှုပေါ် မချရ** — ဒါက အကြီးဆုံး အမှားပါ。
   "② စာမေးပွဲ" ဆိုတဲ့ အခန်းခေါင်းစဉ်က *စာမေးပွဲအကြောင်း ပြောတဲ့အခါ*
   ပေါ်ရမယ်၊ တိတ်တဲ့အခါ မဟုတ်。 လက်နဲ့ လုပ်တုန်းက အဲဒီလို ချခဲ့သည် —
   app က တိတ်ဆိတ်မှုပေါ် ချမိသဖြင့် ကျဘမ်း ဖြစ်ခဲ့သည်。

⇒ စာသားကို Gemini ကို ပေးပြီး **ဘယ်စာကြောင်းမှာ ဘယ်ခေါင်းစဉ် ထိုက်တန်လဲ**
  မေးသည်。 ပြီးလျှင် အဲဒီစာကြောင်းရဲ့ အချိန်ကို သုံးသည်。
"""
import json, os, re, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gemguard as G

MODEL = os.environ.get("IKKI_GEMINI_MODEL", "gemini-3.1-flash-lite")

KINDS = {
 "title":   "ခေါင်းစဉ် — ဗီဒီယိုရဲ့ အကြောင်းအရာ (အစမှာ တစ်ခါပဲ)",
 "chapter": "အခန်း — အကြောင်းအရာ အသစ် စတဲ့နေရာ",
 "fact":    "အချက်အလက် — ကိန်းဂဏန်း ဒါမှမဟုတ် အတိအကျ အချက်",
 "label":   "အညွှန်း — နေရာနာမည် · အဖွဲ့အစည်းနာမည်",
 "cta":     "ဖိတ်ခေါ်ချက် — comment · message ပြောတဲ့နေရာ",
}

PROMPT = """အောက်တွင် မြန်မာဗီဒီယိုတစ်ခု၏ စာတမ်းကို စာကြောင်းနံပါတ်နှင့် ပေးထားသည်။

ဤဗီဒီယိုအတွက် **မျက်နှာပြင်ပေါ် တင်သင့်သော ဂရပ်ဖစ်** များကို ရွေးပေးပါ။

အမျိုးအစားများ:
%s

စည်းကမ်း:
- အများဆုံး %d ခု
- စာကြောင်းရဲ့ **အကြောင်းအရာနှင့် ကိုက်ရမည်** — ပေါ်လာသင့်တဲ့ အချိန်မှာ
- စာသားက **တိုရမည်** — မြန်မာ ၂–၅ လုံး ဒါမှမဟုတ် English ၁–၃ လုံး
- စာတမ်းထဲ ရှိသော အကြောင်းအရာကိုသာ ရေးရမည်။ **မရှိတာ မဖန်းရ**
- JSON array ကိုသာ ပြန်ပါ။ ရှင်းလင်းချက် မထည့်ပါနှင့်

ပုံစံ: [{"line": 3, "kind": "chapter", "text": "စာမေးပွဲ"}, ...]

စာတမ်း:
%s"""

CAP = 400          # ⚠️ prompt ထဲ ထည့်မည့် segment အများဆုံး

def ask(segs, want=6, log=print):
    """စကားဝိုင်းထဲက ခေါင်းစဉ်များ ရွေးသည်。

    ⚠️ အရင်က `segs[:80]` — **ပထမ ၈၀ ခုကိုသာ** ပြခဲ့သည်。 ၁၅ မိနစ်
       ဗီဒီယိုမှာ segment ၂၁၄ ခု ရှိသဖြင့် ဂရပ်ဖစ်အားလုံး ပထမ ၃၇%
       ထဲမှာပဲ ပေါ်နိုင်ပြီး နောက်ပိုင်း ၆၃% မှာ လုံးဝ မပေါ်ခဲ့。
       အတိုတွေမှာ segment ၈၀ အောက်မို့ မသိသာခဲ့ခြင်း ဖြစ်သည်。
    ⚠️ CAP ကျော်လျှင် **တစ်ပြေးညီ နမူနာယူ**ရမည် (ရှေ့ပိုင်း ဖြတ်ယူ၍ မရ) —
       ပြန်ပေးလာသော `line` က နမူနာစာရင်းရဲ့ အညွှန်း ဖြစ်၍ မူရင်း
       segment သို့ ပြန်ပြောင်းပေးရသည်。
    """
    if not segs: return []
    if len(segs) > CAP:
        step = len(segs) / float(CAP)
        idx = sorted({min(len(segs)-1, int(i*step)) for i in range(CAP)})
        log(f"  ⚠️ segment {len(segs)} ခု — {len(idx)} ခု တစ်ပြေးညီ နမူနာယူသည်")
    else:
        idx = list(range(len(segs)))
    view = [segs[i] for i in idx]
    lines = "\n".join(f"{i+1}. {s['text']}" for i,s in enumerate(view))
    kinds = "\n".join(f"- {k}: {v}" for k,v in KINDS.items())
    body = {"contents":[{"parts":[{"text": PROMPT % (kinds, want, lines)}]}],
            "generationConfig":{"temperature":0.2}}
    for i in range(3):
        G.throttle()
        r = urllib.request.Request(G.endpoint(MODEL), data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text","") for p in d["candidates"][0]["content"]["parts"])
            m = re.search(r"\[.*\]", txt, re.S)
            if not m:
                G.log_fail("ask", i + 1, 3, None, "JSON မတွေ့", final=True); return []
            out=[]
            for x in json.loads(m.group(0)):
                n = int(x.get("line", 0)) - 1
                if 0 <= n < len(view) and x.get("text"):
                    g = idx[n]                       # ← မူရင်း segment သို့ ပြန်
                    out.append(dict(at=segs[g]["start"], kind=x.get("kind","label"),
                                    text=str(x["text"])[:40], line=g))
            out.sort(key=lambda z: z["at"])
            G.tally("ask", True)
            log(f"  ခေါင်းစဉ် {len(out)} ခု ရွေးပြီး")
            return out
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8","replace")
            G.log_fail("ask", i + 1, 3, e.code, raw, final=G.fatal(e.code, raw))
            if G.fatal(e.code, raw): return []
            mm = re.search(r'"retryDelay"\s*:\s*"(\d+)s"', raw)
            time.sleep(int(mm.group(1)) if mm else 6*(i+1))
        except Exception as e:
            G.log_fail("ask", i + 1, 3, None, f"{type(e).__name__}: {e}")
            time.sleep(5*(i+1))
    G.log_fail("ask", 3, 3, None, "retry ကုန် — [] ပြန်", final=True)
    return []

# ══ kind → template ═══════════════════════════════════════
# ⚠️ အရင်က kind တစ်ခုလျှင် template **တစ်ခုတည်း** — ဗီဒီယိုတိုင်း
#    title_card · chapter · fact_box · locator · label_pill ပဲ ထွက်ပြီး
#    **အားလုံး တစ်ပုံစံတည်း** ဖြစ်နေခဲ့သည်。
# ⚠️ ⇒ role တစ်ခုလျှင် **ရေကန်** ထားပြီး ဗီဒီယိုအလိုက် ပြောင်းသုံးသည်。
#    ရေကန်ထဲက အားလုံးကို **တစ်ခုချင်း သီးသန့် process နဲ့ render စမ်းပြီး**
#    အောင်မြင်ခဲ့သည် (assets/gfx_ok.txt · ၅၉/၁၉၄)。 မစမ်းဘဲ ထည့်လျှင်
#    argument ပုံစံ ကွာသဖြင့် တိတ်တဆိတ် ကျဘမ်း ဖြစ်မည်。
# ⚠️ အောက်ပါ template တွေကို pool ကနေ **ဖယ်ထား**သည် — တကယ့် မြန်မာ
#    ဝါကျနဲ့ တစ်ခုချင်း render စမ်းပြီး တိုင်းထားသည် (၄၂/၄၆ အောင်)。
#      bumper · number_hero · tag_call — စာက canvas ဘေး ပြတ်သည်
#      countdown — argument mapping ကျဘမ်း
#    မှန်းပြီး ထည့်ထားလျှင် ဗီဒီယိုထဲ စာပြတ်နေတာ ထွက်သည် (တကယ် ဖြစ်ခဲ့)。
POOLS = {
 "title":   ["title_card", "kicker_title", "split_title", "opening_bars",
             "intro_stinger", "episode_card", "side_bar", "glass_third"],
 "chapter": ["chapter", "section", "step_flow", "id_strip",
             "episode_card"],
 "fact":    ["fact_box", "big_number", "stat_title", "pull_quote", "quote_title",
             "quote_block", "stack_call", "scan_box", "vs_split"],
 "label":   ["locator", "name_plate", "map_locator", "minimal_third",
             "photo_third", "name_tag_jp", "badge", "clock_strip"],
 "cta":     ["label_pill", "cta_card", "outro_cta", "subscribe_bug",
             "phone_cta", "end_card", "price_tag", "alert_strip"],
 # ⚠️ အလေးထားချက် စာကြောင်းအတွက် — ပုံမှန် စာတန်းအစား ဒါတွေနဲ့ ထုတ်သည်。
 #    ၈ ခုလုံး တစ်ခုချင်း render စမ်းပြီးသား (assets/gfx_ok.txt)。
 "typo":    ["kern_wide", "quote_block", "sweep",
             "typewriter", "subtitle_2line", "quote_marks", "vertical_jp"],
}

_OKSET = None
def _ok():
    """တကယ် render စမ်းပြီး အောင်မြင်ခဲ့သော template နာမည် set"""
    global _OKSET
    if _OKSET is None:
        _OKSET = set()
        try:
            p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "assets", "gfx_ok.txt")
            for l in open(p, encoding="utf-8"):
                l = l.strip()
                if "." in l: _OKSET.add(l.split(".", 1)[1])
        except OSError:
            pass
    return _OKSET

def templ(kind, seed=0, used=None):
    """(template နာမည်, argument builder) — ရေကန်ထဲမှ ရွေးသည်。

    ⚠️ seed ကို job id ကနေ ပေးရမည် — ဗီဒီယိုတစ်ခုတည်းမှာ ထပ်တလဲလဲ
       မဖြစ်စေရန် `used` နှင့် ရှောင်ပြီး၊ ဗီဒီယိုအလိုက် ကွဲပြားစေရန်。
    """
    pool = [t for t in POOLS.get(kind, []) if t in _ok()] or POOLS.get(kind) or ["title_card"]
    fresh = [t for t in pool if t not in (used or set())] or pool
    return fresh[seed % len(fresh)]

# ⚠️ ဒီ ၁၂ ခုက **လက်နဲ့ စမ်းပြီး မှန်ကန်ကြောင်း သိပြီးသား** — catalog ရဲ့
#    အလိုအလျောက် ဖြည့်ချက်ထက် ဒါက အထက်တန်း。 ဖယ်လိုက်မိသဖြင့် fact_box က
#    number မျှော်တဲ့နေရာ စာသား ရပြီး ကျဘမ်း ဖြစ်ခဲ့သည် (တကယ် ဖြစ်ခဲ့)。
CURATED = {
 "title_card":   lambda t,b: (t, b),
 "chapter":      lambda t,b: ("၀၁", t),
 "fact_box":     lambda t,b: (t, ""),
 "locator":      lambda t,b: (t, ""),
 "label_pill":   lambda t,b: (t,),
 "headline_bar": lambda t,b: ("သတင်း", t),
 "big_number":   lambda t,b: ("100%", t, ""),
 "pull_quote":   lambda t,b: (t, ""),
 "kicker_title": lambda t,b: (b, t),
 "section":      lambda t,b: (t,),
 "stat_title":   lambda t,b: ("100%", t),
 "topic_bar":    lambda t,b: (t,),
 "name_plate":   lambda t,b: (t,),
 "end_card":     lambda t,b: (b, t, ""),
 "badge":        lambda t,b: (t,),
 "side_bar":     lambda t,b: (t,),
 "bumper":       lambda t,b: (b,),
 "quote_title":  lambda t,b: (t,),
 "split_title":  lambda t,b: (t, b),
}

# ══ ဂရပ်ဖစ် စာသား အရှည် ═══════════════════════════════════════
# ⚠️ ဂရပ်ဖစ်က **စကားစုတို** ဖြစ်ရမည် — ဝါကျအပြည့် မဟုတ်。 စာတန်းကြောင်း
#    တစ်ခုလုံး (၅၀+ အက္ခရာ) ကို ထည့်လျှင် template က ချုံ့ရာ floor ကို
#    ကျော်ပြီး **ဘေးနှစ်ဖက် ပြတ်**သည် (typewriter · sweep · quote_marks —
#    တကယ် ဖြစ်ခဲ့、v27 မှာ ၂ ခု ပြတ်နေသည်ကို မြင်ရသည်)。
#    ⇒ ၃၂ အက္ခရာအထိ **စကားလုံး နယ်နိမိတ်မှာ** ဖြတ်သည်。
GTXT = 32

def trim(t, n=GTXT):
    t = (t or "").strip()
    if len(t) <= n: return t
    cut = t[:n]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp >= n*0.5 else cut).rstrip(" ·,။")

def targs(name, text, sub=""):
    """template ရဲ့ argument — curated ရှိလျှင် အဲဒါ၊ မရှိမှ catalog ကနေ"""
    text = trim(text)
    f = CURATED.get(name)
    if f:
        try: return f(text, sub or "IKKI")
        except Exception: pass
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import gfxcat as GC
        for e in GC.catalog():
            if e["fn"] == name:
                return GC.fill(e, text, sub) or (text,)
    except Exception:
        pass
    return (text, sub) if sub else (text,)


# ══ အလေးထားရမည့် စာကြောင်း ရွေးခြင်း ═══════════════════════
# ⚠️ Knowledge Sharing ပုံစံမှာ စာတန်းက **အားလုံး မပေါ်ဘူး**。 Zin ပေးသော
#    reference ၂ ခုကို တိုင်းကြည့်တော့ frame ရဲ့ ၁၀% နှင့် ၁၇% ပဲ စာတန်း
#    ပါသည် (slide မပါ)。 အားလုံး ချလျှင် ဒီပုံစံ မဖြစ်ဘူး。
#    ⇒ ဘယ်စာကြောင်းက **အလေးထားထိုက်လဲ** Gemini ကို မေးသည်。
EMPH = """အောက်တွင် မြန်မာဗီဒီယိုတစ်ခု၏ စာတမ်းကို စာကြောင်းနံပါတ်နှင့် ပေးထားသည်။

ဤဗီဒီယိုမှာ စာတန်း (subtitle) ကို **အားလုံး မပြပါ**။ အရေးကြီးသော
စာကြောင်းများမှာသာ မျက်နှာပြင်ပေါ် စာတင်ပါမည်။

**ဘယ်စာကြောင်းတွေကို စာတင်သင့်လဲ** ရွေးပေးပါ:
- အဓိက အချက် · နိဂုံး · မှတ်သားထိုက်သော အဆို
- ကိန်းဂဏန်း ဒါမှမဟုတ် အတိအကျ အချက်အလက် ပါသော စာကြောင်း
- English စကားလုံး အရေးကြီးသည် ပါသော စာကြောင်း
- နာမည် · နေရာ · စကားလုံးအသစ် မိတ်ဆက်သော စာကြောင်း

စည်းကမ်း:
- အများဆုံး %d ကြောင်း
- ဆက်တိုက် စာကြောင်းများကို မရွေးပါနှင့် — ဗီဒီယိုတစ်လျှောက် ဖြန့်ပါ
- သာမန် ဆက်စပ်စကား · နှုတ်ခွန်းဆက် · "အဲဒါကြောင့်" စတဲ့ အဆက်စကား မရွေးရ
- JSON array ကိုသာ ပြန်ပါ

ပုံစံ: [{"line": 3, "why": "အဓိက အချက်"}, ...]

စာတမ်း:
%s"""

def emphasis(segs, want=8, log=print):
    """စာတန်း တင်ထိုက်သော စာကြောင်း index စာရင်း。

    ⚠️ Gemini ပြန်ပေးသော index ကို **ရှိမရှိ စစ်ရမည်** — ဖန်လာလျှင်
       မဆိုင်တဲ့ စာကြောင်းပေါ် စာတင်မိမည်。
    ⚠️ Gemini မရလျှင် **အလွတ် မပြန်ရ** — အလွတ်ပြန်လျှင် စာတန်း လုံးဝ
       မပါဘဲ ထွက်သွားမည်。 ⇒ အညီအမျှ ဖြန့်ပြီး ရွေးသည် (fallback)。
    """
    if not segs or want <= 0: return []
    lines = "\n".join(f"{i+1}. {s['text']}" for i, s in enumerate(segs[:120]))
    body = {"contents": [{"parts": [{"text": EMPH % (want, lines)}]}],
            "generationConfig": {"temperature": 0.2}}
    for i in range(2):
        G.throttle()
        r = urllib.request.Request(G.endpoint(MODEL), data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
            m = re.search(r"\[.*\]", txt, re.S)
            if not m:
                G.log_fail("emphasis", i + 1, 2, None, "JSON မတွေ့", final=True); break
            out = []
            bad = 0
            for x in json.loads(m.group(0)):
                n = int(x.get("line", 0)) - 1
                if 0 <= n < len(segs): out.append(n)
                else: bad += 1
            out = sorted(set(out))[:want]
            if bad: log(f"  စာတန်း · Gemini index မှား {bad} ခု ဖြုတ်ပြီး")
            if out:
                log(f"  စာတန်း · အလေးထား {len(out)} / {len(segs)} ကြောင်း ရွေးပြီး")
                return out
            break
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            G.log_fail("emphasis", i + 1, 2, e.code, raw, final=G.fatal(e.code, raw) or i == 1)
            if G.fatal(e.code, raw): break
            mm = re.search(r'"retryDelay"\s*:\s*"(\d+)s"', raw)
            time.sleep(int(mm.group(1)) if mm else 6 * (i + 1))
        except Exception as e:
            G.log_fail("emphasis", i + 1, 2, None, f"{type(e).__name__}: {e}", final=(i == 1))
            time.sleep(4 * (i + 1))
    # fallback — အညီအမျှ ဖြန့်
    step = max(1, len(segs) // max(1, want))
    out = list(range(0, len(segs), step))[:want]
    log(f"  စာတန်း · အညီအမျှ {len(out)} ကြောင်း (Gemini မရ)")
    return out


# == keyword colour inside a caption line (short-916) ==================
# Refs (4 shorts, 2026-09-26): one word or short phrase inside the caption
# line is recoloured (red / green / yellow), roughly one caption in three.
# Gemini picks it; every pick must be an EXACT substring of that caption,
# otherwise the colour would land on the wrong glyphs -> dropped.
KW_PROMPT = """အောက်တွင် မြန်မာဗီဒီယိုတစ်ခု၏ စာတန်းစာကြောင်းများကို နံပါတ်နှင့် ပေးထားသည်။

စာတန်းထဲမှ **အဓိကစကားလုံး** ကို အရောင်ပြောင်းပြီး အလေးပေးပြမည်။
ဘယ်စာကြောင်း၏ ဘယ်စကားလုံးကို အရောင်ပြောင်းမလဲ ရွေးပေးပါ။

စည်းကမ်း:
- စာကြောင်း %d ကြောင်းအထိသာ ရွေးပါ၊ ဗီဒီယိုတစ်လျှောက် ဖြန့်ပါ
- စာကြောင်းတစ်ကြောင်းလျှင် စကားလုံး/စကားစု **တစ်ခုတည်း**
- ကိန်းဂဏန်း · နာမည် · နေရာ · English အရေးကြီးစကားလုံး · အဓိပ္ပာယ်အဓိက စကားလုံး
- "word" သည် ထိုစာကြောင်းထဲမှ **စာလုံးပေါင်း အတိအကျ ကူးယူ**ထားရမည် (မပြင်ရ)
- အက္ခရာ ၂ လုံးမှ ၁၄ လုံးအထိ၊ ဆက်စပ်စကား ("ပြီးတော့" · "အဲဒါ") မရွေးရ
- JSON array ကိုသာ ပြန်ပါ: [{"line": 3, "word": "..."}]

စာကြောင်းများ:
%s"""

_KW_RX = re.compile(r"[0-9\u1040-\u1049][0-9\u1040-\u1049,.%]*|[A-Za-z][A-Za-z0-9'+-]{2,}")

def _kw_fallback(caps, want):
    """numbers and Latin terms -- the refs colour those most often"""
    out = {}
    for i, c in enumerate(caps):
        m = _KW_RX.search(c.get("text") or "")
        if m: out[i] = [m.group(0)]
        if len(out) >= want: break
    return out

def keywords(caps, share=0.33, log=print):
    """{caption index: [exact substring, ...]} -- at most `share` of captions"""
    if not caps or share <= 0: return {}
    want = max(1, int(round(len(caps) * share)))
    lines = "\n".join(f"{i+1}. {c['text']}" for i, c in enumerate(caps[:160]))
    body = {"contents": [{"parts": [{"text": KW_PROMPT % (want, lines)}]}],
            "generationConfig": {"temperature": 0.2}}
    for i in range(2):
        G.throttle()
        r = urllib.request.Request(G.endpoint(MODEL), data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
            m = re.search(r"\[.*\]", txt, re.S)
            if not m:
                G.log_fail("keywords", i + 1, 2, None, "no JSON", final=True); break
            out, bad = {}, 0
            for x in json.loads(m.group(0)):
                try: n = int(x.get("line", 0)) - 1
                except (TypeError, ValueError): bad += 1; continue
                w = str(x.get("word") or "").strip()
                if not (0 <= n < len(caps)) or len(w) < 2 or len(w) > 24 \
                        or w not in caps[n]["text"] or w == caps[n]["text"].strip():
                    bad += 1; continue
                out.setdefault(n, [w])
                if len(out) >= want: break
            G.tally("keywords", True)
            log(f"  keyword colour · {len(out)}/{len(caps)} captions"
                + (f" · {bad} rejected (not an exact substring)" if bad else ""))
            if out: return out
            break
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            G.log_fail("keywords", i + 1, 2, e.code, raw, final=G.fatal(e.code, raw) or i == 1)
            if G.fatal(e.code, raw): break
            time.sleep(6 * (i + 1))
        except Exception as e:
            G.log_fail("keywords", i + 1, 2, None, f"{type(e).__name__}: {e}", final=(i == 1))
            time.sleep(4 * (i + 1))
    out = _kw_fallback(caps, want)
    log(f"  keyword colour · fallback (numbers/Latin) {len(out)} captions")
    return out


# ══ full-frame slide အတွက် အကြောင်းအရာ ═══════════════════════
# ⚠️ `ask()` က **စာလုံး ၂–၅ လုံး** ခေါင်းစဉ်တိုလေးတွေ ပြန်ပေးသည် —
#    lower-third အသေးလေးအတွက် လုံလောက်ပေမယ့် **full-frame slide အတွက်
#    လုံးဝ မလုံလောက်**。 slide တစ်ခုမှာ ခေါင်းစဉ် + အချက် ၂–၃ ခု
#    ရှိမှ ကြည့်လို့ ကောင်းသည် (reference ကို တိုင်းထားသည်)。
SLIDE_PROMPT = """အောက်တွင် မြန်မာဗီဒီယိုတစ်ခု၏ စာတမ်းကို စာကြောင်းနံပါတ်နှင့် ပေးထားသည်။

ဤဗီဒီယိုအတွက် **မျက်နှာပြင် အပြည့် ပြမည့် slide** များ ရေးပေးပါ။
ကြည့်သူက ဗီဒီယိုကြားထဲ ဒီ slide ကို မြင်ပြီး အဓိကအချက်ကို မှတ်မိစေရမည်။

layout ၃ မျိုး ရှိသည် —
- "bullets"   : ခေါင်းစဉ် + အချက် ၂–၃ ခု (အသုံးအများဆုံး)
- "statement" : အဓိက စကားတစ်ခွန်း (မှတ်သားဖွယ် အကောင်းဆုံး တစ်ခွန်း)
- "bignum"    : ကိန်းဂဏန်း တစ်ခု + ရှင်းလင်းချက်တို (ကိန်း တကယ် ပြောမှသာ)

စည်းကမ်း:
- **%d ခု ရေးပါ** — ဒီထက် မများရ။ တိုင်းထားသော အချိုး (၁၀ မိနစ်လျှင် ၁၁.၆ ခု)
- ⚠️ **တစ်ပြေးညီ မခွဲရ**。 reference ၂ ခုကို တိုင်းကြည့်ရာ slide တွေက
  **အစုလိုက်** လာသည် — အဓိကအချက် ရှင်းပြတဲ့နေရာမှာ ၂–၃ ခု ဆက်တိုက်၊
  ပြီးရင် **၄၀–၁၂၀ စက္ကန့်လောက် လုံးဝ မပါဘဲ** စကားပဲ ပြောသွားသည်။
  ⇒ အကြောင်းအရာ တကယ် လိုတဲ့နေရာမှာသာ ထားပါ။ နေရာလွတ် ဖြည့်ဖို့ မလုပ်ရ
- ဇာတ်လမ်း ပြောနေတဲ့ အပိုင်း · ခံစားချက် ပြောတဲ့ အပိုင်းမှာ slide **မထားရ**
- စာရင်း · အဆင့်ဆင့် · ကိန်းဂဏန်း ပြောတဲ့နေရာမှာသာ ထားပါ
- `line` က အဲဒီအကြောင်းအရာ **စပြောတဲ့ စာကြောင်း** ဖြစ်ရမည်
- ခေါင်းစဉ် — **အဓိပ္ပာယ် ပြည့်စုံသော စကားစု** ဖြစ်ရမည်။ မြန်မာ ၃–၉ လုံး
- အချက်တစ်ခု — မြန်မာ ၄–၁၀ လုံး။ **စာကြောင်း မပြတ်စေရ** — "…ကျန်ခဲ" ·
  "…လျှောက်လာပ" လို အလယ်ဖြတ်ထားတာမျိုး လုံးဝ မရေးရ
- ခေါင်းစဉ်ရော အချက်ရော **ဝါကျတစ်ခု ပြီးအောင်** ရေးပါ
- **စာတမ်းထဲ ရှိသော အကြောင်းအရာကိုသာ** ရေးရမည်။ မရှိတာ လုံးဝ မဖန်းရ
- စာကြောင်းကို ကူးချရန် မလို — အဓိကအချက်ကို **ကိုယ်ပိုင်စကားနဲ့ တိုတိုရှင်းရှင်း**
- JSON array ကိုသာ ပြန်ပါ

ပုံစံ:
[{"line":12,"layout":"bullets","head":"ပိုက်ဆံ စုဖို့ နည်း ၃ ခု",
  "items":["နေ့စဉ် ကုန်ကျစရိတ် မှတ်ပါ","ဝင်ငွေ ၂၀%% အရင် ခွဲပါ"]},
 {"line":40,"layout":"statement","head":"အရင်ဆုံး ကိုယ့်ကိုယ်ကို ရင်းနှီးမြှုပ်နှံပါ"},
 {"line":77,"layout":"bignum","num":"၃ နှစ်","head":"ပျမ်းမျှ ကြာချိန်"}]

စာတမ်း:
%s"""


def slides(segs, want=10, log=print):
    """[{at, layout, head, items, num}] — full-frame slide အတွက်。"""
    if not segs: return []
    if len(segs) > CAP:
        step = len(segs) / float(CAP)
        idx = sorted({min(len(segs) - 1, int(i * step)) for i in range(CAP)})
    else:
        idx = list(range(len(segs)))
    view = [segs[i] for i in idx]
    lines = "\n".join(f"{i+1}. {s['text']}" for i, s in enumerate(view))
    body = {"contents": [{"parts": [{"text": SLIDE_PROMPT % (want, lines)}]}],
            "generationConfig": {"temperature": 0.3}}
    for i in range(3):
        G.throttle()
        r = urllib.request.Request(G.endpoint(MODEL), data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
            m = re.search(r"\[.*\]", txt, re.S)
            if not m:
                G.log_fail("slides", i + 1, 3, None, "JSON မတွေ့", final=True); return []
            out = []
            for x in json.loads(m.group(0)):
                n = int(x.get("line", 0)) - 1
                if not (0 <= n < len(view)): continue
                lay = str(x.get("layout") or "bullets")
                if lay not in ("bullets", "statement", "bignum"): lay = "bullets"
                head = str(x.get("head") or "").strip()[:72]
                if not head: continue
                items = [str(t).strip()[:84] for t in (x.get("items") or [])
                         if str(t).strip()][:3]
                if lay == "bullets" and not items: lay = "statement"
                g = idx[n]
                out.append(dict(at=segs[g]["start"], layout=lay, head=head,
                                items=items, num=str(x.get("num") or "").strip()[:12],
                                line=g))
            out.sort(key=lambda z: z["at"])
            G.tally("slides", True)
            log(f"  slide {len(out)} ခု ရွေးပြီး · "
                + " · ".join(f"{s['layout']}" for s in out[:5]))
            return out
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            G.log_fail("slides", i + 1, 3, e.code, raw, final=G.fatal(e.code, raw))
            if G.fatal(e.code, raw): return []
            mm = re.search(r'"retryDelay"\s*:\s*"(\d+)s"', raw)
            G.tally("slides", False, f"HTTP {e.code}")
            log(f"  … slides() HTTP {e.code} ({i+1}/3) — ပြန်ကြိုးစားမည်")
            time.sleep(int(mm.group(1)) if mm else 6 * (i + 1))
        except Exception as e:
            # ⚠️ အရင်က log မရေးဘဲ ကျော်ခဲ့သဖြင့် slide ၀ ခု ဖြစ်ရခြင်း
            #    အကြောင်းရင်းကို **လုံးဝ မမြင်ရ**ခဲ့。
            G.tally("slides", False, f"{type(e).__name__}: {e}")
            G.log_fail("slides", i + 1, 3, None, f"{type(e).__name__}: {e}")
            log(f"  … slides() ကျသည် ({i+1}/3): {type(e).__name__}: {e}")
            time.sleep(5 * (i + 1))
    G.log_fail("slides", 3, 3, None, "retry ကုန် — [] ပြန်", final=True)
    log("  ✖ slides() ၃ ကြိမ်လုံး ကျသည် — slide ၀ ခု ပြန်သည်")
    return []
