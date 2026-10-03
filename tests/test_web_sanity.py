# -*- coding: utf-8 -*-
"""web ဖိုင်များ **တကယ် ပြေးနိုင်ရမည်** — syntax မှန်ရုံနဲ့ မလုံလောက်

⚠️⚠️ ၂၀၂၆-၁၀-၀၄ — ကိုယ်တိုင် ရေးလိုက်တဲ့ **မှတ်ချက်က app.js ကို ချိုး**ခဲ့သည်:

      /* ... `/upload/*/parts` ... */
                        ↑ ဒီ `*/` က မှတ်ချက်ကို **စောပိတ်**သည်

   ကျန်တဲ့ စာသားက ကုဒ် ဖြစ်သွားပြီး `ReferenceError: parts is not defined` ⇒
   **app.js တစ်ခုလုံး ရပ်**သည် (ဘာ handler မှ မတပ်ဖြစ်)。
   ⚠️ `node --check` က **အောင်**သည် — ထွက်လာတဲ့ ကုဒ်က syntax အရ မှန်နေ၍。
      ⇒ syntax စစ်ချက်က ဒီအမျိုးအစားကို **ဖမ်းလို့ မရ**。

⚠️ CSS မှာလည်း တူညီသော ထောင်ချောက် ရှိသည် — `/* ... */` တစ်မျိုးတည်း。
"""
import io
import os
import re
import unittest

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = ("web/app.js", "web/app.css", "web/script.html", "web/index.html")


def _src(p):
    return io.open(os.path.join(_R, p), encoding="utf-8").read()


def _blocks(s):
    """(အစ, အဆုံး, ထဲက စာသား) — `/* … */` မှတ်ချက်များ"""
    out, i = [], 0
    while True:
        a = s.find("/*", i)
        if a < 0: break
        b = s.find("*/", a + 2)
        if b < 0:
            out.append((a, len(s), s[a + 2:]))
            break
        out.append((a, b, s[a + 2:b]))
        i = b + 2
    return out


class Comments(unittest.TestCase):
    def test_no_comment_closes_itself_early(self):
        """⚠️⚠️ **အဓိက** — မှတ်ချက်ထဲ `*/` ပါလျှင် ကျန်တာ ကုဒ် ဖြစ်သွားမည်"""
        for f in WEB:
            s = _src(f)
            for a, b, body in _blocks(s):
                self.assertNotIn("*/", body,
                                 f"{f}: စာကြောင်း {s[:a].count(chr(10))+1} မှာ "
                                 f"မှတ်ချက် စောပိတ်သည် — {body[:60]!r}")

    def test_no_comment_ends_in_the_middle_of_a_word(self):
        """⚠️⚠️ **ဒီနေ့ ဖြစ်ခဲ့တဲ့ bug ကို ဖမ်းမယ့် စစ်ချက်**。

        မှတ်ချက် တကယ် ပိတ်တာက `*/` ပြီးရင် နေရာလွတ် (သို့) စာကြောင်းသစ်。
        `*/parts` လို **စာလုံး တန်းလာ**တာက မှတ်ချက်ထဲက URL (`/upload/*/parts`)
        ဖြစ်ပြီး parser က အဲဒီမှာ မှတ်ချက် ပိတ်လိုက်သည် ⇒ ကျန်တာ ကုဒ်。

        ⚠️ `/*` ရေတွက်ပြီး နှိုင်းတာ **မရ** — string/regex ထဲမှာလည်း `/*`
           ပါတတ်သည် (app.js မှာ ၉၈ vs ၉၆ · index.html မှာ ၂ vs ၀)。
        စစ်ထား: ဤစည်းမျဉ်းက ဖိုင် ၄ ခုလုံးမှာ **false positive ၀**。
        """
        import re as _re
        for f in WEB:
            s = _src(f)
            for m in _re.finditer(r"\*/(?=\S)", s):
                ln = s[:m.start()].count("\n") + 1
                self.fail(f"{f}:{ln} — `*/` နောက်မှာ စာလုံး တန်းလာသည်: "
                          f"{s[max(0,m.start()-30):m.start()+20]!r}")


class Executes(unittest.TestCase):
    """⚠️ ပြေးနိုင်မနိုင်ကို node နဲ့ စစ်သည် (ရှိလျှင်)"""

    def _node(self):
        import shutil
        return shutil.which("node")

    def test_app_js_parses(self):
        node = self._node()
        if not node: self.skipTest("node မရှိ")
        import subprocess
        r = subprocess.run([node, "--check", os.path.join(_R, "web/app.js")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[:400])

    def test_the_editor_script_parses(self):
        node = self._node()
        if not node: self.skipTest("node မရှိ")
        import subprocess, tempfile
        s = _src("web/script.html")
        js = "\n;\n".join(re.findall(r"<script[^>]*>(.*?)</script>", s, re.S))
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(js); tmp = fh.name
        try:
            r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr[:400])
        finally:
            os.unlink(tmp)


class Hidden(unittest.TestCase):
    """⚠️⚠️ selector တစ်ခုက `display` သတ်မှတ်လိုက်လျှင် UA ရဲ့
       `[hidden]{display:none}` ကို လွှမ်းသည် ⇒ `el.hidden=true` လုပ်လည်း
       **ပျောက်မသွား**ပါ。 ဒီနေ့ ၂ ကြိမ် ဖြစ်ခဲ့ (မည်းနေသော ဗီဒီယို ဘောင် ·
       ပိတ်ထားတဲ့ ⚙ panel)。 ⇒ စည်းမျဉ်း တစ်ကြောင်းနဲ့ အမျိုးအစားတစ်ခုလုံး ပိတ်。"""

    def test_both_stylesheets_guarantee_hidden(self):
        for f in ("web/app.css", "web/script.html"):
            self.assertIn("[hidden]{display:none !important}", _src(f), f)


class Rejections(unittest.TestCase):
    """⚠️⚠️ `api()` က promise ပစ်သည် · ခေါ်ချက် ၅၈ ခုမှာ ၁၂ ခု `.catch` မပါ
       (`/jobs` · `/uploads/resumable` · `/upload/…/complete` · `/pay` အပါအဝင်)
       ⇒ ကွန်ရက် ပြတ်လျှင် **ဘာမှ မပြဘဲ ရပ်သွား**မည် (「ရပ်သွားပါတယ်」)。"""

    def test_there_is_a_catch_all(self):
        s = _src("web/app.js")
        self.assertIn('addEventListener("unhandledrejection"', s)

    def test_handled_errors_stay_silent(self):
        """⚠️ `auth`/`quota` က `api()` ထဲမှာ ကိုင်ပြီးသား — နှစ်ထပ် မပြရ"""
        s = _src("web/app.js")
        i = s.find('addEventListener("unhandledrejection"')
        w = s[i:i + 700]
        self.assertIn('m==="auth"||m==="quota"', w)
        self.assertIn('r.name==="AbortError"', w)

    def test_it_does_not_block_the_page(self):
        """⚠️ `alert()` က upload/render လုပ်နေစဉ် စာမျက်နှာ တစ်ခုလုံး ပိတ်ဆို့သည်"""
        s = _src("web/app.js")
        i = s.find('addEventListener("unhandledrejection"')
        self.assertNotIn("alert(", s[i:i + 900])

    def test_it_is_testable(self):
        """⚠️ စမ်းလို့ မရလျှင် သက်ရောက်မသက်ရောက် မသိ — ဒီနေ့ ၁၅ မိနစ် ကုန်ခဲ့"""
        s = _src("web/app.js")
        self.assertIn("window.__ikki_rej", s)
        self.assertIn("window.__ikki_err", s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
