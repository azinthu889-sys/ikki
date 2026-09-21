"""ဘေးဘောင် စာရင်း (progress rail) — v5 `HJ0K1yAuGLw` ကနေ တိုင်းယူထားသည်。

⚠️ ကိန်းတိုင်းကို full-res ဖရိန် (၄၀s) ကနေ တိုင်းထားသည် — မှန်းဆ မဟုတ်ပါ
   (၂၀၂၆-၀၉-၂၁ · `docs/HEADTALK_STYLE.md` §၅)。

⚠️ **သဘောသဘာဝ ကွဲသည်** — IKKI ရဲ့ ကျန်ဂရပ်ဖစ်တွေက 「ပြ → ဖယ်」ဖြစ်ပြီး
   ဒါက **မိနစ်ချီ ဆက်ရှိ**နေပြီး item တစ်ခုချင်း အခြေအနေ ပြောင်းသွားသည်。
   ⇒ `gfx_share` (ဘောင်အပြည့် slide) နဲ့ **မရောရ** — ဒါက အမြဲပေါ် အလွှာ。
"""
import os

try:
    import slide as SL
except ImportError:
    from core import slide as SL

# ── တိုင်းထားသော ဘောင် (အချိုး · ဘောင် ၁၉၂၀×၁၀၈၀) ──────────────
HEAD_X = 0.045          # ခေါင်းစဉ် ဘယ်အနား
HEAD_Y = 0.101          # ခေါင်းစဉ် အပေါ်စွန်း
HEAD_H = 0.090          # ခေါင်းစဉ် စာလုံး အမြင့် (၉၇px)
PILL_X = 0.109          # pill ဘယ်အနား
PILL_W = 0.304          # pill အကျယ်
PILL_H = 0.104          # pill အမြင့် (၁၁၃px)
PITCH = 0.1315          # pill အကြား အလယ်မှတ်ချင်း (၁၄၂px)
PILL_Y0 = 0.276         # ပထမ pill အပေါ်စွန်း
TEXT_H = 0.0565         # pill ထဲက စာလုံး အမြင့် (၆၁px)
DOT_D = 0.0354          # အမှတ်အသား စက် အချင်း (၆၈px · W အချိုး)
DOT_CX = 0.072          # စက် အလယ် x

# ⚠️ တိုင်းထားသော အရောင် — brand က လွှမ်းနိုင်သည်
FILL = (18, 15, 0)          # #120F00 — pill အတွင်း
BORD = (125, 110, 33)       # #7D6E21 — pill အနားသတ် (၃px)
TXT = (255, 255, 255)
DOT = (250, 249, 241)       # #FAF9F1
HEAD = (255, 255, 255)
BORD_W = 0.0028             # ၃px / ၁၀၈၀


def fits(n):
    """pill `n` ခု ဘောင်ထဲ ဝင်မဝင် — တိုင်းချက်မှာ ၅ ခု (အောက်စွန်း ၉၀.၆%)"""
    return n >= 1 and PILL_Y0 + (n - 1) * PITCH + PILL_H <= 0.96


def panel(head, items, active=None, done=(), W=1920, H=1080,
          accent=None, mmf="Pyidaungsu-Bold", lat="Figtree-Black"):
    """RGBA ပုံ တစ်ချပ် — ခေါင်းစဉ် + pill စာရင်း + အမှတ်အသား စက်

    `items`  — ပြရမည့် စာသား စာရင်း (နံပါတ် သို့မဟုတ် ခေါင်းစဉ်)
    `active` — ယခု ပြောနေသော အညွှန်း (၀ က စ) · `None` ဆိုလျှင် စက် မပြ
    `done`   — ပြီးသွားပြီးသား အညွှန်းများ (အလင်း လျှော့ပြသည်)

    ⚠️ pill ထဲ စာသား **မဆံ့လျှင် ချုံ့ရမည်** — ဖြတ်ပစ်လျှင် မြန်မာစာ
       ပျက်သည် (`slide._fit` ရဲ့ မှတ်ချက် ကြည့်)。
    """
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    bord = _rgb(accent) if accent else BORD

    # ── ခေါင်းစဉ် ──
    if head:
        px = int(HEAD_H * H)
        maxw = int((PILL_X + PILL_W - HEAD_X) * W)
        while px > 16 and SL.measure(head, px, mmf) > maxw:
            px = int(px * 0.94)
        SL._paste(im, SL._text_png(head, px, mmf, HEAD), int(HEAD_X * W),
                  int(HEAD_Y * H))

    # ── pill များ ──
    x0 = int(PILL_X * W)
    x1 = int((PILL_X + PILL_W) * W)
    ph = int(PILL_H * H)
    rad = ph // 2                      # အစွန်းနှစ်ဖက် ဝိုင်း (capsule)
    bw = max(2, int(BORD_W * H))
    for i, it in enumerate(items):
        y0 = int((PILL_Y0 + i * PITCH) * H)
        y1 = y0 + ph
        if y1 > H:
            break
        # ⚠️ ပြီးသွားပြီးသား item — **လုံးဝ မဖျောက်ရ** (ဆက်ပြရမည်) ·
        #    ဒါပေမယ့် ယခု item က ထင်ရှားရမည် ⇒ ၀.၅၅ ဆ
        dim = 0.55 if (i in done and i != active) else 1.0
        d.rounded_rectangle([x0, y0, x1, y1], radius=rad,
                            fill=FILL + (int(232 * dim),),
                            outline=tuple(int(c * dim) for c in bord) + (255,),
                            width=bw)
        s = str(it or "").strip()
        if s:
            inner = int((x1 - x0) * 0.86)
            # ⚠️ `_fit()` က **`(px, lines)` တွဲ** ပြန်ပေးသည် — lines သက်သက် မဟုတ်。
            #    တွဲကို စာရင်းအဖြစ် ယူမိလျှင် cttext က DecodingError နဲ့ ကျသည်。
            # ⚠️ **space မရှိလျှင် ၁ ကြောင်းသာ** — `_wrap()` က space မရှိရင်
            #    cluster နဲ့ ခွဲပစ်ပြီး 「…မိသ / ၁းစု」ဖြစ်သွားသည် (၂၀၂၆-၀၉-၂၁
            #    ဖမ်းမိ)。 caption ရဲ့ `split2()` နဲ့ တစ်သဘောတည်း。
            _max_ln = 2 if " " in s else 1
            px, lines = SL._fit(s, mmf, inner, int(TEXT_H * H),
                                int(TEXT_H * H * 0.34), _max_ln)
            lines = (lines or [s])[:_max_ln]
            lh = int(px * 1.14)
            # ⚠️ pill အပြင် **မထွက်ရ** — ကြောင်းများလျှင် အရွယ် ထပ်လျှော့သည်
            while len(lines) * lh > ph - int(ph * 0.14) and px > 12:
                px = int(px * 0.92); lh = int(px * 1.14)
            ty = y0 + (ph - lh * len(lines)) // 2
            for ln in lines:
                a = SL._text_png(ln, px, mmf,
                                 tuple(int(c * dim) for c in TXT))
                SL._paste(im, a, x0 + ((x1 - x0) - a.shape[1]) // 2, ty)
                ty += lh

    # ── အမှတ်အသား စက် ──
    if active is not None and 0 <= active < len(items):
        cy = int((PILL_Y0 + active * PITCH + PILL_H / 2) * H)
        r = int(DOT_D * W / 2)
        cx = int(DOT_CX * W)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DOT + (255,))
    return im


def _rgb(h):
    h = str(h or "").lstrip("#")
    if len(h) != 6:
        return BORD
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ══ transcript ကနေ စာရင်း ရှာခြင်း ═══════════════════════════════
# ⚠️ ဒါက **အလွန် သတိထားရသော** အပိုင်း。 rail က မိနစ်ချီ ဆက်ပေါ်နေမည် ⇒
#    မှားလျှင် ဗီဒီယိုတစ်ခုလုံး မှားသည် (pop က ၃.၅s သာ)。
#    ⇒ **ကြေညာချက် အတိအလင်း ရှိမှသာ** လုပ်သည်。 မသေချာလျှင် မလုပ်ပါ。
import re as _re

_MMD = "၀၁၂၃၄၅၆၇၈၉"
# ⚠️ မြန်မာ ရေတွက်စကားလုံး — ASR က ဂဏန်းအဖြစ် မထုတ်တတ်ပါ
_MMW = {"တစ်": 1, "နှစ်": 2, "သုံး": 3, "လေး": 4, "ငါး": 5,
        "ခြောက်": 6, "ခုနစ်": 7, "ခုနှစ်": 7, "ရှစ်": 8, "ကိုး": 9, "ဆယ်": 10}
# ⚠️ item အစ ပြသော အမှတ်အသားများ
_ORD = [("ပထမ", 1), ("ဒုတိယ", 2), ("တတိယ", 3), ("စတုတ္ထ", 4), ("ပဉ္စမ", 5),
        ("ဆဋ္ဌမ", 6), ("သတ္တမ", 7)]
# ⚠️ 「(၅) မျိုး」·「၅ ခု」·「5 steps」 — ရေတွက်စကားလုံး ရှေ့/နောက်
_COUNT = _re.compile(
    r"[\(\（]?\s*([0-9" + _MMD + r"]{1,2})\s*[\)\）]?\s*"
    r"(မျိုး|ခု|ချက်|ဆင့်|အဆင့်|ပိုင်း|နည်း|လမ်း|steps?|ways?|things?|points?)")


_MMDIG = "၀၁၂၃၄၅၆၇၈၉"


def _mm(n):
    """ဂဏန်း → မြန်မာ ဂဏန်း (pill ထဲ ပြရန်)"""
    return "".join(_MMDIG[int(c)] for c in str(int(n)))


def _num(s):
    s = str(s or "").strip()
    # ⚠️ စာလုံးပုံစံ (「တစ်」·「နှစ်」) ကိုပါ ကိန်းအဖြစ် ပြောင်းရမည်
    if s in _MMW:
        return _MMW[s]
    out = ""
    for ch in s:
        i = _MMD.find(ch)
        out += str(i) if i >= 0 else (ch if ch.isdigit() else "")
    try:
        return int(out)
    except ValueError:
        return None


def find(segs, lo=3, hi=7):
    """စာရင်း ကြေညာချက် ရှာသည် — `(အညွှန်း, ခေါင်းစဉ်, အရေအတွက်)` · မရလျှင် None

    ⚠️ **ကြေညာချက်နဲ့ item နှစ်ခုလုံး ရှိမှ** ပြန်ပေးသည်。 ကြေညာရုံနဲ့
       rail မဆောက်ရ — ပြောသူက စာရင်းအတိုင်း မလိုက်လျှင် အလကား ဖြစ်မည်。
    """
    for i, s in enumerate(segs or []):
        t = (s.get("text") or "")
        m = _COUNT.search(t)
        n = _num(m.group(1)) if m else None
        if n is None:
            for w, v in _MMW.items():
                if _re.search(w + r"\s*(မျိုး|ခု|ချက်|ဆင့်|အဆင့်)", t):
                    n = v
                    break
        if n is None or not (lo <= n <= hi) or not fits(n):
            continue
        # ⚠️ ကြေညာပြီးနောက် item အမှတ်အသား **အနည်းဆုံး ၂ ခု** ရှိရမည်
        marks = starts(segs, i + 1, n)
        if len(marks) >= 2:
            return (i, _head(t), n)
    return None


# ⚠️ 「နံပါတ် ၁」က **တကယ့် ဒေတာထဲက အသုံးအများဆုံး** အမှတ်အသား ဖြစ်သည်
#    (tokutei transcript — seg 11/12/15)。 ordinal စကားလုံးချည်း ရှာလျှင်
#    လုံးဝ မဖမ်းမိပါ (၂၀၂၆-၀၉-၂၁ တွေ့)。
# ⚠️ ASR က **တစ်မျိုးတည်း မထုတ်ပါ** — တကယ့် ဒေတာမှာ 「နံပါတ် ၃」(ဂဏန်း) ·
#    「နံပါတ်တစ်」(စာလုံး · space မပါ) · 「နံပါတ်နှစ်」သုံးမျိုးလုံး ပါခဲ့သည်
#    (tokutei · ၂၀၂၆-၀၉-၂၁)。 ဂဏန်းချည်း စစ်လျှင် ၃ ခုမှာ ၁ ခုသာ မိပြီး
#    rail လုံးဝ မပေါ်ပါ。 ⇒ စာလုံးပုံစံကိုပါ လက်ခံရမည်。
_W1 = "တစ်|နှစ်|သုံး|လေး|ငါး|ခြောက်|ခုနစ်|ခုနှစ်|ရှစ်|ကိုး"
_MARK = _re.compile(r"(?:နံပါတ်|အမှတ်|No\.?|#)\s*[\(\（]?\s*"
                    r"([0-9" + _MMD + r"]|" + _W1 + r")")


def starts(segs, frm, n):
    """item တစ်ခုချင်း စတင်သော ဝါကျ အညွှန်းများ — `{item နံပါတ်: seg အညွှန်း}`"""
    out = {}
    for j in range(frm, len(segs or [])):
        t = (segs[j].get("text") or "")
        for w, v in _ORD:
            if v <= n and v not in out and t.lstrip().startswith(w):
                out[v] = j
        m = _re.match(r"\s*[\(\（]?\s*([0-9" + _MMD + r"])\s*[\)\）\.။]", t)
        if m:
            v = _num(m.group(1))
            if v and 1 <= v <= n and v not in out:
                out[v] = j
        mk = _MARK.search(t)
        if mk:
            v = _num(mk.group(1))
            if v and 1 <= v <= n and v not in out:
                # ⚠️ အမှတ်အသားက ဝါကျရဲ့ **အဆုံးနား** ရှိလျှင် item က
                #    နောက်ဝါကျကနေ စသည် (「… နံပါတ် ၂」/「ဂျပန်ရောက်တဲ့အထိ …」·
                #    tokutei seg 12→13)。 မလုပ်လျှင် ခေါင်းစဉ် မှားမည်。
                out[v] = j + 1 if (mk.start() > len(t) * 0.72
                                   and j + 1 < len(segs)) else j
    return out


_PRE = ("ကတော့", "ကတော", "တော့", "မှာ", "က")


def _drop_pre(t):
    """ရှေ့ဆက် အနည်းငယ် ဖယ်သည် — **`strip(charset)` မသုံးရ**

    ⚠️ `t.strip(" ကတော့မှာ")` က အက္ခရာ **အစုလိုက်** ဖြတ်သဖြင့်
       「ကိုယ့်ဘက်က」→「ိုယ့်ဘက်」ဖြစ်ပြီး မြန်မာစာ ပျက်သည်
       (၂၀၂၆-၀၉-၂၁ တွေ့)。 ⇒ စကားလုံး အပြည့်နဲ့သာ ဖြုတ်ရမည်。
    """
    t = str(t or "").strip()
    for _ in range(2):
        for w in _PRE:
            # ⚠️ **space နဲ့ ပိုင်းခြားထားမှသာ** ဖြုတ်ရမည် — `startswith` ချည်း
            #    စစ်လျှင် 「က」က 「ကိုယ့်」ရဲ့ အစကို ဖမ်းပြီး 「ိုယ့်」ဖြစ်သွားသည်
            #    (၂၀၂၆-၀၉-၂၁ ထပ်မံ တွေ့)。 စကားလုံး သီးသန့် ဖြစ်ရမည်。
            if t.startswith(w + " ") and len(t) > len(w) + 4:
                t = t[len(w) + 1:].strip()
                break
        else:
            break
    return t


def cut_at_space(t, n):
    """`n` လုံးအောက် ဖြတ်သည် — **space မှာသာ** (မြန်မာစာ မပျက်စေရန်)"""
    t = " ".join(str(t or "").split())
    if len(t) <= n:
        return t
    k = t.rfind(" ", 0, n + 1)
    return (t[:k] if k > 4 else t[:n]).strip()


def _clause(t):
    """ဝါကျထဲ **ရေတွက်ချက် ပါသော အပိုင်း**ကိုသာ ထုတ်သည်

    ⚠️ ကြေညာချက်က ဝါကျရဲ့ **ဒုတိယပိုင်း**မှာ ရှိတတ်သည် —
       「ဒါပေမဲ့ ဒီအတိုင်းတော့ မရပါဘူး။ အဓိက သော့ချက် ၃ ချက် ရှိပါတယ်။」
       ပထမပိုင်းကို ခေါင်းစဉ် ယူမိလျှင် ဘာမှန်း မသိတော့ပါ
       (tokutei seg 10 · ၂၀၂၆-၀၉-၂၁ တွေ့)。
    """
    t = " ".join(str(t or "").split())
    m = _COUNT.search(t)
    if not m:
        return t
    # ⚠️ 「။」· 「,」နဲ့ ခွဲပြီး ရေတွက်ချက် ပါသော အပိုင်းကို ယူသည်
    best, pos = t, 0
    for part in _re.split(r"(?<=[။\.])\s*", t):
        if not part.strip():
            continue
        if _COUNT.search(part):
            best = part.strip()
        pos += len(part)
    return best


def _strip_mark(t):
    """item စာသားရှေ့က 「နံပါတ် ၁」· 「၁။」 စသည်ကို ဖယ်သည်

    ⚠️ မဖယ်လျှင် pill တိုင်းမှာ 「နံပါတ် …」ပါနေပြီး နေရာ ကုန်သည်。
    """
    t = " ".join(str(t or "").split())
    # ⚠️ ဂဏန်းရော **စာလုံးပုံစံ**ရော ဖယ်ရမည် — 「နံပါတ်တစ်」က တကယ့် ဒေတာ
    t = _re.sub(r"^\s*(?:နံပါတ်|အမှတ်|No\.?|#)\s*[\(\（]?\s*"
                r"(?:[0-9" + _MMD + r"]|" + _W1 + r")\s*[\)\）\.။]?\s*", "", t)
    t = _re.sub(r"^\s*[\(\（]?\s*[0-9" + _MMD + r"]\s*[\)\）\.။]\s*", "", t)
    for w, _v in _ORD:
        if t.startswith(w):
            t = _drop_pre(t[len(w):])
            break
    return t.strip()


def _head(t):
    """ကြေညာဝါကျကနေ ခေါင်းစဉ် — ရှည်လွန်းလျှင် ဖြတ်သည်"""
    t = _clause(t)
    # ⚠️ 「ပါ」·「တယ်」တို့ကို **မသုံးရ** — စကားလုံးတွေ အလယ်မှာ ပါနေသည်
    #    (「ပြောပါမယ်」ထဲက 「ပါ」ကို ဖမ်းပြီး စာလုံးအလယ် ဖြတ်မိခဲ့သည် ·
    #     ၂၀၂၆-၀၉-၂၁ ဖမ်းမိ)。 ရှည်ပြီး တိကျသော နိဂုံးများသာ。
    for cut in ("ရှိပါတယ်", "ရှိတယ်", "ပြောပါမယ်", "ပြောမယ်", "အကြောင်း"):
        k = t.find(cut)
        if 8 <= k <= 46:
            t = t[:k]
            break
    t = _drop_pre(t)
    if len(t) <= 42:
        return t
    # ⚠️ **space မှာသာ ဖြတ်ရမည်** — `t[:42]` က မြန်မာစာလုံး အလယ်မှာ ပြတ်သည်
    k = t.rfind(" ", 0, 43)
    return (t[:k] if k > 8 else t[:42]).strip()
