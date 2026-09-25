# -*- coding: utf-8 -*-
"""SFX role — **unknown မကျန်ရ** · classifier က catalog ကို ပြန်ထုတ်နိုင်ရမည်。

⚠️ ၂၀၂၆-၀၉-၂၁ တိုင်းချက် — ဖိုင် ၇၄၁ ခုမှာ `unknown` ၁၄၄ ခု ရှိပြီး
   `sfxpool.MAP` က ဘယ် family ကမှ မညွှန်သဖြင့် **ထာဝရ မရွေးခံရ**ခဲ့သည်。
   `type`(၇) · `success`(၄) · `error`(၁) လည်း အတူတူ ⇒ ၁၅၆ ခု သေနေခဲ့သည်。
⚠️ HINT က catalog ကို ပြန်ထုတ်မရလျှင် catalog ပြန်ဆောက်တိုင်း ပျက်မည်。
"""
import os, sys, importlib.util, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import sfxpool as SP          # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "sfxcat", os.path.join(ROOT, "tools", "sfxcat.py"))
SC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SC)

ITEMS = SP.catalog()["items"]


class SfxRole(unittest.TestCase):

    def test_no_unknown(self):
        u = [x["id"] for x in ITEMS if (x.get("role") or "?") == "unknown"]
        self.assertEqual(u, [], f"unknown ကျန်နေသည် {len(u)} ခု")

    def test_every_role_is_mapped(self):
        """catalog ရဲ့ role တိုင်းကို MAP က ညွှန်ရမည် — မဟုတ်လျှင် သေနေမည်

        `air` က ချွင်းချက် — ၃.၅s ambient bed ကို cue role တွေ မလိုပါ。
        """
        fams = {v[0] for v in SP.MAP.values()}
        have = {x.get("role") for x in ITEMS} - {None}
        orphan = have - fams - {"air"}
        self.assertEqual(orphan, set(), f"ညွှန်မထားသော role: {sorted(orphan)}")

    def test_classifier_reproduces_catalog(self):
        """HINT က catalog ကို အတိအကျ ပြန်ထုတ်နိုင်ရမည်"""
        bad = [(x["id"], x.get("role"), SC.role_of(x["id"].split("/")[-1]))
               for x in ITEMS
               if SC.role_of(x["id"].split("/")[-1]) != x.get("role")]
        self.assertEqual(bad[:5], [], f"{len(bad)} ခု မကိုက် — ပြန်ဆောက်လျှင် ပျက်မည်")

    def test_no_empty_role_pool(self):
        """role တိုင်း ဖိုင် ရရမည် — ဗလာဆို legacy ဖိုင် တစ်ခုတည်း ပြန်ဖြစ်မည်

        WARN `sfxpool.DROP_ROLES` (`shutter`) is deliberately silenced: it
        fired 0 times across 43 renders and no asset of that role passes the
        band gate, because a camera shutter IS a mid-band sound. Zin's rule is
        that a wrong sound is worse than none, and that nothing may be quietly
        substituted -- so the exemption is checked, not assumed: the second
        assertion proves the role really produces silence.
        """
        _drop = set(SP.DROP_ROLES) if SP.BAND_GATE else set()
        empty = [r for r in SP.MAP
                 if SP.MAP[r][0] not in _drop
                 and not SP.role_pool(r, th="ikki", ship=True)]
        self.assertEqual(empty, [], f"ဗလာ role: {empty}")
        leak = {r: SP.wav(r, "t", 0)[1] for r in SP.MAP
                if SP.MAP[r][0] in _drop and SP.wav(r, "t", 0)[0]}
        self.assertEqual(leak, {}, f"ပိတ်ထားသော role က အသံ ပြန်ပေးသည်: {leak}")

    def test_reach_improved(self):
        """ရနိုင်သော ဖိုင် ၂၉၀ ကျော်ရမည် (ပြင်မတိုင်ခင် ၂၂၇ ဖြစ်ခဲ့)"""
        tot = set()
        for r in SP.MAP:
            tot |= {x["id"] for x in SP.role_pool(r, th="ikki", ship=True)}
        self.assertGreaterEqual(len(tot), 290, f"ရနိုင် {len(tot)} ခုသာ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
