# -*- coding: utf-8 -*-
"""**အခမဲ့ styled preview** — မိနစ် ၀ · ၅၄၀p · upload တစ်ခုလျှင် ၃ ခါ

⚠️⚠️ ၂၀၂၆-၁၀-၀၂ Zin: 「preview က မိနစ် မစားပါစေနဲ့」·「၃ ခါနဲ့ လုပ်ပေးပါ」。
   clean-cut preview က **ဖြတ်ချက်ပဲ** ပြသဖြင့် သုံးစွဲသူက style ရွေးချယ်ချက်
   ၉ ခုကို မမြင်ဘဲ ခန့်မှန်းပြီး ပိုက်ဆံပေးမှ ရလဒ် မြင်ရသည်。

⚠️ ဤစစ်ချက်တွေက **ကိန်းဘောင် မလျှော့ရ** — ၃ ဆိုတာ Zin ဆုံးဖြတ်ချက်。
"""
import io
import os
import sqlite3
import tempfile
import unittest

HERE = os.path.dirname(__file__)


def _src(*p):
    return io.open(os.path.join(HERE, "..", *p), encoding="utf-8").read()


class ApiWiring(unittest.TestCase):
    def setUp(self):
        self.s = _src("api", "main.py")

    def test_cap_is_three(self):
        self.assertIn("PREVIEW_FREE = 3", self.s)

    def test_cutok_takes_the_flag(self):
        self.assertIn('(b or {}).get("preview")', self.s)
        self.assertIn('_mode = "prev" if _want_prev else "go"', self.s)

    def test_every_render_start_refuses_past_the_cap(self):
        """⚠️⚠️ render စလမ်းက **၂ လမ်း** — `/cutok` (ပထမ ထုတ်) နဲ့
           `/reedit` (ပြင်ပြီး ထုတ်)。 တစ်လမ်း ကျန်လျှင် အဲဒီလမ်းက
           အခမဲ့ render အကန့်အသတ်မရှိ ပေးမိမည်。
        """
        n = 0
        i = self.s.find("_want_prev = bool(")
        while i > 0:
            n += 1
            w = self.s[i:i + 800]
            self.assertRegex(w, r"_p?used >= PREVIEW_FREE")
            self.assertIn("402", w)
            i = self.s.find("_want_prev = bool(", i + 10)
        self.assertEqual(n, 2, f"စလမ်း {n} ခုမှာ ကန့်သတ်ချက် ရှိသည် — ၂ လိုသည်")

    def test_reedit_marks_the_child_job(self):
        """⚠️ `/reedit` က job **အသစ်** ဆောက်သည် ⇒ `mode`/`prev_n` ကို
           INSERT မှာ ထည့်ရမည် (UPDATE လမ်း မရှိ)。
        """
        self.assertIn('_pcol = "\'prev\',1" if _want_prev else "NULL,0"', self.s)
        self.assertIn("acct,created,mode,prev_n)", self.s)

    def test_counter_increments_at_start(self):
        """⚠️ ပြီးမှ တိုးလျှင် ဖြတ်ပြီး ပြန်စတာနဲ့ ကန့်သတ်ချက် ကျော်နိုင်သည်"""
        i = self.s.find('_mode = "prev" if _want_prev else "go"')
        w = self.s[i:i + 600]
        self.assertIn("prev_n=COALESCE(prev_n,0)+?", w)

    def test_counter_is_per_upload_not_per_job(self):
        """⚠️ `/reedit` က job အသစ် ဆောက်သဖြင့် job နဲ့ ရေတွက်လျှင်
           ပြင်တိုင်း ၃ ခါ ပြန်ရမည်"""
        i = self.s.find("def prev_used(")
        self.assertGreater(i, 0)
        w = self.s[i:i + 900]
        self.assertIn("SUM(prev_n)", w)
        self.assertIn("WHERE upload_id=? AND acct=?", w)
        # ⚠️ `mode='prev'` ရေတွက်နည်းက job အတူတူ ပြန်ပြန် queue လုပ်ရာ
        #    ၁ မှာ တင်နေမည် ⇒ မသုံးရ
        self.assertNotIn("COUNT(*)", w)

    def test_minutes_are_zero_for_a_preview(self):
        i = self.s.find("_jm = (db.one(")
        self.assertGreater(i, 0)
        w = self.s[i:i + 600]
        self.assertIn('_chg = 0.0 if (_jm or "") == "prev"', w)
        self.assertIn("UPDATE jobs SET minutes=0", w)

    def test_job_json_exposes_the_allowance(self):
        """⚠️ မပါလျှင် သုံးစွဲသူက ခလုပ် နှိပ်ပြီးမှ ၄၀၂ နဲ့ သိရမည်"""
        self.assertIn('j["prev_free"] = PREVIEW_FREE', self.s)
        self.assertIn('j["prev_used"] = prev_used(', self.s)

    def test_a_finished_preview_can_be_previewed_again(self):
        """⚠️ `cut_review` ပဲ လက်ခံလျှင် preview တစ်ခါပြီးတာနဲ့ ပိတ်မိမည်"""
        i = self.s.find("_was_prev = ")
        self.assertGreater(i, 0)
        w = self.s[i:i + 400]
        self.assertIn('j.get("status") == "done" and _was_prev', w)

    def test_migration_adds_the_column(self):
        d = _src("api", "db.py")
        self.assertIn('"prev_n"', d)


class WorkerWiring(unittest.TestCase):
    def setUp(self):
        self.s = _src("worker", "run.py")

    def _fn(self):
        i = self.s.find("def prev_shrink(")
        self.assertGreater(i, 0, "prev_shrink မရှိ")
        return self.s[i:self.s.find("\ndef ", i + 10)]

    def test_renders_at_540p_for_a_preview(self):
        w = self._fn()
        self.assertIn('(job.get("mode") or "") != "prev"', w)
        self.assertIn("h=540", w)
        self.assertIn("scale=-2:{h}", w)

    def test_audio_is_not_re_encoded(self):
        """⚠️ mastering ပြီးသား LUFS/TP ကို ထိစေမည် (ikki-mastering-converge)"""
        self.assertIn('"-c:a", "copy"', self._fn())

    def test_layout_is_not_touched(self):
        """⚠️⚠️ **အရေးကြီးဆုံး** — theme W/H ပြောင်းလျှင် ဂရပ်ဖစ် နေရာချချက်နဲ့
           စာတန်း အရွယ် ပြောင်းသွားပြီး preview က တကယ်ထွက်မည့် ဗီဒီယိုကို
           မဟုတ်တော့ ⇒ **နောက်ဆုံး ဖိုင်ကိုသာ** ချုံ့ရမည်。
        """
        # ချုံ့ချက်က render ပြီးမှ · `post_thumb` မတိုင်ခင်
        i = self.s.find("out = prev_shrink(job, out, log=lambda")
        self.assertGreater(i, self.s.find("m, mo, st, ncap = render("))
        self.assertLess(i, self.s.find(
            "post_thumb(jid, out, log=lambda x: print(x, flush=True))"))

    def test_both_render_paths_shrink(self):
        """⚠️⚠️ လမ်းတစ်ခု ကျန်လျှင် အဲဒီလမ်းက အခမဲ့ **အရွယ်အပြည့်**
           render ပေးမိမည် — API က `mode='prev'` ကို မိနစ် ၀ ကောက်သဖြင့်。
           (ပထမ ရေးချက်မှာ cinematic လမ်း ကျန်ခဲ့ — စစ်ချက်က ဖမ်းမိသည်)
        """
        # ⚠️ `def prev_shrink(job, out…` ကိုပါ ရေမိမည် ⇒ ခေါ်ချက်ပဲ ရေရမည်
        n = self.s.count("out = prev_shrink(job, out")
        self.assertEqual(n, 2, f"ခေါ်ချက် {n} ခု — render လမ်း ၂ ခုလုံး လိုသည်")
        # `post_thumb` ခေါ်ချက် တစ်ခုချင်းရဲ့ ရှေ့မှာ ရှိရမည်
        for k in ("post_thumb(jid, out, log=lambda x: print(x, flush=True))",
                  "post_thumb(jid, out, log=log)"):
            i = self.s.find(k)
            self.assertGreater(i, 0, k)
            self.assertIn("prev_shrink", self.s[max(0, i - 200):i])

    def test_a_failed_downscale_does_not_fail_the_job(self):
        w = self._fn()
        self.assertIn("except Exception as e", w)
        self.assertIn("အရွယ်အတိုင်း ပြသမည်", w)
        self.assertIn("return out", w)

    def test_uses_the_error_reporting_helper(self):
        """⚠️ `subprocess.run(check=True)` က ffmpeg အမှားစာသား မပြ"""
        w = self._fn()
        self.assertIn('ff(["ffmpeg"', w)
        self.assertNotIn('run(["ffmpeg", "-y"', w)


class Counting(unittest.TestCase):
    """`prev_used` ရဲ့ သတ်မှတ်ချက်ကို **တကယ့် sqlite** နဲ့ စစ်သည်"""

    def _db(self):
        fd, p = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        c = sqlite3.connect(p)
        c.execute("CREATE TABLE jobs(id TEXT, upload_id TEXT, acct TEXT, "
                  "prev_n INTEGER)")
        return c, p

    def _used(self, c, up, acct):
        r = c.execute("SELECT COALESCE(SUM(prev_n),0) FROM jobs "
                      "WHERE upload_id=? AND acct=?", (up, acct)).fetchone()
        return int(r[0] or 0)

    def test_sums_across_the_reedit_chain(self):
        c, p = self._db()
        try:
            c.execute("INSERT INTO jobs VALUES('j1','u1','a1',2)")
            c.execute("INSERT INTO jobs VALUES('j2','u1','a1',1)")   # re-edit
            self.assertEqual(self._used(c, "u1", "a1"), 3)
        finally:
            c.close(); os.unlink(p)

    def test_null_counts_as_zero(self):
        c, p = self._db()
        try:
            c.execute("INSERT INTO jobs VALUES('j1','u1','a1',NULL)")
            self.assertEqual(self._used(c, "u1", "a1"), 0)
        finally:
            c.close(); os.unlink(p)

    def test_another_upload_does_not_count(self):
        c, p = self._db()
        try:
            c.execute("INSERT INTO jobs VALUES('j1','u1','a1',3)")
            c.execute("INSERT INTO jobs VALUES('j2','u2','a1',0)")
            self.assertEqual(self._used(c, "u2", "a1"), 0)
        finally:
            c.close(); os.unlink(p)

    def test_another_account_does_not_count(self):
        c, p = self._db()
        try:
            c.execute("INSERT INTO jobs VALUES('j1','u1','a1',3)")
            self.assertEqual(self._used(c, "u1", "a2"), 0)
        finally:
            c.close(); os.unlink(p)


if __name__ == "__main__":
    unittest.main(verbosity=2)
