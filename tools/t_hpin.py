# -*- coding: utf-8 -*-
"""h_pin ကို **တကယ် ပင်ထိုးလား** စစ်သည် — fake planner နဲ့"""
import json, os, sys, tempfile, types, unittest
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)

# ── fake module ၂ ခု (တစ်ခါ ခေါ်တိုင်း တန်ဖိုး ကွာသည် = Gemini ကို ယောင်)
_N = {"plan": 0, "pick": 0}
fake_pln = types.ModuleType("planner")
fake_br = types.ModuleType("broll")

def _plan(segs, dur, opts=None, video_id="src", log=None):
    _N["plan"] += 1
    return {"templateEvents": [{"id": "e%d" % _N["plan"]}], "n": _N["plan"]}

def _pick(segs, want, used=None, min_score=3):
    _N["pick"] += 1
    return [{"clip": "c%d" % _N["pick"]}] * (6 if _N["pick"] % 2 else 5)

fake_pln.plan = _plan
fake_br.pick = _pick
sys.modules["planner"] = fake_pln
sys.modules["broll"] = fake_br

import h_pin  # noqa: E402

SEGS = [{"text": "COE စိတ်ချရတဲ့ Class", "a": 0.0, "b": 2.0},
        {"text": "အေဂျင်စီကောင်း တစ်ခု", "a": 2.0, "b": 4.0}]


class Pin(unittest.TestCase):
    def setUp(self):
        _N["plan"] = _N["pick"] = 0
        h_pin._ST.update(mode=None, path=None, rec={}, play={}, hit=0, miss=0)
        fake_pln.plan = _plan
        fake_br.pick = _pick

    def test_unpinned_differs(self):
        # ⚠️ negative control — ပင်မထိုးလျှင် တကယ် ကွာကြောင်း အရင် သက်သေပြရမည်
        a = fake_pln.plan(SEGS, 90.0)
        b = fake_pln.plan(SEGS, 90.0)
        self.assertNotEqual(a, b, "fake က ကွာမနေလျှင် ဒီ test ဘာမှ မစစ်ပါ")

    def test_record_then_replay_is_identical(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "arm.pin.json")
            h_pin.arm(out=p)
            a1 = fake_pln.plan(SEGS, 90.0)
            b1 = fake_br.pick(SEGS, 4)
            self.assertTrue(os.path.exists(p))

            # arm ၂ — ပြန်ထည့်
            fake_pln.plan = _plan; fake_br.pick = _pick
            h_pin._ST.update(mode=None, rec={}, play={}, hit=0, miss=0)
            h_pin.arm(inp=p)
            a2 = fake_pln.plan(SEGS, 90.0)
            b2 = fake_br.pick(SEGS, 4)
            self.assertEqual(a1, a2, "plan ကွာသည်")
            self.assertEqual(b1, b2, "B-roll ကွာသည်")
            self.assertEqual(h_pin._ST["hit"], 2)
            self.assertEqual(h_pin._ST["miss"], 0)

    def test_miss_is_loud(self):
        # ⚠️ မတွေ့လျှင် တိတ်တဆိတ် မကျော်ရ — miss ရေတွက်ရမည်
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "arm.pin.json")
            json.dump({}, open(p, "w"))
            h_pin.arm(inp=p)
            fake_pln.plan(SEGS, 90.0)
            self.assertEqual(h_pin._ST["miss"], 1)
            self.assertEqual(h_pin._ST["hit"], 0)

    def test_key_is_content_not_order(self):
        # ⚠️ ခေါ်ချက် အစီအစဉ် နဲ့ key လုပ်လျှင် arm ၂ က ခေါ်ချက် နည်း/များ
        #    သည်နှင့် တစ်နေရာစီ ရွေ့ပြီး မှားသော plan ပြန်ပေးမည်
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "arm.pin.json")
            h_pin.arm(out=p)
            fake_pln.plan(SEGS, 90.0)
            rec = json.load(open(p, encoding="utf-8"))
            k = list(rec)[0]
            self.assertIn("90.0", k)
            self.assertNotIn("plan|1", k)

    def test_different_input_misses(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "arm.pin.json")
            h_pin.arm(out=p)
            fake_pln.plan(SEGS, 90.0)
            fake_pln.plan = _plan
            h_pin._ST.update(mode=None, rec={}, play={}, hit=0, miss=0)
            h_pin.arm(inp=p)
            fake_pln.plan(SEGS, 120.0)        # ကာလ ကွာ ⇒ MISS ဖြစ်ရမည်
            self.assertEqual(h_pin._ST["miss"], 1)

    def test_arm_needs_exactly_one(self):
        with self.assertRaises(ValueError):
            h_pin.arm()
        with self.assertRaises(ValueError):
            h_pin.arm(out="/tmp/a", inp="/tmp/b")


if __name__ == "__main__":
    unittest.main(verbosity=2)
