#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · ရေးထားသော script ကို ASR ဝါကျများနှင့် ချိန်ညှိခြင်း。

⚠️ **ဖျက်ခြင်း မလုပ်ပါ** (Zin ၂၀၂၆-၀၉-၁၉) — Script Editor မှာ **အနီ ပြရုံ**、
   သုံးစွဲသူ အတည်ပြုမှသာ ဖျက်သည် (🔴 အုပ်စု သင်ခန်းစာ — အလိုအလျောက် ဖျက်တာ မှားနိုင်)。
⚠️ Gemini **မလို** — စာသား နှိုင်းယှဉ်ခြင်း သက်သက်。
⚠️ မြန်မာစာမှာ space မရှိ၍ **အက္ခရာ အဆင့်** နှိုင်းယှဉ်သည် (စကားလုံး ခွဲရန် မလို)。
"""
import os, re, zipfile
from difflib import SequenceMatcher

MISS = 0.50      # ဤအောက် ကိုက်ညီမှု ⇒ 「script မှာ မပါ」
DUP  = 0.60      # script နေရာ တစ်ခုတည်းကို ဤအထက် ထပ်ဖုံး ⇒ 「၂ ခါ ပြောထား」


def read(src):
    """str — .txt · .docx · စာသား အကြမ်း သုံးမျိုးလုံး ဖတ်သည်。

    ⚠️ `.docx` ကို **python-docx မလိုဘဲ** ဖတ်သည် (zip ထဲက `word/document.xml`)。
       package ထည့်စရာ မလို ⇒ server မှာ မတူညီမှု မဖြစ်。
    """
    if not isinstance(src, str): return ""
    if os.path.exists(src) and src.lower().endswith(".docx"):
        with zipfile.ZipFile(src) as z:
            xml = z.read("word/document.xml").decode("utf-8", "ignore")
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", "", xml)
    if os.path.exists(src):
        return open(src, encoding="utf-8", errors="ignore").read()
    return src


_PUNCT = re.compile(r"[\s​‌‍။၊,.!?;:\"'()\[\]{}–—-]+")

def norm(t):
    """နှိုင်းယှဉ်ရန် ပုံစံ — space · ပုဒ်ဖြတ် ဖယ် (ASR နဲ့ script က ကွဲတတ်၍)。"""
    return _PUNCT.sub("", (t or ""))


def align(script_text, segs):
    """[{n, match, dup, mark}, …] — ဝါကျ တစ်ခုချင်း script နဲ့ ဘယ်လောက် ကိုက်လဲ。

    `match` 0..1 — ဝါကျ အက္ခရာ ဘယ်နှစ်ရာခိုင်နှုန်း script ထဲ တွေ့လဲ
    `dup`        — ဤဝါကျ ဖုံးသော script နေရာကို **နောက်ပိုင်း ဝါကျ** ကလည်း ဖုံးလျှင် True
                   (ရှေ့ကဟာ = ပြန်ရိုက်ခံရမည့်ဟာ)
    `mark`       — "missing" · "dup" · None
    """
    S = norm(read(script_text))
    if not S or not segs: return []
    # ── ဝါကျများကို အက္ခရာ တစ်တန်း အဖြစ် ပေါင်း · index map ချန် ──
    buf = []; owner = []
    for i, s in enumerate(segs):
        t = norm(s.get("text"))
        buf.append(t); owner += [i]*len(t)
    A = "".join(buf)
    if not A: return []
    sm = SequenceMatcher(None, A, S, autojunk=False)
    cov = [0]*len(segs)          # ဖုံးထားသော အက္ခရာ
    span = [None]*len(segs)      # script ထဲ နေရာ (အနည်းဆုံး, အများဆုံး)
    for a, b, n in sm.get_matching_blocks():
        if n <= 0: continue
        for k in range(a, a+n):
            i = owner[k]; cov[i] += 1
            lo = b + (k-a)
            if span[i] is None: span[i] = [lo, lo]
            else:
                span[i][0] = min(span[i][0], lo); span[i][1] = max(span[i][1], lo)
    out = []
    for i, s in enumerate(segs):
        ln = len(norm(s.get("text"))) or 1
        out.append(dict(n=i+1, match=round(cov[i]/ln, 3), dup=False, mark=None,
                        span=span[i]))
    # ── ထပ်နေခြင်း — script နေရာ တစ်ခုတည်းကို ၂ ဝါကျ ဖုံးလျှင် **ရှေ့ကဟာ** ──
    for i in range(len(out)):
        si = out[i]["span"]
        if not si or out[i]["match"] < MISS: continue
        for j in range(i+1, len(out)):
            sj = out[j]["span"]
            if not sj or out[j]["match"] < MISS: continue
            lo = max(si[0], sj[0]); hi = min(si[1], sj[1])
            if hi <= lo: continue
            ov = (hi-lo) / max(1, (si[1]-si[0]))
            if ov >= DUP: out[i]["dup"] = True; break
    for o in out:
        o["mark"] = "dup" if o["dup"] else ("missing" if o["match"] < MISS else None)
        o.pop("span", None)
    return out
