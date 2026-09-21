"""pack — Motion Kit contract test

⚠️ spec §5 — 「No planner may select a template until its manifest is valid
   and its preview-render test passes」。
⚠️ ရှိပြီးသား motionkit manifest မှာ contract field **၇ ခုလုံး မရှိ**ပါ
   (၂၀၂၆-၀၉-၂၁ စစ်၍ တွေ့) ⇒ pack က အပေါ်ကနေ ဖြည့်သည်、မထိပါ。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import pack as PK      # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def main():
    print("── ၁ · pack ဖတ်ခြင်း ──")
    p, t = PK.load()
    check("pack.json ဖတ်ရသည်", p is not None, p)
    check("tokens.json ဖတ်ရသည်", t is not None)
    if not p:
        print("  ✗ ဆက်မစစ်နိုင်ပါ"); return 1
    check("aspect ၂ မျိုး", set(p["aspects"]) == {"16:9", "9:16"}, p["aspects"])
    check("fps ၃ မျိုး", set(p["fps"]) == {24, 25, 30}, p["fps"])

    print("\n── ၂ · token ရဲ့ **အရင်းအမြစ်** ──")
    # ⚠️ ဒါက အရေးကြီးဆုံး — မတိုင်းရသေးတာကို တိုင်းပြီးသားလို မပြောရ
    for keys, want in (
            (("size", "keywordPop"), "measured"),
            (("size", "pillHeight"), "measured"),
            (("size", "pillPitch"), "measured"),
            (("color", "pillFill"), "measured"),
            (("color", "marker"), "measured"),
            (("color", "accent"), "brand"),
            (("motion", "enter"), "measured"),
            (("motion", "exit"), "measured"),
            (("motion", "hold"), "measured"),
            (("motion", "micro"), "spec"),
            (("motion", "settle"), "spec"),
            (("safeZones", "top"), "spec")):
        got = PK.src(t, *keys)
        check(f"{'.'.join(keys)} ⇒ {want}", got == want, got)

    print("\n── ၃ · တိုင်းထားသော ကိန်းများ မပြောင်းရ ──")
    for keys, want in ((("size", "keywordPop"), 0.101),
                       (("size", "pillHeight"), 0.104),
                       (("size", "pillWidth"), 0.304),
                       (("size", "pillPitch"), 0.1315),
                       (("density", "gfxPerMin"), 1.76),
                       (("density", "gfxCoverage"), 0.178),
                       # ⚠️ Step 1 တိုင်းချက် (ဗီဒီယို ၂ · ဖြစ်ရပ် ၂၁)
                       (("motion", "enter"), 0.467),
                       (("motion", "exit"), 0.200),
                       (("motion", "hold"), 1.800)):
        check(f"{'.'.join(keys)} = {want}",
              abs(PK.tok(t, *keys) - want) < 1e-9, PK.tok(t, *keys))

    print("\n── ၃ခ · spec နဲ့ ကွာသွားတာ မှတ်ထားရမည် ──")
    # ⚠️ spec က enter ၀.၂၈ ဟု ဆိုခဲ့သည် — တိုင်းတော့ ၀.၄၆၇ (+၆၇%)。
    #    **ဘယ်ကနေ ပြောင်းလဲ ချန်ထားရမည်** — မဟုတ်လျှင် နောက်တစ်ယောက်က
    #    spec ကိန်းကို ပြန်သွင်းမည်。
    m = t["motion"]["enter"]
    check("enter မှာ မူလ spec ကိန်း ချန်ထားသည်",
          abs(m.get("was_spec", 0) - 0.28) < 1e-9, m.get("was_spec"))
    check("enter မှာ နမူနာ အရေအတွက် ပါသည်", m.get("n", 0) >= 20, m.get("n"))
    check("enter မှာ ဖြန့်ကျက် ပါသည်", "p25" in (m.get("spread") or ""), m.get("spread"))
    # ⚠️ `hold` က spec ရဲ့ `settle` နဲ့ **မတူ** — ရောလျှင် ၁၀ ဆ မှားမည်
    check("hold ≠ settle ဟု မှတ်ထားသည်",
          "settle" in (t["motion"]["hold"].get("note") or ""),
          t["motion"]["hold"].get("note"))
    check("ရွေ့လျားမှု ပုံစံ တိုင်းထားသည်",
          PK.tok(t, "motion", "dominant") == "fade_scale")

    print("\n── ၄ · ပိတ်ထားသော density ──")
    # ⚠️ spec က Headtop ၄–၈/မိနစ် ဆိုသည် · ဂိတ်က ၁.၅ ⇒ **မဖွင့်ရသေး**
    check("sfxPerMin မဖွင့်ရသေး",
          t["density"]["sfxPerMin"].get("active") is False)
    check("ဘာက ပိတ်ထားလဲ ပြောသည်",
          "qc" in t["density"]["sfxPerMin"].get("blocked_by", ""),
          t["density"]["sfxPerMin"].get("blocked_by"))

    print("\n── ၅ · manifest စစ်ချက် ──")
    check("ဗလာ ⇒ ချိုးဖောက်ချက် များစွာ", len(PK.check_manifest({})) >= 7)
    good = dict(id="x", version=1, intent=["number"], aspects=["16:9"],
                duration=dict(min=1.2, preferred=2.2, max=4.5), safeZones={},
                props=dict(number=dict(type="text")),
                render=dict(alpha=True, fps=[30]))
    check("မှန်သော manifest ⇒ အောင်", not PK.check_manifest(good),
          PK.check_manifest(good))
    for nm, patch in (
            ("duration အစဉ် မမှန်", dict(duration=dict(min=3, preferred=1, max=2))),
            ("render.alpha မပါ", dict(render=dict(fps=[30]))),
            ("prop type မပါ", dict(props=dict(x={}))),
            ("aspects ဗလာ", dict(aspects=[]))):
        m = dict(good); m.update(patch)
        check(f"{nm} ⇒ ဖမ်းမိသည်", bool(PK.check_manifest(m)), PK.check_manifest(m))

    print("\n── ၆ · planner ရွေးခွင့် ──")
    # ⚠️ template မဆောက်ရသေး ⇒ ဗလာ ဖြစ်ရမည် (အမှား မဟုတ်ပါ)
    check("verify မပြီးသေး ⇒ ရွေးစရာ မရှိ", PK.selectable() == [],
          PK.selectable())

    print("\n── ၇ · တားမြစ်ချက် ──")
    b = (p.get("banned") or {}).get("effects") or []
    check("letter_animation တားထား", "letter_animation" in b, b)
    check("per_word_sfx တားထား", "per_word_sfx" in b, b)
    check("စာသား မဆံ့လျှင် caption-only သို့",
          (p.get("fallback") or {}).get("captionOnly") is True)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
