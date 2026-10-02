# -*- coding: utf-8 -*-
"""ဖြတ်မှတ် ဆက်ခြင်း — **crossfade** (ကြာချိန် မရွေ့ရ)

⚠️⚠️ Zin ၂၀၂၆-၁၀-၀၂ ရွေးချယ်ချက် 「က」 — user ရွေးထားတဲ့ နယ်နိမိတ်အတိုင်း
   **အတိအကျ ဖြတ်ပြီး crossfade နဲ့ ဖုံး**。 ယခင်က အပိုင်းတိုင်းကို သုညဆီ
   `afade` လုပ်ပြီး `concat` လုပ်ခဲ့ရာ ဆက်မှတ်တိုင်းမှာ အသံ ၄၀ms ပြတ်သည် ⇒
   ဖြတ်မှတ်ကို တိတ်ဆိတ်မှုထဲ ထားရသည် ⇒ ဖျက်ချက် နယ်နိမိတ် ရွေ့ရသည်
   (ဘေးက စကား ၀.၂၂s ပါသွားခဲ့သည် — `test_drop_precision`)。

⚠️⚠️ **ကြာချိန် မရွေ့စေရ**。 `acrossfade=d` က အပိုင်း ၂ ခုကို `d` ကြာ
   ထပ်စေသဖြင့် ဆက်မှတ် ၄၃ ခု ဆိုလျှင် ၁.၀၇s တိုသွားမည် (ဗီဒီယိုနဲ့ မကိုက်)。
   တိုင်းချက် — handle မပါ **−၀.၁၀၀s** / ဆက်မှတ် ၄ ခု ·
   handle ပါ (ပြင်ပ အစွန်း ၂ ဖက် မပါ) **+၀.၀၀၀s**。
"""
import io
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

import spans as SP                                            # noqa: E402

SRC_PY = os.path.join(os.path.dirname(__file__), "..", "core", "spans.py")
WAV = "/private/tmp/claude-501/-Applications-my-file-My-bussiness-ZAE-NEW-OPERATION-N8N-Work-Flow-n8n-All-Workflow/8d95eb58-d414-4434-b5a9-1eacd9f8a629/scratchpad/src.wav"


def _dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


class Shape(unittest.TestCase):
    def setUp(self):
        self.s = io.open(SRC_PY, encoding="utf-8").read()

    def test_video_pass_has_no_audio(self):
        """⚠️ အသံကို span encode မှာ မထည့်ရ — crossfade က နောက်မှ လုပ်သည်"""
        self.assertIn('"-t",f"{d:.3f}","-an"', self.s)
        self.assertNotIn('"-c:a","aac","-b:a","192k",\n                "-avoid_negative',
                         self.s)

    def test_handles_skip_outer_edges(self):
        """⚠️ ပထမရဲ့ အစ · နောက်ဆုံးရဲ့ အဆုံး မှာ handle မထည့်ရ"""
        self.assertIn("hl = (d / 2.0) if i > 0 else 0.0", self.s)
        self.assertIn("hr = (d / 2.0) if i < n - 1 else 0.0", self.s)

    def test_accurate_seek_for_audio(self):
        """⚠️ `-ss` က `-i` **နောက်** — keyframe ရှာဖွေမှု မဟုတ်ရ"""
        i = self.s.index('def xfade_audio(')
        seg = self.s[i:i + 3000]
        self.assertIn('"-i", src,\n                        "-ss"', seg)

    def test_fallback_is_not_silent(self):
        """⚠️ ကျဆုံးလျှင် တိတ်တဆိတ် မကျော်ရ — အကြောင်း ပြရမည်"""
        self.assertIn("အသံ crossfade မရ", self.s)
        self.assertIn("ယခင်နည်း (fade+concat) သို့ ပြန်သွားသည်", self.s)

    def test_xfade_length_named(self):
        self.assertIn("XFADE = 0.025", self.s)


@unittest.skipUnless(os.path.exists(WAV), "နမူနာ အသံ မရှိ")
class Duration(unittest.TestCase):
    SPANS = [(2.0, 5.0), (8.0, 11.5), (14.0, 16.2), (20.0, 23.0), (28.0, 30.5)]

    def test_no_drift(self):
        import tempfile
        want = sum(b - a for a, b in self.SPANS)
        with tempfile.TemporaryDirectory() as d:
            o = os.path.join(d, "a.wav")
            SP.xfade_audio(WAV, self.SPANS, o)
            self.assertAlmostEqual(_dur(o), want, places=2)

    def test_single_span_is_plain(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            o = os.path.join(d, "a.wav")
            SP.xfade_audio(WAV, [(3.0, 6.5)], o)
            self.assertAlmostEqual(_dur(o), 3.5, places=2)

    def test_many_joins_still_exact(self):
        """⚠️ ဆက်မှတ် များလျှင် ရွေ့မှု စုပုံမည် — ၁၂ ခုနဲ့ စစ်သည်"""
        import tempfile
        sp = [(float(i * 3), float(i * 3 + 1.5)) for i in range(12)]
        want = sum(b - a for a, b in sp)
        with tempfile.TemporaryDirectory() as d:
            o = os.path.join(d, "a.wav")
            SP.xfade_audio(WAV, sp, o)
            self.assertAlmostEqual(_dur(o), want, places=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
