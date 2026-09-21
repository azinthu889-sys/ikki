"""Motion Kit pack — contract ဖတ်ခြင်းနှင့် စစ်ဆေးခြင်း。

⚠️ spec §5 — 「No planner may select a template until its manifest is valid
   and its preview-render test passes」⇒ `pack.json` ရဲ့ `templates` ထဲ
   **verify ပြီးသား** ID သာ ပါရမည်。

⚠️ ရှိပြီးသား `motionkit` ရဲ့ manifest မှာ contract field **၇ ခုလုံး မရှိ**ပါ
   (`intent` · `aspects` · `duration` · `safeZones` · `audioAffordances` ·
   `render` · `version` — ၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。 ⇒ pack က အဲဒီအချက်တွေကို
   **အပေါ်ကနေ ဖြည့်**ပေးသည်、ရှိပြီးသား template တွေကို မထိပါ (adapter)。
"""
import json
import os

REQUIRED = ("id", "version", "intent", "aspects", "duration",
            "safeZones", "props", "render")


def _mk():
    try:
        import gfxcat as GC
    except ImportError:
        from core import gfxcat as GC
    return GC.MK


def path(pack="headtop-premium"):
    return os.path.join(_mk(), "packs", pack)


def load(pack="headtop-premium"):
    """`(pack, tokens)` — မရှိလျှင် `(None, None)`"""
    d = path(pack)
    try:
        with open(os.path.join(d, "pack.json"), encoding="utf-8") as f:
            p = json.load(f)
        with open(os.path.join(d, p.get("tokens") or "tokens.json"),
                  encoding="utf-8") as f:
            t = json.load(f)
        return p, t
    except (OSError, ValueError):
        return None, None


def tok(tokens, *keys, default=None):
    """token တစ်ခု ယူသည် — `{"v": …, "src": …}` ပုံစံကို ဖြေပေးသည်

    ⚠️ `src` က **ကိန်းရဲ့ အရင်းအမြစ်** — 'measured' မဟုတ်လျှင်
       တိုင်းပြီးသားလို မပြောရ。
    """
    cur = tokens or {}
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    if isinstance(cur, dict) and "v" in cur:
        return cur["v"]
    return cur


def src(tokens, *keys):
    """token ရဲ့ အရင်းအမြစ် — `measured` / `spec` / `brand` / None

    ⚠️ token တစ်ခုချင်းမှာ `src` မရှိလျှင် **အုပ်စုရဲ့ `src`** ကို ယူသည်
       (`motion` လို အုပ်စုလိုက် သတ်မှတ်ထားတာမျိုး)。 မဟုတ်လျှင်
       「မသိ」ဟု ပြမိပြီး တိုင်းပြီးသားလို ထင်စရာ ဖြစ်မည်。
    """
    cur = tokens or {}
    grp = None
    for k in keys:
        if isinstance(cur, dict) and isinstance(cur.get("src"), str):
            grp = cur["src"]
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    if isinstance(cur, dict) and isinstance(cur.get("src"), str):
        return cur["src"]
    return grp


def check_manifest(m):
    """template manifest တစ်ခု စစ်သည် — ချိုးဖောက်ချက် စာရင်း ပြန်ပေးသည်"""
    bad = []
    for k in REQUIRED:
        if k not in (m or {}):
            bad.append(f"`{k}` မပါ")
    if not m:
        return bad
    a = m.get("aspects") or []
    if not isinstance(a, list) or not a:
        bad.append("`aspects` ဗလာ")
    d = m.get("duration") or {}
    if not all(x in d for x in ("min", "preferred", "max")):
        bad.append("`duration` မပြည့်စုံ (min/preferred/max)")
    elif not (d["min"] <= d["preferred"] <= d["max"]):
        bad.append(f"`duration` အစဉ် မမှန် ({d['min']}/{d['preferred']}/{d['max']})")
    r = m.get("render") or {}
    if "alpha" not in r:
        bad.append("`render.alpha` မပါ")
    if not (r.get("fps") or []):
        bad.append("`render.fps` ဗလာ")
    for pn, pv in (m.get("props") or {}).items():
        if not isinstance(pv, dict) or "type" not in pv:
            bad.append(f"prop `{pn}` — `type` မပါ")
    return bad


def selectable(pack="headtop-premium"):
    """planner ရွေးခွင့်ရှိသော template ID များ — **verify ပြီးသားသာ**

    ⚠️ ဗလာ ပြန်လျှင် **အမှား မဟုတ်**ပါ — template မဆောက်ရသေးခြင်း。
       ခေါ်သူက ရှိပြီးသား လမ်းကြောင်းကို ဆက်သုံးရမည် (adapter)。
    """
    p, _ = load(pack)
    out = []
    for m in (p or {}).get("templates") or []:
        # ⚠️ **manifest မမှန်လျှင် ရွေးခွင့် မပေးရ** (spec §5) —
        #    pack.json ထဲ ရှိရုံနဲ့ မလုံလောက်ပါ。
        if isinstance(m, dict) and not check_manifest(m):
            out.append(m["id"])
    return out


def template(tid, pack="headtop-premium"):
    """manifest တစ်ခု — မရှိ/မမှန်လျှင် None"""
    p, _ = load(pack)
    for m in (p or {}).get("templates") or []:
        if isinstance(m, dict) and m.get("id") == tid and not check_manifest(m):
            return m
    return None


def by_intent(intent, pack="headtop-premium"):
    """`intent` နဲ့ ကိုက်သော template ID များ — planner က ဒီကနေ ရွေးရမည်

    ⚠️ planner က **ဖိုင်နာမည် မရွေးရ**、intent သာ ပြောရမည် (spec §12)。
    """
    p, _ = load(pack)
    out = []
    for m in (p or {}).get("templates") or []:
        if not isinstance(m, dict) or check_manifest(m):
            continue
        if intent in (m.get("intent") or []):
            out.append(m["id"])
    return out
