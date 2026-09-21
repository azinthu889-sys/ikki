"""execute — plan → renderer ပုံစံ ပြောင်းခြင်း test"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import execute as EX        # noqa: E402
import plan_schema as PS    # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def ev(eid, a, b, layer, typ, **kw):
    d = dict(id=eid, startTime=a, endTime=b, layer=layer, type=typ,
             reason="t", confidence=0.8, props=kw.pop("props", {}),
             style=kw.pop("style", {}))
    d.update(kw)
    return d


def main():
    p = PS.empty("v1")
    p["templateEvents"] = [
        ev("t2", 20.0, 23.0, "template", "template",
           motionKitTemplateId="infogfx.steps", props={"items": ["က", "ခ"]}),
        ev("t1", 5.0, 30.0, "template", "template",
           motionKitTemplateId="prem5.line_by_line", props={"lines": ["က"]}),
        ev("t3", 40.0, 40.4, "template", "template",
           motionKitTemplateId="titles.topic_bar", props={"text": "ခေါင်းစဉ်"}),
    ]

    print("── ၁ · ဂရပ်ဖစ် ──")
    g = EX.to_gfx(p)
    check("အချိန်အလိုက် စဉ်သည်", [x["at"] for x in g] == [5.0, 20.0, 40.0],
          [x["at"] for x in g])
    check("ID အပြည့်အစုံ ကျန်သည် (module.fn)",
          g[0]["kind"] == "prem5.line_by_line", g[0]["kind"])
    check("ရပ်ချိန် အများဆုံး ၁၀.၅ ချသည်", g[0]["hold"] == EX.HOLD_MAX,
          g[0]["hold"])
    check("ရပ်ချိန် အနည်းဆုံး ၁.၀ တင်သည်", g[2]["hold"] == EX.HOLD_MIN,
          g[2]["hold"])
    check("props ကို args အဖြစ် ပေးသည်", g[1]["args"] == {"items": ["က", "ခ"]})
    check("fixed=True (plan က နေရာ ဆုံးဖြတ်ပြီး)", all(x["fixed"] for x in g))
    check("event id ပြန်ချိတ်ရန် ပါသည်",
          [x["_eid"] for x in g] == ["t1", "t2", "t3"])

    print("\n── ၂ · စာတန်း ──")
    p["captions"] = [
        ev("c1", 1.0, 3.0, "caption", "caption",
           motionKitTemplateId="capt.multi_line",
           props={"lines": ["ပထမ ကြောင်း", "ဒုတိယ ကြောင်း"]},
           style={"color": PS.WHITE, "bottomPct": 0.08}),
        ev("c2", 4.0, 6.0, "caption", "caption",
           motionKitTemplateId="capt.hl_phrase",
           props={"before": "အရေးကြီးတာက", "hot": "ဒါပါပဲ", "after": "နောက်ဆက်"},
           style={"color": PS.ACCENT, "bottomPct": 0.08}),
        ev("c3", 7.0, 8.0, "caption", "caption",
           motionKitTemplateId="capt.multi_line", props={"lines": []}),
    ]
    caps, sty = EX.to_caps(p)
    check("ဗလာ စာတန်း ကျော်သည်", len(caps) == 2, len(caps))
    check("lines ကို ပေါင်းသည်", caps[0]["text"] == "ပထမ ကြောင်း ဒုတိယ ကြောင်း",
          caps[0]["text"])
    check("hl_phrase ကို before+after ပေါင်းသည်",
          caps[1]["text"] == "အရေးကြီးတာက နောက်ဆက်", caps[1]["text"])
    check("style ပါလာသည်", sty[1]["color"] == PS.ACCENT)
    check("style မှာ event id ပါသည်", sty[0]["_eid"] == "c1")

    print("\n── ၃ · punch → span ──")
    # span (မူရင်း အချိန်) — ဖြတ်ပြီး timeline က 0–10 · 10–20 · 20–35
    spans = [(0.0, 10.0), (12.0, 22.0), (30.0, 45.0)]
    p["cameraReframes"] = [
        ev("r1", 3.0, 5.0, "reframe", "reframe", props={"zoom": 1.06}),
        ev("r2", 15.0, 17.0, "reframe", "reframe", props={"zoom": 1.30}),
        ev("r3", 18.0, 19.0, "reframe", "reframe", props={"zoom": 1.05}),
        ev("r4", 99.0, 99.5, "reframe", "reframe", props={"zoom": 1.05}),
        ev("r5", 25.0, 26.0, "reframe", "reframe", props={"zoom": 1.0}),
    ]
    z = EX.to_zooms(p, spans)
    check("စက္ကန့် → span index မှန်သည်", set(z) == {0, 1}, z)
    check("၁.၀၈ ထက် မကျော်အောင် ချသည်", z[1] == PS.MAX_PUNCH, z.get(1))
    check("span တစ်ခုထဲ ပထမတစ်ခုသာ", z[1] == PS.MAX_PUNCH)
    check("zoom ၁.၀ ကို ကျော်သည်", 2 not in z)
    check("timeline ပြင် ကျော်သည်", len(z) == 2)

    print("\n── ၃ခ · plan punch ကို render span အဖြစ် ခွဲသည် ──")
    p2 = PS.empty("v1")
    p2["cameraReframes"] = [
        ev("rp1", 3.0, 5.0, "reframe", "reframe", props={"zoom": 1.06}),
        ev("rp2", 15.0, 17.0, "reframe", "reframe", props={"zoom": 1.08}),
    ]
    rs, rz = EX.reframe_spans(p2, spans, {0: 1.10})
    check("reframe က source span ကို start/end မှာ ခွဲသည်",
          rs == [(0.0, 3.0), (3.0, 5.0), (5.0, 10.0),
                 (12.0, 15.0), (15.0, 17.0), (17.0, 22.0), (30.0, 45.0)], rs)
    check("ခွဲလည်း output အရှည် မပြောင်း",
          abs(sum(b-a for a,b in rs) - sum(b-a for a,b in spans)) < 1e-6)
    check("ရှိပြီးသား cut punch နဲ့ plan punch ကို နှစ်ခါ crop မလုပ်",
          rz.get(1) == 1.10 and rz.get(4) == 1.08, rz)

    print("\n── ၄ · SFX ──")
    p["sfxEvents"] = [
        ev("s1", 1.0, 1.2, "sfx", "sfx", props={"role": "click", "db": -20}),
        ev("s2", 5.0, 5.3, "sfx", "sfx", props={"role": "မရှိသောသံ"}),
        ev("s3", 9.0, 9.4, "sfx", "sfx", props={"role": "impact"}),
    ]
    s = EX.to_sfx(p)
    check("မရှိသော role ကျော်သည်", len(s) == 2, s)
    check("dB ပါလာသည်", s[0] == (1.0, "click", -20), s[0])
    check("dB မပါလျှင် ပုံသေ", s[1][2] == -16, s[1])

    print("\n── ၅ · အတည်ပြုရမည့် သတိပေးချက် ──")
    p["qualityWarnings"] = [
        dict(code="low_contrast", eventId="c1", message="x"),
        dict(code="template_repeat", eventId="t1", message="y"),
        dict(code="missing_asset", eventId="a1", message="z"),
    ]
    u = EX.unresolved(p)
    check("critical သာ ယူသည်", {x["code"] for x in u} ==
          {"low_contrast", "missing_asset"}, u)

    print("\n── ၆ · အကျဉ်းချုပ် ──")
    sm = EX.summary(p)
    check("ရေတွက် မှန်သည်",
          sm["captions"] == 3 and sm["templates"] == 3 and sm["critical"] == 2, sm)
    check("template ID စာရင်း ပါသည်",
          "prem5.line_by_line" in sm["templateIds"], sm["templateIds"])

    print("\n── ၇ · grade ──")
    p["colorGrades"] = [
        ev("g1", 0.0, 40.0, "grade", "grade", props={"sat": 1.02}),
        ev("g2", 40.0, 77.0, "grade", "grade", props={"sat": 1.10}),
    ]
    msgs = []
    go = EX.grade_over(p, log=msgs.append)
    check("ပထမတစ်ခုသာ ယူသည်", go == {"sat": 1.02}, go)
    check("ကျန်တာ ကျော်ကြောင်း ပြောသည်", any("ပထမတစ်ခုသာ" in m for m in msgs))

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
