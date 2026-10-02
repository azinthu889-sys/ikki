#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`assets/gfx_cutaway.txt` ကို **template အားလုံးရဲ့ တိုင်းချက်** ကနေ ပြန်ဆောက်

    python3 tools/gfx_cutaway_from_ypos.py [--write]

⚠️⚠️ ယခင် စာရင်းက `tools/gfx_cutaway.py` ကနေ ထွက်ပြီး အဲဒါက
   `assets/gfx_fullstage.txt` (၂၁၇ id) + `--bbox` ကိုသာ တိုင်းခဲ့သည် ⇒
   **template ၆၁၇ ခုလုံး မတိုင်းခဲ့**。 စာရင်းထဲ မပါသူတွေက overlay အဖြစ်
   ကမ်းလှမ်းခံရပြီး (က) 「နေရာ မတည့်」 နဲ့ ပယ်ခံ (ခ) `avoid` မရှိလျှင်
   ပြောသူကို **ဖုံး**သည်。
⚠️ **ဂိတ် မလျှော့ပါ** — `gfx_cutaway.py` ရဲ့ `COVER_MIN = 0.85` အတိုင်း。
   တွက်နည်းလည် အတူတူ (ဘောင်အပြည့်ပေါ် ချပြီး alpha ပျမ်းမျှ)。
⚠️ `--write` မပါလျှင် ဖိုင် မရေး。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YP = os.path.join(HERE, "assets", "gfx_ypos_9x16.json")
OUT = os.path.join(HERE, "assets", "gfx_cutaway.txt")
COVER_MIN = 0.85                      # ⚠️ gfx_cutaway.py နဲ့ တူညီရမည်


def main(argv):
    d = json.load(open(YP, encoding="utf-8"))
    it = d["items"]
    ok = {k: v for k, v in it.items() if v.get("ok")}
    old = [l.strip() for l in io.open(OUT, encoding="utf-8")
           if l.strip() and not l.startswith("#")]
    new = sorted(k for k, v in ok.items() if v["mass"] >= COVER_MIN)
    print("တိုင်းပြီး %d / %d · ဖုံးအုပ်မှု ≥ %.2f ⇒ **%d**"
          % (len(ok), len(it), COVER_MIN, len(new)))
    print("  ယခင် စာရင်း %d · ထဲမှ ကျန် %d · **အသစ် %d** · ဖယ် %d"
          % (len(old), len(set(old) & set(new)),
             len(set(new) - set(old)), len(set(old) - set(new))))
    # ⚠️ **ဖယ်မည့်သူကို ပြရမည်** — မတိုင်းရသေး၍ ဖယ်မိလျှင် ဖြတ်ပြောင်း ဆုံးရှုံးမည်
    drop = sorted(set(old) - set(new))
    for i in drop:
        r = it.get(i) or {}
        print("    ✖ ဖယ် %-28s %s" % (i, ("mass %.3f" % r["mass"])
                                      if r.get("ok") else
                                      "**မတိုင်းရ** (%s)" % str(r.get("why"))[:30]))
    # ⚠️⚠️ **ဖြည့်ရုံသာ — ဘယ်တော့မှ မဖယ်ရ**。 ၂၀၂၆-၁၀-၀၂ ပထမ ပြေးချက်မှာ
    #    `thm.media_*` ၁၁ ခု (mass ၀.၀၄–၀.၂၁) ဖယ်မည် ဟု ထွက်ခဲ့သည် —
    #    အဲဒါတွေက **ပုံ/ဗီဒီယို ထည့်ဖို့** template ဖြစ်ပြီး demo မှာ
    #    မီဒီယာ မပါသဖြင့် ဘောင်ဗလာ ဆွဲကာ mass နည်းခြင်း ဖြစ်သည် —
    #    ထုတ်လုပ်မှုမှာ B-roll ပုံနဲ့ **ဘောင်အပြည့်** ဖြစ်မည်。
    #    ⇒ တိုင်းချက်က 「ဖုံးအုပ်မှု နည်း」 ဟု ဆိုရုံနဲ့ ဖြတ်ပြောင်း
    #      တစ်ခုကို **ဆုံးရှုံးခံ၍ မရ**။ ဖယ်ရန်မှာ လူ ကြည့်ပြီးမှ。
    final = sorted(set(old) | set(new))
    print("  ⇒ **ဖြည့်ရုံသာ** (မဖယ်ပါ) ⇒ နောက်ဆုံး **%d**" % len(final))
    if drop:
        print("  ⓘ ဖုံးအုပ်မှု နည်းသူ %d ခု — ချန်ထားသည်、လူ စစ်ရန်" % len(drop))
    if "--write" in argv:
        with io.open(OUT, "w", encoding="utf-8") as f:
            f.write("# **ဖြတ်ပြောင်း (cutaway)** — ပြောသူကို တကယ် ဖုံးသူ。\n")
            f.write("# ထုတ်သူ: tools/gfx_cutaway_from_ypos.py — "
                    "`assets/gfx_ypos_9x16.json` ရဲ့ alpha ပျမ်းမျှ ≥ %.2f。\n"
                    % COVER_MIN)
            f.write("# ⚠️ template **၆၁၇ ခုလုံး** တိုင်းထားသည် "
                    "(ယခင်က gfx_fullstage.txt ၂၁၇ ခုသာ)。\n")
            f.write("# ⚠️ **ဖြည့်ရုံသာ** — ယခင်စာရင်းက တစ်ခုမှ မဖယ်ပါ。\n")
            f.write("# ⚠️ `thm.media_*` တို့က demo မှာ မီဒီယာ မပါ၍ "
                    "ဖုံးအုပ်မှု နည်းပြသည် — ထုတ်လုပ်မှုမှာ ဘောင်အပြည့်。\n")
            for i in final:
                f.write(i + "\n")
        print("ရေးပြီး — %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
