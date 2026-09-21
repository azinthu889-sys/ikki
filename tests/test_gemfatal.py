# -*- coding: utf-8 -*-
"""credit ကုန်ခြင်း (402) က **ပြန်ထူမလာ** ⇒ ချက်ချင်း ရပ်ရမည်。

⚠️ ၂၀၂၆-၀၉-၂၁: `402 Your prepayment credits are depleted` က fatal စာရင်းထဲ
   မပါသဖြင့် chunk တစ်ခုလျှင် retry ၄ ခါ × chunk ၆ ခု = ခေါ်ဆိုမှု ၂၄ ခု
   အလကား ကုန်ပြီး (တစ်ခု ~၆၂s) Zin ရဲ့ အချိန် ၆ မိနစ်ကျော် ကုန်ခဲ့သည်。
   ပြီးတော့ မျက်နှာပြင်မှာ 「chunk ၁၂/၆ ခု အလွတ်」ဟု ပြခဲ့ရာ တကယ့်
   အကြောင်းရင်း (ငွေ) လုံးဝ မပေါ်ခဲ့ပါ。
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import gemguard as G          # noqa: E402

CRED = '{"error":{"code":402,"message":"Your prepayment credits are depleted."}}'


class GemFatal(unittest.TestCase):

    def setUp(self):
        G._dead.clear(); G._reason[0] = ""

    def test_402_is_fatal(self):
        self.assertTrue(G.fatal(402, CRED), "402 က fatal ဖြစ်ရမည်")
        self.assertTrue(G.dead())

    def test_402_records_reason(self):
        G.fatal(402, CRED)
        self.assertIn("depleted", G.reason().lower(),
                      "အကြောင်းရင်း မှတ်ရမည် — မဟုတ်လျှင် UI မှာ မပြနိုင်")

    def test_401_403_still_fatal(self):
        for c in (401, 403):
            G._dead.clear()
            self.assertTrue(G.fatal(c, "{}"), f"{c} က fatal ဖြစ်ရမည်")

    def test_plain_429_not_fatal(self):
        """သာမန် rate limit က ပြန်ကြိုးစားလို့ ရသည် ⇒ fatal မဟုတ်"""
        self.assertFalse(G.fatal(429, '{"error":{"message":"rate limit"}}'))
        self.assertFalse(G.dead())

    def test_500_not_fatal(self):
        self.assertFalse(G.fatal(500, "server error"))

    def test_asr_message_names_credit(self):
        """asr.py က credit ကုန်တာကို အတိအလင်း ပြောရမည် (「chunk အလွတ်」မဟုတ်)"""
        src = open(os.path.join(ROOT, "core", "asr.py"), encoding="utf-8").read()
        self.assertIn("credit ကုန်ပါပြီ", src)
        self.assertIn("ai.studio/projects", src)

    def test_asr_no_double_count(self):
        """ဗလာ chunk ကို နှစ်ခါ မရေတွက်ရ — 「၁၂/၆」ဖြစ်ခဲ့သည်"""
        src = open(os.path.join(ROOT, "core", "asr.py"), encoding="utf-8").read()
        self.assertIn("if not good and txt.strip(): n_empty += 1", src)
        self.assertNotIn("if not good: n_empty += 1", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)
