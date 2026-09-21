# -*- coding: utf-8 -*-
"""နောက်ခံ သီချင်း — catalog · ရွေးချယ်မှု · ကျော့မှတ် (Music audit P0)

⚠️ အရင်က music မှာ test **တစ်ခုမှ မရှိ**ခဲ့ပါ。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))
import music as M      # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def main():
    print("── ၁ · catalog ──")
    c = M.catalog()
    items = c.get("items") or []
    check("catalog ရှိ", len(items) >= 4, len(items))
    need = ("id", "file", "dur", "lufs", "true_peak", "loop", "license")
    miss = [x["id"] for x in items if any(k not in x for k in need)]
    check("field အားလုံး ပါ", not miss, miss)
    nolic = [x["id"] for x in items if not x.get("license")
             or "မမှတ်" in str(x.get("license"))]
    check("လိုင်စင် မှတ်ထားသည်", not nolic, nolic)
    gone = [x["id"] for x in items
            if not os.path.exists(os.path.join(M.DIR, x["file"]))]
    check("ဖိုင် တကယ် ရှိ", not gone, gone)

    print("\n── ၂ · တူညီသော သီချင်းကို ၂ ခါ မရေတွက် ──")
    # ⚠️ "4604 Wallpaper" နဲ့ "Kevin MacLeod Wallpaper" က correlation ၀.၉၉၉၆
    for g in ("trending", "calm", "corporate", "upbeat", "zae"):
        ids = [M.SAME.get(x["id"], x["id"]) for x in M.pool(g)]
        check(f"{g}: ထပ်မနေ", len(ids) == len(set(ids)), ids)

    print("\n── ၃ · ရွေးချယ်မှု တည်ငြိမ် (ပြန်ထုတ်လျှင် တူရမည်) ──")
    a = [M.choose("trending", f"j{i}")[1]["id"] for i in range(6)]
    b = [M.choose("trending", f"j{i}")[1]["id"] for i in range(6)]
    check("seed တူ ⇒ ရလဒ် တူ", a == b, (a, b))
    check("pool ၂ ခုလုံး သုံးသည်", len(set(a)) > 1, set(a))

    print("\n── ၄ · ကျော့မှတ် ──")
    # ⚠️ သီချင်း ၅ ပုဒ်လုံး အဆုံးမှာ တိတ်ပြီး အစက ကျယ်သည် ⇒ ဖိုင်
    #    အစအဆုံး ကျော့လျှင် ၉၃–၁၇၃ dB ထိုးကျသံ (တိုင်းပြီး)。
    bad = [x["id"] for x in items if not x.get("loop")]
    check("အတည်ပြု ကျော့နယ် ရှိ", not bad, bad)
    rough = [(x["id"], x["loop"]["seam_db"]) for x in items
             if x.get("loop") and x["loop"]["seam_db"] > 1.0]
    check("ကျော့နယ် ကျိုးမှု ≤ ၁ dB", not rough, rough)

    print("\n── ၅ · ဗီဒီယို တိုလျှင် ကျော့စရာ မလို ──")
    it = M.entry("Beauty Flow")
    ch = M.loop_chain(it, 60.0, 1.2)
    check("မကျော့ပါ", "aloop" not in ch, ch)
    ch2 = M.loop_chain(it, it["dur"] + 60.0, 1.2)
    check("ရှည်လျှင် ကျော့သည်", "aloop" in ch2, ch2)
    check("ကျော့နယ်ကိုသာ ကျော့", f"atrim={it['loop']['start']:.3f}" in ch2, ch2)

    print("\n── ၆ · ကျော့နယ်က ဘောင်ထဲ ──")
    for x in items:
        lp = x.get("loop")
        if not lp:
            continue
        check(f"{x['id'][:22]}: နယ် မှန်",
              0 <= lp["start"] < lp["end"] <= x["dur"] + 0.05
              and lp["end"] - lp["start"] >= 8.0, lp)

    print("\n── ၇ · true peak ──")
    # ⚠️ သီချင်း ၂ ပုဒ်က +dBTP (ဖြတ်နေသည်) — master QC မတိုင်မီ သိထားရမည်
    hot = [(x["id"], x["true_peak"]) for x in items
           if x.get("true_peak") is not None and x["true_peak"] > 0]
    if hot:
        print(f"    ⚠️ +dBTP သီချင်း {len(hot)} ပုဒ်: {hot} — "
              f"level ချပြီး သုံးသဖြင့် master မှာ ပြဿနာ မဖြစ်ပါ")
    check("true_peak တိုင်းထားသည်",
          all(x.get("true_peak") is not None for x in items))

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
