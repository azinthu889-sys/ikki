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
import os, sys

MK = os.environ.get("IKKI_MOTIONKIT",
      "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")

# overlay အဖြစ် သုံးလို့ရသော အမျိုးအစား
USE = ("title", "infographic", "callout", "typography", "text", "chart")

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

# ── argument ဖြည့်ခြင်း ──────────────────────────────────────
def fill(entry, text, sub="", pct=None):
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
    LISTY = ("levels", "stages", "rows", "items", "lines", "bullets",
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
        if req and ty == "number" and pct is not None:
            args.append(pct)
            continue
        break
    while args and args[-1] == "":
        args.pop()
    return tuple(args) if args else None


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
