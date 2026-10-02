# -*- coding: utf-8 -*-
"""api.HOUSE_THEME must equal motionkit theme.THEMES for the house brands.
The UI shows these as "what this brand renders with"; if they drift, the UI
lies about the colours/fonts again (2026-10-02 audit)."""
import os, sys, tempfile
_T = tempfile.mkdtemp(prefix="ikki_ht_")
os.environ["IKKI_DATA"] = _T; os.environ["IKKI_DB"] = os.path.join(_T, "t.db")
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "api")); sys.path.insert(0, os.path.join(_R, "core"))
try:
    import fastapi  # noqa: F401
except ImportError:
    print("  ⊘ fastapi မရှိ — ကျော်သည်"); sys.exit(0)
import main as M
MK = os.environ.get("IKKI_MOTIONKIT", "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")
if not os.path.isdir(MK):
    print("  ⊘ motionkit မရှိ — ကျော်သည်"); sys.exit(0)
sys.path.insert(0, MK); import theme
bad = 0
for b, h in M.HOUSE_THEME.items():
    t = theme.THEMES[b]
    want = dict(colors=[t[k] for k in ("NAVY", "DEEP", "GOLD", "SKY", "RED")], mmf=t["MMF"], latin=t["LATIN"])
    ok = want == h
    bad += not ok
    print(("  ✓ " if ok else "  ✗ ") + b, "" if ok else f"api={h} motionkit={want}")
sys.exit(1 if bad else 0)
