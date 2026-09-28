# -*- coding: utf-8 -*-
"""Burmese word segmentation for caption chunking (2026-09-28).

Char-level CRF model and feature template from pyidaungsu 0.1.4
(MIT License, Copyright (c) 2020 Kaung Htet San -- see
assets/mmseg/LICENSE.pyidaungsu). Only the word tokenizer is vendored; the
package's fasttext language detector is not needed and does not load on this
Mac. Requires python-crfsuite (MIT); without it `words()` returns None and the
caller falls back to syllable boundaries.
"""
import os

_MODEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "assets", "mmseg", "tokenizer.crfsuite")
_TAGGER = [None]


def _tagger():
    if _TAGGER[0] is None:
        try:
            import pycrfsuite
            t = pycrfsuite.Tagger(); t.open(_MODEL); _TAGGER[0] = t
        except Exception:
            _TAGGER[0] = False
    return _TAGGER[0] or None


def _feat(s, i):
    f = ["bias", "char=" + s[i]]
    if i >= 1: f += ["char-1=" + s[i-1], "char-1:0=" + s[i-1] + s[i]]
    else: f.append("BOS")
    if i >= 2: f += ["char-2=" + s[i-2], "char-2:0=" + s[i-2] + s[i-1] + s[i], "char-2:-1=" + s[i-2] + s[i-1]]
    if i >= 3: f += ["char-3:0=" + s[i-3] + s[i-2] + s[i-1] + s[i], "char-3:-1=" + s[i-3] + s[i-2] + s[i-1]]
    if i + 1 < len(s): f += ["char+1=" + s[i+1], "char:+1=" + s[i] + s[i+1]]
    else: f.append("EOS")
    if i + 2 < len(s): f += ["char+2=" + s[i+2], "char:+2=" + s[i] + s[i+1] + s[i+2], "char+1:+2=" + s[i+1] + s[i+2]]
    if i + 3 < len(s): f += ["char:+3=" + s[i] + s[i+1] + s[i+2] + s[i+3], "char+1:+3=" + s[i+1] + s[i+2] + s[i+3]]
    return f


def words(text):
    """list of words whose concatenation is `text` without spaces, or None"""
    t = _tagger()
    if t is None: return None
    s = str(text).replace(" ", "")
    if not s: return []
    tags = t.tag([_feat(s, i) for i in range(len(s))])
    out, cur = [], ""
    for ch, tg in zip(s, tags):
        if tg == "1" and cur: out.append(cur); cur = ""
        cur += ch
    if cur: out.append(cur)
    return out
