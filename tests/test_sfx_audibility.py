# -*- coding: utf-8 -*-
"""SFX protection — ducking က audible floor အောက် မဆွဲချရ။"""
import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import dress as DR  # noqa: E402


class SfxAudibility(unittest.TestCase):
    def test_speech_duck_respects_audible_floor(self):
        # Asset −15 + cue −15 = −30dB, speech −35dB ⇒ duck လိုသည်။
        # Old policy က −27dB cue ထိ ဆွဲနိုင်ခဲ့သည်; floor က −22 ထက်
        # မနိမ့်စေရ။
        with patch.object(DR, "speech_db", return_value=-35.0):
            got, changed = DR.duck_cues([(1.0, "whoosh_in", -15)], "measured.wav",
                                        sfx_db={"whoosh_in": -15.0})
        self.assertEqual(changed, 1)
        self.assertGreaterEqual(got[0][2], DR.DUCK_DB_FLOOR)
        self.assertEqual(got[0][2], -22)

    def test_quiet_window_leaves_cue_unchanged(self):
        cue = (1.0, "whoosh_in", -15)
        with patch.object(DR, "speech_db", return_value=-50.0):
            got, changed = DR.duck_cues([cue], "measured.wav")
        self.assertEqual((got, changed), ([cue], 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
