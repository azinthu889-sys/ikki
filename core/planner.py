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
          "compare", "location", "warning", "plain")

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
    "warning":   "callout",
}

# အညွှန်း → template ID ဦးစားပေး (မိသားစုထဲမှ)
PREFER = {
    "steps":     ["infogfx.steps", "infogfx.checklist"],
    "checklist": ["infogfx.checklist"],
    "compare":   ["infogfx.big_number", "infogfx.checklist"],
    "number":    ["odo.big_stat", "odo.count_up", "odo.percent_ring"],
    "location":  ["prem7.location_tag", "prem7.note_card"],
    "warning":   ["callouts.box_call", "callouts.underline_call"],
    "fact":      ["callouts.line_call", "callouts.underline_call"],
    "section":   ["titles3.minimal_third", "titles.topic_bar", "titles.chapter"],
    "hook":      ["prem4.big_question", "prem4.stop_scroll", "titles3.opening_bars"],
}

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
        "rows":   two or [_short(text, 24)],
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
PACK_INTENT = {"hook": "hook", "section": "section", "fact": "statement"}


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


def _full_frame(tid):
    """ဘောင်အပြည့် ဖုံးသော pack template လား"""
    try:
        try:
            import pack as _PK
        except ImportError:
            from core import pack as _PK
        return bool((_PK.template(tid) or {}).get("fullFrame"))
    except Exception:
        return False


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
        for k, spec in (t.get("props") or {}).items():
            if spec.get("type") != "text":
                continue
            mx = int(spec.get("maxChars") or 40)
            if not spec.get("required"):
                continue
            v = _short(txt, mx)
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
    for m in _NUM.finditer(t):
        v = m.group(0).strip()
        if len(v.strip("%")) >= 2:          # တစ်လုံးတည်း ဂဏန်း မယူ
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
    "hook":    ("riser_soft", "latch"),    # ဖွင့်ချက်
}
# ⚠️ `FAMILY` ရဲ label → SFX အမျိုးအစား。 မြေပုံ မရှိလျှင် အားလုံး `card`
#    ဖြစ်ပြီး အသံ တစ်မျိုးတည်း ထွက်မည် — အော်အိုက် မရှိတော့。
# ⚠️ အောင့်မြဲမှု အဆင့် — နေရာ တစ်ခုထဲ ဖြစ်ရပ် ၂ ခု ပြိုလျှင် ဘယ်ဟာ ယူမလဲ
SFX_RANK = {"hook": 5, "warning": 4, "number": 3, "card": 2, "pop": 1}
SEM = {"hook": "hook", "number": "number", "warning": "warning",
       "fact": "warning", "section": "card", "steps": "card",
       "checklist": "card", "compare": "card", "location": "card"}
SFX_LEAD = 0.18        # ရှေ့သံက ရုပ်ထက် ဘယ်လောက် စောလဲ
SFX_DB = {"whoosh_in": -15, "riser_soft": -17, "swipe": -16,
          "latch": -17, "pop": -18, "click": -18, "impact": -14}


def sfx_plan(events, dur, per_min, log=None, style=None):
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
    cap = _PL.budget(_pol, dur)

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
        for role, off in ((lead, -SFX_LEAD), (main, 0.0)):
            if not role:
                continue
            t = max(0.0, min(dur - 0.05, at + off))
            # ⚠️ ရှေ့သံက ဘောင်အစမှာ ကပ်သွားလျှင် **ထပ်နေမည်** —
            #    ၂ ခုလုံး ၀.၀၀s ဖြစ်ပြီး အထပ် အဓိပ္ပာယ် ပျက်သည်
            #    (၂၀၂၆-၀၉-၂၁ ဖမ်းမိ)。 ⇒ ကပ်လျှင် ရှေ့သံ ချန်သည်。
            if off < 0 and abs(t - at) < SFX_LEAD * 0.5:
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
        log(f"  SFX plan · အသံအခိုက် {len(keep)} · ဖြစ်ရပ် {len(out)} "
            f"· ဘောင် {per_min}/မိနစ် · ကွာ ≥{gap:.1f}s")
    return out


def build(segs, labels, dur, opts=None, video_id="src"):
    """အညွှန်း → plan (ကုဒ်က တည်ဆောက်သည်、AI မဟုတ်)"""
    o = dict(opts or {})
    en = ENERGY.get(o.get("energy") or "standard", ENERGY["standard"])
    gap = float(o.get("changeGap") or en["gap"])
    fps = int(o.get("fps") or 30)

    p = PS.empty(video_id, fps=fps, aspect=o.get("aspect") or "16:9")
    p["transcript"] = [dict(start=s.get("start"), end=s.get("end"),
                            text=s.get("text", "")) for s in segs]

    n = 0
    last_change = -99.0
    _ff_used = False        # ⚠️ ဘောင်အပြည့် ကတ် — ဗီဒီယိုတစ်ပုဒ်လျှင် တစ်ခါသာ
    last_id = None

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
        if not fam or (a - last_change) < gap:
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
        for _pid in _pack_ids(lab):
            if _full_frame(_pid) and (lab != "hook" or _ff_used):
                continue
            _pp = _pack_props(_pid, lab, txt)
            if _pp is not None:
                cid, pr = _pid, _pp
                if _full_frame(_pid):
                    _ff_used = True
                break
        if not cid:
            cands = [c for c in (PREFER.get(lab) or MF.HEADTOP.get(fam) or [])
                     if c != last_id]
            for c in cands:
                pr = fill(c, lab, txt)
                if pr is not None:
                    cid = c
                    break
        if not cid:
            continue
        n += 1
        p["templateEvents"].append(dict(
            id=f"tpl{n:03d}", startTime=a,
            endTime=min(b, a + 3.2, dur if dur else a + 3.2),
            layer="template", type="template", motionKitTemplateId=cid,
            # ⚠️ **semantic label ကို ပါသွားစေရမည်**。 အရင်က `style={}` ဖြစ်နေသဖြင့်
            #    `sfx_plan` က ဖြစ်ရပ် **အားလုံးကို `card`** ဟု သတ်မှတ်ခဲ့သည် —
            #    `SFX_ROLE` ထဲက warning/number/hook မြေပုံက ရှိပါလျက်
            #    **တစ်ခါမှ အလုပ်မလုပ်ခဲ့ပါ** (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。
            props=pr, style=dict(kind=SEM.get(lab, "card"), lab=lab),
            reason=f"「{lab}」အမျိုးအစား — {txt[:28]}",
            confidence=0.72))
        last_change, last_id = a, cid

    # ── SFX — **ဂရပ်ဖစ် ဖြစ်ရပ်ပေါ်မှာသာ** ──
    # ⚠️ schema မှာ `sfxEvents` ရှိပါလျက် planner က **တစ်ခါမှ မထုတ်ခဲ့ပါ**
    #    ⇒ `execute.to_sfx()` က အမြဲ ဗလာ ပြန်ခဲ့သည် (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。
    # ⚠️ ပိတ်ထားလျှင် **အကြောင်းရင်း ချန်ရမည်** — 「Do not hide disabled
    #    SFX settings」。 `qualityWarnings` ထဲ ထည့်သည်。
    if o.get("sfx_on") is False or o.get("sfx") is False:
        p["qualityWarnings"].append(dict(
            code="sfx_off", eventId=None,
            message="ဤပုံစံမှာ SFX ပိတ်ထားသည် — ဆက်တင်ကနေ ပြန်ဖွင့်နိုင်သည်"))
    else:
        p["sfxEvents"] = sfx_plan(p["templateEvents"], dur,
                                  float(o.get("sfx_per_min") or 1.5),
                                  log=o.get("log"), style=o.get("style"))

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
        # အကျယ် — စာလုံးရေနဲ့ အချိုးကျ (တိုင်းချက်: ၁၁ လုံး ⇒ ၂၆.၇%W)
        tw = max(0.10, min(0.42, 0.024 * len(kw) + 0.02))
        spot = _PC.pick(pose_fr, a, end, tw, _PC.TEXT_H, avoid=[band])
        if spot is None:
            continue
        n += 1
        p["templateEvents"].append(dict(
            id=f"pop{n:03d}", startTime=round(a, 2), endTime=round(end, 2),
            layer="template", type="template",
            motionKitTemplateId="kinetic.word_pop",
            props=dict(text=kw, size=int(round(_PC.TEXT_H * 1080)),
                       dur=round(end - a, 2), fill=PS.ACCENT),
            # ⚠️ `style` က **renderer အတွက်** — template မှာ x မရှိသဖြင့်
            #    compositor က ဒီကိန်းတွေနဲ့ ရွှေ့ပေးရမည်。
            style=dict(kind="pop", cx=spot[0], cy=spot[1], w=round(tw, 3),
                       h=_PC.TEXT_H),
            reason=f"အဓိက စကားလုံး「{kw}」— ပြောသူပေါ် အနက်အနားသတ်နဲ့",
            confidence=0.66))
        last_pop = a

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
