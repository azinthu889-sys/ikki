#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`assets/gfx_qual.json` မှ **သုံးနိုင်သော template စာရင်း** ပြန်ဆောက်သည်。

⚠️ ယခင် ဂိတ် (`gfx_verify.py`) က `alpha` ဖုံးအုပ်မှုပဲ တိုင်းသဖြင့် **အရောင်တုံး
   ချည်းပဲ ပါပြီး စာသား လုံးဝ မပါသော** template များ အောင်သွားခဲ့သည်
   (၂၀၂၆-၀၉-၂၀ · Zin: 「template သုံးထားတာတွေရော quality 0」)。

⛔ **၂၀၂၆-၀၉-၂၀: ဤ ဂိတ်က မယုံရ — အလိုအလျောက် မရေးရ။**
   gradient အချိုးက 「စာသား ပါ」 နဲ့ 「ပုံစံ ရှုပ်」 ကို မခွဲနိုင်။ တိုင်းထားသော
   ကောင်း/ဆိုး နမူနာ ၁၄ ခုမှာ ကိန်းတွေ **ထပ်နေသည်** —
     ဆိုး: ၀.၀၀၀ · ၀.၀၀၁ · ၀.၀၀၈ · ၀.၀၁၇ · ၀.၀၃၆ · ၀.၀၄၈
     ကောင်း: ၀.၀၂၁ · ၀.၀၂၂ · ၀.၀၆၇ · ၀.၁၃၁ · ၀.၂၅၀ · ၀.၇၅၀
   (`charts.ranking` က အဝါစက် တစ်ခုတည်းနဲ့ ၀.၀၄၈ · `qcard.lower_quote` က
    စာသား ဖတ်လို့ရလျက် ၀.၀၂၁)。 scanline အပြောင်းအလဲ နည်းလည်း မအောင် —
   `kin4.push_up` က စာသားပါလျက် ၀ ရသည်。
   ⇒ `assets/gfx_qual.json` ကို **လူကိုယ်တိုင် ကြည့်ရန် ညွှန်းချက်**အဖြစ်သာ
     သုံးပါ。 `--write` ကို **မသုံးရ**。

ဂိတ် (မအောင်မြင်ခဲ့သော စမ်းသပ်ချက် — မှတ်တမ်းအဖြစ် ချန်ထားသည်):
  ① render ဖြစ်ရမည် (`ok`)
  ② **စာသား ရှိရမည်** — gradient သိပ်သည်းမှု `detail ≥ 0.030`
     (အရောင်တုံး ၀.၀၀၀–၀.၀၁၆ · စာသားပါ ၀.၀၄၈–၀.၂၉၈ ဟု တိုင်းထားသည်)
  ③ **ဘောင်ပြင် မထွက်ရ** — Vision က စာသား တွေ့လျှင် `vedge ≥ 0.005`
     (Vision မတွေ့လျှင် မြန်မာစာ ဖြစ်နိုင်၍ ဤစစ်ချက် ကျော်သည်)
"""
import os, sys, json, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DETAIL_MIN = 0.030
VEDGE_MIN  = 0.005
HEAD = """# motionkit template — **တစ်ခုချင်း တကယ် render ပြီး စစ်ပြီးသား** စာရင်း。
# ⚠️ ဂိတ် (`tools/gfx_pool.py` · ၂၀၂၆-၀၉-၂၀ ပြန်ဆောက်):
#      ① render ဖြစ်ရမည်
#      ② **စာသား ရှိရမည်** — gradient သိပ်သည်းမှု ≥ {d}
#         (`alpha` ဖုံးအုပ်မှုနဲ့ တိုင်းလျှင် အရောင်တုံးကြီးက အောင်သွားသည်)
#      ③ **ဘောင်ပြင် မထွက်ရ** — Vision က စာသား တွေ့လျှင် အနား ≥ {v}
# ⚠️ Vision OCR က **မြန်မာစာ မဖတ်နိုင်** ⇒ စာသား ရှိမရှိကို gradient နဲ့ တိုင်းသည်。
# ⚠️ စာရင်း (list) argument ယူသော template များ၏ ပုံစံကို
#    `assets/gfx_args.json` ထဲ မှတ်ထားသည် (`tools/gfx_args.py`)。
""".format(d=DETAIL_MIN, v=VEDGE_MIN)


def verdict(r):
    if not r.get("ok"): return False, r.get("why", "render မဖြစ်")
    d = r.get("detail")
    if d is None: return False, "မတိုင်းရ"
    if d < DETAIL_MIN: return False, f"စာသား မပါ (detail {d})"
    vn, ve = r.get("vn", 0), r.get("vedge", -1)
    if vn and vn > 0 and ve is not None and 0 <= ve < VEDGE_MIN:
        return False, f"ဘောင်ပြင် ထွက် (edge {ve})"
    return True, ""


def main():
    qp = os.path.join(HERE, "assets", "gfx_qual.json")
    rows = json.load(open(qp, encoding="utf-8"))
    ok, bad = [], []
    for r in rows:
        good, why = verdict(r)
        (ok if good else bad).append((r["id"], why))
    ok.sort()
    # ⛔ ဂိတ် မယုံရ (အထက် မှတ်ချက်) — `--write` ကို ပိတ်ထားသည်
    dry = True if "--i-know-this-gate-is-unreliable" not in sys.argv else ("--write" not in sys.argv)
    print(f"  တိုင်းထား {len(rows)} · အောင် {len(ok)} · ကျ {len(bad)}")
    c = collections.Counter(w.split(" (")[0] for _i, w in bad)
    for k, n in c.most_common(): print(f"    ✖ {k:28} {n}")
    print("\n  module အလိုက် အောင်:")
    m = collections.Counter(i.split(".")[0] for i, _w in ok)
    print("   ", dict(m.most_common(14)))
    if dry:
        print("\n  (စမ်းကြည့်ရုံသာ — တကယ် ရေးရန် `--write`)")
        return
    p = os.path.join(HERE, "assets", "gfx_ok.txt")
    old = set()
    if os.path.exists(p):
        old = {l.strip() for l in open(p, encoding="utf-8")
               if l.strip() and not l.startswith("#") and "." in l}
        import shutil, time
        shutil.copy(p, p + f".bak{int(time.time())}")
    with open(p, "w", encoding="utf-8") as f:
        f.write(HEAD)
        for i, _w in ok: f.write(i + "\n")
    new = {i for i, _w in ok}
    print(f"\n  ရေးပြီး — {p}")
    print(f"  ထပ်ဝင် {len(new - old)} · ဖယ်လိုက် {len(old - new)}")
    if old - new:
        print("  ဖယ်လိုက်သည်:", sorted(old - new)[:12], "…")


if __name__ == "__main__":
    main()
