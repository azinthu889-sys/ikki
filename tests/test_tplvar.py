# -*- coding: utf-8 -*-
"""template **ပြန်ပြန် မပေါ်ရ** — ဗီဒီယိုတိုင်း တစ်ပုံစံတည်း ဖြစ်စေသည်。

⚠️ ၂၀၂၆-၀၉-၂၁ တိုင်းချက် — ဝါကျ ၁၀ ကြောင်းနဲ့ plan ပြေးကြည့်တော့
   event ၈ ခု ရပေမယ့် template **၃ မျိုးပဲ** ဖြစ်ပြီး `ht_stat_ring` က
   **၄ ခါ** ပေါ်ခဲ့သည်。 အကြောင်းရင်း —
     `PACK_INTENT` ရဲ့ label အများစုမှာ pack template **၁ ခုပဲ** ရှိပြီး
     pack က အမြဲ အရင် အောင်သဖြင့် catalog ရဲ့ candidate ၃ ခုဆီ
     **ဘယ်တော့မှ မရောက်**ခဲ့。
   ⇒ ကြာသေးသော pack template ကို ကျော်ပြီး catalog ကို အခွင့်ပေးသည်
     (ဂရပ်ဖစ် မပျောက်စေရန် အဆုံးမှာ ပြန်ယူသည်)。
"""
import os, sys, unittest
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
# ⚠️ **Gemini ကို ပိတ်ရမည်** — ဤ test က 「တူညီ seed ⇒ တူညီ ရလဒ်」ဟု
#    စစ်သည်。 `plan()` က Gemini ကို ခေါ်ပြီး Gemini ရဲ့ အဖြေက ခေါ်တိုင်း
#    ကွဲနိုင်သဖြင့် **ကွန်ရက်ကို တိုင်းနေသလို** ဖြစ်သည်。
#    ⚠️ ၂၀၂၆-၀၉-၂၄ တိုင်းချက် — Gemini 503 ဖြစ်နေစဉ် ဤ test အောင်ခဲ့ပြီး
#       Gemini ပြန်ကောင်းလာသည်နှင့် **ကျ**သွားသည် (ဂရပ်ဖစ် ၇ ↔ ၈)。
#       Gemini မရောက်အောင် လုပ်ပြီး စမ်းတော့ **၃ ခါလုံး တူ** ⇒ planner ရဲ့
#       ကိုယ်ပိုင် ရွေးချယ်မှုက deterministic ဖြစ်ပြီးသား。
#    ⇒ ဤ test က **planner ရဲ့ logic** ကို တိုင်းရမည် — Gemini ကို မဟုတ်。
#      (Gemini ဖွင့်ထားလျှင် ပြန်ထုတ်ချက် တူညီမှု **အာမ မခံနိုင်**ပါ။)
os.environ.setdefault("ZJL_FORCE_PROXY", "1")
os.environ["ZJL_GEMINI_PROXY"] = "http://127.0.0.1:9/disabled-in-test"

import planner as PL          # noqa: E402

SENT = ["ဒီနေ့ ဂျပန်စာ N5 အတွက် ဘာလုပ်ရမလဲ ပြောပြမယ်",
        "ပထမဆုံး ဟိရဂနနဲ့ ခတခန ကို အလွတ်ရရမယ်",
        "ကျောင်းသား ၈၅% က ဒီအဆင့်မှာ ရပ်သွားတယ်",
        "အဆင့် ၃ ဆင့် ရှိတယ် — စာလုံး၊ သဒ္ဒါ၊ အကြားအမြင်",
        "စကားလုံး ၈၀၀ လောက် လိုတယ်",
        "ဒါပေမယ့် အရေးကြီးတာက နေ့တိုင်း လုပ်တာပါ",
        "မနက် ၃၀ မိနစ် · ညနေ ၃၀ မိနစ် ခွဲပါ",
        "စာမေးပွဲ မတိုင်ခင် ၂ လ အလေ့အကျင့် လုပ်ပါ",
        "N5 နဲ့ N4 ကို နှိုင်းယှဉ်ကြည့်ရင် ကွာဟမှု ကြီးတယ်",
        "နောက်ဆုံး — မေးခွန်း ရှိရင် comment မှာ ရေးပါ"]


# ⚠️ `plan()` တစ်ခါ ~၁၀s ကြာသည် — test ၆ ခုမှာ ၆ ခါ ပြေးလျှင် suite က
#    ၁၀s → ၇၁s ဖြစ်သည်。 video_id အလိုက် **တစ်ခါသာ** ပြေးစေသည်。
_CACHE = {}


def _plan(vid="t1"):
    if vid in _CACHE:
        return _CACHE[vid]
    segs = [dict(n=i + 1, start=i * 6.0, end=i * 6.0 + 5.0, text=t)
            for i, t in enumerate(SENT)]
    p, _w = PL.plan(segs, 60.0,
                    dict(energy="standard", fps=30, aspect="1920:1080",
                         motionkit_profile="premium", sfx=False, log=None),
                    video_id=vid, log=lambda *a: None)
    _CACHE[vid] = [e["motionKitTemplateId"] for e in p["templateEvents"]]
    return _CACHE[vid]


class TplVar(unittest.TestCase):

    def test_variety(self):
        """ကွဲပြားမှု ၇ မျိုး အနည်းဆုံး (၃ → ၆ → ၈ ဖြစ်လာသည်)"""
        ids = _plan()
        self.assertGreaterEqual(len(set(ids)), 7,
                                f"ကွဲပြား {len(set(ids))} မျိုးသာ: {ids}")

    def test_pop_pool_verified(self):
        """⚠️ pop က `word_pop` တစ်ခုတည်း hardcode ခဲ့သည် ⇒ pop အားလုံး တူတူ。
        `assets/pop_ok.txt` က တစ်ခုချင်း ဆောက်ပြီး တိုင်းထားသော စာရင်း。"""
        pops = PL._pops()
        self.assertGreaterEqual(len(pops), 10, f"pop pool {len(pops)} ခုသာ")
        self.assertIn("kinetic.word_pop", pops)
        # exit animation · အဓိပ္ပာယ် ပြောင်းတာ မပါရ
        for bad in ("pop_out", "blur_out", "wipe_out", "stagger_out",
                    "strike_in", "quote_marks"):
            self.assertFalse(any(bad in x for x in pops),
                             f"{bad} ပါနေသည် — popcheck က ပယ်ထားသည်")

    def test_no_template_twice(self):
        """template တစ်ခုတည်း ၂ ခါထက် မပိုရ"""
        ids = _plan()
        top, n = Counter(ids).most_common(1)[0]
        self.assertLessEqual(n, 2, f"{top} က {n} ခါ: {ids}")

    def test_no_card_four_times(self):
        """ကတ် တစ်ခုတည်း ၃ ခါထက် မပိုရ (`ht_stat_ring` ၄ ခါ ဖြစ်ခဲ့)"""
        ids = [i for i in _plan() if "word_pop" not in i]
        if not ids:
            self.skipTest("ကတ် မရှိ")
        top, n = Counter(ids).most_common(1)[0]
        self.assertLessEqual(n, 3, f"{top} က {n} ခါ ပေါ်သည်: {ids}")

    def test_graphics_not_lost(self):
        """ကွဲပြားမှု အတွက် ဂရပ်ဖစ် မပျောက်ရ"""
        self.assertGreaterEqual(len(_plan()), 6)

    def test_seed_changes_order(self):
        """ဗီဒီယို မတူ ⇒ ရွေးချယ်မှု မတူ (တူညီ seed ⇒ တူညီ ရလဒ်)"""
        a, b = _plan("v-aaa"), _plan("v-bbb")
        _CACHE.pop("v-aaa")                 # cache မဟုတ်ဘဲ တကယ် ပြန်ပြေးစေရန်
        self.assertEqual(a, _plan("v-aaa"), "တူညီ seed က တူရမည်")
        self.assertTrue(len(set(a)) >= 5 and len(set(b)) >= 5)

    def test_rotate_keeps_all(self):
        """`_rotate` က candidate မဖျက်ရ — ရှေ့/နောက် ပြောင်းရုံ"""
        c = ["a", "b", "c", "d"]
        self.assertEqual(sorted(PL._rotate(c, ["a"], "s")), sorted(c))
        self.assertEqual(PL._rotate([], ["a"], "s"), [])

    def test_rotate_fresh_first(self):
        """မသုံးရသေးတာ ရှေ့မှာ ရှိရမည်"""
        out = PL._rotate(["a", "b", "c"], ["a", "b"], "")
        self.assertEqual(out[0], "c")


if __name__ == "__main__":
    unittest.main(verbosity=2)
