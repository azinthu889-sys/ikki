# -*- coding: utf-8 -*-
"""SFX variant pool + ပေါလစီ — role တစ်ခုလျှင် ဖိုင်တစ်ခုတည်း မဖြစ်ရ (P1)

⚠️ audit အချက် C — `sfxlib.ROLE` က role ၂၂ ခုစလုံးကို **ဖိုင်တစ်ခုတည်း**
   ညွှန်းခဲ့သည် (ဖိုင် ၇၄၁ ရှိပါလျက်)。 ဒီ test က အဲဒါ ပြန်မဖြစ်ရန် ထိန်းသည်。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))
import qc as Q          # noqa: E402
import recipes as RC    # noqa: E402
import sfxpol as PL     # noqa: E402
import sfxpool as SP    # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def main():
    print("── ၁ · catalog ──")
    c = SP.catalog()
    check("v2", c.get("version") == 2, c.get("version"))
    check("ဖိုင် ၄၀၀+", len(c.get("items") or []) > 400, len(c.get("items") or []))
    check("root ၂ ခု", len(c.get("roots") or {}) == 2, c.get("roots"))

    print("\n── ၂ · role တိုင်းမှာ ရွေးစရာ ၂ ခုအထက် ──")
    thin = {r: len(SP.role_pool(r)) for r in SP.MAP if len(SP.role_pool(r)) < 2}
    check("role အားလုံး variant ရှိ", not thin, thin)

    print("\n── ၃ · deterministic (render ပြန်လုပ်လျှင် တူရမည်) ──")
    a = [SP.pick("whoosh", "s1", i)["id"] for i in range(8)]
    b = [SP.pick("whoosh", "s1", i)["id"] for i in range(8)]
    check("seed တူ ⇒ ရလဒ် တူ", a == b)
    cc = [SP.pick("whoosh", "s2", i)["id"] for i in range(8)]
    check("seed မတူ ⇒ ရလဒ် ကွဲ", a != cc)

    print("\n── ၄ · မကြာခင်က သုံးထားတာ ပြန်မသုံး ──")
    used, rep = [], []
    for i in range(12):
        it = SP.pick("whoosh", "s1", i, used)
        if it["id"] in used[-SP.NOREPEAT:]:
            rep.append(it["id"])
        used.append(it["id"])
    check(f"ဝင်းဒိုး {SP.NOREPEAT} ခုအတွင်း ထပ်မပါ", not rep, rep)
    check("ကွဲပြားမှု ၆ ခုအထက်", len(set(used)) >= 6, len(set(used)))

    print("\n── ၅ · လိုင်စင် (ရောင်းသော product) ──")
    bad = [x["id"] for r in SP.MAP for x in SP.role_pool(r, ship=True)
           if not x.get("ship")]
    check("youtubesfx pack မပါ", not bad, bad[:3])
    check("ship=False ဖိုင် ရှိသည် (စစ်ချက် အဓိပ္ပာယ် ရှိစေရန်)",
          any(not x.get("ship") for x in c["items"]))

    print("\n── ၆ · ကြာချိန် ဘောင် ──")
    bad = []
    for r in SP.MAP:
        lo = SP.DUR_MIN.get(r, 0.0)
        hi = SP.DUR_MAX.get(SP.MAP[r][0], 2.0)
        for x in SP.role_pool(r):
            if not (lo - 1e-6 <= x["dur"] <= hi + 1e-6):
                bad.append(f"{r}:{x['id']}={x['dur']}")
    check("အားလုံး ဘောင်အတွင်း", not bad, bad[:3])

    print("\n── ၇ · အား (loudness) ပစ်မှတ် ──")
    bad = []
    for r in SP.MAP:
        tg = SP.target(SP.MAP[r][0])
        for x in SP.role_pool(r):
            if SP._reach(x, tg) < -SP.LOUD_TOL - 1e-6:
                bad.append(f"{r}:{x['id']}={SP._reach(x, tg):.1f}")
    check(f"ပစ်မှတ်အထိ {SP.LOUD_TOL} dB အတွင်း တက်နိုင်", not bad, bad[:3])

    print("\n── ၈ · ZJL နိမ့်ဘန်း ကန့်သတ် ──")
    bad = [f"{r}:{x['id']}={x['brightness']}" for r in ("whoosh_in", "riser_air",
           "shimmer") for x in SP.role_pool(r, th="zjl")
           if x["brightness"] < SP.ZJL_MIN_BRIGHT]
    check(f"brightness ≥ {SP.ZJL_MIN_BRIGHT} Hz", not bad, bad[:3])

    print("\n── ၉ · ဖိုင် တကယ် ရှိ ──")
    miss = [x["id"] for r in ("whoosh_in", "latch", "click", "riser_soft",
            "impact", "shimmer") for x in SP.role_pool(r)[:4]
            if not (SP.path(x) and os.path.exists(SP.path(x)))]
    check("လမ်းကြောင်း အားလုံး ရှိ", not miss, miss[:3])

    print("\n── ၁၀ · lead (အသံ ကျယ်ချိန်က ဖြစ်ရပ်နဲ့ ကိုက်ရမည်) ──")
    # ⚠️ riser ကို cue အစား ထည့်လျှင် ၁.၇s နောက်ကျမှ အသံ ရောက်ခဲ့သည်
    #    (တကယ် တိုင်းတွေ့ · ၂၀၂၆-၀၉-၂၁) ⇒ `peak_t` စောပြီး ထည့်ရမည်。
    bad = [x["id"] for r in SP.MAP for x in SP.role_pool(r)
           if x.get("peak_t") is None]
    check("variant တိုင်းမှာ peak_t ရှိ", not bad, bad[:3])
    # transient က ~၀ · riser က ရှည် — ဒါက **တိုင်းချက်** ဖြစ်မှ အဓိပ္ပာယ် ရှိ
    lc = sorted(SP.lead(x) for x in SP.role_pool("click"))
    lr = sorted(SP.lead(x) for x in SP.role_pool("riser_soft"))
    check("click ရဲ့ lead ≈ 0", lc[len(lc) // 2] <= 0.06, lc[len(lc) // 2])
    check("riser ရဲ့ lead > 0.5s", lr[len(lr) // 2] > 0.5, lr[len(lr) // 2])
    bad = [(r, round(SP.lead(x), 2)) for r in SP.MAP for x in SP.role_pool(r)
           if SP.lead(x) > x["dur"] + 1e-6]
    check("lead က ဖိုင်အရှည် မကျော်", not bad, bad[:3])

    print("\n── ၁၁ · ပေါလစီက **ဂိတ်ကို မလျှော့** ──")
    # ⚠️ ဒါက Zin ရဲ့ စည်းကမ်း — 「ဂိတ် မလျှော့ရ」。 ပေါလစီထဲ ဘာရေးထားပါစေ
    #    `clamp()` က ဂိတ်အတွင်း ထည့်ရမည်。
    hard = PL.clamp(dict(per_min=8.0, gap=1.0, layer=5.0))
    check("per_min ဂိတ်အထိသာ", hard["per_min"] <= Q.SFX_MAX_PER_MIN, hard)
    check("gap ဂိတ်အထက်သာ", hard["gap"] >= Q.SFX_MIN_GAP, hard)
    check("layer ဂိတ်အထိသာ", hard["layer"] <= Q.SFX_LAYER_W, hard)
    bad = []
    for e in RC.listing():
        k = e.get("id") if isinstance(e, dict) else e
        p = PL.for_recipe(RC.apply(k, {}))
        if p["per_min"] > Q.SFX_MAX_PER_MIN or p["gap"] < Q.SFX_MIN_GAP:
            bad.append((k, p["per_min"], p["gap"]))
    check("recipe အားလုံး ဂိတ်အတွင်း", not bad, bad)

    print("\n── ၁၂ · အောက်ခြေ ၆၀s (တိုသော ဗီဒီယိုမှာ အသံ ရရမည်) ──")
    # ⚠️ အရင်က ၄၀s အောက် ဗီဒီယိုတိုင်းမှာ **သုည သာ** ဂိတ် ဖြတ်နိုင်ခဲ့သည်
    p = PL.policy("zae", "headtop")
    zero = [d for d in (10, 16, 30, 45) if PL.budget(p, d) < 1]
    check("၁၆s မှာ အသံ ၁ ချက် ရ", not zero, zero)
    over = [d for d in (10, 16, 30, 45, 60, 77.7, 120, 300)
            if PL.budget(p, d) / (max(60.0, d) / 60.0) > Q.SFX_MAX_PER_MIN + 1e-9]
    check("ဘယ်အရှည်မှ ဂိတ် မကျော်", not over, over)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
