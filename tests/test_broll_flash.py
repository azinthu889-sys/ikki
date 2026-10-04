# -*- coding: utf-8 -*-
"""B-roll ပြီးမှ ပြောသူ frame ဖျပ်ခနဲ မပေါ်စေရ — `worker/run.py:snap_broll`

audit ၂၀၂၆-၁၀-၀၄: B-roll က ဖြတ်မှတ်နဲ့ ၀.၂–၀.၄s အကွာမှာ ဆုံးခဲ့ရာ ပြောသူ frame
၇–၁၂ ခု ဖျပ်ခနဲ ပေါ် (၀.၂၃s · ၀.၄၀s)。 worker module ကို import မလုပ်ဘဲ (အလေးကြီး)
function ကိုသာ AST ကနေ ထုတ်စမ်းသည်。
"""
import ast
import os
import unittest

SRC = os.path.join(os.path.dirname(__file__), "..", "worker", "run.py")


def _load():
    tree = ast.parse(open(SRC, encoding="utf-8").read())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "snap_broll")
    ns = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), SRC, "exec"), ns)
    return ns["snap_broll"]


snap = _load()
# ချန်ထားသော span 0–10 · 20–30 · 40–50 ⇒ ထွက်မှာ ဖြတ်မှတ် 10.0 · 20.0
SPANS = [[0, 10], [20, 30], [40, 50]]


class Flash(unittest.TestCase):
    def test_end_snaps_to_cut(self):
        out, n = snap([(6.5, "b", 3.2, "")], SPANS, 2.4)   # 9.7 ⇒ ဖြတ်မှတ် 10.0 မှာ ဆုံး
        self.assertEqual(n, 1)
        self.assertAlmostEqual(out[0][0] + out[0][2], 10.0, places=2)

    def test_start_snaps_to_cut(self):
        out, n = snap([(10.3, "b", 3.0, "")], SPANS, 2.4)  # 10.0 ⇒ ဖြတ်မှတ်မှာ စ
        self.assertEqual((n, out[0][0]), (1, 10.0))

    def test_far_from_cut_untouched(self):
        out, n = snap([(4.0, "b", 3.0, "")], SPANS, 2.4)
        self.assertEqual((n, out[0][0]), (0, 4.0))

    def test_never_before_head(self):
        out, n = snap([(1.0, "b", 1.2, "")], [[0, 2.5], [5, 9]], 2.4)
        self.assertGreaterEqual(out[0][0], 1.0 if n == 0 else 2.4)

    def test_no_overlap_with_next(self):
        out, n = snap([(6.5, "b", 3.2, ""), (9.8, "c", 2.0, "")], SPANS, 2.4)
        self.assertLessEqual(out[0][0] + out[0][2], out[1][0] + 1e-6)


if __name__ == "__main__":
    unittest.main()
