# -*- coding: utf-8 -*-
"""ကတ်ရဲ့ စာသား — `head` လို key ကို လွတ်မသွားရ

⚠️ ၂၀၂၆-၀၉-၂၉ PROOF render — log မှာ
     ▸ ကတ် @   0.7s  headtop.ht_concept_card  ✓  「」
     ▸ ကတ် @  24.5s  thm.cut_pct              ✓  「」
   ၂ ခုလုံး စာသား ဗလာ ပြခဲ့သည်。 `ht_concept_card` ရဲ့ **လိုအပ်သော**
   param က `head` ဖြစ်ပြီး key စာရင်းထဲ q · text · title · items ၄ ခုသာ
   ပါခဲ့သည် ⇒ log လည် မှား、`REPORT["cards"]` လည် မှား、template
   ဆောက်မရလျှင် စာ မပါသော စာရွက် ထွက်နိုင်သည်。
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import run as W  # noqa: E402


class HeadText(unittest.TestCase):
    def test_head_key(self):
        # ⚠️ တကယ် ဖြစ်ခဲ့သော ကိစ္စ — `headtop.ht_concept_card`
        self.assertEqual(W.head_text({"head": "ကျောင်း ရွေးနည်း"}),
                         "ကျောင်း ရွေးနည်း")

    def test_named_order(self):
        # q က အရင် (planner ရဲ့ ပုံသေ)
        self.assertEqual(W.head_text({"q": "အေ", "head": "ဘီ"}), "အေ")

    def test_items_first(self):
        self.assertEqual(W.head_text({"items": ["ပထမ", "ဒုတိယ"]}), "ပထမ")

    def test_pair_rows(self):
        # rows = [(အညွှန်း, ကိန်း)] ⇒ အညွှန်း ကို ယူရမည်
        self.assertEqual(W.head_text({"lines": [["ကျောင်းလခ", 240]]}),
                         "ကျောင်းလခ")

    def test_fallback_any_text(self):
        # နာမည် မသိသော key ဖြစ်လည် စာသား ဆိုလျှင် ယူသည်
        self.assertEqual(W.head_text({"kicker": "N5 အောင်"}), "N5 အောင်")

    def test_skips_colour(self):
        # ⚠️ အရောင် · ပုံ လမ်း တွေကို စာသား အဖြစ် မယူရ
        self.assertEqual(W.head_text({"bg": "/tmp/a.png", "fill": "#FFCC00"}), "")
        self.assertEqual(W.head_text({"accent": "#FFCC00"}), "")
        self.assertEqual(W.head_text({"src": "data:image/png;base64,AAA"}), "")

    def test_empty(self):
        self.assertEqual(W.head_text({}), "")
        self.assertEqual(W.head_text(None), "")

    def test_blank_string_not_used(self):
        self.assertEqual(W.head_text({"title": "   ", "head": "ခေါင်းစဉ်"}),
                         "ခေါင်းစဉ်")

    def test_number_prop_not_text(self):
        # value=240 ဆိုလျှင် စာသား မဟုတ် ⇒ ဗလာ ပြန်ရမည်
        self.assertEqual(W.head_text({"value": 240}), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
