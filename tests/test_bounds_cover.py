# -*- coding: utf-8 -*-
"""ပုံစံတိုင်းရဲ့ **ပုံသေကို UI က ဖော်ပြနိုင်ရမည်**

⚠️ ၂၀၂၆-၁၀-၀၁ တိုင်းချက် — `clean()` က သုံးစွဲသူ ပို့သော `over` ကိုသာ
   ဘောင်နဲ့ ချသည်、recipe ရဲ့ **ကိုယ်ပိုင် ပုံသေကို မစစ်ပါ** ⇒ ပုံသေက
   ဘောင်ပြင် ဖြစ်နေလျှင် သုံးစွဲသူက အဲဒီ ခလုတ်ကို **တစ်ချက် ထိလိုက်တာနဲ့**
   တန်ဖိုး ခုန်ပြီး **ပုံသေဆီ ပြန်မရ**တော့ပါ。 တွေ့ခဲ့သူ ၁၀ ခု:
     cap_pct   knowledge 0.024 · ref-slides 0.024 · ref-fast 0.026 ·
               short-biz 0.0333          (ဘောင် အနိမ့် 0.035)
     cap_base  headtop 0.92 · course 0.88 · short-video 0.877
                                         (ဘောင် အမြင့် 0.87)
     lufs      cinematic-vlog −15.0      (choice ထဲ မပါ)
     music     short-916 "inspiration" · short-video "zae"
                                         (choice ထဲ မပါ — Zin ကိုယ်တိုင်
                                          နားနဲ့ ရွေးထားသော ပုဒ်များ)
   ⇒ ဒီ test က **ဘောင်က ပုံသေအားလုံးကို ခြုံရမည်** ဆိုသော စည်းကမ်းကို
     အမြဲ ထိန်းသည်。 ပုံစံ အသစ် ထည့်တိုင်း ဒီမှာ ဖမ်းမိမည်。
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import recipes as RC   # noqa: E402


def _defaults():
    return {n: RC.get(n) for n in sorted(RC.R)}


class BoundsCoverDefaults(unittest.TestCase):
    def test_every_default_inside_bounds(self):
        bad = []
        for name, r in _defaults().items():
            for k, b in RC.BOUNDS.items():
                v = r.get(k)
                if v is None:
                    continue
                if b[0] in ("int", "float"):
                    if isinstance(v, bool) or not isinstance(v, (int, float)):
                        continue
                    if not (b[1] <= v <= b[2]):
                        bad.append((name, k, v, (b[1], b[2])))
                elif b[0] == "choice":
                    if v not in b[1]:
                        bad.append((name, k, v, b[1]))
        self.assertEqual(bad, [], "ဘောင်ပြင် ပုံသေ: %s" % (bad,))

    def test_clean_keeps_every_default(self):
        """ပုံသေကို `over` အဖြစ် ပြန်ပို့လျှင် **တန်ဖိုး မပြောင်းရ**"""
        bad = []
        for name, r in _defaults().items():
            for k in RC.BOUNDS:
                v = r.get(k)
                if v is None or isinstance(v, bool):
                    continue
                got = RC.clean({k: v}).get(k, "__ဖြုတ်ခံရ__")
                if isinstance(v, float) and isinstance(got, float):
                    if abs(got - v) > 1e-9:
                        bad.append((name, k, v, got))
                elif got != v:
                    bad.append((name, k, v, got))
        self.assertEqual(bad, [], "ခလုတ် ထိလျှင် ပြောင်းသွားမည်: %s" % (bad,))


class MusicGenresReal(unittest.TestCase):
    def test_every_recipe_genre_has_a_pool(self):
        import music as MU
        bad = []
        for name, r in _defaults().items():
            g = r.get("music")
            if not g:
                continue
            if not (MU.pool(g) or []):
                bad.append((name, g))
        self.assertEqual(bad, [], "သီချင်း ရေကန် ဗလာ: %s" % (bad,))

    def test_choice_list_has_no_dead_genre(self):
        # ⚠️ dropdown ထဲ ရွေးလို့ရပါလျက် ရေကန် ဗလာ ဆိုလျှင် သုံးစွဲသူက
        #    သီချင်း မပါသော ဗီဒီယို ရမည်
        import music as MU
        dead = [g for g in RC.MUSIC if g and not (MU.pool(g) or [])]
        self.assertEqual(dead, [], "ရေကန် ဗလာ genre: %s" % (dead,))


class BoundsSane(unittest.TestCase):
    def test_ranges_ordered(self):
        for k, b in RC.BOUNDS.items():
            if b[0] in ("int", "float"):
                self.assertLess(b[1], b[2], k)

    def test_choice_not_empty(self):
        for k, b in RC.BOUNDS.items():
            if b[0] == "choice":
                self.assertTrue(b[1], k)


if __name__ == "__main__":
    unittest.main(verbosity=2)
