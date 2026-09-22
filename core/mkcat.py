# -*- coding: utf-8 -*-
"""Motion Kit → IKKI **curated catalog** (၂၀၂၆-၀၉-၂၁ Zin)。

⚠️ **localhost:8765 ကို သုံးစွဲသူ ဆီ ဘယ်တော့မှ မပြရ** — အဲဒါက ကိုယ်ပိုင်
   development gallery ဖြစ်ပြီး ဖောက်သည် UI မဟုတ်။ CORS · deploy ·
   availability သုံးခုလုံး ပြဿနာ ဖြစ်မည်။
⚠️ motionkit runtime က **worker စက်ထဲမှာသာ** ရှိသည် (Mac)。 API က VPS
   container ထဲ ⇒ တိုက်ရိုက် ဖတ်လို့ **မရ**。 ⇒ worker က ဤ module နဲ့
   **sanitized snapshot** ဆောက်ပြီး API ဆီ တင်သည်、API က ပြန်ဖြန့်သည်。
⚠️ **filesystem path တစ်ခုမှ မထုတ်ရ** — id · နာမည် · အမျိုးအစား · slot
   အချက်အလက်သာ။
⚠️ template ၄၇၉ ခု အားလုံး **မထုတ်ပါ** — `assets/gfx_ok.txt` (တကယ် render
   ပြီး စစ်ထားသော ၂၇၂) ကိုသာ။ 「၄၇၉ စာရင်း」က သုံးစွဲသူကို ကြောက်စေသည်။
"""
import json, os

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OK_PATH = os.path.join(_R, "assets", "gfx_ok.txt")

# ── လူ ဖတ်နိုင်သော အုပ်စု ၅ ခု (Zin ရဲ့ §4) ──
CATS = (
    ("text",    "Text motion",             "စာလုံး လှုပ်ရှားမှု"),
    ("info",    "Infographics",            "အချက်အလက် ပုံ"),
    ("screen",  "Screen / App",            "ဖန်သားပြင် · app"),
    ("compare", "Comparison / Checklist",  "နှိုင်းယှဉ် · စစ်စာရင်း"),
    ("cta",     "CTA / Branding",          "CTA · ဘရန်း"),
)
CAT_IDS = tuple(c[0] for c in CATS)

# ⚠️ **သုံးစွဲသူ ရွေးရန် စာရင်းက AI ရဲ့ pool ထက် ကျယ်သည်**。 `gfxcat.USE`
#    (AI အလိုအလျောက် ရွေးသော အုပ်စု) ထဲ `mockup` မပါပါ — ဟုတ်ပါသည်:
#    ဖန်သားပြင် overlay ကို စကားနဲ့ မကိုက်ဘဲ တင်လျှင် အဆိုးဆုံး。
#    ဒါပေမယ့် သုံးစွဲသူက 「ဒီနေရာက app ပြတဲ့ အပိုင်း」ဆိုပြီး **ကိုယ်တိုင်
#    ရွေး**လျှင် တင်သင့်သည် (Zin ရဲ့ safeguard #4: 「true screen/UI
#    moments」)。 ⇒ library မှာ ပြ · AI pool မှာ မထည့်。
PICK_ONLY = ("mockup",)

# ⚠️ id ထဲက စကားလုံးက motionkit ရဲ့ category ထက် **ပိုတိကျ**သည် —
#    `infogfx.compare_bars` က category «infographic» ဖြစ်ပေမယ့် သုံးစွဲသူ
#    အတွက် «နှိုင်းယှဉ်» ဖြစ်သည် ⇒ စကားလုံးကို အရင် စစ်သည်。
_KW = (
    ("compare", ("compare", "versus", "_vs", "vs_", "checklist", "check",
                 "pros", "cons", "tickbox", "table", "matrix", "swot")),
    ("cta",     ("cta", "subscribe", "follow", "endcard", "end_card", "outro",
                 "brand", "logo", "lower_third", "handle", "social")),
    ("screen",  ("mockup", "browser", "phone", "laptop", "desktop", "app_",
                 "screen", "window", "ui_", "device", "tablet")),
    ("info",    ("chart", "graph", "infogfx", "bar", "pie", "donut", "stat",
                 "ring", "gauge", "funnel", "pyramid", "map", "dash",
                 "timeline", "percent")),
)
# ⚠️ စကားလုံး မတွေ့လျှင် motionkit ရဲ့ category ကနေ
_BY_CAT = {"infographic": "info", "chart": "info", "mockup": "screen",
           "text": "text", "typography": "text", "title": "text",
           "motion": "text", "callout": "text", "explainer": "info",
           "transition": "text"}


def group_of(tid, category=""):
    """template id → လူ ဖတ်နိုင်သော အုပ်စု。"""
    low = (tid or "").lower()
    for g, words in _KW:
        if any(w in low for w in words): return g
    return _BY_CAT.get((category or "").lower(), "text")


def _name(e):
    """ပြရန် နာမည် — raw fn နာမည် (`compare_bars`) ကို လူဖတ်နိုင်အောင်。"""
    for k in ("label_en", "label", "fn"):
        v = (e.get(k) or "").strip()
        if v and v != e.get("fn"): return v
    v = (e.get("fn") or e.get("id") or "").replace("_", " ").strip()
    return v[:1].upper() + v[1:] if v else "(မသိ)"


def verified():
    """`assets/gfx_ok.txt` — တကယ် render ပြီး စစ်ထားသော id များ。"""
    try:
        with open(OK_PATH, encoding="utf-8") as f:
            return {x.strip() for x in f
                    if x.strip() and not x.lstrip().startswith("#")}
    except OSError:
        return set()


def _slots(e):
    """param schema — **သုံးစွဲသူ ဖြည့်ရမည့်** slot များသာ (path မထုတ်ပါ)。"""
    out = []
    for p in (e.get("params") or []):
        nm = str((p or {}).get("name") or "")
        if not nm or nm.startswith("_"): continue
        ty = str(p.get("type") or "")
        # ⚠️ ဖိုင် slot က သုံးစွဲသူ ရွေးစရာ မဟုတ် (asset က AI စီမံ)
        if ty in ("file", "path", "image"): continue
        out.append(dict(name=nm, type=ty, req=bool(p.get("required"))))
        if len(out) >= 8: break
    return out


def build(fmt="16:9", log=None):
    """sanitized catalog — `{ok, n, total, fmt, cats, items}`。

    ⚠️ motionkit ဖတ်မရလျှင် **တိတ်တဆိတ် မကျော်ရ** — `ok=False` နဲ့
       အကြောင်းရင်း ပါရမည် (UI က 「ယခု မရနိုင်」ပြရန်)。
    """
    import gfxcat as G
    cat = G.catalog()
    if not cat:
        return dict(ok=False, n=0, total=0, fmt=fmt, cats=[], items=[],
                    why=(G.LAST_ERR[0] or "motionkit catalog ဗလာ"))
    ok = verified()
    items = []
    for e in cat:
        tid = e.get("id")
        if not tid or tid not in ok: continue
        # ⚠️ overlay အဖြစ် သုံးလို့ရမှသာ (`usable()` ရဲ့ စည်းကမ်း)
        if e.get("category") not in (tuple(G.USE) + PICK_ONLY): continue
        items.append(dict(
            id=tid, name=_name(e), cat=group_of(tid, e.get("category")),
            shape=G.shape_of(tid) or "", slots=_slots(e),
            role=G.role_of(e)))
    items.sort(key=lambda x: (x["cat"], x["name"]))
    if log:
        from collections import Counter
        log(f"  Motion Kit catalog · စစ်ပြီး {len(items)}/{len(cat)} · "
            + " · ".join(f"{k} {v}" for k, v in
                         sorted(Counter(i['cat'] for i in items).items())))
    return dict(ok=True, n=len(items), total=len(cat), fmt=fmt,
                cats=[dict(id=a, en=b, my=c) for a, b, c in CATS],
                items=items)


def preflight(tid, fmt="16:9"):
    """သုံးစွဲသူ ရွေးလိုက်သော template ကို **ကြိုစစ်**သည် → (ok, why)。

    ⚠️ ကျဘမ်းလျှင် **job တစ်ခုလုံး မကျရ** — AI ရွေးချက်ဆီ ပြန်ဆုတ်ပြီး
       report မှာ မှတ်ရမည် (Zin ရဲ့ quality gate #2)。
    """
    import gfxcat as G
    if not tid: return False, "id မပါ"
    if tid not in verified():
        return False, "စစ်ပြီးသား စာရင်းထဲ မပါ"
    e = next((x for x in G.catalog() if x.get("id") == tid), None)
    if not e: return False, "catalog ထဲ မတွေ့"
    if e.get("category") not in (tuple(G.USE) + PICK_ONLY):
        return False, f"overlay အဖြစ် မသုံးနိုင် ({e.get('category')})"
    return True, ""
