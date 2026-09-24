# -*- coding: utf-8 -*-
"""Visible-shot preflight: preserve words, never cross a user cut."""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import cut as CUT

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond:
        OK += 1; print("  ✓ " + name)
    else:
        FAIL += 1; print("  ✗ " + name + ("  " + extra if extra else ""))

print("\n── visible-shot stabilizer ──")
sp, audit, blocked = CUT.stabilize_visible_spans([(1.00, 1.30), (2.0, 2.8)],
                                                   dur=4.0)
ck("တိုသော kept speech ကို မဖျက်", len(sp) == 2 and sp[0][0] < 1.0 and sp[0][1] > 1.3, repr(sp))
ck("preview target 0.80s ရောက်", sp[0][1] - sp[0][0] >= 0.799, repr(sp[0]))
ck("audit ရှိ · block မရှိ", len(audit) == 1 and not blocked, repr((audit, blocked)))

sp, audit, blocked = CUT.stabilize_visible_spans([(1.00, 1.30)],
                                                   explicit_drops=[(0.50, 1.00), (1.30, 1.60)],
                                                   dur=3.0)
ck("user ဖြတ်ချက်ကို မကျော်", sp == [(1.0, 1.3)], repr(sp))
ck("မရလျှင် တိတ်တဆိတ် မပြင်", not audit and len(blocked) == 1, repr((audit, blocked)))

sp, audit, blocked = CUT.stabilize_visible_spans([(0.40, 1.00)], dur=2.0)
ck("0.60s အတိအကျကို မပြင်", sp == [(0.4, 1.0)] and not audit and not blocked, repr((sp, audit, blocked)))

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
