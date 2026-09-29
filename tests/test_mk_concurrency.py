# -*- coding: utf-8 -*-
"""render ၂ ခု တစ်ပြိုင်နက် ပြေးလျှင် ဂရပ်ဖစ် မပျောက်ရ

⚠️ ၂၀၂၆-၀၉-၃၀ (IKKI short video session က တိုင်း၍ တွေ့) —
   modern15 မှာ 「Tokutei」 wipe pop (၀.၄s) ပျောက်ပြီး log မှာ
     ⚠️ slide clip ထုတ်၍ မရ: FileNotFoundError … 'work/kt/sl_008.png'
   တစ်ကြောင်းသာ ကျန်ခဲ့သည်。 အကြောင်းရင်း — motionkit က **တစ်ခုတည်း**
   ရှိပြီး template တွေက `work/<mod>/<tag>_f0000.png` ဆိုတဲ့ relative
   လမ်းကြောင်းမှာ ရေးသည်。 `dress.slide_clip` က catalog လမ်းကြောင်းမှာ
   tag `"sl"` **ကိန်းသေ** သုံးခဲ့သဖြင့်
     (က) job ၂ ခုက တူညီသော ဖိုင်နာမည် ကို ရေးမိ
     (ခ) `_mk_cache_clear()` ရဲ့ `work/*/sl*` glob က **အခြား job ရဲ့**
         ဖရိမ်းများပါ ဖျက်မိ
   ⇒ VPS မှာ worker ၂ ခု တင်လျှင် ကျပန်း ပျောက်မည် ([[ikki-scale-500]])。
"""
import os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import run as W        # noqa: E402
import dress as DR     # noqa: E402


class JobTag(unittest.TestCase):
    def test_differs_per_job(self):
        a = W.mk_job_tag("/tmp/jobA/work")
        b = W.mk_job_tag("/tmp/jobB/work")
        self.assertNotEqual(a, b, (a, b))

    def test_stable(self):
        self.assertEqual(W.mk_job_tag("/tmp/jobA/work"),
                         W.mk_job_tag("/tmp/jobA/work"))

    def test_same_dir_any_spelling(self):
        # ⚠️ abspath ⇒ လမ်းကြောင်း တူလျှင် tag တူရမည်
        self.assertEqual(W.mk_job_tag("/tmp/jobA/work"),
                         W.mk_job_tag("/tmp/jobA/./work"))

    def test_filename_safe(self):
        t = W.mk_job_tag("/tmp/a b/ဂျပန်/work")
        self.assertTrue(t.isalnum(), t)
        self.assertLessEqual(len(t), 8, t)


class FramesClear(unittest.TestCase):
    """`work/*/<tag>*` — **ကိုယ့် job ရဲ့ ဖိုင်များကိုသာ**"""

    def _mk(self, root, mod, name):
        d = os.path.join(root, "work", mod)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, name)
        open(p, "wb").write(b"x")
        return p

    def test_only_own_tag_removed(self):
        with tempfile.TemporaryDirectory() as r:
            mine  = self._mk(r, "kt", "sAAAAAAp00_f0000.png")
            other = self._mk(r, "kt", "sBBBBBBp00_f0000.png")
            n = W.mk_frames_clear(r, "sAAAAAA")
            self.assertEqual(n, 1)
            self.assertFalse(os.path.exists(mine))
            self.assertTrue(os.path.exists(other),
                            "အခြား job ရဲ့ ဖရိမ်း ပျောက်သွားသည်")

    def test_all_modules(self):
        with tempfile.TemporaryDirectory() as r:
            ps = [self._mk(r, m, "sAAAAAAp00_f0000.png")
                  for m in ("kt", "prem", "thm")]
            self.assertEqual(W.mk_frames_clear(r, "sAAAAAA"), 3)
            for p in ps:
                self.assertFalse(os.path.exists(p))

    def test_blank_tag_removes_nothing(self):
        # ⚠️ tag ဗလာ ဆိုလျှင် glob က `work/*/*` ဖြစ်ပြီး အားလုံး ပါသွားမည်
        with tempfile.TemporaryDirectory() as r:
            p = self._mk(r, "kt", "sAAAAAAp00_f0000.png")
            for t in ("", None, "   "):
                self.assertEqual(W.mk_frames_clear(r, t), 0, repr(t))
            self.assertTrue(os.path.exists(p))

    def test_missing_root_ok(self):
        self.assertEqual(W.mk_frames_clear("/nonexistent/xyz", "sAAAAAA"), 0)


class SlideClipTag(unittest.TestCase):
    """`slide_clip(tag=…)` က template ကို တကယ် ရောက်ရမည်"""

    def test_tag_reaches_template(self):
        seen = []

        class FakeMod:
            @staticmethod
            def faker(tag, *a, **k):
                seen.append(tag)
                return {}          # anim မရှိ ⇒ slide_clip က None ပြန်မည်

        sys.modules["zzfake"] = FakeMod
        try:
            with tempfile.TemporaryDirectory() as d:
                DR.slide_clip("statement", "ခေါင်းစဉ်", None, None, "",
                              os.path.join(d, "p00.mov"), 2.0,
                              log=lambda *a: None, fps=30,
                              template="zzfake.faker", props={"text": "အေ"},
                              tag="sDEADBEp00")
        finally:
            sys.modules.pop("zzfake", None)
        self.assertEqual(seen, ["sDEADBEp00"], seen)

    def test_default_tag_from_out(self):
        # tag မပေးလျှင် `out` ရဲ့ ဖိုင်နာမည် (ယခင် အပြုအမူ)
        seen = []

        class FakeMod:
            @staticmethod
            def faker(tag, *a, **k):
                seen.append(tag); return {}

        sys.modules["zzfake2"] = FakeMod
        try:
            with tempfile.TemporaryDirectory() as d:
                DR.slide_clip("statement", "ခေါင်းစဉ်", None, None, "",
                              os.path.join(d, "p07.mov"), 2.0,
                              log=lambda *a: None, fps=30,
                              template="zzfake2.faker", props={"text": "အေ"})
        finally:
            sys.modules.pop("zzfake2", None)
        self.assertEqual(seen, ["p07"], seen)

    def test_never_bare_sl(self):
        # ⚠️ ကိန်းသေ `"sl"` က ဒီ ချွတ်ယွင်းချက် ရဲ့ အရင်းအမြစ် ⇒ ပြန်မလာရ
        import io as _io
        src = _io.open(os.path.join(os.path.dirname(__file__), "..",
                                    "core", "dress.py"), encoding="utf-8").read()
        for bad in ('_call_template(fn, template, "sl"', 'fn("sl", head'):
            self.assertNotIn(bad, src, bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
