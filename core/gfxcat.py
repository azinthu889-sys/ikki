#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · motionkit ရဲ့ template catalog ကို App နှင့် ချိတ်ခြင်း。

⚠️ App က template **၁၂ ခု**ကို hardcode လုပ်ပြီး အလှည့်ကျ သုံးနေခဲ့သည် —
   motionkit မှာ **၂၇၆ ခု** ရှိပါလျက်。 ဒါက ထုတ်လာတဲ့ ဗီဒီယိုကို တစ်ပုံစံတည်း
   ဖြစ်စေသည်。

⚠️ argument ကို **လက်နဲ့ မရေးရ** — catalog က `inspect.signature()` ဖြင့်
   ကုဒ်မှ တိုက်ရိုက် ထုတ်ပေးသည်。 လက်နဲ့ရေးလျှင် builder ပြောင်းတိုင်း
   ဟောင်းသွားပြီး တိတ်တဆိတ် မှားမည်。

⚠️ အမျိုးအစားတိုင်း overlay အဖြစ် မသုံးရ —
   transition က ဖန်သားပြင်တစ်ခုလုံး ဖုံးသည် (A-roll ပျောက်မည်) ·
   mockup က ပြင်ပ ဓာတ်ပုံ လိုသည် · motion က နောက်ခံ element。
"""
import os, sys, json

MK = os.environ.get("IKKI_MOTIONKIT",
      "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")

# overlay အဖြစ် သုံးလို့ရသော အမျိုးအစား
# ⚠️ **အမျိုးအစား အသစ် ထည့်လျှင် ဒီမှာပါ ထည့်ရမည်**。 ၂၀၂၆-၀၉-၂၀:
#    `insert` module ကို catalog မှာ မှတ်ပုံတင်ပြီးသော်လည်း `explainer` က
#    ဒီစာရင်းထဲ မပါ၍ `usable()` က ဖယ်ပစ်ကာ IKKI ဆီ **လုံးဝ မရောက်**ခဲ့。
# ⚠️ ၂၀၂၆-၀၉-၂၂ — `thm` pack က `ui` အမျိုးအစား အသစ် ယူလာသည် (generic
#    browser/phone chrome · ပြင်ပ ပုံ **မလို**)。 ဒီစာရင်းထဲ မထည့်လျှင်
#    `usable()` က ဖယ်ပစ်ကာ ၁၂ ခုလုံး IKKI ဆီ မရောက် — `explainer` နဲ့
#    အတိအကျ တူသော အမှား ထပ်ဖြစ်မည်。
USE = ("title", "infographic", "callout", "typography", "text", "chart",
       "explainer", "ui")

_CAT = None
LAST_ERR = [None]      # catalog() ကျခဲ့လျှင် အကြောင်းရင်း — report အတွက်

def catalog():
    """[{id, module, fn, category, label, params}] — cache လုပ်ထားသည်"""
    global _CAT
    if _CAT is not None: return _CAT
    cwd = os.getcwd()
    try:
        if MK not in sys.path: sys.path.insert(0, MK)
        os.chdir(MK)
        import catalog as C
        _CAT = C.build()
    except Exception as e:
        # ⚠️ **ဒါက အရေးအကြီးဆုံး ကျမှု**。 catalog ဗလာ ဖြစ်လျှင် card တိုင်း
        #    `dress.py:209` မှာ "template မတွေ့" နဲ့ ကျသည် — ဂရပ်ဖစ် လုံးဝ
        #    မပါတော့。 အရင်က log မရေးဘဲ ကျော်ခဲ့သဖြင့် ဘာဖြစ်မှန်း မသိရ。
        LAST_ERR[0] = f"{type(e).__name__}: {e}"
        print(f"  ✖ motionkit catalog ဖတ်မရ: {LAST_ERR[0]}", flush=True)
        print(f"     → MK={MK} · card အားလုံး template မတွေ့ဘဲ ကျမည်", flush=True)
        _CAT = []
    finally:
        try: os.chdir(cwd)
        except Exception: pass
    return _CAT

def usable(categories=USE):
    return [e for e in catalog() if e.get("category") in categories]


# ── edit style ⇄ template ─────────────────────────────────────
# ⚠️ မြေပုံကို **motionkit ထဲက `stylemap.py`** မှာသာ ထားသည် — gallery ရော
#    IKKI ရော ဤတစ်ခုတည်းကို ဖတ်ရမည်。 နှစ်နေရာ ရေးလျှင် တစ်ဖက် ကျန်ခဲ့မည်。
_SM = None


def _stylemap():
    global _SM
    if _SM is not None: return _SM
    cwd = os.getcwd()
    try:
        if MK not in sys.path: sys.path.insert(0, MK)
        os.chdir(MK)
        import stylemap as SM
        _SM = SM
    except Exception as e:
        print(f"  ✖ stylemap ဖတ်မရ: {type(e).__name__}: {e}", flush=True)
        _SM = None
    finally:
        try: os.chdir(cwd)
        except Exception: pass
    return _SM


def styles():
    """[(key, နာမည်, ရှင်းလင်းချက်, အုပ်စု)] — IKKI ရဲ့ UI အတွက်。"""
    sm = _stylemap()
    return list(sm.STYLES) if sm else []


def by_style(style, categories=USE):
    """edit style တစ်ခုအတွက် သုံးနိုင်သော template များ。

    ⚠️ style မသိလျှင် **ဗလာ မပြန်ရ** — ဂရပ်ဖစ် လုံးဝ ပျောက်မည်。
       ⇒ `usable()` အပြည့် ပြန်ပေးပြီး အကြောင်း ပြောသည်。
    """
    sm = _stylemap()
    pool = usable(categories)
    if not sm or style not in getattr(sm, "MAP", {}):
        if style: print(f"  ⚠ style မသိ: {style} — template အားလုံး သုံးမည်", flush=True)
        return pool
    mods = set(sm.MAP[style])
    return [e for e in pool if e["module"] in mods]


def role_of(entry):
    """overlay | cut | fullbleed — ဘယ်နေရာမှာ သုံးရမလဲ。"""
    sm = _stylemap()
    return sm.role_of(entry) if sm else "overlay"


# ── စာရင်း (list) argument ─────────────────────────────────
# ⚠️ template ၁၀၂ ခု (charts · infogfx · maps · dash · capt …) က ပထမ param
#    အဖြစ် **စာရင်း** ယူသည် — `rows` · `lines` · `items` · `words` · `vals`。
#    `fill()` က မဆောက်တတ်၍ 「fill ဗလာ」 သို့မဟုတ် 「too many values to
#    unpack」 ဖြင့် ကျခဲ့သည် (၂၀၂၆-၀၉-၁၉ တိုင်းချက်)。
# ⚠️ ပုံစံက template တစ်ခုချင်း မတူ ⇒ **မှန်းဆ၍ မရ**。 `tools/gfx_args.py` က
#    တစ်ခုချင်း တကယ် render ပြီး အလုပ်ဖြစ်တဲ့ ပုံစံကို `assets/gfx_args.json`
#    ထဲ မှတ်ထားသည် — ဤမှာ အဲဒါကို ဖတ်ရုံသာ。
SHAPES = {
    "pair":  [("ဂျပန်မှာ အလုပ်", 62), ("ပညာသင်", 41), ("ဗီဇာ", 27)],
    "text":  ["ဂျပန်မှာ အလုပ်", "ပညာသင်", "ဗီဇာ"],
    "num":   [62, 41, 27],
    "dict":  [{"label": "ဂျပန်မှာ အလုပ်", "value": 62},
              {"label": "ပညာသင်", "value": 41},
              {"label": "ဗီဇာ", "value": 27}],
    "trip":  [("ဂျပန်မှာ အလုပ်", "ZAE", 62), ("ပညာသင်", "ZAE", 41),
              ("ဗီဇာ", "ZAE", 27)],
}
_ARGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "assets", "gfx_args.json")
_SHAPE_OF = None

def shape_of(tid):
    """template id → စာရင်း ပုံစံ နာမည် (မသိလျှင် None)"""
    global _SHAPE_OF
    if _SHAPE_OF is None:
        try: _SHAPE_OF = json.load(open(_ARGS_PATH, encoding="utf-8"))
        except Exception: _SHAPE_OF = {}
    return _SHAPE_OF.get(tid)

# ── argument ဖြည့်ခြင်း ──────────────────────────────────────
# အကြောင်းအရာ ကိန်း — နာမည်အလိုက် သင့်တော်သော တန်ဖိုး
NUMFILL = {"start": 3, "count": 6, "secs": 10, "sec": 10,
           "h": 0, "m": 1, "s": 30, "n": 3, "steps": 3, "total": 100}


def fill(entry, text, sub="", pct=None, shape=None):
    """template တစ်ခုအတွက် positional argument tuple。

    ⚠️ **စာသား param ကိုသာ ဖြည့်ရမည်**。 size · fill · y · x · maxtrack
       စတာတွေက `None` ပုံသေနှင့် ထားပြီး template က theme ကနေ ကိုယ်တိုင်
       တွက်သည် (ဥပမာ `size = int(BAND()*0.14)`)。 ကိန်း ထည့်ပေးလျှင်
       house style ပျက်ပြီး `can't multiply sequence by non-int` လို
       အမှားများ ဖြစ်သည် (kern_wide · vertical_jp — တကယ် ဖြစ်ခဲ့)。
    ⚠️ `dur` ကို မထည့်ရ — worker က သီးသန့် ပေးသည်。
    ⚠️ `tag` ကိုလည်း **မထည့်ရ** — `dress.track()` က `f"g{i}"` ဖြင့် ကိုယ်တိုင်
       ရှေ့က ထည့်သည်。 ဒီမှာလည်း ထည့်လျှင် argument တစ်နေရာစီ ရွေ့ပြီး
       စာသားက `size` ထဲ ကျသည် → `can't multiply sequence by non-int`
       (kern_wide · sweep · typewriter · vertical_jp — တကယ် ဖြစ်ခဲ့၊
       "ရွေး ၈ ခု · တပ်ပြီး ၄ ခု" ဆိုပြီး တိတ်တဆိတ် ကျသွားခဲ့သည်)。
    """
    texts = [t for t in (text, sub) if t] or [text or "—"]
    LISTY = ("msgs", "results", "tabs",
             "levels", "stages", "rows", "items", "lines", "bullets",
             "steps", "points", "cols", "labels", "values", "data")
    args = []
    ti = 0
    for p in entry.get("params", []):
        nm, ty, req = p.get("name"), p.get("type"), p.get("required")
        # ⚠️ `auto` param (size · y · fill · maxtrack …) ကို **မထည့်ရ** —
        #    template က theme ကနေ ကိုယ်တိုင် တွက်သည်。
        # ⚠️ ပိုအရေးကြီးသည်က — positional tuple ဖြစ်၍ **အလယ်က param ကို
        #    ကျော်ပြီး နောက်ဆုံးဟာကို မထည့်ရ**。 ကျော်လျှင် argument
        #    တစ်နေရာစီ ရွေ့ပြီး စာသားက `size` ထဲ ကျသည်。 (kern_wide ရဲ့
        #    `maxtrack` က type "text" ဖြစ်နေ၍ ဘရန်းနာမည် ဝင်သွားခဲ့သည် —
        #    "can't multiply sequence by non-int" · တကယ် ဖြစ်ခဲ့)。
        #    ⇒ ဖြည့်လို့မရတဲ့ param တွေ့သည်နှင့် **ရပ်**ရမည်。
        if nm == "dur" or p.get("auto"):
            break
        # ⚠️ **စာရင်း param** — ပုံစံကို `assets/gfx_args.json` မှ ယူသည်
        if ty == "list" or (ty == "text" and nm in LISTY):
            sh = shape or shape_of(entry.get("id"))
            if not sh:
                if ty == "list": break          # ပုံစံ မသိ ⇒ မဖြည့်ရ
                args.append([texts[0], sub or "—", "—"]); continue
            args.append(list(SHAPES.get(sh) or SHAPES["text"])); continue
        if ty == "text":
            if nm in LISTY:
                args.append([texts[0], sub or "—", "—"])
            else:
                args.append(texts[ti] if ti < len(texts) else "")
                ti += 1
            continue
        if req and p.get("default") is not None:
            args.append(p["default"])
            continue
        # ⚠️ `required=false` ဖြစ်ပြီး **default ရှိ**သော `auto` မဟုတ်သော param —
        #    default ကို ထည့်လိုက်ခြင်းက မထည့်တာနဲ့ **အတူတူ**ပါပဲ (positional)。
        #    မထည့်ဘဲ `break` လုပ်လျှင် နောက်က param တွေ မရောက်တော့ဘဲ args ဗလာ
        #    ဖြစ်ကာ template က IKKI ဆီ မရောက် (countdown · odo.timer — တကယ်)。
        if not p.get("auto") and p.get("default") is not None:
            args.append(p["default"])
            continue
        if req and ty == "number" and pct is not None:
            args.append(pct)
            continue
        # ⚠️ **အကြောင်းအရာ ကိန်း** (start · h · m · s · secs · count) က `auto` မဟုတ်、
        #    house style နဲ့ မဆိုင် — ဖြည့်လို့ ရသည်。 မဖြည့်လျှင် `fill()` က None
        #    ပြန်ပြီး template က IKKI ဆီ **လုံးဝ မရောက်** (countdown · odo.timer
        #    · typo2.orbit_dots — တိုင်းပြီး ၅ ခု)。
        #    `auto` ကိန်း (size · y · fill · maxtrack) ကိုတော့ အပေါ်မှာ ရပ်ပြီးသား。
        if req and ty in ("int", "number"):
            args.append(NUMFILL.get(nm, pct if pct is not None else 3))
            continue
        break
    # ⚠️ နောက်ဆုံး **ဗလာစာသား**တွေ ဖြုတ်တာက `optional` param အတွက်သာ ဖြစ်ရမည်。
    #    required param ကို ဖြုတ်မိလျှင် template က
    #    `missing N required positional arguments` နဲ့ ကျသည် — စာသား param
    #    ၃ ခုအထက် လိုသော template တိုင်း (`text` + `sub` = ၂ ခုသာ ရှိ)。
    #    ၂၀၂၆-၀၉-၂၂ တိုင်းချက်: thm.cmp_frame · cmp_glass · cmp_meter ·
    #    cmp_price · cmp_win_a · cmp_win_b · stat_note · hook_count ၈ ခု
    #    ဒီအတိုင်း တိတ်တဆိတ် ကျခဲ့သည်。
    _ps = entry.get("params") or []
    _nreq = 0
    for _i, _p in enumerate(_ps[:len(args)]):
        if _p.get("required"): _nreq = _i + 1
    while len(args) > _nreq and args and args[-1] == "":
        args.pop()
    if args: return tuple(args)
    # ⚠️ ပထမ param ကိုက် `dur`/`auto` ဆိုလျှင် **positional argument မလိုပါ** —
    #    `None` ပြန်လျှင် ခေါ်သူက "မရ" ဟု ယူပြီး template ကို ပစ်ပယ်သည်
    #    (motionfx · typo2.orbit_dots လို ၃ ခု — တကယ်)。 ⇒ `()` ပြန်ရမည်。
    ps = entry.get("params") or []
    if ps and (ps[0].get("name") == "dur" or ps[0].get("auto")):
        return ()
    return None


def call(entry, args, dur):
    """template ကို တကယ် ခေါ်သည် — PNG စာရင်း ပြန်ပေးသည်"""
    cwd = os.getcwd()
    try:
        if MK not in sys.path: sys.path.insert(0, MK)
        os.chdir(MK)
        import importlib
        m = importlib.import_module(entry["module"])
        fn = getattr(m, entry["fn"])
        kw = {}
        if any(p.get("name") == "dur" for p in entry.get("params", [])):
            kw["dur"] = dur
        return fn(*args, **kw)
    finally:
        try: os.chdir(cwd)
        except Exception: pass


# ══ motionkit work/ ရှင်းလင်းချက် ═══════════════════════════════════
# ⚠️ template တစ်ခု ဆောက်တိုင်း PNG ၆၀–၂၀၀ ထွက်ပြီး `motionkit/work/<sub>`
#    ထဲ **ကျန်ခဲ့**သည် — ဘယ်သူမှ မဖျက်ပါ。 ၂၀၂၆-၀၉-၂၁ မှာ **၁၁ GB**
#    စုမိပြီး Mac ရဲ့ disk ပြည့်သွားကာ render တွေ ကျခဲ့သည်
#    (`prem` ဖိုလ်ဒါ တစ်ခုတည်းက ၈.၁ GB)。
# ⚠️ IKKI ရဲ့ scratch leak နဲ့ **အတူတူ ပြဿနာ** — တစ်ခါ ဖျက်ရုံနဲ့ မလုံလောက်、
#    ပြန်စုမိမည် ⇒ render စတိုင်း အလိုအလျောက် ရှင်းရမည်。
# ⚠️ **ယခု ပြေးနေသော render ကို မဖျက်မိစေရန်** — သတ်မှတ်ချိန်ထက်
#    အသစ်သော ဖိုလ်ဒါကို မထိပါ。
WORK_MAX_GB = 2.0
WORK_AGE_H = 6.0


def _dsize(d):
    n = 0
    for dp, _dn, fn in os.walk(d):
        for f in fn:
            try:
                n += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return n


def gc_work(max_gb=WORK_MAX_GB, age_h=WORK_AGE_H, log=None):
    """motionkit ရဲ့ `work/` ကို ရှင်းသည် — `(ဖျက်ပြီး ဖိုလ်ဒါ, ပြန်ရ bytes)`

    ၁။ `age_h` ထက် ဟောင်းသော ဖိုလ်ဒါ — အကုန် ဖျက်
    ၂။ ကျန်တာက `max_gb` ကျော်နေလျှင် — **အဟောင်းဆုံးကနေ** ဖျက်
    """
    import shutil
    import time
    root = os.path.join(MK, "work")
    if not os.path.isdir(root):
        return 0, 0
    now = time.time()
    subs = []
    for nm in os.listdir(root):
        p = os.path.join(root, nm)
        if not os.path.isdir(p):
            continue
        try:
            subs.append([p, os.path.getmtime(p), _dsize(p)])
        except OSError:
            pass
    killed = freed = 0
    keep = []
    for p, mt, sz in subs:
        if (now - mt) / 3600.0 > age_h:
            try:
                shutil.rmtree(p); killed += 1; freed += sz
            except OSError:
                keep.append([p, mt, sz])
        else:
            keep.append([p, mt, sz])
    keep.sort(key=lambda x: x[1])                 # အဟောင်းဆုံး ရှေ့
    left = sum(x[2] for x in keep)
    cap = max_gb * (1 << 30)
    for p, _mt, sz in keep:
        if left <= cap:
            break
        try:
            shutil.rmtree(p); killed += 1; freed += sz; left -= sz
        except OSError:
            pass
    if log and killed:
        log(f"  motionkit work/ ရှင်း · ဖိုလ်ဒါ {killed} ခု · "
            f"{freed/(1<<30):.2f} GB ပြန်ရ")
    return killed, freed
