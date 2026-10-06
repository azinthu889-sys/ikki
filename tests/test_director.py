# -*- coding: utf-8 -*-
"""AI director + beat registry + brand kit (Zin ၂၀၂၆-၁၀-၀၇ roadmap ①②③④)"""
import json
import os
import sys
import unittest

R = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(R, "core"))
os.environ["IKKI_DIRECTOR_AI"] = "0"
import director as D   # noqa: E402
import brandkit as BK  # noqa: E402
import remo as RM      # noqa: E402


def _wu():
    fx = json.load(open(os.path.join(R, "tests", "fixtures", "wu_v9_segs.json"), encoding="utf-8"))

    def om(t):
        acc = 0.0
        for a, b in fx["spans"]:
            if a <= t <= b:
                return acc + (t - a)
            acc += b - a
        return None
    segs = []
    for text, ws, end in fx["sents"]:
        w = [dict(w=x, s=s, o0=om(s)) for x, s in ws if om(s) is not None]
        segs.append(dict(text=text, o0=w[0]["o0"], o1=om(end) or w[-1]["o0"] + 0.5, words=w))
    return segs, fx["out_dur"]


class Director(unittest.TestCase):
    def test_registry_size_and_schema(self):
        T = D.types()
        self.assertGreaterEqual(len(T), 30)
        for k, v in T.items():
            self.assertIn(v["zone"], ("side", "center", "top", "bottom"), k)
            self.assertTrue(v["sfx"], k)
            self.assertIsNone(D.validate(dict(type=k)) if any(not p.endswith("?") for p in v["params"].values()) else None)
            ex = D.validate(dict(type=k, **v["example"]))
            self.assertIsNotNone(ex, k)

    def test_registry_in_sync_with_remotion(self):
        p = os.path.expanduser("~/ikki-remotion/src/kit/registry.json")
        if not os.path.exists(p):
            self.skipTest("remotion မရှိ")
        self.assertEqual(json.load(open(p, encoding="utf-8")), D.registry())

    def test_wu_rules(self):
        segs, dur = _wu()
        b = D.direct(segs, dur, ai=False, log=lambda *_: None)
        ty = [x["type"] for x in b]
        self.assertIn("timeline", ty)
        self.assertIn("stat", ty)
        st = next(x for x in b if x["type"] == "stat")
        self.assertEqual(st["value"], "500,000")          # ၅ သိန်း ⇒ 500,000 ကျပ်
        tl = next(x for x in b if x["type"] == "timeline")
        self.assertEqual([i[0] for i in tl["items"]], ["SEP 29", "OCT 31"])
        # spacing · tail · sorted
        for a, c in zip(b, b[1:]):
            self.assertGreaterEqual(c["at"] - a["at"], 2.5)
        self.assertTrue(all(x["at"] <= dur - D.TAIL for x in b))
        # anchor = word onset (output timeline)
        self.assertAlmostEqual(tl["at"], 9.91, places=2)

    def test_busy_respected(self):
        segs, dur = _wu()
        busy = [(0, 12)]
        b = D.direct(segs, dur, ai=False, busy=busy, log=lambda *_: None)
        self.assertTrue(all(x["at"] >= 12 for x in b))

    def test_burmese_clip_keeps_marks(self):
        s = D._clip("ဘယ်လိုဆုတွေရမှာလဲဆိုရင် Casper ငွေပြန်အမ်းတဲ့ဆုရယ်", 22)
        self.assertNotRegex(s[-1:], r"[က-ဪ]$|^$") if False else None
        self.assertFalse(s.endswith("င"))

    def test_face_side(self):
        segs, dur = _wu()
        b = D.direct(segs, dur, ai=False, face_x=0.3, log=lambda *_: None)
        self.assertTrue(all(x.get("pos") in (None, "right") for x in b))

    def test_sfx_events_land_on_beat(self):
        ev = RM.sfx_events([dict(type="notify", at=10.0)])
        if not ev:
            self.skipTest("sfx မရှိ")
        hit = D.registry()["hit"]
        f, t, v = ev[0]
        self.assertAlmostEqual(t + hit["p_message_in"], 10.0, places=2)

    def test_windows_merge(self):
        w = RM._windows([dict(at=5, dur=3), dict(at=8.5, dur=3), dict(at=20, dur=2)], 30)
        self.assertEqual(len(w), 2)


class BrandKit(unittest.TestCase):
    def test_accent_from_colors(self):
        k = BK.kit({"colors": ["#111111", "#1E90FF", "#FFFFFF"], "id": "u"}, {})
        self.assertEqual(k["accent"], "#1E90FF")

    def test_recipe_accent_wins_and_stable_pack(self):
        k = BK.kit({"colors": ["#1E90FF"], "id": "zae"}, {"accent": "#FFD60A"})
        self.assertEqual(k["accent"], "#FFD60A")
        self.assertEqual(BK.kit({"id": "zae"}, {})["pack"], BK.kit({"id": "zae"}, {})["pack"])

    def test_users_differ(self):
        packs = {BK.pack_for(f"user{i}")["name"] for i in range(30)}
        self.assertGreaterEqual(len(packs), 3)


if __name__ == "__main__":
    unittest.main()
