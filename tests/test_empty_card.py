# -*- coding: utf-8 -*-
"""**စာ မပါသော ကတ်** ကို မဆောက်ရ

⚠️⚠️ ၂၀၂၆-၁၀-၀၂ render s6 · ၆၆.၇s · `callouts.underline_call` —
   ဘောင်အပြည့် ဖြတ်ပြောင်း ချပြီး **မျဉ်းတစ်ကြောင်းပဲ** ဆွဲခဲ့သည်:
   အဝါမင် ၂၉၀၅px · x ၁၈၂–၅၄၅ · y **၈၀၄–၈၁၁ (၇px အမြင့်)**。
   log က 「」 (ဗလာ) ပြပါလျက် ကတ်က ✓ ဖြစ်ခဲ့ — ငြင်းမယ့် စစ်ချက် မရှိ。

⚠️ ၂၀၂၆-၀၉-၂၉ မှာ ဒီလက္ခဏာကို `_HEAD_K` ချဲ့ပြီး ပြင်ခဲ့သည်。 အဲဒါက
   **ရှာတွေ့အောင်** လုပ်တာသာ — စာ တကယ် မရှိတဲ့အခါ မကာကွယ်。 plan က
   Gemini ဆီက လာသဖြင့် props ဗလာ ဖြစ်နိုင်ဆဲ ⇒ **သုံးရာမှာ** စစ်ရသည်。

⚠️ ပုံသေ 「ဗလာ ဆို ငြင်း」 **မလုပ်ရ** — `infogfx.*` ၁၁၃ ခုက စာရင်း/ဂဏန်း
   နဲ့ အလုပ်လုပ်ပြီး စာသား param မရှိ。 ⇒ catalog နဲ့ ခွဲရသည်。
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "core"))


def _wk():
    return io.open(os.path.join(HERE, "..", "worker", "run.py"),
                   encoding="utf-8").read()


class Guard(unittest.TestCase):
    def setUp(self):
        self.s = _wk()

    def test_the_guard_exists_and_skips(self):
        i = self.s.find("if not str(_head or \"\").strip() and tmpl_wants_text(")
        self.assertGreater(i, 0, "စစ်ချက် မရှိ")
        w = self.s[i:i + 500]
        self.assertIn("continue", w)
        self.assertIn("**စာ မပါ**", w)

    def test_it_runs_before_the_template_is_built(self):
        """⚠️ ဆောက်ပြီးမှ ပယ်လျှင် render မိနစ် အလဟဿ · ရလဒ်လည်း တူ"""
        g = self.s.find("if not str(_head or \"\").strip() and tmpl_wants_text(")
        b = self.s.find("_mv = _DR.slide_clip(")
        self.assertGreater(g, 0)
        self.assertGreater(b, 0)
        self.assertLess(g, b)

    def test_it_is_recorded_in_the_report(self):
        """⚠️ တိတ်တဆိတ် ပယ်လျှင် 「ဂရပ်ဖစ် နည်းတယ်」 ကို ရှင်းလို့ မရ"""
        self.assertIn('REPORT.setdefault("cards_empty", [])', self.s)

    def test_a_catalog_failure_allows_the_card(self):
        """⚠️ စစ်လို့မရလို့ ပယ်လျှင် ဂရပ်ဖစ် **အားလုံး** ပျောက်မည်
           (manifest ids ထောင်ချောက်နဲ့ အတူတူ)"""
        i = self.s.find("def tmpl_wants_text(")
        w = self.s[i:self.s.find("\ndef ", i + 10)]
        self.assertIn("except Exception:", w)
        j = w.find("except Exception:")
        self.assertIn("v = False", w[j:j + 300])


class Catalog(unittest.TestCase):
    """တကယ့် catalog နဲ့ — စစ်ချက်က ဘယ်ဟာကို မိပြီး ဘယ်ဟာကို လွှတ်လဲ"""

    @classmethod
    def setUpClass(cls):
        import gfxcat as GC
        cls.cat = {e["id"]: e for e in GC.catalog()}

    def _wants(self, cid):
        e = self.cat.get(cid)
        return bool(e) and any(p.get("type") == "text"
                               for p in (e.get("params") or []))

    def test_the_offender_is_caught(self):
        self.assertTrue(self._wants("callouts.underline_call"))

    def test_list_only_templates_are_not_caught(self):
        """⚠️ `infogfx.*` က စာရင်း/ဂဏန်းနဲ့ အလုပ်လုပ်သည် — ပယ်လို့ မရ"""
        for cid in ("infogfx.bars", "infogfx.donut", "infogfx.steps"):
            self.assertIn(cid, self.cat, cid)
            self.assertFalse(self._wants(cid), cid)

    def test_the_guard_is_not_a_blanket_refusal(self):
        """⚠️ catalog ရဲ့ **အများစု**ကို မိလျှင် ဂရပ်ဖစ် မကျန်တော့"""
        n = sum(1 for cid in self.cat if self._wants(cid))
        self.assertEqual(len(self.cat), 623)
        # တိုင်းချက် ၂၀၂၆-၁၀-၀၂: ၅၀၄/၆၁၇ (၈၂%) · ၂၀၂၆-၁၀-၀၅ modern.mt_* ၆ ခု (စာသား param) ⇒ ၅၁၀/၆၂၃
        self.assertEqual(n, 510)
        self.assertEqual(len(self.cat) - n, 113)


class HeadText(unittest.TestCase):
    """`head_text` ကိုယ်တိုင် — ဘယ်အခါ ဗလာ ပြန်လဲ"""

    def setUp(self):
        import importlib.util
        src = _wk()
        i = src.find("_HEAD_K = (")
        j = src.find("\n\n\n", src.find("def head_text("))
        ns = {}
        exec(src[i:j], ns)
        self.f = ns["head_text"]

    def test_empty_props_give_empty(self):
        self.assertEqual(self.f({}), "")
        self.assertEqual(self.f(None), "")

    def test_only_colours_and_sizes_give_empty(self):
        """⚠️ ဒါက s6 ၆၆.၇s ရဲ့ အခြေအနေ အတိအကျ"""
        self.assertEqual(self.f({"col": "#FFD400", "size": 72, "px": 10}), "")

    def test_whitespace_is_empty(self):
        self.assertEqual(self.f({"text": "   "}), "")

    def test_a_list_label_counts_as_text(self):
        self.assertEqual(self.f({"items": ["ပထမ", "ဒုတိယ"]}), "ပထမ")

    def test_a_hex_colour_is_not_text(self):
        self.assertEqual(self.f({"stroke": "#112233"}), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
