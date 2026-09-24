# -*- coding: utf-8 -*-
"""**ဖြတ်ပြောင်း (cutaway)** ဝါယာကြိုး ပြုတ်မသွားရန် ဂိတ်。

⚠️ ၂၀၂၆-၀၉-၂၄ တိုင်းချက် — reference ၂ ပုဒ်လုံးမှာ ဖြတ်ပြောင်း **ပေါ်ချိန်
   ၁၅.၁–၁၅.၂%** (နှုန်း ၁.၀၀ ↔ ၁.၅၁/min · အလယ် ၇.၅ ↔ ၅.၂s ကွဲသော်လည်း
   **ပေါ်ချိန် တည်ငြိမ်**) ⇒ ဂိတ်က ပေါ်ချိန် ဖြစ်ရမည်、နှုန်း မဟုတ်。
⚠️ ပြုတ်ခဲ့သော အချက် ၄ ချက်ကို တစ်ခုချင်း ဖမ်းသည် —
     ① `_ff_max` က ဗီဒီယိုတစ်ပုဒ်လျှင် **၁ ခုသာ** ခဲ့ (`_ff_used` boolean)
     ② ဘတ်ဂျက် လွတ်နေလျှင် ဘောင်အပြည့်ကို **ရှေ့တန်း မတင်**ခဲ့ ⇒ ၄၈ ခုမှာ
        ၃ ခု မဲပေါက်ခဲ ⇒ ၇၈၀s ဗီဒီယိုမှာ တကယ် ထွက်တာ **၁ ခု**
     ③ catalog လမ်းကြောင်းမှာ ဘတ်ဂျက် **မစစ်**ခဲ့
     ④ `_fullstage_ids()` က `gfx_fullstage.txt` (bbox ⇒ အလှဆင်တွေပါ)
        ဖတ်မိခဲ့ — **`gfx_cutaway.txt`** (alpha အလယ်မှတ် တိုင်းချက်) သာ မှန်
⚠️ ဤ test က Gemini **မခေါ်ရ** — `build()` ကို label ကိုယ်တိုင် ပေးပြီး ခေါ်သည်。
"""
import os, sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, "core"))

OK = FAIL = 0


def ck(name, cond, extra=""):
    global OK, FAIL
    if cond:
        OK += 1
    else:
        FAIL += 1
        print(f"  ✗ {name}  {extra}")


import planner as PL

# ── ④ တိုင်းပြီးသော စာရင်းကိုသာ ဖတ်ရမည် ──────────────────────────
src = open(os.path.join(R, "core", "planner.py"), encoding="utf-8").read()
# ⚠️ **မှတ်ချက်နဲ့ docstring ကို ဖယ်ရမည်** — ယခင် ချွတ်ယွင်းချက်ကို မှတ်ချက်
#    အဖြစ် ရေးမှတ်ထားသဖြင့် `"_ff_used" not in src` က မှားကျသည်;
#    `gfx_fullstage.txt` ကို 「မသုံးရ」ဟု docstring မှာ ရေးထားသဖြင့်လည်း
#    မှားကျသည် (၂၀၂၆-၀၉-၂၄ ၂ ခါ)。 ⇒ AST နဲ့ **တကယ့်ကုဒ်**ကိုသာ ယူသည်。
import ast as _ast

_tree = _ast.parse(src)
_doc = set()
for _nd in _ast.walk(_tree):
    if isinstance(_nd, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef,
                        _ast.ClassDef)) and _ast.get_docstring(_nd) is not None:
        _b = _nd.body[0]
        _doc.add(id(_b.value))
_lit = [_nd.value for _nd in _ast.walk(_tree)
        if isinstance(_nd, _ast.Constant) and isinstance(_nd.value, str)
        and id(_nd) not in _doc]
_names = [_nd.id for _nd in _ast.walk(_tree) if isinstance(_nd, _ast.Name)]
_attrs = [_nd.attr for _nd in _ast.walk(_tree) if isinstance(_nd, _ast.Attribute)]
code = "\n".join(_lit + _names + _attrs + [
    l for l in src.splitlines()
    if not l.lstrip().startswith("#")])
ck("gfx_cutaway.txt ကို ဖတ်သည်", "gfx_cutaway.txt" in _lit)
ck("gfx_fullstage.txt ကို မဖတ်ရ (bbox ⇒ မယုံရ)",
   "gfx_fullstage.txt" not in _lit)

# ── ① ဘတ်ဂျက်က ကြာချိန်နဲ့ အတူ တိုးရမည် ─────────────────────────
ck("`_ff_used` boolean ပြန်မလာရ", "_ff_used" not in code)
ck("ဘတ်ဂျက် ကိန်း ရှိ", "_FF_COVER" in code and "_ff_max" in code)
ck("ပေါ်ချိန် ပန်းတိုင် ၁၅%", "_FF_COVER, _FF_LEN, _FF_MAXLEN = 0.15" in code)

# ── ② ရှေ့တန်း တင်ခြင်း + ③ လမ်းကြောင်း ၃ ခုလုံး ────────────────
ck("ဘောင်အပြည့်ကို ရှေ့တန်း တင်သည် (`_ff_order`)", "_ff_order" in code)
ck("`_ff_order` ကို လမ်းကြောင်း ၃ ခုလုံးမှာ သုံးသည်",
   code.count("_ff_order(") >= 4, f"တွေ့သည် {code.count('_ff_order(')} ကြိမ်")
ck("အချိန် အညီအမျှ ခြားသည် (`_ff_gap`)", "_ff_gap" in code and "_ff_last" in code)

# ── ရေတွက်ခြင်းက **တစ်နေရာတည်း** ဖြစ်ရမည် ───────────────────────
ck("`_ff_n += 1` တစ်နေရာတည်း", code.count("_ff_n += 1") == 1,
   f"တွေ့သည် {code.count('_ff_n += 1')} နေရာ")

# ── တကယ် ထုတ်ကြည့် — ကြာချိန် တိုးလျှင် အရေအတွက် တိုးရမည် ─────────
TXT = ["ဒီနေ့ ကျွန်တော် ပြောပြမယ် ဂျပန်မှာ အလုပ်ရှာနည်း အကြောင်းပါ",
       "ပထမဆုံး အချက်က ဘာသာစကား ဖြစ်ပါတယ် N4 အဆင့် လိုအပ်ပါတယ်",
       "လူ ၈၅% က ဒီအချက်ကို လွဲသွားတယ် ဆိုတာ သုတေသနက ပြပါတယ်",
       "အရေးကြီးတာက သင်တန်း ရွေးချယ်မှု ပါ သတိထားပါ",
       "ဒုတိယ အချက် — ငွေကြေး စီမံခန့်ခွဲမှု ဖြစ်ပါတယ်",
       "နောက်ဆုံး အနေနဲ့ ကျွန်တော့် အတွေ့အကြုံ မျှဝေပါမယ်"]
LAB = ["hook", "section", "number", "warning", "section", "section"]


def run(dur):
    segs, labs, t = [], [], 0.0
    while t < dur - 8:
        for s, l in zip(TXT, LAB):
            if t >= dur - 8:
                break
            segs.append(dict(start=round(t, 2), end=round(t + 7.0, 2), text=s))
            labs.append(l)
            t += 7.2
    p = PL.build(segs, labs, float(dur),
                 dict(profile="premium", sfx_on=True), video_id="tst")
    ev = [e for e in p["templateEvents"]
          if (e.get("style") or {}).get("layout") == "full"]
    cov = sum(float(e["endTime"]) - float(e["startTime"]) for e in ev)
    return len(ev), cov / dur


n60, c60 = run(60)
n600, c600 = run(600)
ck("ကြာချိန် ၁၀ ဆ ⇒ ဖြတ်ပြောင်း တိုးရမည်", n600 > n60, f"၆၀s:{n60} ၆၀၀s:{n600}")
ck("၆၀၀s မှာ ဖြတ်ပြောင်း ≥ ၄ ခု", n600 >= 4, f"တွေ့သည် {n600}")
# ⚠️ **ကျော်တာက လျော့တာထက် ဆိုးသည်** — ဖုံးလွန်လျှင် ပြောသူနဲ့ ပြတ်သည်
ck("ပေါ်ချိန် ၁၈% မကျော်ရ", c600 <= 0.18, f"တွေ့သည် {c600*100:.1f}%")
ck("ပေါ်ချိန် ၅% အထက်", c600 > 0.05, f"တွေ့သည် {c600*100:.1f}%")

# ── စုပုံမနေရ — ကွာဟချက် တစ်ပြေးညီနီးပါး ───────────────────────
segs, labs, t = [], [], 0.0
while t < 592:
    for s, l in zip(TXT, LAB):
        if t >= 592:
            break
        segs.append(dict(start=round(t, 2), end=round(t + 7.0, 2), text=s))
        labs.append(l); t += 7.2
p = PL.build(segs, labs, 600.0, dict(profile="premium"), video_id="tst")
at = sorted(float(e["startTime"]) for e in p["templateEvents"]
            if (e.get("style") or {}).get("layout") == "full")
if len(at) >= 3:
    g = [at[i + 1] - at[i] for i in range(len(at) - 1)]
    ck("ဖြတ်ပြောင်းများ စုပုံမနေ (အတိုဆုံး ကွာဟ ≥ ၂၀s)", min(g) >= 20.0,
       f"အတိုဆုံး {min(g):.0f}s")
else:
    ck("ကွာဟ စစ်ရန် ≥၃ ခု လို", False, f"တွေ့သည် {len(at)}")

# ══ worker — ဖြတ်ပြောင်း တစ်ခုစီ မဆောက်ခင် cache ရှင်းရမည် ══════════
# ⚠️ `dress.slide_clip()` က ဖြတ်ပြောင်း အားလုံးကို **tag `"sl"` တစ်ခုတည်း**နဲ့
#    ခေါ်သဖြင့် template ရဲ့ ဖရိမ်း ဖိုင်နဲ့ `prem._CROP` စသော cache တွေက
#    မျှသွားပြီး **ဒုတိယကနေစပြီး ပထမတစ်ခုရဲ့ စာ ပြန်ပေါ်**သည်。
#    ၂၀၂၆-၀၉-၂၄ တိုင်းချက် — ဖြတ်ပြောင်း ၃၀ ခုမှာ **၁၃ ခု** ဖရိမ်း ၆၀/၆၀ တူ;
#    process သီးသန့်မှာ ၅/၅ ကွဲ ⇒ cache ကြောင့်; ရှင်းပြီးနောက် ၅/၅ ကွဲ。
# ⚠️ ယခင်က ဘောင်အပြည့် ၁ ခုသာ ခွင့်ပြုခဲ့သဖြင့် **တစ်ခါမှ မဖြစ်ခဲ့**ပါ —
#    ဤ test က ဖြတ်ပြောင်း များလာသောအခါ ပြန်ပေါ်လာမှုကို ဖမ်းသည်。
import ast as _a2

wsrc = open(os.path.join(R, "worker", "run.py"), encoding="utf-8").read()
ck("worker မှာ cache ရှင်းချက် ရှိ", "_mk_cache_clear" in wsrc)
_wt = _a2.parse(wsrc)
_calls = [n for n in _a2.walk(_wt)
          if isinstance(n, _a2.Call) and isinstance(n.func, _a2.Name)
          and n.func.id == "_mk_cache_clear"]
ck("cache ရှင်းချက်ကို တကယ် ခေါ်သည်", len(_calls) >= 1,
   f"တွေ့သည် {len(_calls)} ကြိမ်")
# ⚠️ `slide_clip` ခေါ်သည့် **အထက်**မှာ ရှိရမည် — အောက်မှာ ဆိုလျှင် အကျိုးမရှိ
_sc = [n.lineno for n in _a2.walk(_wt)
       if isinstance(n, _a2.Call)
       and isinstance(n.func, _a2.Attribute) and n.func.attr == "slide_clip"]
ck("ဖြတ်ပြောင်း ဆောက်ခြင်းရဲ့ အထက်မှာ ခေါ်သည်",
   bool(_sc) and any(c.lineno < max(_sc) for c in _calls),
   f"ရှင်း@{[c.lineno for c in _calls]} · slide_clip@{_sc}")
# ⚠️ helper module အားလုံး ပါရမည် — `prem3`/`prem4`/`insert` မှာ ကိုယ်ပိုင်
#    cache မရှိဘဲ `prem`/`inkbox` ကနေ ယူသည်
for _need in ("_CROP", "inkbox", "cttext_rsvg"):
    ck(f"cache စာရင်းမှာ `{_need}` ပါ", _need in wsrc)

print(f"\n  ဖြတ်ပြောင်း ၆၀s:{n60} · ၆၀၀s:{n600} ({c600*100:.1f}%) "
      f"⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
