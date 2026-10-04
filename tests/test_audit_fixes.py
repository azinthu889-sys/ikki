# -*- coding: utf-8 -*-
"""style audit (၂၀၂၆-၁၀-၀၄) မှာ တွေ့ခဲ့သော ချို့ယွင်းချက်များ ပြန်မဖြစ်စေရန်

report: `AI Company/ikki-audit/IKKI-style-audit-2026-10-04.md`
  X9 · မရှိသော style နာမည်က တိတ်တဆိတ် cinematic-vlog ဖြစ်ခဲ့ (hype-2026)
  X2 · tag 「knowledge_sharing」 တစ်ခုတည်းသော crypto chart က 「ကျွမ်းကျင်မှု」
       စာကြောင်းပေါ် ကျခဲ့ — Gemini က `my` tag သာ မြင်ရ၍
  X1 · စကား ရှိသော်လည်း စာတန်း မရှိ — cap_cover ကို စာကြောင်း အချိုးအဖြစ်
       သုံးခဲ့ · ASR chunk အလွတ်ကို လက်ခံခဲ့ · စာသားက တစ်ဝက်သာ ဖုံးခဲ့
"""
import os
import re
import sys
import unittest

R = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(R, "core"))
import recipes as RC  # noqa: E402
import broll as BR  # noqa: E402


def _src(rel):
    with open(os.path.join(R, rel), encoding="utf-8") as f:
        return f.read()


class X9RecipeAlias(unittest.TestCase):
    def test_renamed_style_maps(self):
        self.assertEqual(RC.apply("hype-2026", {})["_id"], "ref-talk")
        self.assertTrue(RC.known("hype-2026"))

    def test_unknown_is_not_known(self):
        self.assertFalse(RC.known("no-such-style"))

    def test_worker_logs_unknown(self):
        self.assertIn("RC.known(job.get(\"recipe\"))", _src("worker/run.py"))


class X2BrollTags(unittest.TestCase):
    def test_generic_clip_gets_slug_words(self):
        c = {"my": ["knowledge_sharing"], "en": ["knowledge", "sharing"],
             "src": "https://www.pexels.com/video/crypto-market-analysis-with-trading-charts-38687557/"}
        BR._enrich(c)
        for w in ("crypto", "market", "trading", "charts"):
            self.assertIn(w, c["en"])
        self.assertNotIn("with", c["en"])

    def test_described_clip_untouched(self):
        c = {"my": ["ကျောင်းသား", "စာမေးပွဲ"], "en": ["student", "exam"],
             "src": "https://www.pexels.com/video/crypto-market-1/"}
        BR._enrich(c)
        self.assertEqual(c["en"], ["student", "exam"])

    def test_gemini_rows_include_en(self):
        self.assertRegex(_src("core/broll.py"), r'" · "\.join\(_my \+ _en\)')


class X1Captions(unittest.TestCase):
    def test_cap_cover_thins_only_emphasis_styles(self):
        s = _src("worker/run.py")
        self.assertIn("if cov and caps and 0 < cov < 0.5:", s)
        self.assertNotIn("if cov and caps and 0 < cov < 1:", s)

    def test_every_word_styles_keep_all_lines(self):
        # Zin: 「Every word gets a subtitle」 — ဒီ style တွေ ၀.၅ အောက် မကျရ
        for k in ("headtop", "vlog", "short-video", "short-916", "ref-talk"):
            cov = RC.get(k).get("cap_cover")
            self.assertTrue(cov is None or cov >= 0.5, (k, cov))

    def test_empty_asr_chunk_with_speech_retries(self):
        s = _src("core/asr.py")
        self.assertIn("_empty_tries = 2 if _sp_ratio >= 0.30 else 0", s)

    def test_tail_asr_when_text_stops_early(self):
        s = _src("worker/run.py")
        self.assertIn('REPORT["tail_asr"]', s)
        self.assertRegex(s, r"if _tail >= 5\.0:")


class X1CaptionWidth(unittest.TestCase):
    """short-916: ~၁၄s (၂၀%) စာတန်း ဘယ်/ညာ ပြတ် — card လမ်း ၄ ခုလုံး ဖြတ်သော
    `track()` မှာ နောက်ဆုံး ဂိတ်。 တိုင်းထား (MyanmarBlack 182px · stroke 0.3):
    ယခင် ink 0→1080 (ပြတ်) · ယခု ၂ ကြောင်း ခွဲ 69→1011 / 60→1020 (176/143px)。"""
    def test_hard_gate_in_track(self):
        s = _src("core/captions.py")
        self.assertIn("_hard = int(W * 0.92)", s)
        self.assertIn("_two = split_two(lines[0], MW, sz, font, _hard - _sw)", s)


if __name__ == "__main__":
    unittest.main()
