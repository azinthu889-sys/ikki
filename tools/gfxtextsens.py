#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""template က **ကျွန်တော်တို့ စာသားကို တကယ် ရေးလား** စစ်သည်။

    python3 tools/gfxtextsens.py [--only id,id] [--limit N]

⚠️ **ဘာကြောင့် လိုအပ်လဲ** — `gfx_verify.py` ရဲ့ ဂိတ်က 「render ဖြစ်ပြီး မှင်
   ရှိ」ပဲ စစ်သည်。 အရောင်တုံး ချည်းပဲ ပါပြီး စာသား လုံးဝ မပါသော template တွေ
   အောင်သွားကာ ဗီဒီယိုထဲ **အဓိပ္ပာယ်မဲ့ ကွက်** ဖြစ်ခဲ့သည်
   (Zin ၂၀၂၆-၀၉-၂၀: 「template သုံးထားတာတွေရော quality 0」)。
⚠️ `tools/gfx_pool.py` ရဲ့ gradient ဂိတ်က **မယုံရ** — ကောင်း/ဆိုး နမူနာ ၁၄ ခုမှာ
   ကိန်းတွေ ထပ်နေသည် (⛔ မှတ်ချက် ကြည့်ပါ)。

**နည်းလမ်း** — တူညီသော template ကို **စာသား ၂ မျိုး**နဲ့ render လုပ်ပြီး
ထွက်လာသော **ပုံရိပ်** ကွာမကွာ တိုင်းသည်。 စာသားကို တကယ် ရေးလျှင် ပုံရိပ်
**ပြောင်းရမည်**。 မပြောင်းလျှင် လျစ်လျူရှုနေသည် ⇒ pool ထဲ မထည့်ရ。

တိုင်းရာမှာ ချို့ယွင်းချက် ၃ ခု တွေ့ခဲ့ပြီး ၃ ခုလုံး ပြင်ထားသည် —

⚠️ ① **နောက်ဆုံး frame ကို မသုံးရ** — template အများစုက fade ထွက်သွားသဖြင့်
   နောက်ဆုံး frame က ဗလာနီးပါး ⇒ စာသား မတူလည်း တူနေမည် ⇒ **မှင် အများဆုံး
   frame** ကို ရွေးသည်。
⚠️ ② **`statics` ကို မကျန်စေရ** — template အများအပြားက စာသားကို `anim` ထဲ
   မထားဘဲ `statics` ထဲ ပြန်ပေးသည် (`dress.py:394,707,723` က composite လုပ်သည်)。
   တကယ်တွေ့: `infogfx.checklist` ရဲ့ `anim` က checkbox ကွက်သာ (items အရေအတွက်
   ပေါ်သာ မူတည်) ⇒ diff ၀.၀၀၀ ထွက်ခဲ့သည် (၂၀၂၆-၀၉-၂၄)。
⚠️ ③ **alpha ပုံစံချည်း မတိုင်ရ** — အလင်းပိတ် ကတ်ပြားပေါ် စာရေးသော template
   တွေမှာ alpha က ကတ်ပြား ပုံသဏ္ဌာန်သာ ဖြစ်ပြီး **စာသားက RGB ထဲ** ရှိသည်
   ⇒ စာသား ဘာပဲဖြစ်ဖြစ် alpha တူနေမည် (တကယ်တွေ့: `insert.insert_label`
   diff ၀.၀၀၀ · ၂၀၂၆-၀၉-၂၄)。 ⇒ **RGBA ကို နောက်ခံပေါ် ထပ်ပြီး** တိုင်းသည်。

⚠️ **A/A ထိန်းချုပ်မှု** — မတည်ငြိမ်သော template (ကျပန်း · အချိန်အပေါ် မူတည်)
   က စာသား မပြောင်းလည်း ပုံရိပ် ပြောင်းနိုင်သည် ⇒ **false positive**。
   ဒါကြောင့် A/B ကွာဟမှု ဂိတ် ကျော်လျှင် **စာသား တူတူနဲ့ တတိယ render** လုပ်ပြီး
   အဲဒီ A/A ကွာဟမှု သေးမှသာ အောင်စေသည် (`AA_MAX` · `AB_OVER_AA`)。
⚠️ တစ်ခုချင်း **သီးသန့် process** — template တစ်ခု ကျလျှင် တစ်ခုလုံး မရပ်စေရန်。
"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "core"))
TIMEOUT = 150            # render ၃ ခါ ဖြစ်နိုင်သဖြင့် ရှည်ရမည်
DIFF_MIN = 0.02          # ပုံရိပ် ကွာဟမှု အနည်းဆုံး (ဧရိယာ အချိုး)
AA_MAX = 0.02            # စာသား တူတူနဲ့ ကွာဟမှု — ဤထက် ကြီးလျှင် မတည်ငြိမ်
AB_OVER_AA = 3.0         # A/B က A/A ထက် အနည်းဆုံး ဤအဆ ကြီးရမည်
OUT = os.path.join(HERE, "assets", "gfx_textsens.json")

# ⚠️ စာသား ၂ မျိုးက **အရှည် သိသိသာသာ ကွာ**ရမည် — တူညီသော အရှည်ဆိုလျှင်
#    စာလုံး အနေအထား တူပြီး ကွာဟမှု နည်းနိုင်သည်。
TXT_A = "ဂျပန်မှာ အလုပ်"
TXT_B = "ပြည်ပကနေ ချစ်ရသူတွေဆီ ငွေလွှဲခြင်းနဲ့ ဆုလက်ဆောင်"
ITM_A = ["ဂျပန်", "ကိုးရီးယား", "စင်္ကာပူ"]
ITM_B = ["ပြည်ပ ငွေလွှဲ", "ဘဏ် အကောင့်", "မိုဘိုင်း ငွေဖြည့်ခြင်း"]

CHILD = r'''
import os, sys, json
sys.path.insert(0, os.path.join(%(HERE)r, "core"))
import gfxcat as G, dress as DR
import numpy as np
from PIL import Image

eid = sys.argv[1]
e = [x for x in G.catalog() if x["id"] == eid]
if not e:
    print(json.dumps({"ok": 0, "why": "id မတွေ့"})); raise SystemExit
e = e[0]

BG = 128          # နောက်ခံ အလယ်မီးခိုး — RGBA ကို ဤအပေါ် ထပ်သည်
TOL = 24          # ပုံရိပ် ကွာဟမှု အနည်းဆုံး (0–255)


def _flat(q):
    """RGBA ဖိုင်ကို **နောက်ခံပေါ် ထပ်ပြီး** မီးခိုးရောင် + alpha ပြန်ပေးသည်ဂ

    ⚠️ alpha ချည်း မတိုင်ရ — အလင်းပိတ် ကတ်ပြားပေါ် စာရေးသော template မှာ
       alpha က ကတ်ပြား ပုံသဏ္ဌာန်သာ ဖြစ်ပြီး စာသားက RGB ထဲ ရှိသည်ဂ
    """
    im = np.asarray(Image.open(q).convert("RGBA")).astype(np.float32)
    a = im[:, :, 3:4] / 255.0
    rgb = im[:, :, :3] * a + BG * (1.0 - a)
    g = rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114
    return g, im[:, :, 3]


def build(txt, items, tag):
    """engine ရဲ့ လမ်းကြောင်းအတိုင်း — `_tf_args` ⇒ `_call_template`ဂ"""
    a = DR._tf_args(dict(kind=eid, text=txt, items=items),
                    accent="#FFE000", ink="#FFFFFF", dim="#8B8B8B")
    if not a:
        a = G.fill(e, txt, "ZAE", 62)
        if not a:
            return None, "fill ဗလာ"
        if DR._wants_tag(e["fn"]):
            a = ("g0",) + tuple(a)
        el = G.call(e, a, 2.0)
    else:
        # ⚠️ template တွေက frame ကို **motionkit ရဲ့ cwd** နဲ့ ဆက်စပ်ပြီး
        #    ရေးသည် (`gfxcat.call()` က `os.chdir(MK)` လုပ်သည်) ⇒
        #    မလုပ်လျှင် 「ဖိုင် မရှိ」ဖြစ်သည်ဂ
        _cwd = os.getcwd()
        try:
            if G.MK not in sys.path:
                sys.path.insert(0, G.MK)
            os.chdir(G.MK)
            import importlib
            _m = importlib.import_module(e["module"])
            el = DR._call_template(getattr(_m, e["fn"]), eid, tag, a)
        finally:
            try: os.chdir(_cwd)
            except Exception: pass
    if not isinstance(el, dict):
        return None, "dict မဟုတ်"
    fr = el.get("anim") or el.get("frames") or []
    st = el.get("statics") or []
    if len(fr) < 2 and not st:
        return None, "ဖရိမ်း %%d" %% len(fr)

    def rp(q):
        return q if os.path.isabs(q) else os.path.join(G.MK, q)

    # ⚠️ **မှင် အများဆုံး frame** — နောက်ဆုံး frame က fade ထွက်ပြီး ဗလာနီးပါး
    best, bink = None, -1.0
    idx = sorted({int(len(fr) * f) for f in (0.35, 0.45, 0.55, 0.65, 0.75, 0.85)}
                 | ({len(fr) - 1} if fr else set()))
    for j in idx:
        if not (0 <= j < len(fr)):
            continue
        it = fr[j]
        q = rp(it[0] if isinstance(it, (list, tuple)) else it)
        if not os.path.exists(q):
            continue
        g, al = _flat(q)
        ik = float((al > 16).mean())
        if ik > bink:
            bink, best = ik, (g, al)

    # ⚠️ **`statics` ကို မကျန်စေရ** — စာသားက များသောအားဖြင့် ဤထဲ ရှိသည်
    out = [] if best is None else [best]
    for it in st:
        q = rp(it[0] if isinstance(it, (list, tuple)) else it)
        if os.path.exists(q):
            out.append(_flat(q))
    if not out:
        return None, "ဖိုင် မရှိ"
    return out, None


def cmp(p, q):
    """ပုံရိပ် ကွာဟမှု — ကွာသော pixel ÷ မှင် စုစုပေါင်းဂ

    အရွယ် · အရေအတွက် မတူလျှင် None (= လုံးဝ ကွာ)ဂ
    **အများဆုံးကို ယူသည် — ပျမ်းမျှ မဟုတ်**: စာသားက အစိတ်အပိုင်း တစ်ခုတည်း
    ဖြစ်ပြီး ကျန်တာ ကြီးမားလျှင် ပျမ်းမျှက ရေပေါ်သွားမည်ဂ
    """
    if len(p) != len(q) or any(x[0].shape != y[0].shape for x, y in zip(p, q)):
        return None
    d = 0.0
    for (g1, a1), (g2, a2) in zip(p, q):
        m = (a1 > 16) | (a2 > 16)
        un = float(m.sum())
        if not un:
            continue
        d = max(d, float(((np.abs(g1 - g2) > TOL) & m).sum() / un))
    return d


try:
    A, w = build(%(TA)r, %(IA)r, "s0")
    if A is None:
        print(json.dumps({"ok": 0, "why": w})); raise SystemExit
    B, w = build(%(TB)r, %(IB)r, "s1")
    if B is None:
        print(json.dumps({"ok": 0, "why": w})); raise SystemExit
except SystemExit:
    raise
except BaseException as _ex:
    print(json.dumps({"ok": 0,
                      "why": "%%s: %%s" %% (type(_ex).__name__, str(_ex)[:70])}))
    raise SystemExit

ink = max(float((a > 16).mean()) for _, a in A)
ab = cmp(A, B)
if ab is None:
    # အရွယ် ကွာ = စာသားကြောင့် ပုံစံ ပြောင်းသည် ⇒ အောင်
    print(json.dumps({"ok": 1, "diff": 1.0, "aa": 0.0, "ink": round(ink, 5),
                      "why": "အရွယ် ကွာ"}))
    raise SystemExit

if ab < %(DM)f:
    print(json.dumps({"ok": 0, "diff": round(ab, 4), "ink": round(ink, 5),
                      "why": "စာသား ပြောင်းလည်း ပုံရိပ် မပြောင်း (%%0.3f)" %% ab}))
    raise SystemExit

# ⚠️ **A/A ထိန်းချုပ်မှု** — စာသား တူတူနဲ့ ထပ် render လုပ်ပြီး ကျပန်းလား စစ်သည်ဂ
#    ဂိတ် ကျော်ပြီးမှ လုပ်သဖြင့် ကျသွားသော template တွေမှာ အချိန် မကုန်ဂ
try:
    A2, w = build(%(TA)r, %(IA)r, "s2")
except BaseException as _ex:
    A2, w = None, "%%s: %%s" %% (type(_ex).__name__, str(_ex)[:60])
if A2 is None:
    print(json.dumps({"ok": 0, "diff": round(ab, 4), "ink": round(ink, 5),
                      "why": "A/A မရ (%%s)" %% w}))
    raise SystemExit
aa = cmp(A, A2)
if aa is None:
    print(json.dumps({"ok": 0, "diff": round(ab, 4), "aa": 1.0, "ink": round(ink, 5),
                      "why": "မတည်ငြိမ် — စာသား တူလျက် အရွယ် ကွာ"}))
    raise SystemExit

ok = 1 if (aa <= %(AAM)f and ab >= aa * %(AOA)f) else 0
print(json.dumps({"ok": ok, "diff": round(ab, 4), "aa": round(aa, 4),
                  "ink": round(ink, 5),
                  "why": "" if ok else
                         "မတည်ငြိမ် — စာသား တူလျက် ကွာ %%0.3f (A/B %%0.3f)" %% (aa, ab)}))
''' % {"HERE": HERE, "TA": TXT_A, "TB": TXT_B, "IA": ITM_A, "IB": ITM_B,
       "DM": DIFF_MIN, "AAM": AA_MAX, "AOA": AB_OVER_AA}


def main():
    import gfxcat as G
    only = None
    limit = 0
    for i, a in enumerate(sys.argv):
        if a == "--only" and i + 1 < len(sys.argv):
            only = set(sys.argv[i + 1].split(","))
        elif a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    ents = G.usable()
    if only:
        ents = [e for e in ents if e["id"] in only]
    if limit:
        ents = ents[:limit]
    print(f"စစ်မည် {len(ents)} ခု · စာသား ၂ မျိုး + A/A ထိန်းချုပ် · "
          f"ဂိတ် diff ≥{DIFF_MIN} · A/A ≤{AA_MAX} · timeout {TIMEOUT}s", flush=True)
    res, t0 = [], time.time()
    for i, e in enumerate(ents, 1):
        r = {"id": e["id"], "category": e.get("category")}
        try:
            p = subprocess.run([sys.executable, "-c", CHILD, e["id"]],
                               capture_output=True, text=True, timeout=TIMEOUT,
                               cwd=HERE)
            out = [l for l in (p.stdout or "").splitlines() if l.startswith("{")]
            r.update(json.loads(out[-1]) if out else
                     {"ok": 0, "why": "ထွက်ချက် ဗလာ"})
        except subprocess.TimeoutExpired:
            r.update({"ok": 0, "why": f"{TIMEOUT}s ကျော်"})
        except Exception as ex:
            r.update({"ok": 0, "why": f"{type(ex).__name__}: {ex}"})
        res.append(r)
        print(f"  [{i:3d}/{len(ents)}] {'✓' if r.get('ok') else '✖'} "
              f"{e['id']:34s} diff={r.get('diff', '—')} aa={r.get('aa', '—')} "
              f"{str(r.get('why',''))[:40]}", flush=True)
    ok = [r for r in res if r.get("ok")]
    print(f"\nစာသား တကယ် ရေး {len(ok)}/{len(res)} · {time.time()-t0:.0f}s", flush=True)
    # ⚠️ အပိုင်း ပြေးလျှင် **ပေါင်း**သည် (မလွှမ်းရ)
    old = []
    if os.path.exists(OUT):
        try: old = json.load(open(OUT, encoding="utf-8")) or []
        except Exception: old = []
    merged = {r["id"]: r for r in old}
    merged.update({r["id"]: r for r in res})
    json.dump(sorted(merged.values(), key=lambda r: r["id"]),
              open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"ရေးပြီး — {OUT} ({len(merged)} entry)")


if __name__ == "__main__":
    main()
