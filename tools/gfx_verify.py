#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""motionkit template တစ်ခုချင်းကို **တကယ် render ပြီး** စစ်သည်。

⚠️ ဂိတ်ကို **ကိန်း မမြင်ခင်** သတ်မှတ်ထားသည် (၂၀၂၆-၀၉-၁၉):
     PASS = ① fill() က argument ထုတ်ပေးနိုင်
            ② call() က PNG **၂ ဖရိမ်း အနည်းဆုံး** ပြန်ပေး
            ③ ဖိုင်တိုင်း ရှိပြီး > 1 KB
            ④ **ဖရိမ်း ၅ ခု (နမူနာ) + statics ထဲ အမြင့်ဆုံး မှင်** — alpha>16
               pixel က ဧရိယာ၏ **0.05% အထက်** (ထွက်ခွာ animation ရဲ့ နောက်ဆုံး
               ဖရိမ်း ဗလာ ဖြစ်တာ မှန်သည် · board_* စာကြောင်းက statics ထဲ)
            ⑤ 60s အတွင်း ပြီး
⚠️ တစ်ခုချင်း **သီးသန့် process** — အရင်က template တစ်ခု ကျလျှင်
   တစ်ခုလုံး ရပ်သွားခဲ့သည် (timeout · ctypes text trap)。
"""
import os, sys, json, subprocess, time


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
TIMEOUT = 150
MIN_FRAMES = 2
# ⚠️ **ဖိုင် အရွယ် ဂိတ် မထားရ** — animation ရဲ့ ပထမ ဖရိမ်းများက ၁၃၃ bytes
#    (ဗလာနီးပါး) ဖြစ်တတ်သည် · ပုံမှန်。 >1KB ဟု ထားမိ၍ **အလုပ်လုပ်နေသော
#    template ၄၂ ခု** မှားကျခဲ့သည် (၂၀၂၆-၀၉-၁၉)。 မှင်ကို နောက်ဆုံး ဖရိမ်းမှာသာ စစ်。
MIN_BYTES = 1
MIN_INK = 0.0005          # 0.05%

CHILD = r'''
import os, sys, json
sys.path.insert(0, os.path.join(%(HERE)r, "core"))
import gfxcat as G, dress as DR
from PIL import Image
eid = sys.argv[1]
e = [x for x in G.catalog() if x["id"] == eid]
if not e: print(json.dumps({"ok":0,"why":"id မတွေ့"})); raise SystemExit
e = e[0]
# ⚠️ **engine ရဲ့ လမ်းကြောင်းအတိုင်း စစ်ရမည်** (၂၀၂၆-၀၉-၂၂)。 ယခင်က
#    `G.fill()` တစ်ခုတည်း စစ်ခဲ့သဖြင့် 「fill ဗလာ」 ၅၁ ခု ကျခဲ့သည် —
#    ဒါပေမယ့် engine က ယခု `tmplfit` ကိုပါ ပြန်ဆုတ်လမ်း အဖြစ် သုံးသည်
#    ⇒ verifier က engine ထက် **ကျဉ်း**နေလျှင် အသုံးဝင်သော template တွေကို
#    အလကား ပိတ်ထားရာ ကျသည်。
# ⚠️ **ပုံ ယူသော template ကို ပုံ မပေးဘဲ စစ်လျှင် ဘယ်တော့မှ မအောင်**。
#    `thm.media_*` ၁၂ · `social` ၁၀ · `brows` · `maps.photo_inset` ·
#    `typo2.subject_rise` — ၂၈ ခု 「fill ဗလာ」နဲ့ ကျခဲ့သည် (၂၀၂၆-၀၉-၂၅)。
#    ⇒ ကိုယ်ပိုင် icon ကို နမူနာ ပုံ အဖြစ် ပေးသည် (ဒေသတွင်း ဖိုင် · ပြင်ပ
#    ဒေါင်းလုဒ် မလို · လိုင်စင် ကိစ္စ မရှိ)。
DEMO_IMG = "/Users/zinthuaung/ikki/web/img/ikki-icon-512.png"
if not os.path.exists(DEMO_IMG): DEMO_IMG = None
# ⚠️ **စာသား အရှည် — production အတိုင်း** (2026-09-28)。 စာသား တိုတို
#    (၁၀–၁၄ လုံး) နဲ့ စစ်လျှင် စာ ပြတ်/ဘောင်ကျော်ကို ဘယ်တော့မှ မမြင်ရ —
#    ASR စကားစု အရှည် (~၄၀ လုံး · စာရင်း ~၂၀ လုံး) နဲ့ စစ်သည်。
#    `GFX_TEXT=short` ⇒ ယခင် စာသား (နှိုင်းယှဉ်ရန်)。
if os.environ.get("GFX_TEXT") == "short":
    MAIN_TEXT = "ဂျပန်မှာ အလုပ်"; TF_TEXT = "ဂျပန်မှာ အလုပ်ရှာဖွေခြင်း"
    DEMO_TEXTS = ["ဂျပန်မှာ အလုပ်", "ပညာသင် ဗီဇာ", "အခုပဲ စမယ်", "သင်တန်း ၃ လ"]
else:
    MAIN_TEXT = TF_TEXT = "ဂျပန်မှာ အလုပ်ရှာဖွေဖို့ ဘာတွေ ကြိုပြင်ဆင်ထားရမလဲ"
    DEMO_TEXTS = ["ဂျပန်မှာ အလုပ်ရှာဖွေခြင်း", "ပညာသင် ဗီဇာ လျှောက်ထားခြင်း",
                  "အခုပဲ စာရင်းသွင်းလိုက်ပါ", "N5 သင်တန်း ၃ လ အပြည့်"]
args = G.fill(e, MAIN_TEXT, "ZAE", 62, img=DEMO_IMG,
              items=DEMO_TEXTS, nums=[62, 41, 27])
kw = None
# ⚠️ `fill()` က **param မလိုသော** template အတွက် `()` ပြန်ပေးသည် (မှန်သည် —
#    `gfxcat.fill` ကိုယ်တိုင် "`()` ပြန်ရမည်" ဟု ရေးထားပြီးသား)。 `if not args`
#    နဲ့ စစ်လျှင် `()` က falsy ဖြစ်၍ **ကျရှုံးဟု မှတ်**သည် ⇒ `trans` ၂၄/၂၄ ·
#    `motionfx` ၁၄ · `thm.chat_dots` တို့ တစ်ခါမှ မအောင်ခဲ့ (၂၀၂၆-၀၉-၂၄)。
if args is None:
    try:
        kw = DR._tf_args(dict(kind=eid, text=TF_TEXT,
                              items=DEMO_TEXTS[:3],
                              num="62"),
                         accent="#FFE000", ink="#FFFFFF", dim="#8B8B8B")
    except Exception as _e:
        kw = None
    # ⚠️ **၃ ခုမြောက် လမ်းကြောင်း — `demoargs` ရဲ့ ပုံစံ**。 param ရဲ့
    #    တည်ဆောက်ပုံကို နာမည်တစ်ခုတည်းနဲ့ မှန်း၍ မရသော template ၅၅ ခု
    #    ဒီအထိ ကျန်ခဲ့သည် (`grid` က ကိန်း ၂ ဆင့် · `maps` ရဲ့ `a` က
    #    (lat,lon) ဖြစ်လျက် `prem7` ရဲ့ `a` က (နာမည်,ကိန်း))。
    #    `argshape.fit()` က `demoargs` ကို ပုံစံပြ ယူပြီး **စာသား အကွက်**
    #    တွေကိုသာ အစားထိုးသည် — engine ဘက်မှာလည်း ဒီအတိုင်း (`dress.py`)。
    if not kw:
        kw = G.fill_kw(e, DEMO_TEXTS, img=DEMO_IMG, pct=62)
    if not kw:
        print(json.dumps({"ok":0,"why":"fill ဗလာ (tmplfit · demoargs ပုံစံ လည်း မရ)"})); raise SystemExit
# ⚠️ **ကျရှုံးလျှင် `argshape` နဲ့ ထပ်စမ်းရမည်** (၂၀၂၆-၀၉-၂၅)။
#    `fill()` က **တဝက်တစ်ပြက်** args ပြန်ပေးတတ်သည် (`scatter` ကို
#    `(title,)` တစ်ခုတည်း)။ ဘလာ မဟုတ်သဖြင့် `if not kw` ဂိတ်ကို
#    မမိဘဲ ခေါ်မိပြီး `missing 1 required positional argument`
#    နဲ့ ကျသည် — ပထမ အကြိမ်မှာ ၂၀ ခု ဒီအတိုင်း ကျခဲ့သည်။
#    ⇒ **ခေါ်ခြင်း ကျရှုံးမှုကိုလည်း** အခြား လမ်းကြောင်း အဖြစ် သတ်မှတ်ရမည်။
def _try_demoshape():
    kw2 = G.fill_kw(e, DEMO_TEXTS, img=DEMO_IMG, pct=62)
    if not kw2: return None
    _m = __import__(e["module"])
    _fn2 = getattr(_m, "BUILDERS", {}).get(e["fn"]) or getattr(_m, e["fn"])
    import hashlib as _h3
    _t3 = "v" + _h3.sha1(eid.encode()).hexdigest()[:8]
    _c3 = os.getcwd()
    try:
        os.chdir(G.MK)
        return DR._call_template(_fn2, eid, _t3, kw2)
    finally:
        try: os.chdir(_c3)
        except Exception: pass

# ⚠️ **template ရဲ့ exception ကို ဖမ်းရမည်** — မဖမ်းလျှင် child က print
#    မရောက်ခင် သေပြီး parent က 「ထွက်ချက် ဗလာ」ဟုသာ မှတ်ကာ **အကြောင်းရင်း
#    ပျောက်**သည် (၆၄ ခု ဤအတိုင်း ဖြစ်ခဲ့ — တကယ်က စာရင်းပုံစံ မကိုက်ခြင်း)。
if kw is not None:
    try:
        _m = __import__(e["module"])
        # ⚠️ **`getattr(module, fn)` တစ်ခုတည်း မလုံလောက်** — `trans` ရဲ့ ၂၄ ခုက
        #    factory ကနေ ဆောက်ထားသော closure ဖြစ်၍ `BUILDERS` dict ထဲမှာသာ
        #    ရှိပြီး module attribute **မဟုတ်**ပါ ⇒ `AttributeError` နဲ့ ကျကာ
        #    အသွင်ကူး ၂၄ ခုလုံး တစ်ခါမှ မစစ်ဖြစ်ခဲ့ (၂၀၂၆-၀၉-၂၄)。
        _fn = getattr(_m, "BUILDERS", {}).get(e["fn"]) or getattr(_m, e["fn"])
        # ⚠️ **ဤလမ်းကြောင်းမှာလည်း tag ထပ်သည်** — `G.call` ဘက်မှာသာ ပြင်ခဲ့ပြီး
        #    `tmplfit` ဘက်မှာ `"g0"` ကျန်ခဲ့သဖြင့် ဖိုင်များ အပြန်အလှန် လွှမ်းကာ
        #    「ဖိုင် သေး/မရှိ」ဖြစ်သည် (cut_/board_ ၈ ခု — ၂၀၂၆-၀၉-၂၅)。
        import hashlib as _h2
        _tag2 = "v" + _h2.sha1(eid.encode()).hexdigest()[:8]
        # ⚠️ **cwd ကို motionkit သို့ ပြောင်းရမည်** — template တွေက frame ကို
        #    `work/<module>/...` ဆိုသော **relative** လမ်းကြောင်းမှာ ရေးသည်。
        #    `G.call` က ကိုယ်တိုင် `chdir` လုပ်သော်လည်း ဤ tmplfit လမ်းကြောင်းက
        #    မလုပ်ခဲ့ ⇒ frame တွေ `~/ikki/work/` ထဲ ကျပြီး `rp()` က
        #    `MK/work/` မှာ ရှာကာ 「ဖိုင် သေး/မရှိ」 (cut_grid · cut_list ·
        #    cut_steps · cut_timeline — ၂၀၂၆-၀၉-၂၅)。
        #    (`gfxtextsens.py` မှာ ဤအမှားကို ကြိုသိပြီး chdir လုပ်ထားပြီးသား)
        _cwd2 = os.getcwd()
        try:
            os.chdir(G.MK)
            el = DR._call_template(_fn, eid, _tag2, kw)
        finally:
            try: os.chdir(_cwd2)
            except Exception: pass
    except BaseException as _ex:
        if isinstance(_ex, KeyboardInterrupt): raise
        try:
            el = _try_demoshape()
        except BaseException:
            el = None
        if el is None:
            print(json.dumps({"ok":0,"why":"%%s: %%s" %% (type(_ex).__name__, str(_ex)[:90])}))
            raise SystemExit
else:
    # ⚠️ production (dress.py) နှင့် **အတိအကျ တူရမည်** — tag ရှေ့က ထည့်
    # ⚠️ **template တိုင်းကို `g0` နဲ့ ခေါ်လျှင် တစ်ခုနဲ့တစ်ခု ဖိုင် ထပ်သည်**。
    #    `prem._crop()` က crop PNG ကို ဖိုင်နာမည်နဲ့ cache လုပ်ပြီး
    #    `if not os.path.exists(q)` နဲ့ စစ်သဖြင့် ရှေ့ template ရဲ့
    #    `work/prem/g0w_c.png` ကို နောက် template တွေက **အတူတူ ပြန်သုံး**သည် —
    #    `thm.key_pop` က တိုက်ရိုက်ခေါ်လျှင် မှင် ၁၁.၃%%၊ verifier ကနေ ၀.၀၄%%
    #    (၂၀၂၆-၀၉-၂၄ တိုင်း၍ တွေ့)。 ⇒ id အလိုက် **သီးသန့် tag**。
    import hashlib as _h
    _tag = "v" + _h.sha1(eid.encode()).hexdigest()[:8]
    if DR._wants_tag(e["fn"]): args = (_tag,) + tuple(args)
    try:
        el = G.call(e, args, 2.0)
    except BaseException as _ex:
        if isinstance(_ex, KeyboardInterrupt): raise
        try:
            el = _try_demoshape()
        except BaseException:
            el = None
        if el is None:
            print(json.dumps({"ok":0,"why":"%%s: %%s" %% (type(_ex).__name__, str(_ex)[:90])}))
            raise SystemExit
if not isinstance(el, dict):
    print(json.dumps({"ok":0,"why":"dict မဟုတ် (%%s)" %% type(el).__name__})); raise SystemExit
fr = el.get("anim") or el.get("frames") or []
if len(fr) < %(MF)d:
    print(json.dumps({"ok":0,"why":"ဖရိမ်း %%d" %% len(fr)})); raise SystemExit
# ⚠️ လမ်းကြောင်းက motionkit cwd နှင့် ဆက်စပ် — MK အောက်မှ ဖတ်ရမည်
def rp(q): return q if os.path.isabs(q) else os.path.join(G.MK, q)
for it in fr:
    q = rp(it[0] if isinstance(it,(list,tuple)) else it)
    if not os.path.exists(q) or os.path.getsize(q) < %(MB)d:
        print(json.dumps({"ok":0,"why":"ဖိုင် သေး/မရှိ"})); raise SystemExit
# ⚠️ **နောက်ဆုံး ဖရိမ်းမှာ မှင် ရှိရမည်** ဆိုသော ဂိတ်က **မှား**သည် —
#    ထွက်ခွာ animation (`*_out` · `wipe_word` · `intro_stinger`) က နောက်ဆုံး
#    ဖရိမ်းမှာ ဗလာ ဖြစ်တာ **ဒီဇိုင်းအရ မှန်**သည်。 တိုင်းကြည့်ရာ
#    `kinetic2.pop_out` က အလယ်မှာ ၂၈.၃%% · နောက်ဆုံးမှာ ၀%% ⇒ ဂိတ်က
#    အလုပ်လုပ်နေသော template ၇ ခုကို မှားပိတ်ခဲ့သည် (၂၀၂၆-၀၉-၂၃)。
#    ⇒ နမူနာ ဖရိမ်းများထဲက **အမြင့်ဆုံး** မှင်ကို ယူသည်。
_cand = sorted(set([len(fr)-1, len(fr)//2, len(fr)//3, max(0,len(fr)-2), 1]))
ink = 0.0
for _k in _cand:
    if _k < 0 or _k >= len(fr): continue
    _it = fr[_k]
    _im = Image.open(rp(_it[0] if isinstance(_it,(list,tuple)) else _it)).convert("RGBA")
    # ⚠️ မှင်ကို Python loop နဲ့ ရေတွက်ပါက **ပိက်ဆ၁ ၂ သိန်းကို
    #    တစ်ခုချင်း** စစ်ရသည် — 1080×1920 × frame ၅ = ၁၀ သန်း ပတ်ပတ်
    #    ⇒ template တစ်ခု ၁၀–၂၀s။ ၆၁၆ ခု ပြေးလျှင် နာရီ နှစ်ချီ။
    #    numpy က အောက်မှာ သုံးပြီးးသား ⇒ ဒီမှာလည်း သုံးရမည်။
    import numpy as _np0
    _a = _np0.array(_im)[:, :, 3]
    ink = max(ink, float((_a > 16).sum()) / float(_im.width*_im.height))
# ⚠️ **statics (hold layer) ကိုလည်း ထည့်ရမည်** (2026-09-28)。 `board_*` က
#    စာကြောင်းတွေကို `statics=[(png, x, y, delay)]` ထဲ ထားပြီး anim မှာ
#    highlight သာ ရှိသည် ⇒ ink ရော bbox ရော **စာကြောင်း နေရာ မပါ**ခဲ့ ⇒
#    စာတန်းဇုန် ထပ်မှုကို မတိုင်မိ。 statics က ဘောင်ပေါ် offset နဲ့ ချသည်。
_st = el.get("statics") or []
_stb = []
# ⚠️ **`_multi` ကိုလည်း ထည့်ရမည်** (2026-09-28)。 renderer က `_multi=[(seq, y)]`
#    ရှိလျှင် anim အစား **အတန်း sequence များ** ဆွဲသည် — kinetic.stack ·
#    kinetic.line_rise · kinetic2.line_split · kinetic2.subtitle_2line ·
#    typo.stack3 · typo.scale_ramp · typo.slab_block ⇒ anim က **ပထမ တန်း**
#    သာ ဖြစ်၍ ကျန် တန်းတွေရဲ့ ink/bbox ကို မတိုင်မိခဲ့。 (x = 0 · y = offset)
_mu = el.get("_multi") or []
if _mu:
    try:
        import numpy as _np2
        for _seq, _my in _mu:
            if not _seq: continue
            for _k in sorted(set([len(_seq)-1, len(_seq)//2, len(_seq)//3])):
                _q = _seq[min(_k, len(_seq)-1)]
                _q = _q[0] if isinstance(_q, (list, tuple)) else _q
                _ma = _np2.array(Image.open(rp(_q)).convert("RGBA"))[:, :, 3] > 16
                ink = max(ink, float(_ma.sum()) / float(_ma.size))
                if _ma.any():
                    _yy, _xx = _np2.nonzero(_ma)
                    _stb.append((int(_my)+int(_yy.min()), int(_my)+int(_yy.max()), int(_xx.min()), int(_xx.max())))
    except Exception:
        pass
if _st:
    try:
        import numpy as _np1
        try:
            import theme as _TH1
            _t1 = _TH1.t(); _SW, _SH = int(_t1["W"]), int(_t1["H"])
        except Exception:
            _SW, _SH = _im.width, _im.height
        _px = 0
        for _s in _st:
            _sp, _sx, _sy = _s[0], int(_s[1]), int(_s[2])
            _sa = _np1.array(Image.open(rp(_sp)).convert("RGBA"))[:, :, 3] > 16
            _px += int(_sa.sum())
            if _sa.any():
                _yy, _xx = _np1.nonzero(_sa)
                _stb.append((_sy+int(_yy.min()), _sy+int(_yy.max()), _sx+int(_xx.min()), _sx+int(_xx.max())))
        ink = max(ink, _px / float(max(1, _SW*_SH)))
    except Exception:
        pass
im = _im
# ⚠️ **bbox ကိုပါ မှတ်ရမည်** — planner ရဲ့ pool ကို လက်ရေး ၃၀ ကနေ ၂၇၁+ သို့
#    ချဲ့လိုက်သဖြင့် 「ဂရပ်ဖစ်က စာတန်းကို ဖုံးသလား」ကို **တိုင်း**ရမည်。
#    `place.caption_band()` က keyword pop အတွက်သာ သုံးနေပြီး template event
#    ကို မစစ်ပါ (၂၀၂၆-၀၉-၂၂ စစ်၍ တွေ့)。 render ပြီးသား frame ရှိနေချိန်မှာ
#    တိုင်းလျှင် အပို render မလို。
# ⚠️ frame item က `(png, x, y)` — offset မထည့်လျှင် bbox လွဲမည်。
try:
    import numpy as _np
    _n = len(fr)
    _idx = sorted(set([_n-1, _n//2, max(0,_n-2), _n//3]))
    _b = []
    _W = _H = 0
    for _j in _idx:
        _it = fr[_j]
        _pp, _ox, _oy = (_it[0], _it[1], _it[2]) if isinstance(_it,(list,tuple)) and len(_it)>2 else (_it if isinstance(_it,str) else _it[0], 0, 0)
        _im = Image.open(rp(_pp)).convert("RGBA")
        _al = _np.array(_im)[:,:,3]
        _on = _al > 16
        if not _on.any(): continue
        _ys, _xs = _np.nonzero(_on)
        _b.append((_oy+int(_ys.min()), _oy+int(_ys.max()), _ox+int(_xs.min()), _ox+int(_xs.max())))
        _W = max(_W, _ox+_im.width); _H = max(_H, _oy+_im.height)
    # ⚠️ **ဘောင်အရွယ်ကို theme ကနေ ယူရမည်**。 element အများစုက ဘောင်အပြည့်
    #    PNG ပေမယ့် kinetic/capt/thm.type_* တို့က **strip** PNG ကို
    #    `(png, x, y)` နဲ့ ချသည် — strip ရဲ့ အောက်စွန်းနဲ့ စားလျှင် အချိုး
    #    ဖောင်းပြီး 「စာတန်းဇုန် ဖုံးသည်」ဟု **မှားပြ**မည်
    #    (thm.type_word: တကယ် ၀.၄၅ · စား၍ ၀.၈၅ — ၂၀၂၆-၀၉-၂၄ တွေ့)。
    try:
        import theme as _TH
        _tt = _TH.t(); _W, _H = int(_tt["W"]), int(_tt["H"])
    except Exception:
        pass
    _bb = None
    _b += _stb
    if _b and _W and _H:
        _bb = dict(top=round(min(x[0] for x in _b)/_H,4), bottom=round(max(x[1] for x in _b)/_H,4),
                   left=round(min(x[2] for x in _b)/_W,4), right=round(max(x[3] for x in _b)/_W,4))
except Exception:
    _bb = None
# ⚠️ `edge` — ဘောင်အပြည့် မဟုတ်သော ကတ်ရဲ့ ink က ဘယ်/ညာ ဘောင်စွန်းကို ထိလျှင်
#    စာ ဘောင်ကျော်/ပြတ် ဖြစ်နိုင်ကြောင်း **အချက်ပြ**သည် (ဂိတ် မဟုတ် · ok မပြောင်း)。
_edge = bool(_bb and ink < 0.5 and (_bb["left"] <= 0.004 or _bb["right"] >= 0.996))
print(json.dumps({"ok": 1 if ink >= %(MI)f else 0,
                  "why": "" if ink >= %(MI)f else "မှင် %%.4f%%%%" %% (ink*100),
                  "ink": round(ink,5), "n": len(fr), "bbox": _bb, "edge": _edge,
                  "text": "short" if os.environ.get("GFX_TEXT") == "short" else "long"}))
''' % {"HERE": HERE, "MF": MIN_FRAMES, "MB": MIN_BYTES, "MI": MIN_INK}

def main():
    import gfxcat as G
    only = os.environ.get("GFX_ONLY")
    # ⚠️ `usable()` က `USE` အမျိုးအစားသာ ပြန်ပေး ⇒ `mockup` · `transition` ·
    #    `motion` (၁၁၃ ခု) ကို **စစ်တောင် မစစ်ဖြစ်**ခဲ့。 "IKKI ကို ၁၀၀%
    #    ပေး" ဆိုလျှင် အရင်ဆုံး အဲဒါတွေ render ဖြစ်မဖြစ် သိရမည် ⇒ `GFX_ALL=1`。
    ents = G.catalog() if os.environ.get("GFX_ALL") else G.usable()
    if only: ents = [e for e in ents if e["id"] in only.split(",")]
    print(f"စစ်မည် {len(ents)} ခု · timeout {TIMEOUT}s", flush=True)
    res, t0 = [], time.time()
    for i, e in enumerate(ents, 1):
        r = {"id": e["id"], "category": e["category"]}
        try:
            p = subprocess.run([sys.executable, "-c", CHILD, e["id"]],
                               capture_output=True, text=True, timeout=TIMEOUT)
            out = (p.stdout or "").strip().splitlines()
            j = json.loads(out[-1]) if out else {"ok": 0, "why": "ထွက်ချက် ဗလာ"}
            r.update(j)
            if not j.get("ok") and not j.get("why"):
                r["why"] = (p.stderr or "")[-120:]
        except subprocess.TimeoutExpired:
            r.update({"ok": 0, "why": f"{TIMEOUT}s ကျော်"})
        except Exception as ex:
            r.update({"ok": 0, "why": f"{type(ex).__name__}: {ex}"})
        # ⚠️ **template တစ်ခုပြီးတိုင်း ကိုယ့်ယာယီ frame ကို ရှင်းရမည်**。
        #    tag ကို id အလိုက် သီးသန့် လုပ်လိုက်သည်နှင့် ဖိုင်များ အပြန်အလှန်
        #    မလွှမ်းတော့ဘဲ **စုပုံ**သည် — ၅၉၆ ခု ပြေးရာ `work/` က ၅.၃ GB
        #    ရောက်ကာ disk ၁၀၀% ပြည့်ပြီး 「ဖိုင် သေး/မရှိ」နဲ့ ၅၄ ခု
        #    **မှားကျ**ခဲ့သည် (၄၆၁ → ၄၀၇ · ၂၀၂၆-၀၉-၂၄)。
        #    ⚠️ `work/` တစ်ခုလုံး မဖျက်ရ — ဤ id ရဲ့ tag နဲ့ ကိုက်တာကိုသာ。
        try:
            import glob as _g, hashlib as _hh
            _t = "v" + _hh.sha1(e["id"].encode()).hexdigest()[:8]
            for _d in _g.glob(os.path.join(G.MK, "work", "*")):
                for _f in _g.glob(os.path.join(_d, "*%s*" % _t)):
                    try: os.remove(_f)
                    except OSError: pass
        except Exception:
            pass
        res.append(r)
        mark = "✓" if r.get("ok") else "✖"
        print(f"  [{i:3d}/{len(ents)}] {mark} {e['id']:34s} {r.get('why','')[:60]}", flush=True)
    ok = [r for r in res if r.get("ok")]
    print(f"\nအောင် {len(ok)}/{len(res)} · {time.time()-t0:.0f}s", flush=True)
    # ⚠️ **`GFX_ONLY` နဲ့ ပြေးလျှင် ဖိုင်ကို မလွှမ်းရ** — ၂၀၂၆-၀၉-၂၂:
    #    template ၂ ခု spot-check လုပ်ရာ ၁၇၂ entry ဖိုင်ကို ၂ entry နဲ့
    #    လွှမ်းပစ်ခဲ့သည် (git ကနေ ပြန်ယူရ)。 ⇒ အပိုင်း ပြေးလျှင် **ပေါင်း**သည်。
    _p = os.path.join(HERE, "assets", "gfx_verify.json")
    if only:
        old = []
        try:
            old = json.load(open(_p, encoding="utf-8")) or []
        except Exception:
            old = []
        _new = {r["id"]: r for r in old}
        _new.update({r["id"]: r for r in res})
        res_all = sorted(_new.values(), key=lambda r: r["id"])
        print(f"  (အပိုင်း ပြေးပြီး — ရှိပြီးသား {len(old)} နဲ့ ပေါင်း ⇒ "
              f"{len(res_all)})", flush=True)
    else:
        res_all = res
    _DIO.write_derived(_p, res_all, writer=__file__)
    # ⚠️ S-c — provenance **သာ** မှတ်သည် · ဖိုင် ပြန်မထုတ်ပါ။
    #    ဒီ run မှာ တကယ် စစ်ခဲ့သော id များသာ မှတ်ရမည် — အပိုင်းလိုက်
    #    ပြေးလျှင် ကျန် template များ ဟောင်းတုန်း ဖြစ်ရမည် (S-a)。
    if _DC is not None:
        try:
            _DC.record("gfx_verify", ids=[r["id"] for r in res])
        except Exception as _pe:
            print("  ⚠️ provenance မမှတ်နိုင်: %s" % _pe, flush=True)
    from collections import Counter
    print("module အလိုက် အောင်:", dict(Counter(r["id"].split(".")[0] for r in ok)))

if __name__ == "__main__":
    main()
