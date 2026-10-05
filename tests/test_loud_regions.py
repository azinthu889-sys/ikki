# -*- coding: utf-8 -*-
"""`cut.loud_removed()` regions ↔ worker ဖြည်ပုံ ကိုက်ရမည်

၂၀၂၆-၁၀-၀၅ j_0087b4d3e41f: regions က field ၆ ခု (voice ထပ်) ဖြစ်ပြီး
worker က ၅ ခုပဲ ဖြည်ခဲ့ ⇒ 「too many values to unpack (expected 5)」 နဲ့
ကျယ်သံ ပါတဲ့ ဗီဒီယိုတိုင်း render တစ်ခုလုံး ကျခဲ့သည်။
"""
import os
import re
import sys
import unittest

R = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(R, "core"))


class LoudRegions(unittest.TestCase):
    def test_worker_unpack_tolerates_extra_fields(self):
        s = open(os.path.join(R, "worker", "run.py"), encoding="utf-8").read()
        m = re.search(r"for (.+?) in _lr\[\"regions\"\]", s)
        self.assertTrue(m, "regions loop မတွေ့")
        self.assertIn("*_", m.group(1))

    def test_region_tuple_has_at_least_five(self):
        s = open(os.path.join(R, "core", "cut.py"), encoding="utf-8").read()
        i = s.find("regions.append((")
        self.assertGreater(i, 0)
        body = s[i:s.find("))", i)]
        self.assertGreaterEqual(body.count("round("), 5)


if __name__ == "__main__":
    unittest.main()
