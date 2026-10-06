#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modern Talking-Head (`modern.mt_*`) template များ — ၂၀၂၆-၁၀-၀၅

reference ၆ ပုဒ်ကို တိုင်းပြီး motionkit/modern.py မှာ ဆောက်ထားသည်
(`AI Company/ikki-audit/modern-th-spec.md`)。 ဒီမှာ စစ်သည်:
  · pack မှာ ၆ ခုလုံး manifest မှန်ပြီး ရွေးနိုင် (selectable) · intent ချိတ်
  · 16:9 + 9:16 · dur တို (၂.၂s) မှာလည်း ဆောက်ရ · စာတန်း ဇုန် (≥၀.၇၉H) မဝင်
  · overlay ink အကျယ် ≤ ဘောင် − ၂×၂% (dress.track ×၀.၉၆ မချုံ့ရ — band
    ဘေးမှာ ဒေါင်လိုက် အနားသတ် ပြတ် ပေါ်သည်)
  · IKKI motion QC (`motmeas`) — ဝင် ease-out ≥ ၀.၃၀ · ဝင်/ထွက် band အတွင်း
  · MyanmarBlack 「အေ」 font guard — အစားထိုးပြီး stderr မှာ ပြ (တိတ်တဆိတ် မဟုတ်)
motionkit မရှိသော စက် (VPS) မှာ ကျော်သည်。
"""
import io
import os
import sys
import contextlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))

IDS = ["mt_pill_list", "mt_neon_box", "mt_counter", "mt_explainer_page",
       "mt_section", "mt_compare"]
ARGS = {"mt_pill_list": dict(head="ပြင်ဆင်ရမည်", items=["စာရွက်စာတမ်း", "ဘာသာစကား", "ငွေကြေး"]),
        "mt_neon_box": dict(text="အရေးကြီးဆုံး"),
        "mt_counter": dict(value="85%", label="အောင်နှုန်း"),
        "mt_explainer_page": dict(items=["လျှောက်", "စာမေးပွဲ", "ထွက်ခွာ", "ရောက်ရှိ"]),
        "mt_section": dict(head="အပိုင်း ၂", sub="ဗီဇာ"),
        "mt_compare": dict(left="ဂျပန်", right="ကိုရီးယား")}


def main():
    fails = []

    def check(ok, msg):
        print(("✓ " if ok else "✗ ") + msg)
        if not ok:
            fails.append(msg)

    import gfxcat as GC
    if not os.path.isfile(os.path.join(GC.MK, "modern.py")):
        print("✓ motionkit/modern.py မရှိ (VPS) — ကျော်သည် · အားလုံး")
        return 0

    # ── pack ──
    import pack as PK
    sel = set(PK.selectable())
    for k in IDS:
        check(f"modern.{k}" in sel, f"pack selectable: modern.{k}")
    check("modern.mt_pill_list" in PK.by_intent("checklist"), "checklist → mt_pill_list")
    check("modern.mt_counter" in PK.by_intent("number"), "number → mt_counter")
    check("modern.mt_compare" in PK.by_intent("compare"), "compare → mt_compare")
    check(bool((PK.template("modern.mt_explainer_page") or {}).get("fullFrame")),
          "explainer_page က fullFrame (cutaway လမ်း)")

    sys.path.insert(0, GC.MK)
    cwd = os.getcwd()
    os.chdir(GC.MK)
    try:
        import numpy as np
        from PIL import Image
        import theme as TH
        import motmeas as MM
        import modern as M
        import infogfx as IG
        import dress as DR
        check(DR._modern_dur("modern.mt_neon_box", {"text": "x"}, 1.0)["dur"] == 1.4
              and DR._modern_dur("modern.mt_section", {"head": "x"}, 3.0)["dur"] == 3.0
              and DR._modern_dur("modern.mt_section", {"head": "x", "dur": 2.6}, 1.0)["dur"] == 2.6
              and "dur" not in DR._modern_dur("modern.mt_counter", {"value": "1"}, None)
              and DR._modern_dur("prem7.compare_bar", {"a": 1}, 1.0) == {"a": 1},
              "dress `hold` ⇒ modern `dur` (အနည်းဆုံး ချိန်ချက်)")

        for asp in ("16:9", "9:16"):
            TH.use("ikki", asp)
            for k in IDS:
                # ⚠️ "min" = dress ရဲ့ ဖတ်လို့ရသော အနည်းဆုံး (worker `hold` တိုလျှင်) —
                #    motion QC လည်း အောင်ရမည် (j_d96beb16229d)
                for dur in (None, 2.2, "min"):
                    kw = dict(ARGS[k])
                    if dur == "min":
                        dur = DR.MODERN_MIN_DUR[k]
                    if dur:
                        kw["dur"] = dur
                    try:
                        r = getattr(M, k)(f"tmt_{k}_{asp[0]}_{dur}", **kw)
                    except Exception as e:
                        check(False, f"{asp} {k} dur={dur}: {type(e).__name__}: {e}")
                        continue
                    an = r.get("anim") or []
                    check(bool(an) and r.get("dur"), f"{asp} {k} dur={dur} — frame {len(an)}")
                    if dur == 2.2 or k == "mt_explainer_page":
                        continue
                    # ink — အလယ် frame + ပြည့်ချိန် frame (alpha > 8 ကို dress နဲ့ တူ)
                    al = [np.asarray(Image.open(p).convert("RGBA").getchannel("A"))
                          for p, _, _ in an]
                    H_, W_ = al[0].shape
                    mx = np.maximum.reduce(al)
                    ys = np.nonzero(mx.max(axis=1) > 8)[0]
                    xs = np.nonzero(mx.max(axis=0) > 8)[0]
                    check(len(ys) and ys.max() <= 0.79 * H_,
                          f"{asp} {k} — ink အောက်ခြေ {ys.max() / H_:.3f}H ≤ 0.79")
                    check(len(xs) and (xs.max() - xs.min() + 1) <= W_ - 2 * max(8, int(W_ * 0.02)),
                          f"{asp} {k} — ink အကျယ် {(xs.max() - xs.min() + 1) / W_:.3f}W (×0.96 မချုံ့)")
                    v = [float(a.mean()) / 255.0 for a in al]
                    MM.alpha_series = lambda mov, small=None, v=v: (v, 30.0)
                    me = MM.measure("x")
                    bad = [c["key"] for c in MM.premium_checks(me)
                           if isinstance(c, dict) and not c.get("ok", True)
                           and c["key"] != "motion_measured"]
                    check(not bad, f"{asp} {k} — motion QC in {me.get('in_s')} "
                                   f"out {me.get('out_s')} ease {me.get('ease')} {bad or ''}")

        # ── font guard ──
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            IG.FONT_SWAPS.clear()
            a = IG._font_guard({"font": "MyanmarBlack", "text": "အောင်မြင်"})
            b = IG._font_guard({"font": "MyanmarBlack", "text": "ကျောင်း"})
            c = IG._font_guard({"font": "MyanmarYinmar", "text": "အေး"})
        check(a["font"] == "MyanmarYinmar", "MyanmarBlack + 「အေ」 ⇒ MyanmarYinmar")
        check(b["font"] == "MyanmarBlack", "「အေ」 မပါလျှင် မပြောင်း")
        check(c["font"] == "MyanmarYinmar", "အခြား font မထိ")
        check("MyanmarBlack" in err.getvalue() and IG.FONT_SWAPS.get("MyanmarBlack") == 1,
              "အစားထိုးချက်ကို stderr မှာ ပြ · ရေတွက် (တိတ်တဆိတ် မဟုတ်)")
    finally:
        os.chdir(cwd)

    if fails:
        print(f"✗ ကျ {len(fails)}")
        return 1
    print("✓ modern template — အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    sys.exit(main())
