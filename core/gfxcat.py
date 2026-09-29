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
import os, re, sys, json

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
# ⚠️ `cutaway` က overlay မဟုတ် — ဘောင်အပြည့် ဖုံးသည်。 pool ထဲ ထည့်ရမည်
#    (မထည့်လျှင် ရောက်မလာ) ဒါပေမယ့် ခေါ်သူက `role` ကို ကြည့်ပြီး
#    ဖြတ်ပြောင်း လမ်းကြောင်းသို့ ပို့ရမည် — overlay အဖြစ် သုံးလျှင်
#    ပြောသူ လုံးဝ ပျောက်မည်。
USE = ("title", "infographic", "callout", "typography", "text", "chart",
       "explainer", "ui", "cutaway", "board")

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
# ⚠️ ပုံ/ရုပ် လမ်းကြောင်း ယူသော param — `argshape` နဲ့ တစ်ထပ်တည်း ထားရမည်。
IMG_NAMES = {"img", "imgs", "image", "images", "img1", "img2", "img_a", "img_b",
             "img_path", "base", "logo", "logos", "photo", "photos", "pic",
             "thumb", "avatar", "src", "frame", "shot"}

SHAPES = {
    "pair":  [("ဂျပန်မှာ အလုပ်", 62), ("ပညာသင်", 41), ("ဗီဇာ", 27)],
    # ⚠️ **`(စာသား, စာသား)` ပုံစံ ကျန်ခဲ့သည်**။ `pair` က (str, int) ဖြစ်၍
    #    `titles3.schedule_row` လို (အချိန်, ခေါင်းစဉ်) ယူသော template မှာ
    #    `fit(sub, …)` က int နဲ့ ကျသည် ⇒ learner က ကျော်ပြီး **`dict`** ကို
    #    ရွေးမိသည်။ ဒါပေမယ့် 2-key dict ကို `(a, b)` အဖြစ် ဖြေလျှင်
    #    **key နာမည်** ရသည် ⇒ template က 「label」「value」ဆိုသော စာလုံးကို
    #    ထုတ်ပြနေခြင်း — အမှား မတက်သဖြင့် learner က အောင်ဟု မှတ်ခဲ့သည်။
    #    ၂၀၂၆-၀၉-၂၅: `dict` ရွေးထားသူ ၉ ခုလုံး key-index **မလုပ်** ⇒ ၉ ခုလုံး မှား။
    "pair2": [("၉:၀၀", "ဂျပန်မှာ အလုပ်"), ("၁၀:၃၀", "ပညာသင်"),
              ("၁၃:၀၀", "ဗီဇာ")],
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


def fill(entry, text, sub="", pct=None, shape=None, img=None,
         items=None, nums=None):
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
        # ⚠️⚠️ **`SHAPES` ကို အကြောင်းအရာ အဖြစ် သုံး၍ လုံးဝ မရ**。 အရင်က
        #    `SHAPES[sh]` ကို တိုက်ရိုက် ထည့်ခဲ့သည် — ဆိုလိုတာက စာရင်း param
        #    ယူသော template **၅၂ ခု**က အသုံးပြုသူရဲ့ script ဘာဖြစ်ဖြစ်
        #    「ဂျပန်မှာ အလုပ် ၆၂ · ပညာသင် ၄၁ · ဗီဇာ ၂၇」ဆိုတဲ့ **နမူနာစာ
        #    အတိအကျ**ကို ထုတ်ပြနေခြင်း ဖြစ်သည် ⇒ ဗီဒီယိုထဲ **မရှိသော
        #    အချက်အလက်** တင်လိုက်တာ။ ဂိတ်③ က ဒါကို ဖမ်းမိသည် —
        #    `thm.cmp_*` ၁၁ ခု diff = **0.000** (စာသား ပြောင်းလည်း ပုံ မပြောင်း ·
        #    ၂၀၂၆-၀၉-၂၅)。 ဂိတ်က မှန်၊ `fill()` က မှား。
        # ⇒ `SHAPES` က **ပုံစံ** (တည်ဆောက်ပုံ) သာ ဖြစ်ရမည်; အကြောင်းအရာက
        #    ခေါ်သူ ပေးသော `items`/`texts`/`nums` ကနေသာ လာရမည်။ မပေးလျှင်
        #    **`None` ပြန်** (ဖြည့်မရ) — `tmplfit`/`argshape` လမ်းကြောင်းက
        #    အကြောင်းအရာ အစစ်နဲ့ ဖြည့်ပေးမည်။
        if ty == "list" or (ty == "text" and nm in LISTY):
            sh = shape or shape_of(entry.get("id")) or "text"
            src = [str(x) for x in (items or []) if str(x).strip()]
            if not src:
                src = [t for t in texts if t]
            if not src:
                return None
            _n = list(nums or [])
            if pct is not None and not _n:
                _n = [pct]

            def _num(k):
                if _n: return _n[k % len(_n)]
                return None

            if sh == "text":
                val = src
            elif sh == "num":
                if not _n: return None          # ကိန်း မတီထွင်ရ
                val = [_num(k) for k in range(len(src))]
            elif sh == "pair":
                if not _n: return None
                val = [(s, _num(k)) for k, s in enumerate(src)]
            elif sh == "pair2":
                val = [(s, str(sub or texts[0])) for s in src] if len(src) < 2 else \
                      [(src[k], src[(k + 1) % len(src)]) for k in range(len(src))]
            elif sh == "trip":
                if not _n: return None
                val = [(s, str(sub or "—"), _num(k)) for k, s in enumerate(src)]
            elif sh == "dict":
                if not _n: return None
                val = [{"label": s, "value": _num(k)} for k, s in enumerate(src)]
            else:
                val = src
            args.append(list(val)); continue
        # ⚠️ **ပုံ param** — `fill()` မှာ ဤအခွဲ မရှိခဲ့၍ `break` ဖြစ်ကာ args
        #    ဗလာ ပြန်ခဲ့သည် (「fill ဗလာ」)。 `thm.media_*` ၁၃ ခု · `social`
        #    ၁၀ ခု · `brows` · `maps.photo_inset` · `typo2.subject_rise` —
        #    စုစုပေါင်း ၂၈ ခု IKKI ဆီ **လုံးဝ မရောက်**ခဲ့ (၂၀၂၆-၀၉-၂၅)。
        # ⚠️ `img` မပါလျှင် ဆက်မဖြည့်ရ — အသုံးပြုသူ စာသားကို ပုံ လမ်းကြောင်း
        #    အကွက်ထဲ ထည့်မိလျှင် `ffmpeg -i 'ဂျပန်မှာ အလုပ်'` နဲ့ ကျသည်。
        if ty == "file" or nm in IMG_NAMES:
            if not img: break
            args.append([img, img, img] if nm in ("imgs", "images", "logos", "photos")
                        else img)
            continue
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


# ── demoargs ရဲ့ ပုံစံ ပြန်ဆုတ်လမ်း ──────────────────────────
# ⚠️ `fill()` ရော `tmplfit` ရော ဖြည့်မရသော template **၅၅ ခု** ကျန်ခဲ့သည်
#    (၂၀၂၆-၀၉-၂၅)。 အကြောင်းရင်းက param ရဲ့ **တည်ဆောက်ပုံ** ကို နာမည်တစ်ခု
#    တည်းနဲ့ မှန်း၍ မရခြင်း — `grid` က ကိန်း ၂ ဆင့် · `rows` က ၃ တွဲ ·
#    `maps` ရဲ့ `a`/`b` က (lat,lon) ဖြစ်လျက် `prem7` ရဲ့ `a`/`b_` က
#    (နာမည်,ကိန်း)。 ⇒ **motionkit ရဲ့ `demoargs.py` ကို ပုံစံပြ အဖြစ် ယူ**ပြီး
#    စာသား အကွက်တွေကိုသာ အသုံးပြုသူ စာသားနဲ့ အစားထိုးသည် (`argshape.py`)。
# ══ ကိန်း slot ထဲ ဝါကျ ဝင်တာကို တားခြင်း ═══════════════════════════
# ⚠️ ၂၀၂၆-၀၉-၂၈ တိုင်းချက် — `prem6.like_burst(tag, count='12.4K')` ရဲ့
#    `count` ကို manifest က `type: text` လို့ ကြေညာသဖြင့် (`_ptype()` က
#    **ခန့်မှန်း**တာ · param နာမည် ၂၅၆ ခုမှာ type hint ၀ ခု) `argshape.fit`
#    က မြန်မာ ဝါကျ ၆၄ လုံးကို like ရေတွက် နေရာ ထည့်ခဲ့သည်。
#    ⇒ ကတ်မှာ နှလုံးသား သင်္ကေတ + ဖြတ်ခေါက်ထားသော ဝါကျ (arm V7 frame)。
# ⚠️ catalog 616 စစ်၍ **36 ခု** ဒီအမျိုးအစား ဖြစ်သည် · အဲဒီထဲ **7 ခု** က
#    flag ၂ ခု **ပိတ်ထားသည့် လက်ရှိ production** မှာ ရွေးခံရနိုင်သည် ⇒
#    rotate/alias နဲ့ မဆိုင်ဘဲ **ယခုပဲ ဖြစ်နေသော** ချို့ယွင်းချက်。
# ⚠️ category ဂိတ်နဲ့ မတားနိုင်ပါ — ချို့ယွင်းချက် category ၅ မျိုးလုံး
#    (`title` 10 · `infographic` 4 · `mockup` 3 · `callout`/`text`/`typography`)
#    က `fact` label ရဲ့ လက်ခံစာရင်း (၉ မျိုး) ထဲ ပါသည်。
# ⚠️ **param တစ်ခုချင်း** စစ်ရမည် — `titles.chapter` က `num='၀၂'` (ကိန်း)
#    နဲ့ `title` (စာသား အစစ်) ၂ ခုလုံး ရှိသည် ⇒ template တစ်ခုလုံး
#    မငြင်းရ、ကိန်း slot ထဲ ဝါကျ ဝင်မှသာ ငြင်းရမည်。
_NUMSLOT = re.compile(
    r"^\s*[0-9၀-၉]"          # ဂဏန်း (Latin ရော မြန်မာ ရော) နဲ့ စ
    r"[0-9၀-၉.,]*"            # ဂဏန်း · ဒဿမ · ကော်မာ
    r"\s*(?:%|K|M|B|x|×|\+|−|-)?\s*$",  # ယူနစ်/သင်္ကေတ (ရွေးချယ်)
    re.I)
NUMSLOT_MAX = 8      # ကိန်း default ရဲ့ အများဆုံး အရှည်
TEXT_MAX = 16        # ဒီထက် ရှည်လျှင် ဝါကျ ဟု သတ်မှတ်


def _is_numslot(v):
    """default တန်ဖိုး က **ကိန်း slot** ဟု ပြသလား。"""
    if not isinstance(v, str):
        return False
    v = v.strip()
    return bool(v) and len(v) <= NUMSLOT_MAX and bool(_NUMSLOT.match(v))


def numslot_bad(entry, args):
    """ကိန်း slot ထဲ ဝါကျ ဝင်သွားသော param စာရင်း — `[(param, default, n)]`。

    ⚠️ default ကို **builder signature** ကနေ အရင် ယူသည် (အတိအကျဆုံး) ·
       မရလျှင် `demoargs` ရဲ့ positional ကနေ。
    """
    out = []
    if not isinstance(args, dict):
        return out
    defs = {}
    try:
        import importlib
        import inspect
        if MK not in sys.path:
            sys.path.insert(0, MK)
        m = importlib.import_module(entry["module"])
        fn = ((getattr(m, "BUILDERS", {}) or {}).get(entry["fn"])
              or getattr(m, entry["fn"], None))
        _ps = list(inspect.signature(fn).parameters.values())[1:]
        for p in _ps:
            if p.default is not inspect.Parameter.empty:
                defs[p.name] = p.default
        # ⚠️ **`demoargs` ကိုပါ ကြည့်ရမည်** — required param မှာ signature
        #    default မရှိသဖြင့် အဲဒီကနေ ကိန်း အရိပ်အမြွက် မရပါ。
        #    `demoargs` က positional tuple ဖြစ်ပြီး `tag` အလွန် param
        #    အစဉ်နဲ့ ကိုက်သည် ⇒ `_ps[i]` ↔ `demoargs[i]`。
        #    (တိုင်းချက်: signature default တစ်ခုတည်းနဲ့ ၃၆ ထဲ **၅ ခုသာ**
        #     ဖမ်းမိသည် — ကျန် ၃၁ ခုက demoargs ကနေသာ ပေါ်သည်။)
        try:
            import demoargs as _DA
            _dd = (getattr(_DA, entry["module"].upper(), None)
                   or (getattr(_DA, "ALL", {}) or {}).get(entry["module"]) or {})
            _t = _dd.get(entry["fn"])
            if isinstance(_t, (tuple, list)):
                for i, p in enumerate(_ps):
                    if i < len(_t) and p.name not in defs:
                        defs[p.name] = _t[i]
                    elif i < len(_t) and not _is_numslot(defs.get(p.name)):
                        # signature default က ကိန်းပုံစံ မဟုတ်လျှင်
                        # demoargs ကို ဦးစားပေးသည် (ပိုတိကျသည်)
                        if _is_numslot(_t[i]):
                            defs[p.name] = _t[i]
        except Exception:
            pass
    except Exception:
        return out
    for k, v in args.items():
        if k in ("tag", "dur"):
            continue
        if not isinstance(v, str) or len(v.strip()) <= TEXT_MAX:
            continue
        if _is_numslot(defs.get(k)):
            out.append((k, str(defs.get(k)), len(v.strip())))
    return out


def pairs_bad(entry, args):
    """**အတွဲ စာရင်း** လိုသော param ထဲ ရိုးရိုး စာသား ဝင်နေသလား

    ပြန်ပေးသည် — `[(param, နမူနာ အတွဲ အရေအတွက်)]` · မရှိလျှင် `[]`

    ⚠️ ၂၀၂၆-၀၉-၂၉ — `odo.tick_row(rows=[[label, number], …])` ကို ဝါကျ
       ရိုးရိုး ပေးလျှင် `too many values to unpack (expected 2)` နဲ့
       **ဆောက်ချိန်မှာ** ကျသည် ⇒ စာရွက် ပြန်ဆုတ်。 `demoargs` အရ ဤပုံစံ
       **၅၄ ခု** ရှိသည် (charts ၉ · infogfx ၈ · dash ၄ · brows …) ⇒
       တစ်ခုချင်း `STRUCTURED` ထဲ ထည့်နေလို့ မလုံလောက် — planner က
       နောက်တစ်ခု ကောက်ယူသည် (tick_row → checklist_tick → card_grid)。
    ⚠️ **ရွေးချိန်မှာ အကုန် မဖယ်ရ** — `number`/`compare` အညွှန်းတွေက
       အတွဲ ဒေတာ တကယ် ပေးနိုင်သည် ⇒ **ဖြည့်ချိန်**မှာ တန်ဖိုး ကြည့်ပြီးမှ
       ဆုံးဖြတ်ရမည်。 အတွဲ ပေးထားလျှင် ဖြတ်မထားပါ。
    """
    try:
        import demoargs as _DA
    except Exception:
        return []
    shp = ((_DA.ALL or {}).get(entry.get("module")) or {}).get(entry.get("fn"))
    if not isinstance(shp, (list, tuple)):
        return []
    names = [p["name"] for p in (entry.get("params") or [])]
    bad = []
    for i, dv in enumerate(shp):
        if not (isinstance(dv, (list, tuple)) and dv
                and all(isinstance(x, (list, tuple)) and len(x) >= 2
                        for x in dv)):
            continue
        if i >= len(names):
            continue
        got = (args or {}).get(names[i])
        if not isinstance(got, (list, tuple)) or not got:
            continue
        # ⚠️ တစ်ခုချင်းက အတွဲ ဖြစ်ရမည် — မဟုတ်လျှင် ဆောက်ချိန် ကျမည်
        if not all(isinstance(x, (list, tuple)) and len(x) >= 2 for x in got):
            bad.append((names[i], len(dv)))
    return bad


def fill_kw(entry, texts, img=None, pct=None, nums=None, strict=False):
    """`{param: တန်ဖိုး}` သို့ `None` — `demoargs` ပုံစံ + အသုံးပြုသူ စာသား。

    ⚠️ ကိန်း slot ထဲ ဝါကျ ဝင်သွားလျှင် **`None` ပြန်**သည် ·
       `LAST_ERR` မှာ `numeric_slot_overflow` ဟု မှတ်သည် (တိတ်တဆိတ် မဖြစ်စေရန်)。
       `IKKI_NUMSLOT_OFF=1` ⇒ ဂိတ် ပိတ် (A/B အတွက်)。
    """
    cwd = os.getcwd()
    try:
        if MK not in sys.path: sys.path.insert(0, MK)
        os.chdir(MK)
        import argshape as A
        _r = A.fit(entry["module"], entry["fn"], entry.get("params") or [],
                   texts, img=img, pct=pct, nums=nums, strict=strict)
        if _r is not None and os.environ.get("IKKI_NUMSLOT_OFF") != "1":
            _nb = numslot_bad(entry, _r)
            if _nb:
                LAST_ERR[0] = ("numeric_slot_overflow: "
                               + " · ".join(f"{k}={d!r}←{n}လုံး"
                                            for k, d, n in _nb))
                return None
        if _r is not None and os.environ.get("IKKI_PAIRS_OFF") != "1":
            _pb = pairs_bad(entry, _r)
            if _pb:
                LAST_ERR[0] = ("pair_rows_required: "
                               + " · ".join(f"{k} (အတွဲ {n} တွဲ လို)"
                                            for k, n in _pb))
                return None
        return _r
    except Exception as e:
        LAST_ERR[0] = f"{type(e).__name__}: {e}"
        return None
    finally:
        try: os.chdir(cwd)
        except Exception: pass


def call(entry, args, dur):
    """template ကို တကယ် ခေါ်သည် — PNG စာရင်း ပြန်ပေးသည်"""
    cwd = os.getcwd()
    try:
        if MK not in sys.path: sys.path.insert(0, MK)
        os.chdir(MK)
        import importlib
        m = importlib.import_module(entry["module"])
        # ⚠️ **`getattr` တစ်ခုတည်း မလုံလောက်** — `trans` ရဲ့ ၂၄ ခုက factory
        #    ကနေ ဆောက်ထားသော closure ဖြစ်၍ `BUILDERS` dict ထဲမှာသာ ရှိပြီး
        #    module attribute **မဟုတ်**ပါ。 `catalog.build()` ကိုယ်တိုင်က
        #    `BUILDERS` ကနေ စာရင်းထုတ်သဖြင့် ခေါ်သူကလည်း အဲဒီကနေ ရှာရမည် —
        #    မရှာလျှင် အသွင်ကူး ၂၄ ခုလုံး `AttributeError` (၂၀၂၆-၀၉-၂၄)。
        fn = (getattr(m, "BUILDERS", {}) or {}).get(entry["fn"]) \
            or getattr(m, entry["fn"])
        kw = {}
        if any(p.get("name") == "dur" for p in entry.get("params", [])):
            kw["dur"] = dur
        # ⚠️ `args` က **dict** ဖြစ်လျှင် kwargs အဖြစ် ခေါ်သည် — `maps.route_arc`
        #    လို template မှာ `label_a`/`label_b` က `dur` ရဲ့ **နောက်**မှာ
        #    ရှိသဖြင့် positional tuple နဲ့ မရောက်နိုင် (`dur` မှာ ရပ်ရသည်)。
        if isinstance(args, dict):
            a0 = dict(args); a0.pop("dur", None)
            tag = a0.pop("tag", None)
            return fn(tag, **a0, **kw) if tag is not None else fn(**a0, **kw)
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
