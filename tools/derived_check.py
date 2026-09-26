#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**တွက်ထုတ်ထားသော (derived) ဖိုင်များ ဟောင်းနေလား** — content hash နဲ့ တိုင်းသည်။

ဘာကြောင့် ရှိရသလဲ
─────────────────
၂၀၂၆-၀၉-၂၅ မှာ `thm.py` ကို ၁၅ နေရာ ပြင်ပြီးနောက် 「ဂိတ် ၆၁၆/၆၁၆ အောင်」 ဟု
တင်ပြခဲ့သည် — ဒါပေမယ့် `gfx_verify.json` က **၉.၇ နာရီ ဟောင်း**ခဲ့ပြီး
ပြင်ပြီးသား ၈ ခုကိုသာ ပြန်စစ်ခဲ့သည်။ ကုဒ်က သတိမပေးသဖြင့် တိတ်တဆိတ်
ဟောင်းနေတဲ့ ကိန်းကနေ အဖြေ ထုတ်ခဲ့ခြင်း ဖြစ်သည်။

စည်းမျဉ်း (Zin သတ်မှတ်)
───────────────────────
S-a · **fail-closed** — provenance မပါလျှင် 「ဟောင်း」ဟု သတ်မှတ်ရမည်။
      「မသိလို့ ကောင်းတယ်ဟု ယူဆ」 မလုပ်ရ။
S-b · render နဲ့ တိုင်းချက် မတူ —
        production render : သတိပေး · ဆက်သွား  (`--warn`)
        ဂိတ် · တိုင်းချက်  : ⛔ ငြင်းပယ်ရမည် · ကိန်း မထုတ်ရ  (`--gate`)
S-c · **ကိုယ့်ဘာသာ ပြန်မထုတ်ရ** — သတိပေးရုံ။ render အလယ်မှာ auto-regenerate
      လုပ်လျှင် မမျှော်လင့်တဲ့ ဘေးထွက်ဆိုးကျိုး ဖြစ်မည်။
P1  · **mtime မဟုတ်ဘဲ content hash** — `git checkout`/`touch` က mtime ကို
      အကြောင်းအရာ မပြောင်းဘဲ ပြောင်းသည်; တစ်စက္ကန့်အတွင်း ပြင်ချက် ၂ ခုကို
      ခွဲလို့ မရ။ ⇒ mtime က **မြန်သော ရှေ့စစ်ချက်**သာ · hash က အဆုံးအဖြတ်။
P2  · **ပြန်စစ်ရမယ့် template စာရင်း** ထုတ်ပေးရမည် (`--stale-list`) —
      ဒီ tool ရဲ့ တကယ့် တန်ဖိုးက သတိပေးတာ မဟုတ်၊ **ဘာ ပြန်လုပ်ရမလဲ**
      တိတိကျကျ ပြောတာ။ ၅.၅ နာရီ ⇒ မိနစ်ပိုင်း။

အသေးစိတ် — unit အလိုက် hash
──────────────────────────
⚠️ ဖိုင်တစ်ခုလုံး hash နဲ့ တိုင်းလျှင် `thm.py` တစ်ကြောင်း ပြင်ရုံနဲ့ template
   ၁၃၇ ခုလုံး ဟောင်းသွားမည် — ပြန်စစ်ချိန် ၄၅ မိနစ်။ တကယ်တော့ ပြင်ခဲ့တာ
   ၁၅ ခုသာ။ ⇒ module ကို **unit** အလိုက် ခွဲသည်:
     · template unit  — `def name(` (underscore မပါ)
     · helper unit    — `def _name(`
     · shell          — def ပြင်ပ အားလုံး (import · ကိန်းသေ · BUILDERS)
   template ရဲ့ hash = ကိုယ့် source + **ခေါ်သော helper များ (ဆက်တိုက်)** +
   shell ရဲ့ hash။ ⇒ helper ပြောင်းလျှင် ခေါ်သူများသာ ဟောင်းသည်; shell
   ပြောင်းလျှင် အားလုံး (ကိန်းသေက အားလုံးကို ထိသဖြင့် မှန်သည်)。
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MK = os.environ.get(
    "IKKI_MOTIONKIT",
    "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")

# ══ derived ဖိုင် မှတ်ပုံတင် ═══════════════════════════════════════
# name → dict(out=ထွက်ဖိုင်, by=ထုတ်သော tool, tools=[ကုဒ် တွဲဖက်], per_template=bool)
# ⚠️ ဖိုင် အသစ် ထုတ်တိုင်း **ဒီမှာ ထည့်ရမည်** — မထည့်လျှင် ဟောင်းနေတာ
#    မမြင်ဘဲ ကျော်မည် (S-a က ဖိုင်ကို သိမှ အလုပ်လုပ်သည်)。
REG = {
    "gfx_verify": dict(
        out="assets/gfx_verify.json", by="tools/gfx_verify.py",
        tools=["tools/gfx_verify.py", "core/gfxcat.py", "core/dress.py"],
        per_template=True),
    "gfx_textsens": dict(
        out="assets/gfx_textsens.json", by="tools/gfxtextsens.py",
        tools=["tools/gfxtextsens.py", "core/gfxcat.py", "core/dress.py"],
        per_template=True),
    "gfx_args": dict(
        out="assets/gfx_args.json", by="tools/gfx_args.py",
        tools=["tools/gfx_args.py", "core/gfxcat.py"], per_template=True,
        # ⚠️ `gfx_args` က **စာရင်း param ရှိသူ**များကိုသာ ထိသည် — ကျန်တာကို
        #    「ဟောင်း」ဟု တောင်းလျှင် ဂိတ် ဘယ်တော့မှ မပွင့် (trans ၂၄ ခု …)。
        scope="listy"),
    "gfx_size_16x9": dict(
        out="assets/gfx_size_16x9.json", by="tools/gfxsize.py",
        tools=[], per_template=True),
    "gfx_qual": dict(
        out="assets/gfx_qual.json", by="tools/gfxqual.py",
        tools=["tools/gfxqual.py"], per_template=True),
    "gfx_cutaway": dict(
        out="assets/gfx_cutaway.json", by="tools/gfx_cutaway.py",
        tools=[], per_template=True),
    "gfx_ok": dict(
        out="assets/gfx_ok.txt", by="tools/gfx_gate.py",
        tools=["tools/gfx_gate.py"], per_template=False,
        derives_from=["gfx_verify", "gfx_textsens"]),
    "thm_timing": dict(
        out=os.path.join(MK, "thm_timing.json"), by="thm_calib.py",
        tools=[os.path.join(MK, "thm_calib.py")], per_template=True,
        only_module="thm"),
    "thm_manifest": dict(
        out=os.path.join(MK, "manifests", "thm.json"), by="thm_manifest.py",
        tools=[os.path.join(MK, "thm_manifest.py"), os.path.join(MK, "render2.py"),
               os.path.join(MK, "fade.py")],
        per_template=True, only_module="thm",
        derives_from=["thm_timing"]),
}

# ⚠️ template module **မဟုတ်**သော motionkit ဖိုင်များ — unit ခွဲစရာ မလို
NOT_TEMPLATE = {
    "catalog.py", "stylemap.py", "theme.py", "demoargs.py", "argshape.py",
    "fade.py", "render.py", "render2.py", "thm_manifest.py", "thm_calib.py",
    "thm_preview.py", "kit.py", "mkbase.py", "tmplfit.py", "presets.py",
}


def _h(b):
    return hashlib.sha256(b).hexdigest()[:16]


def _fh(p):
    """ဖိုင် content hash — မရှိလျှင် None。"""
    try:
        with open(p, "rb") as f:
            return _h(f.read())
    except OSError:
        return None


def _mt(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return None


# ══ module ကို unit အလိုက် ခွဲခြင်း ═══════════════════════════════
_DEF = re.compile(r"^def\s+(\w+)\s*\(", re.M)


def units(src):
    """`(shell_hash, {name: (own_src, [ခေါ်သော name])})`。"""
    marks = [(m.start(), m.group(1)) for m in _DEF.finditer(src)]
    shell_parts = []
    out = {}
    prev = 0
    for i, (pos, name) in enumerate(marks):
        shell_parts.append(src[prev:pos])
        end = marks[i + 1][0] if i + 1 < len(marks) else len(src)
        out[name] = src[pos:end]
        prev = end
    shell_parts.append(src[prev:])
    names = set(out)
    calls = {}
    for name, body in out.items():
        # ⚠️ ကိုယ့်နာမည် မပါစေရ (recursion က dependency မဟုတ်)
        used = {n for n in names if n != name and re.search(r"\b%s\s*\(" % re.escape(n), body)}
        calls[name] = sorted(used)
    return _h("".join(shell_parts).encode()), {n: (out[n], calls[n]) for n in out}


def unit_hashes(path):
    """`{template_name: hash}` — helper ဆက်တိုက် + shell ပါဝင်သည်。"""
    try:
        src = open(path, encoding="utf-8").read()
    except OSError:
        return {}
    shell, u = units(src)
    memo = {}

    def h_of(name, seen):
        if name in memo:
            return memo[name]
        if name in seen:                      # ⚠️ စက်ဝိုင်း — ကိုယ့် source သာ
            return _h(u[name][0].encode())
        seen = seen | {name}
        own, calls = u[name]
        parts = [own] + [h_of(c, seen) for c in calls if c in u]
        v = _h(("".join(parts) + shell).encode())
        memo[name] = v
        return v

    return {n: h_of(n, frozenset()) for n in u if not n.startswith("_")}


_CATIDS = None


def catalog_ids():
    """**တကယ့် template id အစု** — `catalog.build()` (BUILDERS) က အဆုံးအဖြတ်。

    ⚠️ module ရဲ့ public `def` အားလုံးက template မဟုတ်ပါ — `aurora` · `pieces`
       · `txt` · `ll2xy` တို့က helper (underscore မပါသော်လည်း)。 အဲဒါတွေ
       ထည့်မိလျှင် stale စာရင်းက **၉၄၅** ထွက်ပြီး template က ၆၁၆ သာ
       (၂၀၂၆-၀၉-၂၆ ဖမ်းမိ) ⇒ ပြန်စစ်ရမယ့် အလုပ် ၅၃% ပိုမှန်းမိမည်。
    """
    global _CATIDS
    if _CATIDS is None:
        cwd = os.getcwd()
        try:
            for pth in (os.path.join(HERE, "core"), MK):
                if pth not in sys.path:
                    sys.path.insert(0, pth)
            os.chdir(MK)
            import catalog as _C
            _CATIDS = {e["id"] for e in _C.build()}
        except Exception as e:
            print("  ⚠️ catalog ဖတ်မရ: %s — public def အားလုံး သုံးမည်" % e)
            _CATIDS = set()
        finally:
            try: os.chdir(cwd)
            except Exception: pass
    return _CATIDS


# ⚠️ derived ဖိုင် တစ်ခုချင်းက template **အားလုံး**ကို မထိပါ — scope လိုသည်。
LISTY_NAMES = ("msgs", "results", "tabs", "levels", "stages", "rows", "items",
               "lines", "bullets", "steps", "points", "cols", "labels", "values",
               "data", "pairs", "pins", "fields", "words", "grid", "pts", "cells",
               "parts", "series", "stats", "names", "vals", "kids", "feats",
               "bars", "caps", "segments", "slices")
_SCOPE = {}


def in_scope(spec, tid):
    sc = spec.get("scope")
    if not sc:
        return True
    if sc == "listy":
        if "listy" not in _SCOPE:
            ids = set()
            cwd = os.getcwd()
            try:
                for pth in (os.path.join(HERE, "core"),):
                    if pth not in sys.path: sys.path.insert(0, pth)
                import gfxcat as _G
                for e in _G.catalog():
                    for pm in (e.get("params") or []):
                        if pm.get("type") == "list" or (
                                pm.get("type") == "text"
                                and pm.get("name") in LISTY_NAMES):
                            ids.add(e["id"]); break
            except Exception:
                pass
            finally:
                try: os.chdir(cwd)
                except Exception: pass
            _SCOPE["listy"] = ids
        return tid in _SCOPE["listy"]
    return True


def template_hashes():
    """`{'thm.stat_pct': hash, …}` — **catalog ထဲ ရှိသော id များသာ**。"""
    out = {}
    for fn in sorted(os.listdir(MK)):
        if not fn.endswith(".py") or fn in NOT_TEMPLATE:
            continue
        mod = fn[:-3]
        for name, h in unit_hashes(os.path.join(MK, fn)).items():
            out["%s.%s" % (mod, name)] = h
    ids = catalog_ids()
    if not ids:
        return out
    res = {k: v for k, v in out.items() if k in ids}
    # ⚠️⚠️ **factory closure များ ကျန်ခဲ့သည်** — `trans` ရဲ့ ၂၄ ခုက
    #    `def name(` မဟုတ်ဘဲ factory ကနေ ဆောက်ပြီး `BUILDERS` ထဲ ထည့်ထားသည်
    #    ⇒ source ကနေ unit ခွဲလို့ မရ。 hash မရှိလျှင် **ဘယ်တော့မှ ဟောင်းဟု
    #    မပြ** ⇒ တိတ်တဆိတ် အပေါက် (S-a ချိုးဖောက်)。 ၂၀၂၆-၀၉-၂၆ ဖမ်းမိ:
    #    catalog 616 · unit 592 ⇒ ၂၄ ခု ကျန်。
    #    ⇒ module တစ်ခုလုံးရဲ့ hash ကို သုံးသည် (module ပြောင်းလျှင် ဟောင်း —
    #    ကြားခံ ကျယ်သော်လည်း **မလွတ်**သည်)。
    miss = sorted(ids - set(res))
    for tid in miss:
        mod = tid.split(".", 1)[0]
        mp = os.path.join(MK, mod + ".py")
        h = _fh(mp)
        if h:
            res[tid] = "mod:" + h
    return res


def tool_hashes(spec):
    out = {}
    for t in spec.get("tools") or []:
        p = t if os.path.isabs(t) else os.path.join(HERE, t)
        out[t] = _fh(p)
    return out


# ══ provenance sidecar ════════════════════════════════════════════
def prov_path(spec):
    o = spec["out"]
    o = o if os.path.isabs(o) else os.path.join(HERE, o)
    return o + ".prov.json"


def out_path(spec):
    o = spec["out"]
    return o if os.path.isabs(o) else os.path.join(HERE, o)


def load_prov(spec):
    try:
        return json.load(open(prov_path(spec), encoding="utf-8"))
    except Exception:
        return None


def record(name, ids=None):
    """generate ပြီးနောက် ခေါ်ရမည် — `ids` ပါလျှင် ထိုအတွက်သာ merge。

    ⚠️ S-c — ဒီ function က **ဖိုင် ပြန်မထုတ်**ပါ; provenance သာ မှတ်သည်。
    """
    spec = REG[name]
    op = out_path(spec)
    if not os.path.exists(op):
        print("  ✖ %s မရှိ — provenance မမှတ်ပါ" % spec["out"])
        return 1
    th = template_hashes()
    pv = load_prov(spec) or {}
    pv["of"] = spec["out"]
    pv["by"] = spec["by"]
    pv["at"] = int(os.path.getmtime(op))
    pv["out_hash"] = _fh(op)
    pv["tools"] = tool_hashes(spec)
    pv.setdefault("templates", {})
    only = spec.get("only_module")
    keys = ids if ids else [k for k in th
                           if (not only or k.startswith(only + "."))
                           and in_scope(spec, k)]
    n = 0
    for k in keys:
        if k in th:
            pv["templates"][k] = th[k]; n += 1
    json.dump(pv, open(prov_path(spec), "w"), ensure_ascii=False,
              indent=1, sort_keys=True)
    print("  ✓ %s — template %d မှတ်ပြီး" % (os.path.basename(prov_path(spec)), n))
    return 0


# ══ စစ်ဆေးခြင်း ═══════════════════════════════════════════════════
def check(name):
    """`dict(status, stale_ids, why)` — status: ok | stale | missing。"""
    spec = REG[name]
    op = out_path(spec)
    if not os.path.exists(op):
        return dict(status="missing", stale_ids=[], why="ထွက်ဖိုင် မရှိ")
    pv = load_prov(spec)
    if pv is None:
        # S-a · fail-closed
        return dict(status="stale", stale_ids=["*"],
                    why="provenance မပါ — fail-closed (S-a)")
    if pv.get("out_hash") != _fh(op):
        return dict(status="stale", stale_ids=["*"],
                    why="ထွက်ဖိုင် ပြောင်းထားသည် (provenance နောက် လက်နဲ့ ပြင်?)")
    now = tool_hashes(spec)
    bad = [t for t, h in now.items() if (pv.get("tools") or {}).get(t) != h]
    if bad:
        return dict(status="stale", stale_ids=["*"],
                    why="tool ပြောင်း: " + ", ".join(os.path.basename(b) for b in bad))
    for up in spec.get("derives_from") or []:
        r = check(up)
        if r["status"] != "ok":
            return dict(status="stale", stale_ids=["*"],
                        why="အရင်းအမြစ် %s ဟောင်း (%s)" % (up, r["why"]))
    if not spec.get("per_template"):
        return dict(status="ok", stale_ids=[], why="")
    th = template_hashes()
    only = spec.get("only_module")
    rec = pv.get("templates") or {}
    stale = []
    for k, h in sorted(th.items()):
        if only and not k.startswith(only + "."):
            continue
        if not in_scope(spec, k):
            continue
        if rec.get(k) != h:
            stale.append(k)
    return (dict(status="ok", stale_ids=[], why="")
            if not stale else
            dict(status="stale", stale_ids=stale,
                 why="template %d ခု ပြောင်း" % len(stale)))


# ══ တခြား tool များ import လုပ်ပြီး ခေါ်ရန် ═══════════════════════
def require(name, what="ဂိတ်"):
    """⛔ S-b — ဟောင်းနေလျှင် `SystemExit(1)`။ ဂိတ်/တိုင်းချက်က ဒီကို ခေါ်ရမည်။"""
    r = check(name)
    if r["status"] == "ok":
        return True
    n = len(r["stale_ids"]) if r["stale_ids"] != ["*"] else "အားလုံး"
    raise SystemExit(
        "⛔ %s — `%s` ဟောင်းနေသည်: %s\n"
        "   S-b: ဟောင်းနေတဲ့ ဒေတာကနေ **ကိန်း မထုတ်ရ**။ ပြန်စစ်ရမည်: %s\n"
        "   စာရင်း: python3 tools/derived_check.py --stale-list %s"
        % (what, name, r["why"], n, name))


def warn(name, what="render"):
    """⚠️ S-b — production မှာ သတိပေးရုံ · ဆက်သွားသည်။"""
    r = check(name)
    if r["status"] != "ok":
        print("  ⚠️ %s: `%s` ဟောင်းနေသည် — %s (ဆက်သွားမည်)"
              % (what, name, r["why"]), flush=True)
    return r["status"] == "ok"


def _fmt_mt(p):
    import time
    m = _mt(p)
    return time.strftime("%m-%d %H:%M", time.localtime(m)) if m else "—"


def table():
    print("%-16s %-34s %-12s %-9s %s"
          % ("name", "ထွက်ဖိုင်", "ထုတ်ချိန်", "အနေအထား", "အကြောင်း"))
    nstale = 0
    for name, spec in REG.items():
        r = check(name)
        mark = {"ok": "✓", "stale": "⚠️ ဟောင်း", "missing": "✖ မရှိ"}[r["status"]]
        if r["status"] != "ok":
            nstale += 1
        print("%-16s %-34s %-12s %-9s %s"
              % (name, spec["out"][-34:], _fmt_mt(out_path(spec)), mark, r["why"]))
    print()
    print("**ဟောင်း/မရှိ %d / %d**" % (nstale, len(REG)))
    if nstale:
        print("⛔ S-b — ဂိတ်/တိုင်းချက်က ဟောင်းနေတဲ့ ဖိုင်ကနေ **ကိန်း မထုတ်ရ**。")
        print("   ပြန်စစ်ရမယ့် စာရင်း: derived_check.py --stale-list <name>")
    return 1 if nstale else 0


def main():
    a = sys.argv[1:]
    if not a:
        return table()
    if a[0] == "--stale-list" and len(a) > 1:
        r = check(a[1])
        if r["stale_ids"] == ["*"]:
            print("* (အားလုံး — %s)" % r["why"], file=sys.stderr)
            th = template_hashes()
            only = REG[a[1]].get("only_module")
            for k in sorted(th):
                if not only or k.startswith(only + "."):
                    print(k)
            return 0
        for k in r["stale_ids"]:
            print(k)
        return 0
    if a[0] == "--gate" and len(a) > 1:
        r = check(a[1])
        if r["status"] == "ok":
            print("  ✓ %s — လက်ရှိ ဖြစ်သည် (ကိန်း ထုတ်လို့ရ)" % a[1])
            return 0
        print("  ⛔ %s ဟောင်း — %s" % (a[1], r["why"]), file=sys.stderr)
        print("     S-b: ဂိတ်/တိုင်းချက်က ကိန်း မထုတ်ရ。 ပြန်စစ်ရမယ့် အရေအတွက်: %s"
              % (len(r["stale_ids"]) if r["stale_ids"] != ["*"] else "အားလုံး"),
              file=sys.stderr)
        return 1
    if a[0] == "--warn" and len(a) > 1:
        r = check(a[1])
        if r["status"] != "ok":
            print("  ⚠️ %s ဟောင်း — %s (render ဆက်သွားမည်)" % (a[1], r["why"]))
        return 0
    if a[0] == "--record" and len(a) > 1:
        ids = None
        if "--ids" in a:
            ids = [x for x in a[a.index("--ids") + 1].split(",") if x]
        return record(a[1], ids)
    print(__doc__)
    print("အသုံး: derived_check.py [--stale-list N | --gate N | --warn N | "
          "--record N [--ids a,b]]")
    print("N:", ", ".join(REG))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
