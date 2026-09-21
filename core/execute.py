"""HeadtopEditPlan → ရှိပြီးသား renderer ရဲ့ ပုံစံသို့ ပြောင်းသည်။

⚠️ **ဒီဖိုင်က ဘာမှ မ render ပါ**。 Zin ရဲ့ စည်းမျဉ်း —
   「Reuse the existing renderer; do not create a parallel unmaintainable
     rendering system」。 ⇒ `dress.track()` · `captions.track()` ·
   `spans.spans()` တို့ လက်ခံသော **ပုံစံသို့ ပြောင်းပေးရုံ**သာ。

⚠️ ယခင်က worker က **ဆုံးဖြတ်သူ** ဖြစ်ခဲ့သည် (ဘယ် template · ဘယ်အချိန် ·
   ဘယ်နှစ်ခု)。 ယခု plan က ဆုံးဖြတ်ပြီး worker က **အကောင်အထည်ဖော်သူ**
   ဖြစ်သည် — ဒါမှ သုံးစွဲသူက event တစ်ခုချင်း ပြင်နိုင်မည်。

⚠️ `motionKitTemplateId` ကို **အပြည့်အစုံ** (`module.fn`) ပေးရမည်。
   fn နာမည် ၁၈ ခု module အချင်းချင်း တူနေသည် — နာမည်သက်သက် ပေးလျှင်
   မှားသော module ကို တိတ်တဆိတ် ယူမိမည် (`dress._fn` ရဲ့ မှတ်ချက် ကြည့်)。
"""

try:
    import manifest as MF
    import plan_schema as PS
except ImportError:
    from core import manifest as MF
    from core import plan_schema as PS

# ဂရပ်ဖစ် တစ်ခုရဲ့ အနည်းဆုံး/အများဆုံး ရပ်ချိန် — QC `card_len` ဘောင်အတွင်း
HOLD_MIN, HOLD_MAX = 1.0, 10.5

_ROLES = None


def _sfx_roles():
    """`sfxlib.ROLE` — မရလျှင် None

    ⚠️ `sfxlib` က **motionkit ထဲမှာ** ရှိပြီး `core/` ကနေ တိုက်ရိုက်
       import မရပါ。 path မထည့်ဘဲ `try/except` ချည်း ရေးထားလျှင်
       role စစ်ချက်က **တိတ်တဆိတ် အလုပ်မလုပ်ဘဲ** ဖြစ်မည် — မရှိသော role
       တွေ အကုန် ဖြတ်သွားမည် (၂၀၂၆-၀၉-၂၀ test က ဖမ်းမိသည်)。
    """
    global _ROLES
    if _ROLES is not None:
        return _ROLES or None
    try:
        import os as _o
        import sys as _s
        try:
            import gfxcat as GC
        except ImportError:
            from core import gfxcat as GC
        if GC.MK not in _s.path:
            _s.path.insert(0, GC.MK)
        cwd = _o.getcwd()
        _o.chdir(GC.MK)
        try:
            import sfxlib as SL
            _ROLES = set(SL.ROLE)
        finally:
            _o.chdir(cwd)
    except Exception:
        _ROLES = set()
    return _ROLES or None


def to_gfx(plan, log=None):
    """`templateEvents` → `dress.track()` ရဲ့ `gfx` စာရင်း

    item — `dict(at, kind, args, hold, fixed, _eid)`
    `_eid` က plan ရဲ့ event id — render ပြီးနောက် ပြန်ချိတ်ရန်。
    """
    out = []
    for ev in sorted(plan.get("templateEvents") or [],
                     key=lambda x: x.get("startTime") or 0):
        cid = ev.get("motionKitTemplateId")
        if not cid:
            continue
        a = float(ev.get("startTime") or 0.0)
        b = float(ev.get("endTime") or (a + 3.0))
        hold = max(HOLD_MIN, min(HOLD_MAX, b - a))
        out.append(dict(at=round(a, 2), kind=cid,
                        args=dict(ev.get("props") or {}),
                        hold=round(hold, 2),
                        fixed=True,          # plan က နေရာ သတ်မှတ်ပြီးသား
                        _eid=ev.get("id")))
    if log:
        log(f"  execute · ဂရပ်ဖစ် {len(out)} ခု")
    return out


def to_caps(plan, log=None):
    """`captions` → `captions.track()` ရဲ့ `caps` စာရင်း + style စာရင်း

    ပြန်ပေးသည် — `(caps, styles)`。 `styles[i]` က event ရဲ့ `style`
    (အရောင် · နေရာ · plate) — renderer က အဲဒါနဲ့ ဆုံးဖြတ်သည်。
    """
    caps, styles = [], []
    for ev in sorted(plan.get("captions") or [],
                     key=lambda x: x.get("startTime") or 0):
        pr = ev.get("props") or {}
        # `capt.multi_line` က `lines`、`capt.hl_phrase` က `before`+`after`
        txt = pr.get("lines")
        if isinstance(txt, list):
            txt = " ".join(x for x in txt if x)
        else:
            txt = " ".join(x for x in (pr.get("before"), pr.get("after")) if x)
        txt = (txt or "").strip()
        if not txt:
            continue
        caps.append(dict(text=txt,
                         start=float(ev.get("startTime") or 0.0),
                         end=float(ev.get("endTime") or 0.0)))
        styles.append(dict(ev.get("style") or {}, _eid=ev.get("id")))
    if log:
        log(f"  execute · စာတန်း {len(caps)} ကြောင်း")
    return caps, styles


def to_zooms(plan, spans, log=None):
    """`cameraReframes` → `spans.spans()` ရဲ့ `zooms` dict

    ⚠️ `spans()` က **span index** နဲ့ ယူသည်、စက္ကန့်နဲ့ မဟုတ်。 ⇒ event ရဲ့
       အချိန်ကို ဖြတ်ပြီး timeline ပေါ် ဘယ် span ထဲ ကျလဲ ရှာရသည်。
    ⚠️ span တစ်ခုထဲ reframe နှစ်ခု ကျလျှင် **ပထမတစ်ခုသာ** ယူသည် —
       span တစ်ခုအတွင်း crop အရွယ် မပြောင်းနိုင်ပါ (ffmpeg က w/h ကို
       တစ်ခါတည်း တွက်သည်)。
    """
    zooms = {}
    if not spans:
        return zooms
    # span အစ အချိန်များ (ဖြတ်ပြီး timeline ပေါ်)
    t = 0.0
    bounds = []
    for a, b in spans:
        bounds.append((t, t + (b - a)))
        t += (b - a)
    for ev in sorted(plan.get("cameraReframes") or [],
                     key=lambda x: x.get("startTime") or 0):
        z = (ev.get("props") or {}).get("zoom")
        if not isinstance(z, (int, float)) or z <= 1.001:
            continue
        z = max(1.0, min(PS.MAX_PUNCH, float(z)))
        at = float(ev.get("startTime") or 0.0)
        for i, (s0, s1) in enumerate(bounds):
            if s0 <= at < s1:
                zooms.setdefault(i, z)
                break
    if log:
        log(f"  execute · punch {len(zooms)} span")
    return zooms


def reframe_spans(plan, spans, base_zooms=None, min_piece=0.20, log=None):
    """Plan ၏ source-time reframes ကို render လုပ်နိုင်သော span များအဖြစ် ခွဲသည်。

    `spans.spans()` က clip တစ်ခုလုံးအတွက် crop တစ်ခုသာ ချနိုင်သည်။ အရင်က
    `cameraReframes` ကို plan ထဲ ထုတ်ထားပေမယ့် span မခွဲခဲ့လို့ no-cut talking
    head တစ်ပုဒ်မှာ punch-in **လုံးဝမပေါ်**ခဲ့။ Plan အချိန်က source timeline
    ဖြစ်သောကြောင့် source spans ပေါ်မှာပဲ split လုပ်သည်; output duration မပြောင်း။

    `base_zooms` က silence cut ကို ဖုံးရန်ရှိပြီးသား wide/punch alternation ဖြစ်သည်။
    Plan punch နဲ့ တိုက်လျှင် အကြီးဆုံး zoom ကိုသာ ယူသည် — နှစ်ခါ crop မလုပ်ရ။
    """
    base = dict(base_zooms or {})
    events = []
    for ev in sorted((plan or {}).get("cameraReframes") or [],
                     key=lambda x: x.get("startTime") or 0):
        try:
            a = float(ev.get("startTime") or 0.0)
            b = float(ev.get("endTime") or a)
            z = float((ev.get("props") or {}).get("zoom") or 1.0)
        except (TypeError, ValueError):
            continue
        if b - a < min_piece or z <= 1.001:
            continue
        events.append((a, b, max(1.0, min(PS.MAX_PUNCH, z))))
    if not events:
        return list(spans or []), base

    out, zooms, split_n = [], {}, 0
    for src_i, item in enumerate(spans or []):
        try:
            lo, hi = float(item[0]), float(item[1])
        except (TypeError, ValueError, IndexError):
            continue
        if hi - lo <= 0.05:
            continue
        local = [(max(lo, a), min(hi, b), z) for a, b, z in events
                 if b > lo + min_piece and a < hi - min_piece]
        marks = [lo, hi]
        for a, b, _z in local:
            if lo + min_piece < a < hi - min_piece: marks.append(a)
            if lo + min_piece < b < hi - min_piece: marks.append(b)
        marks = sorted(set(round(x, 4) for x in marks))
        for a, b in zip(marks, marks[1:]):
            if b - a <= 0.05:
                continue
            idx = len(out); out.append((a, b))
            mid = (a + b) / 2.0
            zv = base.get(src_i, 1.0)
            if isinstance(zv, dict): zv = zv.get("zoom", 1.0)
            try: zv = float(zv or 1.0)
            except (TypeError, ValueError): zv = 1.0
            for ea, eb, ez in local:
                if ea <= mid < eb:
                    zv = max(zv, ez)
            if zv > 1.001:
                # Plan event ကိုယ်တိုင်က PS.MAX_PUNCH အောက် ချပြီးသား။
                # `base_zooms` ကတော့ silence cut ကို ဖုံးရန် existing 1.10×
                # framing ဖြစ်နိုင်သည် — plan adapter က အဲဒါကို 1.08× သို့
                # လျှော့မိလျှင် cut quality ကျသွားမည်။ spans._punch() ရဲ့
                # hard ceiling 1.25× အောက်မှာသာ ထားသည်။
                zooms[idx] = min(1.25, zv)
            if len(marks) > 2:
                split_n += 1
    if log:
        log(f"  execute · plan punch {len(events)} ခု ⇒ span {split_n} ခု ခွဲ · "
            f"crop {len(zooms)} ခု")
    return out, zooms


def to_sfx(plan, log=None):
    """`sfxEvents` → `[(အချိန်, role, dB)]`

    ⚠️ role နာမည်ကို `sfxlib.ROLE` နဲ့ စစ်ရမည် — မရှိလျှင် ကျော်သည်。
    """
    known = _sfx_roles()
    out, skipped = [], 0
    for ev in sorted(plan.get("sfxEvents") or [],
                     key=lambda x: x.get("startTime") or 0):
        pr = ev.get("props") or {}
        role = pr.get("role")
        if known is not None and role not in known:
            skipped += 1
            continue
        db = pr.get("db")
        out.append((float(ev.get("startTime") or 0.0), role,
                    int(db) if isinstance(db, (int, float)) else -16))
    if log and (out or skipped):
        log(f"  execute · SFX {len(out)} ခု" +
            (f" · မရှိသော role {skipped} ကျော်" if skipped else ""))
    return out


def grade_over(plan, log=None):
    """`colorGrades` → `grade.apply()` ရဲ့ ပြင်ချက် (ပထမတစ်ခုသာ)

    ⚠️ ယခု renderer က grade ကို **ဗီဒီယိုတစ်ခုလုံး** တစ်မျိုးတည်း ချသည် ⇒
       event များစွာ ရှိလျှင်လည်း ပထမတစ်ခုသာ သုံးနိုင်သည်。 အပိုင်းလိုက်
       grade လိုလျှင် renderer ဘက် ချဲ့ရမည် — ယခု **မလုပ်ရသေး**。
    """
    gs = sorted(plan.get("colorGrades") or [],
                key=lambda x: x.get("startTime") or 0)
    if not gs:
        return {}
    if len(gs) > 1 and log:
        log(f"  ⚠️ execute · grade event {len(gs)} ခု — ပထမတစ်ခုသာ သုံးသည် "
            f"(renderer က အပိုင်းလိုက် မထောက်ပံ့သေးပါ)")
    return dict(gs[0].get("props") or {})


def unresolved(plan):
    """render မတိုင်ခင် **ဖြေရှင်းရမည့်** ပြဿနာများ (critical warnings)

    ⚠️ Zin ရဲ့ စည်းမျဉ်း — 「Do not export with unresolved critical warnings
       unless user confirms」。 ဒီစာရင်း ဗလာ မဟုတ်လျှင် UI က အတည်ပြုခိုင်းရမည်。
    """
    CRIT = {"low_contrast", "missing_asset", "loudness_clip",
            "face_overlap", "number_without_data"}
    return [w for w in (plan.get("qualityWarnings") or [])
            if w.get("code") in CRIT]


def summary(plan):
    """timeline အကျဉ်း — UI နဲ့ log အတွက်"""
    return dict(
        captions=len(plan.get("captions") or []),
        templates=len(plan.get("templateEvents") or []),
        reframes=len(plan.get("cameraReframes") or []),
        assets=len(plan.get("assetEvents") or []),
        sfx=len(plan.get("sfxEvents") or []),
        grades=len(plan.get("colorGrades") or []),
        warnings=len(plan.get("qualityWarnings") or []),
        critical=len(unresolved(plan)),
        templateIds=sorted({e.get("motionKitTemplateId")
                            for e in (plan.get("templateEvents") or [])
                            if e.get("motionKitTemplateId")}),
    )
