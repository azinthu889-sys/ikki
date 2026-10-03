# -*- coding: utf-8 -*-
"""ပျက်သွားသော **အခမဲ့ preview** ကို ပြန်ပေးရမည်

⚠️⚠️ ၂၀၂၆-၁၀-၀၄ အစအဆုံး စစ်ဆေးမှုမှာ တွေ့: `j_5e2a8a101fc6` ရဲ့ အခမဲ့
   preview က QC (`headtop_sfx_moments`) မအောင်ဘဲ ပျက်သွားပြီး `prev_used`
   က ၁ တက်ကာ သုံးစွဲသူက **ဘာမှ မရဘဲ အခွင့်အရေး တစ်ခု ဆုံးရှုံး**ခဲ့သည်。

   `w_fail` က မိနစ်ကို ပြန်ပေးပြီးသား ဖြစ်သည် —
   「ပျက်သွားသော အလုပ်အတွက် မိနစ် မယူရ — UI က ကတိပေးထားသည်」。
   preview ကလည် **စည်းမျဉ်း တစ်ခုတည်း** ဖြစ်ပြီး ဒီတစ်ခု ကျန်ခဲ့ခြင်း。

⚠️ `prev_n` ကို **စချိန်မှာ** တိုးသည် (ပြီးမှ တိုးလျှင် ဖြတ်ပြီး ပြန်စတာနဲ့
   အကန့်အသတ် ကျော်နိုင်၍) ⇒ ပျက်လျှင် **ပြန်လျှော့**ရသည်。

ဆက်စပ်: QC floor က ထုတ်သူရဲ့ cap နဲ့ **တူညီ**သည် (`int(per_min·dur/60)`)
⇒ ထုတ်သူက အတိအကျ မီမှ အောင်သည် — မြှားမျှ လွဲလို့ မရ。 တကယ် ဖြစ်ခဲ့:
အပြည့် render ၉/၉ ⇒ အောင် · preview ၈/၉ ⇒ ကျ。 ဂိတ် မလျှော့ပါ、ဒါပေမယ့်
မမီရင် **အရင်ကတည်းက ပြော**ရမည် (QC အမှားမှာ နာမည်သာ ပေါ်ခဲ့သည်)。
"""
import io
import os
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _src(*p):
    return io.open(os.path.join(_R, *p), encoding="utf-8").read()


class Refund(unittest.TestCase):
    def setUp(self):
        self.s = _src("api", "main.py")

    def test_a_failed_preview_is_given_back(self):
        i = self.s.find("async def w_fail(")
        self.assertGreater(i, 0)
        w = self.s[i:i + 1700]
        self.assertIn('if (j or {}).get("mode") == "prev":', w)
        self.assertIn("prev_n=max(0,COALESCE(prev_n,0)-1)", w)

    def test_it_happens_before_the_status_is_written(self):
        """⚠️ `status='failed'` ရေးပြီးမှ လုပ်လည်း ရသည် — ဒါပေမယ့် `mode` ကို
           `j` ကနေ ဖတ်သဖြင့် **အရင် ဖတ်ထားပြီးသား** ဖြစ်ရမည်。"""
        i = self.s.find("async def w_fail(")
        w = self.s[i:i + 1700]
        a = w.find('j = db.one("SELECT * FROM jobs WHERE id=?", jid)')
        b = w.find('if (j or {}).get("mode") == "prev":')
        self.assertGreater(a, 0)
        self.assertGreater(b, a)

    def test_minutes_are_still_refunded(self):
        """⚠️ အရင် ကတိကို မဖျက်ရ"""
        i = self.s.find("async def w_fail(")
        w = self.s[i:i + 1700]
        self.assertIn("UPDATE usage SET minutes=max(0,minutes-?)", w)

    def test_the_counter_never_goes_negative(self):
        i = self.s.find("async def w_fail(")
        w = self.s[i:i + 1700]
        self.assertIn("max(0,COALESCE(prev_n,0)-1)", w)


class SfxFloor(unittest.TestCase):
    """⚠️ မမီတော့မယ်ဆိုတာ **အရင်ကတည်းက** ပြောရမည် — ဂိတ် မလျှော့ပါ"""

    def setUp(self):
        self.s = _src("worker", "run.py")

    def test_a_shortfall_is_logged_before_qc_fails(self):
        i = self.s.find('REPORT["sfx_permin_dropped"]')
        self.assertGreater(i, 0)
        w = self.s[i:i + 1600]
        self.assertIn("_mnow < _cap5", w)
        self.assertIn("headtop_sfx_moments", w)

    def test_it_records_the_gap(self):
        i = self.s.find('REPORT["sfx_permin_dropped"]')
        self.assertIn('REPORT["sfx_moments_short"]', self.s[i:i + 1600])

    def test_the_gate_itself_is_untouched(self):
        """⚠️⚠️ **ဂိတ် မလျှော့ရ** — `got >= want` အတိုင်း ကျန်ရမည်"""
        i = self.s.find('dict(key="headtop_sfx_moments"')
        self.assertGreater(i, 0)
        self.assertIn("ok=got >= want", self.s[i:i + 200])


if __name__ == "__main__":
    unittest.main(verbosity=2)
