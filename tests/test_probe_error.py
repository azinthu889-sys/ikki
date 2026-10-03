# -*- coding: utf-8 -*-
"""ဗီဒီယို ဖတ်မရလျှင် **ဖတ်လို့ရသော အမှားစာသား** ပြရမည်

⚠️⚠️ ၂၀၂၆-၁၀-၀၃ — Zin က UI မှာ 「**ရပ်သွားပါတယ် · 'streams'**」 ဟု
   မြင်ရသည်。 `probe()` က `j["streams"][0]` ကို တိုက်ရိုက် ယူသဖြင့်
   ဖတ်မရသော ဖိုင်မှာ `KeyError: 'streams'` ဖြစ်ပြီး အဲဒီ စာသားက
   **တိုက်ရိုက် သုံးစွဲသူဆီ** ရောက်သည်。

   「'streams'」 က ဘာမှ မဆိုလို — ဖိုင် ပျက်နေလား · ဗီဒီယို မဟုတ်လား ·
   တင်တာ မပြီးလား **မခွဲနိုင်**ပါ。 သုံးစွဲသူ လုပ်စရာလည်း မပါ。

⚠️ အမှားက `render()` ရဲ့ **ပထမဆုံး စာကြောင်း** (`m = probe(src)`) မှာ
   ဖြစ်သည် ⇒ ဗီဒီယိုတိုင်းက ဒီလမ်းကို ဖြတ်ရသည်。
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "worker"))


class Readable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.zeros = os.path.join(cls.d, "zeros.mp4")
        with open(cls.zeros, "wb") as f:
            f.write(b"\0" * (512 * 1024))
        cls.missing = os.path.join(cls.d, "nope.mp4")
        cls.good = os.path.join(cls.d, "ok.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                        "testsrc2=size=320x240:rate=25:duration=2",
                        "-c:v", "libx264", "-preset", "ultrafast",
                        "-pix_fmt", "yuv420p", cls.good], check=True)

    def _probe(self, p):
        import run as W
        return W.probe(p)

    def test_a_non_video_does_not_leak_a_keyerror(self):
        """⚠️ **အဓိက** — 「'streams'」 ဘယ်တော့မှ မပြရ"""
        with self.assertRaises(Exception) as cm:
            self._probe(self.zeros)
        self.assertNotIsInstance(cm.exception, KeyError)
        self.assertNotEqual(str(cm.exception).strip("'"), "streams")

    def test_the_message_says_what_and_what_to_do(self):
        with self.assertRaises(Exception) as cm:
            self._probe(self.zeros)
        msg = str(cm.exception)
        self.assertIn("ဗီဒီယို ဖတ်လို့ မရပါ", msg)
        self.assertIn("ပြန်တင်", msg)          # လုပ်စရာ
        self.assertIn("MB", msg)                                                  # အရွယ်

    def test_a_missing_file_is_handled_too(self):
        with self.assertRaises(Exception) as cm:
            self._probe(self.missing)
        self.assertNotIsInstance(cm.exception, KeyError)

    def test_a_real_video_still_probes(self):
        """⚠️ guard ထည့်လို့ ပုံမှန် ဖိုင်တွေ ပျက်မသွားစေရ"""
        m = self._probe(self.good)
        self.assertEqual(m["w"], 320)
        self.assertEqual(m["h"], 240)
        self.assertAlmostEqual(m["fps"], 25.0, places=1)
        self.assertAlmostEqual(m["dur"], 2.0, delta=0.2)

    def test_zero_values_are_refused(self):
        """⚠️ **၀ ကို ဆက်မသွားရ** — အောက်က တွက်ချက်မှုတိုင်း ပျက်ပြီး
           အမှားစာသားက ဒီနေရာကနေ ဝေးသွားမည် (ရှာရ ခက်သည်)。"""
        import io
        src = io.open(os.path.join(HERE, "..", "worker", "run.py"),
                      encoding="utf-8").read()
        i = src.find("def probe(p):")
        w = src[i:i + 2600]
        self.assertIn("fps <= 0 or dur <= 0", w)

    def test_ffprobe_own_message_is_carried(self):
        """⚠️ ffprobe ရဲ့ စာသားက အကြောင်းရင်း ပြောတတ်သည် (moov မရှိ စသည်)"""
        import io
        src = io.open(os.path.join(HERE, "..", "worker", "run.py"),
                      encoding="utf-8").read()
        i = src.find("def probe(p):")
        w = src[i:i + 2600]
        self.assertIn("r.stderr", w)
        self.assertIn("ffprobe:", w)


if __name__ == "__main__":
    unittest.main(verbosity=2)
