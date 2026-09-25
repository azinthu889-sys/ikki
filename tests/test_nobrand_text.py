# -*- coding: utf-8 -*-
"""Smart Edit has no brand row, so no graphic may print a made-up brand name.

2026-09-26: `topics.targs()` filled the brand slot with "IKKI", which showed
up as a yellow "IKKI" pill and "Class 1 vs IKKI" on a customer-style render.
"""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import topics as TP      # noqa: E402


class NoBrandText(unittest.TestCase):

    def test_no_ikki_in_any_pool_args(self):
        for kind, pool in TP.POOLS.items():
            for name in pool:
                a = TP.targs(name, "ကျောင်းသား ဗီဇာ", "")
                self.assertNotIn("IKKI", str(a), f"{kind}:{name} printed IKKI")
                # curated ones (fact_box, locator ...) leave slot 2 empty by design
                if a is not None and name not in TP.CURATED:
                    self.assertFalse(TP._blank(a), f"{kind}:{name} has an empty slot {a}")

    def test_brand_slot_templates_step_aside(self):
        for name in TP.USES_SUB:
            self.assertIsNone(TP.targs(name, "ခေါင်းစဉ်", ""), name)

    def test_every_pool_keeps_an_option(self):
        for kind, pool in TP.POOLS.items():
            usable = [n for n in pool if TP.targs(n, "ခေါင်းစဉ်", "") is not None]
            self.assertTrue(usable, f"pool {kind} has nothing without a brand")

    def test_real_brand_still_used(self):
        self.assertEqual(TP.targs("kicker_title", "ခေါင်းစဉ်", "Zin Apex"),
                         ("Zin Apex", "ခေါင်းစဉ်"))


if __name__ == "__main__":
    unittest.main()
