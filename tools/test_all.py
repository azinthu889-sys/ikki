#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI ရဲ့ **test အားလုံး** — `python3 tools/test_all.py`

⚠️ `python -m unittest discover` က **test ၀ ခု** ပြေးပြီး `OK` ပြသည် —
   ဒီ repo ရဲ့ test တွေက `unittest.TestCase` မဟုတ်ဘဲ `main()` ပြန်ပေးသော
   script များ ဖြစ်၍ discover က ဘာမှ မတွေ့ပါ。 「ဘာမှ မပြေးဘဲ OK」က
   test မရှိတာထက် ဆိုးသည် — မှားနေတာကို အောင်နေသလို ပြသဖြင့်。
   ⇒ ဤ runner က ဖိုင်တိုင်းကို **သီးသန့် process** နဲ့ ပြေးပြီး
     exit code ကို စုသည်。

⚠️ သီးသန့် process ဖြစ်ရမည် — test တွေက `sys.path` ကို ကွဲပြားစွာ
   ထည့်ကြပြီး module cache မျှလျှင် တစ်ခုက နောက်တစ်ခုကို ထိခိုက်သည်
   (core/ flat နဲ့ package လမ်းကြောင်း ၂ မျိုး ရှိသည်)。
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TESTS = os.path.join(ROOT, "tests")


def run(path, verbose=False):
    t0 = time.time()
    r = subprocess.run([sys.executable, path], capture_output=True, text=True)
    dt = time.time() - t0
    return r.returncode, r.stdout, r.stderr, dt


def main(argv):
    verbose = "-v" in argv
    only = [a for a in argv[1:] if not a.startswith("-")]
    files = sorted(f for f in os.listdir(TESTS)
                   if f.startswith("test_") and f.endswith(".py"))
    if only:
        files = [f for f in files if any(o in f for o in only)]
    if not files:
        print("⛔ test ဖိုင် မတွေ့ပါ")
        return 2
    bad, tot = [], 0.0
    print(f"── test {len(files)} ဖိုင် ──")
    for f in files:
        code, out, err, dt = run(os.path.join(TESTS, f), verbose)
        tot += dt
        # ⚠️ exit code ကို **အဓိက** ယူသည် — စာသား ရှာတာ မဟုတ်。
        #    ("အောင်" ဟု ရေးထားပြီး exit 1 ပြန်တာမျိုး ဖမ်းရန်)
        ok = (code == 0)
        n = "—"
        for ln in out.splitlines():
            if "✓" in ln and "အားလုံး" in ln:
                n = "အားလုံး အောင်"
        print(f"  {'✓' if ok else '✗'} {f:28} {dt:5.1f}s  {n if ok else 'ကျသည်'}")
        if not ok:
            bad.append(f)
            for ln in (out.splitlines() + err.splitlines()):
                if "✗" in ln or "Error" in ln or "Traceback" in ln:
                    print(f"      {ln.strip()[:150]}")
        elif verbose:
            print("      " + "\n      ".join(out.splitlines()))
    print(f"\n  ကြာချိန် {tot:.1f}s")
    if bad:
        print(f"  ✗ ကျသည် {len(bad)}/{len(files)}: {', '.join(bad)}")
        return 1
    print(f"  ✓ {len(files)}/{len(files)} အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
