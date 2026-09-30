# -*- coding: utf-8 -*-
"""explainer insert က overlay ဂရပ်ဖစ်တွေကို **မဖျက်ဆီးရ**

⚠️⚠️ ၂၀၂၆-၁၀-၀၁ တိုင်းချက် — `INSERT_KINDS = ("insert_label", "insert_flow")`
   ၂ ခုလုံး **၁၀၇၉px** (1080 ဘောင်) ဖြစ်သည် ⇒ worker က
     ⊘ နေရာ မတည့်: insert_label @ 2.2s (ကတ်အမြင့် 1079 · မျက်နှာဇုန် 151–756)
   နဲ့ **အမြဲ ပယ်**သည်。 `apply_inserts` က ရှိပြီးသား ဂရပ်ဖစ်ရဲ့ `kind` ကို
   **အစားထိုး**သဖြင့် (၄၀% အထိ) insert မရတာ တစ်ခုတည်း မဟုတ်ဘဲ
   **အလုပ်လုပ်နေသော overlay တွေပါ ပျောက်**သည်:
     knowledge · ရွေး ၁၀ → တပ်ရ **၄** · gfx_share 0.134 (ပစ်မှတ် 0.17)
   recipe ၃ ခု (knowledge · podcast · ref-talk) က `insert_per_min=2.5` ထားသည် —
   ၃ ခုလုံး ဤအတိုင်း。

⚠️ ဒါက ပြည့်စုံသော ပြင်ချက် မဟုတ် — insert က တကယ် ဘောင်အပြည့် ဖြစ်သင့်၍
   **slide/cutaway track** ကနေ ထွက်ရမည်。 ယခု လုပ်တာက ဖျက်ဆီးမှု ရပ်တာသာ。
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
import dress as DR      # noqa: E402
import recipes as RC    # noqa: E402


def _gfx(n):
    return [dict(at=float(i) * 3, kind="titles.title_card", args=("a",))
            for i in range(n)]


class FullFrameDetect(unittest.TestCase):
    def test_both_insert_kinds_are_full_frame(self):
        # ⚠️ ဒါ မှန်မနေလျှင် အောက်က test တွေ ဘာမှ မစစ်ပါ
        for k in DR.INSERT_KINDS:
            self.assertTrue(DR._insert_full_frame(k), k)

    def test_overlay_template_is_not(self):
        self.assertFalse(DR._insert_full_frame("title_card"))

    def test_cached(self):
        a = DR._insert_full_frame("insert_label")
        self.assertEqual(a, DR._insert_full_frame("insert_label"))


class NoDestruction(unittest.TestCase):
    def test_graphics_all_survive(self):
        g = _gfx(10)
        out = DR.apply_inserts(g, dict(insert_per_min=2.5, _seed="s"), 94.0)
        self.assertEqual(len(out), 10)
        self.assertEqual(sum(1 for x in out if x.get("kind") in DR.INSERT_KINDS), 0)

    def test_kinds_untouched(self):
        g = _gfx(10)
        before = [x["kind"] for x in g]
        out = DR.apply_inserts(g, dict(insert_per_min=2.5, _seed="s"), 94.0)
        self.assertEqual([x["kind"] for x in out], before)

    def test_args_untouched(self):
        # ⚠️ အရင်က `g["args"] = None` လုပ်ခဲ့သည် ⇒ ပြန်တွက်ရမည်
        g = _gfx(4)
        out = DR.apply_inserts(g, dict(insert_per_min=2.5, _seed="s"), 94.0)
        self.assertTrue(all(x.get("args") for x in out))

    def test_says_why(self):
        msgs = []
        DR.apply_inserts(_gfx(6), dict(insert_per_min=2.5, _seed="s"), 94.0,
                         log=lambda m: msgs.append(m))
        self.assertTrue(msgs, "တိတ်တဆိတ် ကျော်သွားသည်")
        joined = " ".join(msgs)
        self.assertIn("ဘောင်အပြည့်", joined)
        self.assertIn("slide track", joined)

    def test_no_insert_rate_means_no_change(self):
        g = _gfx(5)
        out = DR.apply_inserts(g, dict(_seed="s"), 94.0)
        self.assertEqual([x["kind"] for x in out], [x["kind"] for x in g])


class RecipesAffected(unittest.TestCase):
    def test_three_recipes_use_inserts(self):
        got = sorted(n for n in RC.R if RC.get(n).get("insert_per_min"))
        self.assertEqual(got, ["knowledge", "podcast", "ref-talk"], got)


if __name__ == "__main__":
    unittest.main(verbosity=2)
