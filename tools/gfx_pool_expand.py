#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`assets/gfx_ok.txt` ကို **တိုင်းချက် ၂ ခုလုံး အောင်သူ** တွေနဲ့ ချဲ့သည်။

    python3 tools/gfx_pool_expand.py [--write]

⚠️ ဂိတ် **၂ ခုလုံး** အောင်မှ ထည့်သည် —
     ① `assets/gfx_verify.json`   — တကယ် render ဖြစ်ပြီး မှင် ရှိ
     ② `assets/gfx_textsens.json` — **ကျွန်တော်တို့ စာသားကို တကယ် ရေး**
⚠️ ② မပါဘဲ ချဲ့ခဲ့လျှင် အရောင်တုံးချည်း template တွေ ဝင်လာပြီး ဗီဒီယိုထဲ
   အဓိပ္ပာယ်မဲ့ ကွက် ဖြစ်မည် (Zin ၂၀၂၆-၀၉-၂၀: 「template သုံးထားတာတွေရော
   quality 0」)。 ⇒ **`gfx_textsens.json` မစစ်ရသေးသော id ကို မထည့်ရ**。
⚠️ ရှိပြီးသား စာရင်းကို **မဖျက်ရ** — ပေါင်းသာ ထည့်သည်。 (၂၀၂၆-၀၉-၂၃ မှာ
   spot-check တစ်ခုက `gfx_verify.json` ကို ၁၇၂ ⇒ ၂ အဖြစ် လွှမ်းခဲ့ဖူးသည်။)
⚠️ `--write` မပါလျှင် **ဘာမှ မရေး** — ပြရုံသာ。
"""
import json, os, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OK = os.path.join(HERE, "assets", "gfx_ok.txt")
VER = os.path.join(HERE, "assets", "gfx_verify.json")
SENS = os.path.join(HERE, "assets", "gfx_textsens.json")


def _load(p):
    try:
        return json.load(open(p, encoding="utf-8")) or []
    except Exception:
        return []


def main():
    write = "--write" in sys.argv
    ver = {r["id"]: r for r in _load(VER) if r.get("id")}
    sens = {r["id"]: r for r in _load(SENS) if r.get("id")}
    if not sens:
        print("✖ `gfx_textsens.json` မရှိ — `tools/gfxtextsens.py` အရင် ပြေးပါ")
        return 2

    lines = open(OK, encoding="utf-8").read().split("\n") if os.path.exists(OK) else []
    head = [l for l in lines if l.startswith("#")]
    cur = sorted({l.strip() for l in lines
                  if l.strip() and not l.startswith("#")})

    ver_ok = {k for k, r in ver.items() if r.get("ok")}
    sens_ok = {k for k, r in sens.items() if r.get("ok")}
    both = ver_ok & sens_ok
    new = sorted(both - set(cur))
    # ⚠️ ရှိပြီးသားထဲက **စာသား မရေးမှန်း တိုင်းမိသူ** — သတိပေးရုံ (မဖယ်ပါ)
    bad = sorted(k for k in cur if k in sens and not sens[k].get("ok"))

    print(f"gfx_verify  ok {len(ver_ok)}/{len(ver)}")
    print(f"gfx_textsens ok {len(sens_ok)}/{len(sens)}")
    print(f"၂ ခုလုံး အောင်  {len(both)}")
    print(f"လက်ရှိ pool   {len(cur)}")
    print(f"ထပ်ထည့်နိုင်   {len(new)}  ⇒ စုစုပေါင်း {len(cur) + len(new)}")
    for k in new[:14]:
        r = sens.get(k, {})
        print(f"   + {k:34s} diff={r.get('diff')} aa={r.get('aa')}")
    if len(new) > 14:
        print(f"   … နောက်ထပ် {len(new)-14} ခု")
    if bad:
        print(f"\n⚠️ လက်ရှိ pool ထဲမှာ **စာသား မရေး**ဟု တိုင်းမိသူ {len(bad)} ခု —")
        print("   (အလိုအလျောက် မဖယ်ပါ — Zin ဆုံးဖြတ်ရန်)")
        for k in bad[:12]:
            print(f"   ? {k:34s} {str(sens[k].get('why'))[:46]}")

    if not write:
        print("\n(ပြရုံသာ — တကယ် ရေးရန် `--write`)")
        return 0
    if not new:
        print("\nထပ်ထည့်စရာ မရှိ")
        return 0
    # ⛔ ၂၀၂၆-၀၉-၂၆ Zin ဆုံးဖြတ်ချက် — `gfx_ok.txt` ရဲ့ **တစ်ခုတည်းသော**
    #    ရေးသူက `tools/gfx_gate.py`。 ဒီ script မှာ ဂိတ် မပါ · `.bak` မချန် ·
    #    provenance မမှတ် ⇒ ရေးလမ်း ဖယ်လိုက်သည် (တိုင်းချက် ပြရုံ ကျန်သည်)。
    #    ရေးသူ ၃ ခု ကျန်နေလျှင် `gfx_size_16x9.json` လွှမ်းမိမှု အမျိုးအစား
    #    ထပ်ဖြစ်မည် — ပိုင်ရှင် တစ်ခုတည်း ဖြစ်ရမည်。
    print("\n⛔ ဒီ script က **မရေးပါ** — `gfx_ok.txt` ရဲ့ ရေးသူက")
    print("   `tools/gfx_gate.py` တစ်ခုတည်း (ဂိတ် ၃ ခု + provenance ပါသည်)。")
    print("   ပြေးရန်: python3 tools/gfx_gate.py --write")
    return 1


if __name__ == "__main__":
    sys.exit(main())
