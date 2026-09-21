"""planner.sfx_plan — semantic SFX (P0)

⚠️ schema မှာ `sfxEvents` ရှိပါလျက် planner က **တစ်ခါမှ မထုတ်ခဲ့**ပါ ·
   worker ကလည်း `execute.to_sfx()` **မခေါ်ခဲ့**ပါ ⇒ semantic sound design
   လုံးဝ မဖြစ်ခဲ့ပါ (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့)。
⚠️ P0 မှာ **ဂိတ် မထိရ** — `qc.SFX_MAX_PER_MIN` ၁.၅ · `SFX_MIN_GAP` ၈s
   ဖြစ်နေဆဲ ⇒ ထုတ်ချက်က အဲဒီဘောင်ထဲ ရှိရမည်。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))
sys.path.insert(0, os.path.join(HERE, ".."))

import planner as PL      # noqa: E402
import execute as EX      # noqa: E402
import qc as QC           # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def ev(i, at, kind="card"):
    return dict(id=f"t{i}", startTime=at, endTime=at + 3.0,
                layer="template", type="template",
                motionKitTemplateId="prem4.big_question", props={},
                style=dict(kind=kind),
                reason="t", confidence=0.7)


def main():
    print("── ၁ · ဖြစ်ရပ်ပေါ်မှာသာ ──")
    out = PL.sfx_plan([ev(i, i * 12.0) for i in range(5)], 60.0, 1.5)
    check("ဂရပ်ဖစ် မရှိလျှင် ဗလာ", PL.sfx_plan([], 60.0, 1.5) == [])
    check("အရှည် ၀ ဆိုလျှင် ဗလာ", PL.sfx_plan([ev(0, 1)], 0, 1.5) == [])
    check("ထုတ်သည်", len(out) > 0, out)

    print("\n── ၂ · ဂိတ် မကျော်ရ ──")
    moments = sorted({round(e["startTime"], 1) for e in out})
    # ⚠️ အထပ်တွေက **အခိုက်တစ်ခု** — `dress` ရဲ့ LAYER_W နဲ့ တစ်သဘောတည်း
    grp, last = [], -99.0
    for t in moments:
        if t - last > 0.6:
            grp.append(t); last = t
    per = len(grp) / (60.0 / 60.0)
    check(f"မိနစ်နှုန်း {per:.2f} ≤ {QC.SFX_MAX_PER_MIN}",
          per <= QC.SFX_MAX_PER_MIN + 1e-9, per)
    gaps = [b - a for a, b in zip(grp, grp[1:])]
    check(f"ကွာဟချက် ≥ {QC.SFX_MIN_GAP}s",
          all(g >= QC.SFX_MIN_GAP - 1e-6 for g in gaps), gaps)

    print("\n── ၃ · role က sfxlib ထဲ ရှိရမည် ──")
    # ⚠️ 「AI must never invent arbitrary local file paths」⇒ role သာ
    known = EX._sfx_roles()
    roles = sorted({e["props"]["role"] for e in out})
    check("role အားလုံး တကယ်ရှိသည်",
          known is None or all(r in known for r in roles),
          [r for r in roles if known and r not in known])
    check("to_sfx က ကျော်မချပါ",
          len(EX.to_sfx(dict(sfxEvents=out))) == len(out))

    print("\n── ၄ · ဘောင်အတွင်း ──")
    for e in out:
        check(f"{e['props']['role']} အချိန် ဘောင်ထဲ",
              0 <= e["startTime"] <= 60.0, e["startTime"])
    check("dB အားလုံး −၁၀ အောက်",
          all(e["props"]["db"] <= -10 for e in out),
          [e["props"]["db"] for e in out])

    print("\n── ၅ · ထပ်နေသော အချိန် မထွက်ရ ──")
    # ⚠️ ဘောင်အစမှာ ရှေ့သံ ကပ်သွားလျှင် ၂ ခုလုံး ၀.၀၀s ဖြစ်ခဲ့သည်
    e0 = PL.sfx_plan([ev(0, 0.0)], 60.0, 1.5)
    ts = [x["startTime"] for x in e0]
    check("ဘောင်အစ ဖြစ်ရပ် ⇒ အချိန် မထပ်ပါ", len(ts) == len(set(ts)), ts)

    print("\n── ၆ · pop က တစ်ထပ်သာ ──")
    ep = PL.sfx_plan([ev(0, 20.0, kind="pop")], 60.0, 1.5)
    check("pop ⇒ ၁ ခုသာ", len(ep) == 1, ep)
    check("pop ⇒ role `pop`", ep and ep[0]["props"]["role"] == "pop", ep)

    print("\n── ၇ · ဖြစ်ရပ်တိုင်းမှာ အကြောင်းရင်း ──")
    check("reason ပါသည်", all(e.get("reason") for e in out))
    check("confidence ပါသည်", all(0 < e.get("confidence", 0) <= 1 for e in out))
    check("မူလ ဖြစ်ရပ် ချိတ်ထားသည်",
          all(e["props"].get("event") for e in out))

    print("\n── ၈ · semantic role (P2) ──")
    # ⚠️ `SFX_ROLE` ထဲ hook/number/warning မြေပုံ ရှိပါလျက် planner က
    #    **အားလုံးကို `card`** ဟု သတ်မှတ်ခဲ့သဖြင့် တစ်ခါမှ အလုပ်မလုပ်ခဲ့。
    for k, want in (("hook", "riser_soft"), ("warning", "whoosh_in"),
                    ("number", "swipe"), ("card", "whoosh_in")):
        e1 = PL.sfx_plan([ev(0, 20.0, kind=k)], 90.0, 1.5)
        roles = [x["props"]["role"] for x in e1]
        check(f"{k} ⇒ {want}", want in roles, roles)
    check("SEM မြေပုံက FAMILY label အားလုံး ဖုံး",
          set(PL.FAMILY) <= set(PL.SEM), set(PL.FAMILY) - set(PL.SEM))

    print("\n── ၉ · အကွာက ပေါလစီကနေ (ဂိတ် ၈s · ၄၀s မဟုတ်) ──")
    # ⚠️ အရင်က `gap = max(8, 60/per_min)` ⇒ ၁.၅/min မှာ **၄၀s** ဖြစ်ကာ
    #    ဂိတ်ထက် ၅ ဆ တင်းခဲ့သည် — အကွာနဲ့ နှုန်းက ဂိတ် နှစ်ခု、တစ်ခုထဲ မတွက်ရ。
    import sfxpol as SPL
    many = [ev(i, 4.0 + i * 10.0, kind="card") for i in range(28)]
    o9 = PL.sfx_plan(many, 300.0, 1.5)
    ts = sorted({round(x["startTime"], 2) for x in o9})
    mom = []
    for t in ts:
        if not mom or t - mom[-1] > 0.6:
            mom.append(t)
    gaps = [round(b - a, 1) for a, b in zip(mom, mom[1:])]
    check("အနီးဆုံး အကွာ ≥ ၈s", not gaps or min(gaps) >= 8.0, gaps)
    check("၄၀s အတင်း မခွာ (၁၀–၃၉s ဖြစ်နိုင်ရမည်)",
          not gaps or min(gaps) < 40.0, gaps)
    per = len(mom) / (max(60.0, 300.0) / 60.0)
    check("နှုန်း ဂိတ်အတွင်း", per <= 1.5 + 1e-9, per)

    print("\n── ၁၀ · အရေးကြီးတာ ရွေးသည် ──")
    # ⚠️ အရင်က ရှေ့က cap ခုကို ပဲ ယူခဲ့သဖြင့် ဗီဒီယို နောက်ပိုင်း တိတ်ခဲ့သည်
    mix = ([ev(i, 5.0 + i * 9.0, kind="card") for i in range(6)]
           + [ev(90, 100.0, kind="hook"), ev(91, 200.0, kind="warning")])
    o10 = PL.sfx_plan(mix, 300.0, 1.5)
    kinds = {x["style"]["kind"] for x in o10}
    check("hook ပါလာသည်", "hook" in kinds, kinds)
    check("warning ပါလာသည်", "warning" in kinds, kinds)
    last = max((x["startTime"] for x in o10), default=0)
    check("နောက်ပိုင်း မတိတ် (>၁၅၀s မှာ ရှိ)", last > 150.0, last)

    print("\n── ၁၁ · တိုသော ဗီဒီယိုမှာ အသံ ရ ──")
    o11 = PL.sfx_plan([ev(0, 6.0), ev(1, 12.0)], 16.0, 1.5)
    check("၁၆s ⇒ အသံ ရှိသည်", len(o11) > 0, o11)
    mom11 = sorted({round(x["startTime"], 1) for x in o11})
    check("၁၆s ⇒ ဖြစ်ရပ် ၁ ခုသာ",
          len([t for i, t in enumerate(mom11)
               if i == 0 or t - mom11[i - 1] > 0.6]) == 1, mom11)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
