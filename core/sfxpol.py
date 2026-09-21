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
    "headtop":   dict(per_min=1.5, gap=8.0, layer=0.60,
                      src="ဂိတ် ၁.၅ — reference ၄–၈/min ကို layer နဲ့ ဖြေရမည်"),
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


def clamp(p):
    """ပေါလစီကို ဂိတ်အတွင်း **အတင်း ထည့်**သည် — ဂိတ်ကို မလျှော့ပါ

    ⚠️ `per_min` က **အမြင့်ဆုံး** ⇒ `min()`。
    ⚠️ `gap` က **အနည်းဆုံး** ⇒ `max()`。 ဒီနှစ်ခုကို မှားလျှင် ဂိတ် ပြေလျော့သည်。
    """
    c = ceil()
    q = dict(DEF)
    q.update({k: v for k, v in (p or {}).items() if v is not None})
    q["per_min"] = min(float(q["per_min"]), c["per_min"])
    q["gap"] = max(float(q["gap"]), c["gap"])
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
    return clamp(p)


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
                      src=f"recipe sfx_per_min={rc.get('sfx_per_min')} · theme={th}"))


ZJL_FLOOR = 900     # ⚠️ `sfxpool.ZJL_MIN_BRIGHT` နဲ့ တူရမည်
