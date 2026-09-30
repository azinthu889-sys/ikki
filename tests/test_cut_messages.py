# -*- coding: utf-8 -*-
"""ဖြတ်ခြင်း ငြင်းပယ်ချက်က **သုံးစွဲသူ လုပ်နိုင်သော** စာ ဖြစ်ရမည်

⚠️ ၂၀၂၆-၁၀-၀၁ — customer က ဗီဒီယို တင်ပြီး ၂၅ မိနစ် စောင့်ပြီးမှ
     「cut engine ငြင်းပယ်: F2 ဖြတ်မှတ် ၃ ခု စကားပေါ် ကျသည်」
   ဆိုတဲ့ စာ ရမည် — ဘာလုပ်ရမလဲ မပြပါ၊ ကိရိယာ ပျက်သလား ထင်စေသည်。
⚠️ **ဂိတ်ကို မလျှော့ရ** — F2/F3 က ထုတ်ခွင့် ပိတ်ဆဲ ဖြစ်ရမည် (「စကားထဲ
   ဘယ်တော့မှ မဖြတ်」 က ဒီ product ရဲ့ ကတိ)。 စာသားသာ ပြင်သည်。
"""
import io, os, sys, unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "core"))
CUT = io.open(os.path.join(ROOT, "core", "cut.py"), encoding="utf-8").read()
RUN = io.open(os.path.join(ROOT, "worker", "run.py"), encoding="utf-8").read()


class Actionable(unittest.TestCase):
    def test_f2_says_what_to_do(self):
        # 「ညင်သာ」 = gentle · 「မဖြတ်ပါ」 = off — တကယ် ရှိသော ရွေးချယ်ချက်
        self.assertIn("ညင်သာ", CUT)
        self.assertIn("မဖြတ်ပါ", CUT)

    def test_named_options_exist(self):
        import recipes as RC
        labels = {v[0] for v in RC.CUT_LABEL.values()}
        for want in ("ညင်သာ", "မဖြတ်ပါ"):
            self.assertIn(want, labels, "စာထဲ ပြောသော ရွေးချယ်ချက် UI မှာ မရှိ")

    def test_f2_keeps_the_code(self):
        # support အတွက် ကုတ် ကျန်ရမည်
        self.assertIn("F2", CUT)
        self.assertIn("F3", CUT)

    def test_no_engine_broke_wording(self):
        """`raise` ရဲ့ စာထဲ 「cut engine」 ပြန်မလာရ

        ⚠️ ဖိုင် တစ်ခုလုံးကို မစစ်ရ — မှတ်ချက်ထဲ အဟောင်းကို ကိုးကားထားလျှင်
           ဖမ်းမိပြီး fail မည် (ကိုယ့် test ပထမ အမှား)。 `raise` ကြောင်းသာ။
        """
        ix = RUN.find('if st.get("refusals"):')
        self.assertGreater(ix, 0)
        blk = RUN[ix:ix + 600]
        raises = [l for l in blk.splitlines() if "raise RuntimeError" in l]
        self.assertTrue(raises, "raise မတွေ့")
        line = raises[0]
        self.assertNotIn("cut engine", line, line[:120])
        self.assertIn("ဖြတ်ခြင်း ရပ်လိုက်သည်", line)

    def test_in_speech_message_actionable(self):
        ix = RUN.find('if st["in_speech"] > 0:')
        self.assertGreater(ix, 0)
        blk = RUN[ix:ix + 600]
        self.assertIn("ညင်သာ", blk)


class GateStillBlocks(unittest.TestCase):
    """⚠️ ဂိတ် မလျှော့ကြောင်း — raise ကျန်ရမည်"""

    def test_refusals_still_raise(self):
        ix = RUN.find('if st.get("refusals"):')
        self.assertGreater(ix, 0)
        self.assertIn("raise RuntimeError", RUN[ix:ix + 400])

    def test_in_speech_still_raises(self):
        ix = RUN.find('if st["in_speech"] > 0:')
        self.assertGreater(ix, 0)
        self.assertIn("raise RuntimeError", RUN[ix:ix + 400])

    def test_f1_stays_a_warning(self):
        # F1 (ဖယ်တာ များ) က သတိပေးချက်သာ — refusals ထဲ မဝင်ရ
        ix = CUT.find("if ratio > max_removed:")
        self.assertGreater(ix, 0)
        self.assertIn("warn.append", CUT[ix:ix + 300])


class RefusalShape(unittest.TestCase):
    def test_plan_returns_refusals_list(self):
        import cut as C
        # အသံ မတွေ့လျှင် F4
        sp, cuts, st = C.plan(None, meas=([], [], 0.0, {}, "aroll"))
        self.assertIn("refusals", st)
        self.assertIn("F4", st["refusals"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
