# -*- coding: utf-8 -*-
"""A/B arm အတွက် **plan နှင့် B-roll ရွေးချက်ကို ပင်ထိုးခြင်း** (harness သာ)

⚠️ ၂၀၂၆-၀၉-၃၀ — arm ၃ ခုကို 「ကုဒ် · seed · flag တူတူ · per_min သာ ကွာ」 ဟု
   တင်ပြခဲ့သည် — **မှားသည်**。 ကတ် စာရင်း တကယ် ကွာခဲ့ပြီး (C2 မှာ
   thm.list_tick + typew.hl_bar · W2/A3 မှာ titles2.big_number +
   glitch.jitter_caps)、short-video session က အကြောင်းရင်း တွေ့သည်:
   **Gemini ရဲ့ ရလဒ်က run တိုင်း မတူ** (B-roll matcher က ၆ ခု တစ်ခါ · ၅ ခု
   တစ်ခါ · byte တူညီသော ကုဒ် နဲ့ job ပေါ်မှာ)。
   ⇒ seed က rotation ကိုသာ ပင်ထိုးသည်、**Gemini ကို မပင်ထိုးပါ**。
   ⇒ arm ၁ ကနေ သိမ်းပြီး arm ၂/၃ ကို **ပြန်ထည့်**ရမည် — အဲဒါမှသာ
     「တစ်ခုသာ ကွာသည်」 ဆိုတာ တကယ် ဖြစ်မည်。

⚠️ ဤ module က **harness သာ** — production ကုဒ် မထိပါ。 `worker.run` ကို
   import မလုပ်ခင် `arm()` ကို ခေါ်ရမည် (module attribute ကို အစားထိုးသည်)。

သုံးနည်း:
    import h_pin; h_pin.arm(out="/path/arm_A.pin.json")     # သိမ်း
    import h_pin; h_pin.arm(inp="/path/arm_A.pin.json")     # ပြန်ထည့်
"""
import json, os, sys

_ST = {"mode": None, "path": None, "rec": {}, "play": {}, "hit": 0, "miss": 0}


def _key(*a):
    return "|".join(str(x) for x in a)


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _save():
    if _ST["mode"] != "rec" or not _ST["path"]:
        return
    tmp = _ST["path"] + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_ST["rec"], f, ensure_ascii=False)
    os.replace(tmp, _ST["path"])


def _wrap(mod, name, kf):
    """`mod.name` ကို record/replay ဖြင့် အစားထိုးသည်

    ⚠️ **key က input ကနေ တွက်ရမည်** — ခေါ်ချက် အစီအစဉ် (၁, ၂, ၃) နဲ့
       key လုပ်လျှင် arm ၂ က ခေါ်ချက် ပိုနည်း/ပိုများ ဖြစ်သည်နှင့်
       တစ်နေရာစီ ရွေ့ပြီး **မှားသော plan** ပြန်ပေးမည်。
    """
    # ⚠️ module မှာ အဲဒီ function မရှိလျှင် **ကျမသွားရ** — ကျော်သည်
    #    (ကိုယ့် test ရဲ့ fake module က `match` မပါသဖြင့် ဖမ်းမိသည်)。
    orig = getattr(mod, name, None)
    if orig is None:
        print(f"  \u26a0\ufe0f h_pin · {mod.__name__}.{name} မရှိ — ကျော်သည်",
              flush=True)
        return

    def inner(*a, **k):
        try:
            key = _key(name, kf(*a, **k))
        except Exception:
            return orig(*a, **k)
        if _ST["mode"] == "play":
            if key in _ST["play"]:
                _ST["hit"] += 1
                return _ST["play"][key]
            # ⚠️ **တိတ်တဆိတ် မကျော်ရ** — မတွေ့လျှင် ပင်ထိုးချက် မပြည့်ဘဲ
            #    arm က ကွာသွားမည် ⇒ ရေတွက်ပြီး အဆုံးမှာ ပြသည်。
            _ST["miss"] += 1
            print(f"  ⚠️ h_pin · MISS {name} ({key[:70]})", flush=True)
            return orig(*a, **k)
        r = orig(*a, **k)
        if _ST["mode"] == "rec":
            try:
                json.dumps(r, ensure_ascii=False)
            except (TypeError, ValueError):
                print(f"  ⚠️ h_pin · {name} က JSON မဖြစ် — မသိမ်းပါ",
                      flush=True)
                return r
            _ST["rec"][key] = r
            _save()
        return r

    inner.__name__ = name + "_pinned"
    setattr(mod, name, inner)


def report():
    print("  ⌘ h_pin · mode=%s · hit %d · miss %d · သိမ်းထား %d"
          % (_ST["mode"], _ST["hit"], _ST["miss"], len(_ST["rec"])), flush=True)
    return dict(mode=_ST["mode"], hit=_ST["hit"], miss=_ST["miss"],
                recorded=len(_ST["rec"]))


def arm(out=None, inp=None, repo=None):
    """record (`out`) သို့မဟုတ် replay (`inp`) — `worker.run` import မလုပ်ခင်"""
    if bool(out) == bool(inp):
        raise ValueError("out သို့မဟုတ် inp — တစ်ခုသာ")
    if repo:
        for sub in ("core", "worker"):
            p = os.path.join(repo, sub)
            if p not in sys.path:
                sys.path.insert(0, p)
    import planner as PLN
    import broll as BR

    if inp:
        _ST["mode"] = "play"
        _ST["play"] = _load(inp)
        print("  ⌘ h_pin · ပြန်ထည့် %d ချက် ← %s"
              % (len(_ST["play"]), os.path.basename(inp)), flush=True)
    else:
        _ST["mode"] = "rec"
        _ST["path"] = out
        print("  ⌘ h_pin · သိမ်းမည် → %s" % os.path.basename(out), flush=True)

    # ⚠️ key ကို **အကြောင်းအရာ** ကနေ — segs ရဲ့ စာသား နဲ့ ကာလ。 arm တိုင်း
    #    တူညီသော source ကို သုံးသဖြင့် segs တူမည်。 ကွာလျှင် MISS ပြမည်。
    def _plan_key(segs, dur, opts=None, video_id="src", log=None):
        n = len(segs or [])
        txt = "".join(str((s or {}).get("text", ""))[:12] for s in (segs or [])[:8])
        return _key(n, round(float(dur or 0), 1), video_id, txt[:96])

    def _pick_key(segs, want, used=None, min_score=3):
        n = len(segs or [])
        txt = "".join(str((s or {}).get("text", ""))[:12] for s in (segs or [])[:8])
        return _key(n, want, min_score, txt[:96])

    # ⚠⚠ **`broll.match` ကိုပါ ပင်ထိုးရမည်** (၂၀၂၆-၁၀-၀၁)。 cutaway
    #    budget ပြောင်းချက်ကို တိုင်းရာမှာ `match` က run တိုင်း မတူသဖြင့်
    #    **ပြောင်းချက်ရဲ့ အကျိုးသက်ရောက်မှု မတိုင်းရ**ခဲ့:
    #      kb render  match 2 · kc render (budget တင်ပြီး) match **0**
    #      ကိုယ်တိုင် ခေါ်ကြည့်ချိန်  match 4
    #    ကိန်း ၃ မျိုးက Gemini ရဲ့ ကွဲလွဲမှု — budget ရဲ့ သက်ရောက်မှု မဟုတ်。
    def _match_key(segs, want, used=None, log=None, strict=False):
        n = len(segs or [])
        txt = "".join(str((s or {}).get("text", ""))[:12] for s in (segs or [])[:8])
        # ⚠️ `want` ကို key ထဲ **မထည့်ရ** — budget ပြောင်းလျှင် key
        #    ပြောင်းပြီး replay မမိတော့မည်。 တိုင်းချင်တာက အဲဒီ ပြောင်းချက်。
        return _key(n, strict, txt[:96])

    _wrap(PLN, "plan", _plan_key)
    _wrap(BR, "pick", _pick_key)
    _wrap(BR, "match", _match_key)
    return report()
