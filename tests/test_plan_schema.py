"""HeadtopEditPlan schema — အတည်ပြုချက် test

⚠️ import လမ်းကြောင်း **နှစ်မျိုးလုံး** စစ်သည် — worker က `core/` ကို flat
   import လုပ်ပြီး API က package အဖြစ် လုပ်သည် (`ikki-dual-import-paths`)。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import manifest as MF          # noqa: E402
import plan_schema as PS       # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def ev(eid, a, b, layer, typ, **kw):
    d = dict(id=eid, startTime=a, endTime=b, layer=layer, type=typ,
             reason="test", confidence=0.9, props=kw.pop("props", {}))
    d.update(kw)
    return d


def main():
    print("── ၁ · အခြေခံ ပုံစံ ──")
    p = PS.empty("v1")
    ok, e, w = PS.validate(p, MF, duration=77.6)
    check("ဗလာ plan အောင်သည်", ok, e)

    bad = PS.empty("v1"); bad["version"] = 2
    ok, e, _ = PS.validate(bad, MF)
    check("version မှားလျှင် ကျသည်", not ok and any("version" in x for x in e))

    bad = PS.empty("v1"); bad["style"] = "vlog"
    ok, e, _ = PS.validate(bad, MF)
    check("style မှားလျှင် ကျသည်", not ok)

    bad = PS.empty(""); ok, e, _ = PS.validate(bad, MF)
    check("sourceVideoId ဗလာ ကျသည်", not ok)

    print("\n── ၂ · event စည်းမျဉ်း ──")
    p = PS.empty("v1")
    p["captions"] = [ev("c1", 1.0, 2.0, "caption", "caption"),
                     ev("c1", 3.0, 4.0, "caption", "caption")]
    ok, e, _ = PS.validate(p, MF)
    check("id ထပ်လျှင် ကျသည်", not ok and any("ထပ်" in x for x in e))

    p = PS.empty("v1")
    p["captions"] = [ev("c1", 5.0, 2.0, "caption", "caption")]
    ok, e, _ = PS.validate(p, MF)
    check("endTime < startTime ကျသည်", not ok)

    p = PS.empty("v1")
    p["captions"] = [ev("c1", 1.0, 200.0, "caption", "caption")]
    ok, e, _ = PS.validate(p, MF, duration=77.6)
    check("ဗီဒီယို အရှည် ကျော်လျှင် ကျသည်", not ok)

    p = PS.empty("v1")
    x = ev("c1", 1.0, 2.0, "caption", "caption"); x.pop("reason")
    p["captions"] = [x]
    ok, e, _ = PS.validate(p, MF)
    check("reason မပါလျှင် ကျသည်", not ok and any("reason" in y for y in e))

    p = PS.empty("v1")
    x = ev("c1", 1.0, 2.0, "caption", "caption"); x["confidence"] = 1.4
    p["captions"] = [x]
    ok, e, _ = PS.validate(p, MF)
    check("confidence ဘောင်ပြင် ကျသည်", not ok)

    p = PS.empty("v1")
    p["captions"] = [ev("c1", 1.0, 2.0, "caption", "template")]
    ok, e, _ = PS.validate(p, MF)
    check("type က array နဲ့ မကိုက်လျှင် ကျသည်", not ok)

    print("\n── ၃ · template ID ──")
    p = PS.empty("v1")
    p["templateEvents"] = [ev("t1", 1.0, 4.0, "template", "template",
                              motionKitTemplateId="infogfx.steps",
                              props={"items": ["က", "ခ"]})]
    ok, e, _ = PS.validate(p, MF)
    check("တကယ်ရှိသော ID လက်ခံသည်", ok, e)

    p["templateEvents"][0]["motionKitTemplateId"] = "infogfx.does_not_exist"
    ok, e, _ = PS.validate(p, MF)
    check("မရှိသော ID ကျသည်", not ok and any("မရှိ" in x for x in e))

    p = PS.empty("v1")
    p["templateEvents"] = [ev("t1", 1.0, 4.0, "template", "template",
                              props={})]
    ok, e, _ = PS.validate(p, MF)
    check("template event မှာ ID မပါလျှင် ကျသည်", not ok)

    p = PS.empty("v1")
    p["templateEvents"] = [ev("t1", 1.0, 4.0, "template", "template",
                              motionKitTemplateId="infogfx.steps",
                              props={"bogus_param": 1})]
    ok, e, _ = PS.validate(p, MF)
    check("မရှိသော param ကျသည်", not ok and any("param မရှိ" in x for x in e))

    print("\n── ၄ · အရည်အသွေး သတိပေးချက် ──")
    p = PS.empty("v1")
    p["captions"] = [ev("c1", 1.0, 3.0, "caption", "caption",
                        props={"lines": ["၁", "၂", "၃"]})]
    ok, e, w = PS.validate(p, MF)
    check("၃ ကြောင်း သတိပေးသည်", ok and any(x["code"] == "caption_lines" for x in w))

    # ⚠️ အရောင်/နေရာက `style` ထဲ — `props` က template argument သာ
    p["captions"][0]["props"] = {}
    p["captions"][0]["style"] = {"color": "#00FF00"}
    ok, e, w = PS.validate(p, MF)
    check("ခွင့်မပြုသော အရောင် သတိပေးသည်",
          any(x["code"] == "caption_color" for x in w))

    p["captions"][0]["style"] = {"bottomPct": 0.30}
    ok, e, w = PS.validate(p, MF)
    check("စာတန်း နေရာ သတိပေးသည်",
          any(x["code"] == "caption_pos" for x in w))

    p = PS.empty("v1")
    p["cameraReframes"] = [ev("r1", 1.0, 4.0, "reframe", "reframe",
                              props={"zoom": 1.30})]
    ok, e, w = PS.validate(p, MF)
    check("punch ၁.၀၈ ကျော် သတိပေးသည်",
          any(x["code"] == "punch_too_strong" for x in w))

    p["cameraReframes"] = [ev(f"r{i}", i * 2.0, i * 2.0 + 1.0, "reframe",
                              "reframe", props={"zoom": 1.05})
                           for i in range(1, 5)]
    ok, e, w = PS.validate(p, MF)
    check("၁၅s အတွင်း punch ၂ ခု ကျော် သတိပေးသည်",
          any(x["code"] == "punch_too_many" for x in w))

    p = PS.empty("v1")
    p["templateEvents"] = [
        ev("t1", 1.0, 4.0, "template", "template",
           motionKitTemplateId="infogfx.steps", props={"items": ["က"]}),
        ev("t2", 5.0, 8.0, "template", "template",
           motionKitTemplateId="infogfx.steps", props={"items": ["ခ"]})]
    ok, e, w = PS.validate(p, MF)
    check("template ဆက်တိုက် တူ သတိပေးသည်",
          any(x["code"] == "template_repeat" for x in w))

    # ⚠️ `odo.count_up` မှာ `target` (text) လိုအပ်သည် — `label` မရှိပါ。
    #    param မှားလျှင် **error** ဖြစ်ပြီး warning အဆင့် မရောက်တော့。
    p = PS.empty("v1")
    p["templateEvents"] = [ev("t1", 1.0, 4.0, "template", "template",
                              motionKitTemplateId="odo.count_up",
                              props={"target": "ကျောင်းသား"})]
    ok, e, w = PS.validate(p, MF)
    check("ဂဏန်းမပါဘဲ odo သုံးလျှင် သတိပေးသည်",
          ok and any(x["code"] == "number_without_data" for x in w), (e, w))

    p["templateEvents"][0]["props"] = {"target": "၅၀၀"}
    ok, e, w = PS.validate(p, MF)
    check("မြန်မာ ဂဏန်း ပါလျှင် မသတိပေးပါ",
          ok and not any(x["code"] == "number_without_data" for x in w), w)

    p["templateEvents"][0]["props"] = {"target": "500"}
    ok, e, w = PS.validate(p, MF)
    check("အင်္ဂလိပ် ဂဏန်း ပါလျှင် မသတိပေးပါ",
          ok and not any(x["code"] == "number_without_data" for x in w), w)

    print("\n── ၅ · import လမ်းကြောင်း ၂ မျိုး ──")
    import importlib
    sys.path.insert(0, os.path.join(HERE, ".."))
    try:
        pk = importlib.import_module("core.plan_schema")
        check("package အဖြစ် import ရသည်", pk.VERSION == PS.VERSION)
    except Exception as exc:
        check("package အဖြစ် import ရသည်", False, repr(exc))

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
