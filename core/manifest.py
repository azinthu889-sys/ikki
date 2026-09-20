"""motionkit template manifest — planner ရွေးခွင့် ရှိသော စာရင်း။

⚠️ **planner က ဒီစာရင်းထဲကပဲ ရွေးခွင့် ရှိသည်**。 Gemini က မရှိသော template
   နာမည် ဖန်တီးတတ်သည် — မစစ်ဘဲ ယုံလျှင် render ချိန်မှ `KeyError` ဖြစ်ပြီး
   အလုပ် တစ်ခုလုံး ပျက်မည်。

⚠️ **motionkit က API container ထဲ မပါ**。 `core/grade.py` နဲ့ တူညီသော
   ထောင်ချောက် — `/app/core` မှာ ဖိုင် ၆ ခုသာ ရှိပြီး `catalog` ကို import
   မရပါ (၂၀၂၆-၀၉-၂၀ မှာ `grade` import ကြောင့် `/api/styles` တစ်ခုလုံး
   ပျက်ခဲ့သည်)。 ⇒ snapshot JSON ကို repo ထဲ ထည့်ပြီး API က **အဲဒါနဲ့**
   စစ်သည်、motionkit ရှိမှသာ တိုက်ရိုက် ဖတ်သည်。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "manifest_snapshot.json")

_M = None


def _from_catalog():
    """motionkit ရှိလျှင် တိုက်ရိုက် ဖတ်သည် — မရှိလျှင် None"""
    try:
        import sys
        try:
            import gfxcat as GC
        except ImportError:
            from core import gfxcat as GC
        if GC.MK not in sys.path:
            sys.path.insert(0, GC.MK)
        cwd = os.getcwd()
        os.chdir(GC.MK)
        try:
            import importlib
            import glob
            import catalog as CT
            out = {}
            for p in sorted(glob.glob("*.py")):
                mod = p[:-3]
                if mod in ("catalog", "render", "render2", "theme", "kit", "sfxlib"):
                    continue
                try:
                    m = importlib.import_module(mod)
                except Exception:
                    continue
                b = getattr(m, "BUILDERS", None)
                if not isinstance(b, dict):
                    continue
                for fn in b:
                    cid = f"{mod}.{fn}"
                    try:
                        out[cid] = CT.by_id(cid)
                    except Exception:
                        # ⚠️ catalog မှာ မမှတ်ထားသော builder ရှိနိုင် —
                        #    ဖယ်မပစ်ဘဲ အနည်းဆုံး အချက်အလက်နဲ့ ထည့်သည်。
                        out[cid] = dict(id=cid, module=mod, fn=fn,
                                        category="", params=[])
            return out or None
        finally:
            os.chdir(cwd)
    except Exception:
        return None


def load(refresh=False):
    """id → entry (`params` · `category` · `module` ပါသည်)"""
    global _M
    if _M is not None and not refresh:
        return _M
    m = _from_catalog()
    if m is None and os.path.exists(SNAP):
        with open(SNAP, encoding="utf-8") as f:
            m = json.load(f)
    _M = m or {}
    return _M


def save_snapshot(path=SNAP):
    """motionkit ရှိသော စက်မှာ run ပြီး snapshot ထုတ်သည် (deploy အတွက်)"""
    m = _from_catalog()
    if not m:
        raise RuntimeError("motionkit မဖတ်နိုင် — snapshot မထုတ်နိုင်ပါ")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, sort_keys=True)
    return len(m)


def ids():
    return set(load())


def entry(cid):
    return load().get(cid)


# ── Headtop ရွေးခွင့် စာရင်း ────────────────────────────────
# ⚠️ ဤစာရင်းက **Zin သတ်မှတ်ပေးထားသော ID များ** (၂၀၂၆-၀၉-၂၀)。
#    ၃၇ ခုလုံး motionkit ထဲ တကယ် ရှိကြောင်း စစ်ပြီး (မရှိတာ ၀)。
#    ⚠️ ID အသစ် ထည့်လျှင် `load()` နဲ့ ပြန်စစ်ရမည် — မရှိသော ID က
#       render ချိန်ကျမှ ပျက်စေသည်。
HEADTOP = {
    "caption": ["prem5.hl_word_cap", "prem5.karaoke_cap", "prem5.line_by_line",
                "capt.hl_phrase", "capt.multi_line", "capt.line_by_line",
                "kinetic2.subtitle_2line"],
    "hook":    ["prem4.stop_scroll", "prem4.big_question", "prem4.shock_stat",
                "titles3.opening_bars", "typo.hero_word"],
    "ident":   ["titles3.minimal_third", "titles.name_plate",
                "titles.topic_bar", "titles.chapter"],
    "explain": ["infogfx.steps", "infogfx.checklist", "infogfx.compare_bar",
                "infogfx.big_number", "infogfx.timeline"],
    # ⚠️ ဂဏန်း **တကယ် ပြောမှသာ** သုံးရမည် (Zin ရဲ့ စည်းမျဉ်း)
    "number":  ["odo.count_up", "odo.percent_ring", "odo.big_stat"],
    "callout": ["callouts.line_call", "callouts.box_call",
                "callouts.underline_call", "callouts.numbered_pin"],
    "broll":   ["prem7.location_tag", "prem7.checklist_tick", "prem7.step_badge",
                "prem7.note_card", "prem7.end_grid"],
    # ⚠️ glitch · VHS · retro · loud wipe ကို **တမင် ချန်ထားသည်** —
    #    ပညာရေး/အဖွဲ့အစည်း ဗီဒီယိုနဲ့ မလိုက်ဖက်ပါ (Zin ရဲ့ စည်းမျဉ်း)。
    "trans":   ["trans.blur_dissolve", "trans.zoom_punch",
                "trans.whip_pan", "trans.flash"],
}


def headtop_ids():
    out = []
    for v in HEADTOP.values():
        out += v
    return out


def verify(subset=None):
    """စာရင်းထဲက ID တွေ တကယ် ရှိမရှိ — `(ရှိ, မရှိ)` ပြန်ပေးသည်"""
    have = ids()
    want = subset if subset is not None else headtop_ids()
    good = [c for c in want if c in have]
    bad = [c for c in want if c not in have]
    return good, bad


def props_ok(cid, props):
    """event ရဲ့ props က template ရဲ့ param နဲ့ ကိုက်လား — `(ok, [အမှား])`

    ⚠️ မသိသော key ကို **ဖြုတ်မပစ်ဘဲ အမှားအဖြစ် ပြရမည်** — Gemini က
       တီထွင်ထားတာ ဖြစ်နိုင်၍ တိတ်တဆိတ် ကျော်သွားလျှင် ဘာမှ မပေါ်ဘဲ
       ဖြစ်မည် (ဒီ project မှာ တိတ်တဆိတ် ကျရှုံးမှု ထပ်ခါထပ်ခါ ဖြစ်ခဲ့သည်)。
    """
    e = entry(cid)
    if not e:
        return False, [f"template မရှိ: {cid}"]
    known = {p["name"] for p in (e.get("params") or [])}
    errs = []
    if known:
        for k in (props or {}):
            if k not in known:
                errs.append(f"{cid}: param မရှိ '{k}' (ရှိသည်: {sorted(known)})")
        for p in (e.get("params") or []):
            if p.get("required") and not p.get("auto") \
               and p["name"] not in (props or {}):
                errs.append(f"{cid}: လိုအပ်သော param ကျန် '{p['name']}'")
    return (not errs), errs
