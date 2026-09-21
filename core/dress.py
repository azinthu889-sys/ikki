#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · ဂရပ်ဖစ် ရွေးချယ်မှု + SFX cue。

⚠️ template ၉၀ ရှိသည် — အားလုံး တပ်လျှင် ရုပ်ဆိုးသည်。 recipe ရဲ့ `gfx`
   ကိန်းအရ **အရေအတွက် ကန့်သတ်**ပြီး တိတ်ဆိတ်မှုကြီးများ (စကားခေတ္တရပ်သည့်
   အချိန်) မှာသာ ချသည် — စကားပြောနေတုန်း ဂရပ်ဖစ် တက်လာလျှင် စာဖတ်မရ。

⚠️ ffmpeg input ကန့်သတ်ချက် — ဂရပ်ဖစ် PNG တွေကိုပါ input အဖြစ် ထည့်လျှင်
   ၁၄၀ ခန့်မှာ ပျက်သည်。 ⇒ စာတန်းလိုပဲ **alpha track တစ်ခု** ဆောက်ရမည်。
"""
import os

def pick(rc, dur, sil, segs, log=None):
    """(when, kind) စာရင်း — ဂရပ်ဖစ် ဘယ်အချိန် ဘယ်ဟာ ချမလဲ。"""
    want = int(rc.get("gfx") or 0)
    if want <= 0 or dur < 12: return []
    # ⚠️ ပုံမှန်က **ရှည်သော တိတ်ဆိတ်မှုမှာသာ** ချသည် — စကားပြောနေတုန်း မချရ。
    # ⚠️ ဒါပေမယ့် တင်းတင်း ဖြတ်ထားသော footage မှာ အဲဒီလို နေရာ မရှိတော့。
    #    reference တိုင်းချက် (၂၀၂၆-၀၉-၂၀ · `assets/calib/ref_hype_2026.json`):
    #    တိတ်ဆိတ်မှု အလယ်တန်း **၀.၁၆s** · ၀.၄၅s ကျော် **၁၀ နေရာသာ** ရှိပြီး
    #    စာသားက **စကားပြောနေတုန်း ၃၅% ပေါ်နေ**သည် ⇒ ပုံစံ ဒီလို လိုချင်လျှင်
    #    တိတ်ဆိတ်မှုကို စောင့်၍ မရ。 ⇒ style က `gfx_in_speech` ပေးလျှင်
    #    အချိန် အညီအမျှ နေရာချသည် (တိတ်ဆိတ်မှု နီးလျှင် အဲဒီဆီ ကပ်ပေးသည်)。
    _minsil = float(rc.get("gfx_min_sil") or 0.45)
    cand = sorted([s for s in sil if s[1]-s[0] >= _minsil], key=lambda s: -(s[1]-s[0]))
    cand = [s for s in cand if 2.0 <= s[2] <= dur-3.0]
    if rc.get("gfx_in_speech") and len(cand) < want:
        # အချိန် အညီအမျှ အမှတ်များ — တိတ်ဆိတ်မှု ရှိလျှင် အနီးဆုံးဆီ ရွှေ့
        grid = [2.0 + (dur-5.0) * (k+0.5)/want for k in range(want)]
        near = sorted(sil, key=lambda s: s[2]) if sil else []
        out = []
        for g in grid:
            best = min(near, key=lambda s: abs(s[2]-g)) if near else None
            out.append(best if (best and abs(best[2]-g) <= 1.2) else (g, g, g))
        cand = out
    if not cand: return []
    # အချိန် အညီအမျှ ဖြန့် — အစုအစု မဖြစ်စေရန်
    cand.sort(key=lambda s: s[2])
    step = max(1, len(cand)//max(1,want))
    picked = cand[::step][:want]
    # ⚠️ အရင်က template **၁၂ ခု**ကို hardcode လုပ်ပြီး အလှည့်ကျ သုံးခဲ့သည် —
    #    motionkit မှာ ၂၇၆ ခု ရှိပါလျက်。 ထုတ်လာတဲ့ ဗီဒီယိုတိုင်း တစ်ပုံစံတည်း
    #    ဖြစ်စေခဲ့သည်。
    # ⚠️ ဒါပေမဲ့ **တကယ် render စမ်းပြီးသားကိုသာ** သုံးရမည် — argument ပုံစံ
    #    တစ်ခုချင်း ကွာသဖြင့် အားလုံးက အလိုအလျောက် ဖြည့်လို့ မရ。
    #    `assets/gfx_ok.txt` = တစ်ခုချင်း သီးသန့် process နဲ့ စမ်းပြီး
    #    အောင်မြင်ခဲ့သော စာရင်း (၅၉/၁၉၄)。
    # ⚠️ **ဗီဒီယိုတိုင်း တူတူ မဖြစ်စေရ**。 အရင်က `random.Random(7)` ပုံသေ seed
    #    နဲ့ ရောပြီး `KINDS[i % len]` က အမြဲ ၀ ကနေ စခဲ့သဖြင့် — pool ၂၈၄ ခု
    #    ရှိပါလျက် **ဗီဒီယိုတိုင်း တူညီသော ၁၀ ခု** ပဲ ထွက်ခဲ့သည်
    #    (Zin ၂၀၂၆-၀၉-၁၉: 「Template ၄၀၀ ကျော် ရှိပါတယ်။ အဲဒါတွေ တကယ် သုံးပေးပါ」)。
    #    ⇒ job id ကနေ seed ယူသည် — ဗီဒီယိုတိုင်း ကွဲပြားပြီး **တစ်ပုဒ်တည်းကို
    #      ပြန်ထုတ်လျှင် တူညီ**သည် (ပြန်စစ်လို့ ရရန်)。
    KINDS = _verified(rc.get("_seed")) or ["headline_bar","locator","big_number","pull_quote",
             "label_pill","kicker_title","section","chapter","stat_title",
             "fact_box","list_title","topic_bar"]
    out = [dict(at=round(s[2],2), kind=KINDS[i % len(KINDS)])
           for i,s in enumerate(picked)]
    # ⚠️ **explainer insert ကို သီးသန့် နှုန်းနဲ့ ချသည်** (၂၀၂၆-၀၉-၂၀)。
    #    Zin ရဲ့ reference (KCN4-2hyUBM) မှာ မြင်ကွင်း လုံးဝပြောင်းမှု
    #    **၂.၅/မိနစ်** (၁၃:၀၂ မှာ ၃၃ ခါ)。 ကျပန်း ရွေးလျှင် ပေါ်ချင်မှ ပေါ်မည်
    #    ⇒ နေရာ အညီအမျှ ချပြီး insert template ကို **အတင်း သတ်မှတ်**သည်。
    return apply_inserts(out, rc, dur, log=log)


def apply_inserts(out, rc, dur, log=None):
    """ရွေးပြီးသား ဂရပ်ဖစ် စာရင်းထဲ **explainer insert** ကို နှုန်းအလိုက် ထည့်သည်。

    ⚠️ **လမ်းကြောင်း ၂ ခု ရှိသည်** — `pick()` က ပြန်ဆုတ်လမ်းသာ、အဓိကလမ်းက
       `worker/run.py` ရဲ့ Gemini ခေါင်းစဉ် loop ဖြစ်သည်。 ၂၀၂၆-၀၉-၂၀ မှာ
       `pick()` ထဲမှာပဲ ရေးမိ၍ ref-talk render မှာ insert **တစ်ခုမှ မဝင်**ခဲ့。
       ⇒ ဒီ function ကို **နှစ်လမ်းစလုံးက ခေါ်ရမည်**。
    """
    ins_pm = rc.get("insert_per_min")
    if ins_pm and out:
        KINDS = _verified(rc.get("_seed")) or []
        pool = [k for k in KINDS if k in INSERT_KINDS] or list(INSERT_KINDS)
        # ⚠️ **ဂရပ်ဖစ် အားလုံးကို insert မဖြစ်စေရ**。 ၂၀၂၆-၀၉-၂၀ စမ်းသပ်ချက်:
        #    knowledge (gfx ၁၀) မှာ ၁၀ ခုလုံး insert ဖြစ်သွားပြီး ပုံစံ
        #    ကွဲပြားမှု လုံးဝ ပျောက်ခဲ့သည်。 ⇒ ဂရပ်ဖစ်ရဲ့ ၄၀% ထက် မပိုရ。
        # ⚠️ reference ရဲ့ ၂.၅/မိနစ် က **မြင်ကွင်း ပြောင်းမှု အားလုံး** (B-roll ပါ)
        #    ဖြစ်၍ explainer insert တစ်ခုတည်းနဲ့ မပြည့်နိုင်ပါ。 `gfx` နည်းလျှင်
        #    ရနိုင်သလောက်သာ ရသည် — log မှာ အမှန်အတိုင်း ပြသည်。
        n = int(round(float(ins_pm) * dur / 60.0))
        n = max(1, min(int(len(out) * 0.40) or 1, n))
        step = len(out) / float(n)
        for j in range(n):
            g = out[int(j * step)]
            g["kind"] = pool[j % len(pool)]
            # ⚠️ `args` က **မူလ template အတွက်** တွက်ထားသည် — kind ပြောင်းလျှင်
            #    မကိုက်တော့。 ရှင်းပစ်လျှင် `track()` က template အလိုက်
            #    ပြန်တွက်သည် (`a = g.get("args") or …`)。
            g["args"] = None
        # ⚠️ **တောင်းသော နှုန်းနဲ့ ရသော နှုန်း ကွာလျှင် ဖော်ပြရမည်**。
        #    podcast က gfx ၂ ခုသာ ရှိ၍ ၂.၅/မိနစ် တောင်းလည်း ~၀.၁ ပဲ ရသည် —
        #    မပြလျှင် ဆက်တင်က အလုပ်လုပ်နေသလို ထင်ရမည် (တိတ်တဆိတ် ကျရှုံးမှု)。
        if log:
            got = n / (dur / 60.0) if dur > 0 else 0.0
            msg = (f"  insert {n} ခု · {got:.1f}/မိနစ် (တောင်း {float(ins_pm):.1f}) "
                   f"· ဂရပ်ဖစ် {len(out)} ခုရဲ့ {n / len(out) * 100:.0f}%")
            if got < float(ins_pm) * 0.75:
                msg += " ⚠️ ဂရပ်ဖစ် နည်း၍ မပြည့်ပါ — `gfx` တင်မှ ရမည်"
            log(msg)
    return out

_VER = None
_RAW = None
def _verified(seed=None):
    """စမ်းပြီးသား template စာရင်း — id ("titles.title_card") မှ fn နာမည်သို့

    `seed` ပေးလျှင် **အဲဒီ seed အလိုက် ရောပြီး** ပြန်ပေးသည် ⇒ ဗီဒီယို
    တစ်ပုဒ်ချင်း template ကွဲပြားသည်。 seed မပါလျှင် ယခင်အတိုင်း。
    """
    global _VER, _RAW
    if seed is not None:
        if _RAW is None: _verified()          # _RAW ဖြည့်ရန်
        import random as _r
        out = list(_RAW or [])
        _r.Random(str(seed)).shuffle(out)
        return out
    if _VER is not None: return _VER
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "assets", "gfx_ok.txt")
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            # ⚠️ `#` မှတ်ချက်ကြောင်းကို **ကျော်ရမည်** — မကျော်လျှင် မှတ်ချက်ထဲက
            #    "၀.၀၅%" လို အစက်ပါသော စာသားကို template နာမည် ဟု မှတ်ပြီး
            #    "template မတွေ့" ဖြင့် ကျသည် (၂၀၂၆-၀၉-၁၉)。
            if not line or line.startswith("#") or "." not in line: continue
            out.append(line.split(".", 1)[1])
    except OSError:
        pass
    # ⚠️ အလှည့်ကျ သုံးသဖြင့် စာရင်းကို **ရောရမည်** — မရောလျှင် ဗီဒီယိုတိုင်း
    #    ပထမ ၅ ခုပဲ သုံးပြီး ကွဲပြားမှု မရှိဘူး。
    _RAW = list(out)
    import random
    random.Random(7).shuffle(out)
    _VER = out
    return _VER

# ── SFX ─────────────────────────────────────────────────────
# ⚠️ cue ကို ဂရပ်ဖစ် **အပြည့်ပေါ်တဲ့ အချိန်**နဲ့ ကိုက်ရမည်၊ စတဲ့အချိန် မဟုတ်။
#    settle ချိန်ကို နုတ်ရသည် — မနုတ်လျှင် အသံက ပုံထက် စောသည်。
SETTLE = 0.22


# ── template အလိုက် SFX ─────────────────────────────────────
# ⚠️ အရင်က ဂရပ်ဖစ် **တိုင်း**ကို `whoosh_in` တစ်မျိုးတည်း တွဲထားခဲ့သည် —
#    role ၂၂ မျိုး ရှိပါလျက် (Zin ၂၀၂၆-၀၉-၁၉: 「လိုက်ဖတ်တဲ့ sound effect နဲ့တွဲ」)。
#    ⇒ template ရဲ့ **လှုပ်ရှားပုံ**နှင့် ကိုက်အောင် module အလိုက် တွဲသည်。
# ⚠️ အရေအတွက် **မတိုးစေရ** — ဂရပ်ဖစ် တစ်ခုလျှင် အသံ တစ်ထပ် အတိုင်းပင်。
#    (QC `sfx_density` ≤ playbook · `sfx_spacing` ≥ ၈s ဂိတ်များ မပျက်စေရန်)
# ⚠️ explainer insert — `insert.py` (motionkit) ရဲ့ template များ。
INSERT_KINDS = ("insert_label", "insert_flow")

SFX_BY_MOD = {
    # စာတန်း ကတ် — လေ သွားသံ · နက်ရှိုင်း
    "titles": ("whoosh_in", "click"),   "titles2": ("whoosh_in", "click"),
    "titles3": ("deep_whoosh", "latch"), "prem": ("deep_whoosh", "latch"),
    "prem2": ("riser_soft", "latch"),    "prem3": ("deep_whoosh", "click"),
    "qcard": ("whoosh_in", "snap"),      "cine": ("riser_air", "deep_hit"),
    # စက်ရုပ် စာရိုက် — ခလုတ် သံ
    "typew": ("type_tick", "type_key"),
    # စာလုံး လှုပ်ရှား — မြန်ဆန် သွက်လက်
    "typo": ("swipe", "pop"),            "typo2": ("swipe", "pop"),
    "kinetic": ("swipe", "click"),       "kinetic2": ("swipe_metal", "pop"),
    "kinetic3": ("swipe", "pop"),        "kin4": ("swipe_metal", "click"),
    "capt": ("pop", "click"),
    # အထူး အာနိသင်
    "glitch": ("glitch", "radio"),       "retro": ("shutter", "click2"),
    "social": ("snap", "pop"),
    # ကိန်းဂဏန်း / ဇယား — ရေတွက် သံ
    "infogfx": ("pop", "type_tick"),     "charts": ("swipe", "type_tick"),
    "dash": ("latch", "type_tick"),      "odo": ("type_tick", "click"),
    "callouts": ("pop", "click"),        "maps": ("deep_whoosh", "latch"),
    "brows": ("click2", "pop"),          "mockups": ("snap", "click"),
}
SFX_DEF = ("whoosh_in", "click")

_MODOF = None
def _mod_of(kind):
    """fn နာမည် ("title_card") → module နာမည် ("titles")"""
    global _MODOF
    if _MODOF is None:
        _MODOF = {}
        try:
            import gfxcat as _G
            for e in _G.catalog(): _MODOF[e["fn"]] = e["module"]
        except Exception: pass
    return _MODOF.get(kind)


def sfx_for(kind):
    """template တစ်ခုအတွက် (ရှေ့သံ, ထပ်သံ)"""
    return SFX_BY_MOD.get(_mod_of(kind) or "", SFX_DEF)

def sfx(gfx, caps, rc):
    """[(offset, role, dB)] — sfxlib ရဲ့ role နာမည်များ"""
    out=[]
    for g in gfx:
        a, b = sfx_for(g.get("kind") or "")
        out.append((max(0.0, g["at"]-SETTLE), a, -13))
        out.append((g["at"], b, -16))
    # ⚠️ စာတန်းတိုင်းမှာ အသံ မထည့်ရ — Zin ရဲ့ spec: "no per-word SFX"
    if rc.get("captions") == "big" and caps:
        for c in caps[:6]:
            out.append((c["start"], "type_tick", -20))
    out.sort(key=lambda x: x[0])
    # ⚠️ playbook က style တစ်ခုချင်း **မိနစ်လျှင် ဘယ်နှစ်ချက်** သတ်မှတ်သည် —
    #    podcast ၀.၃ · ZAE short ၂၀ — ၆၀ ဆ ကွာသည်。 ကန့်သတ် မထားလျှင်
    #    ဂရပ်ဖစ် အရေအတွက်အလိုက် ပဲ ဖြစ်ပြီး ပုံစံ ကွဲမသွားဘူး。
    #    ⚠️ playbook: "SFX ကို သတိထားမိလောက်အောင် ကြားရရင် ၆ dB ကျယ်နေပြီ"
    per = rc.get("sfx_per_min")
    dur = rc.get("_dur") or 0
    if per is None or dur <= 0 or not out:
        return out

    # ⚠️ **အထပ်ကို မခွဲရ**。 whoosh_in နဲ့ click က ဂရပ်ဖစ်တစ်ခုအတွက်
    #    အသံ **တစ်ခု၏ အထပ်နှစ်ခု** ဖြစ်သည် (0.22s ကွာ)。 အရင်က စာရင်း
    #    ပြားပြားကနေ N ခုခြား ယူခဲ့သဖြင့် whoosh ကျန်ပြီး click ပျောက်တာမျိုး
    #    ဖြစ်နိုင်ခဲ့သည် — အသံက မပြည့်စုံဘဲ ထောက်နေမည်。
    # ⚠️ ကိန်းများကို **ဒီမှာ မရေးတော့ပာ** — `qc.py` နဲ့ ထပ်နေလျှင်
    #    တစ်ခု ပြင်ပြီး နောက်တစ်ခု မပြင်မိလျှင် generator နဲ့ gate ကွဲသွားပြီး
    #    render ပြီးမှ ကျဘမ်း ဖြစ်သည် (တကန် ဖြစ်ခဲ့)。
    try:
        import sfxpol as _PL
    except ImportError:
        from core import sfxpol as _PL
    _pol = _PL.for_recipe(rc)
    LAYER_W = _pol["layer"]
    moments = []
    for c in out:
        if moments and c[0] - moments[-1][0] <= LAYER_W:
            moments[-1][1].append(c)
        else:
            moments.append((c[0], [c]))

    # ⚠️ အသံနှစ်ခု **၈ စက္ကန့်အတွင်း မရှိရ** (playbook P3 · QC gate ကလည်း
    #    ဒီအတိုင်း စစ်သည်)。 generator က မလိုက်နာလျှင် render ပြီးမှ QC မှာ
    #    ကျဘမ်း ဖြစ်ပြီး အလုပ်အားလုံး အလကား ဖြစ်သည် (တကယ် ဖြစ်ခဲ့)。
    MIN_GAP = _pol["gap"]
    keep, last = [], None
    for at, layers in moments:
        if last is None or at - last >= MIN_GAP:
            keep.append((at, layers)); last = at

    # ⚠️ **`round` မသုံးရ — အောက်သို့ ဖြတ်ရမည်**。 `round` က တောင်းထားသော
    #    နှုန်းထက် **ကျော်သွားစေနိုင်**သည်: ၁.၅/မိနစ် × ၇၇.၇s = ၁.၉၄ → ၂ ခု
    #    ⇒ တိုင်းလိုက်တော့ ၁.၅၄၅/မိနစ် ဖြစ်ကာ QC ဂိတ် (≤၁.၅) ကျခဲ့သည်
    #    (၂၀၂၆-၀၉-၂၀ j_f5bd998f5ca3)。 အောက်ဖြတ်လျှင် ဘယ်တော့မှ မကျော်ပါ。
    # ⚠️ `budget()` က အောက်ခြေ ံ၀s အနည်းဆုံး ထားသည် — မျှ မရှိလျှင်
    #    ၄၀s အောက် ဗီဒီယိုတိုင်းမှာ SFX **သုည** ပဲ ထွက်သည် (တိုင်းပြီး တွေ့)。
    cap = _PL.budget(dict(_pol, per_min=per), dur)
    if cap == 0: return []
    if len(keep) > cap:
        step = len(keep) / float(cap)
        keep = [keep[int(i * step)] for i in range(cap)]

    out = [c for _at, layers in keep for c in layers]
    out.sort(key=lambda x: x[0])
    return out

def mix(base, cues, out, cue_path, log=print, stem=None):
    """SFX များကို အသံပေါ် ထပ်သည်。

    ⚠️ input ၁၄၀ ကန့်သတ်ချက် — cue များကို **အုပ်စုလိုက် ခွဲ**ပြီး ပေါင်းရသည်。
    """
    import subprocess
    ins=[]; fc=[]; k=0
    use=[]
    # ⚠️ `cue_path` ကို **(role, index)** နဲ့ ခော်သည် — index မပာလျှင်
    #    variant selector က ခွဲပြားမှု မရပှိ ⇒ အသံ တစ်မျိုးတည်း ထပ်ကာထပ်ကာ
    #    ကြားရမည် (၁၆ ငှစ်ကျိပ်မှာ whoosh တစ်မျိုးတည်း — တကန် ဖြစ်ခဲ့)。
    #    ⚠️ ရှေ့ ပုံစံ (role တစ်ကြောင်းတည်း) ကိုလည်း ထက်ပံ့ပိုင်း ပြီးသား ထားသည်。
    import inspect as _in
    try:
        _two = len(_in.signature(cue_path).parameters) >= 2
    except (TypeError, ValueError):
        _two = False
    for _i, (at, role, db) in enumerate(cues):
        r = cue_path(role, _i) if _two else cue_path(role)
        # ⚠️ callback က `(path, lead)` ပြန်ပေးနိုင်သည် — `lead` က အသံ ကျယ်ချိန်
        #    ကို ဖြစ်ရပ်နဲ့ ကိုက်စေရန် စောထည့်ရမည့် ပမာန。 riser ကို cue အစား
        #    ထည့်လျှင် ၁.၇s နောက်ကျမှ အသံ အကျယ်ဆုံး ရောက်သည်。
        #    ⚠️ အောက်က သုည်အောက် မရောက်ရ — adelay က အနျက်ကို မလုပ်နိုင်。
        _ld = 0.0
        if isinstance(r, (tuple, list)):
            p = r[0]
            _ld = float(r[1] or 0.0) if len(r) > 1 else 0.0
        else:
            p = r
        if p and os.path.exists(p):
            use.append((max(0.0, float(at) - _ld), p, db))
    if not use:
        subprocess.run(["ffmpeg","-v","error","-y","-i",base,"-c","copy",out],check=True)
        return out, 0
    # ⚠️ lead ကြောင့်် အစီအစစ်ဉ် ပြောင်းနိုင်သည် ⇒ အချိန်အလိုက် ပြန်စီသည်
    use.sort(key=lambda x: x[0])
    use = use[:60]                      # ⚠️ ကန့်သတ် — ၆၀ ထက် ပို မလို
    for i,(at,p,db) in enumerate(use):
        ins += ["-i",p]; ms=int(at*1000)
        fc.append(f"[{i+1}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                  f"volume={db}dB,adelay={ms}|{ms}[s{i}]")
    fc.append("[0:a]" + "".join(f"[s{i}]" for i in range(len(use))) +
              f"amix=inputs={len(use)+1}:normalize=0:dropout_transition=0,"
              f"alimiter=limit=0.94[a]")
    # ⚠️ **SFX stem** — `nsfx` က ဖိုင် ရှိမရှိ ရေတွက်ချက်သာ ဖြစ်၍
    #    **တကယ် ကြားရလား** မသိရပါ。 SFX ချည်းသက်သက် ထုတ်ထားလျှင်
    #    cue တစ်ခုချင်းကို ပြန်တိုင်း၍ အတည်ပြုလို့ရသည် (audit: stem ထုတ်ရန်)。
    if stem:
        fcs = list(fc[:-1]) + ["" .join(f"[s{i}]" for i in range(len(use)))
                               + (f"amix=inputs={len(use)}:normalize=0:"
                                  f"dropout_transition=0[sx]"
                                  if len(use) > 1 else "anull[sx]")]
        if len(use) == 1:
            fcs[-1] = "[s0]anull[sx]"
        try:
            subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi",
                "-i",f"anullsrc=r=48000:cl=stereo:d=0.01"]+ins+
                ["-filter_complex",";".join(fcs),"-map","[sx]",
                 "-c:a","pcm_s16le",stem],check=True)
        except Exception as _e:
            log and log(f"  ⚠️ SFX stem မထွက် ({type(_e).__name__})")
    subprocess.run(["ffmpeg","-v","error","-y","-i",base]+ins+
        ["-filter_complex",";".join(fc),"-map","0:v","-map","[a]",
         "-c:v","copy","-c:a","aac","-b:a","192k",out],check=True)
    return out, len(use)


def stem_check(stem, cues, log=None):
    """stem ကနေ cue တစ်ခုချင်း **တကယ် ကြားရလား** တိုင်းသည်

    `(ok, [(at, role, dB)])` — `ok` က ကြားရသော အရေအတွက်、စာရင်းက မကြားရတာ

    ⚠️ `nsfx` က **ဖိုင် ရှိမရှိ** ရေတွက်ချက်သာ。 ဖိုင် ရှိပြီး အသံ မရှိတာ ·
       အချိန် လွဲတာ · အားလုံး လျှော့ခံရတာ ဘယ်တော့မှ မဖမ်းမိပါ。
    """
    if not stem or not os.path.exists(stem) or not cues:
        return 0, []
    try:
        import numpy as _np
    except ImportError:
        return 0, []
    import subprocess
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", stem, "-ac", "1",
                        "-ar", "8000", "-f", "f32le", "-"], capture_output=True)
    x = _np.frombuffer(r.stdout, "<f4").astype(_np.float64)
    if not len(x):
        return 0, [tuple(c)[:3] for c in cues]
    sr, bad, ok = 8000, [], 0
    for c in cues:
        at, role, db = (list(c) + [None, None, None])[:3]
        a = int(max(0.0, float(at) - 0.25) * sr)
        b = min(len(x), int((float(at) + 0.75) * sr))
        if b <= a:
            bad.append((at, role, db)); continue
        pk = 20 * _np.log10(max(1e-6, float(_np.abs(x[a:b]).max())))
        if pk < -60.0:
            bad.append((at, role, db))
            log and log(f"    ⚠️ SFX {at:6.2f}s {role} — stem ထဲ အသံ မရှိ "
                        f"({pk:.0f} dB)")
        else:
            ok += 1
    return ok, bad


# ── ဂရပ်ဖစ် alpha track ─────────────────────────────────────
ARGS = {
 "headline_bar": lambda b,r: ("သတင်း", b),
 "locator":      lambda b,r: (b, r),
 "big_number":   lambda b,r: ("100%", b, r),
 "pull_quote":   lambda b,r: (b, r),
 "label_pill":   lambda b,r: (b,),
 "kicker_title": lambda b,r: (r, b),
 "section":      lambda b,r: (b,),
 "chapter":      lambda b,r: ("၀၁", b),
 "stat_title":   lambda b,r: ("100%", b),
 "fact_box":     lambda b,r: (b, r),
 "list_title":   lambda b,r: (b, [r, "—", "—"]),
 "topic_bar":    lambda b,r: (b,),
}

def _ybox(el, H):
    """element ရဲ့ ဒေါင်လိုက် အကွာအဝေး (alpha bbox)。"""
    y0, y1 = H, 0
    try:
        import numpy as _np
        from PIL import Image as _Im
        seq = list(el["anim"][len(el["anim"])//2:]) + \
              [(q, x, y) for q, x, y, _d in el.get("statics", [])]
        for _p, _x, _y in seq:
            _a = _np.asarray(_Im.open(_p).convert("RGBA"))[:, :, 3]
            _ys = _np.nonzero(_a.max(axis=1) > 8)[0]
            if len(_ys):
                y0 = min(y0, _y + int(_ys.min())); y1 = max(y1, _y + int(_ys.max()))
    except Exception:
        return 0, int(H*0.32)
    if y1 <= y0: return 0, int(H*0.32)
    return max(0, int(y0)), min(int(H), int(y1))


def _yparam(fn):
    """template က နေရာ ရွှေ့လို့ရသော param ရှိလား (`cy` · `y`)。"""
    import inspect
    try: ps = inspect.signature(fn).parameters
    except Exception: return None
    for k in ("cy", "y"):
        if k in ps: return k
    return None


# ⚠️ card ကျော်သွားရခြင်း အကြောင်းရင်းကို **ရေတွက်ရမည်** — "ရွေး ၈ · တပ်ပြီး ၅"
#    ဆိုပြီး ဘာလို့ ၃ ခု ပျောက်လဲ မပြနိုင်ခဲ့。 render report အတွက် ဒီမှာ စုသည်。
LAST = {}


class _PackDone(Exception):
    """pack element ဆောက်ပြီးသား — ပုံမှန် builder ကို ကျော်ရန်"""


def track(gfx, out, work, W, H, fps, T1, T2, brand, label, log=print,
          avoid=None, capy=None, hold=None):
    """ရွေးထားသော ဂရပ်ဖစ်များကို alpha overlay ဗီဒီယို **တစ်ခု** အဖြစ် ဆောက်သည်。

    ⚠️ template တစ်ခုလျှင် PNG ၈၀–၂၀၀ ရှိသည်。 အားလုံး input အဖြစ် ထည့်လျှင်
       ffmpeg ပျက်သည် ⇒ တစ်ခုချင်း အရင် alpha .mov လုပ်ပြီး concat လုပ်ရသည်。
    """
    import subprocess
    os.makedirs(work, exist_ok=True)
    blank = os.path.join(work, "_g0.png")
    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi",
        "-i",f"color=c=black:s=16x16:d=1","-frames:v","1","-pix_fmt","rgba",blank],check=True)
    made=[]
    LAST.clear()
    LAST.update(want=len(gfx), no_template=0, build_fail=0,
                no_room=0, out_of_frame=0, overlap=0, moved=0, placed=0)
    for i,g in enumerate(gfx):
        # ⚠️ အရင်က module ၂ ခု (titles · titles2) ထဲမှာပဲ ရှာသဖြင့်
        #    typo · kinetic · callouts · infogfx ထဲက template တွေ
        #    **တိတ်တဆိတ် ပယ်ခံခဲ့ရသည်** — "ရွေး ၈ ခု · တပ်ပြီး ၂ ခု"
        #    ဆိုပြီး အကြောင်းရင်း မပြဘူး。 ⇒ catalog ကနေ ရှာသည်。
        # ⚠️ **pack template က သီးသန့် လမ်းကြောင်း** — `cards.py` ကို
        #    ခေါ်ပြီး pack ရဲ motion token နဲ့ animation ဆောက်သည်。
        #    မချိတ်လျှင် pack က verify ပြီးသား ဖြစ်ပါလျက်
        #    **ဗီဒီယိုထဲ ဘယ်တော့မှ မပေါ်ဘူး**。
        if str(g.get("kind", "")).startswith("headtop."):
            # ⚠️ **လဲလိုက်သော graphic မှာ `props` မရှိပါ** — `pick()` က
            #    `at`/`kind` သာ ပေးသည် ⇒ စာသား ဗလာ ဖြစ်ပြီး အနားသတ်
            #    **ဗလာ ကွက်** ထွက်မည် (၂၀၂၆-၀၉-၂၁ ဖမ်းမိ)。
            #    ⇒ legacy လမ်းကြောင်းနဲ့ တူညီစွာ brand/label ကနေ ဖြည့်သည်。
            _pp = dict(g.get("props") or {})
            if not _pp:
                _pp = _pack_fill(g["kind"], g.get("text"))
            if not _pp:
                # ⚠️ **အဓိပ္ပာယ်မဲ့ ဂရပ်ဖစ်ထက် မရှိတာက ကောင်း**သည် —
                #    အကြောင်းအရာ စာသား မရလျှင် recipe နာမည် တင်မိမည်。
                LAST["no_args"] = LAST.get("no_args", 0) + 1
                log(f"  ⊘ {g['kind']} @ {g.get('at',0):.1f}s — "
                    f"အကြောင်းအရာ စာသား မရှိ၍ မထည့်ပါ")
                continue
            # ⚠️ တစ်မျိုးတည်း ထပ်နေလျှင် **နေရာ ပြောင်း**ပေးသည် —
            #    ၄ ခုလုံး အလယ်မှာ ပေါ်လျှင် တစ်ပုံစံတည်း ဖြစ်သည်。
            _pp.setdefault("cy", (0.30, 0.42, 0.62, 0.72)[i % 4])
            el = pack_el(g["kind"], _pp, work, f"g{i}", W, H, fps=fps,
                         dur=(hold or None), log=log)
            if el is None:
                LAST["build_fail"] += 1
                log(f"  ⊘ pack ဆောက်မရ: {g['kind']} @ {g.get('at',0):.1f}s")
                continue
            fn = None
        else:
            el = None
            fn = (getattr(T2, g["kind"], None) or getattr(T1, g["kind"], None)
                  or _fn(g["kind"]))
        if el is None and not fn:
            LAST["no_template"] += 1
            log(f"  ⊘ template မတွေ့: {g['kind']} @ {g.get('at',0):.1f}s "
                f"(catalog {len(_CIDX or {})} ခု)")
            continue
        try:
            if el is not None:
                raise _PackDone
            # ⚠️ topics.py က args ပေးလာလျှင် **အဲဒါကို** သုံးရမည် —
            #    အကြောင်းအရာနဲ့ ကိုက်တဲ့ စာသားပါ。
            # ⚠️ ARGS မှာ ၁၂ ခုပဲ ရှိ — စမ်းပြီးသား ၅၉ ခုအတွက် catalog ရဲ့
            #    signature ကနေ ဖြည့်ရမည်。 မဖြည့်ဘဲ (b,) ပေးလျှင် template
            #    အများစု ကျဘမ်း ဖြစ်မည်。
            a = g.get("args") or (ARGS[g["kind"]](brand, label)
                                  if g["kind"] in ARGS else _cargs(g["kind"], brand, label))
            if not a:
                # ⚠️ **မှန်းဆ မဖြည့်ရ** — ကျော်သွားတာကို အကြောင်းရင်းနဲ့ ပြသည်
                LAST["no_args"] = LAST.get("no_args", 0) + 1
                log(f"  ⊘ argument မဖြည့်နိုင်: {g['kind']} @ {g.get('at', 0):.1f}s "
                    f"(ဂဏန်း/စာရင်း param လိုသည်)")
                continue
            # ⚠️ titles/titles2 ရဲ့ template တွေက ပထမ param အဖြစ် `tag`
            #    ယူသည်၊ typo · kinetic · callouts တွေက **မယူ**。 tag ကို
            #    အားလုံးမှာ ရှေ့က ထည့်လျှင် argument တစ်နေရာစီ ရွေ့သွားပြီး
            #    စာသားက number param ထဲ ကျသည် ("can't multiply sequence by
            #    non-int" · "invalid literal for int()" — တကယ် ဖြစ်ခဲ့)。
            # ⚠️ renderer v2 (60fps · motion blur) သုံးမည်ဆိုလျှင် builder ကိုပါ
            #    60fps နဲ့ ဆောက်ရသည် — 30fps ဖရိမ်တွေနဲ့ blur မထွက်。
            _r = _r2()
            if _r is not None:
                with _r.hifps(60):
                    el = fn(f"g{i}", *a) if _wants_tag(g["kind"]) else fn(*a)
            else:
                el = fn(f"g{i}", *a) if _wants_tag(g["kind"]) else fn(*a)
        except _PackDone:
            pass
        except Exception as e:
            LAST["build_fail"] += 1
            log(f"  ⊘ ဆောက်မရ: {g['kind']} @ {g.get('at',0):.1f}s "
                f"{type(e).__name__}: {e}"); continue
        # ⚠️ **မျက်နှာကို မဖုံးရ** — Zin: "Infography ကိုမျက်နှာကိုမဖုန်းစေနဲ့
        #    သေချာ Fitting ကျမည့်နေရာကို ရွေးပြီးလုပ်စေချင်တယ်"。
        # ⚠️ template ရဲ့ `y`/`cy` param ကို မှီခို၍ **မရ** — အများစုမှာ မရှိ။
        #    ⇒ element တစ်ခုလုံးကို **ဒေါင်လိုက် ရွှေ့**သည် (alpha overlay
        #      ဖြစ်၍ ရွှေ့လို့ ရသည်)。 N5 က ဂရပ်ဖစ်ကို ခေါင်းအထက်
        #      နံရံဗလာမှာ ချသည် ⇒ အပေါ်ကို ဦးစားပေး。
        dy = 0
        # ⚠️ **အနားသတ်သာ template က မျက်နှာပေါ် တင်လို့ရသည်**。 pack ရဲ့
        #    `safeZones.subject: true` က 「အတွင်း ပွင့်လင်း ⇒ ပြောသူ
        #    မြင်နေရသည်」 ဟု ဆိုလိုသည် (pack.json မှတ်ချက်)。 ဒါကို
        #    မျက်နှာဇုန်နဲ့ ပယ်လျှင် headtop မှာ **ဘယ်တော့မှ မပေါ်**ဘူး —
        #    မျက်နှာ ၀–၆၄% နဲ့ စာတန်း ၇၀% ကြားမှာ ၆၁px သာ ကျန်၍。
        if avoid and _over_subject(g.get("kind")):
            log(f"  ⊙ {g['kind']} — အနားသတ်သာ ⇒ မျက်နှာပေါ် ခွင့်ပြု")
            avoid2 = None
        else:
            avoid2 = avoid
        if avoid2:
            ay0, ay1 = avoid2
            _y0, _y1 = _ybox(el, H)
            ih = _y1 - _y0
            TOP = int(H*0.075)
            if _y1 > ay0:                       # မျက်နှာဇုန်ထဲ ဒါမှမဟုတ် အောက်
                if ih <= ay0 - TOP - 8:         # ခေါင်းအထက် ဝင်လျှင် — အပေါ်
                    dy = TOP - _y0
                elif capy and (ay1 + 16 + ih) <= capy - 12:
                    dy = (ay1 + 16) - _y0       # မဝင်လျှင် — မျက်နှာအောက်
                elif (ay1 + 16 + ih) <= H - 12:
                    dy = (ay1 + 16) - _y0
                else:
                    LAST["no_room"] += 1
                    log(f"  ⊘ နေရာ မတည့်: {g['kind']} @ {g.get('at',0):.1f}s "
                        f"(ကတ်အမြင့် {ih} · မျက်နှာဇုန် {ay0}–{ay1} · "
                        f"စာတန်းထိပ် {capy} · ဘောင်အမြင့် {H})")
                    continue
                # ဘောင်ထဲ ဝင်မဝင် စစ်
                if _y0 + dy < 0 or _y1 + dy > H:
                    LAST["out_of_frame"] += 1
                    log(f"  ⊘ ဘောင်ကျော်: {g['kind']} @ {g.get('at',0):.1f}s "
                        f"(y {_y0+dy}–{_y1+dy} · dy={dy} · ဘောင် {W}×{H})")
                    continue
        seq = os.path.join(work, f"g{i}_%04d.png")
        # ⚠️ os.link က filesystem ကွဲလျှင် ပျက်သည် — copy ဖြင့် ပြန်ဆုတ်ရမည်
        import shutil as _sh
        for k,(p,x,y) in enumerate(el["anim"]):
            dst = seq % k
            if os.path.exists(dst): continue
            try: os.link(p, dst)
            except OSError: _sh.copyfile(p, dst)
        ax, ay = el["anim"][0][1], el["anim"][0][2] + dy
        ins=["-framerate",str(fps),"-i",seq]
        fc=[f"[0:v]pad={W}:{H}:{ax}:{max(0,ay)}:color=black@0[b0]"]; last="b0"; n=0
        for p,x,y,d in el["statics"]:
            ins += ["-loop","1","-i",p]; n+=1
            fc.append(f"[{last}][{n}:v]overlay={x}:{y+dy}:enable='gte(t,{d:.2f})'[b{n}]")
            last=f"b{n}"
        y0, y1 = _ybox(el, H); y0 += dy; y1 += dy
        mov = os.path.join(work, f"g{i}.mov")
        # ⚠️ ကတ်ကို **ကြာကြာ ရပ်စေရန်** — template ရဲ့ ကိုယ်ပိုင် အရှည်က
        #    ~၂.၂s ပဲ ရှိသည်。 reference ရဲ့ full-screen slide က ကြာကြာ
        #    ရပ်နေသဖြင့် gfx_share ၁၃–၁၄% ရသည် — ကတ် ၂.၂s တွေ အများကြီး
        #    လျှပ်တပြက် ပြ၍ မရ (၅၄ ခု လိုမည်、ပုံစံ လုံးဝ ကွဲသွားမည်)。
        #    ⇒ နောက်ဆုံး frame ကို `tpad` နဲ့ ဆွဲထားသည်。
        gdur = float(el["dur"])
        fc2 = list(fc); last2 = last
        # ⚠️ **event တစ်ခုချင်း** ရပ်ချိန် ပေးလို့ ရရမည် — plan (`execute.py`)
        #    က event တစ်ခုချင်း `startTime`/`endTime` ပေးသည်。 မရှိလျှင်
        #    ယခင်အတိုင်း global `hold`。
        _h = g.get("hold")
        hold = float(_h) if _h else hold
        if hold and hold > gdur + 0.05:
            fc2.append(f"[{last2}]tpad=stop_mode=clone:"
                       f"stop_duration={hold-gdur:.2f}[hp]")
            last2 = "hp"; gdur = float(hold)
        try:
            # ⚠️ renderer v2 — 60fps · sub-pixel · motion blur · alpha (ProRes 4444)。
            #    ယခင် ffmpeg overlay chain က 30fps · blur မရှိ。 မအောင်မြင်လျှင်
            #    အဟောင်းလမ်းကြောင်းသို့ ပြန်ဆုတ်သည် (job မကျအောင်)。
            done_v2 = False
            _r = _r2()
            if _r is not None and os.environ.get("IKKI_GFX_V2", "1") != "0":
                try:
                    el2 = dict(el)
                    el2["anim"] = [(p_, x_, y_ + dy) for (p_, x_, y_) in el["anim"]]
                    el2["statics"] = [(p_, x_, y_ + dy, d_) for (p_, x_, y_, d_) in el.get("statics", [])]
                    base_mov = mov.replace(".mov", "_v2.mov")
                    # ⚠️ `src_fps` က **အပေါ်က `hifps(60)` နဲ့ တွဲနေသည်** —
                    #    builder ကို ၆၀ နဲ့ ဆောက်ခိုင်းထားသဖြင့် ဒီမှာလည်း ၆၀。
                    #    တစ်ဖက် ပြောင်းလျှင် နှစ်ဖက်လုံး ပြောင်းရမည် — မဟုတ်လျှင်
                    #    anim က မြန်/နှေး ဖြစ်ပြီး ခဲသွားမည် (slide မှာ တကယ် ဖြစ်ခဲ့)。
                    _f2, _sub2 = _v2fps(fps)
                    _r.clip_alpha(el2, base_mov, hold=0.02, fps=_f2, sub=_sub2, src_fps=60,
                                   look=dict(grain=1.1,
                                             tone=getattr(_r, "LOOK2026", {}).get("tone")),
                                   camera=(1.0, 1.015))
                    if hold and hold > float(el["dur"]) + 0.05:
                        subprocess.run(["ffmpeg","-v","error","-y","-i",base_mov,"-vf",
                            f"tpad=stop_mode=clone:stop_duration={hold-float(el['dur']):.2f}",
                            "-c:v","prores_ks","-profile:v","4444","-pix_fmt","yuva444p10le",
                            mov], check=True)
                        os.remove(base_mov)
                    else:
                        os.replace(base_mov, mov)
                    gdur = float(hold) if (hold and hold > float(el["dur"])) else float(el["dur"])
                    done_v2 = True
                except Exception as _e:
                    log(f"  ⚠️ v2 render မရ ({type(_e).__name__}) — အဟောင်းနဲ့ ဆက်လုပ်")
            if not done_v2:
                subprocess.run(["ffmpeg","-v","error","-y"]+ins+["-filter_complex",";".join(fc2),
                    "-map",f"[{last2}]","-t",f"{gdur:.2f}","-r",str(fps),
                    "-c:v","qtrle","-pix_fmt","argb",mov],check=True)
            made.append((g["at"], mov, gdur, bool(g.get("fixed")),
                         max(0,int(y0)), min(int(H),int(y1))))
        except subprocess.CalledProcessError as e:
            log(f"  ⚠️ {g['kind']} render မရ")
    if not made: return None, 0
    # ⚠️ **မရွှေ့ရသူကို အရင် နေရာချ**ရမည် — typography က စကားလုံးနဲ့
    #    ချိတ်ထားသည်。 အချိန်အလိုက်သာ စဉ်ပြီး ရှေ့ကလာသူကို ဦးစားပေးလျှင်
    #    ခေါင်းစဉ်ဂရပ်ဖစ်က typography ကို ဖယ်ပစ်သည် (v24 မှာ ၈ ခုထဲ ၃ ခု
    #    ပျောက်ခဲ့သည်)。
    made.sort(key=lambda x: (0 if x[3] else 1, x[0]))
    placed=[]                                   # (start, end) — ယူပြီးသား
    def _free(a, b):
        return all(b <= x or a >= y for x, y in placed)
    # ⚠️ ထပ်နေသော ဂရပ်ဖစ် မရှိစေရ — နောက်ဟာက ရှေ့ဟာ ပြီးမှ စရမည်。
    # ⚠️ ဒါပေမဲ့ ထပ်နေရုံနဲ့ **တိတ်တဆိတ် မဖျက်ရ** — ZAE short မှာ ရွေး ၈ ခု
    #    ထဲက ၄ ခု ဒီနေရာမှာ ပျောက်သွားပြီး Zin က "အရုပ်တွေ ပျောက်သွားတယ်"
    #    ဟု ပြောခဲ့သည် (တကယ်)。 ⇒ အနည်းငယ် ရွှေ့၍ ရလျှင် ရွှေ့ရမည်၊
    #    တကယ် မရမှ ဖျက်ပြီး **အကြောင်းရင်း ပြရ**မည်。
    keep=[]; moved=0; dropped=[]
    for at,mov,d,fixed,y0,y1 in made:
        if not _free(at-0.2, at+d+0.2):
            if fixed:                             # မရွှေ့ရ — ဖျက်ရုံသာ
                dropped.append(round(at,1)); continue
            for step in (0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, -0.5, -1.0, -1.5):
                if _free(at+step-0.2, at+step+d+0.2):
                    at = round(at+step, 2); moved += 1; break
            else:
                dropped.append(round(at,1)); continue
        keep.append((at,mov,d,y0,y1)); placed.append((at-0.2, at+d+0.2))
    keep.sort(key=lambda x: x[0])
    LAST["overlap"] = len(dropped); LAST["moved"] = moved; LAST["placed"] = len(keep)
    if moved:   log(f"  ဂရပ်ဖစ် {moved} ခု ထပ်နေ၍ ရွှေ့လိုက်သည်")
    if dropped: log(f"  ⊘ ထပ်နေ၍ ဖျက် {len(dropped)} ခု (ရွှေ့၍ မရ): {dropped}")
    return keep, len(keep)


_R2 = None
def _r2():
    """motionkit ရဲ့ renderer v2 — ရှိလျှင် သုံး (alpha · 60fps · motion blur)。"""
    global _R2
    if _R2 is not None: return _R2
    try:
        import sys as _s, os as _o
        import gfxcat as GC
        if GC.MK not in _s.path: _s.path.insert(0, GC.MK)
        cwd = _o.getcwd(); _o.chdir(GC.MK)
        try:
            import render2 as R2
        finally:
            _o.chdir(cwd)
        _R2 = R2
    except Exception:
        _R2 = None
    return _R2

def _mk_fps(_r=None):
    """motionkit ရဲ့ builder က **တကယ် သုံးနေသော** fps。

    `kit.nfr(dur) = dur × kit.FPS` ⇒ ဒီတန်ဖိုးကိုပဲ `src_fps` အဖြစ်
    ပေးရမည်。 ကိန်းသေ ရေးထားလျှင် motionkit ဘက်က ပြောင်းသွားချိန်မှာ
    တိတ်တဆိတ် လွဲသွားမည်。
    """
    try:
        import sys as _s
        import gfxcat as GC
        if GC.MK not in _s.path: _s.path.insert(0, GC.MK)
        import kit as _k
        return int(getattr(_k, "FPS", 30)) or 30
    except Exception:
        return 30


def _v2fps(fps):
    """timeline fps နဲ့ ကိုက်ညီသော (fps, sub) ကို ပြန်ပေးသည်。

    ⚠️ **overlay ကို timeline ရဲ့ fps နဲ့ပဲ ထုတ်ရမည်**。 ၆၀fps နဲ့ ထုတ်ပြီး
       ၃၀fps timeline ပေါ် တင်လျှင် ffmpeg က ဖရိမ် **တစ်ဝက် ပစ်သည်** —
       တကယ့် ဂရပ်ဖစ်ဖိုင်နဲ့ တိုင်းကြည့်ရာ ရေးဆွဲထားသော ၁၀၉ ဖရိမ်ထဲက
       ၅၅ ခုသာ ထွက်ဗီဒီယိုထဲ ရောက်သည် (၂၀၂၆-၀၉-၂၀ တိုင်းချက်)。
    ⚠️ fps လျှော့လျှင် `sub` ကို **လိုက်တင်ရမည်**。 sub က ဖရိမ်တစ်ခုအတွင်း
       နမူနာ အရေအတွက် ⇒ fps တစ်ဝက် ဖြစ်လျှင် နမူနာ ခြားချိန် နှစ်ဆ ကျယ်ကာ
       blur က ဆက်တိုက် မဟုတ်ဘဲ **တစ်ဆင့်ချင်း** ဖြစ်သွားမည်。
       ⇒ `fps × sub` (တစ်စက္ကန့် ရေးဆွဲချက်) ကို ၆၀×၃ အတိုင်း ထိန်းထားသည်。
    """
    _r = _r2()
    sub0 = getattr(_r, "SUB", 3) if _r is not None else 3
    f = int(fps or 30) or 30
    return f, max(sub0, int(round(sub0 * 60.0 / f)))


# ══ slide — motionkit template ═══════════════════════════════
# ⚠️ ၂၀၂၆-၀၉-၂၀ Zin: 「ဘောင်အပြည့် ဖြူဖြူ slide … မသုံးနဲ့」。
#    IKKI ကိုယ်ပိုင် `core/slide.py` က PNG တစ်ချပ်ထုတ်ပြီး ၁၀.၅s ငြိမ်နေသည် —
#    ထွက်ဗီဒီယိုရဲ့ ၃၃% မလှုပ်ဘဲ ဖြစ်ခဲ့သည်。 ⇒ motionkit template နဲ့ ပြောင်း。
# ⚠️ template ရဲ့ သဘာဝ ကြာချိန် (~၃.၆s) ကိုသာ animate စေပြီး ကျန်တာကို
#    `tpad=stop_mode=clone` နဲ့ ဆွဲရမည် — `dur` ကို ၁၀.၅ ပေးလျှင် animation
#    တစ်ခုလုံး နှေးကွေးသွားမည်。 (ဂရပ်ဖစ် လမ်းကြောင်းက ဒီနည်းအတိုင်းပါပဲ)
SLIDE_TPL = {
    "bullets":   ("prem", "split_hero"),    # (tag, title, items, eyebrow)
    "statement": ("prem", "quote_card"),    # (tag, quote, who, role)
    "bignum":    ("prem", "quote_card"),
}


def slide_clip(layout, head, items, num, brand, out, hold, log=print, fps=30,
               template=None, props=None):
    """slide တစ်ခုကို motionkit template ဖြင့် alpha .mov အဖြစ် ထုတ်သည်。

    ရလျှင် `out` လမ်းကြောင်း、မရလျှင် `None` (ခေါ်သူက PNG သို့ ပြန်ဆုတ်ရန်)。
    """
    import subprocess, os as _o, sys as _s
    _r = _r2()
    if _r is None: return None
    # ⚠️ `template` ပေးလျှင် **အဲဒါကို** သုံးသည် — plan (Headtop) က ရွေးထားသော
    #    ဘောင်အပြည့် ကတ်ကို **ဖြတ်ပြောင်း** အဖြစ် ထုတ်ရန်。 မပေးလျှင်
    #    ယခင်အတိုင်း `SLIDE_TPL` (Knowledge Sharing လမ်းကြောင်း)。
    # ⚠️ ဘာကြောင့် ဖြတ်ပြောင်း လိုသလဲ — ပြောသူက ဘောင်ရဲ့ ၆၄% ယူပြီး
    #    စာတန်းက ၇၀% ကနေ စသဖြင့် ထပ်တင်ဖို့ **၅.၆% ·H သာ ကျန်**သည်。
    #    template တွေက ၅၀၇–၁၀၇၉px ရှိ၍ ဘာမှ မဝင်နိုင်ပါ (၂၀၂၆-၀၉-၂၁ တိုင်း၍
    #    တွေ့ — ဂရပ်ဖစ် ၄ ခုလုံး 「နေရာ မတည့်」နဲ့ ပယ်ခံခဲ့သည်)。
    if template and "." in template:
        mod_name, fn_name = template.split(".", 1)
    else:
        mod_name, fn_name = SLIDE_TPL.get(layout) or SLIDE_TPL["statement"]
    out = _o.path.abspath(out)
    base = out.replace(".mov", "_b.mov")
    import gfxcat as GC
    if GC.MK not in _s.path: _s.path.insert(0, GC.MK)
    # ⚠️ **cwd ကို motionkit မှာပဲ ထားရမည်** — template တွေက frame PNG ကို
    #    `work/prem/sl_f0000.png` ဆိုတဲ့ **relative** လမ်းကြောင်းမှာ ရေးသည်。
    #    `el` ဆောက်ပြီးမှ cwd ပြန်ပြောင်းလျှင် `clip_alpha` က ရှာမတွေ့ဘဲ
    #    `FileNotFoundError` ဖြစ်သည် (၂၀၂၆-၀၉-၂၀ တကယ် ဖြစ်)。
    # ⚠️ **pack template က motionkit module မဟုတ်** — `headtop.ht_stat_ring`
    #    ကို `__import__("headtop")` လုပ်လျှင် `ModuleNotFoundError` ဖြစ်သည်
    #    (၂၀၂၆-၀၉-၂၁ render မှာ ၃ ခုလုံး ကျခဲ့)。 pack adapter ကို သုံးရမည်。
    if str(template or "").startswith("headtop."):
        # ⚠️ ဘောင်အရွယ်ကို **theme ကနေ** ယူရမည် — slide_clip က W/H
        #    parameter မရှိ。 motionkit က format သတ်မှတ်ပြီးသား ဖြစ်သည်。
        try:
            import theme as _TH2
            _t2 = _TH2.t(); _W, _H = int(_t2["W"]), int(_t2["H"])
        except Exception:
            _W, _H = 1920, 1080
        _wk = _o.path.dirname(out) or "."
        _tag = _o.path.splitext(_o.path.basename(out))[0] or "sl"
        el = pack_el(template, dict(props or {}), _wk, _tag, _W, _H,
                     fps=fps, dur=hold, log=log)
        if el is None:
            return None
        # ⚠️ `slide_clip` က **လမ်းကြောင်း** ပြန်ပေးရမည် — element မဟုတ်。
        base2 = out.replace(".mov", "_b.mov")
        cwd2 = _o.getcwd()
        try:
            _o.chdir(GC.MK)
            _r2v = _r2()
            if _r2v is None:
                return None
            _f3, _sub3 = _v2fps(fps)
            _r2v.clip_alpha(el, base2, hold=0.02, fps=_f3, sub=_sub3,
                            src_fps=_mk_fps(_r2v),
                            look=dict(grain=1.1,
                                      tone=getattr(_r2v, "LOOK2026", {}).get("tone")),
                            camera=(1.0, 1.015))
            _o.replace(base2, out)
        except Exception as e:
            log(f"  ⚠️ pack slide ထုတ်၍ မရ: {type(e).__name__}: {e}")
            try: _o.remove(base2)
            except Exception: pass
            return None
        finally:
            _o.chdir(cwd2)
        return out
    cwd = _o.getcwd()
    try:
        _o.chdir(GC.MK)
        try:
            mod = __import__(mod_name)
            fn = getattr(mod, fn_name)
            its = [str(x).strip() for x in (items or []) if str(x).strip()][:4]
            if template and props is not None:
                # ⚠️ plan ရဲ့ props ကို **အတိအကျ** ပေးသည် — manifest နဲ့
                #    စစ်ပြီးသား ဖြစ်၍ မှန်းဆ မလုပ်ရ。
                el = fn("sl", **props)
            elif layout == "bullets":
                el = fn("sl", head, its or [brand], eyebrow=brand)
            elif layout == "bignum":
                el = fn("sl", str(num or head), head if num else brand, role=brand)
            else:
                el = fn("sl", head, brand, role="")
        except Exception as e:
            log(f"  ⚠️ slide template {mod_name}.{fn_name} မရ: {type(e).__name__}: {e}")
            return None
        if not isinstance(el, dict) or not el.get("anim"): return None
        # ⚠️ **`src_fps` ကို builder ရဲ့ အမှန်နဲ့ ကိုက်ရမည်**。 `track()` က
        #    `hifps(60)` သုံး၍ ကိုက်နေပေမယ့် ဒီနေရာမှာ မသုံးသဖြင့် motionkit က
        #    `kit.FPS`=30 နဲ့ ဆောက်ကာ `clip_alpha` က ၆၀ ဟု ယူဆခဲ့သည်。
        #    ⇒ anim ကို **နှစ်ဆ မြန်** စားပြီး တစ်ဝက်မှာ ခဲသွားသည်
        #    (တိုင်းချက်: quote_card · split_hero နှစ်ခုလုံး anim ၁၀၈ / ၃.၆၀s
        #     = ၃၀fps · ၂၀၂၆-၀၉-၂၀)。 slide က 「မလှုပ်ဘူး」ဖြစ်ရခြင်း。
        _sf = _mk_fps(_r)
        _f2, _sub2 = _v2fps(fps)
        _r.clip_alpha(el, base, hold=0.02, fps=_f2, sub=_sub2, src_fps=_sf,
                      look=dict(grain=1.1,
                                tone=getattr(_r, "LOOK2026", {}).get("tone")),
                      camera=(1.0, 1.015))
        # ⚠️ ကြာချိန်ကို clip ထဲ **မဆွဲရ**。 `tpad` နဲ့ ၁၀.၅s အထိ ဆွဲလျှင်
        #    ProRes 4444 က တစ်ချပ် **၇၀၃ MB** ဖြစ်သည် (၂၀၂၆-၀၉-၂၀ တိုင်း၍ တွေ့)。
        #    overlay မှာ `eof_action=repeat` သုံးလျှင် နောက်ဆုံး frame ကို
        #    ဝင်းဒိုး ပိတ်သည်အထိ ရပ်ထားပေးသည် ⇒ clip က သဘာဝ ၃.၆s ပဲ လို
        #    (၂၂၇ MB)。 စမ်းသပ်ပြီး အတည်ပြုထားသည်。
        _o.replace(base, out)
    except Exception as e:
        log(f"  ⚠️ slide clip ထုတ်၍ မရ: {type(e).__name__}: {e}")
        try: _o.remove(base)
        except Exception: pass
        return None
    finally:
        _o.chdir(cwd)
    return out


_CIDX = None
def _cargs(kind, brand, label):
    """catalog ရဲ့ signature ကနေ argument ဖြည့်သည် (ARGS မှာ မရှိသော template)。"""
    global _CIDX
    if _CIDX is None:
        _CIDX = {}
        try:
            import gfxcat as GC
            for e in GC.catalog(): _CIDX[e["fn"]] = e
        except Exception:
            _CIDX = {}
    # ⚠️ အရင်က ဖြည််မရရင် `(brand,)` သာ ပြန်ပေးခဲ့သည် — ဒါက
    #    **ဂဏန်း param ထဲ စာသား ထည့်လိုက်ခြင်း**。 `kinetic2.count_roll` က
    #    `val` (number) လိုသည် ⇒ `f"{val:,}"` မှာ
    #    「Cannot specify ',' with 's'」 ဖြစ်ပြီး ဂရပ်ဖစ် ပျောက်သည်
    #    (၂၀၂၆-၀၉-၂၁ render မှာ တကယ် ဖြစ်ခဲ့)。
    #    ⇒ **ဖြည််လို့မရလျှင် `None`** — အဲဒီ template ကို မသုံးတော့ပါ。
    #    (`gfxcat.fill` ကိုယ်တိုင်လည်း 「ဖြည့်လို့မရတဲ့ param တွေ့ဆို ရပ်ရမည်」 ဆိုပြီးသား)
    e = _CIDX.get(kind)
    if not e:
        return None
    try:
        import gfxcat as GC
        return GC.fill(e, brand, label)
    except Exception:
        return None


_FNC = {}
def _fn(name):
    """catalog ကနေ template function ရှာသည်。

    `"module.fn"` ပေးလျှင် **အဲဒီ module ကသာ** ယူသည်。
    `"fn"` သက်သက်ဆိုလျှင် ပထမတွေ့သော module (ယခင်အတိုင်း)。

    ⚠️ **fn နာမည် ၁၈ ခု module အချင်းချင်း တူနေသည်** (၂၀၂၆-၀၉-၂၀ တိုင်း၍
       တွေ့) — `line_by_line` က `capt` ရော `prem5` ရောမှာ ရှိပြီး
       `compare_bar` က `dash`·`infogfx`·`prem7` ၃ ခုမှာ ရှိသည်。
       နာမည်သက်သက် ပေးလျှင် **မှားသော module** ကို တိတ်တဆိတ် ယူမိနိုင်သည်
       ⇒ plan က `motionKitTemplateId` အပြည့် ပေးရမည်。
    """
    if name in _FNC: return _FNC[name]
    f = None
    want_mod = None
    if "." in name:
        want_mod, name = name.split(".", 1)
    try:
        import importlib, sys as _s
        import gfxcat as GC
        for e in GC.catalog():
            if e["fn"] == name and (want_mod is None or e["module"] == want_mod):
                cwd = os.getcwd()
                try:
                    if GC.MK not in _s.path: _s.path.insert(0, GC.MK)
                    os.chdir(GC.MK)
                    f = getattr(importlib.import_module(e["module"]), name, None)
                finally:
                    try: os.chdir(cwd)
                    except Exception: pass
                break
    except Exception:
        f = None
    _FNC[name] = f
    return f

def resolves(name):
    """template ကို တကယ် ရှာလို့ရလား — caption ဖယ်ခင် စစ်ရန်"""
    try:
        import titles as _t1, titles2 as _t2
        if getattr(_t2, name, None) or getattr(_t1, name, None): return True
    except Exception:
        pass
    return _fn(name) is not None


_TAGQ = {}
def _wants_tag(name):
    """template က ပထမ param အဖြစ် `tag` ယူလား"""
    if name in _TAGQ: return _TAGQ[name]
    # ⚠️ catalog ရဲ့ params က `tag` ကို **ဖယ်ထားသည်** (auto-supplied ဟု
    #    သတ်မှတ်၍)。 ဒါကြောင့် catalog နဲ့ စစ်လျှင် အားလုံး "မလို" ထွက်ပြီး
    #    တကယ် လိုတဲ့ ၁၂ ခုပါ ချိုးမိသည်。 ⇒ signature ကို တိုက်ရိုက် ကြည့်ရမည်。
    want = True
    try:
        import inspect
        fn = getattr(T2, name, None) or getattr(T1, name, None) or _fn(name)
        if fn:
            ps = list(inspect.signature(fn).parameters)
            want = bool(ps) and ps[0] == "tag"
    except Exception:
        want = True
    _TAGQ[name] = want
    return want


# ══ template အမြင့် ↔ ရနိုင်သော နေရာ (Overlay audit P0) ════════════
# ⚠️ တကယ့် headtop render မှာ ဂရပ်ဖစ် ၇ ခု ရွေးပြီး **၀–၃ ခုသာ** တပ်ဖြစ်ခဲ့သည် —
#    စကားပြောသူက အပေါ် ၆၄% ဖုံးပြီး အောက်က စာတန်းက ယူထားလို့ **၆၁ px သာ**
#    ကျန်သည်。 ကတ်တွေက ၅၂၈–၁၀၇၇ px မြင့်၍ တစ်ခုမှ မဝင်ပါ。
# ⚠️ အရင်က **ဆောက်ပြီးမှ** သိရသဖြင့် အချိန် ကုန်ပြီး ဂရပ်ဖစ် မရှိတော့。
#    ⇒ `tools/gfxsize.py` က အမြင့်ကို ကြိုတိုင်းထားပြီး ဒီမှာ ကြိုစစ်သည်。
# ⚠️ **ဒီတွက်နည်းက placement နဲ့ အတူတူ ဖြစ်ရမည်** — မတူလျှင် ကြိုစစ်ချက်က
#    အလကား (ရွေးပြီးမှ ပယ်ခံဦးမည်)。 ⇒ `_fits()` ကို နှစ်နေရာလုံး သုံးသည်。
_SIZE = None


def sizes(fmt="16:9"):
    """template → တိုင်းထားသော အမြင့် (px · production ဘောင်အတိုင်း)"""
    global _SIZE
    if _SIZE is None:
        _SIZE = {}
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "assets", f"gfx_size_{fmt.replace(':', 'x')}.json")
        try:
            import json as _j
            with open(p, encoding="utf-8") as f:
                _SIZE = {k: v for k, v in (_j.load(f).get("items") or {}).items()
                         if "h" in v}
        except (OSError, ValueError):
            _SIZE = {}
    return _SIZE


def room(avoid, capy, H):
    """ဂရပ်ဖစ် ချနိုင်သော **အမြင့်ဆုံး px** — `avoid` မရှိလျှင် `H`

    ⚠️ placement (`track()`) ရဲ့ ကိန်းများနဲ့ **တစ်ထပ်တည်း** ဖြစ်ရမည်。
    """
    if not avoid:
        return H
    ay0, ay1 = avoid
    TOP = int(H * 0.075)
    above = ay0 - TOP - 8                      # ခေါင်းအထက်
    below = (capy - 12 if capy else H - 12) - (ay1 + 16)
    return max(0, above, below)


def fits(kind, avoid, capy, H, fmt="16:9"):
    """`kind` က နေရာ ဝင်လား — တိုင်းချက် မရှိလျှင် `True` (ကြိုမပယ်ရ)

    ⚠️ **ပြောသူပေါ် တင်ခွင့်ရှိသော template ကို အမြင့်နဲ့ မပယ်ရ** —
       အဲဒါတွေက မျက်နှာဇုန်ကို မဖြတ်သန်းရဘဲ ဘောင်အပြည့် သုံးနိုင်သည်。
    """
    if _over_subject(kind):
        return True
    it = sizes(fmt).get(kind)
    if not it:
        return True
    return int(it["h"]) <= room(avoid, capy, H)


def swap_fit(gfx, avoid, capy, H, seed="", fmt="16:9", log=None):
    """ဝင်မဆံ့သော kind ကို **ဝင်ဆံ့သော အခြား template** နဲ့ လဲပေးသည်

    ⚠️ ပယ်လိုက်တာထက် လဲတာက ကောင်းသည် — ဂရပ်ဖစ် မရှိလျှင် `gfx_share`
       ဂိတ် ကျပြီး ဗီဒီယိုက ခြောက်သွေ့သည်。
    ⚠️ **တူညီသော seed ⇒ တူညီသော အစားထိုး** (ပြန်ထုတ်လျှင် တူရန်)。
    """
    cap = room(avoid, capy, H)
    sz = sizes(fmt)
    if not sz:
        return gfx, 0
    pool = [k for k in _verified(seed) if k in sz and int(sz[k]["h"]) <= cap]
    # ⚠️ **နေရာ တစ်ခုမှ မရှိသော အခြေအနေ ရှိသည်**。 ၂၀၂၆-၀၉-၂၁ တိုင်းချက် —
    #    headtop framing (မျက်နှာ ၀–၆၄% · စာတန်း ၇၀%) မှာ ကျန်နေရာက
    #    **၃၃ px (၃.၁%H)** သာ ဖြစ်ပြီး တိုင်းထားသော template ၂၄၃ ခုထဲက
    #    **တစ်ခုမှ မဝင်**ပါ (အနိမ့်ဆုံးက ၆၁px)。
    #    ⇒ တစ်ခုတည်းသော လမ်းက **ပြောသူပေါ် တင်နိုင်သော အနားသတ်** —
    #      reference ကလည်း အဲဒီလိုပဲ လုပ်ထားသည် (ink ၈–၁၆%H · ပွင့်လင်း)。
    sub = _subject_pool()
    out, n, used = [], 0, set()
    for i, g in enumerate(gfx):
        k = g.get("kind")
        if fits(k, avoid, capy, H, fmt):
            out.append(g); used.add(k); continue
        alt = next((c for c in pool if c not in used), None) \
            or (pool[i % len(pool)] if pool else None)
        src = "အမြင့် ဝင်ဆံ့"
        if not alt and sub:
            alt = sub[i % len(sub)]
            src = "ပြောသူပေါ် တင်နိုင်"
        if not alt:
            # ⚠️ **တိတ်တဆိတ် မထားရ** — ဘာမှ မရှိလျှင် အကြောင်းရင်း ပြရမည်
            log and log(f"  ⚠️ {k} မဝင် · အစားထိုး မရှိ (နေရာ {cap}px) — "
                        f"placement မှာ ပယ်မည်")
            out.append(g); continue
        g2 = dict(g); g2["kind"] = alt; g2.pop("args", None)
        used.add(alt); out.append(g2); n += 1
        log and log(f"  ↺ {k} ({sz.get(k, {}).get('h', '?')}px) မဝင် ⇒ "
                    f"{alt} ({src}) · နေရာ {cap}px")
    return out, n


def _pack_fill(tid, text):
    """pack template ရဲ့ required text props — **အကြောင်းအရာ စာသား** ကနေ

    ⚠️ brand/label ကို **မသုံးရ** — 「Headtop」လို recipe နာမည်ကို
       မျက်နှာပြင်ပေါ် တင်မိပြီး အဓိပ္ပာယ်မဲ့ ဖြစ်သည်。 စာသား မရှိလျှင်
       `{}` ပြန်ပေးပြီး ခေါ်သူက **ကျော်**ရမည်。
    """
    txt = (text or "").strip()
    if not txt:
        return {}
    try:
        try:
            import pack as _PK
            import planner as _P
        except ImportError:
            from core import pack as _PK, planner as _P
        t = _PK.template(tid) or {}
        out = {}
        for k, spec in (t.get("props") or {}).items():
            if spec.get("type") == "text" and spec.get("required"):
                out[k] = _P._short(txt, int(spec.get("maxChars") or 30))
        return out
    except Exception:
        return {}


def _subject_pool():
    """ပြောသူပေါ် တင်နိုင်သော **verify ပြီးသား** pack template များ"""
    try:
        try:
            import pack as _PK
        except ImportError:
            from core import pack as _PK
        # ⚠️ **fullFrame ကို အစားထိုး အဖြစ် မသုံးရ** — ဂရပ်ဖစ်တိုင်းကို
        #    ဘောင်အပြည့် ကတ်နဲ့ လဲလျှင် ဗီဒီယိုက slideshow ဖြစ်သွားပြီး
        #    ပြောသူနဲ့ ဆက်သွယ်မှု ပြတ်သည်。 အနားသတ်သာ ယူသည်。
        return [t for t in _PK.selectable()
                if _over_subject(t) and not _full_frame(t)]
    except Exception:
        return []


# ══ SFX က စကားကို မဖုံးစေရန် (SFX audit P0) ═══════════════════════
# ⚠️ `mix()` က cue တိုင်းကို **ပုံသေ dB** နဲ့ ထပ်သည် — စကားပြောနေချိန်လား
#    တိတ်နေချိန်လား မကြည့်ပါ。 စကားပေါ် whoosh တစ်ချက် ကျယ်ကျယ် ဝင်လျှင်
#    စကားလုံး ပျောက်သည် (「no SFX masks a protected speech onset」)。
# ⚠️ **အချိန်ကို မရွှေ့ရ** — cue က ဂရပ်ဖစ်နဲ့ တွဲနေသည်。 အသံကိုသာ လျှော့သည်。
# ⚠️ playbook — 「SFX ကို သတိထားမိလောက်အောင် ကြားရရင် ၆ dB ကျယ်နေပြီ」
#    ⇒ စကားပေါ်မှာ SFX က စကားအောက် ၆ dB ရှိရမည်。
DUCK_MARGIN = 6.0        # စကားအောက် ဘယ်နှစ် dB ထားမလဲ
DUCK_MAX = 12.0          # ဒီထက် ပို မလျှော့ရ — လျှော့လွန်းလျှင် မကြားရတော့
DUCK_WIN = 0.40          # cue ပတ်လည် ဘယ်လောက် တိုင်းမလဲ (s)


def speech_db(wav, at, win=DUCK_WIN):
    """`at` ပတ်လည် ရဲ့ စကားသံ အား (dBFS) — မတိုင်းရလျှင် `None`"""
    import subprocess
    if not wav or not os.path.exists(wav):
        return None
    try:
        import numpy as _np
    except ImportError:
        return None
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, at-win/2):.3f}",
                        "-t", f"{win:.3f}", "-i", wav, "-ac", "1", "-ar", "16000",
                        "-f", "f32le", "-"], capture_output=True)
    x = _np.frombuffer(r.stdout, "<f4").astype(_np.float64)
    if not len(x):
        return None
    return float(20 * _np.log10(max(1e-6, _np.sqrt((x ** 2).mean()))))


def _asset_db(role):
    """role ရဲ့ asset အား (dB) — catalog ကနေ · မရလျှင် −၁၆"""
    try:
        try:
            import sfxpool as _SP
        except ImportError:
            from core import sfxpool as _SP
        fam = _SP.MAP.get(role, (role, None, 0))[0]
        return float(_SP.target(fam))
    except Exception:
        return -16.0


def duck_cues(cues, wav, sfx_db=None, log=None):
    """စကားပေါ် ကျသော cue များကို လျှော့သည် — `([cue], လျှော့ခဲ့တာ)`

    `sfx_db` — `{role: အသံ အား dB}` (catalog ကနေ)。 မပါလျှင် cue ရဲ့
               ကိုယ်ပိုင် dB ကို အသုံးပြုသည်。
    """
    if not cues or not wav:
        return cues, 0
    out, n = [], 0
    for c in cues:
        at, role, db = (list(c) + [None, None, None])[:3]
        sp = speech_db(wav, float(at))
        if sp is None or sp < -45.0:          # တိတ်နေသည် ⇒ မထိ
            out.append(c); continue
        # ⚠️ **cue ရဲ့ `db` က အား မဟုတ် — လျှော့ချက်**。 asset ကို role
        #    မိသားစုရဲ့ ပစ်မှတ် အား (catalog ကနေ တိုင်းထား · ဥပမာ whoosh
        #    −၁၅.၃ dB) သို့ normalise ထားပြီးမှ `db` နဲ့ လျှော့သည် ⇒
        #    တကယ့် အား = ပစ်မှတ် + db。 ဒါကို မတွက်ဘဲ `db` ကို အားလို့
        #    ယူမိလျှင် **cue တိုင်း လျှော့ခံရ**ပြီး SFX မကြားရတော့ပါ
        #    (ပထမ ရေးဆွဲချက်မှာ ၅/၅ လျှော့ခဲ့သည် — ၂၀၂၆-၀၉-၂၁ ဖမ်းမိ)。
        lv = float(db or -16) + float((sfx_db or {}).get(role, _asset_db(role)))
        want = sp - DUCK_MARGIN
        if lv <= want:
            out.append(c); continue
        cut = min(DUCK_MAX, lv - want)
        out.append((at, role, int(round(float(db) - cut))))
        n += 1
        log and log(f"    ↓ SFX {at:6.2f}s {role:11} {db:+d} → "
                    f"{int(round(float(db)-cut)):+d} dB "
                    f"(စကား {sp:.0f} dB — ဖုံးမည် ဖြစ်၍)")
    return out, n


# ══ Headtop Premium pack → render adapter (Overlay audit P0) ═══════
# ⚠️ audit — 「the new Headtop pack has two verified templates but is not
#    selected by the production planner or called by the production
#    renderer」。 `packs/headtop-premium/templates/` က **ဗလာ** ဖြစ်ပြီး
#    တကယ့် ရေးဆွဲချက်က `core/cards.py` မှာ ရှိသည် ⇒ ဒီမှာ ချိတ်သည်。
# ⚠️ motion ကို pack ရဲ့ **တိုင်းထားသော token** အတိုင်း သုံးရမည် —
#    enter ၀.၄၆၇ · exit ၀.၂၀၀ · fade+scale (reference ၂ ပုဒ် · ဖြစ်ရပ် ၂၁
#    ခုကနေ တိုင်းယူ)。 ကိုယ်ပိုင် ကိန်း ထည့်လျှင် pack က အလကား ဖြစ်သည်。
PACK_FN = {"headtop.ht_concept_card": "concept_card",
           "headtop.ht_outline_title": "outline_title",
           "headtop.ht_stat_ring": "stat_ring",
           "headtop.ht_check_list": "check_list",
           "headtop.ht_compare_two": "compare_two"}


_PRIMS = {}


def _over_subject(kind):
    """ဤ template က မျက်နှာဇုန်ကို ကျော်လို့ရလား — pack manifest ကနေ

    နည်းလမ်း ၂ ခု ရှိသည် —
      · `safeZones.subject` — **အနားသတ်သာ** ⇒ ပြောသူ မြင်နေရသည်
      · `fullFrame`         — **တမင် ဖုံး**သည် (title card အခိုက်)
    ⚠️ **manifest ကနေသာ ယူရမည်** — နာမည်နဲ့ မှန်းလျှင် template အသစ်
       တိုင်း မှားမည်。
    """
    if not kind or "." not in str(kind):
        return False
    try:
        try:
            import pack as _PK
        except ImportError:
            from core import pack as _PK
        t = _PK.template(kind) or {}
        return bool(t.get("safeZones", {}).get("subject") or t.get("fullFrame"))
    except Exception:
        return False


def _full_frame(kind):
    """ဘောင်အပြည့် ဖုံးသော template လား — **တစ်ခါသာ** သုံးခွင့်ရှိသည်"""
    if not kind or "." not in str(kind):
        return False
    try:
        try:
            import pack as _PK
        except ImportError:
            from core import pack as _PK
        return bool((_PK.template(kind) or {}).get("fullFrame"))
    except Exception:
        return False


def _prims(pdir):
    """pack ရဲ့ `primitives.py` ကို လမ်းကြောင်းကနေ တင်သည် (cache)"""
    if pdir in _PRIMS:
        return _PRIMS[pdir]
    m = None
    try:
        import importlib.util as _iu
        q = os.path.join(pdir, "primitives.py")
        spec = _iu.spec_from_file_location("ht_prims", q)
        m = _iu.module_from_spec(spec)
        spec.loader.exec_module(m)
    except Exception:
        m = None
    _PRIMS[pdir] = m
    return m


def pack_el(tid, props, work, tag, W, H, fps=30, dur=None, mmf=None, log=None):
    """pack template → `track()` သုံးနိုင်သော element dict · မရလျှင် `None`

    ⚠️ `cards.py` က **ပုံ တစ်ပုံသာ** ပြန်ပေးသည် — animation မပါ。
       ⇒ pack ရဲ့ primitive နဲ့ ဝင်/ထွက် frame များ ဆောက်သည်。
    """
    import math
    try:
        try:
            import cards as CD
            import pack as PK
        except ImportError:
            from core import cards as CD, pack as PK
        from PIL import Image
    except ImportError as e:
        log and log(f"  ⚠️ pack adapter မရ: {e}")
        return None
    fn = PACK_FN.get(tid)
    if not fn or not hasattr(CD, fn):
        return None
    # ⚠️ `PK.src()` က token ရဲ့ **အရင်းအမြစ်** (measured/spec) ကို ပြန်ပေးသည် —
    #    module မဟုတ်。 primitives.py ကို လမ်းကြောင်းကနေ တင်ရသည်。
    _p, _t = PK.load()
    if not _p or not _t:
        return None
    P = _prims(PK.path())
    if P is None:
        log and log("  ⚠️ pack primitives တင်မရ")
        return None
    en = float(PK.tok(_t, "motion", "enter", default=0.467))
    ex = float(PK.tok(_t, "motion", "exit", default=0.200))
    hold = float(dur or PK.tok(_t, "motion", "hold", default=1.8))
    try:
        if fn == "concept_card":
            base = CD.concept_card(props.get("head") or "", props.get("sub") or "",
                                   W=W, H=H, mmf=mmf)
        elif fn == "stat_ring":
            base = CD.stat_ring(props.get("value") or "", props.get("label") or "",
                                W=W, H=H, mmf=mmf)
        elif fn == "check_list":
            base = CD.check_list(props.get("items") or [], W=W, H=H, mmf=mmf)
        elif fn == "compare_two":
            base = CD.compare_two(props.get("left") or "", props.get("right") or "",
                                  W=W, H=H, mmf=mmf)
        else:
            base = CD.outline_title(props.get("text") or "", W=W, H=H, mmf=mmf,
                                    cx=float(props.get("cx", 0.5)),
                                    cy=float(props.get("cy", 0.5)),
                                    halo=float(props.get("halo", 0.0)))
        if base is None:
            log and log(f"  ⚠️ pack {tid} — အကြောင်းအရာ မလောက်၍ မဆောက်ပါ")
            return None
    except Exception as e:
        log and log(f"  ⚠️ pack {tid} ဆောက်မရ: {type(e).__name__}: {e}")
        return None
    os.makedirs(work, exist_ok=True)
    ni = P.frames(en, fps)
    no = P.frames(ex, fps)
    anim, statics = [], []

    def _w(im, k):
        q = os.path.join(work, f"{tag}_{k:04d}.png")
        im.save(q); return q

    for i in range(ni + 1):
        a = P.at(P.fade, i, ni, dur=en)
        s = P.at(P.scale, i, ni, dur=en)
        im = base if abs(s - 1.0) < 1e-4 else base.resize(
            (max(1, int(W * s)), max(1, int(H * s))), Image.LANCZOS)
        if im.size != (W, H):                 # ⚠️ ဘောင် အလယ်မှာ ထားရမည်
            c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            c.paste(im, ((W - im.size[0]) // 2, (H - im.size[1]) // 2)); im = c
        if a < 0.999:
            al = im.split()[3].point(lambda v, _a=a: int(v * _a))
            im = im.copy(); im.putalpha(al)
        anim.append((_w(im, i), 0, 0))
    # ⚠️ ရပ်ချိန်ကို frame အပြည့် မရေးရ — ဖိုင် ထောင်ချီ ထွက်မည် ⇒ statics
    statics.append((anim[-1][0], 0, 0, max(0.1, hold)))
    for j in range(1, no + 1):
        a = P.at(P.fade, j, no, dur=ex, out=True)
        im = base.copy()
        im.putalpha(base.split()[3].point(lambda v, _a=a: int(v * _a)))
        anim.append((_w(im, ni + j), 0, 0))
    return dict(anim=anim, statics=statics, dur=round(en + hold + ex, 3),
                kind=tid, pack=True)
