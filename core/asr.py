#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · စကား → စာသား。

⚠️ **whisper က မြန်မာလို လုံးဝ မရ** — model ၂ ခုလုံး စမ်းပြီးသား:
   large-v3-turbo က `လလလလ…` တစ်လုံးတည်း ၂၁၉ ကြိမ်၊ large-v3 က
   romanised gibberish (`KooKooKooApiathDeePyoLaaMee`)。 အသံကို ကြားသည်
   (Saitama မှန်သည်) — မြန်မာစာ မရေးတတ်ရုံသာ。
   ⇒ မြန်မာ = Gemini · ဂျပန်/အင်္ဂလိပ် = whisper。

⚠️ **Gemini ရဲ့ အချိန်ကို မယုံရ** — segment timing က ~၀.၄s စောသည်。
   စာတန်းအတွက် သေလောက်သော အမှား。 ⇒ စာသားကို Gemini က ယူ၊
   **အချိန်ကို ကိုယ်တိုင် တိုင်းထားသော တိတ်ဆိတ်မှုနဲ့ ချိန်**ရသည်。
"""
import base64, json, os, re, subprocess, sys, tempfile, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gemguard as G
import measure as M

# ⚠️ `flash-lite` ကို **မသုံးရ** — ၂၀၂၆-၀၉-၁၉ တိုင်းချက် (j_8fc361134d92 ပထမ ၄၂s):
#    ဗီဇာ→「ပီဇာ」 · skill→「scale」 · Class 1→「class ဝမ်း」 · သော့ချက်→「သောချက်」 ·
#    ကုန်ကျစရိတ်→「ကုန်ကျ စိတ်」 · 特定技能→「တစ်ခုတည်း」(၅ နေရာ) · JSON ပုံစံပါ ပျက်ခဲ့。
#    `flash` က ဤအားလုံးကို မှန်အောင် ထုတ်သည်。
MODEL = os.environ.get("IKKI_GEMINI_MODEL", "gemini-flash-latest")
CHUNK = 24.0      # ⚠️ ၂၄s က တိုင်းထားသော အကောင်းဆုံး — ~၅s ကြာသည်
# ⚠️ space ညွှန်ကြားချက်ကို **ဤ prompt ထဲမှာပဲ** ထည့်ရသည် — Gemini က
#    မြန်မာစကားလုံးကို အလွန်ခွဲသည် ("ကျွန်တော် တို့")。 သီးသန့် mmspace pass
#    လုပ်လျှင် စာကြောင်းတစ်ကြောင်းလျှင် API call တစ်ခု ထပ်ကုန်သည် (၄၂ ကြောင်း =
#    ၄၂ call)。 ဤ prompt ထဲ ထည့်လျှင် **အခမဲ့** ဖြစ်ပြီး တိုင်းကြည့်တော့
#    space 18% → 13% ကျသည် ("ဇီး ဂျပန် လိုက် ချန်နယ်" → "ဇီးဂျပန်လိုက်ချန်နယ်")。
PROMPT = ("ဤအသံဖိုင်ထဲက စကားပြောသံကို မြန်မာစာဖြင့် အတိအကျ ရေးချပါ။\n"
          "- ကြားရသည့်အတိုင်းသာ ရေးပါ။ ပြင်ဆင်ခြင်း · ဖြည့်စွက်ခြင်း မလုပ်ပါနှင့်။\n"
          "- **space ကို မြန်မာစာ အမှန်အတိုင်း ထားပါ** —\n"
          "  စကားလုံးတစ်လုံးအတွင်း space မထားရ ('ကျွန်တော် တို့' ❌ → 'ကျွန်တော်တို့' ✅)\n"
          "  သီးခြားစကားလုံးများကြားတွင်သာ space ထားရ\n"
          "  English စကားလုံးများ၏ နှစ်ဖက်တွင် space ချန်ပါ\n"
          "- ရှင်းလင်းချက် မထည့်ပါနှင့်။\n"
          "\n"
          "**JSON array တစ်ခုတည်း** ပြန်ပါ — ဝါကျတစ်ခုချင်းစီအတွက် တစ်ခု:\n"
          '[{"start": 0.0, "end": 3.2, "text": "..."}, ...]\n'
          "- start/end က **ဤအသံဖိုင်ရဲ့ အစကနေ** စက္ကန့် (ဒသမ ၁ လုံး)\n"
          "- ဝါကျတစ်ခု **၂–၅ စက္ကန့်** ဖြစ်ရမည်။ ၆ စက္ကန့် မကျော်ရ\n"
          "- ရှည်လျှင် အဓိပ္ပာယ် ပြည့်တဲ့ နေရာမှာ **ခွဲပါ** (စာလုံး မဖြုတ်ရ)\n"
          "- ၂၅ စက္ကန့် အသံမှာ ဝါကျ **၅–၁၀ ခု** ရှိသင့်သည်\n"
          "- စာသားကို **မပြင်ရ · မဖြည့်ရ** — ကြားရတာ အတိအကျသာ\n"
          "\n"
          "⚠️ **space ကို ထပ်မံ သတိပေးသည်** (JSON ထဲမှာပါ တူတူ) —\n"
          "  ❌ 'ကျွန်တော် တို့ ရောက် ခါစ'   ✅ 'ကျွန်တော်တို့ ရောက်ခါစ'\n"
          "  ❌ 'တစ်လ ကို ဘယ်လောက် စု မိ မလဲ'  ✅ 'တစ်လကို ဘယ်လောက် စုမိမလဲ'\n"
          "  စကားလုံးတစ်လုံးအတွင်း space **လုံးဝ မထားရ**\n"
          "\n"
          "\n"
          "⚠️ **စကားလုံးအလိုက် အချိန်မှတ်ပါ ထည့်ပါ** — ဝါကျတစ်ခုချင်းစီမှာ\n"
          '  "words": [{"w":"စကားလုံး","s":0.0,"e":0.4}, ...]\n'
          "  · `w` = စာလုံး (ဝါကျထဲက အတိအကျ · မပြင်ရ)\n"
          "  · `s`/`e` = ဤအသံဖိုင်ရဲ့ အစကနေ စက္ကန့်\n"
          "  · စကားလုံးများ **အစဉ်လိုက်** ဖြစ်ရမည် · မထပ်ရ\n"
          "\n"
          "- JSON အပြင် ဘာမှ မရေးပါနှင့်")

# ── အသုံးအနှုန်း စာရင်း — assets/calib/glossary.json (code ထဲ မရေးရ · R5) ──
# ⚠️ ၂၀၂၆-၀၉-၁၅ တိုင်းချက်: glossary မပါလျှင် 'self value' ကို ကြိမ် ၄ ခုမှာ
#    Shes/assess/sex value/ပျောက် — ၄ မျိုး မှား。 ပါလျှင် ၄/၄ မှန်。
#    ⚠️ `write` ကို ဂျပန်လို ရေးမိလျှင် စာတန်းထဲ ဂျပန်အက္ခရာ ထွက်သည် (၄/၄)。
_GLOSS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "assets", "calib", "glossary.json")
USE_GLOSS = [True]
_GLOSS_CACHE = []

def _gloss_block():
    # ⚠️ ဖိုင် မရှိလျှင် glossary မသုံး (ရွေးချယ်ခွင့်)。 **ရှိပြီး ပုံစံ ပျက်လျှင်
    #    ကျဘမ်းရမည်** — တိတ်တဆိတ် "" ပြန်လျှင် glossary ပျောက်သွားတာ မသိရ。
    if not _GLOSS_CACHE:
        if not os.path.exists(_GLOSS_PATH):
            _GLOSS_CACHE.append("")
        else:
            g = json.load(open(_GLOSS_PATH, encoding="utf-8"))
            if not g.get("enabled", True):
                _GLOSS_CACHE.append(""); return _GLOSS_CACHE[0]
            terms = [t if isinstance(t, str) else t["write"] for t in g.get("terms", [])]
            lines = [g.get("header", "")] + [f"  {t}" for t in terms]
            lines += [f"⚠️ {r}" for r in g.get("rules", [])]
            _GLOSS_CACHE.append("\n\n" + "\n".join(x for x in lines if x))
    return _GLOSS_CACHE[0]

_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uff66-\uff9f]+")

def gloss_audit(segs):
    """glossary term တစ်လုံးချင်းရဲ့ **ထွက်စာလုံး** — render report အတွက်。

    ⚠️ glossary ရဲ့ ဆိုးကျိုးကို **မမြင်ရဘဲ ထားလို့ မရ** — ၂၀၂၆-၀၉-၁၆ တိုင်းချက်:
       `overtime` term ထည့်တော့ `アルバイト` (katakana) ၃/၈ ထွက်၊ `self value`
       ထည့်တော့ Overtime ၇/၈→၇/၁၂ ကျနိုင်ခြေ။ ⇒ term + watch စကားလုံး
       တစ်ခုချင်း အတိအကျ · ပုံစံကွဲ · CJK ကို ရေတွက်ပြသည် (ပြင်ခြင်း မလုပ်)。
    ⚠️ ပုံစံကွဲ — Latin စာလုံးသာ difflib နဲ့ ရှာ · မြန်မာ အသံထွက်ရေး
       (`ဒီအိုဗာတိုင်း`) ကို `known_bad` စာရင်းနဲ့သာ ဖမ်းနိုင်သည်。
    """
    import difflib
    try:
        g = json.load(open(_GLOSS_PATH, encoding="utf-8"))
    except FileNotFoundError:
        return None
    rep = g.get("report") or {}
    sim = float(rep.get("similarity", 1.0))
    bad = rep.get("known_bad") or {}
    text = " ".join(str(s.get("text", "")) for s in (segs or []))
    low = text.lower()
    runs = re.findall(r"[A-Za-z][A-Za-z\-]*(?:\s+[A-Za-z][A-Za-z\-]*)*", text)
    lat = lambda x: bool(re.search(r"[A-Za-z]", x))
    def one(w):
        # ⚠️ Latin — **case မခွဲ** (`Overtime` က မှန်သည်၊ ပုံစံကွဲ မဟုတ်)
        n = low.count(w.lower()) if lat(w) else text.count(w)
        forms = {}
        for b in bad.get(w, []):
            k = low.count(b.lower()) if re.search(r"[A-Za-z]", b) else text.count(b)
            if k: forms[b] = k
        if re.search(r"[A-Za-z]", w):
            nw = len(w.split())
            for r_ in runs:
                ws = r_.split()
                for m in {max(1, nw - 1), nw, nw + 1}:
                    for i in range(len(ws) - m + 1):
                        cand = " ".join(ws[i:i + m])
                        if cand.lower() == w.lower() or cand.lower() in (x.lower() for x in forms): continue
                        if difflib.SequenceMatcher(None, cand.lower(), w.lower()).ratio() >= sim:
                            forms[cand] = forms.get(cand, 0) + 1
        return dict(exact=n, variants=forms)
    terms = [t if isinstance(t, str) else t["write"] for t in g.get("terms", [])]
    return dict(enabled=bool(g.get("enabled", True)),
                terms={t: one(t) for t in terms},
                watch={w: one(w) for w in g.get("watch", [])},
                cjk=[m.group(0) for m in _CJK.finditer(text)])

# ⚠️ **တိတ်ဆိတ်သော chunk မှာ glossary မထည့်ရ**。 ၂၀၂၆-၀၉-၁၆ တိုင်းချက်:
#    `self value` ကို ဗီဒီယို ၄ ခု · ၁၆ ကြိမ် ထုတ်ခဲ့ပြီး **အားလုံး တိတ်ဆိတ်မှု
#    ၉၀%+ chunk များတွင်** — model က ဘာမှ မကြားရလျှင် စာရင်းထဲက စကားလုံးကို
#    ထုတ်ချင်တတ်သည်。 ⇒ စကား အချိုး ဤဂိတ် အောက်လျှင် glossary ဖြုတ်သည်。
GLOSS_MIN_SPEECH = 0.25
# ⚠️ **global မထားရ** — chunk များကို အပြိုင် ခေါ်သဖြင့် တစ်ခုက တစ်ခုရဲ့
#    တန်ဖိုးကို ဖျက်မိမည် (၂၀၂၆-၀၉-၁၉ အပြိုင် ပြောင်းစဉ်)。 ⇒ parameter。
def _prompt(gloss_ok=True):
    if not USE_GLOSS[0] or not gloss_ok: return PROMPT
    return PROMPT + _gloss_block()

# ⚠️ **Gemini ရဲ့ အချိန်ကို သံသယဖြင့် လက်ခံရသည်**。 `_place()` ရဲ့ မှတ်ချက်
#    (ဤဖိုင် အောက်ပိုင်း) မှာ "Gemini ရဲ့ ကိုယ်ပိုင် အချိန် ~၀.၄s စော" ဟု
#    အရင်က တိုင်းပြီး ငြင်းထားခဲ့သည်。 ယခု ပြန်သုံးသဖြင့် **လွဲချက်ကို
#    တိုင်းပြီး report မှာ ပြရမည်** — မလုံလျှင် offset ချိန်ရန်。
TIMED = [0, 0]      # [ဝါကျ အရေအတွက်, chunk အရေအတွက်] — အချိန်နဲ့ ရလာတာ


_JSONISH = re.compile(r'^[\[\]{},]|"(start|end|text)"\s*:|^\s*[\[{]')


def _looks_json(line):
    """JSON အပိုင်းအစ ဟုတ်မဟုတ် — စာတန်းထဲ မဝင်စေရန်。"""
    return bool(_JSONISH.search((line or "").strip()))


# ══ ဝါကျ ↔ အသံ တွဲခြင်း (monotone LIS) ═══════════════════════
# ⚠️ **ရိုးရိုး "အနီးဆုံးကို snap" မလုပ်ရ** — ဝါကျ ၂ ခုက တိတ်ဆိတ်မှု
#    တစ်ခုတည်းကို ယူမိပြီး အစီအစဉ် ပြောင်းပြန် ဖြစ်နိုင်သည်。
#    ⇒ အမှတ်အများဆုံး **တိုးနေသော** လမ်းကြောင်းကို DP ဖြင့် ရွေးသည်
#      (calib လုပ်စဉ်က ဤနည်းဖြင့် 903/910 ရခဲ့သည်)。
# ⚠️ Gemini ရဲ့ အချိန်က ပျမ်းမျှ **−၀.၄၃s စော** (၂၀၂၆-၀၉-၁၅ တိုင်းချက်)。
#    tolerance ထက် ဝေးသော တွဲချက်ကို လက်မခံဘဲ bias ပြင်ချက်သာ သုံးသည် —
#    ဝေးလွန်းသော snap က bias ပြင်ခြင်းထက် **ပိုမကောင်း**。
BIAS = 0.43
STAT = {}      # နောက်ဆုံး _place() ရဲ့ အကျဉ်းချုပ် — report အတွက်

# ⚠️ တွဲချက် ဤထက် နည်းလျှင် bias ကို **ဖိုင်ကနေ တိုင်း၍ မရ** —
#    ငယ်သော နမူနာနဲ့ တွက်လျှင် ဆူညံသံကို bias ဟု မှတ်မိမည်。
MIN_PAIRS = 8
# ⚠️ ASR bias က စက္ကန့်တစ်ဝက်ဝန်းကျင်သာ ဖြစ်သင့်သည် (zjl တိုင်းချက် ၀.၃၁ ·
#    module ပုံသေ ၀.၄၃)。 ဒီထက် ကြီးလျှင် alias ဖြစ်နိုင်ခြေ ပိုများသည်。
MAX_BIAS = 1.5      # ကိန်းအပြည့် ဘောင် — ဒီကျော်လျှင် alias ဟု ယူဆသည်


def est_bias(raw, onsets, W=1.0, start=BIAS, iters=4, min_pairs=MIN_PAIRS):
    """ဤဖိုင်ရဲ့ **ကိုယ်ပိုင် bias** ကို တိုင်းသည် — `(bias, တွဲမိ)` · မရလျှင် `(None, n)`

    နည်းလမ်းက `_place()` ရဲ့ မှတ်ချက်ထဲက **တည်ငြိမ်အမှတ်** အတိုင်းပင် —
    bias ထည့် → DP တွဲ → ကျန်လွဲချက် median ကို bias အသစ်အဖြစ် ထပ်သွင်း。

    ⚠️ ဘာကြောင့် လိုသလဲ — `BIAS = 0.43` က **zjl ချန်နယ်** ကနေ တိုင်းယူထားတာ。
       calib မရှိသော brand (ikki · zae) မှာ အဲဒီကိန်းကို အတိအကျ ယူသုံးနေသည် ⇒
       `cut.calib()` ရဲ့ မှတ်ချက် တားမြစ်ထားတဲ့ အမှားမျိုးပင် ("ZJL ရဲ့ ကိန်းကို
       ZAE ပေါ် သုံးလျှင် grade မှာ လုပ်မိသလို အမှား")。 ဖိုင်မှာ တွဲစရာ
       လုံလောက်လျှင် **ကိုယ့်ဖိုင်ကနေ တိုင်းတာက ချေးယူတာထက် အမြဲ ကောင်းသည်**。
    ⚠️ တွဲချက် မလုံလောက်လျှင် **မှန်းဆ မလုပ်ရ** — `None` ပြန်ပြီး ခေါ်သူက
       ပေးထားသော ကိန်းကို ဆက်သုံးကာ report မှာ 「အတည် မပြုရ」ဟု ပြရမည်。
    """
    if not raw or not onsets:
        return None, 0
    b, n = float(start), 0
    # ⚠️ အစ ကိန်းက အလွန် မှားနေလျှင် W အတွင်း တွဲစရာ မရှိတော့ဘဲ ရှာမတွေ့ဘဲ
    #    ပြန်ထွက်သွားမည် — စမ်းသပ်ချက်: −၁.၂s ကနေ စလျှင် တွဲ ၀ ခု。
    #    ⇒ **ဘောင် ကျယ်ကျယ်နဲ့ အကြမ်း တစ်ချက် ရှာပြီးမှ** ပုံမှန် ဘောင်နဲ့
    #      ချောမွေ့စေသည်。 နောက်ဆုံး ကိန်းက ပုံမှန် ဘောင်ကနေပဲ ထွက်သည်。
    _s0 = [(x, y) for x, y in raw]
    _try = align(_s0 and [(x + b, y + b) for x, y in _s0], onsets, W=W, accept=W)
    if sum(1 for j in _try if j is not None) < min_pairs:
        for wide in (2.0 * W, 4.0 * W):
            sent = [(x + b, y + b) for x, y in _s0]
            r2 = align(sent, onsets, W=wide, accept=wide)
            d2 = sorted(sent[i][0] - onsets[j] for i, j in enumerate(r2) if j is not None)
            if len(d2) >= min_pairs:
                b -= d2[len(d2) // 2]
                break
    for _ in range(max(1, iters)):
        sent = [(s0 + b, e0 + b) for s0, e0 in raw]
        res = align(sent, onsets, W=W, accept=W)
        d = sorted(sent[i][0] - onsets[j] for i, j in enumerate(res) if j is not None)
        n = len(d)
        if n < min_pairs:
            return None, n
        med = d[n // 2]
        if abs(med) < 0.005:
            break
        b -= med                      # ကျန်လွဲချက်ကို bias ထဲ ပြန်သွင်း
    # ⚠️ **alias ကို ငြင်းရမည်** — တိတ်ဆိတ်မှုတွေက အချိန်မှန် ခြားနေလျှင်
    #    DP က နောက်တစ်ခုကို တွဲမိပြီး bias ထဲ အဲဒီအကွာအဝေး တစ်ခုလုံး
    #    ဝင်သွားနိုင်သည် (စမ်းသပ်: ၄.၀s ခြား → +၂.၅ ကနေ စလျှင် +၄.၃ ထွက်)。
    #    ⇒ ဖြစ်နိုင်သော ဘောင် ကျော်လျှင် **မှန်းဆ မလုပ်ဘဲ** ငြင်းသည်。
    # ⚠️ 「အစ ကနေ ဘယ်လောက် ရွှေ့လဲ」နဲ့ မတိုင်းရ — အစ ကိန်း ကိုယ်တိုင်
    #    မှားနေတာ ဖြစ်နိုင်သည် (ချေးယူထားလို့)。 alias က **ကိန်းအပြည့်
    #    ဘောင်ကျော်** တာနဲ့ ကွဲပြားသည် ⇒ ဘောင်တစ်ခုတည်းနဲ့ စစ်သည်。
    if abs(b) > MAX_BIAS:
        return None, n
    return round(b, 3), n


def align(sent, onsets, W=0.8, accept=BIAS):
    """[(start,end)] ↔ အသံ onset — monotone DP (အမှတ်အများဆုံး တိုးနေသော လမ်းကြောင်း)。

    `sent`   — ဝါကျ (start, end) · အချိန်အလိုက် စဉ်ထားရမည်
    `onsets` — တိတ်ဆိတ်မှု **အဆုံး** (= စကားစချိန်) · စဉ်ထားရမည်
    `W`      — candidate ရွေးရာ ဘောင်
    `accept` — ဤထက် ဝေးသော ရွှေ့ချက် လက်မခံ (bias ပြင်ခြင်းက ပိုကောင်း၍)

    ပြန်ပေးသည် — ဝါကျတစ်ခုလျှင် onset index သို့မဟုတ် None。

    ⚠️ backpointer ကို **cell (i,j) အလိုက်** သိမ်းရမည်。 j တစ်ခုလျှင်
       တစ်နေရာတည်း သိမ်းလျှင် နောက်ဝါကျက ရှေ့ဝါကျရဲ့ တွဲချက်ကို ဖျက်ပစ်ပြီး
       ပြန်လျှောက်ရာမှာ ကွင်းဆက် ပြတ်သည် (စမ်းသပ်ချက် ၂ ခု ကျခဲ့သည်)。
    """
    n, m = len(sent), len(onsets)
    if not n or not m: return [None] * n
    cand = [[(j, 1.0 / (1.0 + abs(onsets[j] - st)))
             for j in range(m) if abs(onsets[j] - st) < W]
            for st, _en in sent]
    NEG = float("-inf")
    cells = {}                       # (i,j) -> (အမှတ်ပေါင်း, ရှေ့ cell)
    bestat = [(NEG, None)] * m       # index j မှာ အဆုံးသတ်သော အကောင်းဆုံး
    for i, c in enumerate(cand):
        if not c: continue
        pm = [(0.0, None)] * (m + 1)     # pm[j] = j ထက် ငယ်သော အကောင်းဆုံး
        run = (0.0, None)
        for j in range(m):
            pm[j] = run
            if bestat[j][0] > run[0]: run = bestat[j]
        pm[m] = run
        upd = []
        for j, sc in c:
            base, bcell = pm[j]
            upd.append((j, base + sc, bcell))
        for j, v, bcell in upd:
            if v > bestat[j][0]:
                cells[(i, j)] = (v, bcell)
                bestat[j] = (v, (i, j))
    if all(v == NEG for v, _ in bestat): return [None] * n
    cell = max(bestat, key=lambda t: t[0])[1]
    pairs = {}
    while cell is not None:
        i, j = cell
        if i in pairs: break
        pairs[i] = j
        cell = cells[cell][1]
    out = []
    for i, (st, _en) in enumerate(sent):
        j = pairs.get(i)
        out.append(j if (j is not None and abs(onsets[j] - st) < accept) else None)
    return out


def _parse_timed(txt, a, b):
    """JSON array → [{text,start,end}] (chunk offset ပေါင်းပြီး)。

    ⚠️ ပုံစံ မမှန်လျှင် **ကျဘမ်း မဖြစ်စေရ** — `None` ပြန်ပြီး ခေါ်သူက
       ယခင်နည်း (တစ်တုံးတည်း) သို့ ပြန်ဆုတ်သည်。
    ⚠️ R7 — စာလုံး **မပြင်ရ**。 အချိန် ခွဲရုံသာ。
    """
    m = re.search(r"\[.*\]", txt or "", re.S)
    if not m: return None
    try: arr = json.loads(m.group(0))
    except Exception: return None
    if not isinstance(arr, list) or not arr: return None
    dur = b - a
    out = []
    for x in arr:
        if not isinstance(x, dict): continue
        t = str(x.get("text") or "").strip()
        if not t: continue
        try:
            st = float(x.get("start")); en = float(x.get("end"))
        except Exception:
            continue
        # chunk ဘောင်ထဲ ဝင်ရမည် — ကျော်လျှင် ညှိသည်
        st = max(0.0, min(dur, st)); en = max(st + 0.3, min(dur, en))
        e = dict(text=t, start=round(a + st, 2), end=round(a + en, 2))
        ws = x.get("words")
        if isinstance(ws, list) and ws:
            wl = []
            for w in ws:
                try:
                    s2 = max(0.0, min(dur, float(w.get("s"))))
                    e2 = max(s2, min(dur, float(w.get("e"))))
                except Exception:
                    continue
                t2 = str(w.get("w") or "")
                if not t2.strip(): continue
                wl.append(dict(w=t2, s=round(a + s2, 2), e=round(a + e2, 2)))
            if wl: e["words"] = wl
        out.append(e)
    return out or None

def _b64(p):
    return base64.b64encode(open(p,"rb").read()).decode()

# ⚠️ API က JSON ကို **ကိုယ်တိုင် serialise** လုပ်ပေးသဖြင့် model ဘက်က
#    ပုံစံမမှန် `\uXXXX` escape (ဥပမာ `\u10`) ထွက်စရာ လမ်း မရှိတော့ပါ。
#    ၂၀၂၆-၀၉-၁၅ တိုင်းချက် — အဲဒီ escape တစ်ခုကြောင့် chunk တစ်ခုလုံး
#    (ဝါကျ ၃ ခု) ပြုတ်ကျခဲ့သည်。 run ၃ ခုမှာ ၀ · ၂ · ၁ chunk ကျခဲ့သည်。
# ⚠️ `words` — **စကားလုံးအလိုက် အချိန်မှတ်** (Zin ခွင့်ပြု ၂၀၂၆-၀၉-၁၇)。
#    ဖြတ်ပြီးသား ဗီဒီယို (ခေတ္တရပ် မရှိ) မှာ ဝါကျအဆင့် အချိန်က ±၀.၄–၁.၅s
#    လွဲသည် (တိုင်းထားသည်) ⇒ ကျောက်ချစရာ အဖြစ် စကားလုံး အချိန် လိုသည်。
#    ⚠️ `required` ထဲ **မထည့်ရ** — model က မပေးနိုင်လျှင် ဝါကျအဆင့်နဲ့ ဆက်သွားရန်。
SCHEMA = {"type":"ARRAY","items":{"type":"OBJECT","properties":{
    "start":{"type":"NUMBER"},"end":{"type":"NUMBER"},"text":{"type":"STRING"},
    "words":{"type":"ARRAY","items":{"type":"OBJECT","properties":{
        "w":{"type":"STRING"},"s":{"type":"NUMBER"},"e":{"type":"NUMBER"}},
        "required":["w","s","e"]}}},
    # ⚠️ `words` ကို **required ထဲ ထည့်မှ** model က ပေးသည် — မထည့်လျှင်
    #    ချန်ထားတတ်သည် (တိုင်းချက် ၂၀၂၆-၀၉-၁၇: ဝါကျ ၂၃/၂၃ မှာ words ၀)。
    "required":["start","end","text","words"]}}
SCHEMA_OK = [True]        # model က မထောက်ပံ့လျှင် ပိတ်ပြီး ဆက်သွားသည်

# ⚠️ တိုင်းချက် (၂၀၂၆-၀၉-၁၉ · စကား ၁၀၀.၇s): gap 5.0/အပြိုင် ၁ = ၄၁–၆၈s ·
#    gap 0.3/အပြိုင် ၆ = ၁၁–၂၁s。 စာလုံး ၁၉၂၉→၁၉၇၉ · ဖုံးအုပ်မှု တူ ⇒ **မပျောက်**。
ASR_GAP = float(os.environ.get("IKKI_ASR_GAP", "0.3"))
FALLBACK = os.environ.get("IKKI_GEMINI_MODEL_FALLBACK", "gemini-flash-lite-latest")
_FELL = [False]
# ⚠️ **ဗလာ တုံ့ပြန်ချက်ရဲ့ အကြောင်းရင်း** — 200 ပြန်ပေမယ့် စာသား မပါတာ
#    လမ်းကြောင်း ၂ မျိုး ရှိသည် (candidates ဗလာ · content ဗလာ)。 ဒါကို
#    မမှတ်လျှင် နောက်ဆုံး အမှားစာသားက 「chunk အလွတ်」ပဲ ပြပြီး ဘာလို့လဲ
#    ဘယ်တော့မှ မသိရ (၂၀၂၆-၀၉-၂၁: `gemini-flash-latest` က thinking နဲ့
#    output budget ကုန်ပြီး `finishReason=MAX_TOKENS` · content {} ပြန်သည်)。
_EMPTY_WHY = [""]

def _call(b64, mime="audio/ogg", tries=4, schema=None, model=None, gloss_ok=True):
    url = G.endpoint(model or MODEL)
    use = SCHEMA_OK[0] if schema is None else schema
    body = {"contents":[{"parts":[{"text":_prompt(gloss_ok)},
            {"inline_data":{"mime_type":mime,"data":b64}}]}],
            "generationConfig":{"temperature":0.0}}
    if use:
        body["generationConfig"]["responseMimeType"] = "application/json"
        body["generationConfig"]["responseSchema"] = SCHEMA
    for i in range(tries):
        # ⚠️ ASR သီးသန့် gap — chunk ၁၆ ခုမှာ ၅s စီ စောင့်လျှင် **၈၀s** ကုန်သည်
        G.throttle(ASR_GAP)
        r = urllib.request.Request(url, data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            c = d.get("candidates") or []
            if not c:
                _w = ("candidates ဗလာ · promptFeedback="
                      + str(d.get("promptFeedback") or "မရှိ")[:100])
                _EMPTY_WHY[0] = _w
                G.log_fail("asr", i + 1, tries, 200, _w)
                return ""
            _parts = ((c[0].get("content") or {}).get("parts")) or []
            if not _parts:
                # ⚠️ **thinking model က output budget ကုန်စေနိုင်သည်**。
                #    `finishReason=MAX_TOKENS` + content {} ဆိုလျှင် ပြန်ကြိုးစားလည်း
                #    တူတူ ဖြစ်မည် — model ပြောင်းရမည်。 ⇒ retry မကုန်စေဘဲ ထုတ်。
                _fr = str(c[0].get("finishReason") or "?")
                _w = (f"content ဗလာ · finishReason={_fr} · model="
                      f"{model or MODEL}")
                if _fr == "MAX_TOKENS":
                    _w += " — thinking နဲ့ output budget ကုန်သည် ⇒ model ပြောင်းပါ"
                _EMPTY_WHY[0] = _w
                G.log_fail("asr", i + 1, tries, 200, _w)
                return ""
            return "".join(p.get("text","") for p in _parts).strip()
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8","replace")
            # schema ကို မထောက်ပံ့လျှင် တစ်ခါတည်း ပိတ်ပြီး JSON prompt နဲ့ ဆက်သွား
            if use and e.code == 400 and ("responseSchema" in raw or "response_schema" in raw
                                          or "responseMimeType" in raw):
                G.log_fail("asr", i + 1, tries, e.code, "schema မထောက်ပံ့ — JSON prompt သို့ ပြောင်း: " + raw)
                SCHEMA_OK[0] = False
                return _call(b64, mime, tries, schema=False, model=model, gloss_ok=gloss_ok)
            # ⚠️ rate-limit 429 နှင့် credit ကုန်သော 429 က မတူ — နှစ်ခုလုံး "quota" ဟု ပြော。
            #    "quota" စာလုံးနဲ့ တိုက်လျှင် သာမန် rate limit မှာ ရပ်သွားသည်。
            if G.fatal(e.code, raw):
                # ⚠️ quota ကုန်လျှင် **တိတ်တဆိတ် ဗလာ မပြန်ရ** — ၂၀၂၆-၀၉ မှာ chunk
                #    တိုင်း ဗလာ ဖြစ်ပြီး error မပြဘဲ ASR အားလုံး ပျောက်ခဲ့သည်。
                #    ⇒ **ပိုသေးသော model ဆီ ကျဆင်း**ပြီး log မှာ ကျယ်ကျယ် ပြောသည်。
                # ⚠️ **402 (credit ကုန်) မှာ model မလဲရ** — billing က account
                #    အလိုက် ဖြစ်၍ တခြား model သုံးလည်း တူတူ ကျမည်。 ခေါ်ဆိုမှု
                #    တစ်ခု (~၆၂s) အလကား ကုန်ပြီး အမှားစာသားလည်း ရှုပ်သည်。
                _bill = ("depleted" in raw.lower() or "prepayment" in raw.lower()
                         or e.code == 402)
                if MODEL != FALLBACK and not _FELL[0] and not _bill:
                    _FELL[0] = True
                    G.log_fail("asr", i + 1, tries, e.code,
                               f"{MODEL} ရပ်သွား — {FALLBACK} သို့ ကျဆင်းသည်", final=False)
                    print(f"  ⚠️ ASR model {MODEL} ရပ်သွားပြီ (quota?) — "
                          f"{FALLBACK} နဲ့ ဆက်သွားသည်။ စာလုံးပေါင်း ညံ့နိုင်သည်။", flush=True)
                    return _call(b64, mime, tries, schema, model=FALLBACK, gloss_ok=gloss_ok)
                G.log_fail("asr", i + 1, tries, e.code, raw, final=True)
                raise RuntimeError(f"Gemini ရပ်သွားပြီ: {raw[:200]}")
            G.log_fail("asr", i + 1, tries, e.code, raw)
            m = re.search(r'"retryDelay"\s*:\s*"(\d+)s"', raw)
            time.sleep(int(m.group(1)) if m else min(45, 6*(i+1)))
        except Exception as e:
            G.log_fail("asr", i + 1, tries, None, f"{type(e).__name__}: {e}")
            time.sleep(min(30, 5*(i+1)))
    G.log_fail("asr", tries, tries, None, "retry ကုန် — \"\" ပြန်", final=True)
    return ""

def burmese(wav, log=print, meas=None, align_cfg=None):
    """မြန်မာ — Gemini ဖြင့် စာသား၊ အချိန်ကို တိတ်ဆိတ်မှုနဲ့ ချိန်သည်。

    `meas` — `measure.speech()` ရဲ့ ရလဒ် (sp, sil, dur, ev, cls)。
    ⚠️ **တစ်ခါပဲ တွက်ရမည်** — အရင်က ဒီမှာ `band/threshold/gaps` နဲ့ သီးသန့်
       တွက်ခဲ့ပြီး `cut.plan()` က `speech()` သုံးသဖြင့် မြေပုံ ၂ ခု ကွဲခဲ့သည်。
       ⇒ worker က တစ်ခါ တွက်ပြီး ASR · cut · dress သုံးခုလုံးကို မျှပေးသည်。
    """
    if meas is None: meas = M.speech(wav)
    sp, sil2, dur, _ev, _cls = meas
    # ⚠️ chunk အစွန်းကို **တိတ်ဆိတ်မှုထဲ** ချရသည် — စာလုံးအလယ် ဖြတ်လျှင်
    #    Gemini က နှစ်ဖက်စလုံးမှာ မှားရေးသည် (chunk seam artefact)。
    sil = M.as_gaps(sil2, min_len=0.24)
    marks=[0.0]
    while marks[-1] + CHUNK < dur:
        want = marks[-1] + CHUNK
        near = min(sil, key=lambda s: abs(s[2]-want)) if sil else None
        marks.append(near[2] if near and abs(near[2]-want) < CHUNK*0.4 else want)
    marks.append(dur)

    out=[]; n_try = n_empty = 0
    TIMED[0] = TIMED[1] = 0
    # ⚠️ ပုံမှန်ထက် အလွန် ရှည်သော တုံ့ပြန်ချက် = ထပ်နေသော စာသား ထုတ်နေခြင်း。
    #    ၂၀၂၆-၀၉-၁၅ တိုင်းချက် — JSON ပျက်သော ၂ ခု: ၁၉၂၇ · ၁၇၀၈ လုံး ·
    #    တူညီသော chunk ရဲ့ ပုံမှန် ၃၉၇–၄၁၀ လုံး (≈၅ ဆ)。 parse အောင်သည့်
    #    တိုင် စာသား ယုံကြည်ရမှု နည်းသဖြင့် သတိပေးသည် (ဖယ်မထုတ်ပါ — R7)。
    lens = []
    warn_x    = float((align_cfg or {}).get("long_warn_x", 0) or 0)
    # ⚠️ ပုံသေ ၁ → ၃ (Zin ၂၀၂၆-၀၉-၁၇) — calib မရှိသော brand (zae · AA Japan) က
    #    JSON ပျက်လျှင် ချက်ချင်း လက်လျှော့ခဲ့သည်。 zjl မှာ ၃ ဖြင့် တိုင်းထားပြီး
    #    (chunk ၁၉: ၅/၅ · chunk ၃၅: ၄/၅) ⇒ brand အားလုံး တူညီစေရန်。
    tries_json = int((align_cfg or {}).get("json_tries", 3) or 3)
    work=tempfile.mkdtemp(prefix="ikki_asr_")
    try:
        # ⚠️ **chunk များကို အပြိုင် ခေါ်သည်** — ၂၀၂၆-၀၉-၁၉ တိုင်းချက်:
        #    ၆ မိနစ် ဗီဒီယိုမှာ chunk ၁၆ ခု × ~၈.၅s = ~၁၄၀s ကို **တစ်ခုပြီးမှ
        #    တစ်ခု** ခေါ်နေခဲ့သည်。 network စောင့်ချိန်သာ ဖြစ်၍ အပြိုင် ခေါ်လျှင်
        #    တိုက်ရိုက် ချုံ့လို့ရသည်。
        # ⚠️ သို့သော် **အစုလိုက်** လုပ်ရမည် — quota ကုန်လျှင် ချက်ချင်း ရပ်စေမည့်
        #    「chunk ၄ ခု ဆက်တိုက် အလွတ်」 ကာကွယ်ချက်ကို မပျက်စေရန်。
        #    အားလုံး တစ်ပြိုင်နက် ခေါ်လျှင် အဲဒါ အလုပ် မဖြစ်တော့。
        PAR = int(os.environ.get("IKKI_ASR_PAR", "6"))
        from concurrent.futures import ThreadPoolExecutor
        _cuts = []
        for i in range(len(marks)-1):
            a,b = marks[i], marks[i+1]
            if b-a < 0.6: continue
            p = os.path.join(work, f"c{i:03d}.ogg")
            subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{a:.2f}","-i",wav,
                "-t",f"{b-a:.2f}","-ac","1","-ar","16000","-c:a","libopus","-b:a","24k",p],
                check=True)
            _cuts.append((i, a, b, p))

        def _fetch(job):
            i, a, b, p = job
            _spk = sum(min(b, e2) - max(a, s2) for s2, e2 in sp if e2 > a and s2 < b)
            _ok = ((_spk / (b - a)) if b > a else 1.0) >= GLOSS_MIN_SPEECH
            t0 = time.time(); txt = ""; tm = None
            for _k in range(max(1, tries_json)):
                txt = _call(_b64(p), gloss_ok=_ok)
                if not txt.strip(): break
                tm = _parse_timed(txt, a, b)
                if tm: break
                if _k + 1 < max(1, tries_json):
                    log(f"  ↻ ASR chunk {i+1} — JSON ပျက် ({len(txt)} လုံး) · "
                        f"ပြန်ခေါ်သည် {_k+2}/{tries_json}")
            return (i, a, b, txt, tm, time.time() - t0)

        _res = []
        with ThreadPoolExecutor(max_workers=max(1, PAR)) as _ex:
            for _k0 in range(0, len(_cuts), max(1, PAR)):
                _res.extend(list(_ex.map(_fetch, _cuts[_k0:_k0+max(1, PAR)])))
                # ⚠️ အစု တစ်ခု ပြီးတိုင်း ရပ်သင့်မရပ်သင့် စစ်သည်
                _e = sum(1 for r in _res if not r[3].strip())
                if len(_res) >= 4 and _e == len(_res):
                    break
        log(f"  ASR · chunk {len(_cuts)} ခု · အပြိုင် {PAR}")
        _RES = {r[0]: r for r in _res}

        for (i, a, b, p) in _cuts:
            # ⚠️ **JSON ပျက်လျှင် ပြန်ခေါ်ရမည်** — ကျဘမ်းက ကျပန်းဖြစ်၍
            #    (run ၃ ခုမှာ ၀ · ၂ · ၁ chunk ကျခဲ့ပြီး ကျတဲ့ chunk မတူ)。
            #    ပြန်မခေါ်လျှင် chunk တစ်ခုလုံး (၂၀–၃၀s စကား) ပျောက်သည်。
            _r = _RES.get(i)
            if _r is None: continue
            _i2, _a2, _b2, txt, tm, _el = _r
            log(f"  ASR {i+1}/{len(marks)-1} · {b-a:.0f}s → {len(txt)} လုံး · {_el:.1f}s")
            n_try += 1
            if not txt.strip(): n_empty += 1
            # ⚠️ **တိတ်တဆိတ် ဆက်မသွားရ**。 Gemini ရဲ့ နေ့စဥ် quota ကုန်သွားချိန်
            #    chunk တိုင်း အလွတ် ပြန်ပြီး pipeline က ဆက်သွားခဲ့သည် —
            #    ၃၉ chunk × ၂၄၀s = ၂.၆ နာရီ ကုန်ပြီး စာသား လုံးဝ မပါသော
            #    ဗီဒီယို ထွက်လာမည် (စာတန်း မရှိ · ဂရပ်ဖစ် မရှိ · ဖြတ်ချက်
            #    စကားထဲ ကျမကျ မစစ်နိုင်)。 ⇒ အစောပိုင်းမှာပဲ ရပ်သည်。
            if n_try >= 4 and n_empty == n_try:
                raise RuntimeError(
                    f"ASR က chunk {n_try} ခုဆက်တိုက် အလွတ် ပြန်နေသည် — "
                    f"Gemini ရဲ့ နေ့စဉ် quota ကုန်နေခြင်း ဖြစ်နိုင်သည် "
                    f"(model {MODEL})။ IKKI_GEMINI_MODEL ကို ပြောင်းပါ "
                    f"သို့မဟုတ် quota ပြန်ရသည်အထိ စောင့်ပါ။")
            # ⚠️ **အချိန်နဲ့ ပြန်လာလျှင် အဲဒါကို သုံး** — CHUNK 24s ကြောင့်
            #    အရင်က chunk တစ်ခုလုံး စာကြောင်းတစ်ခုတည်း ဖြစ်ပြီး
            #    ၂၁.၄s/ကြောင်း ရှိခဲ့သည် (စာတန်း · slide နေရာချ · transcript
            #    ဖြတ်ခြင်း သုံးခုလုံး ပိတ်မိသည်)。
            if warn_x and txt.strip():
                if len(lens) >= 3:
                    med = sorted(lens)[len(lens)//2]
                    if med and len(txt) > med * warn_x:
                        log(f"  ⚠️ ASR chunk {i+1} — တုံ့ပြန်ချက် {len(txt)} လုံး · "
                            f"ပုံမှန် median {med} × {warn_x:g} ကျော် · "
                            f"ထပ်နေသော စာသား ဖြစ်နိုင် (စာသား မဖယ်ပါ)")
                lens.append(len(txt))
            if tm:
                TIMED[0] += len(tm); TIMED[1] += 1
                for x in tm:
                    # ⚠️ `words` ကို **ဒီမှာ ပါ သယ်ရမည်** — မသယ်လျှင် `_place`
                    #    မှာ မမြင်ရဘဲ ဝါကျအဆင့် အချိန်ပဲ သုံးဖြစ်သည် (တကယ် ဖြစ်ခဲ့)。
                    _e = dict(text=x["text"], chunk=i, a=round(a,2),
                              b=round(b,2), start=x["start"], end=x["end"])
                    if x.get("words"): _e["words"] = x["words"]
                    out.append(_e)
            else:
                # ပုံစံ မမှန် — ယခင်နည်း (တစ်တုံးတည်း) · **ကျဘမ်း မဖြစ်စေရ**
                # ⚠️ **JSON အကြမ်းကို စာတန်းအဖြစ် မသိမ်းရ** — ပုံစံ မမှန်တဲ့
                #    chunk ရဲ့ `[{"start": 7.35, …` က မျက်နှာပြင်ပေါ် တက်သွားခဲ့သည်
                #    (တကယ် ဖြစ်ခဲ့)。 JSON ပုံစံ ပါတဲ့ စာကြောင်း ဖယ်ရမည်。
                good = []
                for line in [x.strip() for x in txt.splitlines() if x.strip()]:
                    if _looks_json(line): continue
                    good.append(line)
                if txt.strip():
                    log(f"  ⚠️ ASR chunk {i+1} — JSON ပုံစံ မမှန် · "
                        f"အချိန် မခွဲဘဲ သိမ်းသည် ({len(good)} ကြောင်း)")
                # ⚠️ **နှစ်ခါ မတိုးရ** — အပေါ်မှာ `if not txt.strip()` နဲ့
                #    တိုးပြီးသား ဖြစ်၍ ဗလာ chunk တစ်ခုကို ၂ ခု ဟု ရေတွက်မိသည်
                #    ⇒ chunk ၆ ခု ဗလာဆို 「၁၂/၆ ခု အလွတ်」ဟု ပြခဲ့သည်
                #    (၂၀၂၆-၀၉-၂၁ Zin ရဲ့ မျက်နှာပြင်)。 ဒီမှာက စာသား
                #    **ရပေမယ့် သုံးမရ**တာကိုသာ ရေတွက်ရမည်。
                if not good and txt.strip(): n_empty += 1
                for line in good:
                    out.append(dict(text=line, chunk=i, a=round(a,2), b=round(b,2)))
    finally:
        subprocess.run(["rm","-rf",work])
    # ⚠️ တစ်ဝက်ကျော် အလွတ်ဆိုလျှင် ရလဒ်က မယုံရ — စာတန်းတွေ ပြုတ်ကျန်မည်
    if n_try and n_empty > n_try * 0.5:
        # ⚠️ **တကယ့် အကြောင်းရင်းကို ပြရမည်** (「Name the blocker」)。
        #    ၂၀၂၆-၀၉-၂၁: တကယ်က `402 credits are depleted` ဖြစ်ပါလျက်
        #    「chunk ၁၂/၆ ခု အလွတ် (model gemini-flash-latest)」ဟု ပြခဲ့သဖြင့်
        #    model/ASR ချွတ်ယွင်းချက် ဟု ထင်ရပြီး **ဘာလုပ်ရမလဲ မသိ**ပါ。
        _why = (G.reason() or "")
        _wl = _why.lower()
        if "depleted" in _wl or "prepayment" in _wl or "billing" in _wl:
            raise RuntimeError(
                "Gemini ရဲ့ credit ကုန်ပါပြီ — စာသား ထုတ်လို့ မရပါ။ "
                "ai.studio/projects မှာ billing ဖြည့်ပြီး ပြန်လုပ်ပါ။ "
                "(ဗီဒီယို မထုတ်ပါ · မိနစ် မယူပါ · မူရင်း ဖိုင် မထိပါ)")
        if "quota" in _wl or "rate" in _wl:
            raise RuntimeError(
                f"Gemini ရဲ့ quota ကုန်နေပါသည် — စာသား ထုတ်လို့ မရပါ။ "
                f"ခဏ စောင့်ပြီး ပြန်လုပ်ပါ (model {MODEL})။")
        _w2 = _why or _EMPTY_WHY[0]
        raise RuntimeError(
            f"ASR chunk {n_empty}/{n_try} ခု အလွတ် — စာသား မပြည့်စုံပါ "
            f"(model {MODEL})။ ဒီအတိုင်း ဆက်လုပ်လျှင် စာတန်း ပြုတ်မည်။"
            + (f" အကြောင်းရင်း: {_w2[:160]}" if _w2 else ""))
    if not out:
        raise RuntimeError(f"ASR က စာသား လုံးဝ မရပါ (model {MODEL})")
    log(f"  ASR · အချိန်ပါ ဝါကျ {TIMED[0]} ခု / chunk {TIMED[1]}/{len(marks)-1} · "
        f"စုစုပေါင်း စာကြောင်း {len(out)}")
    # ── စာကြောင်းတိုင်းကို chunk အတွင်း စကားပြောချိန်နဲ့ ဖြန့်ချသည် ──
    # အကြမ်း အချိန် (bias/snap မလုပ်ရသေး) ကို သိမ်းနိုင်သည် — W sweep ·
    # bias ပြန်တိုင်းရန် လိုသည်။ ရလဒ်ကို မထိပါ (debug hook သာ)。
    if os.environ.get("IKKI_ASR_RAW"):
        try:
            with open(os.environ["IKKI_ASR_RAW"], "w") as fh:
                json.dump(out, fh, ensure_ascii=False)
        except Exception as e:
            log(f"  ⚠️ ASR raw dump မအောင်: {e}")
    return _place(out, meas, cfg=align_cfg)


# ══ စကားလုံး အချိန်မှတ် — ထိန်းသိမ်းခြင်း နှင့် စစ်ဆေးခြင်း ═══════════
# ⚠️ `_place()` က ယခင်က `words` ကို **span တွက်ရန်သာ** သုံးပြီး ထွက်ချက်ထဲ
#    မထည့်ခဲ့ပါ (`asr.py` ရဲ့ out.append မှာ text/start/end သာ)。 ⇒ Script
#    Editor က စကားလုံးအလိုက် အချိန်ကို လုံးဝ မမြင်ရပါ (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。
# ⚠️ Gemini ရဲ့ အချိန်က **အရိပ်အမြွက်သာ**、ground truth မဟုတ်ပါ ⇒ ထိန်းသိမ်းရုံနဲ့
#    မလုံလောက်、**confidence နဲ့တွဲ** ပေးရမည်。


def shift_words(words, s0, e0, st, en, tol=0.25):
    """raw span `(s0,e0)` ကနေ placed span `(st,en)` သို့ စကားလုံးများ ရွှေ့သည်。

    ပြန်ပေးသည် — `(words, conf, note)`。 မရလျှင် `(None, 0.0, အကြောင်းရင်း)`。

    ⚠️ **ဆန့်ခြင်း (stretch) ကို သတိထားရမည်** — placed span က raw span ထက်
       သိသိသာသာ ကွာလျှင် စကားလုံး အချိန်တွေ မှားကုန်မည်。 ⇒ ရွှေ့ရုံသာ
       လုပ်ပြီး、ဆန့်ရလျှင် confidence လျှော့သည်。
    ⚠️ ဖြတ်ပစ်၍ **မရ** — ဝင်းဒိုးပြင် ကျသော စကားလုံးကို ဘောင်ထဲ ချသည်。
    """
    if not words:
        return None, 0.0, "words မပါ"
    try:
        ws = [(str(w.get("w") or ""), float(w["s"]), float(w["e"])) for w in words]
    except (KeyError, TypeError, ValueError):
        return None, 0.0, "ပုံစံ မမှန်"
    if not ws:
        return None, 0.0, "words ဗလာ"
    raw = max(1e-3, e0 - s0)
    new = max(1e-3, en - st)
    ratio = new / raw
    off = st - s0
    out = []
    prev = st
    for w, a, b in ws:
        a2 = max(st, min(en, a + off))
        b2 = max(a2, min(en, b + off))
        if a2 < prev:
            a2 = prev
        if b2 <= a2:
            b2 = min(en, a2 + 0.02)
        out.append(dict(w=w, s=round(a2, 3), e=round(b2, 3)))
        prev = a2
    # ⚠️ confidence — ဆန့်မှု များလေ နိမ့်လေ。 ၁.၀ က ရွှေ့ရုံ。
    conf = max(0.0, 1.0 - abs(ratio - 1.0) / max(tol, 1e-6) * 0.5)
    conf = round(min(1.0, conf), 3)
    note = "ရွှေ့ရုံ" if abs(ratio - 1.0) <= 0.02 else f"ဆန့် ×{ratio:.2f}"
    return out, conf, note


def check_words(words, st, en, dur=None):
    """စကားလုံး အချိန်မှတ် စစ်ဆေးချက် — ချိုးဖောက်ချက် စာရင်း ပြန်ပေးသည်

    ⚠️ 「valid or explicitly low-confidence」— မမှန်လျှင် **ဖျောက်မထားရ**、
       ဘာမှားလဲ ပြောရမည်。
    """
    bad = []
    if not words:
        return ["words မရှိ"]
    prev_e = None
    for i, w in enumerate(words):
        try:
            a, b = float(w["s"]), float(w["e"])
        except (KeyError, TypeError, ValueError):
            bad.append(f"[{i}] ပုံစံ မမှန်"); continue
        if b <= a:
            bad.append(f"[{i}] end ≤ start ({a:.3f}≥{b:.3f})")
        if a < st - 0.05 or b > en + 0.05:
            bad.append(f"[{i}] ဝါကျ ဘောင်ပြင် ({a:.2f}–{b:.2f} ⊄ {st:.2f}–{en:.2f})")
        if dur and (a < -0.05 or b > dur + 0.05):
            bad.append(f"[{i}] source ကျော် ({b:.2f} > {dur:.2f})")
        if prev_e is not None and a < prev_e - 0.05:
            bad.append(f"[{i}] အစဉ် ပြောင်းပြန် ({a:.3f} < {prev_e:.3f})")
        prev_e = b
    return bad


def _place(lines, meas, cfg=None):
    """စာကြောင်းများကို တိုင်းထားသော စကားပြောကြားကာလပေါ် ချထားသည်。

    ⚠️ **Gemini ရဲ့ အချိန်က စနစ်တကျ စောသည်** — ၂၀၂၆-၀၉-၁၅ · ၉၂၉s · ဝါကျ ၁၄၅:
         တည်ငြိမ် bias **၀.၃၁၀s** · တွဲ ၈၇ · ကျန်လွဲချက် |x| median ၀.၁၅၀s
         · ≥၀.၅s ၁၀/၈၇
       တိုင်းနည်း — **တည်ငြိမ်အမှတ်**: bias ထည့် → DP တွဲ → ကျန်လွဲချက်
       median ကို bias အသစ် အဖြစ် ထပ်သွင်း (၃ ကြိမ်တွင် ငြိမ်သည်)。
       ⚠️ **"အနီးဆုံး onset နဲ့ တိုင်း" မလုပ်ရ** — အနီးဆုံး ရွေးခြင်းက
          လွဲချက် ငယ်သူကိုပဲ ကောက်ယူ၍ ရွေးချယ်မှု ဘက်လိုက်မှု ဝင်သည်。
          အရင် n=၁၆ (၁၂၀s) နဲ့ ၀.၄၃ ရခဲ့တာ ဒီနည်းကြောင့် ဖြစ်သည်。
    ⚠️ ဝါကျ ၁၄၅ တွင် ၈၉ ခုသာ W အတွင်း တိတ်ဆိတ်မှု ရှိသည် (၆၁%) —
       ကျန်သည် ခေတ္တရပ် မရှိဘဲ သဒ္ဒါအရ ခွဲထားသဖြင့် snap စရာ မရှိပါ。
       ⇒ "snap %" ဂိတ်ကို **ဝါကျစုစုပေါင်း**နဲ့ မတိုင်းရ — ရနိုင်သူနဲ့
         တိုင်းရမည် (၈၇/၈၉ = ၉၈%)。
    ⚠️ space — JSON prompt က space မတိုးစေပါ。 chunk ၅ ခု တိုက်ရိုက် တိုင်းချက်
       (၂၀၂၆-၀၉-၁၅): ဟောင်း **၁၄.၉%** · အသစ် **၁၃.၇%**。
       ရှေ့က `' '.join(seg.text)` ဖြင့် တွက်ခဲ့တာ **အတု** ဖြစ်ခဲ့သည် —
       segment အရေအတွက် ကွာလျှင် ပေါင်းစပ် space အချိုး ကွာသွား၍。
    """

    sp, sil, _dur, _ev, _cls = meas
    _dur_hint = float(_dur or 0) or None
    cfg = cfg or {}
    bias = float(cfg.get("bias_s", BIAS))
    W    = float(cfg.get("window_s", 1.0))
    mg   = float(cfg.get("min_gap_s", 0.3))
    gaps = [(x, y) for x, y in sil if y - x >= mg]
    onsets  = [y for x, y in gaps]        # တိတ်ဆိတ်မှု အဆုံး = စကားစ
    offsets = [x for x, y in gaps]        # တိတ်ဆိတ်မှု အစ   = စကားဆုံး

    # ⚠️ ပုံသေ ပိတ် → ၃.၀ (Zin ၂၀၂၆-၀၉-၁၇) — calib မရှိသော brand မှာ end-snap က
    #    ၀.၀၁s ဝါကျ ဖြစ်စေနိုင်သည် (zjl တိုင်းချက် ၂၀၂၆-၀၉-၁၅)。
    cps_x = float(cfg.get("cps_guard_x", 3.0) or 3.0)
    timed = [l for l in lines if l.get("start") is not None]
    # ⚠️ အကြမ်းကနေ တွက်သော CPS median — **ဗီဒီယိုတိုင်း သီးသန့်**。
    #    end-snap ရွေးရာမှာ ကာကွယ်ရန် လိုသည် (အောက်ကို ကြည့်)。
    _r = sorted(len(l["text"]) / (l["end"] - l["start"])
                for l in timed if l["end"] - l["start"] > 0)
    cps_med = _r[len(_r) // 2] if _r else 0.0
    rest  = [l for l in lines if l.get("start") is None]
    out = []
    STAT.clear(); STAT.update(timed=len(timed), snapped=0, biased=0, reach=0,
                              word_kept=0, word_bad=0)
    if timed:
        # ⚠️ **bias ကို အရင် ပြင်ပြီးမှ snap** — snap က bias ကို ပြိုင်တာ မဟုတ်ဘဲ
        #    သန့်စင်ပေးတာ。 မူရင်း start နဲ့ တိုင်းလျှင် accept ဘောင်က ပျမ်းမျှ
        #    လွဲချက် ဖြစ်နေ၍ **သင်္ချာအရ တစ်ဝက် ပယ်မိ**သည် (sweep ဖြင့် အတည်ပြု)。
        # ⚠️ **စကားလုံး အချိန် ရှိလျှင် အဲဒါကို ဦးစားပေး** (Zin ခွင့်ပြု ၂၀၂၆-၀၉-၁၇) —
        #    ဖြတ်ပြီးသား ဖိုင် (ခေတ္တရပ် မရှိ) မှာ ဝါကျအဆင့် အချိန်က ±၀.၄–၁.၅s
        #    လွဲသည်。 စကားလုံး အချိန်က ပထမစာလုံးရဲ့ စချိန်ကို ပိုတိကျစေသည်。
        _nw = 0
        def _span(l):
            global _nw
            ws = l.get("words") or []
            if len(ws) >= 2:
                try:
                    return float(ws[0]["s"]), float(ws[-1]["e"]), True
                except Exception:
                    pass
            return float(l["start"]), float(l["end"]), False
        _pairs = [_span(l) for l in timed]
        _nw = sum(1 for _s, _e, ok in _pairs if ok)
        STAT["word_ts"] = _nw
        # ⚠️ **ချေးယူထားသော bias ထက် ကိုယ့်ဖိုင်ကနေ တိုင်းတာက ကောင်းသည်** —
        #    `bias` ပုံသေက zjl ကနေ လာသည်。 တွဲစရာ လုံလောက်လျှင် ဒီဖိုင်ရဲ့
        #    ကိုယ်ပိုင်ကိန်းကို သုံးပြီး၊ မလုံလောက်လျှင် ပေးထားတာကို ဆက်သုံးကာ
        #    **အတည် မပြုရသေးကြောင်း** report မှာ ပြသည် (STAT["bias_src"])。
        _raw = [(s0, e0) for s0, e0, _ok in _pairs]
        _eb, _en_pairs = est_bias(_raw, onsets, W=W, start=bias)
        STAT["bias_pairs"] = _en_pairs
        if _eb is not None:
            STAT["bias_src"] = "measured"
            STAT["bias_given"] = round(bias, 3)
            bias = _eb
        else:
            STAT["bias_src"] = "unverified"
        STAT["bias_s"] = round(bias, 3)
        sent = [(s0 + bias, e0 + bias) for s0, e0, _ok in _pairs]
        # ရနိုင်သူ = W အတွင်း onset ရှိသော ဝါကျ。 ဂိတ်ကို ဒီနဲ့ တိုင်းရမည် —
        # ခေတ္တရပ် မရှိသော ဝါကျကို snap မရတာ ချို့ယွင်းချက် မဟုတ်ပါ。
        STAT["reach"] = sum(1 for st0, _e in sent
                            if any(abs(o - st0) < W for o in onsets))
        res = align(sent, onsets, W=W, accept=W)
        prev = None
        for i, l in enumerate(timed):
            s0, e0 = sent[i]
            j = res[i]
            if j is None:
                st, en = s0, e0; STAT["biased"] += 1
            else:
                st = onsets[j]; STAT["snapped"] += 1
                # ⚠️ end ကိုပါ **နောက်တိတ်ဆိတ်မှုရဲ့ အစ**သို့ snap
                # ⚠️ သို့သော် **အနီးဆုံးကို မျက်စိမှိတ် မယူရ** — ၂၀၂၆-၀၉-၁၅:
                #    ၇၁၁.၀ က ၇၁၁.၅၈ ထက် ၀.၀၂s ပိုနီးရုံနဲ့ ရွေးမိပြီး
                #    အရှည် ၀.၇၀s → ၀.၁၂s (CPS ၁၉၂) ဖြစ်သွားခဲ့သည်。
                #    ⇒ CPS က median × cps_guard_x ကျော်စေမယ့် ကိုယ်စားလှယ်
                #      မယူရ。 တစ်ခုမှ မကျန်လျှင် မူရင်း အရှည်ကို ရွှေ့သုံးသည်。
                c = [o for o in offsets if o > st and abs(o - e0) < W]
                if cps_x and cps_med and c:
                    n = len(l["text"])
                    ok = [o for o in c if o > st and n / (o - st) <= cps_med * cps_x]
                    if ok: c = ok
                    else:  c = []
                en = min(c, key=lambda o: abs(o - e0)) if c else e0 + (st - s0)
            # ⚠️ အစီအစဉ် မချိုးရ · အရှည် ၀ ထက် ကြီးရမည်
            if prev is not None and st <= prev: st = prev + 0.01
            if en <= st: en = st + 0.4
            # ⚠️ **`words` ကို သယ်ရမည်** — ယခင်က ဒီမှာ ကျန်ခဲ့ပြီး Script
            #    Editor က စကားလုံးအလိုက် အချိန် လုံးဝ မမြင်ရခဲ့ပါ。
            _e = dict(text=l["text"], start=round(st, 2), end=round(en, 2))
            _w, _wc, _wn = shift_words(l.get("words"), s0, e0, st, en)
            if _w:
                _bad = check_words(_w, st, en, _dur_hint)
                if _bad:
                    # ⚠️ မမှန်လျှင် **ဖျောက်မထားရ** — ပြပြီး confidence ၀ ချသည်
                    STAT["word_bad"] = STAT.get("word_bad", 0) + 1
                    _e["words_note"] = _bad[0][:60]
                    _wc = 0.0
                else:
                    _e["words"] = _w
                    STAT["word_kept"] = STAT.get("word_kept", 0) + 1
                _e["words_conf"] = _wc
                _e["timing_src"] = "word" if _pairs[i][2] else "segment"
            else:
                # ⚠️ စကားလုံး အချိန် မရှိလျှင် **ဝါကျအဆင့်ဟု ရိုးရိုးသားသား
                #    ပြောရမည်** — word-accurate ဟု ဟန်ဆောင်၍ မရ。
                _e["words_conf"] = 0.0
                _e["timing_src"] = "segment"
            _e["place"] = "snap" if j is not None else "bias"
            out.append(_e)
            prev = st

    # ── အချိန် မပါသော စာကြောင်း — ယခင်နည်း (chunk အတွင်း အချိုးကျ) ──
    by = {}
    for l in rest: by.setdefault(l["chunk"], []).append(l)
    for ci, ls in sorted(by.items()):
        a_, b_ = ls[0]["a"], ls[0]["b"]
        runs = [(max(s2, a_), min(e2, b_)) for s2, e2 in sp if e2 > a_ and s2 < b_]
        talk = sum(e2 - s2 for s2, e2 in runs) or (b_ - a_)
        tot = sum(max(1, len(l["text"])) for l in ls)
        pos = a_
        for l in ls:
            share = max(1, len(l["text"])) / tot
            st = pos; en = min(b_, pos + talk * share * ((b_ - a_) / talk if talk else 1))
            # ⚠️ ဒါက **စာလုံးရေ အချိုးနဲ့ ခွဲထားတာ** — အချိန်မှတ် မဟုတ်ပါ。
            #    「Never use character-count allocation as authoritative timing」
            #    ⇒ confidence ၀ နဲ့ အမှတ်အသား တပ်ရမည်。
            out.append(dict(text=l["text"], start=round(st, 2),
                            end=round(max(st + 0.4, en), 2),
                            words_conf=0.0, timing_src="charshare",
                            place="charshare"))
            pos = en
    out.sort(key=lambda x: x["start"])
    # ⚠️ **နောက်ဆုံး အာမခံချက်** — အချိန်ပါ ဝါကျနဲ့ အချိန်မပါ ဝါကျ ရောပြီးမှ
    #    စစ်ရသည်。 `end` ကို နောက်တိတ်ဆိတ်မှုဆီ snap လျှင် နောက်ဝါကျရဲ့
    #    စချိန်ကို ကျော်နိုင်သည် (ထပ်နေလျှင် စာတန်း ၂ ကြောင်း တစ်ပြိုင်နက်)。
    # ⚠️ သို့သော် **အမြဲ clamp လုပ်၍ မရ** — chunk seam မှာ ဝါကျ ၂ ခုရဲ့
    #    စချိန် ကပ်နေလျှင် ၀.၀၁s ဝါကျ ဖြစ်သွားသည် (၂၀၂၆-၀၉-၁၅ တိုင်းချက်:
    #    median×၃ ကျော်သူ ၂ ခု → ၄ ခု **တိုးသွား**ခဲ့သည် — ပြင်ချက်က
    #    ပြဿနာကို ဖုံးလိုက်တာ)。 ⇒ clamp ပြီး CPS က ဗီဒီယိုရဲ့ median ×
    #    `cps_guard_x` ကျော်လျှင် ဝါကျ ၂ ခုကို **ပေါင်း**သည် (စာလုံး မဖျက် ·
    #    မထည့် — ကြားညှပ် space သာ · R7)。
    STAT["cps_med"] = round(cps_med, 1); STAT["merged"] = 0
    res, i = [], 0
    while i < len(out):
        cur = dict(out[i])
        while i + 1 < len(out):
            nxt = out[i + 1]
            if cur["end"] <= nxt["start"] + 1e-9: break      # ထပ်မနေ
            d = nxt["start"] - cur["start"]
            hot = (cps_x and cps_med and
                   (d <= 0 or len(cur["text"]) / d > cps_med * cps_x))
            if not hot:
                cur["end"] = nxt["start"]; break             # clamp လုံလောက်
            t1, t2 = cur["text"], nxt["text"]
            join = " " if (t1 and t2 and not t1.endswith(" ")
                           and not t2.startswith(" ")) else ""
            cur["text"] = t1 + join + t2
            cur["end"]  = max(cur["end"], nxt["end"])
            STAT["merged"] += 1
            i += 1
        res.append(cur); i += 1
    for i in range(len(res) - 1):
        if res[i + 1]["start"] <= res[i]["start"]:
            res[i + 1]["start"] = round(res[i]["start"] + 0.01, 2)
        if res[i]["end"] > res[i + 1]["start"]:
            res[i]["end"] = res[i + 1]["start"]
        if res[i]["end"] <= res[i]["start"]:
            res[i]["end"] = round(res[i]["start"] + 0.01, 2)
    if res and res[-1]["end"] <= res[-1]["start"]:
        res[-1]["end"] = round(res[-1]["start"] + 0.01, 2)
    return res


def japanese(wav, log=print):
    """ဂျပန်/အင်္ဂလိပ် — whisper.cpp (realtime ၄.၈၈ ဆ · တိုင်းပြီး)"""
    mdl = os.path.expanduser("~/.cache/whisper/ggml-large-v3-turbo.bin")
    if not os.path.exists(mdl): log("  ⚠️ whisper model မရှိ"); return []
    js = wav + ".json"
    subprocess.run(["whisper-cli","-m",mdl,"-f",wav,"-oj","-of",wav,"-np","-nt"],
                   capture_output=True, text=True)
    if not os.path.exists(js): return []
    try:
        d=json.load(open(js,encoding="utf-8",errors="replace"))
        segs=[dict(text=s["text"].strip(),
                   start=_ts(s["offsets"]["from"]), end=_ts(s["offsets"]["to"]))
              for s in d.get("transcription",[]) if s.get("text","").strip()]
    except Exception as e:
        log(f"  ⚠️ whisper JSON: {e}"); segs=[]
    os.remove(js)
    return segs

def _ts(ms): return round(ms/1000.0, 2)

def run(wav, lang="my", log=print, meas=None, align_cfg=None):
    return (burmese(wav, log, meas=meas, align_cfg=align_cfg)
            if lang == "my" else japanese(wav, log))
