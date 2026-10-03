# -*- coding: utf-8 -*-
"""ဆွဲချမှု **မပြည့်လျှင် အောင်မြင်သလို မပြန်ရ**

⚠️⚠️ ၂၀၂၆-၁၀-၀၄ Zin: 「ရပ်သွားပါတယ် · ဗီဒီယို ဖတ်လို့ မရပါ — ရုပ်လိုင်း
   မတွေ့ပါ (0.0 MB)」。 upload ၃ ခု (j_7f62a5112b47 · j_4c287c61ddb4 ·
   j_c269c834569c) တူတူ ပျက်ခဲ့သည်。

   တိုင်းထားသော သက်သေ:
   · မူရင်းဖိုင် `~/Downloads/pYoIvgBmehsqlgS5zK0TDA.mp4` = ၁၈၃,၃၄၅,၉၃၉ byte (အတိ)
   · API ပြန်ပေးချက် = `200 OK` · `content-length: 183345939` · body **၀ byte**
   · worker log = 「ဆွဲချ 0 MB · 0.4s」 ⇒ **အောင်မြင်ဟု** မှတ်ခဲ့သည်
   · `/Volumes/a/ikki_big/j_7f62a5112b47_src.mp4` = **၀ byte**

   အကြောင်းရင်း ၂ ဆင့်:
   ① API process က `~/Downloads` **ဖတ်ခွင့် မရ** (macOS)。 `os.path.isfile`
      က `stat` သာ လိုသဖြင့် ဖြတ်သွားပြီး `FileResponse` က **header ပို့ပြီးမှ**
      `open` လုပ်သည် ⇒ client က `200` + အရွယ်အတိ ရပြီး body ၀。
      သက်သေ: အတူတူ ကုဒ်ကို process အသစ် ဖွင့်တော့ ၁၈၃,၃၄၅,၉၃၉ byte အပြည့် ရသည်။
      process အဟောင်းက `/tmp/ikki_dev/uploads/` ထဲက ၃ MB ဖိုင် ရပြီး
      `~/Downloads` ထဲက ဖိုင် ၂ ခု နှစ်ခုလုံး ၀ byte。
   ② worker ရဲ့ ဆွဲချ loop က `b` ဗလာ ဖြစ်တာနဲ့ **「ပြီးပြီ」** ဟု ထင်ပြီး
      `dest` ကို ပြန်ပေးသည် — `got`/`total` **မတိုက်**ပါ。

⚠️ ① ကို ပြင်လျှင် ② က ကျန်နေမည် — ကွန်နက်ရှင် ပြတ်တာ · storage ပျက်တာ
   တိုင်းမှာ ဒီအမှားက ပြန်ပေါ်မည် ⇒ **နှစ်ဖက်လုံး** ပြင်ရသည်。
"""
import io
import os
import sys
import tempfile
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = tempfile.mkdtemp(prefix="ikki_fc_")
os.environ.setdefault("IKKI_DATA", _T)
os.environ.setdefault("IKKI_DB", os.path.join(_T, "t.db"))
sys.path.insert(0, os.path.join(_R, "worker"))
sys.path.insert(0, os.path.join(_R, "api"))
sys.path.insert(0, os.path.join(_R, "core"))


def _src(*p):
    return io.open(os.path.join(_R, *p), encoding="utf-8").read()


class Done(unittest.TestCase):
    """`_dl_done` — worker ဘက် guard"""

    def setUp(self):
        import run as W
        self.W = W
        self.d = tempfile.mkdtemp()
        self.p = os.path.join(self.d, "x.mp4")
        with open(self.p, "wb") as f:
            f.write(b"\0" * 1000)

    def test_a_complete_download_passes_through(self):
        """⚠️ guard ထည့်လို့ ပုံမှန် ဆွဲချမှု ပျက်မသွားစေရ"""
        self.assertEqual(self.W._dl_done(self.p, 1000, 1000, 0.0), self.p)
        self.assertTrue(os.path.exists(self.p))

    def test_zero_bytes_raises(self):
        """⚠️⚠️ **အဓိက** — Zin ဖြစ်ခဲ့တဲ့ အတိအကျ အမှု"""
        with self.assertRaises(RuntimeError):
            self.W._dl_done(self.p, 0, 183345939, 0.0)

    def test_a_short_download_raises(self):
        with self.assertRaises(RuntimeError):
            self.W._dl_done(self.p, 90_000_000, 183345939, 0.0)

    def test_the_truncated_file_is_removed(self):
        """⚠️ ကျန်ခဲ့လျှင် `_local_by_size` က ယူမှားနိုင်သည် ·
           `probe()` က 「0.0 MB」 ဟု **လွဲမှားစွာ** ပြမည်。"""
        with self.assertRaises(RuntimeError):
            self.W._dl_done(self.p, 0, 1000, 0.0)
        self.assertFalse(os.path.exists(self.p))

    def test_an_unknown_length_is_allowed_when_bytes_arrived(self):
        """⚠️ Content-Length မပါတဲ့ server ရှိသည် — အဲဒါကို အမှား မလုပ်ရ"""
        self.assertEqual(self.W._dl_done(self.p, 1000, 0, 0.0), self.p)

    def test_an_unknown_length_with_zero_bytes_still_raises(self):
        with self.assertRaises(RuntimeError):
            self.W._dl_done(self.p, 0, 0, 0.0)

    def test_the_message_gives_both_numbers_and_an_action(self):
        try:
            self.W._dl_done(self.p, 0, 183345939, 0.0)
        except RuntimeError as e:
            m = str(e)
        self.assertIn("0.0 MB", m)
        self.assertIn("183.3 MB", m)
        self.assertIn("ပြန် upload", m)

    def test_it_says_which_take_failed(self):
        """⚠️ multi-take မှာ ဘယ်ဖိုင်လဲ မပြောလျှင် ရှာရ ခက်သည်"""
        try:
            self.W._dl_done(self.p, 0, 10, 0.0, "take 3")
        except RuntimeError as e:
            self.assertIn("take 3", str(e))


class Wired(unittest.TestCase):
    """⚠️ guard ရေးထားပြီး **မခေါ်လျှင်** အလကား — ဆွဲချ loop နှစ်ခုလုံး ခေါ်ရမည်"""

    def setUp(self):
        self.s = _src("worker", "run.py")

    def test_both_download_loops_call_it(self):
        self.assertEqual(self.s.count("return _dl_done("), 2)

    def test_no_loop_returns_dest_bare_any_more(self):
        for fn in ("def fetch_src(", "def fetch_take("):
            i = self.s.find(fn)
            self.assertGreater(i, 0, fn)
            j = self.s.find("\ndef ", i + 1)
            self.assertNotIn("\n    return dest\n", self.s[i:j], fn)


class Serve(unittest.TestCase):
    """`_srv_up` / `_no_up` — API ဘက် guard"""

    @classmethod
    def setUpClass(cls):
        try:
            import fastapi  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("fastapi မရှိ")
        import main as M
        cls.M = M
        cls.d = tempfile.mkdtemp()
        cls.ok = os.path.join(cls.d, "ok.mp4")
        with open(cls.ok, "wb") as f:
            f.write(b"\0" * 2048)
        cls.locked = os.path.join(cls.d, "locked.mp4")
        with open(cls.locked, "wb") as f:
            f.write(b"\0" * 2048)
        os.chmod(cls.locked, 0o000)
        cls.can_lock = not os.access(cls.locked, os.R_OK)

    @classmethod
    def tearDownClass(cls):
        try: os.chmod(cls.locked, 0o644)
        except OSError: pass

    def test_a_readable_file_is_served(self):
        r = self.M._srv_up({"path": self.ok, "size": 2048})
        self.assertIsNotNone(r)

    def test_a_missing_file_falls_through(self):
        self.assertIsNone(self.M._srv_up({"path": os.path.join(self.d, "nope.mp4")}))
        self.assertIsNone(self.M._srv_up({}))

    def test_an_unreadable_file_falls_through(self):
        """⚠️⚠️ **အဓိက** — `os.path.isfile` တစ်ခုတည်း စစ်တာက ဒီဖိုင်ကို
           ဖြတ်သွားပြီး body ၀ byte နဲ့ `200 OK` ပေးခဲ့သည်。"""
        if not self.can_lock:
            self.skipTest("root အဖြစ် ဖွင့်နေသည် — ဖတ်ခွင့် ပိတ်လို့ မရ")
        self.assertIsNone(self.M._srv_up({"path": self.locked, "size": 2048}))

    def test_the_failure_says_it_is_a_permission_problem_not_a_missing_file(self):
        """⚠️ `404 no source` က 「မရှိ」 — လုပ်ရမယ့်အရာ လုံးဝ ကွဲသည်"""
        if not self.can_lock:
            self.skipTest("root အဖြစ် ဖွင့်နေသည်")
        e = self.M._no_up({"path": self.locked}, "source")
        self.assertEqual(e.status_code, 503)
        self.assertIn("ဖတ်ခွင့် မရပါ", e.detail)
        self.assertIn(self.locked, e.detail)
        self.assertIn("PermissionError", e.detail)

    def test_a_genuinely_missing_file_is_still_404(self):
        e = self.M._no_up({"path": os.path.join(self.d, "nope.mp4")}, "source")
        self.assertEqual(e.status_code, 404)
        self.assertEqual(e.detail, "no source")

    def test_shared_uploads_mode_still_short_circuits(self):
        """⚠️ စက်တူဆို ၁၈၃ MB ကို HTTP ဖြတ်ပို့စရာ မလို — အဲဒီလမ်း မပျက်စေရ"""
        os.environ["IKKI_SHARED_UPLOADS"] = "1"
        try:
            r = self.M._srv_up({"path": self.ok, "size": 2048, "local": 1})
            self.assertEqual(r, {"local": self.ok, "size": 2048})
        finally:
            os.environ.pop("IKKI_SHARED_UPLOADS", None)


class ServeWired(unittest.TestCase):
    """⚠️ endpoint ၄ ခုလုံး (src · src2 · take · ref) တူတူ ပျက်တတ်သည်

    ⚠️ `w_ref_src` က `os.path.exists` သုံးသည် (`isfile` ထက် ပိုလျော့) ⇒
       directory တစ်ခုကိုပါ ဖြတ်သွားမည်。 အတူတူ ပြင်ရသည်。
    """

    def setUp(self):
        self.s = _src("api", "main.py")

    def test_all_three_endpoints_use_the_guard(self):
        self.assertEqual(self.s.count("_r = _srv_up(u,"), 4)
        self.assertEqual(self.s.count("raise _no_up(u,"), 4)

    def test_the_error_is_always_raised_never_returned(self):
        """⚠️ `_no_up` က exception ကို ပြန်ပေးသည် — ခေါ်သူ `raise` မေ့လျှင်
           endpoint က `200 null` ပြန်မည် (worker က JSON ဟု ဖတ်ပြီး ပျက်မည်)。"""
        import re
        for m in re.finditer(r"(\n *)_no_up\(", self.s):
            self.assertIn("raise", self.s[m.start()-6:m.end()],
                          self.s[m.start():m.end()+30])

    def test_the_bare_isfile_serve_is_gone(self):
        """⚠️ တစ်နေရာ ကျန်ခဲ့လျှင် အဲဒီလမ်းက တိတ်တဆိတ် ပျက်နေမည်"""
        self.assertNotIn('return FileResponse(u["path"])', self.s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
