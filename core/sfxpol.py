"""SFX ပေါလစီ — density / gap ကို **profile အလိုက်** သတ်မှတ်ခြင်း (P1 · အချက် ၅)

⚠️ အရင်က `SFX_MIN_GAP = 8.0` က **နှစ်နေရာ** ရှိသည် — `qc.py:18` နဲ့
   `dress.py:236`。 တစ်ခုကို ပြင်ပြီး နောက်တစ်ခု မပြင်လျှင် generator နဲ့ gate
   ကွဲသွားပြီး render ပြီးမှ ကျဘမ်း ဖြစ်သည် (တကယ် ဖြစ်ခဲ့သော ပုံစံ)。
   ⇒ **ရင်းမြစ် တစ်ခုတည်း** ဖြစ်ရမည်。

⚠️ **ဂိတ် မလျှော့ရ** — `qc` ရဲ့ ကိန်းများက **အမြင့်ဆုံး ကန့်သတ်**。
   profile က ထို့အောက် **ပိုတင်း**လို့ရသည်、**ပိုလျှော့လို့ မရ**。
   `clamp()` က အဲဒါကို အတင်း ဖြစ်စေသည် ⇒ profile ထဲ ၄/min ရေးထားလျှင်
   ၁.၅ ဖြစ်သွားပြီး ဂိတ်ကို ဘယ်တော့မှ မကျော်ပါ。
"""

# ⚠️ ကိန်း တိုင်းက **ရင်းမြစ်** ပါရမည် — မှန်းဆချက်ကို ကိန်းလို မမြင်ရစေရန်
POLICY = {
    # theme/style → dict(per_min, gap, layer, bright_floor)
    "zjl": dict(per_min=1.1, gap=9.0,
                src="REF-A (Bhone) တိုင်းချက် ၁.၁/min", bright_floor=900),
    "zae": dict(per_min=1.5, gap=8.0, src="playbook P3", bright_floor=0),
}
# ⚠️ style အလိုက် — theme ထက် **ပိုတိတိကျကျ**。 podcast က ၀.၃/min ဟု
#    playbook မှာ ရေးထားသည် (ZAE short ၂၀ နဲ့ ၆၀ ဆ ကွာ)。
BY_STYLE = {
    "podcast":   dict(per_min=0.3, gap=20.0, src="playbook — podcast ၀.၃/min"),
    "knowledge": dict(per_min=0.6, gap=12.0, src="REF-B တိုင်းချက် ၀.၆/min"),
    # ⚠️ headtop ရဲ့ reference က ၄–၈/min ဖြစ်သည် (တိုင်းပြီးသား) ပေမယ့်
    #    ဂိတ်က ၁.၅ ⇒ `clamp()` က ၁.၅ ဖြစ်စေမည်。 **ဂိတ်ကို မလျှော့ရ** ⇒
    #    ပိုထည့်ချင်လျှင် ဂိတ်ကို မဟုတ်ဘဲ **ဖြစ်ရပ် တစ်ခုတည်း၏ အထပ်** အဖြစ်
    #    ဆောက်ရမည် (layer — QC က အထပ်ကို တစ်ခုလို့ ရေတွက်သည်)。
    # ⚠️ **ဤ ၁.၅ က မသုံးတော့ပါ** — `clamp()` က `MEASURED["headtop"]`
    #    (၈.၇/min · အကွာ ၂.၀s) နဲ့ **အစားထိုး**သည် ⇒ `policy("zae","headtop")`
    #    က ၈.၇ ပြန်သည်。 ဤအထဲက `layer` ၀.၆၀ သာ အသက်ဝင်သည်。
    #    ⚠️ **ဖျက်မထားရ** — `POLICY["zae"]` က theme အဆင့် ၁.၅ ကို
    #      သတ်မှတ်ဆဲ ဖြစ်၍ headtop က MEASURED စာရင်းက ထွက်လျှင်
    #      ဤတန်ဖိုးက အောက်ခံ ဖြစ်ရမည် (တိုင်းချက် ပျောက်လျှင် ဂိတ် ပြန်တင်း)。
    #    စမ်းသပ်ချက် — `tests/test_sfxpool.py` ၁၁-ခ。
    "headtop":   dict(per_min=1.5, gap=8.0, layer=0.60,
                      src="ဂိတ် ၁.၅ (အောက်ခံသာ · MEASURED ၈.၇ က လွှမ်းသည်) "
                          "— reference ၄–၈/min ကို layer နဲ့ ဖြေရမည်"),
}
DEF = dict(per_min=1.5, gap=8.0, layer=0.60, bright_floor=0,
           src="ပုံသေ — qc ဂိတ်နဲ့ တူ")


def ceil():
    """qc ရဲ့ **အမြင့်ဆုံး ကန့်သတ်** — ဤဖိုင်မှာ ကိန်း ထပ်မရေးရ"""
    try:
        import qc as Q
    except ImportError:
        from core import qc as Q
    return dict(per_min=float(Q.SFX_MAX_PER_MIN), gap=float(Q.SFX_MIN_GAP),
                layer=float(getattr(Q, "SFX_LAYER_W", 0.60)))


# ⚠️ **တိုင်းထားသော profile** — ဤအထဲက per_min/gap ကသာ ပုံသေ ဂိတ်ကို
#    ကျော်ခွင့်ရှိသည်。 `src` မှာ တိုင်းချက် မှတ်ထားရမည် — မှတ်မထားလျှင်
#    「ဂိတ် လျှော့」သာ ဖြစ်ပြီး တိုင်းချက် မဟုတ်ပါ。
# ⚠️ Zin: 「sound effect လဲတစ်ခုမှမတွေ့ရသေးဘူး」(၂၀၂၆-၀၉-၂၁) — ၇၂s render
#    မှာ အသံဖြစ်ရပ် **၁ ခုတည်း** (၀.၈၃/min) ထွက်ခဲ့သည်。
# ⚠️ reference ၈ ပုဒ် × ၂၄၀s တိုင်းချက် —
#      သိပ်သည်းမှု ၆.၂၅ · ၆.၂၅ · ၆.၅၀ · ၇.၅၀ · ၈.၀၀ · ၈.၂၅ · ၈.၅၀ · ၈.၅၀/min
#      အကွာ (n=၁၆၆) p10 ၁.၂ · p25 ၂.၂ · **အလယ် ၄.၇** · p75 ၉.၁ · p90 ၁၈.၉s
#      ⇒ ပုံသေ ဂိတ် (≥၈s) က reference ကိုယ်တိုင်ရဲ့ **၇၀%** ကို ပယ်မည်
#    ⇒ headtop/ref-talk ကို တိုင်းချက်အတိုင်း ဖွင့်သည် — အနိမ့်ဆုံး
#      တိုင်းချက် (၆.၂၅) အောက် ၆.၀ နဲ့ p25 (၂.၂) အနီး ၂.၀ ဟု **ကွာလပ်
#      ချန်ပြီး** ထားသည်。
# ⚠️⚠️ **၂၀၂၆-၀၉-၂၈ — headtop ကို ၆.၀ → ၈.၇ တင်သည်。 ဤကိန်းက
#    တိုင်းချက် ကနေ **မလာပါ** — Zin ရဲ့ **နား** ကနေ လာသည်。**
#    လုပ်ထုံး: ကုဒ် တူတူ · seed တူတူ · flag တူတူ (rotate=0 alias=0 decl=1)
#    ပေါ်မှာ ၉၀s render ၃ ခု ထုတ်ပြီး **တံဆိပ် မပါဘဲ · အစဉ် ရော**ကာ
#    နားထောင်ခိုင်းသည် (mix_1/2/3 · mapping ကို သူ မမြင်ရ):
#        ၅.၃၄/min (ဖြစ်ရပ် ၈) · ၇.၃၃ (၁၁) · **၈.၆၈ (၁၃)**
#    Zin: 「ပထမဗီဒီယိုကောင်းတယ်」 ⇒ **၈.၆၈/min** ကို ရွေးသည်。
#    ⇒ n=၁ နားထောင်ချက် · ဗီဒီယို ၁ ပုဒ် · စမ်းသပ်ချက် တစ်ကြိမ်。
# ⚠️ **၈.၇ က reference band ရဲ့ ထိပ် (၈.၅၀) ကို ကျော်သည်**。 ရွေးထားသော
#    သိပ်သည်းမှုက reference ၈ ပုဒ်လုံး**ထက် များ**သည် — အရင်က ၆.၀ နဲ့
#    အားလုံးထက် **နည်း**ခဲ့သလို、ယခု အားလုံးထက် **များ**သည်。 ၂ ခုလုံး
#    band ပြင်ပ ဖြစ်၍ **မှတ်ထားရမည်**、ဖုံးမထားရ。
# ⚠️ `ref-talk` · `short-916` · `short-video` ကို **မထိရ** — သူတို့က
#    ကိုယ်ပိုင် ၆.၀ ရေးထားပြီးသား ဖြစ်၍ ဤပြောင်းလဲမှု မရောက်ပါ。
#    headtop အတွက် သူ့နားက သူတို့အတွက် သက်သေ မဟုတ်ပါ (အမှား #၃၇)。
MEASURED = {
    "headtop":  dict(per_min=8.7, gap=2.0,
                     src="⚠️ **Zin ရဲ့ နား ၂၀၂၆-၀၉-၂၈** (တိုင်းချက် မဟုတ်) — "
                         "မမြင်ရသော A/B ၃ ခု ၅.၃၄ · ၇.၃၃ · ၈.၆၈/min ထဲက "
                         "၈.၆၈ ကို ရွေး · n=၁ · reference band ၆.၂၅–၈.၅၀ ရဲ့ "
                         "**ထိပ်ကို ကျော်** · အကွာ ၂.၀s က တိုင်းချက်အတိုင်း"),
    "ref-talk": dict(per_min=6.0, gap=2.0,
                     src="headtop နဲ့ တူညီသော reference"),
    # WARN measured 2026-09-25 on Zin's own two ZAE references
    #    (`~/Downloads/1.mp4`, `2.mp4`) because the default 1.5/min left a
    #    78 s render with **one** sound moment for six graphics, and he asked
    #    for the gate to be raised **from a measurement**, not by hand.
    # WARN counting SFX inside a finished mix is impossible -- four attempts,
    #    four implausible answers ([[ikki-eleven-references]]). So this does
    #    NOT count sounds. It measures, with one detector across all three
    #    files: at each visual change (scene score > 0.30), is there an HF
    #    transient within +/-0.20 s? Yes/no only.
    #      ZAE ref 1  21 changes @ 21.55/min -> **43%** carry a sound
    #      ZAE ref 2  27 changes @ 18.89/min -> **56%**
    #      IKKI v6    24 changes @ 18.55/min -> **21%**
    #    The change RATE already matches (18.6 vs 18.9-21.6); only the sound
    #    coverage differs. IKKI's 21% is its floor, since that render carried
    #    exactly one SFX moment -- the rest is music and B-roll audio landing
    #    on cuts. Lifting 24 changes from 5 sounded to ~12 (the reference's
    #    ~50%) needs about 7 more moments in 77.6 s = **5.4/min**, so 6.0
    #    admits it with a little room and matches the `headtop` profile.
    # WARN spacing is measured too, not guessed: the gaps between sounded
    #    changes run min 0.67-1.03 s, p10 1.03-1.60 s, median 4.47-5.30 s.
    #    2.0 s is therefore slightly TIGHTER than the references (2-3 of their
    #    events sit closer than that) -- it is not a loosening.
    # WARN the 43/56% figures are solid; any "SFX per minute" split out of them
    #    assumes IKKI's 21% non-SFX coincidence rate also holds for the
    #    references, which cannot be checked without their stems. Stated, not
    #    hidden.
    # short-916 (2026-09-26). Zin: "no SFX" -- the 1.5/min house ceiling and the
    #    `ikki` theme's 8 s gap left 77.6 s with ONE sound moment (3 ticks
    #    inside the first second). Same change-coincidence detector as ZAE
    #    (scene>0.30, HF transient within 0.2 s) on the 4 shorts refs:
    #    80 / 100 / 100 / 80 % of visual changes carry a sound. WARN the
    #    detector also reads 89 % on IKKI v6, whose only sounds were those
    #    ticks -- speech sibilants trigger it -- so this proves the refs sound
    #    their changes, NOT a per-minute rate. The rate is therefore the
    #    already-measured ZAE/headtop figure, 6.0/min with a 2.0 s gap, and
    #    Zin asked for SFX explicitly. Stated, not hidden.
    "short-916": dict(per_min=6.0, gap=2.0,
                      src="4 shorts refs — ပုံပြောင်းချိန် အသံပါမှု 80/100/100/80% "
                          "(detector က IKKI v6 မှာလည်း 89% ⇒ ရှိကြောင်းသာ သက်သေ၊ "
                          "နှုန်းမဟုတ်) · နှုန်းက ZAE/headtop ရဲ့ တိုင်းပြီး 6.0/min · "
                          "Zin 2026-09-26 SFX တောင်း"),
    "short-video": dict(per_min=6.0, gap=2.0,
                        src="ZAE reference ၂ ပုဒ် (1.mp4 · 2.mp4) — "
                            "ရုပ်ပြောင်းချိန်မှာ အသံပါမှု ၄၃% / ၅၆% ↔ "
                            "IKKI ၂၁% · ပြောင်းနှုန်း ၂၁.၅၅ / ၁၈.၈၉ ↔ ၁၈.၅၅ · "
                            "အကွာ အလယ်တန်း ၄.၄၇–၅.၃၀s (အနည်းဆုံး ၀.၆၇) · "
                            "harness scratchpad/sfxgate.py"),
}


def clamp(p, style=None):
    """ပေါလစီကို ဂိတ်အတွင်း **အတင်း ထည့်**သည် — ဂိတ်ကို မလျှော့ပါ

    ⚠️ `per_min` က **အမြင့်ဆုံး** ⇒ `min()`。
    ⚠️ `gap` က **အနည်းဆုံး** ⇒ `max()`。 ဒီနှစ်ခုကို မှားလျှင် ဂိတ် ပြေလျော့သည်。
    """
    c = ceil()
    q = dict(DEF)
    q.update({k: v for k, v in (p or {}).items() if v is not None})
    m = MEASURED.get(style or "")
    if m:
        # ⚠️ တိုင်းထားသော profile — ကိုယ်ပိုင် ကိန်းကို သုံးသည်
        q["per_min"] = float(m["per_min"])
        q["gap"] = float(m["gap"])
        q["src"] = m["src"]
        q["measured"] = True
        # ⚠️ **စမ်းသပ်ချက် အတွက်သာ** — Zin ၂၀၂၆-၀၉-၂၈: 「band ရဲ့ အလယ်
        #    ~၇.၄/min ဗားရှင်း တစ်ခု ထုတ်ပြီး နားနဲ့ ဆုံးဖြတ်မယ်」。
        #    ⚠️ `for_recipe()` ကနေ `sfx_per_min=7.4` ပို့လျှင် **မရပါ** —
        #      အပေါ် ၃ လိုင်းက MEASURED နဲ့ အစားထိုးပြီးသား ဖြစ်သည် ⇒
        #      env ကနေသာ ဝင်ရသည်。
        #    ⚠️ ဤ env က **ဂိတ် လျှော့တာ မဟုတ်** — generator ရော `qc` ရော
        #      တူညီသော `clamp()` ကနေ ယူသဖြင့် ၂ ခုလုံး တစ်ပြိုင်နက် တက်သည်
        #      (ရင်းမြစ် တစ်ခုတည်း ဆိုသည့် ဤဖိုင်၏ ရည်ရွယ်ချက်)。
        #    ⚠️ `worker.TEST_ONLY_ENV` ထဲ ရှိသဖြင့် production မှာ ငြင်းသည်。
        import os as _os
        _ev = (_os.environ.get("IKKI_SFX_PERMIN") or "").strip()
        if _ev:
            try:
                _pv = float(_ev)
            except ValueError:
                _pv = 0.0
            if 0.0 < _pv <= 12.0:
                q["per_min"] = _pv
                q["src"] = (f"⚠️ စမ်းသပ်ချက် env IKKI_SFX_PERMIN={_pv:g} "
                            f"(တိုင်းချက် {m['per_min']:g} ကို ဖယ်ထား) · "
                            + str(m["src"]))
                q["permin_env"] = _pv
    else:
        # ⚠️ မတိုင်းရသေးသော profile — **ပုံသေ ဂိတ်ကို မကျော်ရ**
        q["per_min"] = min(float(q["per_min"]), c["per_min"])
        q["gap"] = max(float(q["gap"]), c["gap"])
        q["measured"] = False
    q["layer"] = min(float(q.get("layer") or c["layer"]), c["layer"])
    return q


def policy(theme=None, style=None):
    """profile အလိုက် ပေါလစီ — `dict(per_min, gap, layer, bright_floor, src)`

    ⚠️ အစီအစဥ် — **style > theme > ပုံသေ**。 style က ပိုတိကျသည်。
    """
    p = dict(DEF)
    if theme and theme in POLICY:
        p.update(POLICY[theme])
    if style and style in BY_STYLE:
        p.update(BY_STYLE[style])
    return clamp(p, style=style)


def budget(p, dur):
    """ကြာချိန် `dur` s အတွက် **ဖြစ်ရပ် အရေအတွက်** ကန့်သတ်

    ⚠️ **`round` မသုံးရ — အောက်သို့ ဖြတ်ရမည်**。 ၁.၅/min × ၇၇.၇s = ၁.၉၄ →
       `round` က ၂ ⇒ တိုင်းလိုက်တော့ ၁.၅၄၅/min ဖြစ်ကာ ဂိတ် (≤၁.၅) ကျခဲ့သည်
       (၂၀၂၆-၀၉-၂၀ j_f5bd998f5ca3)。
    """
    if dur <= 0:
        return 0
    # ⚠️ အောက်ခြေက **ံ၀ စက္ကန့္ အနည်းဆုံး** — `qc.sfx_density` နဲ့ **တူရမည်**。
    #    မတူလျှင် generator ထုတ်တာ ဂိတ် မဖြတ်ဘဲ render ပြီးမှ ကျမည်。
    return max(0, int(float(p["per_min"]) * max(60.0, float(dur)) / 60.0))


# ⚠️ theme အလိုက် **အကွာ / အထပ်** — `per_min` က recipe ထဲ ရှိပြီးသား
#    (၁၁ ခုလုံး သတ်မှတ်ထားသည် · podcast ၀.၃ … headtop ၁.၅) ⇒ ဒီမှာ
#    **ထပ်မရေးရ**。 ထပ်ရေးလျှင် recipe နဲ့ ကွဲသွားမည်。
GAP = {"zjl": 9.0, "zae": 8.0, "ikki": 8.0}


def for_recipe(rc):
    """recipe dict → ပေါလစီ · **ဂိတ်အတွင်း ညှိပြီးသား**

    ⚠️ `per_min` ရဲ့ ရင်းမြစ်က **recipe**。 `gap`/`layer` ရဲ့ ရင်းမြစ်က
       theme。 နှစ်ခုလုံးကို `clamp()` က ဂိတ်အတွင်း ထည့်သည်。
    """
    rc = rc or {}
    th = rc.get("theme")
    return clamp(dict(per_min=rc.get("sfx_per_min"),
                      gap=GAP.get(th), layer=None,
                      bright_floor=ZJL_FLOOR if th == "zjl" else 0,
                      src=f"recipe sfx_per_min={rc.get('sfx_per_min')} · theme={th}"),
                 style=rc.get("_id") or rc.get("style"))


ZJL_FLOOR = 900     # ⚠️ `sfxpool.ZJL_MIN_BRIGHT` နဲ့ တူရမည်
