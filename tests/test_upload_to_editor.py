# -*- coding: utf-8 -*-
"""upload ပြီးတာနဲ့ pane ၃ ခု editor ထဲ တန်းဝင် (Zin ၂၀၂၆-၁၀-၀၅)

「video upload လုပ်လိုက်တာနဲ့ စဖွင့်ကတည်းက 3 layout design နဲ့ စဖွင့်ပြီး
 export အထိ UI နဲ့ သွားလို့ရအောင်」
  · app.js — job ဆောက်ပြီးတာနဲ့ script.html ဆီ ပို့ (Cinematic · ?old=1 မပါ)
  · script.html — ASR မပြီးခင် prep mode (ပုံ · progress · timeline စောင့်)
    ⇒ `review` ရောက်တာနဲ့ reload မလုပ်ဘဲ editor ဖွင့်
"""
import os
import unittest

R = os.path.join(os.path.dirname(__file__), "..", "web")


def _r(n):
    with open(os.path.join(R, n), encoding="utf-8") as f:
        return f.read()


class UploadGoesToEditor(unittest.TestCase):
    def setUp(self):
        self.a = _r("app.js")
        self.s = _r("script.html")

    def test_new_job_redirects_to_editor(self):
        i = self.a.find("editorPoster(files[0], j.job_id)")
        self.assertGreater(i, 0)
        w = self.a[i - 400:i + 200]
        self.assertIn("!cine", w)
        self.assertIn("old=1", w)
        self.assertIn("/script.html?job=", w)

    def test_poster_never_blocks(self):
        i = self.a.find("function editorPoster(")
        w = self.a[i:i + 1600]
        self.assertIn("setTimeout(end, 2500)", w)
        self.assertIn("ikki_poster_", w)

    def test_editor_enters_prep_when_no_transcript(self):
        self.assertIn("function prepEnter()", self.s)
        self.assertIn('["queued","running"].indexOf(JOBROW.status)>-1){ prepEnter(); return }', self.s)

    def test_review_opens_without_reload(self):
        i = self.s.find("if(PREP){")
        w = self.s[i:i + 300]
        self.assertIn('if(st==="review"){ prepExit(); return }', w)

    def test_prep_keeps_three_panes(self):
        i = self.s.find("function prepEnter()")
        w = self.s[i:i + 2600]
        for k in ('vb.hidden=false', 'sk.id="prepsk"', 'tb.hidden=false'):
            self.assertIn(k, w)


if __name__ == "__main__":
    unittest.main()
