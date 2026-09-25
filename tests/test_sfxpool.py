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
    # ⚠️ **ဖိုင်အရှည် (`dur`) နဲ့ မစစ်ရ** (၂၀၂၆-၀၉-၂၅ ပြင်)。 `wav()` က
    #    `render_dur()` အထိ **ဖြတ်ပြီး** ရေးသဖြင့် ထွက်လာသော cue က
    #    ဂိတ်အတွင်း အမြဲ ရှိသည်。 ဖိုင်အရှည်နဲ့ စစ်လျှင် reverb အမြီး
    #    ရှည်သော cue (`SWOOSH-005` ဖိုင် ၃.၁၈s · ကြားရ ၀.၉၇s) ကို
    #    「ဂိတ်ကျော်」ဟု မှားစွပ်စွဲပြီး ပယ်မိသည်。
    #    ⚠️ **ဂိတ် လျှော့တာ မဟုတ်** — စစ်ရမည့် အချက် ၃ ချက် ပိုတင်းသည်:
    #      ① ထွက်မည့် အရှည်က ဘောင်အတွင်း ② အသံ ကျယ်ချက် (`peak_t`) က
    #      ဖြတ်မျဉ်း + fade အတွင်း ကျန် ③ lead ခွင့်ပြုချက်ထဲ ဝင်。
    bad, cut, late = [], [], []
    for r in SP.MAP:
        lo = SP.DUR_MIN.get(r, 0.0)
        fam = SP.MAP[r][0]
        hi = SP.DUR_MAX.get(fam, 2.0)
        for x in SP.role_pool(r):
            rd = SP.render_dur(x, fam)
            if not (lo - 1e-6 <= rd <= hi + 1e-6):
                bad.append(f"{r}:{x['id']}={rd:.2f}")
            pt = x.get("peak_t")
            if pt is not None:
                if float(pt) + 0.001 > rd:
                    cut.append(f"{r}:{x['id']} peak {pt} > ထွက် {rd:.2f}")
                # ⚠️ `bed` က ဖြစ်ရပ်ပေါ် ကွက်တိ ကျရန် မဟုတ် — ခံပေးရန် ⇒
                #    `lead()` က `bed` အတွက် ၀ ပြန်သည် (စောလျှင် ဗီဒီယို
                #    အစမတိုင်ခင် ရောက်မည်) ⇒ ဒီစစ်ချက် မသက်ဆိုင်ပါ。
                if fam != "bed" and float(pt) > SP.LEAD_MAX:
                    late.append(f"{r}:{x['id']} peak {pt}")
    check("ထွက်မည့် အရှည် ဘောင်အတွင်း", not bad, bad[:3])
    check("အသံ ကျယ်ချက် ဖြတ်မခံရ", not cut, cut[:3])
    check("lead နဲ့ ပြန်ညှိလို့ရ", not late, late[:3])

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
    # ⚠️ ယခင်က 「click ရဲ့ lead အလယ်တန်း ≤ ၀.၀၆」 ဟု စစ်ခဲ့သည် — အဲဒါက
    #    **ဖိုင်က ချက်ချင်း စသည်** ဆိုသော ယူဆချက် ဖြစ်ပြီး pool သေးစဉ်
    #    မှန်ခဲ့သည်。 pool ၁၂၇ ခု ဖြစ်လာသောအခါ အလယ်တန်း ၀.၁၃၃ ဖြစ်သည် —
    #    ရှေ့မှာ တိတ်နေသော ဖိုင်များ ပါလာ၍。 ⚠️ အဲဒါက **ချွတ်ယွင်းချက်
    #    မဟုတ်** — `lead()` က `peak_t` စောပြီး ထည့်သဖြင့် အသံက ဖြစ်ရပ်ပေါ်
    #    **ကွက်တိ** ကျသည် (ဒါက `lead()` ရဲ့ တာဝန်)。 ⇒ စစ်ရမည့်အချက်က
    #    「ပြန်ညှိလို့ ရသလား」 ဖြစ်သည်、「ဖိုင်က စော/နှေး」 မဟုတ်。
    check("click ကို lead နဲ့ ပြန်ညှိလို့ရ",
          lc[-1] <= SP.LEAD_MAX, lc[-1])
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
    # ⚠️ **တိုင်းထားသော profile သာ ပုံသေ ဂိတ်ကို ကျော်ခွင့်ရှိသည်**。
    #    headtop ကို reference ၈ ပုဒ်ကနေ တိုင်းရာ ၆.၂၅–၈.၅၀/min ဖြစ်ပြီး
    #    ပုံသေ ၁.၅ က ၅ ဆ တင်းလွန်းသည် — ၇၂s render မှာ အသံ ၁ ခုတည်း
    #    ထွက်ခဲ့ပြီး Zin 「တစ်ခုမှမတွေ့ရသေးဘူး」 ဟု ပြောခဲ့သည်。
    bad, meas = [], []
    for e in RC.listing():
        k = e.get("id") if isinstance(e, dict) else e
        p = PL.for_recipe(RC.apply(k, {}))
        over = p["per_min"] > Q.SFX_MAX_PER_MIN or p["gap"] < Q.SFX_MIN_GAP
        if over and p.get("measured"):
            meas.append((k, p["per_min"], p["gap"]))
        elif over:
            bad.append((k, p["per_min"], p["gap"]))
    check("မတိုင်းရသေးသော recipe က ဂိတ် မကျော်", not bad, bad)
    check("ကျော်သည့်ဟာတိုင်း တိုင်းချက် မှတ်ထားသည်",
          all(PL.MEASURED.get(k, {}).get("src") for k, _a, _b in meas), meas)

    print("\n── ၁၂ · အောက်ခြေ ၆၀s (တိုသော ဗီဒီယိုမှာ အသံ ရရမည်) ──")
    # ⚠️ အရင်က ၄၀s အောက် ဗီဒီယိုတိုင်းမှာ **သုည သာ** ဂိတ် ဖြတ်နိုင်ခဲ့သည်
    p = PL.policy("zae", "headtop")
    zero = [d for d in (10, 16, 30, 45) if PL.budget(p, d) < 1]
    check("၁၆s မှာ အသံ ၁ ချက် ရ", not zero, zero)
    # ⚠️ ဂိတ်က ယခု profile အလိုက် — headtop ရဲ့ ကိုယ်ပိုင် ကန့်သတ်နဲ့ စစ်သည်
    over = [d for d in (10, 16, 30, 45, 60, 77.7, 120, 300)
            if PL.budget(p, d) / (max(60.0, d) / 60.0) > p["per_min"] + 1e-9]
    check("ဘယ်အရှည်မှ ကိုယ့်ကန့်သတ် မကျော်", not over, over)
    dflt = PL.policy("zae", "short-biz")
    over2 = [d for d in (16, 60, 300)
             if PL.budget(dflt, d) / (max(60.0, d) / 60.0) > Q.SFX_MAX_PER_MIN + 1e-9]
    check("မတိုင်းရသေးသောဟာက ပုံသေ ဂိတ် မကျော်", not over2, over2)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
