# -*- coding: utf-8 -*-
"""ဖျက်ချက် အတည်ပြုချက်က **သုံးစွဲသူဆီ ရောက်ရမည်**

⚠️⚠️ Zin ၂၀၂၆-၁၀-၀၃: 「တိကျအောင်လုပ်ပေးဖိ့」。 `cut.verify_drops()` က
   ဖျက်ချက် တစ်ခုချင်းကို စစ်ပြီးသား ဖြစ်သော်လည်း ရလဒ်က **log ထဲမှာပဲ**
   ကျန်ခဲ့သည် — `post_cut` က မပို့ခဲ့ ⇒ Cut Review မှာ သုံးစွဲသူက
   「ငါ ဖျက်ခိုင်းတာ တကယ် ပြီးပြီလား」 ကို ဘယ်တော့မှ မမြင်ရ。

⚠️ **အောင်မြင်မှုကိုပါ ပြရမည်** — အမှား ရှိမှ ပြလျှင် ဘာမှ မပေါ်တာက
   「စစ်ပြီးပြီ · အိုကေ」 လား 「လုံးဝ မစစ်ခဲ့」 လား မခွဲနိုင်
   (ikki-measure-the-real-path)。

⚠️ `cut_note` က UI မှာ ပြပြီးသား (`web/script.html` ရဲ့ `j.cut_note`) ⇒
   **web/ ပြင်စရာ မလို**。
"""
import io
import os
import unittest

HERE = os.path.dirname(__file__)


def _src(*p):
    return io.open(os.path.join(HERE, "..", *p), encoding="utf-8").read()


class WorkerSends(unittest.TestCase):
    def setUp(self):
        self.s = _src("worker", "run.py")

    def test_the_cut_preview_carries_the_verification(self):
        i = self.s.find("post_cut(job[\"id\"], _cpv,")
        self.assertGreater(i, 0)
        w = self.s[i:i + 900]
        for k in ("drops=int(st.get(\"user_cuts\")",
                  "drop_left=st.get(\"drop_left\")",
                  "drop_over=st.get(\"drop_over\")"):
            self.assertIn(k, w, k)

    def test_both_directions_are_stored_before_sending(self):
        a = self.s.find('st["drop_left"] = _left')
        b = self.s.find('st["drop_over"] = _over')
        c = self.s.find('post_cut(job["id"], _cpv,')
        self.assertGreater(a, 0)
        self.assertGreater(b, 0)
        self.assertLess(a, c)
        self.assertLess(b, c)


class ApiNote(unittest.TestCase):
    def setUp(self):
        self.s = _src("api", "main.py")

    def test_the_note_reports_success_too(self):
        """⚠️ အမှား ရှိမှ ပြလျှင် 「စစ်ပြီး အိုကေ」 နဲ့ 「မစစ်ခဲ့」 မခွဲနိုင်"""
        self.assertIn("အတိအကျ ဖြတ်ပြီးပါပြီ", self.s)

    def test_the_note_reports_both_failure_kinds(self):
        self.assertIn("အပြည့် မပျောက်သေး", self.s)
        self.assertIn("ဘေးစကားလုံး ပါသွားနိုင်", self.s)

    def test_nothing_is_claimed_when_there_were_no_deletions(self):
        """⚠️ ဖျက်ချက် မရှိဘဲ 「၀ ခုလုံး ပြီးပြီ」 ပြလျှင် ရုပ်ဆိုးသည်"""
        i = self.s.find('_nd = int(m.get("drops") or 0)')
        self.assertGreater(i, 0)
        w = self.s[i:i + 900]
        self.assertIn("if _nd:", w)

    def test_the_note_is_capped(self):
        """⚠️ `cut_note` က စာကြောင်းတစ်ကြောင်း — ရှည်လွန်းလျှင် ဖတ်မရ"""
        self.assertIn("if note and len(note) > 400:", self.s)

    def test_it_is_written_to_the_job(self):
        i = self.s.find('_nd = int(m.get("drops") or 0)')
        j = self.s.find("cut_n=?,cut_note=?,minutes=0 WHERE id=?")
        self.assertGreater(j, i, "note က UPDATE မတိုင်ခင် ဆောက်ရမည်")


class ReachesTheUser(unittest.TestCase):
    def test_the_page_already_renders_it(self):
        """⚠️ ဒါက 「web/ ပြင်စရာ မလို」 ဆိုတဲ့ ကြေညာချက်ရဲ့ သက်သေ —
           မပြဘဲ ဆိုလျှင် note ရေးတာ အလဟဿ。"""
        w = _src("web", "script.html")
        self.assertIn("j.cut_note", w)


if __name__ == "__main__":
    unittest.main(verbosity=2)
