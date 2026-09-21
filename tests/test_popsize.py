# -*- coding: utf-8 -*-
"""pop ရဲ့ size ကို **တိုင်းထားသော ink ကနေ** ပြန်တွက်ခြင်း。

⚠️ ကိန်းသေ ဖော်မြူလာ (`size = h × 1.20 × H`) က မမီနိုင်ပါ —
   ၂၀၂၆-၀၉-၂၁ တိုင်းချက် (size ၁၃၁ · H ၁၀၈၀ · ပစ်မှတ် ၁၀.၁%H) —
     「အရေးကြီး」၁၆.၉%  「ဂျပန်」၁၆.၈%  「မနက်」၁၅.၉%
     「ကမ္ဘာ」၁၁.၅%     「Japan」၁၂.၅%
   စကားလုံး ပုံစံပေါ် မူတည်ပြီး **၁၁.၅–၁၆.၉%** ကွာသည် (ဗျည်းတွဲ/အထက်သရ)。
⚠️ ink က size နဲ့ **မျဉ်းဖြောင့်** ⇒ တစ်ခါ တိုင်းလျှင် တိကျစွာ တွက်လို့ရသည်。
   တကယ် ဆောက်ပြီး စမ်းချက် — ၅ မျိုးလုံး ၁၀.၀–၁၀.၁% ရသည်。
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "worker"))
sys.path.insert(0, os.path.join(ROOT, "core"))
import run as W          # noqa: E402

H, WANT = 1080.0, 0.101
# (စကားလုံး, size ၁၃၁ မှာ တိုင်းရသော %H) — တကယ် ဆောက်ပြီး တိုင်းထားသည်
MEASURED = [("အရေးကြီး", 0.169), ("ဂျပန်", 0.168), ("မနက်", 0.159),
            ("ကမ္ဘာ", 0.115), ("Japan", 0.125)]


class PopSize(unittest.TestCase):

    def test_corrects_every_word_shape(self):
        """ဂိတ် ကျော်တာတွေကို ပြန်တွက်ပြီး ပစ်မှတ်ကို ±၅% အတွင်း မီရမည်

        ⚠️ `ကမ္ဘာ` ၁၁.၅% က ပစ်မှတ်နဲ့ ၁၃.၉% ပဲ ကွာသဖြင့် ဂိတ် (၁၅%)
           **အတွင်း** ⇒ ပြန်မဆောက်ပါ (render တစ်ခု သက်သာ · reference
           ဘောင် ၈–၁၆%H အတွင်းလည် ရှိသည်)。
        """
        for w, got in MEASURED:
            s1, redo = W._pop_size(131, got, WANT, H)
            off = abs(got - WANT) / WANT
            self.assertEqual(redo, off > 0.15,
                             f"{w} — လွဲချက် {off*100:.0f}% · redo={redo}")
            if not redo:
                continue
            # မျဉ်းဖြောင့် k = got/131 ⇒ size s1 မှာ ink = k·s1
            pred = (got / 131.0) * s1
            self.assertLess(abs(pred - WANT) / WANT, 0.05,
                            f"{w} — size {s1} မှာ {pred*100:.1f}%H")

    def test_within_reference_band(self):
        """ပြင်ပြီးနောက် ink က reference ဘောင် ၈–၁၆%H အတွင်း ရှိရမည်"""
        for w, got in MEASURED:
            s1, redo = W._pop_size(131, got, WANT, H)
            h = (got / 131.0) * s1
            self.assertTrue(0.08 <= h <= 0.16,
                            f"{w} — {h*100:.1f}%H (size {s1})")

    def test_no_rebuild_when_close(self):
        """လွဲချက် ၁၅% အတွင်းဆို **မပြောင်းရ** — ပြန်ဆောက်တာ အလကား"""
        for got in (0.101, 0.105, 0.095, 0.115, 0.088):
            s1, redo = W._pop_size(131, got, WANT, H)
            self.assertFalse(redo, f"{got*100:.1f}% — ပြောင်းသင့် မဟုတ်")
            self.assertEqual(s1, 131)

    def test_clamped(self):
        """⚠️ ဘောင် ကန့်သတ်ရမည် — ink အနည်းငယ်ဆို size က ဘောင်ကျော်မည်"""
        s1, _ = W._pop_size(131, 0.002, WANT, H)
        self.assertLessEqual(s1, int(H * 0.5))
        s1, _ = W._pop_size(131, 0.90, WANT, H)
        self.assertGreaterEqual(s1, 24)

    def test_bad_input_safe(self):
        """ကျဘမ်း မဖြစ်ရ — render တစ်ခုလုံး မပျက်စေရန်"""
        for got in (0.0, -1.0, None, "x"):
            s1, redo = W._pop_size(131, got, WANT, H)
            self.assertEqual((s1, redo), (131, False))
        self.assertEqual(W._pop_size(None, 0.2, WANT, H)[1], False)

    def test_ink_returns_four(self):
        """`_pop_ink` က ဒေါင်လိုက်ပါ ပြန်ပေးရမည် — မဟုတ်လျှင် အမြင့် မတိုင်းနိုင်"""
        import inspect
        src = inspect.getsource(W._pop_ink)
        self.assertIn("rows", src)
        self.assertIn("int(rows.min()), int(rows.max())", src)

    def test_worker_rebuilds_once(self):
        """⚠️ ပြန်ဆောက်တာ **တစ်ခါသာ** — အဆုံးမရှိ မဖြစ်စေရ"""
        src = open(os.path.join(ROOT, "worker", "run.py"), encoding="utf-8").read()
        self.assertEqual(src.count("_pop_size("), 2)   # def + ခေါ်ချက် ၁


if __name__ == "__main__":
    unittest.main(verbosity=2)
