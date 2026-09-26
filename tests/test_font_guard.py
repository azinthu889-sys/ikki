#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Font guard — render the chosen font or refuse; never a silent substitution.

Zin, 2026-09-26.  motionkit's Linux renderer maps Pyidaungsu (and 8 more) to
Noto Sans Myanmar silently; CoreText falls back silently for unknown names.
The worker must check the job's Burmese fonts against the list measured for
its own renderer (api/fonts_render.json) and refuse, naming the font.
"""
import os, sys, json, tempfile, importlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))


def main():
    fails = []
    def check(ok, msg):
        print(("✓ " if ok else "✗ ") + msg)
        if not ok: fails.append(msg)
    import fonts as FN
    d = tempfile.mkdtemp(); p = os.path.join(d, "fonts_render.json")
    json.dump(dict(coretext=["Pyidaungsu", "Padauk"], pango=["Padauk"]), open(p, "w"))
    FN._RJ = [p]
    check(FN.guard(["Pyidaungsu"], log=lambda *_: None, r="coretext"),
          "Pyidaungsu passes on CoreText")
    # a recipe font outside the picker must be checked too (promotional's
    # "NotoSansMyanmar" slipped through when only picker ids were checked)
    try:
        FN.guard(["NotoSansMyanmar"], log=lambda *_: None, r="coretext")
        check(False, "an unmeasured recipe font must be refused")
    except FN.FontRefused:
        check(True, "a recipe font that is not in the measured list is refused")
    try:
        FN.guard(["Pyidaungsu"], log=lambda *_: None, r="pango")
        check(False, "Pyidaungsu on Pango must be refused")
    except FN.FontRefused as e:
        check("Pyidaungsu" in str(e) and "pango" in str(e), "Pyidaungsu on Pango refused, font named")
    FN._RJ = [os.path.join(d, "missing.json")]
    try:
        FN.guard(["Padauk"], log=lambda *_: None, r="pango")
        check(False, "no measured list ⇒ nothing allowed")
    except FN.FontRefused:
        check(True, "unmeasured renderer refuses instead of guessing")
    os.environ["MK_TEXT"] = "rsvg"
    check(FN.renderer() == "pango", "MK_TEXT=rsvg ⇒ pango (motionkit's own rule)")
    os.environ.pop("MK_TEXT")
    # every recipe + its theme passes on CoreText with the REAL measured list
    FN._RJ = [os.path.join(ROOT, "api", "fonts_render.json")]
    import recipes as R
    sys.path.insert(0, FN.MK)
    import theme as TH
    refused = []
    for k in R.R:
        rc = R.get(k)
        try:
            TH.use(rc.get("theme") or "ikki"); thm = TH.t().get("MMF")
        except Exception:
            thm = None
        try:
            FN.guard([rc.get("mmf"), thm], log=lambda *_: None, r="coretext")
        except FN.FontRefused:
            refused.append(k)
    check(not refused, f"all {len(R.R)} recipes pass the CoreText guard ({refused})")
    # the worker no longer falls back to the recipe font for an unknown choice
    src = open(os.path.join(ROOT, "worker", "run.py"), encoding="utf-8").read()
    check("ပုံသေ သုံးသည်\")" not in src and "FontRefused(f\"ဖောင့် '{jf}'" in src,
          "unknown user font is refused, not silently replaced")
    check(src.count("FN.guard(") >= 3, "guard called in render(), cine_handle() and the captioner")
    print(f"\n{len(fails)} failed" if fails else "\nall passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
