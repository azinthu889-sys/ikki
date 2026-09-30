# -*- coding: utf-8 -*-
"""motionkit ရဲ့ ကတ် ဆောက်မရလျှင် **render မရပ်ရ**

⚠️⚠️ ၂၀၂၆-၁၀-၀၁ တကယ် ဖြစ်ခဲ့ — knowledge render မှာ cttext ရဲ့ Swift
   `try!` က `DecodingError.typeMismatch` ဖြစ်ပြီး motionkit က
   `raise SystemExit` လုပ်ခဲ့သည်。 `SystemExit` က **`BaseException`** ကနေ
   ဆင်းသက်၍ ခေါ်သူရဲ့ `except Exception` က မဖမ်းမိပါ ⇒ ၂၅ မိနစ် render
   တစ်ခုလုံး **Traceback မရှိဘဲ · res.json မရှိဘဲ** တိတ်တဆိတ် သေခဲ့သည်。
   ကတ် တစ်ခု ပျက်တာက ဗီဒီယို မထွက်ရ အကြောင်း မဟုတ် — 「⊘ ဆောက်မရ」 နဲ့
   ကျော်သွားရမည် (ခေါ်သူမှာ အဲဒီလမ်း ရှိပြီးသား)。
"""
import io, os, sys, unittest

MK = ("/Applications/my file/My bussiness/ZAE NEW　OPERATION/"
      "N8N Work Flow/n8n All Workflow/motionkit")
# ကတ် တစ်ခုချင်း ဆောက်ရာမှာ ခေါ်သော module များ
PER_CARD = ("infogfx.py", "kinetic.py", "thm.py", "render.py", "render2.py")


def _src(fn):
    return io.open(os.path.join(MK, fn), encoding="utf-8").read()


@unittest.skipUnless(os.path.isdir(MK), "motionkit မရှိ")
class NoSystemExit(unittest.TestCase):
    def test_per_card_modules_have_none(self):
        bad = []
        for fn in PER_CARD:
            s = _src(fn)
            if "raise SystemExit" in s:
                bad.append(fn)
        self.assertEqual(bad, [], "ကတ် လမ်းမှာ SystemExit ကျန်နေသည်: %s" % (bad,))

    def test_mkerror_defined_and_catchable(self):
        sys.path.insert(0, MK)
        for m in ("infogfx", "kinetic", "thm", "render", "render2"):
            mod = __import__(m)
            E = getattr(mod, "MKError", None)
            self.assertIsNotNone(E, m)
            self.assertTrue(issubclass(E, Exception), m)
            self.assertFalse(issubclass(E, SystemExit), m)

    def test_except_exception_catches_it(self):
        sys.path.insert(0, MK)
        import infogfx
        try:
            raise infogfx.MKError("စမ်း")
        except Exception:
            pass
        else:
            self.fail("except Exception က မဖမ်းမိ")

    def test_cli_modules_may_keep_it(self):
        # ⚠️ CLI entry point (mkapp · jobs · compose) မှာ SystemExit က မှန်သည် —
        #    အဲဒါတွေကို မထိရ。 ဒီ test က အဲဒီ ကွဲပြားမှုကို မှတ်တမ်း တင်သည်。
        keep = [f for f in ("mkapp.py", "jobs.py", "compose.py")
                if os.path.exists(os.path.join(MK, f))]
        self.assertTrue(keep)
        self.assertTrue(any("raise SystemExit" in _src(f) for f in keep),
                        "CLI မှာလည် ဖယ်မိသလား")


if __name__ == "__main__":
    unittest.main(verbosity=2)
