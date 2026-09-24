#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ပျက်နေသော template များအတွက် **ပြင်ရန် အလုပ်စာရင်း** ထုတ်သည်။

    python3 tools/gfx_fixlist.py [--out PATH]

⚠️ `IKKI_CONTRACT.md` က **အသစ် ဆောက်မယ့်အခါ** လိုက်နာရန် စာချုပ် ဖြစ်သည်။
   ဤဖိုင်က **ရှိပြီးသား ပျက်နေတာတွေကို ပြင်ရန်** အလုပ်စာရင်း — id တိုင်း
   တိုင်းချက်ကနေ တိုက်ရိုက် ထုတ်ထားသည် (လက်နဲ့ မရေး ⇒ မှားစရာ မရှိ)。
⚠️ **ပြင်လို့ မရသူကို သီးသန့် ခွဲ**ထားသည် — စာသားကို လျစ်လျူရှုသော
   အလှဆင် template တွေက ပြင်စရာ မဟုတ်ဘဲ **ချန်ထားရန်** ဖြစ်သည်
   (Zin ၂၀၂၆-၀၉-၂၄: 「၅၆ ခုကို ချန်ထား」)。
"""
import json, os, sys, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TS = os.path.join(HERE, "assets", "gfx_textsens.json")
VJ = os.path.join(HERE, "assets", "gfx_verify.json")
OK = os.path.join(HERE, "assets", "gfx_ok.txt")

# (အုပ်စု အမည်, ပြင်နည်း, စာချုပ် အပိုဒ်, စာသားထဲ ရှာမည့် သော့)
GROUPS = [
    ("အတွဲ (rows) လိုသည်",
     "slot ကို `rows` ဟု အမည်ပေးပြီး `[(str, float), …]` လက်ခံပါ။ "
     "flat စာရင်းဆိုလျှင် `items` ဟု အမည်ပေးပါ။", "§၁",
     ("unpack", "multiply sequence", "not supported between",
      "unsupported operand")),
    ("argument မပြည့်",
     "required parameter ကို လျှော့ပါ — `tag` + စာသား ၁ ခု သာ၊ "
     "ကျန်အားလုံး default ထားပါ။", "§၂",
     ("missing", "argument")),
    ("ကျပန်း (random)",
     "`tag` ကနေ seed ထုတ်ပါ — `Random(md5(tag))`။ "
     "ပြန်ထုတ်တိုင်း ရလဒ် တူရမည်။", "§၅",
     ("မတည်ငြိမ်",)),
    ("နှေးလွန်း",
     "clip ၂–၃s ကို ၃၀s အတွင်း render ဖြစ်ရမည် — ဖရိမ်းတိုင်း SVG အပြည့် "
     "ပြန်မဆောက်ဘဲ `statics` ကို သုံးပါ။", "§၁၀",
     ("ကျော်",)),
    ("ဆောက်ရင်း ကျ (အခြား)",
     "template ကို `tools/gfxtextsens.py --only <id>` နဲ့ ပြေးပြီး "
     "traceback ကို ကြည့်ပါ — အများစုက argument အမျိုးအစား လွဲနေခြင်း။", "§၁·§၂",
     ("Error", "error", "ဗလာ", "invalid literal", "index out of range",
      "concatenate", "not all arguments")),
]

SKIP = ("ပုံရိပ် မပြောင်း",)          # ⚠️ ပြင်စရာ မဟုတ် — ချန်ထားရန်


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    ts = {r["id"]: r for r in json.load(open(TS, encoding="utf-8"))}
    vj = {r["id"]: r for r in json.load(open(VJ, encoding="utf-8"))}
    pool = {l.strip() for l in open(OK, encoding="utf-8")
            if l.strip() and not l.startswith("#")}

    bad = {k: r for k, r in ts.items() if not r.get("ok")}
    skip, used = {}, set()
    for k, r in bad.items():
        if any(s in str(r.get("why") or "") for s in SKIP):
            skip[k] = r; used.add(k)

    L = []
    A = L.append
    A("# Motion Kit — **ပြင်ရန် အလုပ်စာရင်း**")
    A("")
    A("⚠️ ဤစာရင်းက `tools/gfx_fixlist.py` နဲ့ **တိုင်းချက်ကနေ တိုက်ရိုက်**")
    A("   ထုတ်ထားသည် — လက်နဲ့ မရေးပါ။ ပြင်ပြီးတိုင်း ပြန်ထုတ်ပါ။")
    A("⚠️ ပြင်နည်း အသေးစိတ်ကို `IKKI_CONTRACT.md` ရဲ့ အပိုဒ်နံပါတ်မှာ ကြည့်ပါ။")
    A("")
    A(f"catalog **{len(vj)}** · တိုင်းပြီး **{len(ts)}** · "
      f"IKKI သုံးနိုင် **{len(pool)}** · ပြင်စရာ **{len(bad)-len(skip)}** · "
      f"ချန်ထား **{len(skip)}**")
    A("")

    for name, how, sec, keys in GROUPS:
        ids = sorted(k for k, r in bad.items()
                     if k not in used
                     and any(x in str(r.get("why") or "") for x in keys))
        if not ids:
            continue
        used.update(ids)
        A(f"## {name} — **{len(ids)} ခု**  ({sec})")
        A("")
        A(f"**ပြင်နည်း** — {how}")
        A("")
        by = collections.defaultdict(list)
        for i in ids:
            by[i.split(".")[0]].append(i)
        for mod in sorted(by):
            A(f"- `{mod}.py` — " + " · ".join(f"`{i.split('.',1)[1]}`"
                                              for i in sorted(by[mod])))
        A("")

    rest = sorted(k for k in bad if k not in used)
    if rest:
        A(f"## အမျိုးအစား မခွဲရသေး — **{len(rest)} ခု**")
        A("")
        for i in rest:
            A(f"- `{i}` — {str(bad[i].get('why'))[:70]}")
        A("")

    A(f"## ⏸ ချန်ထားရန် — **{len(skip)} ခု** (ပြင်စရာ မဟုတ်)")
    A("")
    A("စာသား ပြောင်းလည်း ပုံရိပ် မပြောင်းသော **အလှဆင်/နောက်ခံ** template များ။")
    A("IKKI က စာသား ပြရန် သုံးသဖြင့် ဤအမျိုးအစား မလိုပါ — ဆောက်ထားတာ")
    A("မှားသည် မဟုတ်၊ **အသုံးဝင်ရာ နေရာ ကွဲ**သည်။ `category` မှာ `decor` ဟု")
    A("မှတ်ပေးလျှင် IKKI က တိတ်တဆိတ် ကျော်သွားမည်。")
    A("")
    by = collections.defaultdict(list)
    for i in sorted(skip):
        by[i.split(".")[0]].append(i)
    for mod in sorted(by):
        A(f"- `{mod}.py` — {len(by[mod])} ခု: "
          + " · ".join(f"`{i.split('.',1)[1]}`" for i in sorted(by[mod])[:8])
          + (" …" if len(by[mod]) > 8 else ""))
    A("")

    txt = "\n".join(L)
    if out:
        open(out, "w", encoding="utf-8").write(txt)
        print(f"ရေးပြီး — {out} ({len(L)} လိုင်း)")
    else:
        print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
