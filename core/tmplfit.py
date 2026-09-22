# -*- coding: utf-8 -*-
"""motionkit template ၄၄၇ ခုကို **အကြောင်းအရာနဲ့** ဖြည့်ခြင်း。

⚠️ **ဘာအတွက် ရှိလဲ** — plan လမ်းကြောင်း (Talking Head) က `pack.selectable()`
   ကနေသာ ရွေးသဖြင့် `headtop-premium` pack ရဲ့ **၅ ခုပဲ** မြင်ခဲ့သည်
   (catalog မှာ ၄၇၉ ရှိ · ၄၄၇ က ဖြည့်လို့ရ — ၂၀၂၆-၀၉-၂၁ တိုင်းချက်)。
   ⇒ ဗီဒီယိုတိုင်း အဲဒီ ၅ ခုပဲ ပြန်ပြန် ပေါ်ပြီး 「တစ်ပုံစံတည်း」ဖြစ်သည်。

⚠️ **`gfxcat.fill()` က brand/label ကနေ ဖြည့်သည်** — ဗီဒီယိုရဲ့ အကြောင်းအရာ
   မဟုတ်ပါ。 အဲဒါနဲ့ ဖြည့်လျှင် မျက်နှာပြင်ပေါ် 「Headtop」ဟု တင်မိသည်
   (၂၀၂၆-၀၉-၂၁ တကယ် ဖြစ်ခဲ့ — ဗလာကွက် ထက် ဆိုးသည်)。
   ⇒ ဤ module က **transcript ကလာသော အကြောင်းအရာ**ကိုသာ ထည့်သည်。

⚠️ **ဖြည့်လို့ မရလျှင် ငြင်းရမည် — မှန်းဆ မဖြည့်ရ** (Zin ရဲ့ စည်းမျဉ်း:
   「ဂဏန်း မတီထွင်ရ」·「အဓိပ္ပာယ်မဲ့ ဂရပ်ဖစ်ထက် မရှိတာက ကောင်း」) —
     ဂဏန်း လိုပေမယ့် transcript မှာ မရှိ      ⇒ ငြင်း
     စာရင်း လိုပေမယ့် item ၂ ခု မပြည့်        ⇒ ငြင်း
     ရုပ်ပုံ (`file`) လိုသည်                   ⇒ ငြင်း (ပုံ မရှိ)
     စာသား နေရာ များပေမယ့် အကြောင်းအရာ မလောက် ⇒ ငြင်း
"""
# ── slot အမည် ↔ အကြောင်းအရာ အမျိုးအစား ────────────────────────────
# ⚠️ catalog ရဲ့ param နာမည်များကို တိုင်းပြီး စီထားသည် (required · default
#    မရှိ · auto မဟုတ် — text ၄၅၇ · list ၈၈ · number ၁၇ · color ၆ · file ၈)。
HEAD = ("text", "title", "head", "headline", "q", "msg", "line", "l1",
        "word", "w1", "name", "label", "left", "before", "top")
SUB = ("sub", "subtitle", "kicker", "note", "desc", "caption", "l2", "w2",
       "right", "after", "bottom", "value", "num", "detail")
LIST = ("items", "lines", "rows", "bullets", "points", "steps", "words")
# ⚠️ `target`·`to`·`goal`·`end_val` — `odo.count_up` လို counter template
#    တွေရဲ့ ပစ်မှတ် ဂဏန်း。 catalog မှာ `type="text"` ဟု မှတ်ထားသော်လည်း
#    template က **float နဲ့ မြှောက်**သည် (၂၀၂၆-၀၉-၂၂ တကယ့် render:
#    「TypeError: can't multiply sequence by non-int of type 'float'」) ⇒
#    ဂဏန်း ဖြစ်ကြောင်း သက်သေ ရှိသည် · မှန်းဆချက် မဟုတ်。
NUM = ("pct", "val", "value_n", "count", "n", "score", "amount", "percent",
       "target", "to", "goal", "end_val", "total_n", "num")

# ── အရောင် slot — **အဓိပ္ပာယ်အလိုက် ခွဲရမည်** ──────────────────────
# ⚠️ ၂၀၂၆-၀၉-၂၁ စမ်းစဉ် ဖမ်းမိ — အရောင် slot အားလုံးကို accent တစ်ခုတည်း
#    ပေးလိုက်လျှင် —
#      `kinetic.spotlight`     fill == dim  ⇒ အလေးထားချက် **ပျောက်**
#      `kinetic2.highlight_bar` fill == col  ⇒ bar ပေါ် စာလုံး **မမြင်ရ**
#    ⇒ စာလုံးအရောင် · အလေးထားအရောင် · မှိန်အရောင် သုံးမျိုး ခွဲပေးသည်。
C_INK = ("fill", "text_col", "tc", "txt", "fg")          # စာလုံး
C_HOT = ("col", "hot", "accent", "bar", "line", "c1", "hl")  # အလေးထား
C_DIM = ("dim", "mute", "muted", "bg", "c2", "back", "sub_col")  # မှိန်

# ⚠️ **အစီအစဉ်လိုက် slot** — `l1 l2 l3` · `w1 w2 w3` စသည်။ item စာရင်းကနေ
#    တစ်ခုချင်း ခွဲထည့်သည် — မလောက်လျှင် ငြင်းသည်。
import re as _re
_SEQ = _re.compile(r"^(l|w|t|s|item|line|word|row)(\d+)$")

MIN_ITEMS = 2


def _p(p):
    """param dict → `(name, type, required, has_default)`"""
    if not isinstance(p, dict):
        return (str(p), "text", True, False)
    return (p.get("name") or "", (p.get("type") or "text").lower(),
            bool(p.get("required")), p.get("default") is not None
            or bool(p.get("auto")))


def _num_of(txt):
    """စာသားထဲက **ပထမ ဂဏန်း** — မရှိလျှင် None (တီထွင် မလုပ်ရ)"""
    if not txt:
        return None
    m = _re.search(r"\d+(?:[.,]\d+)?", str(txt))
    return m.group(0) if m else None


def fit(entry, c, accent=None, dur=None, ink=None, dim=None):
    """catalog entry + အကြောင်းအရာ → kwargs dict · ဖြည့်မရလျှင် `None`

    `c` — `dict(head=str, sub=str, items=[str], num=str|None)`
          `head` က transcript ကလာသော **အဓိက စာသား**。
    `accent` · `ink` · `dim` — theme ရဲ့ အရောင် ၃ မျိုး (styling သာ)。
              အလေးထား · စာလုံး · မှိန် — **တစ်ခုတည်း မပေးရ** (effect ပျောက်မည်)
    """
    head = (c.get("head") or "").strip()
    sub = (c.get("sub") or "").strip()
    items = [str(x).strip() for x in (c.get("items") or []) if str(x).strip()]
    num = c.get("num") or _num_of(head) or _num_of(sub)

    out, used_seq = {}, 0
    used = {"head": False, "sub": False}
    ctaken = set()
    got = False              # အကြောင်းအရာ (စာသား/စာရင်း/ဂဏန်း) ထည့်ဖြစ်လား
    for p in (entry.get("params") or []):
        name, typ, req, has_d = _p(p)
        if not name:
            continue
        if name == "dur":
            if dur:
                out["dur"] = float(dur)
            continue
        low = name.lower()

        # ── ရုပ်ပုံ — မရှိ ⇒ ငြင်း (required ဆိုလျှင်) ──
        if typ == "file":
            if req and not has_d:
                return None
            continue

        # ── အရောင် — styling ⇒ theme ကနေ · **အဓိပ္ပာယ်အလိုက်** ──
        if typ == "color":
            _ink, _dim = (ink or "#FFFFFF"), (dim or "#8B8B8B")
            v = None
            if low in C_INK: v = _ink
            elif low in C_HOT: v = accent
            elif low in C_DIM: v = _dim
            # ⚠️ **template တစ်ခုအတွင်း အရောင် ၂ ခု တူမဖြစ်ရ** —
            #    `hot` ရော `col` ရော accent ရလျှင် အလေးထားချက် ပျောက်သည်
            #    (`hl_phrase` · `accent_word` · `word_fill` … ၇ ခု — တိုင်း၍ တွေ့)。
            #    ⇒ ယူပြီးသား အရောင် ဖြစ်လျှင် ကျန်တစ်ခုကို ယူသည်。
            if v and v in ctaken:
                v = next((x for x in (accent, _ink, _dim)
                          if x and x not in ctaken), None)
            if v:
                out[name] = v; ctaken.add(v)
            elif req and not has_d:
                # ⚠️ ဘယ်အရောင် လဲ မသိ ⇒ **မှန်းဆ မပေးရ**
                return None
            continue

        # ── ဂဏန်း — **transcript မှာ ရှိမှ** ──
        if typ in ("number", "int", "float") or low in NUM:
            if low in NUM or (req and not has_d):
                if num is None:
                    if req and not has_d:
                        return None
                    continue
                out[name] = int(float(num.replace(",", ""))) if typ == "int" \
                    else float(num.replace(",", ""))
                got = True
            continue

        # ── စာရင်း — item ၂ ခု အနည်းဆုံး ──
        if typ == "list" or low in LIST:
            if len(items) < MIN_ITEMS:
                if req and not has_d:
                    return None
                continue
            out[name] = items[:5]; got = True
            continue

        # ── အစီအစဉ်လိုက် စာသား slot (l1 l2 · w1 w2 …) ──
        m = _SEQ.match(low)
        if m and typ == "text":
            if used_seq < len(items):
                out[name] = items[used_seq]; used_seq += 1; got = True
            elif used_seq == 0 and head:
                out[name] = head; used_seq += 1; got = True
            elif req and not has_d:
                return None            # နေရာ ရှိပေမယ့် အကြောင်းအရာ မလောက်
            continue

        # ── ပုံမှန် စာသား ──
        # ⚠️ **စာသား တစ်ခုကို နေရာ ၂ ခုမှာ မထည့်ရ** — `insert_label` က
        #    `label` ရော `title` ရော HEAD စာရင်းထဲ ရှိသဖြင့် နှစ်ခုလုံး
        #    တူညီသော စာသား ရပြီး မျက်နှာပြင်ပေါ် **ထပ်နေ**ခဲ့သည်
        #    (၂၀၂၆-၀၉-၂၁ စမ်းစဉ် ဖမ်းမိ)。 ⇒ တစ်ခါသာ ခွဲပေးသည်。
        if typ == "text":
            if low in HEAD and head and not used["head"]:
                out[name] = head; used["head"] = True; got = True
            elif low in SUB and sub and not used["sub"]:
                out[name] = sub; used["sub"] = True; got = True
            elif (low in HEAD or low in SUB):
                # ဒုတိယ/တတိယ စာသား နေရာ — ကျန်နေသော အကြောင်းအရာကနေ
                _left = ([sub] if (sub and not used["sub"]) else []) + \
                        [x for x in items if x not in out.values()]
                if _left:
                    out[name] = _left[0]; got = True
                    if _left[0] == sub: used["sub"] = True
                elif req and not has_d:
                    return None        # နေရာ ရှိပေမယ့် အကြောင်းအရာ မလောက်
            elif req and not has_d:
                return None            # ဘယ် slot လဲ မသိ ⇒ မှန်းဆ မဖြည့်ရ
            continue

        # ── အခြား type — required ဆိုလျှင် ငြင်း ──
        if req and not has_d:
            return None
    # ⚠️ **အကြောင်းအရာ တစ်ခုမှ မထည့်ရလျှင် အလကား** — ဗလာကွက် ဖြစ်မည်。
    #    ⚠️ 「စာသား ရှိလား」ဟု စစ်ရုံနဲ့ **မလုံလောက်** — အရောင်က string
    #       ဖြစ်သဖြင့် `{"col": "#F5D000"}` က guard ကို ကျော်ပြီး
    #       စာသား မပါသော ဗလာကွက် ထွက်ခဲ့သည် (၂၀၂၆-၀၉-၂၁ test က ဖမ်းမိ)。
    #    ⇒ **အကြောင်းအရာ တကယ် ထည့်ဖြစ်လား** ကို သီးသန့် မှတ်ရသည်。
    if not got:
        return None
    return out


def fits(entry, c, accent=None, ink=None, dim=None):
    """`fit()` ရလား — bool"""
    return fit(entry, c, accent=accent, ink=ink, dim=dim) is not None
