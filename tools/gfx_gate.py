#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`assets/gfx_ok.txt` ကို **တိုင်းလို့ရသော ဂိတ် ၂ ခု**ဖြင့် ပြန်ဆောက်သည်。

⚠️ ယခင် ဂိတ် (`tools/gfx_pool.py`) က gradient သိပ်သည်းမှုနဲ့ 「စာသား ပါလား」
   ခန့်မှန်းခဲ့ပြီး **ကောင်း/ဆိုး ကိန်းတွေ ထပ်နေသဖြင့် မယုံရ**ဟု သူကိုယ်တိုင်
   မှတ်ထားသည် (`--write` မသုံးရ)。 ⇒ ဤမှာ **ခန့်မှန်းချက် လုံးဝ မသုံး** —
   တိုင်းလို့ရတာ နှစ်ခုကိုသာ စစ်သည်:

     ဂိတ် ① render ဖြစ်ရမည် · ဖရိမ်း ≥၂ · နောက်ဆုံး ဖရိမ်းမှာ မှင် ≥၀.၀၅%
            (`gfx_verify.json` ရဲ့ `ok`)
     ဂိတ် ② **စာတန်းဇုန် မဖုံးရ** — bbox ရဲ့ အောက်စွန်းက `CAP_TOP` အထက်
            ဖြစ်ရမည်。 IKKI က စာတန်းကို `cap_base=0.92` မှာ ချပြီး အမြင့်
            ~၀.၁၃ ⇒ ၀.၇၉ ကနေ အောက် စာတန်း ယူထားသည် (`place.caption_band`)。
            ⚠️ `place.caption_band()` က **keyword pop အတွက်သာ** သုံးနေပြီး
               template event ကို run-time မှာ မစစ်ပါ ⇒ ဒီမှာ ကြိုဖယ်ရမည်。

⚠️ **ကျဉ်းလိုက်တာကို အစီရင်ခံရမည်** — အရင်က ပါပြီး ယခု ကျသွားသူများကို
   သီးသန့် ပြသည်。 တိတ်တဆိတ် မဖယ်ရ。
"""
import os, sys, json, collections


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
CAP_TOP = 0.79            # စာတန်း ယူထားသော ဇုန်၏ အပေါ်စွန်း
VJ = os.path.join(HERE, "assets", "gfx_verify.json")
OK = os.path.join(HERE, "assets", "gfx_ok.txt")
# ⚠️ ဂိတ်③ — `tools/gfxtextsens.py` ရဲ့ တိုင်းချက် (မရှိလျှင် ကျော်သည်)
TS = os.path.join(HERE, "assets", "gfx_textsens.json")

HEAD = """# motionkit template — **တစ်ခုချင်း တကယ် render ပြီး စစ်ပြီးသား** စာရင်း。
# ထုတ်သူ: tools/gfx_gate.py  ({n} ခု)
# ⚠️ ဂိတ် ၂ ခု — ခန့်မှန်းချက် မပါ、တိုင်းလို့ရတာချည်း:
#      ① render ဖြစ် · ဖရိမ်း ≥၂ · နောက်ဆုံး ဖရိမ်းမှာ မှင် ≥၀.၀၅%
#      ② bbox အောက်စွန်း < {cap} ·H — စာတန်းဇုန် မဖုံးရ
#      ③ **ကျွန်တော်တို့ စာသားကို တကယ် ရေးရမည်** — စာသား ၂ မျိုးနဲ့ render
#         လုပ်ပြီး ပုံရိပ် ပြောင်းမပြောင်း တိုင်းသည် (`gfxtextsens.py`)
# ⚠️ bbox မသိသေးသူကို **ဖယ်မထားပါ** (ဂိတ် ① အောင်လျှင် ထည့်) — ဒါပေမယ့်
#    အောက်က မှတ်ချက်မှာ ရေတွက် ပြထားသည်; full pass ပြန်ပြေးပြီး ဖြည့်ပါ。
"""


# ⚠️ **ဂိတ်③ ဆုံးဖြတ်ချက်ကို ဒီမှာ ပြန်တွက်သည်** — `gfx_textsens.json` ရဲ့
#    `ok` အလံကို မယုံရ。 အကြောင်းက အောက်ခံ (`DIFF_PX`) ပြောင်းလိုက်တိုင်း
#    template ၆၁၆ ခု ပြန် render ရမည် (၅.၅ နာရီ) — ဒါပေမယ့် `dpx`/`aapx` က
#    မှတ်ထားပြီးသား ဖြစ်၍ **render မလိုဘဲ** ပြန်တွက်လို့ရသည်。
# ⚠️ တိုင်းထားသော ဖြန့်ဖြူးမှု (၂၀၂၆-၀၉-၂၅ · n=383):
#       dpx = 0        →  2 ခု (စာသား လုံးဝ မဆွဲ)
#       dpx 1–352      →  **ဘာမှ မရှိ**
#       dpx 353–371    →  2 ခု (mockups — စာသား သေးသော UI)
#       dpx ≥ 1000     →  379 ခု
#    ⇒ အောက်ခံကို ကွက်လပ် (၁–၃၅၂) အတွင်း ထားလျှင် ဆုံးဖြတ်ချက် တူတူ ⇒ 100。
# ⚠️ A/A က အားလုံး ၀ **မဟုတ်** — `retro` ၃ ခု ကျပန်း ဆူညံမှု သုံးသည်
#    (`vhs_title` A/A = 14,265 px)。 ⇒ **အဆ** စည်းမျဉ်းပါ လိုသည်
#    (တိုင်းရသော အနည်းဆုံး အဆ = 9.8× ⇒ ၄× က လုံလောက်သော ကြားခံ)。
# ⚠️ **ဂိတ်② က `role="overlay"` တွေမှာသာ သက်ဆိုင်သည်**။ `fullbleed` (motion ·
#    mockup) တွေက ဘောင်တစ်ခုလုံး ဖုံးပြီး **ပြောသူပေါ် မတင်ရ** — IKKI က
#    ဖြတ်ပြောင်း/နောက်ခံ လမ်းကြောင်းသို့ ပို့သည် (`gfxcat.USE` ထဲ မပါ)。
#    အဲဒါတွေကို စာတန်းဇုန်နဲ့ တိုက်လျှင် **ဘယ်တော့မှ မအောင်** — ဂိတ်က
#    မှားခြင်း ဖြစ်သည် (စာသား param မရှိသူကို ဂိတ်③ တင်တာနဲ့ အတူတူ)。
#    ၂၀၂၆-၀၉-၂၅ တိုင်းချက်: ကျသူ ၂၅ ခုအနက် **၁၇ ခု** က `fullbleed`
#    (`social` ၈ · `brows` ၇ · `motionfx` ၂) ⇒ တကယ် ပြင်ရမည်က **၈ ခု**。
# ⚠️ `role_of()` က `stylemap.py` တစ်နေရာကနေသာ လာရမည် — လက်နဲ့ စာရင်း မရေးရ。
_ROLE = {}


def role_of(tid):
    """template ရဲ့ role — `overlay` / `cut` / `fullbleed` (မသိလျှင် overlay)。"""
    if not _ROLE:
        try:
            # ⚠️ `core/` ကို path ထဲ ထည့်ရမည် — မထည့်လျှင် `ImportError` ကို
            #    တိတ်ဆိတ် ဖမ်ပြီး role အားလုံး 「overlay」 ဖြစ်ကာ ဂိတ်② က
            #    `fullbleed` ၁၇ ခုကို ဆက်ပြီး မှားပိတ်မည်။
            import os as _os
            _h = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            for _p in (_os.path.join(_h, "core"), _h):
                if _p not in sys.path: sys.path.insert(0, _p)
            import gfxcat as _GC
            for e in _GC.catalog():
                try: _ROLE[e["id"]] = _GC.role_of(e)
                except Exception: _ROLE[e["id"]] = "overlay"
        except Exception as _e:
            print("  ⚠️ role ဖတ်မရ: %s: %s — ဂိတ်② အားလုံးကို overlay ဟု မှတ်မည်"
                  % (type(_e).__name__, _e))
        if not _ROLE:
            print("  ⚠️ role စာရင်း ဗလာ — ဂိတ်② မှားနိုင်သည်")
            _ROLE["__empty__"] = "overlay"
    return _ROLE.get(tid, "overlay")

G3_PX = 100
G3_RATIO = 4.0


def gate3_ok(t):
    """(ok, အကြောင်းရင်း) — `dpx`/`aapx` ကနေ ပြန်တွက်သည်。"""
    if t is None:
        return True, ""                  # မစစ်ရသေး ⇒ ကျဟု မမှတ်ရ
    if t.get("why", "").startswith("စာသား param မရှိ"):
        return True, ""                  # ကင်းလွတ်
    dpx = t.get("dpx"); aapx = t.get("aapx")
    if not isinstance(dpx, int):
        return bool(t.get("ok")), str(t.get("why") or "")[:44]
    if dpx < G3_PX:
        return False, "စာသား ပြောင်းလည်း pixel %d သာ" % dpx
    if isinstance(aapx, int) and aapx and dpx < G3_RATIO * aapx:
        return False, "မတည်ငြိမ် — A/A %d px (A/B %d)" % (aapx, dpx)
    return True, ""


def main():
    # ⛔ S-b — အရင်းအမြစ် ၂ ခု ဟောင်းလျှင် ကိန်း မထုတ်ရ
    if _DC is not None and "--force-stale" not in sys.argv:
        _DC.require("gfx_verify", "ဂိတ်①②")
        _DC.require("gfx_textsens", "ဂိတ်③")
    write = "--write" in sys.argv
    try:
        rows = json.load(open(VJ, encoding="utf-8"))
    except OSError:
        print("gfx_verify.json မရှိ — tools/gfx_verify.py အရင် ပြေးပါ"); return 1
    old = set()
    try:
        old = {l.strip() for l in open(OK, encoding="utf-8")
               if l.strip() and not l.lstrip().startswith("#")}
    except OSError:
        pass

    # ⚠️ **ဘောင်အပြည့် template ကို ဂိတ်②နဲ့ မပယ်ရ** — `prem.hero_line` လို
    #    title card တွေက ဘောင်တစ်ခုလုံး (၀.၀၀–၀.၉၉) ယူတာ **ဒီဇိုင်းအရ မှန်**သည်;
    #    overlay မဟုတ်ဘဲ **full-stage** အဖြစ် သုံးရမည်。 ⇒ ခွဲမှတ်ပြီး
    #    `assets/gfx_fullstage.txt` ထဲ ထည့်သည် — planner က `_layout="full"`
    #    လမ်းကြောင်းသို့ ပို့ရန်。 overlay တွေကိုသာ စာတန်းဇုန်နဲ့ တိုက်သည်。
    def _isfull(b):
        return (b.get("top", 1) < 0.08 and b.get("bottom", 0) > 0.92
                and b.get("left", 1) < 0.08 and b.get("right", 0) > 0.92)

    # ⚠️ ဂိတ်③ — စစ်ပြီးသားမှသာ သုံးသည်。 မစစ်ရသေးသူကို 「ကျ」ဟု
    #    **မသတ်မှတ်ရ** (မသိတာနဲ့ ကျတာ မတူ)。
    ts = {}
    try:
        ts = {r["id"]: r for r in (json.load(open(TS, encoding="utf-8")) or [])
              if r.get("id")}
    except OSError:
        pass

    keep, g1_fail, g2_fail, g3_fail, nobb, full = [], [], [], [], 0, []
    for r in rows:
        if not r.get("ok"):
            g1_fail.append(r["id"]); continue
        _t = ts.get(r["id"])
        _g3ok, _g3why = gate3_ok(_t)
        if not _g3ok:
            g3_fail.append((r["id"], _g3why)); continue
        bb = r.get("bbox")
        if not bb:
            nobb += 1; keep.append(r["id"]); continue
        if _isfull(bb):
            full.append(r["id"]); keep.append(r["id"]); continue
        # ⚠️ overlay မဟုတ်လျှင် စာတန်းဇုန် မတိုက်ရ — အပေါ်က မှတ်ချက် ကြည့်
        if role_of(r["id"]) != "overlay":
            full.append(r["id"]); keep.append(r["id"]); continue
        if float(bb.get("bottom") or 0) >= CAP_TOP:
            g2_fail.append((r["id"], bb["bottom"])); continue
        keep.append(r["id"])
    keep = sorted(set(keep)); full = sorted(set(full))

    print("စစ်ချက် %d ခု" % len(rows))
    print("  ဂိတ်① render ကျ      %3d" % len(g1_fail))
    print("  ဂိတ်② စာတန်းဇုန်ဖုံး  %3d" % len(g2_fail))
    print("  ဂိတ်③ စာသား မရေး     %3d  (စစ်ပြီး %d / မစစ်ရသေး %d)"
          % (len(g3_fail), len(ts), sum(1 for r in rows
                                        if r.get("ok") and r["id"] not in ts)))
    print("  bbox မသိသေး          %3d  (ဂိတ်② မစစ်ရသေး)" % nobb)
    print("  ဘောင်အပြည့် (full-stage) %3d  — ဂိတ်② ကင်းလွတ်" % len(full))
    print("  ⇒ **အောင် %d**" % len(keep))
    if g3_fail:
        print("\n  စာသား မရေးသူ (ဂိတ်③):")
        for i, w in g3_fail[:15]:
            print("     %-30s %s" % (i, w))
        if len(g3_fail) > 15:
            print("     … နောက်ထပ် %d ခု" % (len(g3_fail) - 15))
    if g2_fail:
        print("\n  စာတန်းဇုန် ဖုံးသူ (အောက်စွန်း ·H):")
        for i, b in sorted(g2_fail, key=lambda x: -x[1])[:15]:
            print("     %-30s %.3f" % (i, b))
    lost = sorted(old - set(keep))
    if lost:
        print("\n  ⚠️ အရင်က ပါပြီး **ယခု ကျသွားသူ %d**:" % len(lost))
        for i in lost[:20]:
            r = next((x for x in rows if x["id"] == i), None)
            print("     %-30s %s" % (i, (r or {}).get("why", "စစ်ချက်ထဲ မပါ")))
    new = sorted(set(keep) - old)
    print("\n  ✅ အသစ် ဝင်လာ %d" % len(new))
    print("     module အလိုက်:", dict(collections.Counter(i.split(".")[0] for i in new)))

    if write:
        _DIO.write_derived(OK, HEAD.format(n=len(keep), cap=CAP_TOP)
                           + "\n".join(keep) + "\n", writer=__file__)
        print("\n  ရေးပြီး → %s (%d)" % (OK, len(keep)))
        if _DC is not None:
            try: _DC.record("gfx_ok")
            except Exception as _pe: print("  ⚠️ provenance: %s" % _pe)
        _fs = os.path.join(HERE, "assets", "gfx_fullstage.txt")
        _DIO.write_derived(_fs,
            "# ဘောင်အပြည့် ဖုံးသော template — **overlay အဖြစ် မသုံးရ**。\n"
            "# planner က `_layout=\"full\"` (full-stage / cutaway) သို့ ပို့ရမည်。\n"
            "# ထုတ်သူ: tools/gfx_gate.py — bbox တိုင်းချက်ကနေ (မှန်းမရေး)。\n"
            + "\n".join(full) + "\n", writer=__file__)
        print("  ရေးပြီး → %s (%d)" % (_fs, len(full)))
    else:
        print("\n  (စမ်းကြည့်ရုံ — ရေးရန် `--write`)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
