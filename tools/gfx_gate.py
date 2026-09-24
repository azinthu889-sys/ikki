#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`assets/gfx_ok.txt` ကို **တိုင်းလို့ရသော ဂိတ် ၂ ခု**ဖြင့် ပြန်ဆောက်သည်。

⚠️ ယခင် ဂိတ် (`tools/gfx_pool.py`) က gradient သိပ်သည်းမှုနဲ့ 「စာသား ပါလား」
   ခန့်မှန်းခဲ့ပြီး **ကောင်း/ဆိုး ကိန်းတွေ ထပ်နေသဖြင့် မယုံရ**ဟု သူကိုယ်တိုင်
   မှတ်ထားသည် (`--write` မသုံးရ)。 ⇒ ဤမှာ **ခန့်မှန်းချက် လုံးဝ မသုံး** —
   တိုင်းလို့ရတာ နှစ်ခုကိုသာ စစ်သည်:

     ဂိတ် ① render ဖြစ်ရမည် · ဖရိမ်း ≥၂ · နောက်ဆုံး ဖရိမ်းမှာ မှင် ≥၀.၀၅%
            (`gfx_verify.json` ရဲ့ `ok`)
     ဂိတ် ② **စာတန်းဇုန် မဖုံးရ** — bbox ရဲ့ အောက်စွန်းက `CAP_TOP` အထက်
            ဖြစ်ရမည်。 IKKI က စာတန်းကို `cap_base=0.92` မှာ ချပြီး အမြင့်
            ~၀.၁၃ ⇒ ၀.၇၉ ကနေ အောက် စာတန်း ယူထားသည် (`place.caption_band`)。
            ⚠️ `place.caption_band()` က **keyword pop အတွက်သာ** သုံးနေပြီး
               template event ကို run-time မှာ မစစ်ပါ ⇒ ဒီမှာ ကြိုဖယ်ရမည်。

⚠️ **ကျဉ်းလိုက်တာကို အစီရင်ခံရမည်** — အရင်က ပါပြီး ယခု ကျသွားသူများကို
   သီးသန့် ပြသည်。 တိတ်တဆိတ် မဖယ်ရ。
"""
import os, sys, json, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP_TOP = 0.79            # စာတန်း ယူထားသော ဇုန်၏ အပေါ်စွန်း
VJ = os.path.join(HERE, "assets", "gfx_verify.json")
OK = os.path.join(HERE, "assets", "gfx_ok.txt")
# ⚠️ ဂိတ်③ — `tools/gfxtextsens.py` ရဲ့ တိုင်းချက် (မရှိလျှင် ကျော်သည်)
TS = os.path.join(HERE, "assets", "gfx_textsens.json")

HEAD = """# motionkit template — **တစ်ခုချင်း တကယ် render ပြီး စစ်ပြီးသား** စာရင်း。
# ထုတ်သူ: tools/gfx_gate.py  ({n} ခု)
# ⚠️ ဂိတ် ၂ ခု — ခန့်မှန်းချက် မပါ、တိုင်းလို့ရတာချည်း:
#      ① render ဖြစ် · ဖရိမ်း ≥၂ · နောက်ဆုံး ဖရိမ်းမှာ မှင် ≥၀.၀၅%
#      ② bbox အောက်စွန်း < {cap} ·H — စာတန်းဇုန် မဖုံးရ
#      ③ **ကျွန်တော်တို့ စာသားကို တကယ် ရေးရမည်** — စာသား ၂ မျိုးနဲ့ render
#         လုပ်ပြီး ပုံရိပ် ပြောင်းမပြောင်း တိုင်းသည် (`gfxtextsens.py`)
# ⚠️ bbox မသိသေးသူကို **ဖယ်မထားပါ** (ဂိတ် ① အောင်လျှင် ထည့်) — ဒါပေမယ့်
#    အောက်က မှတ်ချက်မှာ ရေတွက် ပြထားသည်; full pass ပြန်ပြေးပြီး ဖြည့်ပါ。
"""


def main():
    write = "--write" in sys.argv
    try:
        rows = json.load(open(VJ, encoding="utf-8"))
    except OSError:
        print("gfx_verify.json မရှိ — tools/gfx_verify.py အရင် ပြေးပါ"); return 1
    old = set()
    try:
        old = {l.strip() for l in open(OK, encoding="utf-8")
               if l.strip() and not l.lstrip().startswith("#")}
    except OSError:
        pass

    # ⚠️ **ဘောင်အပြည့် template ကို ဂိတ်②နဲ့ မပယ်ရ** — `prem.hero_line` လို
    #    title card တွေက ဘောင်တစ်ခုလုံး (၀.၀၀–၀.၉၉) ယူတာ **ဒီဇိုင်းအရ မှန်**သည်;
    #    overlay မဟုတ်ဘဲ **full-stage** အဖြစ် သုံးရမည်。 ⇒ ခွဲမှတ်ပြီး
    #    `assets/gfx_fullstage.txt` ထဲ ထည့်သည် — planner က `_layout="full"`
    #    လမ်းကြောင်းသို့ ပို့ရန်。 overlay တွေကိုသာ စာတန်းဇုန်နဲ့ တိုက်သည်。
    def _isfull(b):
        return (b.get("top", 1) < 0.08 and b.get("bottom", 0) > 0.92
                and b.get("left", 1) < 0.08 and b.get("right", 0) > 0.92)

    # ⚠️ ဂိတ်③ — စစ်ပြီးသားမှသာ သုံးသည်。 မစစ်ရသေးသူကို 「ကျ」ဟု
    #    **မသတ်မှတ်ရ** (မသိတာနဲ့ ကျတာ မတူ)。
    ts = {}
    try:
        ts = {r["id"]: r for r in (json.load(open(TS, encoding="utf-8")) or [])
              if r.get("id")}
    except OSError:
        pass

    keep, g1_fail, g2_fail, g3_fail, nobb, full = [], [], [], [], 0, []
    for r in rows:
        if not r.get("ok"):
            g1_fail.append(r["id"]); continue
        _t = ts.get(r["id"])
        if _t is not None and not _t.get("ok"):
            g3_fail.append((r["id"], str(_t.get("why") or "")[:44])); continue
        bb = r.get("bbox")
        if not bb:
            nobb += 1; keep.append(r["id"]); continue
        if _isfull(bb):
            full.append(r["id"]); keep.append(r["id"]); continue
        if float(bb.get("bottom") or 0) >= CAP_TOP:
            g2_fail.append((r["id"], bb["bottom"])); continue
        keep.append(r["id"])
    keep = sorted(set(keep)); full = sorted(set(full))

    print("စစ်ချက် %d ခု" % len(rows))
    print("  ဂိတ်① render ကျ      %3d" % len(g1_fail))
    print("  ဂိတ်② စာတန်းဇုန်ဖုံး  %3d" % len(g2_fail))
    print("  ဂိတ်③ စာသား မရေး     %3d  (စစ်ပြီး %d / မစစ်ရသေး %d)"
          % (len(g3_fail), len(ts), sum(1 for r in rows
                                        if r.get("ok") and r["id"] not in ts)))
    print("  bbox မသိသေး          %3d  (ဂိတ်② မစစ်ရသေး)" % nobb)
    print("  ဘောင်အပြည့် (full-stage) %3d  — ဂိတ်② ကင်းလွတ်" % len(full))
    print("  ⇒ **အောင် %d**" % len(keep))
    if g3_fail:
        print("\n  စာသား မရေးသူ (ဂိတ်③):")
        for i, w in g3_fail[:15]:
            print("     %-30s %s" % (i, w))
        if len(g3_fail) > 15:
            print("     … နောက်ထပ် %d ခု" % (len(g3_fail) - 15))
    if g2_fail:
        print("\n  စာတန်းဇုန် ဖုံးသူ (အောက်စွန်း ·H):")
        for i, b in sorted(g2_fail, key=lambda x: -x[1])[:15]:
            print("     %-30s %.3f" % (i, b))
    lost = sorted(old - set(keep))
    if lost:
        print("\n  ⚠️ အရင်က ပါပြီး **ယခု ကျသွားသူ %d**:" % len(lost))
        for i in lost[:20]:
            r = next((x for x in rows if x["id"] == i), None)
            print("     %-30s %s" % (i, (r or {}).get("why", "စစ်ချက်ထဲ မပါ")))
    new = sorted(set(keep) - old)
    print("\n  ✅ အသစ် ဝင်လာ %d" % len(new))
    print("     module အလိုက်:", dict(collections.Counter(i.split(".")[0] for i in new)))

    if write:
        with open(OK, "w", encoding="utf-8") as f:
            f.write(HEAD.format(n=len(keep), cap=CAP_TOP))
            f.write("\n".join(keep) + "\n")
        print("\n  ရေးပြီး → %s (%d)" % (OK, len(keep)))
        _fs = os.path.join(HERE, "assets", "gfx_fullstage.txt")
        with open(_fs, "w", encoding="utf-8") as f:
            f.write("# ဘောင်အပြည့် ဖုံးသော template — **overlay အဖြစ် မသုံးရ**。\n"
                    "# planner က `_layout=\"full\"` (full-stage / cutaway) သို့ ပို့ရမည်。\n"
                    "# ထုတ်သူ: tools/gfx_gate.py — bbox တိုင်းချက်ကနေ (မှန်းမရေး)。\n")
            f.write("\n".join(full) + "\n")
        print("  ရေးပြီး → %s (%d)" % (_fs, len(full)))
    else:
        print("\n  (စမ်းကြည့်ရုံ — ရေးရန် `--write`)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
