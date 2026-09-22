# -*- coding: utf-8 -*-
"""SFX အကွာ ပြန်ခြားချက် — **အထပ် အတွဲကို မခွဲရ**。

⚠️ ၂၀၂၆-၀၉-၂၂ ငါ့ regression: `sfx_spacing` ဂိတ်အတွက် ဖြတ်ပြီး အချိန်မှာ
   အကွာ ပြန်ခြားခဲ့သည် — ဒါပေမယ့် **cue တစ်ခုချင်း** စစ်မိသဖြင့်
   ဖြစ်ရပ်တစ်ခုရဲ့ ရှေ့သံ+ထပ်သံ (`card` ⇒ whoosh_in + latch · ၀.၁၈s ကွာ)
   ကို ခွဲပြီး ထပ်သံကို ဖယ်ပစ်ခဲ့သည် ⇒ တကယ့် render မှာ
     1.92 riser_soft · 9.16 swipe · 15.28/23.12/29.30/36.74 **whoosh_in ×4**
   ဖြစ်ကာ 「အသံ တစ်မျိုးတည်း」ဖြစ်ခဲ့သည်。
⚠️ `planner` ရဲ့ မှတ်ချက်: 「Layered sounds count as one sound moment」。
"""
import os, re, sys

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

W = open(os.path.join(_R, "worker", "run.py"), encoding="utf-8").read()

print("── ① ဖြစ်ရပ် အလိုက် စုပြီးမှ အကွာ စစ်ရမည် ──")
ck("`LAYER_W` ရှိ", "LAYER_W" in W)
ck("ဖြစ်ရပ် စုချက် ရှိ", "_mom" in W and "_mom[-1].append(_c)" in W)
ck("cue တစ်ခုချင်း စစ်တာ မရှိ",
   not re.search(r"if _keep2 and \(_c\[0\] - _keep2\[-1\]\[0\]\) < _g", W))
ck("role ထပ်မှု အစီရင်ခံ", 'REPORT["sfx_role_max_run"]' in W)
ck("role အရေအတွက် အစီရင်ခံ", 'REPORT["sfx_roles"]' in W)

print("\n── ② logic — အထပ် အတွဲ ကျန်ရမည် ──")
m = re.search(r"LAYER_W\s*=\s*([0-9.]+)", W)
LAYER_W = float(m.group(1)) if m else 0.40
def respace(cues, g):
    mom = []
    for c in sorted(cues, key=lambda x: x[0]):
        if mom and (c[0] - mom[-1][-1][0]) <= LAYER_W: mom[-1].append(c)
        else: mom.append([c])
    keep, dm = [], 0
    for mm in mom:
        if keep and (mm[0][0] - keep[-1][0]) < g: dm += 1; continue
        keep.extend(mm)
    return sorted(keep, key=lambda x: x[0]), len(mom), dm

C = [(1.92, "riser_soft"), (2.10, "latch"), (9.16, "swipe"), (9.34, "click"),
     (15.28, "whoosh_in"), (15.46, "latch"), (16.00, "pop")]
keep, nm, dm = respace(C, 2.0)
ck("ဖြစ်ရပ် ၄ ခု အဖြစ် စု", nm == 4, nm)
ck("ထပ်သံ `latch` ကျန်", any(r == "latch" for _a, r in keep), keep)
ck("ထပ်သံ `click` ကျန်", any(r == "click" for _a, r in keep))
ck("အကွာ နီးသော ဖြစ်ရပ် ဖယ်", dm == 1, dm)
# ⚠️ ဖြစ်ရပ် အချင်းချင်း အကွာက ဂိတ် အထက် ဖြစ်ရမည်
firsts = []
for a, r in keep:
    if not firsts or a - firsts[-1] > LAYER_W: firsts.append(a)
ck("ဖြစ်ရပ် အကွာ ≥ 2.0s",
   all(firsts[i+1] - firsts[i] >= 2.0 - 1e-9 for i in range(len(firsts)-1)),
   firsts)

print("\n── ③ ဖြစ်ရပ် တစ်ခုတည်း ⇒ ဘာမှ မဖယ်ရ ──")
keep2, nm2, dm2 = respace([(5.0, "whoosh_in"), (5.18, "latch")], 2.0)
ck("၂ ခုလုံး ကျန်", len(keep2) == 2, keep2)
ck("ဖယ်ချက် မရှိ", dm2 == 0)

print("\n── ④ role ထပ်မှု တိုင်းချက် ──")
def maxrun(rs):
    run = mx = 1
    for i in range(1, len(rs)):
        run = run + 1 if rs[i] == rs[i-1] else 1
        mx = max(mx, run)
    return mx if rs else 0
ck("whoosh ×4 ⇒ run 4",
   maxrun(["riser_soft", "swipe", "whoosh_in", "whoosh_in", "whoosh_in",
           "whoosh_in"]) == 4)
ck("အထပ် ပါလျှင် run 1",
   maxrun(["riser_soft", "latch", "swipe", "click", "whoosh_in", "latch"]) == 1)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
