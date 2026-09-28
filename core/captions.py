#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · မြန်မာ စာတန်း。

⚠️ **ffmpeg မှာ input ၁၄၀ ခန့်ရောက်လျှင် ပျက်သည်** — scaler/decoder ကုန်သည်
   ("Resource temporarily unavailable" / "Error while opening decoder")。
   ဗီဒီယို ၁၀ မိနစ်မှာ စာတန်း ~၂၀၀ ရှိသဖြင့် PNG အားလုံးကို input အဖြစ်
   **တစ်ပြိုင်တည်း ထည့်၍ မရ**。
   ⇒ concat demuxer ဖြင့် **alpha overlay ဗီဒီယို တစ်ခု** အရင်ဆောက်ပြီး
     အဲဒါ တစ်ခုတည်းကို overlay လုပ်သည် (input ၂ ခုသာ)。

⚠️ မြန်မာစာ **စကားလုံးအလယ် မပိုင်းရ**。 အက္ခရာအရေအတွက်ဖြင့် အကျယ် မမှန်းရ —
   IG.MW() ဖြင့် တိုင်းရသည် (ခန့်မှန်းလျှင် ၂ ဆ လွဲသည်)。

⚠️ **cttext ကို newline ပါသော စာသား ပို့၍ မရ** — သူက input စာသားကို
   output JSON ထဲ escape မလုပ်ဘဲ ပြန်ထည့်သဖြင့် `json.loads` ပျက်သည်
   ("Invalid control character")。 ⇒ စာတန်း **တစ်ကြောင်းတည်း**သာ ရေးရသည်。
   ဒါက house spec နှင့်လည်း ကိုက်သည် — "one line, ~28 clusters"。
   ရှည်လျှင် အရွယ် ချုံ့၊ မလုံလျှင် စာတန်း ၂ ခု ခွဲသည်。
"""
import os, re, subprocess

# မြန်မာ cluster — အခြေအက္ခရာ + ပေါင်းစပ် သင်္ကေတများ
_CL = re.compile(r"[\u1000-\u102A\u103F\u104C-\u104F\u0020-\u007E]"
                 r"[\u102B-\u103E\u1039\u1040-\u104B\uFE00-\uFE0F]*")

# ⚠️ regex က စာကြောင်းကို မကုန်စားနိုင်လျှင် `list(t)` — **အက္ခရာလိုက် ခွဲ**သည်။
#    အဲဒီအခါ ေ ာ ် ြ ွ ပြုတ်နိုင်သည်။ ဘယ်နှစ်ကြိမ် ဖြစ်လဲ ရေတွက်ထားမှ
#    render report မှာ ပြနိုင်မည် (ပစ်မှတ် = ၀)။
FALLBACK = [0]

def clusters(t):
    out = _CL.findall(t)
    # findall က မိမသော အက္ခရာများ ကျန်စေရန် အရှည် စစ်သည်
    if sum(len(x) for x in out) == len(t):
        return out
    FALLBACK[0] += 1
    return list(t)

def wrap(text, size, maxw, MW, font=None):
    """စကားလုံးအလယ် **မပိုင်း**ဘဲ ကြောင်းခွဲသည်。

    ⚠️ space ဖြင့်သာ ခွဲလျှင် မလုံလောက် — မြန်မာစာမှာ စကားလုံးရှည်တွေ
       space မပါ ("ဘာသာကိုယ်လေ့လာခိုင်းတာမျိုးမဟုတ်" = ၁၁၅px မှာ 1766px
       တစ်လုံးတည်း၊ ဘောင်က 928px သာ)。 ⇒ အဲဒီအခါ **cluster နယ်နိမိတ်**မှာ
       ခွဲရသည် — အက္ခရာ အလယ် မပိုင်းရ (မာတ်တွေ ပြုတ်သွားမည်)。
    """
    out=[]
    for w in [x for x in text.replace(" ", " ").split(" ") if x]:
        if MW(w, size, font) <= maxw:
            out.append(w); continue
        cur=""
        for c in clusters(w):
            if cur and MW(cur+c, size, font) > maxw:
                out.append(cur); cur=c
            else:
                cur += c
        if cur: out.append(cur)
    # တစ်လုံးချင်းကို ကြောင်းအလိုက် ပြန်ပေါင်း
    lines=[]; cur=""
    for w in out:
        t=(cur+" "+w).strip()
        if cur and MW(t, size, font) > maxw:
            lines.append(cur); cur=w
        else:
            cur=t
    if cur: lines.append(cur)
    return lines

def cards(c, size, maxw, MW, font, max_lines=2, hold=4.0):
    """စာတန်းတစ်ခုကို ကတ်အလိုက် ခွဲသည် — ကတ်တစ်ခုမှာ **အများဆုံး ၂ ကြောင်း**。

    ⚠️ ZAE spec: "တစ်ကြောင်း ဒါမှမဟုတ် ၂ ကြောင်း၊ **၃ ကြောင်း မရ**"。
    ⚠️ ၈% အရွယ် (၁၁၅px) မှာ တစ်ကြောင်းတည်းဆို **ဘယ်ဟာမှ မဝင်** —
       တိုင်းကြည့်ရာ ရှည်တာက 3278px လိုပြီး ဘောင်က 928px သာ ရှိသည်。
       ⇒ ၂ ကြောင်းနဲ့လည် မလုံလျှင် **အချိန် ခွဲ**ရသည် (စာအရင်၊ ပြီးမှ အချိန်)。
    ⚠️ စကားလုံးအလယ် **မပိုင်းရ** — wrap() က စကားလုံးနယ်နိမိတ်ကိုပဲ သုံးသည်。
    """
    ls = wrap(c["text"], size, maxw, MW, font)
    if not ls: return []
    # ⚠️ ကြောင်း အလွန်များလျှင် (၆ ကြောင်းထက်) စာတန်းက မြန်လွန်း ဖတ်မရ —
    #    အရွယ် နည်းနည်း ချုံ့ပြီး ကြောင်းရေ လျှော့သည် (spec ရဲ့ ၇၅% ထိ)。
    sz = size
    # ⚠️ ကြောင်း အလွန်များလျှင် အရွယ် ချုံ့သည် — **ချုံ့ထားတဲ့ အရွယ်ကို
    #    ပြန်ပေးရမည်**。 မပေးလျှင် track() က မူရင်းအရွယ်နဲ့ ဆွဲပြီး
    #    ဘောင် ကျော်ထွက်သည် (တကယ် ဖြစ်ခဲ့)。
    # ⚠️ ရှည်လျှင် အရွယ် ချုံ့တာကို **ရပ်လိုက်ပြီ** — ကတ် အရေအတွက် တိုးပေး
    #    ပြီးဖြစ်၍ မလိုတော့。 ချုံ့လျှင် စာတန်း အရွယ် တစ်ခုနဲ့တစ်ခု မတူဘဲ
    #    ၃၀px ↔ ၄၄px ကြား ခုန်နေသည် (N5 က အမြဲ တစ်အရွယ်တည်း)。
    if len(ls) > 14:
        while sz > int(size*0.86) and len(ls) > 12:
            sz -= 3; ls = wrap(c["text"], sz, maxw, MW, font)
    # ⚠️ **ဘောင် မကျော်စေရ** — မြန်မာစကားလုံး တစ်လုံးတည်းက `maxw` ထက်
    #    ရှည်လျှင် wrap က ခွဲလို့ မရ (စကားလုံးအလယ် မပိုင်းရ) ⇒ ကြောင်းက
    #    ဘောင်ကျော်ပြီး cttext က ဖြတ်ပစ်သည်。 ⇒ အဲဒီကတ်အတွက်သာ ချုံ့သည်。
    HARD = int(maxw/0.63*0.90) if maxw else 0        # ≈ ဘောင်၏ ၉၀%
    if HARD:
        for _ in range(12):
            if max((MW(x, sz, font) for x in ls), default=0) <= HARD: break
            sz -= 4
            if sz < int(size*0.55): break
            ls = wrap(c["text"], sz, maxw, MW, font)
    dur = max(0.4, c["end"]-c["start"])
    groups = [ls[i:i+max_lines] for i in range(0, len(ls), max_lines)]
    # ⚠️ `hold` ကို **ကတ်ရဲ့ အချိန်ကို ဖြတ်ပြီး ကန့်သတ်၍ မရ** — ဖြတ်လိုက်လျှင်
    #    ကျန်အချိန်မှာ စာတန်း **လုံးဝ မရှိ**တော့ဘူး。 ASR က ၁၀s+ segment
    #    ပေးတတ်၍ ဗီဒီယိုရဲ့ ၂၀% မှာ စာတန်း ပျောက်ခဲ့သည် (Zin: "ဗီဒီယို
    #    တစ်ပုဒ်လုံး မထိုးထားဘူး")。
    #    ⇒ ရှည်လျှင် **ကတ် အရေအတွက် တိုးပေး** (တစ်ကြောင်းစီ ခွဲ) ပြီး
    #      အချိန်ကို အချိုးကျ ခွဲသည် — ကွက်လပ် လုံးဝ မကျန်စေရ。
    if len(groups) and dur/len(groups) > hold and max_lines > 1:
        groups = [ls[i:i+1] for i in range(len(ls))]
    tot = sum(sum(len(x) for x in g) or 1 for g in groups)
    out=[]; pos=c["start"]
    for g in groups:
        w = (sum(len(x) for x in g) or 1)/tot
        # ⚠️ ကတ်တစ်ခုကို **ဘယ်လောက်ပဲ ကြာကြာ မထားရ**。 ASR က စာပိုဒ်လုံး
        #    တစ်ခုတည်း ပေးတတ်သည် (segment တစ်ခု ၂၁.၄s · ၁၀.၇s — တကယ်
        #    ဖြစ်ခဲ့)。 အဲဒါကို ကတ်တစ်ခုအဖြစ် ချလျှင် စာတန်းက ဆယ်စက္ကန့်
        #    ကျော် ရပ်နေပြီး ပြောနေတဲ့ စကားနှင့် လုံးဝ မကိုက်တော့ဘူး。
        d = max(0.45, dur*w)
        out.append((g, pos, pos+d, sz)); pos += d
    if out:                         # ⚠️ segment ရဲ့ အဆုံးထိ ဖြည့်ရမည်
        g, a, _b, z = out[-1]; out[-1] = (g, a, max(_b, c["end"]), z)
    return out

def _word_text(text, ws):
    """card text = the original substring covering these words, so the
    caption keeps the transcript's own spacing (Burmese words are often
    written without spaces). Falls back to joining the words."""
    pos, a, b = 0, None, None
    for w, _s, _e in ws:
        i = text.find(w, pos)
        if i < 0: return "".join(x[0] for x in ws) if not any(" " in x[0] for x in ws) else " ".join(x[0] for x in ws)
        if a is None: a = i
        pos = b = i + len(w)
    return text[a:b].strip()

def word_cards(c, size, maxw, MW, font, hold=1.6, pause=0.28):
    """One-line cards split **only between words**, each starting on its first
    word's onset (short-916). Zin 2026-09-26: captions broke words apart and
    did not match the speech -- the char-share split in `cards()` guessed
    both. Returns the same tuples as `cards()`, or None without word timings."""
    ws = c.get("words") or []
    if len(ws) < 2: return None
    groups, cur = [], []
    for w in ws:
        if cur:
            t = _word_text(c["text"], cur + [w])
            gap = w[1] - cur[-1][2]
            if MW(t, size, font) > maxw or (w[2] - cur[0][1]) > hold or gap >= pause:
                groups.append(cur); cur = []
        cur.append(w)
    if cur: groups.append(cur)
    out = []
    for k, g in enumerate(groups):
        a = g[0][1]
        nxt = groups[k + 1][0][1] if k + 1 < len(groups) else None
        # end = last word + 0.45 s, never into the next card. Every card, not
        # only the last: v7 held "တစ်ခုတည်းအတွက်" 5 s through a pause because
        # the card ran until the next word started.
        b = g[-1][2] + 0.45
        if nxt is not None: b = min(b, nxt)
        else: b = min(max(b, g[-1][2]), c["end"] + 0.45)
        txt = _word_text(c["text"], g)
        sz = size
        # a single word wider than the line: shrink that card, never split it
        while MW(txt, sz, font) > maxw * 1.35 and sz > int(size * 0.6):
            sz -= 3
        if b - a >= 0.12:
            out.append(([txt], a, b, sz))
    return out or None

def concat_items(timed, blank, fade, faded, total=None, FSTEP=3):
    """[(a, b, png)] sorted -> [(png, dur)] for the ffmpeg concat list.
    Invariant: the running sum of durations is the real clock, so every
    shown card starts at max(a, previous end) -- never earlier. (Before
    2026-09-27 a gap <= 40 ms, or a card dropped after its blank, was lost
    from / double-counted in that sum and later cards burned up to 120 ms off.)"""
    items = []; t = 0.0
    for a, b, p in timed:
        if a > t + 0.04:
            items.append((blank, a - t)); t = a
        elif a > t:
            # too short for a blank: the previous card holds through it
            if items: items[-1] = (items[-1][0], items[-1][1] + (a - t))
            else: items.append((blank, a - t))
            t = a
        else:
            a = t
        if b - a < 0.12: continue
        f = min(fade, (b - a) * 0.45)
        st = f / FSTEP if FSTEP else 0
        # fade 0 = hard switch (short-916): no partial-alpha steps at all,
        # else each step still costs the 0.02 s concat minimum and drifts.
        for i in (range(1, FSTEP + 1) if f > 0.005 else ()):
            items.append((faded(p, i / float(FSTEP)), st))
        items.append((p, (b - a) - f))
        t = b
    if total and total > t: items.append((blank, total - t))
    return items

def cut_runs(runs, spans):
    """source speech runs -> cut timeline, split at every removed region
    (a card may never straddle a cut). Returns [(a, b)] on the output clock."""
    out = []; acc = 0.0
    for sa, sb in spans:
        for a, b in runs:
            x0, x1 = max(a, sa), min(b, sb)
            if x1 - x0 >= 0.02:
                out.append((round(acc + x0 - sa, 3), round(acc + x1 - sa, 3)))
        acc += sb - sa
    return sorted(out)

def cut_energy(db, spans, frame=0.02):
    """20 ms energy track (source) -> cut timeline, same frame size"""
    import numpy as np
    parts = [db[int(round(a / frame)):int(round(b / frame))] for a, b in spans]
    return np.concatenate(parts) if parts else np.array([])

def speech_cards(caps, runs, db, size, maxw, MW, font, max_dur=4.0, short=0.6,
                 merge_gap=0.35, dip_win=0.25, frame=0.02, min_piece=0.30,
                 trail=0.0, min_dur=0.0, bridge=0.0, max_lines=1):
    """Cards timed by the cut engine's speech runs, not by ASR word times
    (short-916 · Zin 2026-09-27: "on as the voice starts, off as it ends").

    - on = run start, off = run end (cut timeline). No caption over silence.
    - text = whole ASR words assigned to the run they overlap most (nearest run
      if none) -- R1: words are only ever kept or dropped, never edited.
    - a run < `short` s joins its closer neighbour when the gap < `merge_gap`.
    - a run group longer than `max_dur` s or wider than `maxw` px is split only
      between two words, at the lowest-energy 20 ms frame within `dip_win` of
      that word boundary (never inside a word); every piece >= `min_piece` s.
    Returns [dict(lines=[text], a, b, sz, kw)] sorted by time."""
    import numpy as np
    runs = [list(r) for r in runs if r[1] - r[0] > 0.02]
    if not runs: return []
    # words (cut timeline) with the caption they came from
    W = []
    for ci, c in enumerate(caps):
        for w in (c.get("words") or []):
            W.append((float(w[1]), float(w[2]), str(w[0]), ci))
    W.sort()
    # merge short runs into the nearer neighbour when the gap is small
    changed = True
    while changed and len(runs) > 1:
        changed = False
        for i, (a, b) in enumerate(runs):
            if b - a >= short: continue
            gl = a - runs[i - 1][1] if i > 0 else 9e9
            gr = runs[i + 1][0] - b if i + 1 < len(runs) else 9e9
            j = i - 1 if gl <= gr else i + 1
            if min(gl, gr) < merge_gap:
                lo, hi = min(i, j), max(i, j)
                runs[lo] = [runs[lo][0], runs[hi][1]]; del runs[hi]
                changed = True; break
    # assign words
    buckets = [[] for _ in runs]
    for ws, we, t, ci in W:
        ov = [max(0.0, min(we, b) - max(ws, a)) for a, b in runs]
        k = int(np.argmax(ov)) if max(ov) > 0 else \
            int(np.argmin([min(abs(ws - b), abs(we - a)) for a, b in runs]))
        buckets[k].append((ws, we, t, ci))
    def text_of(ws_):
        # keep the transcript's own spacing inside one caption
        out, cur, ci0 = [], [], None
        for w in ws_:
            if ci0 is not None and w[3] != ci0:
                out.append(_word_text(caps[ci0]["text"], [(x[2], x[0], x[1]) for x in cur])); cur = []
            cur.append(w); ci0 = w[3]
        if cur: out.append(_word_text(caps[ci0]["text"], [(x[2], x[0], x[1]) for x in cur]))
        return " ".join(x for x in out if x)
    def dip(t0, t1, lo, hi):
        """lowest-energy frame near the boundary [t0, t1], kept inside (lo, hi)"""
        a = max(lo + frame, min(t0, t1) - dip_win); b = min(hi - frame, max(t0, t1) + dip_win)
        if b <= a or len(db) == 0: return max(lo + frame, min(hi - frame, (t0 + t1) / 2))
        i0, i1 = int(a / frame), max(int(a / frame) + 1, int(b / frame))
        seg = db[i0:i1]
        return (i0 + int(np.argmin(seg))) * frame + frame / 2 if len(seg) else (t0 + t1) / 2
    cards = []
    for (ra, rb), ws_ in zip(runs, buckets):
        if not ws_: continue
        ws_.sort()
        pieces, cur = [], [ws_[0]]
        for w in ws_[1:]:
            t = text_of(cur + [w])
            if MW(t, size, font) > maxw or (w[1] - cur[0][0]) > max_dur:
                pieces.append(cur); cur = []
            cur.append(w)
        pieces.append(cur)
        # cuts in order, each piece >= min_piece: ASR word times clump, so two
        # independent dips could land 40 ms apart (a 0.00-0.04 s card, 2026-09-27).
        # No room -> that piece's words join the previous card (none dropped).
        # A join must still fit the line (2026-09-27: joining regardless of width
        # made 1765 px cards shrunk to 47 px). If it would not fit, the floor
        # relaxes to 0.30 s for that cut instead -- a short card beats tiny text.
        edges, kept = [ra], [pieces[0]]
        for nxt in pieces[1:]:
            fits = MW(text_of(kept[-1] + nxt), size, font) <= maxw
            c = None
            for mp in ((min_piece, 0.30) if not fits else (min_piece,)):
                lo, hi = edges[-1] + mp, rb - mp
                c = dip(kept[-1][-1][1], nxt[0][0], lo - frame, hi + frame) if hi > lo else None
                if c is not None and lo - 1e-6 <= c <= hi + 1e-6: break
                c = None
            if c is None:
                kept[-1] = kept[-1] + nxt; continue
            edges.append(c); kept.append(nxt)
        edges.append(rb); pieces = kept
        for i, pc in enumerate(pieces):
            txt = text_of(pc); sz = size
            lines = [txt]
            if MW(txt, sz, font) > maxw and max_lines >= 2:
                two = split_two(txt, MW, sz, font, maxw)   # syllable boundary, never mid-cluster
                if two: lines = two
            while max(MW(l, sz, font) for l in lines) > maxw and sz > int(size * 0.6):
                sz -= 3                       # still too wide: shrink
            kw = sorted({k for x in pc for k in (caps[x[3]].get("kw") or [])})
            cards.append(dict(lines=lines, a=round(edges[i], 3), b=round(edges[i + 1], 3), sz=sz, kw=kw,
                              **({"split": True} if len(lines) > 1 else {})))
    return settle(cards, trail=trail, min_dur=min_dur if max_lines >= 2 else 0.0, bridge=bridge,
                  size=size, maxw=maxw, MW=MW, font=font)

def settle(cards, trail=0.0, min_dur=0.0, bridge=0.0, size=None, maxw=None, MW=None, font=None):
    """Off-times after the voice (Zin 2026-09-27: speech-edge off read "too fast").
    - trail: the card stays `trail` s after its run ends (never past the next card)
    - bridge: a gap to the next card shorter than `bridge` s is held, not blanked
      (float('inf') = hold until the next card always)
    - min_dur: a card still shorter than this joins its closer neighbour
      (text kept whole and in order -- R1). On-times are never moved (G1)."""
    cards = [dict(c) for c in sorted(cards, key=lambda c: c["a"])]
    if not cards or (trail <= 0 and bridge <= 0 and min_dur <= 0): return cards
    for i, c in enumerate(cards):
        nxt = cards[i + 1]["a"] if i + 1 < len(cards) else float("inf")
        if nxt - c["b"] < bridge: c["b"] = nxt
        else: c["b"] = min(c["b"] + trail, nxt)
    if min_dur <= 0: return cards
    # Roll-up (2026-09-28): a card that has not been up for `min_dur` stays as
    # the top line while the next card enters underneath AT ITS OWN on-time.
    # Joining text into one earlier card instead showed words before they were
    # spoken, and pushing split points later made text lag the voice
    # (G13: 23 % of words outside their card, 34/81 cards > 0.3 s late).
    out = []
    for c in cards:
        p = out[-1] if out else None
        if (p is not None and not p.get("split") and not c.get("split")
                and abs(c["a"] - p["b"]) <= 0.05
                and c["a"] - p.get("_since", p["a"]) < min_dur - 1e-6):
            top = p["lines"][-1]
            out.append(dict(lines=[top, c["lines"][0]], a=c["a"], b=c["b"],
                            sz=min(p["sz"], c["sz"]),
                            kw=sorted(set(p.get("kw") or []) | set(c.get("kw") or [])),
                            _since=c["a"], _top_since=p.get("_since", p["a"])))
        else:
            d = dict(c); d["_since"] = c["a"]; out.append(d)
    for d in out:
        d.pop("_since", None); d.pop("_top_since", None)
    return out

MM_CONS = "\u1000-\u1021"
def syllables(txt):
    """Burmese syllable pieces (break before a consonant that is not stacked
    under a virama and not killed by an asat), Latin/digits kept as whole words.
    Joining the pieces gives the text back exactly."""
    import re
    out, cur = [], ""
    for i, ch in enumerate(txt):
        brk = False
        if cur:
            j = i + 1
            while j < len(txt) and txt[j] == "\u1037": j += 1     # dot-below may sit before the asat
            nxt = txt[j] if j < len(txt) else ""
            prv = txt[i - 1]
            if "\u1000" <= ch <= "\u1021" and prv != "\u1039" and nxt not in ("\u103a", "\u1039"):
                brk = True
            elif ch == " ":
                brk = True
            elif re.match(r"[A-Za-z0-9]", ch) and not re.match(r"[A-Za-z0-9]", prv):
                brk = True
        if brk: out.append(cur); cur = ""
        cur += ch
    if cur: out.append(cur)
    return out

def split_two(txt, MW, size, font, maxw):
    """one over-wide line -> two lines at the syllable boundary that best
    balances the widths (None if the text has no boundary)."""
    sy = syllables(txt)
    best = None
    for k in range(1, len(sy)):
        l1, l2 = "".join(sy[:k]).rstrip(), "".join(sy[k:]).lstrip()
        if not l1 or not l2: continue
        w1, w2 = MW(l1, size, font), MW(l2, size, font)
        if best is None or max(w1, w2) < best[0]:
            best = (max(w1, w2), [l1, l2])
    # the most balanced split; the caller shrinks if a line still overflows
    return best[1] if best and best[0] < MW(txt, size, font) else None

# particles that never start a chunk: they stay with the word before them
_PART = {"တဲ့", "တယ်", "ပါ", "မယ်", "ပြီး", "တော့", "နဲ့", "ရဲ့", "က", "ကို", "မှာ", "လို့",
         "သည်", "၏", "နော်", "ဘူး", "လဲ", "လား", "တွေ", "များ", "ရင်", "ဆို", "လည်း", "ပဲ",
         "စေ", "ပေး", "သွား", "ခဲ့", "ရ", "နိုင်", "ချင်", "ဖို့"}

def chunk_word(txt, size, maxw, MW, font):
    """An ASR "word" wider than the line (often a whole phrase with no spaces)
    -> chunks that fit, broken only where a Burmese word boundary (mmseg) AND a
    syllable boundary agree; particles stay with the word before them. Text is
    never changed (R1). Returns [(text, syllables)] -- one chunk if it fits."""
    if MW(txt, size, font) <= maxw: return [(txt, max(1, len(syllables(txt))))]
    sy = syllables(txt)
    sb = set(); pos = 0
    for p in sy[:-1]: pos += len(p); sb.add(pos)
    try:
        import mmseg as _MS
        ws = _MS.words(txt)
    except Exception:
        ws = None
    if ws and "".join(ws) == txt.replace(" ", "") and " " not in txt:
        wb = set(); pos = 0
        for w in ws[:-1]: pos += len(w); wb.add(pos)
        cut = sorted(wb & sb)
    else:
        cut = sorted(sb)                     # fallback: syllable boundaries only
    units, prev = [], 0
    for c in cut + [len(txt)]:
        units.append(txt[prev:c]); prev = c
    merged = []
    for u in units:
        punct = u.strip() in ("။", "၊") or not u.strip()
        is_p = punct or u.strip() in _PART
        if merged and (punct or (is_p and MW(merged[-1] + u, size, font) <= maxw)):
            merged[-1] += u                  # particle stays with its word while the line fits
        else:
            merged.append(u)
    chunks = []
    for u in merged:
        if chunks and MW(chunks[-1] + u, size, font) <= maxw: chunks[-1] += u
        else: chunks.append(u)
    return [(c, max(1, len(syllables(c)))) for c in chunks]

def word_pop_cards(caps, runs, db, size, maxw, MW, font, snap=0.10, frame=0.02, min_card=0.15,
                   min_read=0.40, read_floor=0.90):
    """One card per ASR word, like the references (r1/r3: one word per card,
    2.3 cards/s, the card is always the word being said now). Zin 2026-09-28:
    "the subtitle must be exactly on the voice".

    - first word of a speech run: on = run start (acoustic, exact)
    - later words: Gemini start snapped to the quietest 20 ms frame within
      +-`snap` s (the syllable boundary), kept monotonic
    - off = next word's on inside the run; the last word ends at the run end
    - words are never split, joined across runs, changed or reordered (R1)"""
    import numpy as np
    runs = [tuple(r) for r in runs if r[1] - r[0] > 0.02]
    W = []
    for ci, c in enumerate(caps):
        for w in (c.get("words") or []):
            W.append((float(w[1]), float(w[2]), str(w[0]), ci))
    W.sort()
    buckets = [[] for _ in runs]
    for ws, we, t, ci in W:
        ov = [max(0.0, min(we, b) - max(ws, a)) for a, b in runs]
        if not ov: continue
        k = int(np.argmax(ov)) if max(ov) > 0 else \
            int(np.argmin([min(abs(ws - b), abs(we - a)) for a, b in runs]))
        buckets[k].append((ws, we, t, ci))
    def snap_to(t, lo, hi):
        a = max(lo, t - snap); b = min(hi, t + snap)
        if b <= a or len(db) == 0: return min(hi, max(lo, t))
        i0, i1 = int(a / frame), max(int(a / frame) + 1, int(b / frame))
        seg = db[i0:i1]
        return (i0 + int(np.argmin(seg))) * frame if len(seg) else t
    cards = []
    for (ra, rb), ws_ in zip(runs, buckets):
        if not ws_: continue
        ws_.sort()
        ons = [ra]
        for w in ws_[1:]:
            lo = ons[-1] + min_card; hi = rb - min_card
            if hi <= lo: ons.append(None); continue
            ons.append(snap_to(min(hi, max(lo, w[0])), lo, hi))
        # words that found no room join the previous card (text kept whole)
        groups = []
        for w, on in zip(ws_, ons):
            if on is None and groups: groups[-1][0].append(w)
            else: groups.append([[w], on])
        for gi, (gw, on) in enumerate(groups):
            off = groups[gi + 1][1] if gi + 1 < len(groups) else rb
            txt = " ".join(x[2] for x in gw)
            kw = sorted({k for x in gw for k in (caps[x[3]].get("kw") or [])})
            ch = chunk_word(txt, size, maxw, MW, font)
            # time the chunks by syllable share, snapped to a dip; each >= min_card
            tot = float(sum(n for _, n in ch)); t0 = on; acc = 0
            starts = [on]
            for _, n in ch[:-1]:
                acc += n
                lo = starts[-1] + min_card; hi = off - min_card
                if hi <= lo: starts.append(None); continue
                starts.append(snap_to(min(hi, max(lo, on + (off - on) * acc / tot)), lo, hi))
            pieces = []
            for (ct, n), st in zip(ch, starts):
                if st is None and pieces: pieces[-1][0] += ct
                else: pieces.append([ct, st])
            for pi, (ct, st) in enumerate(pieces):
                en = pieces[pi + 1][1] if pi + 1 < len(pieces) else off
                sz = size
                while MW(ct, sz, font) > maxw and sz > int(size * 0.6): sz -= 3
                cards.append(dict(lines=[ct], a=round(st, 3), b=round(en, 3), sz=sz, kw=kw, _run=ra))
    # readability (Zin 2026-09-28 "a little too fast"): 37 % of cards were up
    # < 0.35 s. A card shorter than `min_read` joins the NEXT word of the same
    # run (on-time stays the first word's -> still on the voice) while the line
    # fits; else the previous card. Never across a silence.
    i = 0
    while i < len(cards):
        c = cards[i]
        if c["b"] - c["a"] >= min_read - 1e-6: i += 1; continue
        nx = cards[i + 1] if i + 1 < len(cards) and cards[i + 1]["_run"] == c["_run"] else None
        pv = cards[i - 1] if i > 0 and cards[i - 1]["_run"] == c["_run"] else None
        # MyanmarBlack 80 px is wide: two words overflow 778 px in 21 of the 24
        # blocked joins (insp render). A joined card may shrink to `read_floor`
        # of the base size (80 -> 72: resolves 8 of them); below that the size
        # jump between cards shows, so the short card stays.
        def fits(t, sz):
            lo = int(size * read_floor)
            while sz >= lo:
                if MW(t, sz, font) <= maxw: return sz
                sz -= 2
            return None
        s2 = nx is not None and fits(c["lines"][0] + " " + nx["lines"][0], min(c["sz"], nx["sz"]))
        if s2:
            cards[i] = dict(lines=[c["lines"][0] + " " + nx["lines"][0]], a=c["a"], b=nx["b"],
                            sz=s2, kw=sorted(set(c["kw"]) | set(nx["kw"])), _run=c["_run"])
            del cards[i + 1]; continue                       # re-check the joined card
        s2 = pv is not None and fits(pv["lines"][0] + " " + c["lines"][0], min(c["sz"], pv["sz"]))
        if s2:
            cards[i - 1] = dict(lines=[pv["lines"][0] + " " + c["lines"][0]], a=pv["a"], b=c["b"],
                                sz=s2, kw=sorted(set(c["kw"]) | set(pv["kw"])), _run=c["_run"])
            del cards[i]; i = max(0, i - 1); continue
        i += 1
    for c in cards: c.pop("_run", None)
    return cards

def plan(segs, spans, max_lines=2):
    """ဖြတ်ပြီးနောက် အချိန်သို့ စာတန်းများကို ပြောင်းသည်。

    ⚠️ ဖြတ်တောက်ပြီးလျှင် အချိန်တွေ ရွှေ့သွားသည် — မူရင်းအချိန်ကို
       ကျန်ရှိသော span များပေါ် ပြန်တွက်ရမည်။ မတွက်လျှင် စာတန်းက
       ဗီဒီယိုနှင့် လွဲသွားသည်。
    """
    # မူရင်းအချိန် → ဖြတ်ပြီးအချိန် map
    def remap(t):
        acc=0.0
        for a,b in spans:
            if t < a: return None            # ဖြတ်ပစ်လိုက်သော အပိုင်း
            if t <= b: return acc + (t-a)
            acc += b-a
        return None
    out=[]
    for s in segs:
        a=remap(s["start"]); b=remap(s["end"])
        if a is None or b is None or b-a < 0.25: continue
        e = dict(text=s["text"], start=round(a,2), end=round(b,2))
        # word timings (Gemini ASR `words`) -> cut timeline, for word cards
        ws = []
        for w in (s.get("words") or []):
            try: w0, w1 = remap(float(w["s"])), remap(float(w["e"]))
            except (KeyError, TypeError, ValueError): continue
            t = str(w.get("w") or "").strip()
            if t and w0 is not None and w1 is not None and w1 >= w0:
                ws.append((t, round(w0, 3), round(w1, 3)))
        if ws: e["words"] = ws
        out.append(e)
    return out

def track(caps, out, work, W, H, size, fill, font, fallback, bot,
          ct, MW, fps=30, total=None, stroke=None, stroke_w=0.0, hold=4.0,
          gap_pct=0.18, fade=0.14, hide=None, log=None, wide=0.86,
          plate=None, max_lines=2, accent=None, kw_box=None, by_word=False,
          cards_pre=None, pop=0.0):
    """စာတန်းများကို alpha overlay ဗီဒီယို တစ်ခု အဖြစ် ဆောက်သည်。

    ⚠️ ကြောင်းနှစ်ကြောင်း အကွာအဝေးကို **ink ဖြတ်ပြီးမှ** သတ်မှတ်ရသည်。
       cttext ရဲ့ canvas က size×2.2 ဖြစ်၍ အတိုင်းအတာအတိုင်း ထပ်လျှင်
       ကြားက ၀.၆၅×size လောက် ကွာသွားသည် — N5 reference ထက် ၃ ဆကျော်
       ကွာပြီး Zin က "အကွာအဝေးက အရမ်းဝေးလွန်းနေတယ်" ဟု ပြောခဲ့သည်。
       ⇒ ကြောင်းတစ်ခုချင်းကို alpha bbox အတိုင်း ဖြတ်ပြီး `gap_pct×size`
         ဖြင့် ထပ်သည်。
    ⚠️ `hide` — ဂရပ်ဖစ် ပေါ်နေချိန် စာတန်း **ဖျောက်**ရသည် (စာနှစ်ထပ် မဖြစ်စေရန်)。
    ⚠️ `fade` — ကတ်တိုင်း alpha ၃ ဆင့်ဖြင့် ပွင့်လာသည် (ရုတ်တရက် မပေါ်စေရန်)。
    ⚠️ `plate` — `dict(alpha, pad_x, pad_y, radius)` ပေးလျှင် စာလုံးနောက်မှာ
       **အမှောင် အကွက်** ခံသည်。 နောက်ခံ လင်းလွန်းလျှင် အဖြူစာ ပျောက်သည် —
       `IKKI_Premium_v2.mp4` ကို တိုင်းရာ နမူနာ ၁၃ နေရာလုံး WCAG ၃:၁
       မမီခဲ့ (၂.၁၃–၂.၇၅ · နောက်ခံ RGB ~၁၇၆)。 `None` ဆိုလျှင် ယခင်အတိုင်း
       — အခြား ပုံစံများ မထိခိုက်စေရန်。
    ⚠️ အကွက်က **ink ရဲ့ အကျယ်အတိုင်း**သာ ဖြစ်ရမည်、ဘောင်အပြည့် ဘားက
       ဈေးပေါဆန်သည်。
    """
    os.makedirs(work, exist_ok=True)
    band_h = int(size*2.2)*2
    blank = os.path.join(work, "_blank.png")
    ct(dict(text=" ", font=font, fallback=fallback, size=size, w=W, h=band_h,
            fill="#00000000", unit="cluster", align="center",
            frames=[{"out":blank, "words":[]}]))

    def _acc(txt, kws):
        """keyword colour runs for one rendered line -- UTF-16 offsets for cttext.
        A keyword split across two lines is skipped rather than half-coloured."""
        out = []
        for w in (kws or []):
            i = txt.find(w)
            if i < 0: continue
            u = lambda x: len(x.encode("utf-16-le")) // 2
            out.append(dict(s=u(txt[:i]), n=u(w), fill=accent))
        return out

    def _sp(txt, sz, outp, h=None, kws=None):
        d = dict(text=txt, font=font, fallback=fallback, size=sz, w=W, h=h or band_h,
                 fill=fill, unit="cluster", align="center",
                 # ⚠️ အရိပ်က **ဖတ်ရလွယ်မှုအတွက်** — အလှအတွက် မဟုတ်。
                 #    ၂၀၂၆-၀၉-၂၀ တိုင်းချက်: အလင်းများသော B-roll ပေါ်မှာ
                 #    စာလုံး/နောက်ခံ ကွာခြားမှု **၃.၄၀:၁** သာ ရှိပြီး ဖတ်ရလွယ်သော
                 #    စံ (၄.၅:၁) အောက် ကျနေသည် (stroke မပါသော style များ)。
                 #    ⇒ alpha ၀.၅၅→၀.၇၂ · blur ၀.၁၁→၀.၁၄ (ဒီဇိုင်း မပြောင်း၊
                 #    အောက်ခံ မှောင်ပေးရုံ)。 stroke ရှိသော style မှာ သက်ရောက်မှု နည်း。
                 shadow=dict(dx=0, dy=max(1, int(sz*0.055)), blur=max(2, int(sz*0.14)),
                             alpha=0.72),
                 frames=[{"out":outp, "words":[]}])
        if accent and kws:
            _a = _acc(txt, kws)
            if _a: d["accents"] = _a
        if stroke and stroke_w:
            d["stroke"] = stroke; d["strokeWidth"] = max(2, int(sz*stroke_w))
        return d

    try:
        # ⚠️ `ImageDraw` ကိုပါ ဒီမှာပဲ ယူရမည် — plate ဆွဲရာမှာ လိုသည်。
        #    ဖိုင်ထိပ်မှာ မယူဘဲ ဒီထဲ ထားရခြင်းက PIL မရှိလျှင်လည်း
        #    module က import ရနေစေရန် (fallback လမ်းကြောင်း ရှိသည်)。
        from PIL import Image, ImageDraw
        import numpy as _np
    except Exception:
        Image = ImageDraw = None

    def _ink(p, pad=3):
        """PNG ကို alpha bbox အတိုင်း ဖြတ်သည် (ဒေါင်လိုက်သာ)。"""
        if Image is None: return None
        im = Image.open(p).convert("RGBA")
        a = _np.asarray(im)[:, :, 3]
        ys = _np.nonzero(a.max(axis=1) > 6)[0]
        if len(ys) == 0: return None
        y0 = max(0, int(ys.min())-pad); y1 = min(im.size[1], int(ys.max())+1+pad)
        return im.crop((0, y0, im.size[0], y1))

    def _stack(parts, sz, outp):
        """ink ဖြတ်ပြီး gap ဖြင့် ထပ် → band_h ထဲ အောက်ခြေ ကပ်ထား。"""
        if Image is None: return False
        ims = [_ink(q) for q in parts]
        ims = [x for x in ims if x is not None]
        if not ims: return False
        gap = int(sz*gap_pct)
        tot = sum(x.size[1] for x in ims) + gap*(len(ims)-1)
        canvas = Image.new("RGBA", (W, band_h), (0,0,0,0))
        y0 = band_h - tot
        if y0 < 0: y0 = 0
        if plate:
            # ⚠️ ink ရဲ့ **အလျားလိုက် နယ်နိမိတ်** ကို အရင် ရှာရသည် —
            #    `_ink()` က ဒေါင်လိုက်သာ ဖြတ်သဖြင့် ပုံက ဘောင်အပြည့် ကျန်နေသည်。
            x0, x1 = W, 0
            for x in ims:
                a = _np.asarray(x)[:, :, 3]
                cols = _np.nonzero(a.max(axis=0) > 6)[0]
                if len(cols):
                    x0 = min(x0, int(cols.min())); x1 = max(x1, int(cols.max()))
            if x1 > x0:
                px = int(plate.get("pad_x", sz * 0.45))
                py = int(plate.get("pad_y", sz * 0.22))
                rad = int(plate.get("radius", sz * 0.28))
                al = int(max(0.0, min(1.0, plate.get("alpha", 0.62))) * 255)
                box = (max(0, x0 - px), max(0, y0 - py),
                       min(W, x1 + px), min(band_h, y0 + tot + py))
                lay = Image.new("RGBA", (W, band_h), (0, 0, 0, 0))
                ImageDraw.Draw(lay).rounded_rectangle(box, radius=rad,
                                                      fill=(0, 0, 0, al))
                canvas.alpha_composite(lay)
        y = y0
        for x in ims:
            canvas.alpha_composite(x, (0, y)); y += x.size[1] + gap
        canvas.save(outp)
        return True

    def _boxit(q, txt, kws, sz, r):
        """draw a rounded box behind the first keyword found in this line"""
        if Image is None or not isinstance(r, dict): return
        w = next((x for x in kws if x in txt), None)
        if not w: return
        pre = txt[:txt.index(w)]
        try:
            m = ct(dict(text=txt, font=font, fallback=fallback, size=sz, w=W,
                        h=line_h, fill="#FFFFFF", frames=[], measure=[pre or " ", w]))
            wp = m[0] if pre else 0
            wk = m[1]
        except Exception:
            return
        ox = int(r.get("ox", 0)); y0 = int(r.get("iy0", 0)); y1 = int(r.get("iy1", line_h))
        px, py = int(sz * 0.16), int(sz * 0.10)
        box = (max(0, ox + wp - px), max(0, y0 - py),
               min(W, ox + wp + wk + px), min(line_h, y1 + py))
        im = Image.open(q).convert("RGBA")
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        hx = kw_box.lstrip("#")
        col = tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
        ImageDraw.Draw(lay).rounded_rectangle(box, radius=int(sz * 0.14), fill=col)
        lay.alpha_composite(im)
        lay.save(q)

    _fcache = {}
    def _popped(p, k):
        """pop-in step (r1 word pop): the card at scale 1 + (pop-1)(1-k)^2,
        scaled about its ink centre, full opacity."""
        if Image is None: return p
        q = _fcache.get(("pop", p, k))
        if q: return q
        q = p[:-4] + f"_p{int(k*100):03d}.png"
        if not os.path.exists(q):
            im = Image.open(p).convert("RGBA"); a = _np.asarray(im)[:, :, 3]
            ys, xs = _np.nonzero(a > 8)
            sc = 1.0 + (float(pop) - 1.0) * (1.0 - k) ** 2
            if len(xs) == 0 or sc <= 1.001:
                im.save(q)
            else:
                cx, cy = (xs.min() + xs.max()) / 2.0, (ys.min() + ys.max()) / 2.0
                inv = 1.0 / sc
                out = im.transform(im.size, Image.AFFINE,
                                   (inv, 0, cx - cx * inv, 0, inv, cy - cy * inv), Image.BICUBIC)
                out.save(q)
        _fcache[("pop", p, k)] = q
        return q

    def _faded(p, k):
        """alpha ကို k ဆ လျှော့ထားသော မိတ္တူ (fade-in ထစ်)。"""
        if pop and pop > 1.0: return _popped(p, k)
        if Image is None: return p
        q = _fcache.get((p, k))
        if q: return q
        q = p[:-4] + f"_f{int(k*100):03d}.png"
        if not os.path.exists(q):
            im = Image.open(p).convert("RGBA")
            a = _np.asarray(im).copy()
            a[:, :, 3] = (a[:, :, 3].astype(_np.float32)*k).astype(_np.uint8)
            Image.fromarray(a, "RGBA").save(q)
        _fcache[(p, k)] = q
        return q

    # ⚠️ **ကြောင်းအကျယ်ကို ကျဉ်းထားရမည်** — N5 reference ကို တိုင်းတော့
    #    ကြောင်းတစ်ခုက ဘောင်ရဲ့ ၀.၄၈ သာ ကျယ်ပြီး **တစ်ကြောင်းတည်း**များသည်;
    #    စာလုံးက ၀.၁၂၄·H (၁၄၄၀ ဘောင်တွင် ၁၇၈px) ရှိသည်。
    #    ကျယ်ကျယ် (၀.၈၆) ထားလျှင် ဝါကျရှည်က ၂ ကြောင်း ဖြစ်ပြီး စာလုံး
    #    ချုံ့ရသဖြင့် **N5 ရဲ့ တစ်ဝက်** သာ ကြီးသည် (Zin: "လုံးဝ အဆင်မပြေဘူး")。
    maxw = int(W*wide)
    line_h = int(size*2.2)
    timed=[]; k=0
    # cards_pre (short-916 speech timing): one unit per card, already timed
    # WARN `is not None` let an EMPTY list through, and an empty unit list is a
    #    video with NO CAPTIONS AT ALL. That happened for real: an approve
    #    rebuilt each segment as text/start/end only, word_pop_cards() got no
    #    word timings, returned [], and every caption silently vanished.
    #    The producers were fixed (2026-09-28, 268319c), but the class stays
    #    open while the consumer accepts []. So the fallback lives HERE, at the
    #    one place that decides, not at each call site: empty pre-timed cards
    #    means "nothing pre-timed", never "render nothing".
    if cards_pre is not None and not cards_pre and caps:
        if log:
            log("  ⚠️ စာတန်း · cards_pre ဗလာ — caps သို့ ပြန်ကျ (စာတန်း မပျောက်စေရ)")
        cards_pre = None
    _units = ([(dict(kw=x.get("kw")), [(x["lines"], x["a"], x["b"], x["sz"])]) for x in cards_pre]
              if cards_pre else [(c, None) for c in caps])
    for c, _pre in _units:
        _wc = None if _pre is not None else (word_cards(c, size, maxw, MW, font, hold=hold) if by_word else None)
        for lines, a, b, sz in (_pre or _wc or cards(c, size, maxw, MW, font, max_lines=max_lines, hold=hold)):
            parts=[]
            for j,txt in enumerate(lines):
                q = os.path.join(work, f"c{k:04d}_{j}.png")
                _kw = c.get("kw")
                # kw_box: keyword stays white and sits on a solid box (ref r4
                # "They'll [change] the") -- otherwise it is recoloured text.
                _r = ct(_sp(txt, sz, q, h=line_h, kws=None if kw_box else _kw))
                if kw_box and _kw:
                    _boxit(q, txt, _kw, sz, _r)
                parts.append(q)
            p = os.path.join(work, f"c{k:04d}.png"); k += 1
            if not _stack(parts, sz, p):
                # ⚠️ PIL မရလျှင် ယခင်နည်း (ဘောင်အပြည့် ထပ်) ကို ပြန်သုံးသည်
                if len(parts) == 1:
                    subprocess.run(["ffmpeg","-v","error","-y","-i",parts[0],
                        "-vf",f"pad={W}:{band_h}:0:{band_h-line_h}:color=black@0",
                        "-frames:v","1","-pix_fmt","rgba",p],check=True)
                else:
                    subprocess.run(["ffmpeg","-v","error","-y","-i",parts[0],"-i",parts[1],
                        "-filter_complex",
                        f"[0][1]vstack=2,pad={W}:{band_h}:0:{band_h-line_h*2}:color=black@0",
                        "-frames:v","1","-pix_fmt","rgba",p],check=True)
            timed.append([float(a), float(b), p])

    # ── ဂရပ်ဖစ် ပေါ်နေချိန် ဖျောက် ──
    if hide:
        cut=[]
        for a,b,p in timed:
            segs=[(a,b)]
            for ha,hb in hide:
                nx=[]
                for x,y in segs:
                    if hb <= x or ha >= y: nx.append((x,y)); continue
                    if x < ha: nx.append((x,ha))
                    if hb < y: nx.append((hb,y))
                segs=nx
            # the 0.20 s floor is for slivers a graphic left behind -- a card no
            # graphic touches keeps its own length (word-pop cards are 0.14-0.2 s;
            # the old rule dropped them with no graphic in sight, 2026-09-28)
            touched = len(segs) != 1 or segs[0] != (a, b)
            for x,y in segs:
                if y-x > 0.20 or (not touched and y-x > 0.0): cut.append([x,y,p])
        n_hid = len(timed)-len(cut)
        if log and n_hid: log(f"  စာတန်း · ဂရပ်ဖစ်ပေါ်လို့ ဖျောက် {n_hid} ကတ်")
        timed = cut
    timed.sort(key=lambda x: x[0])

    items = concat_items(timed, blank, fade, _faded, total)
    if not items: return None
    lst = os.path.join(work, "caps.txt")
    with open(lst, "w") as f:
        for p,d in items:
            f.write("file '%s'\nduration %.3f\n" % (p.replace("'","'\\''"), max(0.02,d)))
        f.write("file '%s'\n" % items[-1][0].replace("'","'\\''"))
    subprocess.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",lst,
        "-r",str(fps),"-c:v","qtrle","-pix_fmt","argb",out], check=True)
    return out
