# -*- coding: utf-8 -*-
"""Motion Kit **curated catalog** — သုံးစွဲသူ ဆီ ဘာ ထွက်သွားလဲ။

⚠️ browser က `localhost:8765` (motionkit dev gallery) ကို ဘယ်တော့မှ မဆွဲရ ⇒
   API/worker လမ်းကြောင်းသာ။ ဤ test က **ထွက်လာသော ဒေတာ** ကို စစ်သည်。
⚠️ **filesystem path တစ်ခုမှ မယိုစိမ့်ရ** — id/နာမည်/အုပ်စု/slot သာ。
⚠️ template ၄၇၉ ခု အားလုံး မထုတ်ရ — `gfx_ok.txt` (render စစ်ပြီးသား) သာ。
"""
import os, sys, json
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))
import mkcat as MK

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

print("── ① အုပ်စု ခွဲခြားမှု (id စကားလုံး > motionkit category) ──")
for tid, want in (("infogfx.checklist", "compare"),
                  ("titles2.compare_bars", "compare"),
                  ("charts.bar_race", "info"),
                  ("infogfx.funnel", "info"),
                  ("mockups.browser_window", "screen"),
                  ("titles.cta_subscribe", "cta"),
                  ("kinetic.word_pop", "text"),
                  ("titles3.lower_bar_ticker", "info")):
    got = MK.group_of(tid, "")
    ck(f"{tid} ⇒ {want}", got == want, got)
ck("«ticker» က checklist အဖြစ် မမှားဖမ်းရ",
   MK.group_of("titles3.lower_bar_ticker", "") != "compare")
ck("မသိလျှင် category ကနေ",
   MK.group_of("zzz.unknown", "infographic") == "info")
ck("category လည်း မသိလျှင် text", MK.group_of("zzz.unknown", "") == "text")

print("\n── ② build() ──")
d = MK.build()
if not d.get("ok"):
    print(f"  ⊘ motionkit မရှိ ({d.get('why')}) — ဒီစက်မှာ ဆက်စစ်လို့ မရ")
    print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
    sys.exit(1 if FAIL else 0)
ck("ok", d["ok"])
ck("verified < total (အားလုံး မထုတ်ရ)", d["n"] < d["total"], (d["n"], d["total"]))
ok_ids = MK.verified()
ck("item တိုင်း gfx_ok.txt ထဲ ပါ",
   all(i["id"] in ok_ids for i in d["items"]))
ck("အုပ်စု ၅ ခု ဖော်ပြထား", len(d["cats"]) == 5, len(d["cats"]))
ck("item တိုင်း အုပ်စု မှန်",
   all(i["cat"] in MK.CAT_IDS for i in d["items"]))
ck("နာမည် ဗလာ မရှိ", all(str(i["name"]).strip() for i in d["items"]))

print("\n── ③ **path မယိုစိမ့်ကြောင်း** ──")
blob = json.dumps(d, ensure_ascii=False)
for bad in ("/Users", "/Applications", "/Volumes", "motionkit/", ".py", "8765"):
    ck(f"«{bad}» မပါ", bad not in blob)
ck("slot ထဲ file/path type မပါ",
   not [s for i in d["items"] for s in i["slots"]
        if s["type"] in ("file", "path", "image")])

print("\n── ④ preflight — မမှန်လျှင် ရှင်းရှင်း ငြင်းရမည် ──")
ck("verified id ⇒ ok", MK.preflight(d["items"][0]["id"])[0])
ck("မရှိသော id ⇒ ငြင်း", not MK.preflight("nope.nope")[0])
ck("ဗလာ ⇒ ငြင်း", not MK.preflight("")[0])
ck("None ⇒ ငြင်း", not MK.preflight(None)[0])
ck("ငြင်းလျှင် အကြောင်းရင်း ပါ", bool(MK.preflight("nope.nope")[1]))

print("\n── ⑤ Screen/App က ဗလာ ဖြစ်နိုင်သည် — **ဝှက်၍ မပြရ** ──")
_sc = [i for i in d["items"] if i["cat"] == "screen"]
print(f"     screen {len(_sc)} ခု (mockup ကို render စစ်ချက် မလုပ်ရသေးလျှင် ၀)")
ck("ဗလာ ဖြစ်လျှင်လည်း အုပ်စု စာရင်းထဲ ရှိနေရမည် (UI က အကြောင်းရင်း ပြရန်)",
   any(c["id"] == "screen" for c in d["cats"]))

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
