#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""User taste memory — သုံးစွဲသူ ခဏခဏ ပြင်တာကို မှတ်ပြီး နောက်ဗီဒီယိုမှာ အလိုလို လုပ်ပေး (Zin ၂၀၂၆-၁၀-၀၇)

「User တစ်ယောက်က ဘာကို ခဏခဏ ပြင်လဲ (ကတ်ကို အမြဲဖြုတ် · SFX လျှော့) မှတ်ပြီး နောက်ဗီဒီယိုမှာ လိုက်လုပ်」

အချက်ပြ (signal) ၃ မျိုး:
  · look  — 「အလှအပ · SFX · Motion」 မှာ သိမ်းသော တန်ဖိုး (ဂဏန်း ⇒ ပျမ်းမျှ · ဖွင့်/ပိတ် ⇒ အများစု)
  · remove — Visual Plan / beat 「ဖြုတ်」 (ပုံစံ အမျိုးအစား အလိုက် ရေတွက်)
  · swap  — beat ပုံစံ လဲ (A ⇒ B : A ကို မကြိုက် · B ကို ကြိုက်)

⚠️ **ယုံကြည်မှု ဂိတ်** — တစ်ကြိမ်တည်း ပြင်တာကို အမြဲ မလုပ်ရ (MIN_N ကြိမ် ထပ်မှ)。
⚠️ **ဘောင်အတွင်းသာ** — look တန်ဖိုးကို `recipes.clean()` ထပ်စစ် (QC ဂိတ် မထိ)。
⚠️ **ပြန်ဖျက်နိုင်ရမည်** — UI မှာ 「မှတ်ထားတာ」 ပြပြီး 「မေ့လိုက်」 ခလုတ်。
⚠️ ဗီဒီယိုတစ်ပုဒ်ချင်း ပြင်ချက်က အမြဲ အနိုင် — taste က **ပုံသေ** သာ ပေး (job ရဲ့ over ထဲ မရှိတာကိုသာ ဖြည့်)。
"""
import time

MIN_N = 2          # ဤအကြိမ် ထပ်မှ မှတ်ချက်အဖြစ် သုံး
ALPHA = 0.5        # ဂဏန်း — နောက်ဆုံး ပြင်ချက်ကို ပိုအလေးပေး (EMA)
AVOID_AT = 2       # ဖြုတ်/လဲ အကြိမ် — ဒီလောက် ရောက်လျှင် director ရှောင်

LOOK_LABEL = {"gfx": "ဂရပ်ဖစ်", "broll_pct": "B-roll", "sfx_per_min": "SFX", "sfx_trim": "SFX အသံ",
              "music": "တီးလုံး", "music_lufs": "တီးလုံး အသံ", "cam_moves": "ကင်မရာ",
              "broll_whip": "whip", "kin_title": "စာလုံး လှုပ်ရှား"}


KEEP_JOBS = 30     # နောက်ဆုံး ဗီဒီယို ၃၀ ပုဒ်ကနေသာ သင်ယူ (ပုံစံ ပြောင်းလျှင် လိုက်ပြောင်း)


def empty():
    return {"look": {}, "avoid": {}, "like": {}, "n_jobs": 0, "updated": 0}


# ── job အလိုက် သိမ်း ⇒ ပေါင်း (ထပ်ထုတ်လည်း နှစ်ခါ မရေ · နောက်ဆုံး အခြေအနေသာ) ─────────
def observe(store, jid, look=None, removed=(), swaps=()):
    """`store` = `{"by_job": {jid: {...}}}` — job တစ်ခု ပြီးတိုင်း ခေါ် (ပြန်ထုတ်လည်း အစားထိုးသာ)"""
    store = dict(store or {})
    bj = dict(store.get("by_job") or {})
    bj[str(jid)] = {"look": dict(look or {}), "remove": [str(x) for x in removed if x],
                    "swap": [[str(a), str(b)] for a, b in swaps if a and b], "t": time.time()}
    if len(bj) > KEEP_JOBS:
        for k in sorted(bj, key=lambda x: bj[x].get("t", 0))[:len(bj) - KEEP_JOBS]:
            bj.pop(k, None)
    store["by_job"] = bj
    return store


def aggregate(store):
    """by_job ⇒ ပေါင်းထားသော taste (`look`/`avoid`/`like`) — အဟောင်း → အသစ် အစဉ်"""
    d = empty()
    jobs = sorted(((store or {}).get("by_job") or {}).values(), key=lambda x: x.get("t", 0))
    for j in jobs:
        record_look(d, j.get("look") or {})
        for k in j.get("remove") or []:
            record_remove(d, k)
        for a, b in j.get("swap") or []:
            record_swap(d, a, b)
    d["n_jobs"] = len(jobs)
    return d


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def record_look(d, look):
    """look dict (သုံးစွဲသူ ထိထားသော key သာ) ⇒ d ပြင်"""
    d = d or empty()
    L = d.setdefault("look", {})
    for k, v in (look or {}).items():
        e = L.setdefault(k, {"n": 0})
        e["n"] = int(e.get("n", 0)) + 1
        if _num(v):
            e["v"] = float(v) if "v" not in e or not _num(e.get("v")) else \
                round(ALPHA * float(v) + (1 - ALPHA) * float(e["v"]), 4)
            e.pop("c", None)
        else:
            key = "null" if v is None else str(v)
            c = e.setdefault("c", {})
            c[key] = int(c.get(key, 0)) + 1
    d["updated"] = time.time()
    return d


def record_remove(d, kind):
    """ဖြုတ်ခြင်း — `kind` = `beat.timeline` · `modern.mt_counter` စသည်"""
    d = d or empty()
    if kind:
        a = d.setdefault("avoid", {})
        a[kind] = int(a.get(kind, 0)) + 1
    d["updated"] = time.time()
    return d


def record_swap(d, old, new):
    d = record_remove(d, old) if old and old != new else (d or empty())
    if new and old != new:
        lk = d.setdefault("like", {})
        lk[new] = int(lk.get(new, 0)) + 1
    d["updated"] = time.time()
    return d


def look_defaults(d, clean=None):
    """ယုံကြည်လောက်သော look ပုံသေ — `{key: value}`"""
    out = {}
    for k, e in ((d or {}).get("look") or {}).items():
        if int(e.get("n", 0)) < MIN_N:
            continue
        if "v" in e and _num(e["v"]):
            v = e["v"]
            out[k] = int(round(v)) if k == "gfx" else round(float(v), 3)
        elif e.get("c"):
            key, cnt = max(e["c"].items(), key=lambda x: x[1])
            if cnt < MIN_N:
                continue
            out[k] = None if key == "null" else (True if key == "True" else False if key == "False" else key)
    if clean and out:
        nulls = {k for k, v in out.items() if v is None}
        cl = clean({k: v for k, v in out.items() if v is not None})
        for k in nulls:
            cl[k] = None
        out = cl
    return out


def avoid_types(d):
    """director ရှောင်ရမည့် beat type — ဖြုတ်/လဲ ≥ AVOID_AT နဲ့ ကြိုက် အကြိမ်ထက် များ"""
    av, lk = (d or {}).get("avoid") or {}, (d or {}).get("like") or {}
    out = []
    for k, n in av.items():
        if k.startswith("beat.") and int(n) >= AVOID_AT and int(n) > int(lk.get(k, 0)):
            out.append(k[5:])
    return sorted(out)


def apply(d, over, clean=None):
    """job အသစ်ရဲ့ `over` ⇒ taste ပုံသေ ဖြည့် (ရှိပြီးသား key ကို မထိ)。 ပြန်: (over, applied)"""
    over = dict(over or {})
    applied = {}
    for k, v in look_defaults(d, clean).items():
        if k not in over:
            over[k] = v
            applied[k] = v
    av = avoid_types(d)
    if av and "_avoid_types" not in over:
        over["_avoid_types"] = av
        applied["_avoid_types"] = av
    if applied:
        over["_taste"] = sorted(applied)
    return over, applied


def summary(d, tnames=None):
    """UI အတွက် မြန်မာ စာကြောင်းများ"""
    tnames = tnames or {}
    out = []
    for k, v in look_defaults(d).items():
        lab = LOOK_LABEL.get(k, k)
        if isinstance(v, bool):
            out.append(f"{lab} {'ဖွင့်' if v else 'ပိတ်'}")
        elif v is None:
            out.append(f"{lab} မထည့်")
        elif k == "broll_pct":
            out.append(f"{lab} {round(float(v) * 100)}%")
        else:
            out.append(f"{lab} {v}")
    for t in avoid_types(d):
        out.append(f"「{tnames.get(t, t)}」 မသုံး")
    return out
