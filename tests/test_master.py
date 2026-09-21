# -*- coding: utf-8 -*-
"""mastering converge loop — **စုပေါင်း gain ကို ပြန်မထည့်ရ**。

⚠️ ၂၀၂၆-၀၉-၂၁ j_1f9561de04b3 — `out` က ကြိမ်တိုင်း ပြောင်းပြီးသား ဖြစ်ပါလျက်
   စုပေါင်း `gain` ကို ပြန်ထည့်သဖြင့် နှစ်ထပ် ဖြစ်ကာ တုန်ခါခဲ့သည် —
     −15.4 → −14.6 → −13.6 → −13.4 ⇒ loop ကုန်ပြီး **−13.0** ထွက်
   ဂိတ် (−15.5…−13.5) ကျသည်。 ပြီးတော့ loop က နောက်ဆုံး ရေးချက်ကို
   **မတိုင်းဘဲ** ထွက်သဖြင့် log ရဲ့ နောက်ဆုံးလိုင်းက ဟောင်းနေခဲ့သည်。
"""
import os, re, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = open(os.path.join(ROOT, "core", "spans.py"), encoding="utf-8").read()


class Master(unittest.TestCase):

    def test_applies_delta_not_total(self):
        """ffmpeg ကို **ဒီကြိမ် ကွာချက်** ပဲ ပေးရမည်"""
        self.assertIn('volume={step:+.2f}dB', SRC)
        self.assertNotIn('volume={gain:+.2f}dB', SRC,
                         "စုပေါင်း gain ကို ပြန်ထည့်နေသည် — နှစ်ထပ် ဖြစ်မည်")

    def test_step_is_clamped(self):
        """တစ်ကြိမ်လျှင် ခုန်ချက် ကန့်သတ်ရမည် — တုန်ခါမှု တားရန်"""
        self.assertRegex(SRC, r"step\s*=\s*max\(-3\.0,\s*min\(3\.0,\s*d_i\)\)")

    def test_final_verify_exists(self):
        """မကိုက်ဘဲ ထွက်လျှင် တကယ့် ကိန်းကို ပြရမည်"""
        self.assertIn("if not ok:", SRC)
        self.assertIn("mastering ချိန်", SRC)
        # loop ပြီးမှ ပြန်တိုင်းသည်
        i = SRC.index("if not ok:")
        self.assertIn("_tp(out)", SRC[i:i + 400])
        self.assertIn("_lufs(out)", SRC[i:i + 400])

    def test_gate_not_weakened(self):
        """ဂိတ် မလျှော့ရ — လက်ခံချက် ±၀.၄ LUFS · TP ≤ target အတိုင်း"""
        self.assertIn("abs(d_i) <= 0.4", SRC)
        self.assertIn("d_tp <= 0.0", SRC)

    def test_default_targets(self):
        """ပုံသေ −14 LUFS · −1.0 dBTP (YouTube/TikTok)"""
        self.assertRegex(SRC, r"def loudness\(inp, out, lufs=-14\.0, tp=-1\.0")

    def test_iterations_enough(self):
        """၄ ကြိမ်က မလောက်ခဲ့ — ၅ ကြိမ်"""
        self.assertRegex(SRC, r"ITER\s*=\s*5")

    def test_limiter_level_disabled(self):
        """`alimiter` **တိုင်း** မှာ `level=disabled` ပါရမည် — မပါလျှင်
        makeup gain က LUFS ကို −14.18 မှ −12.68 သို့ တင်ပစ်သည် (တိုင်းထားသည်)。"""
        used = re.findall(r"alimiter=[^\"']+", SRC)
        self.assertGreaterEqual(len(used), 2, "alimiter ၂ နေရာ ရှိရမည်")
        for a in used:
            self.assertIn("level=disabled", a, f"level=disabled မပါ: {a[:60]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
