#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset ရဲ့ ?v= ကို ဖိုင်ရဲ့ mtime နှင့် ပြန်ရေးသည်。

⚠️ ?v= ကို **hardcode မထားရ**。 ထားလျှင် app.js ပြင်လည်း URL မပြောင်းသဖြင့်
   browser က အရင်ဖိုင်ကို ဆက်သုံးပြီး **အသစ်က မမြင်ရဘူး** (တကယ် ဖြစ်ခဲ့ —
   အရွယ် ရွေးတဲ့ အကွက် ပေါ်မလာခဲ့)。 deploy တိုင်း ဒီ script ကို run ရမည်。
"""
import io, os, re, sys

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
p = os.path.join(WEB, "index.html")
h = io.open(p, encoding="utf-8").read()
n = 0
for asset in ("app.js", "app.css"):
    f = os.path.join(WEB, asset)
    if not os.path.exists(f): continue
    v = int(os.path.getmtime(f))
    h2 = re.sub(r"(/%s)\?v=\d+" % re.escape(asset), r"\1?v=%d" % v, h)
    if h2 != h: n += 1
    h = h2
    print("  %-8s ?v=%d" % (asset, v))
io.open(p, "w", encoding="utf-8").write(h)
print("  ✓ %d ခု ပြောင်းပြီး" % n)
