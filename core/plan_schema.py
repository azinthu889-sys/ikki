"""HeadtopEditPlan — AI ပြန်ပေးသော တည်းဖြတ် အစီအစဉ်ကို **တင်းကျပ်စွာ** စစ်သည်။

ဒီဖိုင်က စာချုပ် ဖြစ်သည် — AI က ဒီပုံစံအတိုင်းသာ ပြန်ပေးရမည်、renderer က
ဒီပုံစံကိုသာ လက်ခံသည်。 AI က တိုက်ရိုက် render မလုပ်ရ。

⚠️ **အမှားကို တိတ်တဆိတ် မကျော်ရ**。 ဒီ project မှာ တိတ်တဆိတ် ကျရှုံးမှု
   ထပ်ခါထပ်ခါ ဖြစ်ခဲ့သည် (brand override · zoom NameError · cap_cover ·
   SFX round)。 ⇒ မမှန်လျှင် `errors` ထဲ ထည့်ပြီး **ပြရမည်**。

⚠️ pydantic မသုံးပါ — API image မှာ dependency အပို မထည့်လိုပါ。 `core/` က
   worker (flat) ရော API (package) ရော import လုပ်သဖြင့် standard library
   သာ သုံးသည် (`ikki-dual-import-paths`)。
"""

VERSION = 1

# ── စည်းမျဉ်း ကိန်းများ ──────────────────────────────────────
# ⚠️ ကိန်းတိုင်းကို Zin ရဲ့ spec (၂၀၂၆-၀၉-၂၀) ကနေ တိုက်ရိုက် ယူထားသည်。
MAX_CAPTION_LINES = 2
CAP_BOTTOM_MIN, CAP_BOTTOM_MAX = 0.07, 0.09   # အောက်ခြေမှ အထက် %
MAX_PUNCH = 1.08                               # punch-in အများဆုံး
PUNCH_WINDOW, PUNCH_MAX_IN_WINDOW = 15.0, 2    # ၁၅s အတွင်း ၂ ခြိမ်း
SILENCE_CUT_MS_DEFAULT = 400
CHANGE_GAP_MIN, CHANGE_GAP_MAX = 4.0, 8.0      # မြင်ကွင်း ပြောင်းမှု ကြား

WHITE, ACCENT, ALERT = "#FFFFFF", "#FFE500", "#F31313"
CAPTION_COLORS = {WHITE, ACCENT, ALERT}

LAYERS = ("video", "reframe", "grade", "broll", "template",
          "caption", "transition", "sfx")

EVENT_TYPES = {
    "cut", "reframe", "caption", "template", "asset", "sfx", "grade",
    "transition",
}

# event အမျိုးအစား → ဘယ် array ထဲ နေရမလဲ
ARRAY_OF = {
    "cuts": "cut", "cameraReframes": "reframe", "captions": "caption",
    "templateEvents": "template", "assetEvents": "asset",
    "sfxEvents": "sfx", "colorGrades": "grade",
}
ARRAYS = tuple(ARRAY_OF) + ("transcript", "qualityWarnings")

# template လိုအပ်သော အမျိုးအစား
NEEDS_TEMPLATE = {"template", "transition"}


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# မြန်မာ ဂဏန်း ၀–၉ ပါ ပါသည် — ASR က မြန်မာလို ပြန်ပေးတတ်သည်
_DIGITS = set("0123456789" + "".join(chr(0x1040 + i) for i in range(10)))


def _has_number(v):
    """ကိန်း ဒါမှမဟုတ် ဂဏန်းပါသော စာသား ဟုတ်မဟုတ်"""
    if _num(v):
        return True
    if isinstance(v, str):
        return any(c in _DIGITS for c in v)
    if isinstance(v, (list, tuple)):
        return any(_has_number(x) for x in v)
    return False


def _ev_errors(ev, arr, dur, seen_ids):
    """event တစ်ခုချင်း — မှားချက် စာရင်း ပြန်ပေးသည်"""
    e = []
    where = f"{arr}[{ev.get('id') or '?'}]"

    eid = ev.get("id")
    if not isinstance(eid, str) or not eid.strip():
        e.append(f"{where}: `id` လိုအပ်သည် (string)")
    elif eid in seen_ids:
        # ⚠️ id ထပ်လျှင် သုံးစွဲသူ ပြင်ချက်က **မှားသော event** ကို
        #    သွားထိမည် — ပြင်လို့ မရတော့ဘူးလို့ ထင်စေသည်。
        e.append(f"{where}: `id` ထပ်နေသည်")
    else:
        seen_ids.add(eid)

    a, b = ev.get("startTime"), ev.get("endTime")
    if not _num(a) or a < 0:
        e.append(f"{where}: `startTime` မမှန်")
    if not _num(b):
        e.append(f"{where}: `endTime` မမှန်")
    if _num(a) and _num(b):
        if b <= a:
            e.append(f"{where}: `endTime` က `startTime` ထက် ကြီးရမည်")
        if dur and b > dur + 0.05:
            e.append(f"{where}: ဗီဒီယို အရှည် ({dur:.2f}s) ကျော်နေသည်")

    if ev.get("layer") not in LAYERS:
        e.append(f"{where}: `layer` မမှန် ({ev.get('layer')!r})")

    t = ev.get("type")
    if t not in EVENT_TYPES:
        e.append(f"{where}: `type` မမှန် ({t!r})")
    elif ARRAY_OF.get(arr) and t != ARRAY_OF[arr]:
        e.append(f"{where}: `type` က {arr} နဲ့ မကိုက် ({t} ≠ {ARRAY_OF[arr]})")

    if not isinstance(ev.get("reason"), str) or not ev["reason"].strip():
        # ⚠️ `reason` မရှိလျှင် သုံးစွဲသူက **ဘာကြောင့် ဒီလို လုပ်လဲ** မသိဘဲ
        #    ပြင်လို့ မရပါ (Zin ရဲ့ လိုအပ်ချက်)。
        e.append(f"{where}: `reason` လိုအပ်သည်")

    c = ev.get("confidence")
    if not _num(c) or not (0.0 <= c <= 1.0):
        e.append(f"{where}: `confidence` က ၀–၁ ဖြစ်ရမည်")

    if not isinstance(ev.get("props", {}), dict):
        e.append(f"{where}: `props` က object ဖြစ်ရမည်")
    # ⚠️ `props` နဲ့ `style` ကို **ခွဲရမည်**。 `props` က template ရဲ့
    #    argument (manifest နဲ့ တိတိကျကျ စစ်သည်)、`style` က renderer ရဲ့
    #    အပြင်အဆင် (အရောင် · နေရာ · plate)。 ရောထားလျှင် 「param မရှိ」
    #    ဆိုပြီး မှန်သော plan တောင် ကျသွားမည် (၂၀၂၆-၀၉-၂၀ တကယ် ဖြစ်)。
    if not isinstance(ev.get("style", {}), dict):
        e.append(f"{where}: `style` က object ဖြစ်ရမည်")

    return e


def _template_errors(plan, mf):
    """template ID တွေ တကယ် ရှိမရှိ + props ကိုက်မကိုက်"""
    e = []
    for arr in ("templateEvents", "captions", "assetEvents"):
        for ev in plan.get(arr) or []:
            cid = ev.get("motionKitTemplateId")
            if ev.get("type") in NEEDS_TEMPLATE and not cid:
                e.append(f"{arr}[{ev.get('id')}]: `motionKitTemplateId` လိုအပ်")
                continue
            if not cid:
                continue
            if mf is None:
                continue
            ok, errs = mf.props_ok(cid, ev.get("props") or {})
            if not ok:
                e += [f"{arr}[{ev.get('id')}]: {x}" for x in errs]
    return e


def _rule_warnings(plan):
    """render ရနိုင်ပေမယ့် **အရည်အသွေး** ပြဿနာ ဖြစ်စေမည့်အရာများ"""
    w = []

    # စာတန်း — ၂ ကြောင်းထက် မပိုရ · အရောင် ၃ မျိုးသာ · နေရာ ၇–၉%
    for ev in plan.get("captions") or []:
        # ⚠️ အရောင်/နေရာက `style` ထဲ、စာကြောင်းက `props` ထဲ ရှိသည်
        st = ev.get("style") or {}
        p = ev.get("props") or {}
        lines = p.get("lines")
        if isinstance(lines, list) and len(lines) > MAX_CAPTION_LINES:
            w.append(dict(code="caption_lines", eventId=ev.get("id"),
                          message=f"စာတန်း {len(lines)} ကြောင်း — "
                                  f"အများဆုံး {MAX_CAPTION_LINES}"))
        col = st.get("color")
        if col and col.upper() not in CAPTION_COLORS:
            w.append(dict(code="caption_color", eventId=ev.get("id"),
                          message=f"အရောင် {col} — ခွင့်ပြုသည်မှာ "
                                  f"အဖြူ · {ACCENT} · {ALERT} သာ"))
        bot = st.get("bottomPct")
        if _num(bot) and not (CAP_BOTTOM_MIN <= bot <= CAP_BOTTOM_MAX):
            w.append(dict(code="caption_pos", eventId=ev.get("id"),
                          message=f"အောက်ခြေမှ {bot:.0%} — "
                                  f"{CAP_BOTTOM_MIN:.0%}–{CAP_BOTTOM_MAX:.0%} ဖြစ်သင့်"))

    # punch-in — ၁.၀၈× ထက် မကျော်ရ · ၁၅s အတွင်း ၂ ခုထက် မပိုရ
    rf = sorted((e for e in (plan.get("cameraReframes") or [])),
                key=lambda x: x.get("startTime") or 0)
    punches = []
    for ev in rf:
        z = (ev.get("props") or {}).get("zoom")
        if _num(z):
            if z > MAX_PUNCH + 1e-6:
                w.append(dict(code="punch_too_strong", eventId=ev.get("id"),
                              message=f"punch {z:.3f}× — အများဆုံး {MAX_PUNCH}×"))
            if z > 1.001:
                punches.append(ev.get("startTime") or 0)
    for i, t0 in enumerate(punches):
        n = sum(1 for t in punches[i:] if t - t0 < PUNCH_WINDOW)
        if n > PUNCH_MAX_IN_WINDOW:
            w.append(dict(code="punch_too_many", eventId=None,
                          message=f"{t0:.1f}s မှစ၍ {PUNCH_WINDOW:.0f}s အတွင်း "
                                  f"punch {n} ခု — အများဆုံး {PUNCH_MAX_IN_WINDOW}"))
            break

    # template တူ ဆက်တိုက် မသုံးရ
    tv = sorted((e for e in (plan.get("templateEvents") or [])),
                key=lambda x: x.get("startTime") or 0)
    for a, b in zip(tv, tv[1:]):
        if a.get("motionKitTemplateId") and \
           a.get("motionKitTemplateId") == b.get("motionKitTemplateId"):
            w.append(dict(code="template_repeat", eventId=b.get("id"),
                          message=f"{b.get('motionKitTemplateId')} ဆက်တိုက် ၂ ခါ"))

    # ဂဏန်း template — တကယ် ဂဏန်း ပြောမှသာ
    for ev in tv:
        cid = ev.get("motionKitTemplateId") or ""
        if cid.startswith(("odo.", "charts.")):
            p = ev.get("props") or {}
            # ⚠️ ဂဏန်းက **စာသားအဖြစ်** လာတတ်သည် — `odo.count_up` ရဲ့
            #    `target` က type `text` ဖြစ်သည် ("၅၀၀" · "500" · "95%")。
            #    ကိန်းသက်သက် စစ်လျှင် တကယ့် ဂဏန်းကိုပါ 「မပါ」ဟု လွဲမည်。
            if not any(_has_number(v) for v in p.values()):
                w.append(dict(code="number_without_data", eventId=ev.get("id"),
                              message=f"{cid} — တကယ့် ဂဏန်း မပါဘဲ သုံးထားသည်"))

    # မြင်ကွင်း ပြောင်းမှု ကြားကာလ ၄–၈s
    marks = sorted([e.get("startTime") or 0
                    for e in (plan.get("templateEvents") or [])
                    + (plan.get("assetEvents") or [])
                    + (plan.get("cameraReframes") or [])])
    for a, b in zip(marks, marks[1:]):
        if b - a > CHANGE_GAP_MAX * 2:
            w.append(dict(code="static_stretch", eventId=None,
                          message=f"{a:.1f}–{b:.1f}s ({b-a:.1f}s) "
                                  f"မြင်ကွင်း ပြောင်းမှု မရှိ"))
            break

    return w


def validate(plan, manifest=None, duration=None):
    """`(ok, errors, warnings)` — `errors` ရှိလျှင် **render မလုပ်ရ**

    `manifest` — `core.manifest` module (မပေးလျှင် template ID မစစ်ပါ)
    `duration` — ဗီဒီယို အရှည် (စက္ကန့်)
    """
    e, w = [], []

    if not isinstance(plan, dict):
        return False, ["plan က object ဖြစ်ရမည်"], []

    if plan.get("version") != VERSION:
        e.append(f"`version` က {VERSION} ဖြစ်ရမည် (ရလာသည် {plan.get('version')!r})")
    if plan.get("style") != "headtop":
        e.append(f"`style` က 'headtop' ဖြစ်ရမည် (ရလာသည် {plan.get('style')!r})")
    if not isinstance(plan.get("sourceVideoId"), str) or not plan["sourceVideoId"]:
        e.append("`sourceVideoId` လိုအပ်သည်")
    fps = plan.get("fps")
    if fps not in (24, 25, 30):
        e.append(f"`fps` မမှန် ({fps!r})")
    if not isinstance(plan.get("aspectRatio"), str):
        e.append("`aspectRatio` လိုအပ်သည်")

    for k in ARRAYS:
        if k in plan and not isinstance(plan[k], list):
            e.append(f"`{k}` က array ဖြစ်ရမည်")

    dur = duration if _num(duration) else None
    seen = set()
    for arr in ARRAY_OF:
        for ev in plan.get(arr) or []:
            if not isinstance(ev, dict):
                e.append(f"{arr}: event က object ဖြစ်ရမည်")
                continue
            e += _ev_errors(ev, arr, dur, seen)

    e += _template_errors(plan, manifest)
    if not e:
        w = _rule_warnings(plan)

    return (not e), e, w


def empty(source_video_id, fps=30, aspect="16:9"):
    """ဗလာ plan — fallback နဲ့ test အတွက်"""
    p = dict(version=VERSION, aspectRatio=aspect, fps=fps, style="headtop",
             sourceVideoId=source_video_id)
    for k in ARRAYS:
        p[k] = []
    return p
