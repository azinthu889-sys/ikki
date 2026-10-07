#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render smoke test — deploy မတိုင်ခင် **တိုတောင်းသော clip ဖြင့် pipeline တစ်ခုလုံး** စစ် (Zin ၂၀၂၆-၁၀-၀၇)

ဖြစ်ခဲ့ပုံ: beats engine ကို unit test သာ စစ်ပြီး deploy ⇒ Zin ရဲ့ ၉.၅ မိနစ် Raw.mp4 က
render ပြီးမှ QC မှာ ၂ ကြိမ် ကျ (npx PATH · gfx ရေတွက် · SFX cap) ⇒ ၂ နာရီ ဆုံးရှုံး။
⇒ worker `render()` ကို **ဒီစက်ပေါ်မှာ offline** (API/queue မထိ) ပြေးပြီး QC + beats ကို စစ်。

    python3 tools/smoke_render.py [--src clip.mp4] [--recipe headtop] [--fmt 16:9]

exit 0 = QC PASS (+ engine="beats" ဆိုလျှင် beat ≥1 ခု ထွက်) · 1 = ကျ · 2 = clip မရှိ。
⚠️ worker job လည်နေစဉ် မပြေးပါနဲ့ (CPU/disk ခွဲယူ) — deploy.sh က busy စစ်ပြီးမှ ခေါ်သည်。
"""
import argparse
import importlib.util
import json
import os
import shutil
import sys
import time

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_SRC = os.path.expanduser(os.environ.get("IKKI_SMOKE_SRC", "~/.ikki/smoke/headtop_60s.mp4"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEF_SRC)
    ap.add_argument("--recipe", default="headtop")
    ap.add_argument("--fmt", default="16:9")
    ap.add_argument("--keep", action="store_true", help="work/ နဲ့ ထွက်ဖိုင် ချန်")
    # ⚠️ ၆၀s clip မှာ IKKI ကတ်က gfx_share ဘောင် ပြည့်ပြီး beat နေရာ မကျန် ⇒ IKKI ကတ် လျှော့ပြီး beat ကို စစ်
    ap.add_argument("--over", default='{}', help="recipe override JSON")
    ap.add_argument("--run-py", default=os.path.join(R, "worker", "run.py"),
                    help="စမ်းမည့် worker/run.py (patch မတပ်ခင် ကော်ပီကို စမ်းရန်)")
    a = ap.parse_args()
    if not os.path.exists(a.src):
        print(f"⚠️ smoke clip မရှိ: {a.src}\n   talking-head 45–90s clip ကို ဒီနေရာ ထားပါ (သို့) --src")
        return 2
    sys.path.insert(0, os.path.join(R, "core"))
    sys.path.insert(0, os.path.join(R, "worker"))
    spec = importlib.util.spec_from_file_location("ikki_worker_run", a.run_py)
    W = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(W)          # ⚠️ main() က __main__ မှာသာ ⇒ job loop မစ
    jid = "j_5m0ke" + time.strftime("%H%M%S")
    src = os.path.join(W.SCRATCH, jid + "_src.mp4")
    shutil.copy(a.src, src)
    out = os.path.join(W.SCRATCH, jid + ".mp4")
    job = dict(id=jid, recipe=a.recipe, fmt=a.fmt, title="smoke", mode="auto", lang="my")
    W.REPORT.clear()
    t0 = time.time()
    ok, why = False, ""
    try:
        W.render(job, None, src, out, lambda n, name: print(f"  {n}/7 {name}", flush=True),
                 log=lambda s: print(s, flush=True), over=json.loads(a.over or "{}"))
        rep = W.REPORT
        qc = rep.get("qc")
        ok = qc == "PASS"
        why = qc or "qc မရှိ"
        try:
            import recipes as RC
            eng = (RC.get(a.recipe) or {}).get("engine")
        except Exception:
            eng = None
        if ok and eng == "beats":
            b = rep.get("beats") or {}
            ok = bool(b.get("ok")) and int(b.get("n") or 0) >= 1   # beat ≥1 ခု တကယ် ထွက်ရမည်
            why += f" · beats n={b.get('n')} ok={b.get('ok')}"
    except Exception as e:
        why = f"{type(e).__name__}: {e}"
    dt = time.time() - t0
    print("\n══ SMOKE " + ("PASS ✅" if ok else "FAIL ❌") + f" · {dt / 60:.1f} မိနစ် · {why}")
    try:
        os.makedirs(os.path.expanduser("~/.ikki"), exist_ok=True)
        json.dump(dict(ok=ok, why=why, t=time.time(), dur_s=round(dt), recipe=a.recipe,
                       report={k: W.REPORT.get(k) for k in ("qc", "beats", "remotion")}),
                  open(os.path.expanduser("~/.ikki/smoke_last.json"), "w"), ensure_ascii=False, default=str)
    except Exception:
        pass
    if not a.keep:
        for p in (src, out, os.path.join(W.SCRATCH, jid + "_w")):
            try:
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
            except OSError:
                pass
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
