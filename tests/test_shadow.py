# -*- coding: utf-8 -*-
"""function အမည်ကို **တန်ဖိုးနဲ့ လွှမ်းမိခြင်း** ကို ဖမ်းသည်။

⚠️ ၂၀၂၆-၀၉-၂၄ — `render()` ထဲမှာ `def _drop(...)` ရှိပြီးသား ဖြစ်လျက်
   နောက်ပိုင်းမှာ `_keep, _drop = [], []` ဟု ရေးမိသဖြင့် `_drop(cutv)`
   ခေါ်ချိန် `TypeError: 'list' object is not callable` ဖြစ်ကာ
   **render တစ်ခုလုံး ကျ**ခဲ့သည် (~၁၅ မိနစ် ကုန်)。
⚠️ `make test` က မဖမ်းနိုင်ခဲ့ — test တွေက `render()` ကို တကယ် မခေါ်ပါ。
   ⇒ AST နဲ့ **ကုဒ်ဖတ်ပြီး** စစ်သည် (render မလုပ်ဘဲ ဖမ်းနိုင်သည်)。
⚠️ ဤစစ်ချက်က `worker/` · `core/` · `api/` အားလုံးကို လွှမ်းသည်。
"""
import ast, os, sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ("worker", "core", "api", "tools")

OK = FAIL = 0


def ck(name, cond, extra=""):
    global OK, FAIL
    if cond:
        OK += 1
    else:
        FAIL += 1
        print(f"  ✗ {name}  {extra}")


def _targets(node):
    """assignment target အမည်များ"""
    out = []
    for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
        for n in ast.walk(t):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                out.append((n.id, n.lineno))
    return out


def scan(path):
    """`(fn_name, shadowed_name, def_line, assign_line)` စာရင်း"""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except SyntaxError as e:
        return [("<parse>", str(e), 0, 0)]
    bad = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # ⚠️ **တိုက်ရိုက် ကလေးများသာ** — nested function ထဲက def ကို
        #    ပြင်ပ scope က မဖြစ်နိုင်သဖြင့် ထည့်၍ မရ。
        inner = {}
        for st in ast.walk(fn):
            if (isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and st is not fn):
                inner.setdefault(st.name, st.lineno)
        if not inner:
            continue
        for st in ast.walk(fn):
            if not isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                continue
            for nm, ln in _targets(st):
                if nm in inner and ln > inner[nm]:
                    bad.append((fn.name, nm, inner[nm], ln))
    return bad


print("── function အမည်ကို တန်ဖိုးနဲ့ လွှမ်းမိမှု ──")
tot = 0
for d in DIRS:
    p = os.path.join(R, d)
    if not os.path.isdir(p):
        continue
    for f in sorted(os.listdir(p)):
        if not f.endswith(".py"):
            continue
        q = os.path.join(p, f)
        bad = scan(q)
        tot += 1
        ck(f"{d}/{f}", not bad,
           " · ".join(f"{fn}(): «{nm}» def@{dl} ⇒ လွှမ်း@{al}"
                      for fn, nm, dl, al in bad[:4]))

print(f"\n  ဖိုင် {tot} ခု စစ်ပြီး ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
