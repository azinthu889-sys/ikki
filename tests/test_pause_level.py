# -*- coding: utf-8 -*-
"""「ဘယ်လောက် ဖြုတ်မလဲ」 — `cut` နဲ့ သီးခြား ဝင်ရိုး

⚠️⚠️ ၂၀၂၆-၁၀-၀၃ Zin: 「ဖြုတ်တာ များလွန်း/နည်းလွန်း」。 တိုင်းကြည့်တော့
   **`CUTS` က ဖြုတ်မှု ပမာဏကို မထိန်းချုပ်ပါ** (ဖိုင် ၁၇၈.၇s · တိတ် ၆၁%):

     အဆင့်       ဖြုတ်   ဖြတ်ချက်   /မိနစ်
     ညင်သာ       ၃၉%      ၁၇       ၉.၄
     ပုံမှန်      ၄၂%      ၂၃      ၁၃.၃
     တင်းတင်း    ၄၄%      ၃၂      ၁၉.၁
     ပြတ်သား     ၄၆%      ၄၃      ၂၆.၇

   ဖြုတ်မှုက **၇ မှတ်** ပဲ ကွာပြီး ဖြတ်ချက်က **၂.၅ ဆ** ကွာသည် ⇒ `CUTS` က
   「ဘယ်လောက် ဖြတ်ဖြတ်ပြတ်ပြတ် ဖြစ်မလဲ」 ကို ထိန်းတာ ဖြစ်ပြီး
   「ဘယ်လောက် ဖြုတ်မလဲ」 ကို **မထိန်း**。 သုံးစွဲသူ 「များလွန်းတယ်」
   ဆိုလျှင် ဖြေပေးမယ့် ခလုတ် မရှိခဲ့。

   `pause_ratio`/`pause_max` က မှန်ကန်သော ဝင်ရိုး — keep/min_sil မပြောင်းဘဲ
   ဖြုတ်မှု ၄၅→၁၈% ပြောင်းပြီး **ဖြတ်ချက် ၂၃ အမြဲ**。

⚠️ ဖိုင် ၁ ခုကနေ တိုင်းထားသည် (measure-distribution-rule)。 ပမာဏက
   မူရင်းရဲ့ တိတ်ဆိတ်မှု အချိုးပေါ် မူတည်၍ ဖိုင်တိုင်း မတူ —
   **အစဉ်လိုက်** ကတော့ တူမည် ⇒ အောက်က စစ်ချက်က အစဉ်ကိုသာ စစ်သည်。
"""
import math
import os
import struct
import sys
import tempfile
import unittest
import wave

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "core"))
SR = 16000


def _mk(plan, path):
    import random
    random.seed(9)
    fr = []
    ph = 0.0
    for d, amp in plan:
        for _ in range(int(d * SR)):
            if amp <= 0:
                fr.append(random.gauss(0, 0.0003))
            else:
                ph += 2 * math.pi * 130.0 / SR
                fr.append(amp * (math.sin(ph) + 0.4 * math.sin(3 * ph)) / 1.4)
    w = wave.open(path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32000))
                           for v in fr))
    w.close()
    return sum(d for d, _ in plan)


class Table(unittest.TestCase):
    def test_the_levels_are_ordered(self):
        """⚠️ ratio တက် ⇒ ဖြုတ်မှု ကျ。 ဇယားက အစဉ်လိုက် ဖြစ်ရမည်"""
        import recipes as RC
        order = ["max", "more", "normal", "less", "keep"]
        self.assertEqual(list(RC.PAUSES), order)
        prev = -1.0
        for k in order:
            r, _m = RC.PAUSES[k]
            self.assertGreater(r, prev, k)
            prev = r

    def test_every_level_has_a_label(self):
        import recipes as RC
        for k in RC.PAUSES:
            self.assertIn(k, RC.PAUSE_LABEL, k)
            my, en = RC.PAUSE_LABEL[k]
            self.assertTrue(my.strip() and en.strip(), k)

    def test_the_default_is_unchanged(self):
        """⚠️ ပုံသေ ပြောင်းလျှင် ရှိပြီးသား သုံးစွဲသူတိုင်းရဲ့ ရလဒ် ပြောင်းမည်"""
        import recipes as RC
        self.assertEqual(RC.PAUSES["more"], (0.10, 1.50))
        r = RC.apply("short-916", {})
        self.assertAlmostEqual(r["pause_ratio"], 0.10)
        self.assertAlmostEqual(r["pause_max"], 1.50)
        self.assertEqual(RC.pause_name(r), "more")


class Plumbing(unittest.TestCase):
    def test_the_name_reaches_the_recipe(self):
        import recipes as RC
        for k, (a, b) in RC.PAUSES.items():
            r = RC.apply("short-916", {"pause": k})
            self.assertAlmostEqual(r["pause_ratio"], a, msg=k)
            self.assertAlmostEqual(r["pause_max"], b, msg=k)

    def test_both_routes_agree(self):
        """⚠️⚠️ ဘောင်က ဇယားကို **လွှမ်းရမည်**。 မလွှမ်းလျှင် `keep`
           (၀.၅၀/၆.၀) က ဇယားလမ်းက ရပြီး ကိန်းသေလမ်းက ချခံရကာ
           လမ်း ၂ ခု တိတ်တဆိတ် ကွဲမည်。
        """
        import recipes as RC
        for k, (a, b) in RC.PAUSES.items():
            t = RC.apply("short-916", {"pause": k})
            d = RC.apply("short-916", {"pause_ratio": a, "pause_max": b})
            self.assertAlmostEqual(t["pause_ratio"], d["pause_ratio"], msg=k)
            self.assertAlmostEqual(t["pause_max"], d["pause_max"], msg=k)

    def test_an_unknown_name_is_ignored(self):
        import recipes as RC
        r = RC.apply("short-916", {"pause": "zzz"})
        self.assertAlmostEqual(r["pause_ratio"], 0.10)

    def test_it_shows_in_the_listing(self):
        """⚠️ `listing()` မှာ မပါလျှင် UI မှာ ဘယ်တော့မှ မပေါ်"""
        import recipes as RC
        rows = RC.listing()
        self.assertTrue(rows)
        for row in rows:
            self.assertIn("pause", row, row.get("id"))

    def test_the_worker_passes_it_to_the_cut_engine(self):
        import io
        src = io.open(os.path.join(HERE, "..", "worker", "run.py"),
                      encoding="utf-8").read()
        self.assertIn('pause_ratio=rc.get("pause_ratio")', src)
        self.assertIn('pause_max=rc.get("pause_max")', src)


class Effect(unittest.TestCase):
    """တကယ် သက်ရောက်မှု — **ဖြတ်ချက် အရေအတွက် မပြောင်းဘဲ** ဖြုတ်မှု ပြောင်း"""

    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.w = os.path.join(cls.d, "p.wav")
        # စကား ၂s နဲ့ တိတ် ၃s ကို ၆ ကြိမ် — အနားယူချိန် ရှည်သော ဖိုင်
        plan = []
        for _ in range(6):
            plan += [(2.0, 0.30), (3.0, 0.0)]
        plan += [(2.0, 0.30)]
        cls.dur = _mk(plan, cls.w)

    def _run(self, pr, pm):
        import cut as CUT
        import measure as M
        meas = M.speech(self.w)
        spans, cuts, st = CUT.plan(self.w, keep_pause=0.40, min_sil=0.75,
                                   edge=0.06, meas=meas,
                                   pause_ratio=pr, pause_max=pm)
        kept = sum(b - a for a, b in spans)
        return kept, int(st.get("cuts") or 0)

    def test_more_kept_pause_removes_less(self):
        """⚠️ **အဓိက** — ဒါက သုံးစွဲသူရဲ့ 「များလွန်းတယ်」 ကို ဖြေပေးသည်"""
        import recipes as RC
        prev = None
        for k in ("max", "more", "normal", "less", "keep"):
            a, b = RC.PAUSES[k]
            kept, _c = self._run(a, b)
            if prev is not None:
                self.assertGreaterEqual(kept, prev - 1e-6,
                                        f"{k}: {kept:.2f} < {prev:.2f}")
            prev = kept

    def test_the_cut_count_does_not_change(self):
        """⚠️⚠️ ဒါက ဒီ dial ရဲ့ **အဓိက ဂုဏ်သတ္တိ** — ဖြုတ်မှု ပြောင်းပေမယ့်
           ဖြတ်ဖြတ်ပြတ်ပြတ်မှု မပြောင်း。 `cut` dial က ပြောင်းသည်。
        """
        import recipes as RC
        counts = set()
        for k in ("max", "more", "normal", "less", "keep"):
            a, b = RC.PAUSES[k]
            _kept, c = self._run(a, b)
            counts.add(c)
        self.assertEqual(len(counts), 1, counts)

    def test_the_range_is_wide_enough_to_matter(self):
        """⚠️ ၂ မှတ် ပဲ ကွာလျှင် ခလုတ် ထည့်တာ အဓိပ္ပာယ် မရှိ"""
        import recipes as RC
        lo, _c1 = self._run(*RC.PAUSES["max"])
        hi, _c2 = self._run(*RC.PAUSES["keep"])
        self.assertGreater((hi - lo) / self.dur, 0.08, (lo, hi, self.dur))


if __name__ == "__main__":
    unittest.main(verbosity=2)
