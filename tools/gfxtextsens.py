#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""template က **ကျွန်တော်တို့ စာသားကို တကယ် ရေးလား** စစ်သည်။

    python3 tools/gfxtextsens.py [--only id,id] [--limit N]

⚠️ **ဘာကြောင့် လိုအပ်လဲ** — `gfx_verify.py` ရဲ့ ဂိတ်က 「render ဖြစ်ပြီး မှင်
   ရှိ」ပဲ စစ်သည်。 အရောင်တုံး ချည်းပဲ ပါပြီး စာသား လုံးဝ မပါသော template တွေ
   အောင်သွားကာ ဗီဒီယိုထဲ **အဓိပ္ပာယ်မဲ့ ကွက်** ဖြစ်ခဲ့သည်
   (Zin ၂၀၂၆-၀၉-၂၀: 「template သုံးထားတာတွေရော quality 0」)。
⚠️ `tools/gfx_pool.py` ရဲ့ gradient ဂိတ်က **မယုံရ** — ကောင်း/ဆိုး နမူနာ ၁၄ ခုမှာ
   ကိန်းတွေ ထပ်နေသည် (⛔ မှတ်ချက် ကြည့်ပါ)。

**နည်းလမ်း** — တူညီသော template ကို **စာသား ၂ မျိုး**နဲ့ render လုပ်ပြီး
ထွက်လာသော **ပုံရိပ်** ကွာမကွာ တိုင်းသည်。 စာသားကို တကယ် ရေးလျှင် ပုံရိပ်
**ပြောင်းရမည်**。 မပြောင်းလျှင် လျစ်လျူရှုနေသည် ⇒ pool ထဲ မထည့်ရ。

တိုင်းရာမှာ ချို့ယွင်းချက် ၃ ခု တွေ့ခဲ့ပြီး ၃ ခုလုံး ပြင်ထားသည် —

⚠️ ① **နောက်ဆုံး frame ကို မသုံးရ** — template အများစုက fade ထွက်သွားသဖြင့်
   နောက်ဆုံး frame က ဗလာနီးပါး ⇒ စာသား မတူလည်း တူနေမည် ⇒ **မှင် အများဆုံး
   frame** ကို ရွေးသည်。
⚠️ ② **`statics` ကို မကျန်စေရ** — template အများအပြားက စာသားကို `anim` ထဲ
   မထားဘဲ `statics` ထဲ ပြန်ပေးသည် (`dress.py:394,707,723` က composite လုပ်သည်)。
   တကယ်တွေ့: `infogfx.checklist` ရဲ့ `anim` က checkbox ကွက်သာ (items အရေအတွက်
   ပေါ်သာ မူတည်) ⇒ diff ၀.၀၀၀ ထွက်ခဲ့သည် (၂၀၂၆-၀၉-၂၄)。
⚠️ ③ **alpha ပုံစံချည်း မတိုင်ရ** — အလင်းပိတ် ကတ်ပြားပေါ် စာရေးသော template
   တွေမှာ alpha က ကတ်ပြား ပုံသဏ္ဌာန်သာ ဖြစ်ပြီး **စာသားက RGB ထဲ** ရှိသည်
   ⇒ စာသား ဘာပဲဖြစ်ဖြစ် alpha တူနေမည် (တကယ်တွေ့: `insert.insert_label`
   diff ၀.၀၀၀ · ၂၀၂၆-၀၉-၂၄)。 ⇒ **RGBA ကို နောက်ခံပေါ် ထပ်ပြီး** တိုင်းသည်。

⚠️ **A/A ထိန်းချုပ်မှု** — မတည်ငြိမ်သော template (ကျပန်း · အချိန်အပေါ် မူတည်)
   က စာသား မပြောင်းလည်း ပုံရိပ် ပြောင်းနိုင်သည် ⇒ **false positive**。
   ဒါကြောင့် A/B ကွာဟမှု ဂိတ် ကျော်လျှင် **စာသား တူတူနဲ့ တတိယ render** လုပ်ပြီး
   အဲဒီ A/A ကွာဟမှု သေးမှသာ အောင်စေသည် (`AA_MAX` · `AB_OVER_AA`)。
⚠️ တစ်ခုချင်း **သီးသန့် process** — template တစ်ခု ကျလျှင် တစ်ခုလုံး မရပ်စေရန်。
"""
import json, os, subprocess, sys, time


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── W-1…W-4 လုံခြုံ ရေးမှု (`core/derived_io.py`) ─────────────────────
# ⚠️ ၂၀၂၆-၀၉-၂၆: derived ရေးသူ ၄၈ ခုထဲ ၄၄ မှာ ဗလာ-guard မရှိ · ၄၅ မှာ atomic
#    မရှိ ⇒ `gfx_size_16x9.json` (၅၉၃ entry) ဗလာနဲ့ လွှမ်းခံရသည်。
# ⚠️ path ကို **ကိုယ်တိုင် ထည့်ရမည်** — ဒီ script တွေမှာ `core` path insert က
#    `HERE` ရဲ့ အောက်မှာ ရှိသဖြင့် အပေါ်မှာ import လျှင် ကျမည် (တိုင်းပြီး တွေ့)。
try:
    _cp = os.path.join(HERE, "core")
    if _cp not in sys.path:
        sys.path.insert(0, _cp)
    import derived_io as _DIO
except ImportError as _die:      # ⚠️ fail-closed — guard မရှိဘဲ မရေးရ
    raise SystemExit("⛔ core/derived_io.py ဖတ်မရ: %s" % _die)

# ⚠️ S-b — ဂိတ်/တိုင်းချက်က **ဟောင်းနေတဲ့ derived ဖိုင်ကနေ ကိန်း မထုတ်ရ**။
#    ၂၀၂၆-၀၉-၂၅ မှာ ဒီစစ်ချက် မရှိလို့ ၉.၇ နာရီ ဟောင်းတဲ့ `gfx_verify.json`
#    ကနေ 「၆၁၆/၆၁၆ အောင်」 ဟု တင်ပြခဲ့သည်。
try:
    sys.path.insert(0, os.path.join(HERE, "tools"))
    import derived_check as _DC
except Exception:
    _DC = None
sys.path.insert(0, os.path.join(HERE, "core"))
TIMEOUT = 420           # render ၃ ခါ ဖြစ်နိုင်သဖြင့် ရှည်ရမည်
DIFF_MIN = 0.02          # ပုံရိပ် ကွာဟမှု အနည်းဆုံး (ဧရိယာ အချိုး)
# ⚠️ **အစစ်အမှန် ဂိတ်က ဒီတစ်ခု** — A/B ကွာသော pixel အရေအတွက်။
#    1080x1920 = 2.07M px ထဲ 500 px က 0.024% — မြန်မာ စာလုံး
#    တစ်လုံးထက် ငယ်သည်။ တိုင်းထားသော အနည်းဆုံး တုံ့ပြန်သူ = 2,302 px
#    (`thm.cmp_glass`) · မတုံ့ပြန်သူ = 0 px ⇒ ကွာဟမှု ကြီးမား။
DIFF_PX = 100
AA_MAX = 0.02            # စာသား တူတူနဲ့ ကွာဟမှု — ဤထက် ကြီးလျှင် မတည်ငြိမ်
AB_OVER_AA = 3.0         # A/B က A/A ထက် အနည်းဆုံး ဤအဆ ကြီးရမည်
OUT = os.path.join(HERE, "assets", "gfx_textsens.json")

# ⚠️ စာသား ၂ မျိုးက **အရှည် သိသိသာသာ ကွာ**ရမည် — တူညီသော အရှည်ဆိုလျှင်
#    စာလုံး အနေအထား တူပြီး ကွာဟမှု နည်းနိုင်သည်。
TXT_A = "ဂျပန်မှာ အလုပ်"
TXT_B = "ပြည်ပကနေ ချစ်ရသူတွေဆီ ငွေလွှဲခြင်းနဲ့ ဆုလက်ဆောင်"
ITM_A = ["ဂျပန်", "ကိုးရီးယား", "စင်္ကာပူ"]
ITM_B = ["ပြည်ပ ငွေလွှဲ", "ဘဏ် အကောင့်", "မိုဘိုင်း ငွေဖြည့်ခြင်း"]

# ⚠️ **ကိန်းပါသော နမူနာ** (`--num`) — chart/dashboard template ၄၁ ခုက
#    `rows` = (စာသား, ကိန်း) အတွဲ လိုသဖြင့် ကိန်းမပါသော နမူနာနဲ့ စစ်လျှင်
#    「adapter ဖွဲ့စည်းပုံ မကိုက်」နဲ့ ကျပြီး pool ထဲ လုံးဝ မဝင်ခဲ့
#    (၂၀၂၆-၀၉-၂၄ တိုင်းပြီး)。 ဤနမူနာနဲ့ **တကယ့် စွမ်းရည်** ကို စစ်သည်。
# ⚠️⚠️ **ကိန်းကိုလည်း A/B ကွာစေရမည်**။ အရင်က `nums=[62,41,27]` ကို
#    A ရော B ရော **တူတူ** ပေးခဲ့သည် ⇒ ကိန်းကိုပဲ ပြသော template
#    (`kinetic.count_up` · `odo.money` · `titles2.rating` · `charts.*`) တွေက
#    ပုံ တစ်ထပ်တည်း ထွက်ပြီး diff = 0.000 — **ဂိတ်က မှားစွဲချက်**
#    တင်မည် (၂၀၂၆-၀၉-၂၅)။ ⇒ ကိန်း ၂ စုံ သီးသီးခွဲ ထားသည်။
NUM_A = [62, 41, 27]
NUM_B = [37, 58, 19]
ITM_NA = ["ဂျပန် ၅၂", "ကိုးရီးယား ၃၁", "စင်္ကာပူ ၁၇"]
ITM_NB = ["ပြည်ပ ငွေလွှဲ ၆၈", "ဘဏ် အကောင့် ၂၄", "မိုဘိုင်း ၈"]
if "--num" in sys.argv:
    ITM_A, ITM_B = ITM_NA, ITM_NB
    TXT_A = "ဂျပန်မှာ အလုပ် ၅၂ ရာခိုင်နှုန်း"
    TXT_B = "ပြည်ပကနေ ငွေလွှဲခြင်း ၆၈ ရာခိုင်နှုန်း နဲ့ ဆုလက်ဆောင်"

CHILD = r'''
import os, sys, json
sys.path.insert(0, os.path.join(%(HERE)r, "core"))
import gfxcat as G, dress as DR
import numpy as np
from PIL import Image

eid = sys.argv[1]
e = [x for x in G.catalog() if x["id"] == eid]
if not e:
    print(json.dumps({"ok": 0, "why": "id မတွေ့"})); raise SystemExit
e = e[0]

BG = 128          # နောက်ခံ အလယ်မီးခိုး — RGBA ကို ဤအပေါ် ထပ်သည်
TOL = 24          # ပုံရိပ် ကွာဟမှု အနည်းဆုံး (0–255)


def _flat(q):
    """RGBA ဖိုင်ကို **နောက်ခံပေါ် ထပ်ပြီး** မီးခိုးရောင် + alpha ပြန်ပေးသည်ဂ

    ⚠️ alpha ချည်း မတိုင်ရ — အလင်းပိတ် ကတ်ပြားပေါ် စာရေးသော template မှာ
       alpha က ကတ်ပြား ပုံသဏ္ဌာန်သာ ဖြစ်ပြီး စာသားက RGB ထဲ ရှိသည်ဂ
    """
    im = np.asarray(Image.open(q).convert("RGBA")).astype(np.float32)
    a = im[:, :, 3:4] / 255.0
    rgb = im[:, :, :3] * a + BG * (1.0 - a)
    g = rgb[:, :, 0] * 0.299 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.114
    return g, im[:, :, 3]


# ⚠️ ပုံ ယူသော template ကို ပုံ မပေးဘဲ စစ်လျှင် ဘယ်တော့မှ မအောင်
DEMO_IMG = "/Users/zinthuaung/ikki/web/img/ikki-icon-512.png"
if not os.path.exists(DEMO_IMG): DEMO_IMG = None


def _fill_call(txt, items, tag, nums=None):
    """`G.fill()` (သင်ယူထားသော စာရင်း ပုံစံ) နဲ့ ခေါ်သည် — မရလျှင် `None`။

    ⚠️ `tmplfit` က `thm` ရဲ့ စာရင်း param တွေကို ၁၃-တွဲ အဖြစ် ဖြည့်တတ်သည် —
       `thm.stat_trio` တို့ **၂-တွဲ** လိုသည် (`too many values to unpack`)။
       `gfx_args.json` ထဲ သင်ယူထားသော ပုံစံ (`pair`) မှန်ပြီးသား ဖြစ်လျက်
       `tmplfit` က အရင် ပြေးသဖြင့် မရောက်ခဲ့ ⇒ **ကျရှုံးလျှင် `fill()` နဲ့ ထပ်စမ်း**။
       (thm စာရင်း param ယူသူ ၃၈ ခုကို demoargs လက်နဲ့ မရေးဘဲ ဖြေရှင်းသည်)
    """
    a = G.fill(e, txt, "ZAE", (nums or [62])[0], img=DEMO_IMG, items=items,
               nums=nums)
    if a is None:
        return None
    if DR._wants_tag(e["fn"]):
        a = (tag,) + tuple(a)
    return G.call(e, a, 2.0)


def _demoshape_call(txt, items, tag, nums=None):
    """`argshape` (demoargs ပုံစံ) နဲ့ ခေါ်သည် — မရလျှင် `None`။"""
    kw = G.fill_kw(e, [txt] + list(items or []), img=DEMO_IMG,
                   pct=(nums or [62])[0], nums=nums)
    if not kw:
        return None
    _cwd = os.getcwd()
    try:
        if G.MK not in sys.path:
            sys.path.insert(0, G.MK)
        os.chdir(G.MK)
        import importlib
        _m = importlib.import_module(e["module"])
        _fn = (getattr(_m, "BUILDERS", {}) or {}).get(e["fn"]) or getattr(_m, e["fn"])
        return DR._call_template(_fn, eid, tag, kw)
    finally:
        try: os.chdir(_cwd)
        except Exception: pass


def build(txt, items, tag, nums):
    """engine ရဲ့ လမ်းကြောင်းအတိုင်း — `_tf_args` ⇒ `_call_template`ဂ

    ⚠️ **ခေါ်ခြင်း ကျရှုံးလျှင်ကိုလည်း `argshape` နဲ့ ထပ်စမ်းရမည်**။
       `fill()` က **တဝက်တစ်ပြက်** args ပြန်ပေးတတ်သည် (`maps.route_arc`
       ကို စာသား ၂ ခုတည်း) ⇒ `a is None` မဖြစ်သဖြင့် ပြန်ဆုတ်လမ်း
       အလုပ်မလုပ်ပါ — `gfx_verify.py` မှာ ပြင်ပြီးသားပေမယ့် ဒီမှာ ကျန်ခဲ့
       (၂၀၂၆-၀၉-၂၅: maps ၉ ခု · arg အမျိုးအစား အမှား ၃၅ ခု)။
    """
    a = DR._tf_args(dict(kind=eid, text=txt, items=items, num=str(nums[0])),
                    accent="#FFE000", ink="#FFFFFF", dim="#8B8B8B")
    if not a:
        a = G.fill(e, txt, "ZAE", nums[0], img=DEMO_IMG, items=items,
                   nums=nums)
        # ⚠️ `fill()` က param မလိုသော template အတွက် `()` ပြန်ပေးသည် (မှန်သည်)。
        #    `not a` နဲ့ စစ်လျှင် ကျရှုံးဟု မှတ်မိသည် ⇒ `is None` သာ。
        if a is None:
            # ⚠️ **`demoargs` ပုံစံ ပြန်ဆုတ်လမ်း** — `fill()` ရော `tmplfit` ရော
            #    တည်ဆောက်ပုံ ရှုပ်သော param ကို မဘြည့်နိုင်။ ဒီဂိတ်မှာ မပါလျှင်
            #    render အောင်ပြီးသား template ကိုပါ `gfx_ok.txt` ထဲ မရောက်ပါ
            #    (၂၀၂၆-၀၉-၂၅: ၁၅၃ ခု ဒီအတိုင်း ကျန်ခဲ့)။
            a = G.fill_kw(e, [txt] + list(items or []), img=DEMO_IMG, pct=62)
            if not a:
                return None, "fill ဗလာ"
        # ⚠️ **`"g0"` ကိန်းသေ သုံး၍ မရ** — A နဲ့ B run နှစ်ခုလုံး တူညီသော
        #    ဖိုင်နာမည်သို့ ရေးသဖြင့် `prem._crop()` ရဲ့ cache
        #    (`if not os.path.exists(q)`) က B အတွက် A ရဲ့ PNG ကို ပြန်ပေးကာ
        #    **diff = 0.000** ဖြစ်စေသည် — template က မမှား၊ စစ်ဆေးချက်က မှား。
        #    (၂၀၂၆-၀၉-၂၄: thm ၂၈ ခုထဲ ၁၇ ခု ဤအကြောင်းကြောင့် မှားကျခဲ့)。
        if DR._wants_tag(e["fn"]):
            a = (tag,) + tuple(a)
        try:
            el = G.call(e, a, 2.0)
        except BaseException:
            el = _demoshape_call(txt, items, tag, nums)
            if el is None:
                raise
    else:
        # ⚠️ template တွေက frame ကို **motionkit ရဲ့ cwd** နဲ့ ဆက်စပ်ပြီး
        #    ရေးသည် (`gfxcat.call()` က `os.chdir(MK)` လုပ်သည်) ⇒
        #    မလုပ်လျှင် 「ဖိုင် မရှိ」ဖြစ်သည်ဂ
        _cwd = os.getcwd()
        try:
            if G.MK not in sys.path:
                sys.path.insert(0, G.MK)
            os.chdir(G.MK)
            import importlib
            _m = importlib.import_module(e["module"])
            # ⚠️ `trans` ရဲ့ ၂၄ ခုက factory closure မို့ `BUILDERS` ထဲမှာသာ ရှိသည်
            _fnx = (getattr(_m, "BUILDERS", {}) or {}).get(e["fn"]) \
                or getattr(_m, e["fn"])
            try:
                el = DR._call_template(_fnx, eid, tag, a)
            except BaseException:
                os.chdir(_cwd)
                el = None
                try:
                    el = _fill_call(txt, items, tag, nums)
                except BaseException:
                    el = None
                if el is None:
                    el = _demoshape_call(txt, items, tag, nums)
                if el is None:
                    raise
                os.chdir(G.MK)
        finally:
            try: os.chdir(_cwd)
            except Exception: pass
    if not isinstance(el, dict):
        return None, "dict မဟုတ်"
    fr = el.get("anim") or el.get("frames") or []
    st = el.get("statics") or []
    if len(fr) < 2 and not st:
        return None, "ဖရိမ်း %%d" %% len(fr)

    def rp(q):
        return q if os.path.isabs(q) else os.path.join(G.MK, q)

    # ⚠️⚠️ **「မှင် အများဆုံး frame」ကို ရွေး၍ မရ** — မှင်မျဉ်းကွေးက ထိပ်နားမှာ
    #    ပြားနေသဖြင့် run တစ်ခုနဲ့တစ်ခု အနည်းငယ် ကွာရုံနဲ့ **ရွေးချယ်တဲ့
    #    frame ကွဲ**သွားသည် (0.45 vs 0.55) ⇒ စာသား တူတူနဲ့ ပြန် render လျှင်
    #    မတူတဲ့ frame ၂ ခု နှိုင်းရာ A/A ကွာဟမှု 0.44–0.63 ထွက်ကာ
    #    「မတည်ငြိမ်」ဟု **မှားစွဲချက်** တင်ခဲ့သည် (thm.cmp_* ၆ ခု ·
    #    ၂၀၂၆-၀၉-၂၅)。 template က မမှား၊ တိုင်းချက်က မှား。
    # ⇒ **အတည်တကျ အညွှန်း**တွေမှာသာ နမူနာယူသည် — run နှစ်ခုလုံး တူညီသော
    #    အချိန်ကို နှိုင်းရမည်。 နောက်ဆုံး frame က မှိန်ထွက်ပြီး ဗလာနီးပါး
    #    ဖြစ်တာမို့ ချန်သည်。
    out_fr = []
    # ⚠️ `fr` ဗလာ ဖြစ်နိုင်သည် (board က `statics` တစ်ခုတည်း) ⇒ စစ်ရမည်
    if fr:
        # ⚠️ **နောက်ပိုင်း ပေါ်လာသော စာသားကို မလွတ်စေရ** — မြေပုံ/အညွှန်း
        #    template အများက အညွှန်းကို နောက်ဆုံးမှာပဲ ချသည်။ ၀.၈၈ ကို
        #    မထည့်ရ — နောက်ဆုံး frame က မှိန်ထွက်ပြီး ဗလာနီးပါး။
        for f in (0.35, 0.45, 0.55, 0.65, 0.75, 0.88):
            j = min(len(fr) - 1, max(0, int(len(fr) * f)))
            it = fr[j]
            q = rp(it[0] if isinstance(it, (list, tuple)) else it)
            if not os.path.exists(q):
                continue
            out_fr.append(_flat(q))

    # ⚠️ **`statics` ကို မကျန်စေရ** — စာသားက များသောအားဖြင့် ဤထဲ ရှိသည်
    out = list(out_fr)
    for it in st:
        q = rp(it[0] if isinstance(it, (list, tuple)) else it)
        if os.path.exists(q):
            out.append(_flat(q))
    if not out:
        return None, "ဖိုင် မရှိ"
    return out, None


def cmp(p, q):
    """ပုံရိပ် ကွာဟမှု — ကွာသော pixel ÷ မှင် စုစုပေါင်းဂ

    အရွယ် · အရေအတွက် မတူလျှင် None (= လုံးဝ ကွာ)ဂ
    **အများဆုံးကို ယူသည် — ပျမ်းမျှ မဟုတ်**: စာသားက အစိတ်အပိုင်း တစ်ခုတည်း
    ဖြစ်ပြီး ကျန်တာ ကြီးမားလျှင် ပျမ်းမျှက ရေပေါ်သွားမည်ဂ
    """
    if len(p) != len(q) or any(x[0].shape != y[0].shape for x, y in zip(p, q)):
        return None
    d = 0.0; px = 0
    for (g1, a1), (g2, a2) in zip(p, q):
        m = (a1 > 16) | (a2 > 16)
        un = float(m.sum())
        ch = int(((np.abs(g1 - g2) > TOL) & m).sum())
        px = max(px, ch)
        if un:
            d = max(d, float(ch / un))
    return (d, px)


try:
    A, w = build(%(TA)r, %(IA)r, "s0", %(NA)r)
    if A is None:
        print(json.dumps({"ok": 0, "why": w})); raise SystemExit
    B, w = build(%(TB)r, %(IB)r, "s1", %(NB)r)
    if B is None:
        print(json.dumps({"ok": 0, "why": w})); raise SystemExit
except SystemExit:
    raise
except BaseException as _ex:
    print(json.dumps({"ok": 0,
                      "why": "%%s: %%s" %% (type(_ex).__name__, str(_ex)[:70])}))
    raise SystemExit

ink = max(float((a > 16).mean()) for _, a in A)
_r = cmp(A, B)
ab, abpx = (None, None) if _r is None else _r
if ab is None:
    # အရွယ် ကွာ = စာသားကြောင့် ပုံစံ ပြောင်းသည် ⇒ အောင်
    print(json.dumps({"ok": 1, "diff": 1.0, "aa": 0.0, "ink": round(ink, 5),
                      "why": "အရွယ် ကွာ"}))
    raise SystemExit

# ⚠⚠ **အချိုး (union) နဲ့ မစစ်ရ** — `diff` က မှင် union နဲ့ စားသဖြင့်
#    နောက်ခံ ကြီးသော template မှာ စာသား အပြောင်းအလဲ ပျောက်သည်။
#    တိုင်းချက် (၂၀၂၆-၀၉-၂၅): `thm.cmp_glass` က pixel ၂,၃၀၂ ပြောင်းသည်
#    ဖြစ်လျက် union ၀.၀၀၉ ⇒ ၀.၀၂ အောက်ကျ — `cmp_frame` (၂,၅၂၁ px)
#    ကတော့ union ၀.၀၄၉ ⇒ အောင်။ **တူသော လုပ်ဆောင်မှု · ဘောင်အရွယ်ကြောင့်
#    ဆုံးဖြတ်ချက် ကွဲ**။
#    A/A ထိန်းချုပ်မှုက template ၁၀ ခုမှာ **pixel ၀ တိတိ** ⇒ ဆူညံမှု
#    အောက်ခံက သုည။ ⇒ pixel အရေအတွက်နဲ့ ဂိတ်လုပ်သည် (ဘောင်အရွယ်နဲ့ မဆိုင်)။
if abpx < %(DPX)d:
    print(json.dumps({"ok": 0, "diff": round(ab, 4), "dpx": abpx,
                      "ink": round(ink, 5),
                      "why": "စာသား ပြောင်းလည်း ပုံရိပ် မပြောင်း (pixel %%d · union %%0.4f)"
                             %% (abpx, ab)}))
    raise SystemExit

# ⚠️ **A/A ထိန်းချုပ်မှု** — စာသား တူတူနဲ့ ထပ် render လုပ်ပြီး ကျပန်းလား စစ်သည်ဂ
#    ဂိတ် ကျော်ပြီးမှ လုပ်သဖြင့် ကျသွားသော template တွေမှာ အချိန် မကုန်ဂ
try:
    A2, w = build(%(TA)r, %(IA)r, "s2", %(NA)r)
except BaseException as _ex:
    A2, w = None, "%%s: %%s" %% (type(_ex).__name__, str(_ex)[:60])
if A2 is None:
    print(json.dumps({"ok": 0, "diff": round(ab, 4), "ink": round(ink, 5),
                      "why": "A/A မရ (%%s)" %% w}))
    raise SystemExit
_r2 = cmp(A, A2)
aa, aapx = (None, None) if _r2 is None else _r2
if aa is None:
    print(json.dumps({"ok": 0, "diff": round(ab, 4), "aa": 1.0, "ink": round(ink, 5),
                      "why": "မတည်ငြိမ် — စာသား တူလျက် အရွယ် ကွာ"}))
    raise SystemExit

# ⚠️ A/A ကို pixel နဲ့ပါ စစ်သည် — တိုင်းရမှာ A/A = ၀ px ဖြစ်သဖြင့်
#    A/B က A/A ထက် သိမ်သိမ် များရမည်။
ok = 1 if (abpx >= %(DPX)d and abpx >= 4 * aapx) else 0
print(json.dumps({"ok": ok, "diff": round(ab, 4), "aa": round(aa, 4),
                  "dpx": abpx, "aapx": aapx,
                  "ink": round(ink, 5),
                  "why": "" if ok else
                         "မတည်ငြိမ် — စာသား တူလျက် pixel %%d ကွာ (A/B %%d)" %% (aapx, abpx)}))
''' % {"HERE": HERE, "TA": TXT_A, "TB": TXT_B, "IA": ITM_A, "IB": ITM_B,
       "DM": DIFF_MIN, "AAM": AA_MAX, "AOA": AB_OVER_AA, "DPX": DIFF_PX,
       "NA": NUM_A, "NB": NUM_B}


# ⚠️ **စာသား param မရှိသော template ကို ဂိတ်③နဲ့ မစစ်ရ**。 ဂိတ်③ က စာသား
#    ၂ မျိုး ပေးပြီး ပုံရိပ် ပြောင်းမပြောင်း တိုင်းသည် — `trans` ၂၄ ခု ·
#    `motionfx` ၁၉ ခု စသဖြင့် **၆၁ ခု**က စာသား လုံးဝ မယူပါ (အသွင်ကူး ·
#    နောက်ခံ လှုပ်ရှားမှု)。 အဲဒါတွေကို စစ်လျှင် diff = 0.000 နဲ့
#    「စာသား မရေး」ဟု ကျပြီး `gfx_ok.txt` ကနေ **ထုတ်ပစ်**မည် — ဂိတ်က
#    မှားခြင်း ဖြစ်သည်၊ template က မမှား (၂၀၂၆-၀၉-၂၅)。
#    ⇒ signature ကနေ ကြည့်ပြီး ကင်းလွတ် ပေးသည် (လက်နဲ့ စာရင်း မရေးရ)。
# ⚠️ **enum/စတိုင် ရွေးချယ် param ကို စာသား ဓု မမှတ်ရ** — `shape="circle"` က
#    စာရိုက်ပုံ ရွေးချယ်မှု ဖြစ်ပြီး အကြောင်းအရာ မဗုတ်။ catalog က default စာသား
#    ဖြစ်လျှင် "text" ဟု မှတ်သဖြင့် `motionfx.shape_wipe` က စာသား ပါသည်
#    ဟု ထင်ပြီး ဂိတ်③ တင်ကာ မအောင်နိုင်ခဲ့ (၂၀၂၆-၀၉-၂၅)။
_ENUM_SKIP = ("shape", "kind", "style", "align", "mode", "variant", "dir",
              "side", "layout", "anim", "ease", "fit", "pos")
_NOTEXT_SKIP = ("img", "imgs", "img_path", "logo", "logos", "image",
                "img1", "img2", "img_a", "img_b", "base", "src") + _ENUM_SKIP


def has_text_param(ent):
    """template က စာသား/စာရင်း param ယူသလား — ဂိတ်③ သက်ဆိုင်မသက်ဆိုင်。"""
    for p in ent.get("params") or []:
        if p.get("auto") or p.get("name") in ("dur", "tag"):
            continue
        if p.get("type") in ("text", "list") and p.get("name") not in _NOTEXT_SKIP:
            return True
    return False


def main():
    import gfxcat as G
    only = None
    limit = 0
    for i, a in enumerate(sys.argv):
        if a == "--only" and i + 1 < len(sys.argv):
            only = set(sys.argv[i + 1].split(","))
        elif a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    # ⚠️ **`usable()` က ၅၀၂ ခုသာ ပြန်ပေးသည်** — `mockup` · `transition` ·
    #    `motion` ၁၁၄ ခုကို ဘယ်တော့မှ မစစ်ဖြစ် ⇒ `gfx_gate` မှာ းကို
    #    မစစ်ရသောပေ အဖြစ်သာ ကျန်နေသည်။ `gfx_verify.py` နဲ့ တူသည့်
    #    `GFX_ALL=1` ဆွာ ရှိရမည် (၂၀၂၆-၀၉-၂၅)။
    ents = G.catalog() if os.environ.get("GFX_ALL") else G.usable()
    # ⚠️ `GFX_ONLY` ကိုလည်း လက်ခံရမည် — `gfx_verify.py` က env နဲ့ပဲ ရှိသဖြင့်
    #    `--only` တစ်ခုတည်း ဆိုလျှင် တိတ်ဆိတ် ၁၅၀၂ ခုလုံး ပြေးသွားတတ်သည်။
    if not only and os.environ.get("GFX_ONLY"):
        only = set(os.environ["GFX_ONLY"].split(","))
    if only:
        ents = [e for e in ents if e["id"] in only]
    if limit:
        ents = ents[:limit]
    print(f"စစ်မည် {len(ents)} ခု · စာသား ၂ မျိုး + A/A ထိန်းချုပ် · "
          f"ဂိတ် diff ≥{DIFF_MIN} · A/A ≤{AA_MAX} · timeout {TIMEOUT}s", flush=True)
    res, t0 = [], time.time()
    for i, e in enumerate(ents, 1):
        r = {"id": e["id"], "category": e.get("category")}
        if not has_text_param(e):
            r.update({"ok": 1, "diff": None, "aa": None,
                      "why": "စာသား param မရှိ — ဂိတ်③ မသက်ဆိုင်"})
            res.append(r)
            print(f"  [{i:3d}/{len(ents)}] – {e['id']:34s} "
                  f"စာသား param မရှိ — ကိင်းလွတ်", flush=True)
            continue
        try:
            p = subprocess.run([sys.executable, "-c", CHILD, e["id"]],
                               capture_output=True, text=True, timeout=TIMEOUT,
                               cwd=HERE)
            out = [l for l in (p.stdout or "").splitlines() if l.startswith("{")]
            r.update(json.loads(out[-1]) if out else
                     {"ok": 0, "why": "ထွက်ချက် ဗလာ"})
        except subprocess.TimeoutExpired:
            r.update({"ok": 0, "why": f"{TIMEOUT}s ကျော်"})
        except Exception as ex:
            r.update({"ok": 0, "why": f"{type(ex).__name__}: {ex}"})
        res.append(r)
        print(f"  [{i:3d}/{len(ents)}] {'✓' if r.get('ok') else '✖'} "
              f"{e['id']:34s} diff={r.get('diff', '—')} aa={r.get('aa', '—')} "
              f"{str(r.get('why',''))[:40]}", flush=True)
    ok = [r for r in res if r.get("ok")]
    print(f"\nစာသား တကယ် ရေး {len(ok)}/{len(res)} · {time.time()-t0:.0f}s", flush=True)
    # ⚠️ အပိုင်း ပြေးလျှင် **ပေါင်း**သည် (မလွှမ်းရ)
    old = []
    if os.path.exists(OUT):
        try: old = json.load(open(OUT, encoding="utf-8")) or []
        except Exception: old = []
    merged = {r["id"]: r for r in old}
    merged.update({r["id"]: r for r in res})
    _DIO.write_derived(OUT, sorted(merged.values(), key=lambda r: r["id"]),
                       writer=__file__)
    print(f"ရေးပြီး — {OUT} ({len(merged)} entry)")
    # ⚠️ S-c — provenance **သာ** မှတ်သည် · ဖိုင် ပြန်မထုတ်ပါ။
    #    ဒီ run မှာ တကယ် စစ်ခဲ့သော id များသာ မှတ်ရမည် — အပိုင်းလိုက်
    #    ပြေးလျှင် ကျန် template များ ဟောင်းတုန်း ဖြစ်ရမည် (S-a)。
    if _DC is not None:
        try:
            _DC.record("gfx_textsens", ids=[r["id"] for r in res])
        except Exception as _pe:
            print("  ⚠️ provenance မမှတ်နိုင်: %s" % _pe, flush=True)


if __name__ == "__main__":
    main()
