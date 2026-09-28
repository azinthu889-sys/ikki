# -*- coding: utf-8 -*-
"""Script-assisted spelling for captions (Zin 2026-09-28: "တစ်ချို့ user တွေက
script ထည့်ပေးပါလိမ့်မယ်။ Script ထည့်ပေးရင် Script နဲ့ပါ မှန်အောင် တိုက်နိုင်အောင်").

The ASR model that has quota (gemini-3.1-flash-lite) mishears names and loan
words (measured on tokutei: "သက္ခာလာနိုဘာဘာ" for Takadanobaba, "တစ်ခုတည်း"
for Tokutei, "ကျွန်တော်တို့" from a female speaker). When the user pasted a
script, its spelling is usually right -- but the speaker does NOT read it word
for word ("၄ နှစ်" in the script, "၂ နှစ်" said; "Zin Apex" in the script,
"J-Path" said).

WARN giving the whole script to the ASR prompt fixed 7-8/10 errors but wrote
   "Zin Apex" where the speaker said "J-Path" in 2/2 runs -- the model copies
   the script instead of listening. A terms-only list was safe but fixed 1.
   => the audio decides, one disputed span at a time:
   1. align ASR words to the script by syllables; a short `replace`/`insert`
      between two matching anchors is a candidate
   2. cut that span's audio (+context) and ask the model to CHOOSE: the
      script's spelling, the ASR's, or neither -- choosing between two given
      strings is easier than transcribing, and "neither" keeps unsaid script
      text out
   3. only a "script" pick is applied; word timings are kept (the covering
      words merge into one timed word)
WARN deletions are never applied: a speaker saying MORE than the script is
   normal, and a caption must never lose a word that was spoken.
WARN segments the user already edited (`fix`) are left alone -- the user wins.
"""
import hashlib, json, os, re, subprocess, tempfile, urllib.request

import captions as CP
import script as SC

ANCHOR = 2          # matching syllables required on both sides of a candidate
MAX_SYL = 8         # longest disputed span (syllables, either side)
MAX_INS = 2         # longest pure insertion (script has, ASR lacks)
PAD = 0.35          # audio context around the disputed words (s)
MAX_CALLS = 60      # per video

_LAT = re.compile(r"[A-Za-z0-9]")


def _syl(s):
    return [x for x in CP.syllables(s) if x.strip()]


def _key(x):
    # dot-below / asat order differs between ASR and typed text ("ယ့်" vs "ယ့်")
    return x.lower().replace("\u103a\u1037", "\u1037\u103a")


def _weight(sy):
    """spoken length of syllables -- a Latin word counts its vowel groups
    (WARN "Takadanobaba" is ONE syllable token but ~6 spoken; counted as 1
    the length guard blocked it against "သက္ခာလာနိုဘာဘာ")"""
    n = 0
    for x in sy:
        if _LAT.search(x):
            # a Burmese transliteration splits consonant clusters ("Program" ->
            # ပ-ရို-ဂ-ရမ်, 4 syllables for 2 vowels) -> letters / 2, not vowel groups
            n += max(1, -(-len(re.sub(r"[^A-Za-z0-9]", "", x)) // 2))
        else:
            n += 1
    return n


def _script_syl(raw):
    """script syllables of the normalised text + (start, end) offsets into `raw`,
    so a suggestion can show the script's own spelling WITH its spaces
    ("Tokutei Program", not "TokuteiProgram")."""
    keep = [(i, ch) for i, ch in enumerate(raw) if SC.norm(ch)]
    flat = "".join(ch for _i, ch in keep)
    out, pos = [], 0
    for x in CP.syllables(flat):
        n = len(x)
        if x.strip():
            out.append((x, keep[pos][0], keep[pos + n - 1][0] + 1))
        pos += n
    return out


def _join(parts):
    """join text pieces, with a space where Burmese meets Latin
    ("တက်ပြီး" + "Tokutei Program" -> "တက်ပြီး Tokutei Program")"""
    out = ""
    for p in parts:
        if not p: continue
        if out and (bool(_LAT.search(out[-1])) != bool(_LAT.search(p[0]))) \
                and not out.endswith(" ") and not p.startswith(" "):
            out += " "
        out += p
    return out


def candidates(words, script_text):
    """words: [(text, s, e)] in time order -> [dict(w0, w1, base, new, prev, next)]

    `w0..w1` (inclusive) are the ASR words the span touches; `base`/`new` are
    their joined text before/after taking the script's spelling."""
    raw = SC.read(script_text)
    SS = _script_syl(raw)
    S = [x for x, _a, _b in SS]
    A, own = [], []                          # base syllables, owning word index
    for wi, (t, _s, _e) in enumerate(words):
        for x in _syl(SC.norm(t)):
            A.append(x); own.append(wi)
    if not A or not S:
        return []
    from difflib import SequenceMatcher
    ops = SequenceMatcher(None, [_key(x) for x in A], [_key(x) for x in S], autojunk=False).get_opcodes()
    out = []
    for k, (op, i1, i2, j1, j2) in enumerate(ops):
        if op not in ("replace", "insert"):
            continue
        if op == "replace" and (i2 - i1 > MAX_SYL or j2 - j1 > MAX_SYL):
            continue
        if op == "insert" and j2 - j1 > MAX_INS:
            continue
        # WARN a script span SHORTER than what was heard deletes spoken words
        #    (measured: "…အောင်လက်မှတ်…" and "တွေ" vanished) -- at most 1 syllable shorter
        if op == "replace" and _weight(S[j1:j2]) < _weight(A[i1:i2]) - 1:
            continue
        pv = ops[k - 1] if k else None
        nx = ops[k + 1] if k + 1 < len(ops) else None
        if not (pv and pv[0] == "equal" and pv[2] - pv[1] >= ANCHOR and
                nx and nx[0] == "equal" and nx[2] - nx[1] >= ANCHOR):
            continue
        if op == "insert":                   # attach to the word before the gap
            w0 = w1 = own[i1 - 1]
        else:
            w0, w1 = own[i1], own[i2 - 1]
        # rebuild the covering words' text with the script syllables in place
        first = own.index(w0); last = len(own) - 1 - own[::-1].index(w1)
        base = "".join(A[first:last + 1])
        new = "".join(A[first:i1]) + "".join(S[j1:j2]) + "".join(A[i2:last + 1])
        if _key(SC.norm(base)) == _key(SC.norm(new)):
            continue                         # case / spacing / mark order only
        disp = (raw[SS[j1][1]:SS[j2 - 1][2]].strip() if j2 > j1 else "")
        new_disp = _join(["".join(A[first:i1]), disp, "".join(A[i2:last + 1])])
        out.append(dict(w0=w0, w1=w1, base=base, new=new, new_disp=new_disp,
                        prev="".join(A[max(0, first - 6):first]),
                        next="".join(A[last + 1:last + 7])))
    return out


def _ask(clip, prev, opts, nxt, model, endpoint):
    """-> 'A' | 'B' | 'C' | None"""
    import base64
    b64 = base64.b64encode(open(clip, "rb").read()).decode()
    prompt = ("ဒီအသံ အပိုင်းမှာ မြန်မာ ပြောသူ တစ်ယောက် ပြောနေသည်။\n"
              f"ရှေ့က စကား: «{prev}» … နောက်က စကား: «{nxt}»\n"
              "ကြားထဲမှာ **တကယ် ပြောတာ** ဘယ်ဟာလဲ —\n"
              f"A: «{opts[0]}»\nB: «{opts[1]}»\n"
              "C: နှစ်ခုလုံး မဟုတ် / မသေချာ\n"
              "အသံကို နားထောင်ပြီး ဆုံးဖြတ်ပါ — စာလုံးပေါင်း လှတာကို မရွေးရ။ "
              "A · B · C တစ်လုံးသာ ဖြေပါ။")
    body = {"contents": [{"parts": [{"text": prompt},
                                    {"inline_data": {"mime_type": "audio/ogg", "data": b64}}]}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json",
                                 "responseSchema": {"type": "OBJECT",
                                                    "properties": {"pick": {"type": "STRING",
                                                                            "enum": ["A", "B", "C"]}},
                                                    "required": ["pick"]}}}
    for _ in range(3):
        try:
            r = urllib.request.Request(endpoint(model), data=json.dumps(body).encode(),
                                       headers={"Content-Type": "application/json"}, method="POST")
            d = json.loads(urllib.request.urlopen(r, timeout=90).read())
            t = d["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(t).get("pick")
        except Exception:
            continue
    return None


def _w(w):
    """(text, start, end) from either word shape: ASR `{w, s, e}` or caption `[w, s, e]`"""
    if isinstance(w, dict):
        return str(w.get("w", "")), float(w.get("s", 0)), float(w.get("e", 0))
    return str(w[0]), float(w[1]), float(w[2])


def fix(segs, script_text, wav, log=print, model=None, endpoint=None):
    """Apply script spellings the audio confirms. Returns (segs, report)."""
    rep = dict(candidates=0, asked=0, script=0, asr=0, neither=0, failed=0, changes=[])
    if not script_text or not segs:
        return segs, rep
    if model is None or endpoint is None:
        import asr as _A, gemguard as _G
        model = model or _A.MODEL; endpoint = endpoint or _G.endpoint
    # flat word list (segments the user edited are skipped entirely)
    flat = []
    for si, s in enumerate(segs):
        if not isinstance(s, dict) or s.get("fix"):
            continue
        ws = s.get("words") or []
        for wi, w in enumerate(ws):
            t, a, b = _w(w)
            flat.append((t, a, b, si, wi))
    if not flat:
        return segs, rep
    cands = candidates([(t, a, b) for t, a, b, _si, _wi in flat], script_text)
    # never across a segment boundary (the merged word must stay in one caption line)
    cands = [c for c in cands if flat[c["w0"]][3] == flat[c["w1"]][3]]
    rep["candidates"] = len(cands)
    work = tempfile.mkdtemp(prefix="ikki_sfix_")
    edits = {}                                   # (si, wi0, wi1) -> new text
    for c in cands[:MAX_CALLS]:
        a = max(0.0, flat[c["w0"]][1] - PAD); b = flat[c["w1"]][2] + PAD
        if b - a < 1.0:
            m = (a + b) / 2; a, b = max(0.0, m - 0.5), m + 0.5
        clip = os.path.join(work, f"{len(edits)}_{a:.2f}.ogg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.2f}", "-t", f"{b - a:.2f}",
                        "-i", wav, "-ac", "1", "-ar", "16000", "-c:a", "libopus", "-b:a", "24k", clip],
                       check=True)
        # order by hash so the model cannot learn "A is always the script"
        # WARN one question is not enough: flash-lite picked the script in 12/20
        #    and never said "neither" -- incl. "Zin Apex" for a spoken "J-Path".
        #    => ask twice with A/B swapped; the script wins only if BOTH say so.
        votes = []
        for opts in ((c["new"], c["base"]), (c["base"], c["new"])):
            p = _ask(clip, c["prev"], opts, c["next"], model, endpoint)
            votes.append(None if p is None else ("C" if p == "C" else
                         ("script" if opts["AB".index(p)] == c["new"] else "asr")))
        rep["asked"] += 1
        if None in votes: pick = None
        elif votes == ["script", "script"]: pick = "script"
        elif "script" in votes and "asr" not in votes: pick = "C"
        elif votes == ["asr", "asr"]: pick = "asr"
        else: pick = "C"                          # the model contradicted itself
        if pick is None: rep["failed"] += 1
        elif pick == "C": rep["neither"] += 1
        else: rep[pick] += 1
        rep["changes"].append(dict(t=round(flat[c["w0"]][1], 2), base=c["base"], script=c["new"],
                                   pick=pick or "failed"))
        if pick == "script":
            si = flat[c["w0"]][3]
            edits[(si, flat[c["w0"]][4], flat[c["w1"]][4])] = c["new"]
    # apply, last first so word indices stay valid
    for (si, w0, w1), new in sorted(edits.items(), key=lambda kv: (-kv[0][0], -kv[0][1])):
        ws = segs[si]["words"]
        a0, b1 = _w(ws[w0])[1], _w(ws[w1])[2]
        ws[w0:w1 + 1] = [dict(w=new, s=a0, e=b1) if isinstance(ws[w0], dict) else [new, a0, b1]]
        tail = "။" if str(segs[si].get("text", "")).rstrip().endswith("။") else ""
        segs[si]["text"] = " ".join(_w(w)[0] for w in ws).rstrip("။") + tail
        segs[si]["script_fixed"] = True
    log(f"  script စာလုံးပေါင်း · ကွဲ {rep['candidates']} · မေး {rep['asked']} · "
        f"script {rep['script']} · ASR {rep['asr']} · မဟုတ် {rep['neither']}"
        + (f" · ⚠️ မရ {rep['failed']}" if rep["failed"] else ""))
    return segs, rep


def suggest(segs, script_text):
    """Spelling suggestions for the transcript editor -- no audio, no model call.

    [dict(i, base, new, text)] -- `i` segment index, `base` the words as shown
    in that segment's text, `new` the script's spelling, `text` the whole line
    with just this suggestion applied. The user accepts each one (Zin: the
    audio model cannot yet tell "J-Path" from the script's "Zin Apex")."""
    flat = []
    for si, sg in enumerate(segs or []):
        if not isinstance(sg, dict):
            continue
        for wi, w in enumerate(sg.get("words") or []):
            t, a, b = _w(w)
            flat.append((t, a, b, si, wi))
    if not flat or not script_text:
        return []
    out = []
    for c in candidates([(t, a, b) for t, a, b, _si, _wi in flat], script_text):
        si = flat[c["w0"]][3]
        if flat[c["w1"]][3] != si:
            continue
        ws = segs[si].get("words") or []
        parts = [_w(ws[k])[0] for k in range(flat[c["w0"]][4], flat[c["w1"]][4] + 1)]
        text = str(segs[si].get("fix") or segs[si].get("text") or "")
        m = re.search(r"\s*".join(re.escape(x) for x in parts if x), text)
        if not m:
            continue
        new = c["new_disp"]
        tail = re.search(r"[။၊,.!?]+\s*$", m.group(0))
        if tail and not re.search(r"[။၊,.!?]\s*$", new):
            new += tail.group(0).strip()     # keep the line's own full stop
        out.append(dict(i=si, base=m.group(0), new=new,
                        text=text[:m.start()] + new + text[m.end():]))
    return out


def retext(words, new_text):
    """Give timed words the text of a user fix, keeping every time.

    WARN the worker used to swap only `text` for `fix`; word-pop captions read
    `words`, so an accepted spelling ("Takadanobaba") never reached the screen.
    Syllables of the fix are aligned to the words' syllables: matching and
    replaced syllables go to the word they align with, inserted ones to the word
    before; a word left with no text gives its time to its neighbour. The
    concatenation of the result is exactly `new_text` (spaces between words)."""
    ws = [list(_w(w)) for w in (words or [])]
    if not ws or not str(new_text or "").strip():
        return words
    A, own = [], []
    for wi, (t, _a, _b) in enumerate(ws):
        for x in _syl(SC.norm(t)):
            A.append(x); own.append(wi)
    SS = _script_syl(str(new_text))
    if not A or not SS:
        return words
    from difflib import SequenceMatcher
    B = [x for x, _a, _b in SS]
    got = [[] for _ in ws]                       # per word: indices into SS
    for op, i1, i2, j1, j2 in SequenceMatcher(None, [_key(x) for x in A], [_key(x) for x in B],
                                               autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(j2 - j1): got[own[i1 + k]].append(j1 + k)
        elif op == "replace":
            n_a = i2 - i1
            for k in range(j2 - j1):             # spread over the replaced words in order
                got[own[i1 + min(n_a - 1, k * n_a // max(1, j2 - j1))]].append(j1 + k)
        elif op == "insert":
            got[own[i1 - 1] if i1 else 0].extend(range(j1, j2))
    raw = str(new_text)
    out = []
    for wi, idx in enumerate(got):
        if not idx:
            if out: out[-1][2] = ws[wi][2]       # the previous word absorbs the time
            else: ws[wi + 1][1] = ws[wi][1] if wi + 1 < len(ws) else ws[wi][1]
            continue
        a, b = SS[min(idx)][1], SS[max(idx)][2]
        out.append([raw[a:b].strip(), ws[wi][1], ws[wi][2]])
    if not out:
        return words
    as_dict = isinstance((words or [None])[0], dict)
    return [dict(w=t, s=a, e=b) for t, a, b in out] if as_dict else out
