"""transcript → HeadtopEditPlan。

⚠️ **AI ကို timeline မတောင်းပါ**。 Zin ရဲ့ စည်းမျဉ်း —
   「AI must NOT directly generate a free-form video edit」。
   ⇒ AI က **အဓိပ္ပာယ် အညွှန်း** (ဝါကျတစ်ခုချင်း ဘာအမျိုးအစားလဲ) သာ
     ပြန်ပေးပြီး **timeline ကို ဒီကုဒ်က တည်ဆောက်**သည်。
   ဒါကြောင့် မရှိသော template · ဘောင်ပြင် အချိန် · မမှန်သော layer
   ထွက်ဖို့ **လမ်းမရှိ**တော့ပါ — Gemini က ဘာပဲ ပြန်ပြန် label ကို
   ပိတ်ထားသော စာရင်းနဲ့ စစ်ပြီး မကိုက်လျှင် `plain` ဖြစ်သွားသည်。

⚠️ Gemini မရလျှင် **အလုပ် မရပ်ရ** — heuristic နဲ့ ဆက်လုပ်သည်。
   (ASR တိတ်တဆိတ် ကျရှုံးမှုက ဒီ project မှာ တစ်နာရီ ကုန်စေဖူးသည်)。
"""
import json
import os
import re
import urllib.request

try:
    import gemguard as G
    import manifest as MF
    import plan_schema as PS
except ImportError:                                   # API က package အဖြစ်
    from core import gemguard as G
    from core import manifest as MF
    from core import plan_schema as PS

# ⚠️ model ကို **ကိန်းသေ မရေးရ** — `IKKI_GEMINI_MODEL` ကနေ ယူရသည်
#    (`topics.py` · `asr.py` နဲ့ တူညီစွာ)。 ကိန်းသေ ရေးမိ၍ `gemini-2.0-flash`
#    က **HTTP 404** ပြန်ကာ planner က heuristic သို့ တိတ်တဆိတ် ကျဆင်းခဲ့သည်
#    (၂၀၂၆-၀၉-၂၁ — log မှာ 「Gemini မရ」ဟုသာ ပေါ်၍ အကြောင်းရင်း မသိခဲ့)。
MODEL = os.environ.get("IKKI_GEMINI_MODEL", "gemini-flash-latest")

# ── ပိတ်ထားသော အညွှန်း စာရင်း ────────────────────────────────
# ⚠️ AI က ဒီထဲကပဲ ရွေးခွင့် ရှိသည်。 အခြားဟာ ပြန်ပေးလျှင် `plain` ဖြစ်သည်。
LABELS = ("hook", "section", "fact", "number", "steps", "checklist",
          "compare", "location", "screen", "warning", "plain")

# အညွှန်း → template မိသားစု (manifest.HEADTOP ထဲက)
FAMILY = {
    "hook":      "hook",
    "section":   "ident",
    "fact":      "callout",
    "number":    "number",
    "steps":     "explain",
    "checklist": "explain",
    "compare":   "explain",
    "location":  "broll",
    "screen":    "mockup",
    "warning":   "callout",
}

# အညွှန်း → template ID ဦးစားပေး (မိသားစုထဲမှ)
PREFER = {
    "steps":     ["infogfx.steps", "infogfx.checklist"],
    "checklist": ["infogfx.checklist"],
    "compare":   ["infogfx.big_number", "infogfx.checklist"],
    "number":    ["odo.big_stat", "odo.count_up", "odo.percent_ring"],
    "location":  ["prem7.location_tag", "prem7.note_card"],
    # Generic browser animation only. A real product screen is rendered only
    # when the user supplies its screenshot/screen recording as an asset.
    "screen":    ["brows.window_open"],
    "warning":   ["callouts.box_call", "callouts.underline_call"],
    # ⚠️ **`fact` ကို `callouts.*` နဲ့ မချိတ်ရ** (၂၀၂၆-၀၉-၂၅)。 `fact` က
    #    အညွှန်း မကိုက်သမျှ **အားလုံး ကျရာ** ယေဘုယျ အိမ် ဖြစ်သည် (တကယ့် job
    #    `j_c42e5c142058` — ဝါကျ ၁၇ ကြောင်းမှာ `plain`/`fact` ၉ ကြောင်း) ⇒
    #    **အသေးဆုံး မျဉ်းလေး**ကို **အများဆုံး ဝါကျ**မှာ ချိတ်မိခဲ့သည်。
    #    Zin: 「Graphic တွေက ဒီထက်ပိုမိုက်တာ သုံးစေချင်တယ် · size ပိုကြီး」
    #    ⇒ premium ကတ်ကို ရှေ့、`callouts.*` က auto tail မှာ ရှိဆဲ ဖြစ်သည်。
    # ⚠️ `prem7.note_card` ကို **မထားရ** — ဖုံးအုပ်မှု **၁.၀၀** (၂၀၂၆-၀၉-၂၅
    #    တိုင်းချက်) ⇒ ဖြတ်ပြောင်း ဖြစ်သည်。 `gfx_fullstage.txt` ထဲ မပါသဖြင့်
    #    ဖုံးနေခဲ့သည် — အဲဒီဖိုင်က လုံခြုံသော superset **မဟုတ်**。
    "fact":      ["dash.kpi_card", "dash.card_grid", "thm.board_points",
                  "infogfx.callout"],
    "section":   ["titles3.minimal_third", "titles.topic_bar", "titles.chapter"],
    "hook":      ["prem4.big_question", "prem4.stop_scroll", "titles3.opening_bars"],
}

# ── MotionKit visual language ─────────────────────────────────────
#
# User ကို raw template ID ၄၇၉ ခုလုံး မရွေးခိုင်းပါ။ Template တချို့က rows,
# map point စတဲ့ structured data လိုပြီး၊ တချို့က face safe-zone မရှိသဖြင့်
# talking-head ပေါ် တင်လို့မရပါ။ ဒီ mapping က profile တစ်ခုစီအတွက် render
# လုပ်နိုင်ပြီးသား (manifest-verified) template ကိုသာ ရွေးစေသည်။
# `premium` က လက်ရှိ best-of set + Headtop pack ကို သုံးသည်။ အခြား mode များ
# က explicit family ဖြစ်လို့ user ရွေးလိုက်သော visual language တကယ်ကွာသည်။
PROFILE_PREFER = {
    "clean": {
        "hook": ["titles3.opening_bars", "prem4.big_question"],
        "section": ["titles3.minimal_third", "titles.topic_bar"],
        "fact": ["infogfx.callout", "thm.board_terms",
                 "callouts.underline_call"],
        "number": ["odo.big_stat"],
        "steps": ["infogfx.steps"],
        "checklist": ["infogfx.checklist"],
        "compare": ["infogfx.big_number"],
        "location": ["prem7.location_tag"],
        "screen": ["brows.window_open"],
        "warning": ["callouts.underline_call"],
    },
    "bold": {
        "hook": ["prem4.stop_scroll", "prem4.big_question"],
        "section": ["titles.chapter", "titles.topic_bar"],
        "fact": ["dash.kpi_card", "thm.board_points",
                 "callouts.box_call"],
        "number": ["odo.count_up", "odo.big_stat"],
        "steps": ["infogfx.checklist", "infogfx.steps"],
        "checklist": ["infogfx.checklist"],
        "compare": ["infogfx.big_number"],
        "location": ["prem7.note_card", "prem7.location_tag"],
        "screen": ["brows.window_open"],
        "warning": ["callouts.box_call"],
    },
    "explainer": {
        "hook": ["prem4.big_question", "titles3.opening_bars"],
        "section": ["titles.chapter", "titles.topic_bar"],
        # ⚠️ `insert.insert_label` ကို ဒီမှာ **မထားရ** — ဖုံးအုပ်မှု
        #    **၁.၀၀** (တိုင်းထားသည်) ⇒ ဖြတ်ပြောင်း ဖြစ်ပြီး `_ff_order` က
        #    ဘတ်ဂျက် မကျချိန် ဖယ်သဖြင့် pin က အလဟဿ ဖြစ်မည်。
        "fact": ["thm.cmp_rows", "dash.card_grid",
                 "callouts.line_call"],
        "number": ["odo.big_stat", "odo.percent_ring"],
        "steps": ["infogfx.steps", "infogfx.checklist"],
        "checklist": ["infogfx.checklist"],
        "compare": ["infogfx.big_number"],
        "location": ["prem7.note_card"],
        "screen": ["brows.window_open"],
        "warning": ["callouts.box_call"],
    },
}


# ⚠️ **template ပြန်ပြန် ပေါ်တာကို တားရမည်** (၂၀၂၆-၀၉-၂၁ တိုင်းချက်)。
#    ဝါကျ ၁၀ ကြောင်းနဲ့ plan ပြေးကြည့်တော့ event ၈ ခု ရပေမယ့် template
#    **၃ မျိုးပဲ** ဖြစ်ပြီး `ht_stat_ring` က **၄ ခါ** ပေါ်ခဲ့သည် —
#    candidate order က ပုံသေ ဖြစ်ပြီး `last_id` တစ်ခုပဲ ရှောင်သဖြင့်
#    label တူတိုင်း **ထိပ်ဆုံး တစ်ခုတည်း** ကို ပြန်ပြန် ယူသည်。
#    ⇒ SFX pool (`sfxpool.NOREPEAT=6`) နည်းတူ ဝင်းဒိုး + seed နဲ့ လှည့်သည်。
# ⚠️ **ဦးစားပေး အစီအစဉ်ကို မပျက်စေရ** — မသုံးရသေးတာများကို ရှေ့တင်ရုံသာ
#    (အဲဒီအုပ်စု အတွင်းမှာ verified best-of order အတိုင်း ကျန်သည်)。
NOREPEAT = 6

# ⚠️ **keyword pop က `kinetic.word_pop` တစ်ခုတည်း hardcode ခဲ့သည်** ⇒ pop
#    အားလုံး တူတူ (တိုင်းချက်: ဝါကျ ၁၀ ကြောင်းမှာ ၃ ခါ)。 props ပုံစံ
#    (`text`/`size`/`y`/`fill`) တူတာ ၃၅ ခု ရှိပြီး `tools/popcheck.py` က
#    တစ်ခုချင်း ဆောက်ပြီး တိုင်းရာ **၂၁ ခု** အောင်သည် —
#      exit animation ၄ (နောက်ဆုံး frame ဗလာ) · ဘောင်ကျော် ၁ · `fill`
#      မလက်ခံ ၃ · အမြင့် စံနဲ့ ၂၄–၃၁% ကွာ ၄ · အဓိပ္ပာယ် ပြောင်း ၂ ⇒ ပယ်。
#    ⚠️ `assets/pop_ok.txt` မရှိလျှင် `word_pop` တစ်ခုတည်း — ယခင်အတိုင်း。
_POPS = None


def _pops():
    """တိုင်းထားပြီးသော keyword pop template များ — `assets/pop_ok.txt`"""
    global _POPS
    if _POPS is not None:
        return _POPS
    out = []
    try:
        import os as _o
        q = _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))),
                         "assets", "pop_ok.txt")
        with open(q, encoding="utf-8") as f:
            for ln in f:
                ln = ln.split("#")[0].strip()
                if ln and "." in ln:
                    out.append(ln)
    except OSError:
        out = []
    _POPS = out or ["kinetic.word_pop"]
    return _POPS


def _rotate(cands, used, seed="", k=NOREPEAT):
    """မသုံးရသေးသော candidate များကို ရှေ့တင်သည် — seed နဲ့ လှည့်။"""
    if not cands:
        return []
    recent = set(list(used)[-k:])
    fresh = [c for c in cands if c not in recent]
    stale = [c for c in cands if c in recent]
    if fresh and seed:
        # ⚠️ ဗီဒီယိုအလိုက် ကွဲပြားစေရန် — တူညီသော seed ⇒ တူညီသော ရလဒ်
        import hashlib
        h = int.from_bytes(hashlib.sha1(str(seed).encode()).digest()[:4], "big")
        # ⚠️ **ရှေ့ဆုံး အနည်းငယ်အတွင်းသာ လှည့်ရမည်** (၂၀၂၆-၀၉-၂၅)。
        #    candidate စာရင်းက semantic ဦးစားပေး အစဉ်လိုက် ဖြစ်သည် —
        #    label-specific ရှေ့、ယေဘုယျ pool နောက်。 စာရင်း တစ်ခုလုံးကို
        #    cyclic shift လုပ်လျှင် pool ကြီးလာတဲ့အခါ (၁၁ → ၂၁၆)
        #    **ယေဘုယျ template က semantic ကို ကျော်တက်**သည် —
        #    `screen` ဝါကျက browser template အစား `prem2.word_pop` ရခဲ့သည်
        #    (`tests/test_planner.py` က ဖမ်းမိ)。
        #    ⇒ ရှေ့ဆုံး `HEAD` အတွင်းသာ လှည့်ပြီး ကျန်တာ အစဉ်အတိုင်း。
        # ⚠️ နယ်နိမိတ်ကို **ယေဘုယျ pool ဝင်သည့် နေရာ**ကနေ တွက်သည် —
        #    ကိန်းသေ ထားလျှင် label အလိုက် မကိုက်ပါ (`screen` မှာ
        #    label-specific ၁၁ ခုသာ ရှိပြီး `HEAD=12` က ကျော်သွားခဲ့)。
        try:
            _gen = set(_auto_candidates("fact"))
        except Exception:
            _gen = set()
        # ⚠️ **ရှေ့ကနေ ရေတွက်၍ မရ** — label-specific စာရင်းထဲမှာပင်
        #    ယေဘုယျ pool နဲ့ ထပ်နေသူ ပါနိုင်သည် (`screen` ရဲ့ index ၁ က
        #    `kinetic2.type_cursor` — ၂ ခုလုံးမှာ ပါသည်) ⇒ ပထမတစ်ခုမှာ
        #    ရပ်လျှင် k2=1 ဖြစ်ကာ fallback က ယေဘုယျအထိ လှည့်မိသည်。
        # ⇒ ယေဘုယျ pool က **အဆုံးမှာ တစ်စပ်တည်း** ဆက်တွဲထားသဖြင့်
        #   **နောက်ကနေ** ရေတွက်ပြီး အဲဒီ အစွန်းကို နယ်နိမိတ် ထားသည်。
        k2 = len(fresh)
        while k2 > 0 and fresh[k2 - 1] in _gen:
            k2 -= 1
        if k2 < 2:                      # label က ယေဘုယျ pool ကိုပဲ သုံးသည်
            k2 = min(len(fresh), 12)
        k2 = max(1, min(k2, len(fresh)))
        r = h % k2
        fresh = fresh[r:k2] + fresh[:r] + fresh[k2:]
    return fresh + stale


# ══ catalog အပြည့် သုံးခြင်း ═══════════════════════════════════
# ⚠️ ၂၀၂၆-၀၉-၂၂ တိုင်းချက် — `PROFILE_PREFER` နဲ့ `PREFER` က **လက်နဲ့ရေးထားသော
#    id စာရင်း**သာ ဖြစ်ပြီး profile တစ်ခုလျှင် ~၁၀ ခုသာ ပါသည်。 catalog မှာ
#    ၅၉၆ ခု · render စစ်ပြီးသား ၂၇၂ ခု ရှိပါလျက် planner က **~၃၀ ခု**ကိုသာ
#    ထိသည် ⇒ ဗီဒီယိုတိုင်း တစ်ပုံစံတည်း ဖြစ်ခဲ့ခြင်း ([[ikki-template-pools]])。
#    Zin: 「IKKI ကို motionkit 100% အသုံးပြုခွင့်ပေးလိုက်ပါ」
# ⇒ လက်ရေး စာရင်းကို **ရှေ့မှာ အတိအကျ ထား**ပြီး (အရည်အသွေး အစဉ်လိုက် မပျက်စေရန်)
#   catalog ကနေ ကျန်သမျှကို **နောက်က ဆက်တွဲ**သည်。 ဖယ်ထုတ်ခြင်း မရှိ。
# ⚠️ ဂိတ် ၃ ခု မဖြစ်မနေ ဖြတ်ရမည် — ① render စစ်ပြီးသား (`mkcat.verified()`)
#    ② `STRUCTURED` မဟုတ် (ASR စာသားကနေ ဖွဲ့စည်းပုံ data မမှန်းရ)
#    ③ `mockup`/`transition`/`motion` မပါ — အဲဒါတွေက overlay မဟုတ်、
#      role သီးသန့် လမ်းကြောင်း လိုသည် (ပုံ လို · ဘောင်အပြည့် ဖုံး)。
_AUTO_RULES = (
    ("number",    r"stat|num|count|pct|percent|metric|delta|roll|ring|score|price|big"),
    ("steps",     r"step|list|flow|order|process|timeline|stage|phase|seq"),
    ("checklist", r"check|tick|todo|task|done|correct"),
    ("compare",   r"cmp|vs|versus|compare|before|after|two|split|win|swap|pair"),
    ("hook",      r"hook|question|stop|scroll|open|intro|punch|q$|big_q"),
    ("section",   r"title|chapter|topic|section|third|ident|header|bumper|kicker|lower"),
    ("warning",   r"red|warn|alert|strike|wrong|error|risk|danger|caution"),
    ("location",  r"location|place|map|pin|geo|city|country"),
    ("screen",    r"brows|browser|phone|app|window|search|notif|tab|cursor|ui_|screen"),
    ("fact",      r"call|note|fact|quote|statement|key|tag|under|box|pill|hl|"
                  r"emphas|highlight|type_|word|line|text|caption"),
)
_AUTO = None


def _auto_candidates(label):
    """catalog ကနေ **စစ်ပြီးသား** template များကို semantic အညွှန်းအလိုက် ခွဲသည်。"""
    global _AUTO
    if _AUTO is not None:
        return _AUTO.get(label, [])
    import re
    try:
        import gfxcat as GC, mkcat as MK
    except ImportError:
        from core import gfxcat as GC, mkcat as MK
    try:
        ok = MK.verified()
        cat = GC.catalog()
    except Exception:
        _AUTO = {}
        return []
    out = {k: [] for k in FAMILY}
    for e in cat:
        tid = e.get("id") or ""
        if tid not in ok or tid in STRUCTURED:
            continue
        if e.get("category") in ("mockup", "transition", "motion"):
            continue
        nm = tid.split(".", 1)[-1]
        labs = {lab for lab, pat in _AUTO_RULES if re.search(pat, nm)}
        if e.get("category") == "ui":
            labs.add("screen")
        if e.get("category") == "chart":
            labs |= {"number", "compare"}
        # ⚠️ ဘယ်အညွှန်းနဲ့မှ မကိုက်လျှင် **ဘယ်တော့မှ သုံးဖြစ်မည် မဟုတ်** ⇒
        #    ယေဘုယျ အညွှန်း `fact` ထဲ ထည့်သည်。
        if not labs:
            labs = {"fact"}
        for lab in labs:
            if lab in out:
                out[lab].append(tid)
    # ⚠️ **အက္ခရာစဉ် မစီရ** (၂၀၂၆-၀၉-၂၅)。 `v.sort()` က `callouts.*`
    #    (မျဉ်း/မြှား အသေးလေးတွေ) ကို **အမြဲ ရှေ့ဆုံး** တင်ပြီး `prem*`
    #    (ကတ်ကြီး ဒီဇိုင်းတွေ) ကို နောက်ကျစေသည် — ယေဘုယျ pool ၂၃၁ ခုရဲ့
    #    ရှေ့ဆုံး ၁၀ ခု **အားလုံး `callout`** ဖြစ်ခဲ့သည်。 ZAE render မှာ
    #    `stack_call` · `map_locator` စသည် ရွေးမိခြင်းရဲ့ အကြောင်းရင်း
    #    (Zin: 「Graphic တွေက ဒီထက်ပိုမိုက်တာ သုံးစေချင်တယ် · size ပိုကြီး」)。
    # ⚠️ **category အလိုက် စီသည်** — category က catalog မှာ ရှိပြီးသား
    #    (မှန်းဆ မဟုတ်)。 ဘောင်အပြည့်/data ကတ်/title က အကြီးဆုံးနဲ့
    #    ဒီဇိုင်းဆန်ဆုံး ⇒ ရှေ့。 `callout` က အသေးဆုံး ⇒ နောက်ဆုံး。
    #    အဆင့်တူအတွင်း အက္ခရာစဉ် ⇒ ရလဒ် တည်ငြိမ်သည်。
    # ⚠️ **မိသားစု အဆင့်က category ထက် အထက်** — Zin ၂၀၂၆-၀၉-၂၅ မှာ
    #    「Premium ဆန်တဲ့ ဒီဇိုင်းတွေကို ဦးစားပေး」ဟု ဆိုပြီး မိသားစု
    #    စာရင်း တိုက်ရိုက် ပေးသည်: `prem6` · `odo` · `dash` · `thm.cmp_*` ·
    #    `thm.cut_*` · `insert`。 ⚠️ `prem6.*` ရဲ့ category က **`callout`**
    #    ဖြစ်သဖြင့် category တစ်ခုတည်းနဲ့ စီလျှင် Zin အတိအလင်း တောင်းသော
    #    မိသားစုက **နောက်ဆုံး** ရောက်မည် ⇒ မိသားစုကို ရှေ့မှာ ထားရသည်。
    _FAM = {}
    for _t, _fs in (
        (0, ("prem", "prem2", "prem3", "prem4", "prem5", "prem6", "prem7",
             "odo", "dash", "insert", "thm", "infogfx", "qcard")),
        (1, ("charts", "maps", "titles", "titles2", "titles3",
             "mockups", "mockups2", "brows", "social")),
        (2, ("kinetic", "kinetic2", "kinetic3", "kin4", "typo", "typo2",
             "typew", "capt", "cine", "glitch", "retro", "motionfx")),
        (3, ("callouts",))):
        for _f in _fs:
            _FAM[_f] = _t
    # အဆင့်တူ မိသားစုအတွင်း — ဖုံးအုပ်မှု/ဒီဇိုင်း ကြီးမားမှု အလိုက်
    _RANK = {"cutaway": 0, "board": 1, "infographic": 2, "chart": 2,
             "explainer": 3, "title": 4, "mockup": 5, "typography": 6,
             "text": 7, "callout": 9}
    _cat = {}
    for e in cat:
        _cat[e.get("id") or ""] = (e.get("category") or "").lower()
    for v in out.values():
        v.sort(key=lambda t: (_FAM.get(t.split(".")[0], 2),
                              _RANK.get(_cat.get(t, ""), 8), t))
    _AUTO = out
    return _AUTO.get(label, [])


def _profile_candidates(label, profile, last_id=None):
    """Profile + semantic label → allowed template IDs.

    `premium` ကို special-case လုပ်ထားသည်: Headtop pack ကိုပါ သုံးပြီး
    ယခင် verified best-of order ကို မပြောင်းစေပါ။ အခြား profile မှာတော့
    user ရွေးထားသော visual language ကို ဖျက်ပစ်မိမည်မဟုတ်အောင် explicit
    candidate list ကနေသာ ရွေးသည်။
    """
    prof = PROFILE_PREFER.get(str(profile or "premium"))
    cands = list((prof or {}).get(label) or [])
    if not cands:
        fam = FAMILY.get(label)
        cands = list(PREFER.get(label) or (MF.HEADTOP.get(fam) if fam else []) or [])
    seen = set(cands)
    cands += [c for c in _auto_candidates(label) if c not in seen]
    # ⚠️ **ဗလာ အညွှန်းကို ယေဘုယျ pool နဲ့ ဖြည့်ရမည်** (၂၀၂၆-၀၉-၂၅ တိုင်းချက်) —
    #    `plain` · `quote` · `list` ၃ ခုမှာ candidate **၀** ဖြစ်နေသည်。
    #    တကယ့် job (`j_c42e5c142058`) ရဲ့ အညွှန်း ဖြန့်ကျက်မှုက
    #    `hook ၁ · number ၇ · **plain ၉**` ⇒ ဝါကျ ၁၇ ကြောင်းမှာ **၉ ကြောင်း
    #    ဂရပ်ဖစ် လုံးဝ မရနိုင်**ခဲ့ပါ。 ကျန်တာကလည်း pool သေးသဖြင့်
    #    `headtop.ht_outline_title` က တစ်ပုဒ်တည်းမှာ **၃–၄ ကြိမ်** ထပ်ခဲ့သည်
    #    (Zin: 「မထပ်အောင်」)。 recipe က ဂရပ်ဖစ် ၂၄ ခု တောင်းပါလျက် **၅ ခု**သာ
    #    ထွက်ခဲ့ခြင်းရဲ့ အဓိက အကြောင်းရင်း ဖြစ်သည်。
    # ⚠️ `fact` က ယေဘုယျ အိမ် — အညွှန်း မကိုက်သမျှ အားလုံး အဲဒီထဲ ကျသည်
    #    (`_auto_candidates`)。 ၂၂၀ ခု ရှိပြီး ၁၄၁ ခု ဖြည့်လို့ရသည်。
    # ⚠️ **ပမာဏကို ဒီနေရာက မဆုံးဖြတ်ပါ** — `gfx_share` QC ဘောင် (၀.၁၇–၀.၂၅)
    #    က နောက်မှာ ကန့်သတ်ဆဲ ဖြစ်၍ 「ဝါကျတိုင်း ကတ်」 မဖြစ်ပါ。 ဒီမှာ
    #    လုပ်တာက **ရွေးစရာ ရှိအောင်** ဖြစ်သည်。
    # ⚠️ **ဗလာ အခါမှသာ မဟုတ် — အမြဲ ဆက်တွဲရမည်**。 `section` က ၂၂ ခုသာ
    #    ရှိပြီး ဖြည့်လို့ရတာ ၉ ခု ⇒ ဝါကျ ၄ ကြောင်းလောက်နဲ့ ကုန်ကာ ထပ်စ ပြန်
    #    ဖြစ်သည်。 semantic ဦးစားပေးမှု မပျက်စေရန် label-specific ကို **ရှေ့**
    #    မှာ ထားပြီး ယေဘုယျ pool ကို **နောက်က** ဆက်တွဲသည် (လက်ရေး စာရင်းကို
    #    catalog နဲ့ ဆက်တွဲသလိုပင်)。
    if label != "fact":
        _seen2 = set(cands)
        cands += [c for c in _auto_candidates("fact") if c not in _seen2]
    return [c for c in cands if c != last_id]

# ── စွမ်းအင် အဆင့် ──────────────────────────────────────────
# `gap` — မြင်ကွင်း ပြောင်းမှု ကြားကာလ ပစ်မှတ် (စက္ကန့်)
ENERGY = {
    "minimal":  dict(gap=11.0, punch=False, transitions=False),
    "standard": dict(gap=6.5,  punch=True,  transitions=True),
    "dynamic":  dict(gap=4.5,  punch=True,  transitions=True),
}

# ⚠️ စာသားကနေ **ပုံသဏ္ဌာန် မှန်မှန် မဆောက်နိုင်သော** template များ。
#    ဒါတွေက ကိန်းဂဏန်း ဖွဲ့စည်းပုံ လိုသည် — ASR စာသားကနေ မှန်းဆ၍ မရပါ。
STRUCTURED = {
    "infogfx.compare_bar",     # rows = [(စာသား, ဘယ်, ညာ)] ၃ လုံးတွဲ
    "infogfx.timeline",        # points = ဖွဲ့စည်းပုံ ရှိသော စာရင်း
}

DIGITS = set("0123456789" + "".join(chr(0x1040 + i) for i in range(10)))

PROMPT = """မြန်မာလို စကားပြော ဗီဒီယိုတစ်ခုရဲ့ စာကြောင်းများ ဖြစ်သည်။
စာကြောင်းတစ်ခုချင်းကို အောက်ပါ အမျိုးအစား **တစ်ခုတည်း** သတ်မှတ်ပါ —

hook      ဗီဒီယိုအစ စိတ်ဝင်စားစေသော မေးခွန်း/ထိတ်လန့်ဖွယ် ဖွင့်ဆိုချက်
section   ခေါင်းစဉ် အသစ် စတင်ခြင်း
fact      အရေးကြီး အချက်အလက် တစ်ခု
number    ဂဏန်း/ရာခိုင်နှုန်း/ကာလ တကယ် ပြောထားသည်
steps     အဆင့်ဆင့် လုပ်ငန်းစဉ်
checklist လိုအပ်ချက် / စာရင်း
compare   နှိုင်းယှဉ်ချက်
location  နေရာ / ကျောင်း / ရုံး ဖော်ပြချက်
screen    app / website / browser / dashboard ကို screen ဖြင့် ပြသရမည့်အချက်
warning   သတိပေးချက် / ပြဿနာ / အန္တရာယ်
plain     အထက်ပါ ဘယ်ဟာမှ မဟုတ် (အများစုက ဒါ ဖြစ်သင့်သည်)

⚠️ အများစုကို `plain` ထားပါ။ တကယ် ထင်ရှားမှသာ အခြား အမျိုးအစား ပေးပါ။
⚠️ `number` ကို **ဂဏန်း တကယ် ပါမှသာ** ပေးပါ။
JSON array သာ ပြန်ပါ — ပုံစံ: [{"line":1,"label":"plain"}, ...]

စာကြောင်းများ:
%s"""


def _has_digit(t):
    return any(c in DIGITS for c in (t or ""))


def _heuristic(segs):
    """Gemini မရလျှင် — စာသားကြည့်ပြီး ခန့်မှန်းသည်

    ⚠️ ရိုးရှင်းပေမယ့် **ဘယ်တော့မှ မမှားသော ပုံစံ** ထုတ်ပေးသည်。
       ဂဏန်း မပါဘဲ `number` မပေးပါ ⇒ QC ရဲ့ `number_without_data` မဖြစ်。
    """
    out = []
    for i, s in enumerate(segs):
        t = (s.get("text") or "").strip()
        lab = "plain"
        if i == 0:
            lab = "hook"
        elif _has_digit(t):
            lab = "number"
        elif re.search(r"(လား|လဲ)\s*[?။]?\s*$", t):
            lab = "fact"
        elif any(k in t for k in ("အဆင့်", "ပထမ", "ဒုတိယ", "နည်းလမ်း")):
            lab = "steps"
        elif any(k in t for k in ("လိုအပ်", "ရှိရမယ်", "ရှိရမည်")):
            lab = "checklist"
        elif any(k in t for k in ("သတိ", "ပြဿနာ", "အန္တရာယ်", "မရ")):
            lab = "warning"
        # UI / browser reference ကို နေရာ (location) သို့ မပို့ရ။ ဒီ label က
        # generic animated mockup အတွက်သာ ဖြစ်ပြီး user asset မရှိလျှင် real
        # app screenshot ကို မဖန်တီး/မဟန်ဆောင်ပါ။
        elif (any(k in t.lower() for k in ("app", "website", "web site", "browser",
                                             "screen", "dashboard", "ui", "link", "page"))
              or any(k in t for k in ("အက်ပ်", "ဝဘ်", "ဝက်ဘ်", "စကရင်",
                                      "မျက်နှာပြင်", "လင့်"))):
            lab = "screen"
        elif any(k in t for k in ("ကျောင်း", "ရုံး", "နေရာ", "မြို့")):
            lab = "location"
        out.append(lab)
    return out


def annotate(segs, log=print):
    """ဝါကျတစ်ခုချင်းအတွက် အညွှန်း — Gemini、မရလျှင် heuristic"""
    if not segs:
        return []
    lines = "\n".join(f"{i+1}. {s.get('text','')}" for i, s in enumerate(segs[:200]))
    body = {"contents": [{"parts": [{"text": PROMPT % lines}]}],
            "generationConfig": {"temperature": 0.1}}
    for attempt in range(2):
        try:
            G.throttle()
            r = urllib.request.Request(
                G.endpoint(MODEL), data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text", "")
                          for p in d["candidates"][0]["content"]["parts"])
            m = re.search(r"\[.*\]", txt, re.S)
            if not m:
                raise ValueError("JSON မတွေ့")
            out = ["plain"] * len(segs)
            bad = 0
            for it in json.loads(m.group(0)):
                n = int(it.get("line", 0)) - 1
                lab = str(it.get("label", "plain"))
                if not (0 <= n < len(segs)):
                    bad += 1
                    continue
                # ⚠️ **ပိတ်ထားသော စာရင်းနဲ့ စစ်ရမည်** — Gemini က
                #    အမျိုးအစား တီထွင်တတ်သည်。
                out[n] = lab if lab in LABELS else "plain"
            # ⚠️ ဂဏန်း မပါဘဲ `number` ပေးလျှင် **ပြန်ဖြုတ်ရမည်** —
            #    မဟုတ်လျှင် odo template က ဂဏန်းမဲ့ ထွက်မည်。
            fixed = 0
            for i, lab in enumerate(out):
                if lab == "number" and not _has_digit(segs[i].get("text")):
                    out[i] = "fact"
                    fixed += 1
            if bad or fixed:
                log(f"  planner · index မှား {bad} · ဂဏန်းမဲ့ number {fixed} ပြင်ပြီး")
            return out
        except Exception as e:
            G.log_fail("headtop_annotate", attempt + 1, 2, None, str(e)[:120],
                       final=(attempt == 1))
    log("  ⚠️ planner · Gemini မရ — heuristic နဲ့ ဆက်သွားသည်")
    return _heuristic(segs)



def split2(text, maxlen=34):
    """စာသားကို **အများဆုံး ၂ ကြောင်း** ခွဲသည်

    ⚠️ မြန်မာစာမှာ **စာလုံးတစ်လုံးချင်း မခွဲရ** — glyph shaping ပျက်သည်
       (ေ ိ ် စသည် အသီးသီး ကွဲသွားမည်)。 ⇒ **space နေရာမှာသာ** ခွဲသည်。
       space မရှိလျှင် တစ်ကြောင်းတည်း ထားလိုက်သည် — မခွဲဘဲ ကျန်တာက
       ပျက်နေတာထက် ကောင်းသည်。
    """
    t = " ".join((text or "").split())
    if len(t) <= maxlen or " " not in t:
        return [t] if t else []
    words = t.split(" ")
    best, bi = None, 1
    for i in range(1, len(words)):
        a = " ".join(words[:i]); b = " ".join(words[i:])
        d = abs(len(a) - len(b))
        if best is None or d < best:
            best, bi = d, i
    return [" ".join(words[:bi]), " ".join(words[bi:])]


def _first_number(text):
    """ဝါကျထဲက ပထမ ဂဏန်း — မတွေ့လျှင် None"""
    m = re.search(r"[0-9\u1040-\u1049]+(?:[.,][0-9\u1040-\u1049]+)?", text or "")
    return m.group(0) if m else None


_CL = re.compile(r"[\u1000-\u102A\u103F\u104C-\u104F\u0020-\u007E]"
                 r"[\u102B-\u103E\u1039\u1040-\u104B\uFE00-\uFE0F]*")


def _ncl(t):
    """မြင်ရသော စာလုံး အရေအတွက် (မြန်မာ cluster)

    ⚠️ `len()` က **code point** ရေတွက်သည် — 「ပြီး」က ၄ ခု ဖြစ်ပြီး
       မြင်ရတာ ၁ လုံးသာ。 ⇒ မြန်မာစာကို အလွန်အကျွံ တိုအောင် ဖြတ်မိသည်
       (「Language school နှစ်နှစ်တက်ပြီးတော့」 = code point ၃၅ · cluster ၂၅)。
    """
    out = _CL.findall(t or "")
    return len(out) if sum(len(x) for x in out) == len(t or "") else len(t or "")


def _short(text, n=26):
    """ကတ်ပေါ် တင်ရန် အတိုချုံး — **space မှာသာ ဖြတ်သည်**

    ⚠️ `t[:n]` ဟု တိုက်ရိုက် ဖြတ်လျှင် မြန်မာစာလုံးတစ်လုံး အလယ်မှာ ပြတ်သည် —
       `IKKI_Headtop_16s.mp4` ၁.၅s မှာ 「…တက်ပြီးတ」ဟု ထွက်ခဲ့သည်
       (「တော့」 ရဲ့ 「ော့」 ပျောက်)。 ဗျည်းတွဲ/သရ က code point သီးသန့်
       ဖြစ်သဖြင့် စာလုံးရေ နဲ့ ဖြတ်၍ **လုံးဝ မရ**。
    ⚠️ `n` အတွင်း space မရှိလျှင် **မဖြတ်ဘဲ အပြည့်** ပြန်ပေးသည် —
       စာလုံး ပျက်တာထက် ကတ် ရှည်တာက သာသည် (`split2()` နဲ့ တစ်သဘောတည်း)。
    """
    t = " ".join((text or "").split())
    if _ncl(t) <= n:
        return t
    words, out = t.split(" "), []
    for w in words:
        cand = out + [w]
        if out and _ncl(" ".join(cand)) > n:
            break
        out = cand
    return " ".join(out) if out else t


def _num_rows(text):
    """စာသားကနေ **(အညွှန်း, ကိန်း)** အတွဲများ — မတွေ့လျှင် ဗလာ

    ⚠️ ကိန်းကို **မတီထွင်ရ** — စာသားထဲ တကယ် ပါမှသာ ယူသည်。 မြန်မာ ဂဏန်း
       (၀–၉) နဲ့ အာရဗီ ဂဏန်း ၂ မျိုးလုံး ကို ကိုင်သည်。
    """
    import re as _re
    out = []
    for part in _re.split(r"[၊။,;]|\s{2,}", str(text or "")):
        m = _re.search(r"([0-9၀-၉]+(?:\.[0-9၀-၉]+)?)", part)
        if not m:
            continue
        lab = (part[:m.start()] + part[m.end():]).strip(" ·-—:\t")
        if len(lab) < 2:
            continue
        v = m.group(1)
        v = "".join(str(ord(c) - 0x1040) if "၀" <= c <= "၉" else c
                    for c in v)
        try:
            out.append((lab[:18], float(v)))
        except ValueError:
            continue
    return out


def fill(cid, label, text):
    """template ရဲ့ **required param အတိုင်း** ဖြည့်သည် — မဖြည့်နိုင်လျှင် None

    ⚠️ param နာမည်ကို **မှန်းဆ မရေးရ** — manifest ကနေ ဖတ်ရသည်。
       ငါ `text`/`color` ဟု မှန်းဆရေးမိပြီး schema က ဖမ်းခဲ့သည်
       (`capt.multi_line` က `lines`/`col` ယူသည်)。
    """
    e = MF.entry(cid)
    if not e:
        return None
    # ⚠️ **ပုံသဏ္ဌာန် မတည်ဆောက်နိုင်သော template ကို လုံးဝ မသုံးရ**。
    #    `infogfx.compare_bar` ရဲ့ `rows` က **၃ လုံးတွဲ** (စာသား, ဘယ်, ညာ)
    #    လိုသည် — စာသား စာရင်း ပေးမိ၍ render ချိန်မှာ
    #    `ValueError: not enough values to unpack` ဖြစ်ခဲ့သည်
    #    (၂၀၂၆-၀၉-၂၁)。 schema က **နာမည်နဲ့ ရှိမရှိ**သာ စစ်ပြီး
    #    ပုံသဏ္ဌာန် မစစ်နိုင်ပါ ⇒ ဒီမှာ ပိတ်ရသည်。
    #    ⚠️ ဂဏန်း ၂ ခု တကယ် မပါဘဲ နှိုင်းယှဉ်ချက် မဆွဲရ (Zin ရဲ့
    #       「Never add a chart without factual data」နဲ့ တူညီသော စည်းမျဉ်း)。
    if cid in STRUCTURED:
        return None
    # ⚠️ **chart က ကိန်းအတွဲ မရှိဘဲ မဆွဲရ** (၂၀၂၆-၀၉-၂၅)。 `rows` ကို
    #    စာလုံး စာရင်း ပေးမိသဖြင့် `charts.stacked_bar` က render ချိန်မှာ
    #    `ValueError: too many values to unpack (expected 2)` နဲ့ ကျပြီး
    #    ဂရပ်ဖစ် တစ်ခု **ပျောက်**ခဲ့သည် (j_c42e5c142058)。
    # ⚠️ manifest နဲ့ ခွဲ၍ **မရ** — `charts.stacked_bar` ရော
    #    `prem.list_reveal` ရော `rows: list` ဟုသာ ပြောသည်、ဒါပေမယ့်
    #    ဒုတိယက စာလုံး စာရင်းနဲ့ အလုပ်ဖြစ်သည် ⇒ **category** နဲ့ ခွဲရသည်。
    # ⚠️ ASR စာသားမှာ အညွှန်းတွဲ ကိန်း ၂ ခု ရှိခဲမည် ⇒ chart အများစု
    #    ကျော်သွားမည် — အဲဒါ **မှန်**သည် (「Never add a chart without
    #    factual data」)。 ကိန်း မှန်းဆ ဆွဲတာထက် မဆွဲတာ ကောင်းသည်。
    try:
        _cat = (e.get("category") or "").lower()
    except AttributeError:
        _cat = ""
    _chart_rows = None
    if _cat == "chart":
        _rq = {q.get("name") for q in (e.get("params") or [])
               if q.get("required")}
        if "rows" in _rq:
            _chart_rows = _num_rows(text)
            if len(_chart_rows) < 2:
                return None
    req = [q["name"] for q in (e.get("params") or [])
           if q.get("required") and not q.get("auto")]
    two = split2(text)
    num = _first_number(text)
    hot = _short(text, 14)
    m = {
        "lines":  two,
        "line1":  two[0] if two else "",
        "line2":  two[1] if len(two) > 1 else "",
        "text":   _short(text, 30),
        "q":      _short(text, 32),
        "title":  _short(text, 24),
        "name":   _short(text, 22),
        "place":  _short(text, 20),
        "before": two[0] if two else _short(text, 20),
        "hot":    hot,
        "after":  two[1] if len(two) > 1 else "",
        "items":  two or [_short(text, 24)],
        "points": two or [_short(text, 24)],
        # ⚠️ chart ဆိုလျှင် **(အညွှန်း, ကိန်း) အတွဲ** ဖြစ်ရမည် — စာလုံး
        #    စာရင်း ပေးလျှင် `ValueError: too many values to unpack` ကျမည်。
        "rows":   _chart_rows or two or [_short(text, 24)],
        "left":   two[0] if two else _short(text, 12),
        "right":  two[1] if len(two) > 1 else _short(text, 12),
        "value":  num or "",
        "target": num or "",
        "pct":    num or "",
        "label":  _short(text, 18),
        "num":    num or "1",
    }
    out = {}
    for k in req:
        if k not in m:
            # ⚠️ မသိသော required param — **မှန်းဆ မဖြည့်ရ**、
            #    ဒီ template ကို ကျော်လိုက်သည်。
            return None
        v = m[k]
        if v in ("", [], None):
            return None
        out[k] = v
    return out

# ⚠️ semantic label → pack intent。 pack က `title`/`statement`/`chapter`/
#    `hook`/`emphasis`/`section` ကို လက်ခံသည် — FAMILY label နဲ့ မတူ ⇒ ချိတ်ရမည်。
PACK_INTENT = {"hook": "hook", "section": "section", "fact": "statement",
               "number": "number", "checklist": "checklist",
               "steps": "steps", "compare": "compare"}


def _pack_ids(lab):
    """label အတွက် **verify ပြီးသား** pack template များ — မရှိလျှင် ဗလာ

    ⚠️ `selectable()` က manifest စစ်ပြီးသား id ကိုသာ ပြန်ပေးသည်
       (spec §5: 「No planner may select a template until its manifest is
       valid」)。 ဒါကို မဖြတ်ရ。
    """
    it = PACK_INTENT.get(lab)
    if not it:
        return []
    try:
        try:
            import pack as _PK
        except ImportError:
            from core import pack as _PK
        ok = set(_PK.selectable())
        return [x for x in _PK.by_intent(it) if x in ok]
    except Exception:
        return []


_FULLSTAGE = None


def _fullstage_ids():
    """`assets/gfx_cutaway.txt` — **ဖုံးအုပ်မှု တိုင်းပြီး** ဖြတ်ပြောင်း id。

    ⚠️ **`gfx_fullstage.txt` ကို မသုံးရ**。 အဲဒါက `bbox` ကနေ ထုတ်ထားပြီး
       `bbox` က alpha > ၁၆ pixel ကို ရေတွက်သဖြင့် **စာတန်း** template
       (`prem5.karaoke_cap` · `word_pop_cap` · `hl_word_cap` …) တွေပါ
       ပါဝင်သည် — အဲဒါတွေကို ဖြတ်ပြောင်း လုပ်လျှင် စာတန်းက ပြောသူကို
       ဖုံးပစ်မည်。 ၂၀၂၆-၀၉-၂၄: ၃၉ ခုမှာ ၃၀ ခုက `ink` ၁.၀၀၀၀ တိတိ ⇒
       တိုင်းချက် ပျက်နေခြင်း。 `tools/gfx_cutaway.py` က alpha **အလယ်မှတ်**
       နဲ့ ပြန်တိုင်းသည်。
    ⚠️ ဖိုင် မရှိလျှင် **ဗလာ ပြန်**သည် — pack manifest ရဲ့ `fullFrame`
       တစ်ခုတည်း အလုပ်လုပ်မည်。 မတိုင်းရသေးဘဲ ခန့်မှန်းထည့်လျှင်
       စာတန်းကို ဖြတ်ပြောင်း လုပ်မိမည်。
    """
    global _FULLSTAGE
    if _FULLSTAGE is None:
        _FULLSTAGE = set()
        try:
            import os as _o
            q = _o.path.join(_o.path.dirname(_o.path.dirname(
                _o.path.abspath(__file__))), "assets", "gfx_cutaway.txt")
            with open(q, encoding="utf-8") as f:
                _FULLSTAGE = {l.strip() for l in f
                              if l.strip() and not l.startswith("#")}
        except OSError:
            pass
    return _FULLSTAGE


def _full_frame(tid):
    """ဘောင်အပြည့် ဖုံးသော template လား

    ⚠️ ယခင်က **pack manifest ရဲ့ `fullFrame`** ကိုသာ ကြည့်ခဲ့သဖြင့်
       `assets/gfx_fullstage.txt` ထဲက **catalog template ၃၉ ခု** ကို
       ဘောင်အပြည့် ဟု **လုံးဝ မမှတ်မိ**ခဲ့ — ဘေးကတ် အဖြစ် သေးသေးလေး
       ချခဲ့ရာ ကြည့်သူ မမြင်ရပါ (၂၀၂၆-၀၉-၂၄ တိုင်းပြီး)。
    """
    if tid in _fullstage_ids():
        return True
    try:
        try:
            import pack as _PK
        except ImportError:
            from core import pack as _PK
        return bool((_PK.template(tid) or {}).get("fullFrame"))
    except Exception:
        return False


# ⚠️ pack template ရဲ့ စာသား slot — **စကားလုံး အများဆုံး**。 manifest ရဲ့
#    `maxChars` က စာလုံးရေ ဖြစ်ပြီး မြန်မာစာမှာ ဗျည်းတွဲ/သရ က code point
#    သီးသန့် ဖြစ်၍ ရှည်နေသည် ⇒ စကားလုံး အရေအတွက်နဲ့ ထပ်ကန့်သတ်သည်。
PACK_TEXT_WORDS = 4


def _pack_props(tid, lab, txt):
    """pack template ရဲ့ **required props** ဖြည့်သည် — မရလျှင် `None`

    ⚠️ manifest ရဲ့ `maxChars` ကို လိုက်နာရမည် — ကျော်လျှင် စာလုံး ပြတ်ပြီး
       မြန်မာစာ ဗျည်းတွဲ ပျက်နိုင်သည် ⇒ `_short()` (cluster-safe) နဲ့ ဖြတ်。
    """
    try:
        try:
            import pack as _PK
        except ImportError:
            from core import pack as _PK
        t = _PK.template(tid) or {}
        out = {}
        two = split2(txt)
        for k, spec in (t.get("props") or {}).items():
            if not spec.get("required"):
                continue
            mx = int(spec.get("maxChars") or 40)
            if spec.get("type") == "list":
                # ⚠️ စာရင်း — ဝါကျကို ခွဲသည်。 ၂ ခုအောက် ဆိုလျှင်
                #    စာရင်း မဖြစ်သေး ⇒ ဤ template ကို မသုံးရ。
                it = [x for x in (two or []) if x][:int(spec.get("maxItems") or 5)]
                if len(it) < 2:
                    return None
                # ⚠️ **စာရင်း item တွေလည်း ၄ လုံး ကန့်သတ်ရမည်** —
                #    「စာသားအားလုံး」(Zin ၂၀၂၆-၀၉-၂၄)。 list branch က
                #    `continue` နဲ့ စောစီးစွာ ထွက်သဖြင့် အောက်က ကန့်သတ်ချက်
                #    မထိမိခဲ့ (`ht_check_list` မှာ တိုင်းပြီး တွေ့)。
                def _cap4(_x):
                    _xw = _short(_x, mx).split()
                    return " ".join(_xw[:PACK_TEXT_WORDS]) \
                        if len(_xw) > PACK_TEXT_WORDS else _short(_x, mx)
                out[k] = [_cap4(x) for x in it]
                continue
            if spec.get("type") != "text":
                continue
            # ⚠️ `value` က **ဂဏန်း** ဖြစ်ရမည် — ဝါကျကို ၅ လုံး ဖြတ်ထည့်လျှင်
            #    「ဂျပန်မှာ အ」 လို အဓိပ္ပာယ်မဲ့ စာပိုင်း ဖြစ်ပြီး maxChars
            #    ဂိတ်ကိုလည်း ကျော်သည် (၂၀၂၆-၀၉-၂၁ render မှာ plan တစ်ခုလုံး
            #    fallback ကျခဲ့: 「'value' က 7 လုံး > 5」)。
            #    ⚠️ ဂဏန်း မပါလျှင် **ဤ template ကို မသုံးရ** — Zin ရဲ့
            #      「Never add a chart without factual data」နဲ့ တစ်သဘောတည်း。
            if k == "value":
                num = _first_number(txt)
                if not num:
                    return None
                # ⚠️ **ရက်စွဲ/ကိန်းသေး ကို stat အဖြစ် မပြရ** — ၂၀၂၆-၀၉-၂၄
                #    v5 render မှာ `ht_stat_ring` ရဲ့ အဝါစက်ဝိုင်းထဲ
                #    「စက်တင်ဘာလ **၂၉** ရက်နေ့」ကနေ ယူထားသော 「၂၉」ချည်း
                #    ပေါ်ခဲ့ပြီး label မပါ ⇒ ကြည့်သူအတွက် အဓိပ္ပာယ် မရှိ。
                #    ⇒ `keyword()` နဲ့ **တူညီသော စည်းမျဉ်း** — `%` ပါလျှင်
                #    ဒါမှမဟုတ် ဂဏန်း ၃ လုံးအထက် (ခုနှစ် · ပမာဏ) မှ လက်ခံ。
                _d = str(num).strip().strip("%").strip()
                if "%" not in str(txt) and "ရာခိုင်နှုန်း" not in str(txt) \
                        and len(_d) < 3:
                    return None
                out[k] = _short(str(num), mx)
                continue
            # ⚠️ `left`/`right` က **နှစ်ပိုင်း ခွဲ**ရမည် — တစ်ခုတည်း ထည့်လျှင်
            #    နှိုင်းယှဉ်ချက် မဖြစ်ပါ。
            if k in ("left", "right"):
                if len(two) < 2:
                    return None
                v = _short(two[0] if k == "left" else two[1], mx)
            else:
                v = _short(txt, mx)
            # ⚠️ **စကားလုံး ၄ လုံး ကန့်သတ်** (Zin ၂၀၂၆-၀၉-၂၄:「စာသားအားလုံး
            #    ၄ လုံး ကန့်သတ်ပါ」)。 `worker/run.py` ရဲ့ ကန့်သတ်ချက်က
            #    `gfx[*]["text"]` မှာသာ သက်ရောက်ပြီး **headtop pack** က
            #    ဤနေရာကနေ ဝါကျကို တိုက်ရိုက် ယူသဖြင့် မထိမိခဲ့ —
            #    v7 · v8 ၄၈.၈s မှာ `ht_outline_title` က ဝါကျ အပြည့် ပြပြီး
            #    အောက်က စာတန်းနဲ့ စာကြောင်းတူကာ ၂ ကြောင်း ကျိုးခဲ့သည်。
            # ⚠️ space နဲ့ ခွဲသည် — code point နဲ့ ဖြတ်လျှင် မြန်မာ ဗျည်းတွဲ ပျက်。
            _vw = (v or "").split()
            if len(_vw) > PACK_TEXT_WORDS:
                v = " ".join(_vw[:PACK_TEXT_WORDS])
            if not v:
                return None
            out[k] = v
        return out or None
    except Exception:
        return None


def _pick(family, labels_used, last_id):
    """မိသားစုထဲက template — **ဆက်တိုက် မတူစေရ**"""
    opts = [c for c in family if c in MF.ids()]
    if not opts:
        return None
    for c in opts:
        if c != last_id:
            return c
    return opts[0] if opts[0] != last_id else None


# ══ keyword pop ═══════════════════════════════════════════════
# ⚠️ `docs/HEADTALK_STYLE.md` — reference မှာ pop လုပ်ထားတာတွေက
#    `WHY?` · `2.DEVELOP` · `3.EXECUTE` · `Controlable` · `S.W.O.T Analysis`
#    ⇒ **တို · အလေးနက် · အများစုက Latin/ဂဏန်း**。 ဝါကျတစ်ခုလုံး မဟုတ်ပါ。
# ⚠️ မြန်မာစာလုံးကို pop မလုပ်ရ — ဗျည်းတွဲ/သရ က code point သီးသန့် ဖြစ်၍
#    template တွေက တစ်လုံးချင်း လှုပ်လျှင် ပုံပျက်မည် (Zin ရဲ့ စည်းမျဉ်း:
#    「never animate individual Unicode characters」)。 ⇒ Latin/ဂဏန်းသာ。
# ⚠️ `N4` · `N5` · `JLPT2` ကဲ့သို့ **အက္ခရာ+ဂဏန်း** ကို လက်ခံရမည် —
#    အဲဒါတွေက Zin ရဲ့ အကြောင်းအရာမှာ အရေးကြီးဆုံး ဝေါဟာရများ ဖြစ်သည်
#    (`assets/calib/glossary.json` မှာလည်း ပါပြီးသား)。
_LAT = re.compile(r"[A-Za-z][A-Za-z0-9.\-]{1,17}(?:\s+[A-Za-z][A-Za-z0-9.\-]{2,17})?")
_NUM = re.compile(r"[0-9\u1040-\u1049]+(?:[.,][0-9\u1040-\u1049]+)?\s*%?")
# ⚠️ အဓိပ္ပာယ် မရှိသော Latin — pop လုပ်လျှင် ရယ်စရာ ဖြစ်သည်
_STOP = {"the", "and", "for", "you", "that", "this", "with", "from",
         "are", "was", "have", "has", "but", "not", "can", "will"}


def keyword(text):
    """ဝါကျတစ်ခုကနေ pop လုပ်ထိုက်သော စကားလုံး — မရှိလျှင် `None`

    ⚠️ **အရှည်ဆုံးကို မယူရ** — reference မှာ `2.DEVELOP` ကဲ့သို့ နံပါတ်တွဲ
       ဒါမှမဟုတ် သီးသန့် နာမည် ဖြစ်သည်。 ⇒ ဂဏန်းပါလျှင် ဂဏန်း ဦးစားပေး。
    """
    t = " ".join((text or "").split())
    if not t:
        return None
    # ⚠️ **ဂဏန်းချည်းသက်သက် မယူရ** — ၂၀၂၆-၀၉-၂၄ render မှာ 「၂၉」ကို pop
    #    လုပ်ခဲ့ပြီး မျက်နှာပြင်ပေါ် **အဓိပ္ပာယ်မဲ့ အဝါကွက်** ဖြစ်ခဲ့သည်
    #    (မူရင်းဝါကျ — 「စက်တင်ဘာလ ၂၉ ရက်နေ့」)。 reference ရဲ့ နမူနာတွေက
    #    `2.DEVELOP` · `S.W.O.T` — **အကြောင်းအရာ တွဲပါ**သည်、ဂဏန်းချည်း မဟုတ်。
    #    ⇒ လက်ခံသည် — `%` ပါလျှင် (ရာခိုင်နှုန်း) · ဂဏန်း ၃ လုံးအထက်
    #    (ခုနှစ် · ပမာဏ — `၂၀၂၆` · `100`)。 ကျန်တာ Latin လမ်းကြောင်းသို့。
    for m in _NUM.finditer(t):
        v = m.group(0).strip()
        _d = v.strip("%").strip()
        if "%" in v and len(_d) >= 1:
            return v
        if len(_d) >= 3:
            return v
    # ⚠️ **စကားလုံးအလိုက် ခွဲပြီးမှ** stop word ဖယ်ရမည် — အရင်က regex ရဲ့
    #    ၂ လုံးတွဲကို အတုံးလိုက် စစ်ခဲ့သဖြင့် `the team` က `the` ကြောင့်
    #    တစ်ခုလုံး ပျက်ပြီး `this is` က `is` ကို ရွေးမိခဲ့သည် (၂၀၂၆-၀၉-၂၁)。
    words = [w.strip(".-") for w in re.findall(r"[A-Za-z][A-Za-z0-9.\-]*", t)]
    ok = [w for w in words
          if w.lower() not in _STOP
          and (len(w) >= 3 or any(c.isdigit() for c in w))]
    if not ok:
        return None
    best, bi = None, -1
    for k, w in enumerate(ok):
        if best is None or len(w) > len(best):
            best, bi = w, k
    # ⚠️ ဘေးချင်းကပ် စကားလုံး ၂ လုံးဆိုလျှင် တွဲသည် (`Language school`)
    if 0 <= bi < len(ok) - 1:
        a_i, b_i = words.index(ok[bi]), None
        try:
            b_i = words.index(ok[bi + 1])
        except ValueError:
            b_i = None
        if b_i is not None and b_i == a_i + 1 and len(best) + len(ok[bi + 1]) <= 22:
            best = best + " " + ok[bi + 1]
    return best



# ══ SFX — semantic event → role ═══════════════════════════════
# ⚠️ **AI က file path မရွေးရ** — role နာမည်သာ。 role ကို `sfxlib.ROLE`
#    (၂၂ ခု) နဲ့ `execute.to_sfx()` က စစ်သည်、မရှိလျှင် ကျော်သည်。
# ⚠️ 「A sound is an intentional part of a visual or semantic event」⇒
#    **ဂရပ်ဖစ် ဖြစ်ရပ်ပေါ်မှာသာ** ချသည်。 ဖြတ်မှတ်တိုင်း · စာတန်းတိုင်း
#    မချရ (Zin ရဲ့ စည်းမျဉ်း ၁ · 「no per-word SFX」)。
# ⚠️ P0 မှာ **ဂိတ် မထိရ** — `qc.SFX_MAX_PER_MIN` က ၁.၅/မိနစ် ဖြစ်နေဆဲ ⇒
#    ဒီမှာ အဲဒီဘောင်ထဲ ချသည်。 ပိုသိပ်သည်းသော profile ကို P1 မှာ
#    (density policy ရွှေ့ပြီးမှ) ဖွင့်ရမည်。
SFX_ROLE = {
    # ဖြစ်ရပ် အမျိုးအစား → (ရှေ့သံ, ထပ်သံ) · ရှေ့သံက `lead` စက္ကန့် စော
    "card":    ("whoosh_in", "latch"),     # ဘောင်အပြည့် ကတ် ဝင်လာ
    "pop":     (None, "pop"),              # keyword pop — တစ်ထပ်သာ
    "number":  ("swipe", "click"),         # ကိန်းဂဏန်း ပေါ်လာ
    "warning": ("whoosh_in", "impact"),    # သတိပေးချက်
    # ⚠️ ဖွင့်ချက်ရဲ့ ရှေ့သံကို `bed` ဖြစ်အောင် လဲထားသည် (၂၀၂၆-၀၉-၂၅) —
    #    Zin ကြိုက်သော `CINEMATIC-028` (ကြားရ ၄.၆s · ကွာ ၁၁.၂ dB) နဲ့
    #    `HIGH_TECH-002` (၄.၂s · ၁၅.၅ dB) က `riser` ဂိတ် ၃.၂s ကို ကျော်ပေမယ့်
    #    စွမ်းအင်က **စကား band ပြင်ပ** ဖြစ်၍ ဖွင့်ချက်မှာ ခံနေခြင်းက
    #    reference တွေရဲ့ ပုံစံ ဖြစ်သည်。 `bed` မှာ cue မရှိလျှင်
    #    `sfxpool.wav()` က `(None, None)` ပြန်ပြီး ရှေ့သံ ကျော်သွားမည်။
    "hook":    ("bed", "latch"),           # ဖွင့်ချက်
    "ui":      ("swipe", "click"),          # browser / phone / dashboard
}
# ⚠️ `FAMILY` ရဲ label → SFX အမျိုးအစား。 မြေပုံ မရှိလျှင် အားလုံး `card`
#    ဖြစ်ပြီး အသံ တစ်မျိုးတည်း ထွက်မည် — အော်အိုက် မရှိတော့。
# ⚠️ အောင့်မြဲမှု အဆင့် — နေရာ တစ်ခုထဲ ဖြစ်ရပ် ၂ ခု ပြိုလျှင် ဘယ်ဟာ ယူမလဲ
SFX_RANK = {"hook": 5, "warning": 4, "number": 3, "ui": 3, "card": 2, "pop": 1}
SEM = {"hook": "hook", "number": "number", "warning": "warning",
       "fact": "warning", "section": "card", "steps": "card",
       "checklist": "card", "compare": "card", "location": "card",
       "screen": "ui"}
SFX_LEAD = 0.18        # ရှေ့သံက ရုပ်ထက် ဘယ်လောက် စောလဲ
# WARN **anchor to the settle, not the start** (2026-09-25). `props.anchor`
#    already says `visual_settle` for the main cue, but the time used was the
#    event's `startTime` -- when the entrance BEGINS. The entrance runs 0.45 s,
#    so the hit fired ~0.47 s early, on the take-off. `dress.sfx()` was fixed
#    the same way; the two must agree or QC measures one thing and the render
#    produces another.
SFX_ENTER = 0.45       # = worker.EASE_ENT / dress.ENTER_DEF
SFX_DB = {"whoosh_in": -15, "riser_soft": -17, "swipe": -16,
          "latch": -17, "pop": -18, "click": -18, "impact": -14,
          # ⚠️ `bed` က ရှည်သဖြင့် **ပိုနိမ့်** ရမည် — စကားအောက်မှာ ခံသည်
          "bed": -22}


def sfx_plan(events, dur, per_min, log=None, style=None, out_dur=None):
    """`templateEvents` → `sfxEvents` · **ဂိတ်ဘောင်ထဲ** ကန့်သတ်သည်

    ⚠️ 「Layered sounds count as one sound moment if they share the same
       event」⇒ ဖြစ်ရပ်တစ်ခုရဲ့ အထပ်များကို **တစ်ခါတည်း** ယူ/ပယ်ရမည်。
       ခွဲယူလျှင် whoosh ကျန်ပြီး latch ပျောက်ကာ အသံ မပြည့်စုံဘဲ ဖြစ်မည်
       (`dress.sfx` ရဲ့ `LAYER_W` မှတ်ချက်နဲ့ တစ်သဘောတည်း)。
    """
    if not events or not dur or dur <= 0:
        return []
    moments = []
    for e in sorted(events, key=lambda x: x.get("startTime") or 0):
        st = (e.get("style") or {}).get("kind")
        kind = st if st in SFX_ROLE else "card"
        lead, main = SFX_ROLE.get(kind) or (None, None)
        if not main:
            continue
        at = float(e.get("startTime") or 0.0)
        moments.append((at, kind, lead, main, e.get("id")))
    if not moments:
        return []
    # ⚠️ အရင်က `gap = max(8, 60/per_min)` — ၁.၅/min ဆိုလျှင် **၄၀s**
    #    ဖြစ်သွားပြီး ဂိတ်ထက် ၅ ဆ တင်းခဲ့သည်。 အကွာနဲ့ နှုန်းက
    #    **ဂိတ် နှစ်ခု** — တစ်ခုထဲ နောက်တစ်ခုကို ထည့်မတွက်ရ。
    #    ⇒ အကွာက ပေါလစီက · အရေအတွက်က budget · ဖြန့်ကျကျမှုက bucket。
    try:
        import sfxpol as _PL
    except ImportError:
        from core import sfxpol as _PL
    _pol = _PL.clamp(dict(per_min=per_min), style=style)
    gap = _pol["gap"]
    # ⚠️ **budget ကို ဖြတ်ပြီး အရှည်နဲ့ တွက်ရမည်** — QC က ထွက်ဖိုင်ပေါ်မှာ
    #    တိုင်းသည်。 ၂၀၂၆-၀၉-၂၁ j_1f9561de04b3: မူရင်း ၁၇၈.၇s နဲ့ တွက်၍
    #    cue ၁၇ ခု ခွင့်ပြုခဲ့ရာ ဖြတ်ချက်က ၄၉% ဖယ်ပြီး ထွက် ၆၉.၃s သာ ဖြစ်သဖြင့်
    #    **၆.၉၃/min** ဖြစ်ကာ ဂိတ် (≤၆.၀) ကျခဲ့သည် — ဂရပ်ဖစ်မှာ ဖြစ်ဖူးသော
    #    「source vs cut time」အမှားမျိုးပင်。
    #    ⚠️ ဖြစ်ရပ် အချိန်မှတ်တွေက **မူရင်း timeline** အတိုင်း ကျန်ရမည် —
    #       `omap` က နောက်မှ ပြောင်းသည် ⇒ `dur` ကို မထိရ、budget သာ ပြောင်း。
    _bd = float(out_dur) if (out_dur and float(out_dur) > 0) else float(dur)
    cap = _PL.budget(_pol, _bd)
    if log and out_dur and abs(_bd - float(dur)) > 1.0:
        log(f"  SFX budget — ဖြတ်ပြီး {_bd:.0f}s နဲ့ တွက် "
            f"(မူရင်း {float(dur):.0f}s မဟုတ်) ⇒ အများဆုံး {cap} ခု")

    # ⚠️ **အရေးကြီးဆုံးကို ရွေးရမည်** — အရင်က ရှေ့က cap ခုကို ပဲ ယူခဲ့သဖြင့်
    #    ဗီဒီယို နောက်ပိုင်းမှာ အသံ တိတ်ဆိတ်နေစေသည်。
    # ⚠️ ဗုတ်ထဲ ခွဲပြီး တစ်ပိုင်းစီ ယူတာကိုလည်း စွန့်လွတ်ခဲ့ပြီ (၂၀၂၆-၀၉-၂၁) —
    #    အကွာက ဗုတ်အကျယ် (dur/cap) ဖြစ်သွားပြီး ဂိတ်ရဲ ၈s က အလကာ。
    #    ⇒ **အရေးပါမှု အစစ်** · အကွာ ၆s ကြီးမှ လက်ခံ · cap ထိ — ဗီဒီယိုရဲ
    #      အရေးကြီးတဲ့ အချိန်တွေက ကိုယ်တိုင် ပျံ့နှံ့နေသဖြင့် ပျံ့နှံ့သွားမည်。
    keep = []
    for m in sorted(moments, key=lambda x: (-SFX_RANK.get(x[1], 0), x[0])):
        if len(keep) >= cap:
            break
        if all(abs(m[0] - k[0]) >= gap for k in keep):
            keep.append(m)
    keep.sort(key=lambda m: m[0])
    out, n = [], 0
    for at, kind, lead, main, eid in keep:
        _st = at + SFX_ENTER                 # ကတ် အပြည့် ပေါ်ချိန်
        for role, off in ((lead, -SFX_LEAD), (main, 0.0)):
            if not role:
                continue
            t = max(0.0, min(dur - 0.05, _st + off))
            # ⚠️ ရှေ့သံက ဘောင်အစမှာ ကပ်သွားလျှင် **ထပ်နေမည်** —
            #    ၂ ခုလုံး ၀.၀၀s ဖြစ်ပြီး အထပ် အဓိပ္ပာယ် ပျက်သည်
            #    (၂၀၂၆-၀၉-၂၁ ဖမ်းမိ)。 ⇒ ကပ်လျှင် ရှေ့သံ ချန်သည်。
            if off < 0 and abs(t - _st) < SFX_LEAD * 0.5:
                continue
            n += 1
            out.append(dict(
                id=f"sfx{n:03d}", startTime=round(t, 2),
                endTime=round(min(dur, t + 0.6), 2),
                layer="sfx", type="sfx",
                props=dict(role=role, db=SFX_DB.get(role, -16),
                           anchor="visual_settle" if off == 0 else "visual_enter",
                           priority="medium", event=eid),
                style=dict(kind=kind),
                reason=f"「{kind}」ဖြစ်ရပ် — {'ဝင်လာ' if off else 'ကျနေရာ'}",
                confidence=0.7))
    if log:
        # ⚠️ **တကယ် သုံးတဲ့ ကိန်းကို ပြရမည်** — `per_min` က ဝင်လာတဲ့
        #    argument သာ ဖြစ်ပြီး profile က လွှမ်းနိုင်သည်。 အဟောင်းကို
        #    ပြလျှင် 「၁.၅/min」 ဟု မြင်ရပြီး တကယ် ၆.၀ ဖြစ်နေသည်。
        log(f"  SFX plan · အသံအခိုက် {len(keep)}/{len(moments)} · ဖြစ်ရပ် {len(out)} "
            f"· ဘောင် {_pol['per_min']:.1f}/မိနစ် · ကွာ ≥{gap:.1f}s"
            + (" (တိုင်းထား)" if _pol.get("measured") else ""))
    return out


def build(segs, labels, dur, opts=None, video_id="src"):
    """အညွှန်း → plan (ကုဒ်က တည်ဆောက်သည်、AI မဟုတ်)"""
    o = dict(opts or {})
    en = ENERGY.get(o.get("energy") or "standard", ENERGY["standard"])
    profile = str(o.get("motionkit_profile") or "premium")
    gap = float(o.get("changeGap") or en["gap"])
    fps = int(o.get("fps") or 30)

    p = PS.empty(video_id, fps=fps, aspect=o.get("aspect") or "16:9")
    p["transcript"] = [dict(start=s.get("start"), end=s.get("end"),
                            text=s.get("text", "")) for s in segs]

    n = 0
    last_change = -99.0
    # ⚠️ **ဘောင်အပြည့် (cutaway) ကို တစ်ခါသာ ခွင့်ပြုခဲ့တာ မှားသည်** —
    #    reference ၂ ပုဒ်ကို ၂ fps နဲ့ တိုင်းရာ —
    #      ပုဒ်① ၁၃ ခု/၁၃ မိနစ် = ၁.၀၀/min · အလယ် ၇.၅s · **ပေါ်ချိန် ၁၅.၂%**
    #      ပုဒ်② ၁၄ ခု/၉.၂ မိနစ် = ၁.၅၁/min · အလယ် ၅.၂s · **ပေါ်ချိန် ၁၅.၁%**
    #    ⇒ နှုန်းနဲ့ ကြာချိန် ကွဲသော်လည်း **ပေါ်ချိန် ၁၅% က တည်ငြိမ်**သည်
    #      ⇒ အဲဒါကို ဘတ်ဂျက် အဖြစ် ထားသည် (နှုန်း မဟုတ်)。
    # ⚠️ ယခင် `_ff_used = True` က ဗီဒီယိုတစ်ပုဒ်လျှင် **၁ ခုသာ** ခွင့်ပြုခဲ့ ⇒
    #    ၆၀s ထွက်ဖိုင်မှာ ပေါ်ချိန် ၁၀% ပင် မပြည့်; ရှည်သော ဗီဒီယိုမှာ ပိုဆိုး。
    # ⚠️ **ကတ်တိုင်း ၃.၂s အမြင့်ဆုံး ဖြစ်နေတာ ဘောင်အပြည့်အတွက် မှားသည်** —
    #    reference ရဲ့ cutaway အလယ်ကြာချိန် **၅.၂–၇.၅s**。 ၃.၂s ဆိုလျှင်
    #    ဘတ်ဂျက် ပြည့်ပါလျက် ပေါ်ချိန် **၁၅% ဘယ်တော့မှ မရောက်**နိုင်ပါ
    #    (၆.၀s လိုသည့်နေရာ ၃.၂s ⇒ ၅၃% သာ)。 ဘေးကတ်က ၃.၂s အတိုင်း ထားသည်。
    # WARN **the full-frame cutaway shipped a 6 s dead screen and is now off.**
    #    2026-09-25, TH render `OP6Nl6TC7SJSYkRhPC6O3A.mp4` 2.80-9.13 s:
    #    a near-black full-frame card carrying ONE line of text, held 6.1 s,
    #    the speaker gone. Measured: mean luminance 19-24, and 97% of pixels
    #    under 45 -- `blackdetect` reports it as 6.33 s of black. Zin: "လုံးဝ
    #    အဆင်မပြေ".
    # WARN **my own error, not a tuning miss.** I set 0.15 coverage / 6.0 s
    #    from the reference measurement (cutaway median 5.2-7.5 s), but the
    #    reference's cutaways are FOOTAGE filling the frame. IKKI's are text
    #    cards that draw their own dark background (`thm._cut_bg`). Holding a
    #    line of text on black for 6 s is not the same edit at all.
    # WARN it cannot simply be shortened: `qc.black_frames` now fails any
    #    near-black stretch over 0.3 s, so ANY duration of this card fails --
    #    which is the correct verdict. A cutaway is only a cutaway when there
    #    is something to cut TO.
    #    ⇒ re-enable by setting `gfx_cutaway` on the recipe, once a cutaway
    #      card can be composited over B-roll footage instead of its own black
    #      panel. The rotation, budget and spacing code below all still work.
    # ⚠️ Zin ၂၀၂၆-၀၉-၂၅: 「ကိန်း မပြောင်းပါနှင့် — reference မှာ
    #    「အမှောင် + စာတစ်ကြောင်း」 ကတ် ရှိမရှိ တိုင်းပြီးမှ ငါ ဆုံးဖြတ်မယ်」
    #    ⇒ ကျွန်တော် ပိတ်လိုက်မိတာကို ပြန်ဖွင့်သည်。 `gfx_cutaway` က
    #    recipe ကနေ လွှမ်းလိုလျှင်သာ。
    _FF_COVER = float((opts or {}).get("gfx_cutaway") or 0.15)
    _FF_LEN, _FF_MAXLEN = 6.0, 6.5
    # ⚠️ **တကယ့်ကြာချိန်နဲ့ တွက်ရမည်** — `_FF_LEN` (၆.၀) နဲ့ `round()` သုံးလျှင်
    #    ၆၀s ဗီဒီယိုမှာ ၂ ခု ⇒ ၂×၆.၅ = ၁၃s = **၂၁.၇%** (ပန်းတိုင် ၁၅% ကျော်)。
    #    အောက်လျှော (`int`) + `_FF_MAXLEN` နဲ့ ၁ ခု ⇒ ၁၀.၈%。 ကျော်တာက
    #    လျော့တာထက် ပိုဆိုးသည် — ဖုံးလွန်လျှင် ပြောသူနဲ့ ဆက်သွယ်မှု ပြတ်သည်。
    # ⚠️ `max(1, …)` ကြမ်းခင်းက coverage ၀ ဖြစ်လျှင်လည် ၁ ခု အာမခံသည်
    #    ⇒ ပိတ်ထားပါလျက် ဘောင်အပြည့် တစ်ခု ထွက်နေမည်。
    _ff_max = (max(1, int(_FF_COVER * float(dur or 0) / _FF_MAXLEN))
               if _FF_COVER > 0 else 0)
    _ff_n = 0               # ⚠️ ယခုအထိ သုံးပြီးသော ဘောင်အပြည့် အရေအတွက်
    # ⚠️ **ဘတ်ဂျက်က အမြင့်ဆုံးသာ — ပန်းတိုင် မဟုတ်**。 ၂၀၂၆-၀၉-၂၄ တိုင်းချက်:
    #    ဘတ်ဂျက် ၂၀ ဖွင့်ပေးပြီးမှ ၇၈၀s ဗီဒီယိုမှာ ဘောင်အပြည့် **၁ ခုသာ**
    #    ထွက်ခဲ့သည် — `number` ရဲ့ candidate ၄၈ ခုမှာ ဘောင်အပြည့် ၃ ခုသာ
    #    ဖြစ်သဖြင့် `_rotate` ရဲ့ ရှေ့ဆုံးသို့ **ဘယ်တော့မှ မရောက်**ခဲ့。
    #    ⇒ ဘတ်ဂျက် လွတ်နေလျှင် ဘောင်အပြည့်ကို **ရှေ့တန်း တင်**ရသည်。
    # ⚠️ **အချိန် အညီအမျှ ခြားရမည်** — မစုပုံရ。 (slide rhythm တိုင်းချက်:
    #    ဖုံးအုပ်မှု ပြည့်ပါလျက် အစုလိုက် ပေါ်ပြီး ၄၀–၁၂၀s ပျောက်နေလျှင်
    #    slideshow ဟု ခံစားရသည် — ကြာချိန် မဟုတ်၊ **ကွာဟချက်** က အဓိက)。
    _ff_gap = (float(dur or 0) / (_ff_max + 1)) if dur else 1e9
    _ff_last = -1e9         # နောက်ဆုံး ဘောင်အပြည့် ကျသည့် အချိန်
    last_id = None
    # ⚠️ **cache ကို ကြိုဖြည့်ရမည်** — ၂၀၂၆-၀၉-၂၄ တိုင်းချက်: process တစ်ခုရဲ့
    #    **ပထမဆုံး `plan()`** က နောက်ပိုင်း ခေါ်ဆိုမှုတွေနဲ့ **မတူ**ခဲ့သည်
    #    (cache ကို အဲဒီ ခေါ်ဆိုမှု အတွင်း ဆောက်နေသဖြင့်)。 warm-up ပြီးလျှင်
    #    ၄ ခါ ဆက်တိုက် တူညီသည် — တိုင်းပြီး。
    #    ⚠️ worker က job များစွာကို **တစ် process ထဲ** ပြေးသဖြင့် restart ပြီး
    #       ပထမ job က re-render နဲ့ မတူဖြစ်မည် — ပြန်ထုတ်လျှင် တူရမည်ဆိုသော
    #       စည်းမျဉ်း ပျက်သည်。
    try:
        _pops()
        _auto_candidates("plain")
    except Exception:
        pass
    _used_tpl = []          # ⚠️ ရွေးပြီးသား template — ပြန်ပြန် မပေါ်စေရန်

    for i, s in enumerate(segs):
        a = float(s.get("start") or 0.0)
        b = float(s.get("end") or a + 1.0)
        # ⚠️ ASR က နောက်ဆုံးဝါကျကို media အဆုံးထက် **အနည်းငယ် ကျော်**ပြီး
        #    ပေးတတ်သည် (၁၆.၀၀s clip မှာ ၁၆.၄s)。 ပယ်ချလျှင် plan တစ်ခုလုံး
        #    မမှန်ဖြစ်ပြီး fallback သို့ ကျကာ **ဂရပ်ဖစ် ၀ ခု** ဖြစ်သွားသည်
        #    (၂၀၂၆-၀၉-၂၁ j_ec9716d51b31)。 ⇒ **ချ (clamp) ရမည်**、မပယ်ရ。
        if dur and dur > 0:
            a = max(0.0, min(a, dur - 0.05))
            b = min(b, dur)
        if b <= a:
            continue
        lab = labels[i] if i < len(labels) else "plain"
        txt = (s.get("text") or "").strip()
        if not txt:
            continue

        # ── စာတန်း — စကားတိုင်းမှာ ရှိရမည် ──
        n += 1
        col = PS.WHITE
        if lab in ("number", "fact"):
            col = PS.ACCENT
        elif lab == "warning":
            col = PS.ALERT
        cap_id = "capt.hl_phrase" if col != PS.WHITE else "capt.multi_line"
        cap_props = fill(cap_id, lab, txt)
        if cap_props is None:                    # ဖြည့်၍ မရလျှင် ရိုးရှင်းသို့
            cap_id, cap_props = "capt.multi_line", fill("capt.multi_line", lab, txt)
        if cap_props is None:
            continue
        p["captions"].append(dict(
            id=f"cap{n:03d}", startTime=a, endTime=b,
            layer="caption", type="caption",
            motionKitTemplateId=cap_id,
            props=cap_props,
            style=dict(color=col, bottomPct=0.08),
            reason=("အလေးထား စကားစု" if col != PS.WHITE else "ပုံမှန် စကား"),
            confidence=0.9))

        # ── ဂရပ်ဖစ် — အဓိပ္ပာယ် ရှိမှ · ကြားကာလ စောင့် ──
        fam = FAMILY.get(lab)
        # A product/UI reveal often follows the hook within 3–4 seconds in
        # premium talking-head edits. Treat it as a deliberate visual beat,
        # not generic cadence fill, while retaining a 2.5s anti-spam gap.
        _need_gap = min(gap, 2.5) if lab == "screen" else gap
        if not fam or (a - last_change) < _need_gap:
            continue
        # ⚠️ **pack ကို အရင် စစ်ရမည်** (spec §5 · audit P0) — verify
        #    ပြီးသား pack template ရှိလျှင် အဲဒါကို ယူပြီး
        #    မရှိမှ legacy manifest ကို ပြန်ဆုတ်သည်。
        #    ⚠️ legacy ကို **ဖ်ယ်မပစ်ရ** — pack မှာ template ၂ ခုပဲ
        #       ရှိသေး၍ label ၁ ခုထဲ ၂ ခုသာ အကျုံးဝင်သည်。
        cid = pr = None
        # ⚠️ **ဘောင်အပြည့် ကတ်က တစ်ခါသာ** — ပြောသူကို တမင် ဖုံးသဖြင့်
        #    ထပ်ခါထပ်ခါ သုံးလျှင် talking-head က slideshow ဖြစ်ပြီး
        #    ပြောသူနဲ့ ဆက်သွယ်မှု ပြတ်သည် (pack.json မှတ်ချက်)。
        #    ဖွင့်ချက် (`hook`) မှာသာ ခွင့်ပြုသည်。
        # Premium profile ကသာ Headtop pack ကို ဦးစားပေးသည်။ Clean/Bold/
        # Explainer တို့မှာ user ရွေးထားသော explicit MotionKit family ကိုသာ
        # သုံးစေ၍ profile select က render ထဲ အမှန်တကယ် သက်ရောက်စေသည်။
        # ⚠️ **pack က အမြဲ အရင် အောင်လျှင် တစ်ခုတည်း ပြန်ပြန် ပေါ်သည်**
        #    (၂၀၂၆-၀၉-၂၁ တိုင်းချက်) — `PACK_INTENT` ရဲ့ label အများစုမှာ
        #    pack template **၁ ခုပဲ** ရှိသည် (`number` → `ht_stat_ring`)。
        #    ဝါကျ ၄ ကြောင်း `number` ဆိုလျှင် ၄ ခုလုံး တူညီသည် —
        #    catalog မှာ ၃ ခု ရှိပါလျက် ဘယ်တော့မှ မရောက်ခဲ့。
        #    ⇒ အဆင့် ၃ ဆင့်: ① pack (ကြာသေးတာ ကျော်) ② catalog
        #      ③ pack (ကျော်ခဲ့တာ ပြန်ယူ — ဂရပ်ဖစ် မပျောက်စေရန်)
        _recent = set(_used_tpl[-NOREPEAT:])
        _pack_c = (_rotate(_pack_ids(lab), _used_tpl, video_id)
                   if profile == "premium" else [])
        # ⚠️ ဤအပိုင်းမှာ ဘောင်အပြည့် **သင့်မသင့်** — ဘတ်ဂျက် လွတ်ရမည်၊
        #    နောက်ဆုံး ဖြတ်ပြောင်းနဲ့ `_ff_gap` ခွာရမည်。 သင့်လျှင် ရှေ့တန်း
        #    တင်သည်; မသင့်လျှင် **လုံးဝ ချန်**သည် (ဘေးကတ်နဲ့ အစားထိုးသည်)。
        # ⚠️ `screen` မှာ **ဖြတ်ပြောင်း ရှေ့မတင်ရ** — အဲဒီအညွှန်းက UI/mockup
        #    template (browser · app window) ကို ရည်ရွယ်ပြီး `layout="full"`
        #    ကို သီးသန့် ရသည်。 တင်လိုက်လျှင် `prem2.word_pop` လို ယေဘုယျ
        #    ဖြတ်ပြောင်းက browser template ကို ကျော်တက်သည်
        #    (`tests/test_planner.py` က ဖမ်းမိ · ၂၀၂၆-၀၉-၂၅)。
        _want_ff = (_ff_n < _ff_max) and (a - _ff_last >= _ff_gap) \
            and lab != "screen"

        def _ff_order(ids):
            """ဘောင်အပြည့်တွေကို ရှေ့/နောက် စီ (သို့) ဖယ်သည်"""
            _f = [x for x in ids if _full_frame(x)]
            _o = [x for x in ids if not _full_frame(x)]
            return (_f + _o) if _want_ff else _o

        _pack_c = _ff_order(_pack_c)
        _stale = []
        for _pid in _pack_c:
            if _pid in _recent:
                _stale.append(_pid); continue      # ကြာသေး ⇒ catalog ကို အခွင့်ပေး
            _pp = _pack_props(_pid, lab, txt)
            if _pp is not None:
                cid, pr = _pid, _pp
                break
        if not cid:
            cands = _rotate(_profile_candidates(lab, profile, last_id),
                            _used_tpl, video_id)
            # ⚠️ catalog လမ်းကြောင်းမှာလည်း အတူတူ စီရမည် — ယခင်က pack
            #    လမ်းကြောင်းမှာသာ စစ်ခဲ့သဖြင့် ① ဘတ်ဂျက် မကန့်သတ်ရ
            #    ② ဘောင်အပြည့် ရှေ့တန်း မတက်ရ ဖြစ်ခဲ့သည်。
            for c in _ff_order(cands):
                pr = fill(c, lab, txt)
                if pr is not None:
                    cid = c
                    break
        if not cid:
            # ⚠️ **ဂရပ်ဖစ် မပျောက်စေရ** — ကွဲပြားမှုထက် ရှိတာက ကောင်းသည်
            for _pid in _ff_order(_stale):
                _pp = _pack_props(_pid, lab, txt)
                if _pp is not None:
                    cid, pr = _pid, _pp
                    break
        if not cid:
            continue
        n += 1
        # Browser / product grammar must have a larger stage. It is routed to
        # the full-frame alpha compositor even if the speaker has side room;
        # otherwise a wide browser mockup gets built and then rejected by the
        # side-safe-zone fitting check.
        _ff = _full_frame(cid)
        _layout = "full" if lab == "screen" or _ff else "side"
        # ⚠️ ရေတွက်ခြင်းကို **ဒီတစ်နေရာတည်း**မှာ လုပ်သည် — ရွေးသည့်နေရာ
        #    ၃ ခုစီမှာ တွက်လျှင် လမ်းကြောင်း တစ်ခု လွတ်သွားတတ်သည်။
        if _ff:
            _ff_n += 1
            _ff_last = a
        # ⚠️ **ဖြတ်ပြောင်းကို ဝါကျ တစ်ကြောင်းနဲ့ ချုပ်၍ မရ**。 ၂၀၂၆-၀၉-၂၄
        #    တကယ့် job (`j_228ad0f42421`) နဲ့ စစ်ရာ ဖြတ်ပြောင်း ၁ ခုက
        #    **၀.၈s** သာ ရခဲ့သည် — `min(b, …)` ရဲ့ `b` က ဝါကျ အဆုံး ဖြစ်ပြီး
        #    တကယ့် ဝါကျတွေက ၀.၈–၃s သာ ရှည်သည်。 ပိုဆိုးတာက worker ရဲ့
        #    `omap_window(min_d=1.0)` က ၁s အောက်ကို **ပယ်**သဖြင့် ဗီဒီယိုမှာ
        #    ဖြတ်ပြောင်း **လုံးဝ မပါ**ဖြစ်မည်。
        # ⚠️ reference မှာ ဖြတ်ပြောင်းက **ဝါကျ အများကြီး ကျော်ဖြတ်**သည်
        #    (ဝါကျ ~၂s · ဖြတ်ပြောင်း အလယ် ၅.၂–၇.၅s)。 ပြောသူကို ဖုံးထားသည်
        #    ဖြစ်၍ ဝါကျ အဆုံးမှာ ရပ်ရန် အကြောင်း မရှိပါ。 ဘေးကတ်က ဝါကျနဲ့
        #    ဆက်စပ်သဖြင့် ယခင်အတိုင်း `b` နဲ့ ချုပ်သည်。
        if _ff:
            _e1 = min(a + _FF_LEN, dur) if dur else a + _FF_LEN
        else:
            _e1 = min(b, a + 3.2, dur if dur else a + 3.2)
        p["templateEvents"].append(dict(
            id=f"tpl{n:03d}", startTime=a,
            endTime=_e1,
            layer="template", type="template", motionKitTemplateId=cid,
            # ⚠️ **semantic label ကို ပါသွားစေရမည်**。 အရင်က `style={}` ဖြစ်နေသဖြင့်
            #    `sfx_plan` က ဖြစ်ရပ် **အားလုံးကို `card`** ဟု သတ်မှတ်ခဲ့သည် —
            #    `SFX_ROLE` ထဲက warning/number/hook မြေပုံက ရှိပါလျက်
            #    **တစ်ခါမှ အလုပ်မလုပ်ခဲ့ပါ** (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。
            props=pr, style=dict(kind=SEM.get(lab, "card"), lab=lab,
                                  layout=_layout),
            reason=f"「{lab}」အမျိုးအစား — {txt[:28]}",
            confidence=0.72))
        last_change, last_id = a, cid
        _used_tpl.append(cid)

    # ── SFX setting ──────────────────────────────────────────────
    # Actual cue generation ကို keyword-pop / rhythm-fill ပြီးမှ အောက်ဆုံးမှာ
    # လုပ်သည်။ ဒီနေရာမှာလုပ်မိလျှင် နောက်မှ ထည့်သော visual events အတွက်
    # SFX မပါဘဲ ကျန်သွားသည်။
    if o.get("sfx_on") is False or o.get("sfx") is False:
        p["qualityWarnings"].append(dict(
            code="sfx_off", eventId=None,
            message="ဤပုံစံမှာ SFX ပိတ်ထားသည် — ဆက်တင်ကနေ ပြန်ဖွင့်နိုင်သည်"))

    # ══ စည်းချက် ဖြည့်ခြင်း — **editing psychology** ══════════════════
    # ⚠️ label classifier က ဝါကျ ၂၂ ကြောင်းကနေ ဂရပ်ဖစ် **၅ ခုသာ** ထုတ်သည်
    #    (၂၃%) — အများစုက `plain` ကျသဖြင့်。 ဒါက reference ရဲ့ သိပ်သည်းမှုကို
    #    မရောက်စေ。
    # ⚠️ တိုင်းချက် (reference ၆ ပုဒ် · ၂၀၂၆-၀၉-၂၁) — မြင်ကွင်း ပြောင်းလဲမှု
    #    ၉.၃–၁၄.၃/min ⇒ အကွာ **၄.၂–၆.၅s**。 IKKI က ၇.၅/min (၆၇%)。
    # ⚠️ **pattern interrupt** — ၈s ထက် ပိုကြာစွာ ဘာမှ မပြောင်းလျှင် ကြည့်သူ
    #    အာရုံ လွတ်သွားသည်。 ⇒ ကွက်လပ် ရှည်လျှင် အသုံးမချရသေးသော ဝါကျကနေ
    #    ဖြည့်သည်。 **အဓိပ္ပာယ် ရှိသော template ရှိမှ** ဖြည့်သည် — မရှိလျှင်
    #    မဖြည့်ပါ (အဓိပ္ပာယ်မဲ့ ဂရပ်ဖစ်ထက် ကွက်လပ်က ကောင်းသည်)。
    _fill_gap = float(o.get("gfx_gap_max") or 0)
    if _fill_gap > 0 and p["templateEvents"]:
        _ex = [x for x in p["templateEvents"]
               if (x.get("style") or {}).get("kind") != "pop"]
        _at = sorted(float(x.get("startTime") or 0) for x in _ex)
        _used_t = set(round(v, 1) for v in _at)
        _added = 0
        for i, s2 in enumerate(segs):
            a2 = float(s2.get("start") or 0.0)
            b2 = float(s2.get("end") or a2 + 1.0)
            if dur and a2 > dur - 2.0:
                continue
            if round(a2, 1) in _used_t:
                continue
            # ⚠️ အနီးဆုံး ဂရပ်ဖစ်နဲ့ ဘယ်လောက် ကွာလဲ
            _near = min((abs(a2 - t) for t in _at), default=1e9)
            if _near < _fill_gap:
                continue
            _txt2 = (s2.get("text") or "").strip()
            if len(_txt2) < 8:
                continue
            _lab2 = (labels[i] if i < len(labels) else "plain")
            _cid2 = _pr2 = None
            # ⚠️ **ဒီလမ်းကြောင်းကိုပါ လှည့်ရမည်** — ၂၀၂၆-၀၉-၂၁: အပေါ်က
            #    ၂ နေရာ လှည့်ပြီးမှ တိုင်းကြည့်တော့ `ht_stat_ring` က ၄ ခါ
            #    ပေါ်နေဆဲ ဖြစ်ခဲ့သည် — event အများစုက **ဒီ gap-fill** ကနေ
            #    လာသဖြင့်。 (တိုင်းပြီးမှ တွေ့ — code ဖတ်ရုံနဲ့ မရ)
            _pack_fill = (_rotate(_pack_ids(_lab2) or _pack_ids("section"),
                                  _used_tpl, video_id)
                          if profile == "premium" else [])
            # ⚠️ **ကြာသေးတာကို ကျော်ရမည်** — main loop မှာ `_recent` စစ်ချက်
            #    ရှိပြီး ဒီမှာ **မထည့်မိ**ခဲ့ပါ。 `_pack_ids("section")` မှာ
            #    id **တစ်ခုတည်း** (`headtop.ht_outline_title`) သာ ရှိသဖြင့်
            #    `plain` ဝါကျတိုင်းရဲ့ ဖြည့်ကတ်က **အတူတူ** ဖြစ်ခဲ့သည် —
            #    တစ်ပုဒ်တည်းမှာ ၆ ကြိမ် (Zin ၂၀၂၆-၀၉-၂၅: 「မထပ်အောင်」)。
            _recent2 = set(_used_tpl[-NOREPEAT:])
            for _pid2 in _pack_fill:
                if _full_frame(_pid2) or _pid2 in _recent2:
                    continue
                _pp2 = _pack_props(_pid2, _lab2, _txt2)
                if _pp2 is not None:
                    _cid2, _pr2 = _pid2, _pp2
                    break
            if not _cid2:
                # Non-pack profile တွေအတွက်လည်း cadence fill ရှိရမည်၊ ဒါပေမယ့်
                # profile ပြင်ပ template ဆီ တိတ်တဆိတ် ပြန်မကျစေရ။
                for _cid_try in _rotate(
                        _profile_candidates(_lab2, profile)
                        + _profile_candidates("section", profile),
                        _used_tpl, video_id):
                    # ⚠️ ဒီမှာလည်း ကြာသေးတာ ကျော်ရမည် — `_rotate` က ရှေ့တင်
                    #    ပေးရုံသာ、**ပယ်မပေးပါ**。 pool သေးလျှင် ထပ်နိုင်ဆဲ。
                    if _cid_try in _recent2:
                        continue
                    _pr_try = fill(_cid_try, _lab2, _txt2)
                    if _pr_try is not None:
                        _cid2, _pr2 = _cid_try, _pr_try
                        break
            if not _cid2:
                continue
            n += 1
            _layout2 = "full" if _lab2 == "screen" or _full_frame(_cid2) else "side"
            p["templateEvents"].append(dict(
                id=f"fil{n:03d}", startTime=round(a2, 2),
                endTime=round(min(b2, a2 + 3.2, dur if dur else a2 + 3.2), 2),
                layer="template", type="template", motionKitTemplateId=_cid2,
                props=_pr2, style=dict(kind=SEM.get(_lab2, "card"), lab=_lab2,
                                        layout=_layout2),
                reason=f"စည်းချက် ဖြည့် — {_near:.0f}s ကွက်လပ်",
                confidence=0.55))
            _at.append(round(a2, 2)); _at.sort(); _used_t.add(round(a2, 1))
            _used_tpl.append(_cid2)
            _added += 1
        if _added and o.get("log"):
            o["log"](f"  စည်းချက် ဖြည့် · ဂရပ်ဖစ် {_added} ခု ထပ်ထည့် "
                     f"(ကွက်လပ် > {_fill_gap:.0f}s)")
        p["templateEvents"].sort(key=lambda x: x.get("startTime") or 0)

    # ── punch-in — ၁၅s အတွင်း ၂ ခု · ၁.၀၈ ထက် မကျော် ──
    if en["punch"]:
        marks = [e["startTime"] for e in p["templateEvents"]]
        used = []
        for t in marks:
            if sum(1 for x in used if t - x < PS.PUNCH_WINDOW) >= PS.PUNCH_MAX_IN_WINDOW:
                continue
            if t + 2.0 > dur:
                continue
            n += 1
            p["cameraReframes"].append(dict(
                id=f"pun{n:03d}", startTime=t, endTime=min(dur, t + 2.4),
                layer="reframe", type="reframe",
                props=dict(zoom=1.06, anchorY=0.42),
                reason="အလေးထားချက်ကို ခံစားစေရန် အနည်းငယ် ချဲ့သည်",
                confidence=0.6))
            used.append(t)

    # ══ keyword pop — ပြောသူပေါ် တိုက်ရိုက် ══════════════════════
    # ⚠️ `docs/HEADTALK_STYLE.md` (v4 KCN4 · ၄Hz + full-res blob တိုင်းချက်) —
    #      စာလုံး အမြင့်  ၁၀.၁%H (၈.၁–၁၆.၃)
    #      ကြာချိန်      median ၃.၅s (p25 ၂.၈ · p75 ၅.၂)
    #      ကြားကာလ     median ၁၅.၀s (p25 ၅.၅)
    # ⚠️ IKKI က ယခင်က 「ကျန်နေရာ ၅.၆%H သာ」ဟု ယူဆကာ ထပ်တင် လုံးဝ မလုပ်ခဲ့ပါ。
    #    Reference က ပြောသူပေါ် တင်ပြီး **မျက်နှာကိုသာ ရှောင်**သည် ⇒ `place`。
    try:
        import place as _PC
    except ImportError:
        from core import place as _PC
    pose_fr = o.get("pose")
    band = _PC.caption_band(float(o.get("cap_base") or 0.92))
    # ⚠️ `minimal` မှာ **လုံးဝ မထည့်ရ** — ကြားကာလ ကြီးကြီး ထားရုံနဲ့
    #    မလုံလောက်ပါ (`last_pop` က −၉၉ ကနေ စသဖြင့် ပထမတစ်ခု ထွက်မည်)。
    #    「ဂရပ်ဖစ် နည်းနည်း」ဟု ရွေးထားသူကို မပေးရ。
    _lvl = o.get("energy") or "standard"
    # ⚠️ **တိုင်းထားသော ကိန်း** — v4 ရဲ့ ဂရပ်ဖစ် ကြားကာလ median ၁၅.၀s
    #    (p25 ၅.၅ · p75 ၃၆.၅)。 ကျွန်တော် ပထမ ၁၂s ဟု မှန်းခဲ့သည် —
    #    အဲဒါဆိုလျှင် တစ်မိနစ် ၅ ခုအထိ ဖြစ်ပြီး reference ရဲ့ ၁.၇၆ ထက်
    #    ၃ ဆ များမည်。 ⇒ median ကို သုံးသည်。 `dynamic` က p25 ဘက်。
    pop_gap = {"standard": 15.0, "dynamic": 8.0}.get(_lvl, 15.0)
    last_pop = -99.0
    # Browser / phone overlays are focus moments. A keyword pop over the
    # same moment makes a real UI look like a generic template, and can hide
    # controls the user is trying to see.
    _full_windows = [
        (float(x.get("startTime") or 0.0), float(x.get("endTime") or 0.0))
        for x in p["templateEvents"]
        if (x.get("style") or {}).get("layout") == "full"
    ]
    for i, s2 in enumerate(segs if _lvl != "minimal" else []):
        a = float(s2.get("start") or 0.0)
        b = float(s2.get("end") or a + 1.0)
        if dur and dur > 0:
            a = max(0.0, min(a, dur - 0.05)); b = min(b, dur)
        if b <= a or (a - last_pop) < pop_gap:
            continue
        kw = keyword(s2.get("text") or "")
        if not kw:
            continue
        # ⚠️ ကြာချိန် — တိုင်းထားသော p25–p75 ထဲ、ဝါကျထက် မကျော်ရ
        hold = max(2.8, min(5.2, b - a))
        end = min(dur if dur else a + hold, a + hold)
        if end - a < 1.2:
            continue
        if any(a < fb and end > fa for fa, fb in _full_windows):
            continue
        # အကျယ် — စာလုံးရေနဲ့ အချိုးကျ (တိုင်းချက်: ၁၁ လုံး ⇒ ၂၆.၇%W)
        tw = max(0.10, min(0.42, 0.024 * len(kw) + 0.02))
        spot = _PC.pick(pose_fr, a, end, tw, _PC.TEXT_H, avoid=[band])
        if spot is None:
            continue
        n += 1
        # ⚠️ **pop ကိုပါ လှည့်ရမည်** — `_used_tpl` မျှသုံးသဖြင့် ကတ်နဲ့ pop
        #    အချင်းချင်းလည်း ထပ်မနေပါ。
        _pop_c = _rotate(_pops(), _used_tpl, video_id)
        _pop_tid = _pop_c[0] if _pop_c else "kinetic.word_pop"
        _used_tpl.append(_pop_tid)
        p["templateEvents"].append(dict(
            id=f"pop{n:03d}", startTime=round(a, 2), endTime=round(end, 2),
            layer="template", type="template",
            motionKitTemplateId=_pop_tid,
            props=dict(text=kw, size=int(round(_PC.TEXT_H * 1080)),
                       dur=round(end - a, 2), fill=PS.ACCENT),
            # ⚠️ `style` က **renderer အတွက်** — template မှာ x မရှိသဖြင့်
            #    compositor က ဒီကိန်းတွေနဲ့ ရွှေ့ပေးရမည်。
            style=dict(kind="pop", cx=spot[0], cy=spot[1], w=round(tw, 3),
                       h=_PC.TEXT_H),
            reason=f"အဓိက စကားလုံး「{kw}」— ပြောသူပေါ် အနက်အနားသတ်နဲ့",
            confidence=0.66))
        last_pop = a

    # SFX ကို **နောက်ဆုံး** template event စာရင်းကနေ ဆောက်ရမည်။ အရင် code က
    # initial cards ပေါ်သာ cue တင်ပြီး gap-fill / keyword pop တွေ အသံမပါခဲ့လို့
    # output က motion graphic ဖြစ်ပါလျက် silent slideshow လိုခံစားရသည်။
    if o.get("sfx_on") is not False and o.get("sfx") is not False:
        p["sfxEvents"] = sfx_plan(p["templateEvents"], dur,
                                  float(o.get("sfx_per_min") or 1.5),
                                  log=o.get("log"), style=o.get("style"),
                                  out_dur=o.get("out_dur"))
    p["motionKitProfile"] = profile
    return p


def plan(segs, dur, opts=None, video_id="src", log=print):
    """အဓိက လမ်းကြောင်း — `(plan, warnings)`

    schema မအောင်လျှင် **fallback** ကို သုံးသည် — အလုပ် မရပ်ပါ。
    """
    labels = annotate(segs, log=log)
    opts = dict(opts or {}); opts.setdefault("log", log)
    p = build(segs, labels, dur, opts, video_id)
    ok, errs, warns = PS.validate(p, MF, duration=dur)
    if not ok:
        # ⚠️ ကိုယ့်ကုဒ်ကိုယ် မယုံရ — build() က ပျက်လျှင်လည်း
        #    fallback နဲ့ ဗီဒီယို ထွက်ရမည် (Zin: safe fallback edit)。
        log(f"  ⚠️ planner · plan မမှန် ({len(errs)} ချက်) — fallback သို့")
        for x in errs[:3]:
            log(f"      {x}")
        p = fallback(segs, dur, opts, video_id)
        ok, errs, warns = PS.validate(p, MF, duration=dur)
        if not ok:
            raise RuntimeError(f"fallback ပင် မမှန်: {errs[:2]}")
    # ⚠️ **လွှမ်း၍ မရ** — `build()` က ထည့်ထားသော သတိပေးချက် (ဥပမာ
    #    `sfx_off`) ပျောက်သွားမည် ⇒ ပေါင်းရမည် (၂၀၂၆-၀၉-၂၁ ဖမ်းမိ)。
    p["qualityWarnings"] = list(p.get("qualityWarnings") or []) + list(warns or [])
    log(f"  planner · စာတန်း {len(p['captions'])} · ဂရပ်ဖစ် "
        f"{len(p['templateEvents'])} · punch {len(p['cameraReframes'])} · "
        f"သတိပေး {len(warns)}")
    return p, warns


def fallback(segs, dur, opts=None, video_id="src"):
    """AI မပါဘဲ — စာတန်းသာ · ဂရပ်ဖစ် မပါ · ဘယ်တော့မှ မမှန်မဖြစ်

    ⚠️ ဒါက **ဘေးကင်းသော အနိမ့်ဆုံး** ဖြစ်သည် — ဖတ်လို့ရသော စာတန်းနဲ့
       သန့်ရှင်းသော ဖြတ်ချက်。 ဂရပ်ဖစ် မထည့်သဖြင့် မမှန်သော template
       ထွက်ဖို့ လမ်း မရှိပါ。
    """
    o = dict(opts or {})
    p = PS.empty(video_id, fps=int(o.get("fps") or 30),
                 aspect=o.get("aspect") or "16:9")
    p["transcript"] = [dict(start=s.get("start"), end=s.get("end"),
                            text=s.get("text", "")) for s in segs]
    for i, s in enumerate(segs):
        txt = (s.get("text") or "").strip()
        if not txt:
            continue
        a = float(s.get("start") or 0.0)
        b = float(s.get("end") or a + 1.0)
        pr = fill("capt.multi_line", "plain", txt)
        if pr is None:
            continue
        p["captions"].append(dict(
            id=f"cap{i+1:03d}", startTime=max(0.0, min(a, dur - 0.05)),
            endTime=min(b, dur),
            layer="caption", type="caption",
            motionKitTemplateId="capt.multi_line",
            props=pr, style=dict(color=PS.WHITE, bottomPct=0.08),
            reason="fallback — စာတန်းသာ", confidence=0.5))
    return p
