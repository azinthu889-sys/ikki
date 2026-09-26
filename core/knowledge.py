#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · **Knowledge Sharing engine** (ZIN JAPAN LIFE ပုံစံ)。

Zin ၂၀၂၆-၀၉-၂၆: 「Knowledge Sharing engine ကို reference အသစ်နဲ့ ဆောက် ·
infographic ပါ ထည့်」 → 「@zinjapanlife9742 ထဲက knowledge sharing
ဗီဒီယိုတွေကိုပဲ reference」。 တိုင်းချက် အပြည့် —
`/Volumes/a/ikki_refs/knowledge/measure/KNOWLEDGE_STYLE_zjl.md`
(ref ၈ ပုဒ် · 「အသစ် ၄ ပုဒ်」 wYuK · VD71 · Ih7G · aW32 က ပစ်မှတ်)。

ဒီ module က ဘာလုပ်လဲ
  1. `plan()`   — AI က **အဓိပ္ပာယ်** (panel · ဂဏန်း · ဂျပန်စကားလုံး · ✕) ကိုသာ
                  ပေးသည်。 **timeline ကို ဒီကုဒ်က** တည်ဆောက်သည် (headtop
                  planner နဲ့ စည်းမျဉ်းတူ — AI က အချိန် မချရ)。
  2. `bake()`   — cutaway (B-roll montage · paper panel) ကို ဖြတ်ပြီးသား
                  ဗီဒီယိုထဲ **segment အလိုက် အစားထိုး**ပြီး ပြန်ဆက်သည်。
                  ⚠️ overlay input အဖြစ် မထည့်ရ — worker ရဲ့ `bmov[:10]`
                  ကန့်သတ်ချက်နဲ့ ffmpeg input ကန့်သတ်ချက်ကြောင့် ၈ မိနစ်
                  ဗီဒီယိုရဲ့ cutaway ~၂၀ ခုထဲ ၁၀ ခုပဲ ကျန်မည်。
  3. `checks()` — QC。

⚠️ **shared layer ကို မထိရ** (Zin ရဲ့ Z1 စည်းမျဉ်း · ၂၀၂၆-၀၉-၂၆):
   planner.py · dress.py · gfxcat.py · sfxpol.py · motionkit — import
   လုပ်ပြီး **ခေါ်ရုံ**သာ。 ဒီ engine ရဲ့ ကိန်းအားလုံး ဒီဖိုင်ထဲမှာ。
"""
import json
import math
import os
import re
import subprocess
import time
import urllib.error
import urllib.request

try:
    import broll as BR
    import gemguard as G
    import slide as SL
except ImportError:                                   # API က package အဖြစ်
    from core import broll as BR
    from core import gemguard as G
    from core import slide as SL

MODEL = os.environ.get("IKKI_GEMINI_MODEL", "gemini-flash-latest")

# ══ တိုင်းထားသော ကိန်းများ ═════════════════════════════════════
# ref 「အသစ် ၄ ပုဒ်」 (KNOWLEDGE_STYLE_zjl.md §1):
#   cutaway အချိန်  34 · 38 · 42 · 34 %
#   အကြိမ်/min     1.5 · 3.4 · 1.8 · 1.7
#   ကြာချိန် p50    12.5 · 5.8 · 6.0 · 5.0 s   (montage — shot များစွာ)
#   talk ကြား p50   13 · 8 · 23 · 11 s  ·  max 56 · 30 · 60 · 203 s
# ⚠️ **ပစ်မှတ် = coverage၊ ceiling မဟုတ်** ([[ikki-cutaway-engine]] —
#    budget ကို ceiling အဖြစ်သာ ထားလျှင် ၁ ခုပဲ ထွက်ခဲ့)。 scheduler က
#    အချိန်တိုင်းမှာ 「ယခုထိ ရသင့်သော cutaway အချိန်」နဲ့ နှိုင်းပြီး ချသည်。
SPEC = dict(
    share=0.34,            # ပစ်မှတ် (ref 0.34–0.42 ရဲ့ အောက်ခြေ — library က ကန့်သတ်)
    share_max=0.45,        # ကျော်လျှင် ပြောသူ ပျောက် ⇒ QC ပိတ်
    share_min=0.15,        # အောက်ကျလျှင် သတိပေးသာ (library ချို့တဲ့မှု)
    gap_min=6.0,           # cutaway ၂ ခုကြား ပြောသူ အနည်းဆုံး (ref p25 5–12)
    gap_max=60.0,          # ref 「အသစ်」 ၃/၄ ရဲ့ max ≤ 60s
    broll_len=(4.0, 9.0),  # event တစ်ခု (montage) — ref p25–p75 4.0–12.5
    clip_len=(2.4, 5.0),   # montage ထဲ shot တစ်ခု
    panel_len=(4.0, 8.0),  # paper panel — ref hrms/qUCE 4.5–7.0
    num_len=(2.2, 3.6),    # 3D ဂဏန်း (ပြောသူပေါ်)
    jp_len=(2.8, 4.5),     # ဂျပန် ribbon
    cold=(8.0, 30.0),      # cold-open montage (ref 20–40s · ၈ မိနစ်ဗီဒီယိုမှာ)
    cold_frac=0.06,
    cold_min_dur=90.0,     # ဒီထက် တိုလျှင် cold open မလုပ်
    tail=5.0,              # နောက်ဆုံး ၅s ပြောသူ (worker ရဲ့ broll_tail နဲ့ တူ)
    panel_per_min=0.8,     # ref hrms 0.75 · qUCE 1.1 /min
    panel_gap=20.0,        # panel ၂ ခုကြား အနည်းဆုံး (ref hrms 0:29→1:08→1:21 · ~13–40s)
)

# paper panel (hrms 0:31 · qUCE 1:30 · 854/640px frame ကနေ တိုင်း)
PAPER_W = 0.489                        # ဘယ်ဘက် ဘောင်ကျယ် (ref 0.489 နှစ်ခုလုံး)
PAPER_RGB = (238, 234, 220)            # hrms ပျမ်းမျှ #EEEADC (qUCE #F5F5D8)
PAPER_INK = (24, 22, 20)
SPEAKER_ZOOM = 1.10                    # ညာဘက်တစ်ဝက်ထဲ ပြောသူ (မျက်စိဖြင့် ~1.1×)
PAPER_TXT = 0.052                      # စာလုံး em ÷ H (ink span 2 ကြောင်း 0.106–0.115)

KINDS = ("panel", "number", "jp", "no", "none")

# ══ AI — အဓိပ္ပာယ်သာ ══════════════════════════════════════════
NPROMPT = """မြန်မာ knowledge-sharing ဗီဒီယိုတစ်ခု၏ စာတမ်း (စာကြောင်း နံပါတ်ပါ) ပေးထားသည်။

ပြောသူက ပရိသတ်ကို အကြံဉာဏ်/အသိပညာ ပေးနေသည်။ အောက်ပါ ဂရပ်ဖစ် အမျိုးအစား
ပေါ်သင့်သော စာကြောင်းများကိုသာ ရွေးပါ။

- "panel"  : ဗီဒီယိုရဲ့ **အဓိက အချက်** (ခေါင်းစဉ်ခွဲ · အရေးကြီးသော သဘောတရား ·
             သတိပေးချက်)。 `text` = ဖန်သားပြင်ပေါ် ရေးမည့် စကားစု (မြန်မာ ၄၀ လုံးအောက်
             · ပြောသူ၏ စကားကို တိုတိုရှင်းရှင်း)。 အများဆုံး %d ခု · တစ်ခုနှင့်တစ်ခု
             ကွာကွာ ဖြန့်ပါ
- "number" : စာကြောင်းမှာ **အရေးကြီးသော ဂဏန်း** ပါသည် (နှစ် · ရာခိုင်နှုန်း · ယန်း ·
             အရေအတွက်)。 `num` = ဂဏန်း+ယူနစ် (ဥပမာ "2022" · "100%%" · "15万円")
- "jp"     : ဂျပန် စကားလုံး/အသုံးအနှုန်း ကို ရှင်းပြနေသည်。 `jp` = ဂျပန်စာ
             (かな/漢字) · `romaji` = romaji
- "no"     : 「မလုပ်ရ · မှားသည်」ဟု တိုက်ရိုက် ပြောသော စာကြောင်း。 `text` = ၂၀ လုံးအောက်
- မသေချာလျှင် **မရွေးပါနှင့်**

JSON array သာ ပြန်ပါ:
[{"line": 12, "kind": "panel", "text": "..."}, {"line": 30, "kind": "number", "num": "2022"},
 {"line": 41, "kind": "jp", "jp": "おもてなし", "romaji": "omotenashi"}]

စာတမ်း:
%s"""

_DIG = re.compile(r"[0-9၀-၉]")
_JP = re.compile(r"[぀-ヿ一-鿿]+")
# WARN number cards are drawn in Figtree (no Burmese digits) -> map to ASCII
_MMDIG = str.maketrans("\u1040\u1041\u1042\u1043\u1044\u1045\u1046\u1047\u1048\u1049", "0123456789")


def _clean(t, n):
    return " ".join(str(t or "").split())[:n]


def validate_notes(raw, lines):
    """Gemini အဖြေကို **ပိတ်ထားသော စာရင်း**နဲ့ စစ်သည်။ မကိုက်လျှင် ဖယ်。

    ⚠️ ဂဏန်းမဲ့ `number`၊ ဂျပန်စာမဲ့ `jp`၊ စာသားမဲ့ `panel` — ဖန်လာတာ
       ဖြစ်သဖြင့် ဖယ်သည် (odo template ဂဏန်းမဲ့ ထွက်ခဲ့ဖူးသော အမှားမျိုး)。
    """
    out, bad = {}, 0
    for it in raw or []:
        try:
            n = int(it.get("line", 0)) - 1
        except (TypeError, ValueError):
            bad += 1; continue
        k = str(it.get("kind") or "")
        if not (0 <= n < len(lines)) or k not in KINDS or k == "none" or n in out:
            bad += 1; continue
        if k == "panel":
            t = _clean(it.get("text"), 48)
            if len(t) < 3: bad += 1; continue
            out[n] = dict(kind=k, text=t)
        elif k == "number":
            v = _clean(it.get("num"), 12).translate(_MMDIG)
            if not _DIG.search(v): bad += 1; continue
            out[n] = dict(kind=k, num=v)
        elif k == "jp":
            j = _clean(it.get("jp"), 12)
            if not _JP.search(j): bad += 1; continue
            out[n] = dict(kind=k, jp=j, romaji=_clean(it.get("romaji"), 20))
        elif k == "no":
            t = _clean(it.get("text"), 24)
            out[n] = dict(kind=k, text=t or "No")
    return out, bad


def heuristic_notes(lines):
    """Gemini မရလျှင် — စာသားကနေ တိုက်ရိုက် မြင်ရတာသာ (ဂဏန်း · ဂျပန်စာ)。

    panel ကို မှန်းမထုတ်ပါ — 「အဓိက အချက်」ကို စာလုံးကြည့်ပြီး မဆုံးဖြတ်နိုင်。
    """
    out = {}
    for i, c in enumerate(lines):
        t = c.get("text") or ""
        m = _JP.search(t)
        if m and len(m.group(0)) >= 2:
            out[i] = dict(kind="jp", jp=m.group(0)[:12], romaji="")
            continue
        m = re.search(r"[0-9၀-၉][0-9၀-၉,.]*\s*(%|万|円|ယန်း|နှစ်)?", t)
        if m and len(re.sub(r"\D", "", m.group(0).translate(
                str.maketrans("၀၁၂၃၄၅၆၇၈၉", "0123456789")))) >= 2:
            out[i] = dict(kind="number", num=m.group(0).strip().translate(_MMDIG)[:12])
    return out


def ask_notes(lines, dur, log=print):
    if not lines:
        return {}
    want = max(1, int(round(dur / 60.0 * SPEC["panel_per_min"])))
    view = "\n".join(f"{i+1}. {c.get('text','')}" for i, c in enumerate(lines[:400]))
    body = {"contents": [{"parts": [{"text": NPROMPT % (want, view)}]}],
            "generationConfig": {"temperature": 0.2}}
    for k in range(2):
        try:
            G.throttle()
            r = urllib.request.Request(G.endpoint(MODEL), data=json.dumps(body).encode(),
                                       headers={"Content-Type": "application/json"},
                                       method="POST")
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
            m = re.search(r"\[.*\]", txt, re.S)
            if not m:
                raise ValueError("JSON မတွေ့")
            notes, bad = validate_notes(json.loads(m.group(0)), lines)
            G.tally("knowledge_notes", True)
            log(f"  knowledge · AI မှတ်ချက် {len(notes)} ခု"
                + (f" · မှား {bad} ဖယ်" if bad else ""))
            return notes
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            G.log_fail("knowledge_notes", k + 1, 2, e.code, raw,
                       final=G.fatal(e.code, raw) or k == 1)
            if G.fatal(e.code, raw):
                break
            time.sleep(6 * (k + 1))
        except Exception as e:
            G.log_fail("knowledge_notes", k + 1, 2, None, f"{type(e).__name__}: {e}",
                       final=(k == 1))
            time.sleep(4 * (k + 1))
    G.tally("knowledge_notes", False, "Gemini မရ")
    notes = heuristic_notes(lines)
    log(f"  ⚠️ knowledge · AI မရ — heuristic {len(notes)} ခု (panel မပါ)")
    return notes


def ask_broll(lines, log=print, chunk=70):
    """line → [(clip, score)]。 ⚠️ `BR.match` က ပထမ ၈၀ ကြောင်းကိုသာ ကြည့်သည် —
    ၈ မိနစ်ဗီဒီယိုရဲ့ ~၁၅၀ ကြောင်းထဲ နောက်တစ်ဝက် B-roll မရမည် ⇒ window ခွဲမေး。"""
    hits, used = {}, set()
    for a in range(0, len(lines), chunk):
        part = lines[a:a + chunk]
        try:
            got = BR.match(part, len(part), used=used, log=log, strict=True)
        except Exception as e:
            log(f"  ⚠️ knowledge · B-roll match မရ ({a}): {type(e).__name__}: {e}")
            got = []
        for si, clip, sc in got:
            hits.setdefault(a + si, []).append((clip, float(sc)))
            used.add(clip["path"])
    return hits


# ══ scheduler — timeline ကို ကုဒ်က ဆောက် ═════════════════════════
def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def panel_len(text):
    """ဖတ်ချိန် — စာလုံးရေ အလိုက် (ref slide ၂၃ ခု: ဖတ်စရာ များလျှင် ကြာ)。"""
    return round(_clamp(3.4 + 0.09 * len(text or ""), *SPEC["panel_len"]), 2)


def schedule(lines, dur, notes, hits, spec=None):
    """lines (cut timeline) + AI မှတ်ချက် + B-roll hit → event စာရင်း。

    event: dict(kind, at, dur, …)
      cutaway : "broll" (clips=[(clip, d), …]) · "panel" (text) · "no" (text)
      overlay : "number" (num) · "jp" (jp, romaji)   ← ပြောသူပေါ် · share မဝင်
    ⚠️ deterministic — ကျပန်း မသုံး (A/B ပြန်လုပ်လို့ ရစေရန်)。
    """
    S = dict(SPEC, **(spec or {}))
    ev, used = [], set()
    end_ok = dur - S["tail"]

    def _take(li):
        for clip, sc in hits.get(li, []):
            if clip["path"] not in used:
                used.add(clip["path"]); return clip
        return None

    # ① cold open — ပထမ ၂၀–၄၀s ကို B-roll montage နဲ့ ဖွင့် (ref ၄/၄)
    t_end = 0.0
    if dur >= S["cold_min_dur"]:
        co = _clamp(dur * S["cold_frac"], *S["cold"])
        pool = [li for li in sorted(hits) if lines[li]["start"] < co + 15.0]
        pool += [li for li in sorted(hits, key=lambda i: -max(s for _c, s in hits[i]))
                 if li not in pool]
        clips, tot = [], 0.0
        for li in pool:
            if tot >= co - 0.5 or len(clips) >= 5:
                break
            c = _take(li)
            if not c:
                continue
            d = min(float(c.get("dur") or 99), S["clip_len"][1], co - tot)
            if d < S["clip_len"][0]:
                used.discard(c["path"]); continue
            clips.append((c, round(d, 2))); tot += d
        if len(clips) >= 2:
            ev.append(dict(kind="broll", at=0.0, dur=round(tot, 2), clips=clips,
                           cold=True, line=None))
            t_end = tot

    # ② panel ကို **အရင်** ချသည် — B-roll ကို greedy အရင်ချလျှင် AI ရွေးထားသော
    #    panel စာကြောင်းက B-roll အောက် ရောက်ပြီး panel ၀ ခု ဖြစ်သည်
    #    (test ပထမ run: panel 0 · overlay 0 · B-roll 28)。
    busy = [(0.0, t_end)] if t_end else []

    def _free(a, b, pad):
        return all(b + pad <= x or a - pad >= y for x, y in busy)

    for li in sorted(notes):
        n = notes[li]
        if n["kind"] not in ("panel", "no"):
            continue
        s = float(lines[li]["start"])
        d = panel_len(n["text"]) if n["kind"] == "panel" else 3.2
        if s + d > end_ok or not _free(s, s + d, max(S["gap_min"], S["panel_gap"])):
            continue
        ev.append(dict(kind=n["kind"], at=round(s, 2), dur=d, text=n["text"], line=li))
        busy.append((s, s + d))

    def _spent(t):
        return sum(max(0.0, min(y, t) - x) for x, y in busy)

    # ③ overlay (ဂဏန်း · ဂျပန် ribbon) — **ပြောသူ ပေါ်နေချိန်**မှာသာ · share မဝင်。
    #    B-roll မချခင် နေရာ ကြိုယူရသည် — နောက်မှ ချလျှင် B-roll အောက် ရောက်ပြီး
    #    ၀ ခု ဖြစ်သည် (test ဒုတိယ run)。
    hold, last_ov = [], -99.0
    for li in sorted(notes):
        n = notes[li]
        if n["kind"] not in ("number", "jp"):
            continue
        s = float(lines[li]["start"])
        if s - last_ov < 4.0 or s >= end_ok or not _free(s, s + 0.1, 0.4):
            continue
        lo, hi = S["num_len"] if n["kind"] == "number" else S["jp_len"]
        nxt = min([x for x, _y in busy if x > s] + [end_ok])
        d = min(_clamp(float(lines[li]["end"]) - s, lo, hi), nxt - s - 0.2)
        if d < lo - 0.01:
            continue
        e = dict(kind=n["kind"], at=round(s, 2), dur=round(d, 2), line=li)
        e.update({k: v for k, v in n.items() if k != "kind"})
        ev.append(e); hold.append((s - 0.4, s + d + 0.4)); last_ov = s + d

    # ④ B-roll — coverage ပစ်မှတ်ကို အချိန်နဲ့အမျှ လိုက်ပြီး ကွက်လပ်ထဲ ဖြည့်
    for li, c in enumerate(lines):
        if li not in hits:
            continue
        s = float(c["start"])
        if s >= end_ok or not _free(s, s + S["broll_len"][0], S["gap_min"]):
            continue
        if any(x < s + S["broll_len"][0] and y > s for x, y in hold):
            continue
        busy.sort()
        nxt = min([x for x, _y in busy if x > s] + [end_ok + S["gap_min"]])
        room = min(nxt - S["gap_min"], min([x for x, _y in hold if x > s] + [9e9])) - s
        last = max([y for _x, y in busy if y <= s] + [0.0])
        # ref ညီညာ — ယခုထိ ရသင့်တာထက် ကျော်နေလျှင် မချ (ပြောသူ အရှည်ကြီး မဖြစ်သရွေ့)
        behind = S["share"] * s - _spent(s)
        if behind < -2.0 and s - last < S["gap_max"]:
            continue
        # ⚠️ နောက်ကျနေလျှင် montage ကို **ရှည်စေ**သည် — clip တစ်ခုစာ (၄–၅s) ပဲ
        #    ချလျှင် share 0.28 မှာ ရပ်သည် (test) · ref p50 12.5s အထိ ရှည်သည်
        want = _clamp(max(float(c["end"]) - s, S["broll_len"][0] + max(0.0, behind)),
                      *S["broll_len"])
        want = min(want, room)
        if want < S["broll_len"][0] - 0.01:
            continue
        first = _take(li)
        if not first:
            continue
        d0 = min(float(first.get("dur") or 99), S["clip_len"][1], want)
        if d0 < S["clip_len"][0]:
            used.discard(first["path"]); continue
        clips, tot = [(first, round(d0, 2))], d0
        j = li + 1                     # montage — နောက်ကြောင်းတွေရဲ့ hit ဆက်တွဲ
        while tot < want - 0.5 and j < len(lines) and len(clips) < 3:
            if float(lines[j]["start"]) > s + want:
                break
            c2 = _take(j); j += 1
            if not c2:
                continue
            d2 = min(float(c2.get("dur") or 99), S["clip_len"][1], want - tot)
            if d2 < S["clip_len"][0]:
                used.discard(c2["path"]); break
            clips.append((c2, round(d2, 2))); tot += d2
        ev.append(dict(kind="broll", at=round(s, 2), dur=round(tot, 2), clips=clips, line=li))
        busy.append((s, s + tot))

    ev.sort(key=lambda e: e["at"])
    return ev


CUTAWAY = ("broll", "panel", "no")


def stats(ev, dur):
    cut = sorted((e["at"], e["at"] + e["dur"]) for e in ev if e["kind"] in CUTAWAY)
    share = sum(b - a for a, b in cut) / dur if dur else 0.0
    gaps, t = [], 0.0
    for a, b in cut:
        gaps.append(a - t); t = b
    gaps.append(max(0.0, dur - t))
    return dict(n_cut=len(cut), share=round(share, 3),
                rate=round(len(cut) / dur * 60.0, 2) if dur else 0.0,
                max_talk=round(max(gaps) if gaps else dur, 1),
                n_panel=sum(1 for e in ev if e["kind"] in ("panel", "no")),
                n_broll=sum(1 for e in ev if e["kind"] == "broll"),
                n_over=sum(1 for e in ev if e["kind"] in ("number", "jp")),
                cold=next((e["dur"] for e in ev if e.get("cold")), 0.0))


def plan(lines, dur, rc=None, log=print):
    """worker ရဲ့ ⑤ graphics အဆင့်က ခေါ်သည်။ `lines` = **စာတမ်း အပြည့်**
    (emphasis စစ်ထုတ်ထားသော caps မဟုတ် — ဒါဆို ၁၅% ပဲ ရမည်)。"""
    lines = [c for c in (lines or []) if (c.get("text") or "").strip()]
    notes = ask_notes(lines, dur, log=log)
    hits = ask_broll(lines, log=log)
    ev = schedule(lines, dur, notes, hits, spec=(rc or {}).get("kn_spec"))
    st = stats(ev, dur)
    log(f"  knowledge · cutaway {st['n_cut']} ခု ({st['rate']}/min) · "
        f"share {st['share']:.0%} (ပစ်မှတ် {SPEC['share']:.0%}) · "
        f"panel {st['n_panel']} · B-roll {st['n_broll']} · overlay {st['n_over']} · "
        f"cold open {st['cold']:.1f}s · ပြောသူ အရှည်ဆုံး {st['max_talk']}s")
    return dict(events=ev, dur=dur, stats=st)


def hide_caps(caps, P):
    """panel ပေါ်နေချိန် စာတန်း ဖျောက် (ref: panel frame မှာ စာတန်း မရှိ)。"""
    if not P:
        return caps
    win = [(e["at"], e["at"] + e["dur"]) for e in P["events"] if e["kind"] in ("panel", "no")]
    return [c for c in caps
            if not any(float(c["start"]) < b and float(c["end"]) > a for a, b in win)]


# ══ render ════════════════════════════════════════════════════
def _ff(args, timeout=900):
    # ⚠️ `-nostdin` + timeout — render ၂ ခုလုံး overlay pass မှာ CPU 0% နဲ့
    #    ၈၀ မိနစ် ရပ်ခဲ့သည် (၂၀၂၆-၀၉-၂၆)。 job တစ်ခုကို ဘယ်တော့မှ အဆုံးမဲ့ မစောင့်ရ ·
    #    timeout ဖြစ်လျှင် exception ⇒ caller က ပြောသူ ပြန်ထားသည်。
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *args],
                       capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout)
    if r.returncode:
        # ⚠️ stderr **အပြည့်** — အဆုံး ၄၀၀ လုံးပဲ ထားခဲ့ရာ render အစစ်မှာ
        #    「…ent)」ပဲ ကျန်ပြီး panel ကျရခြင်း အကြောင်းရင်း မမြင်ရခဲ့。
        err = r.stderr.decode("utf-8", "replace")
        lines = [l for l in err.splitlines() if l.strip()]
        raise RuntimeError("ffmpeg: " + " | ".join(lines[:3] + (["…"] + lines[-3:] if len(lines) > 6 else lines[3:]))[:1200])


def _enc(fps):
    # ⚠️ segment အားလုံး **encoder တစ်ခုတည်း · ကိန်းတူ** ဖြစ်ရမည် —
    #    concat demuxer `-c copy` က SPS မတူလျှင် ပျက်သည်。 videotoolbox နဲ့
    #    libx264 ရောလျှင် ဖြစ်သည် ⇒ ဒီမှာ libx264 သီးသန့်。
    return ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14",
            "-pix_fmt", "yuv420p", "-r", str(fps), "-video_track_timescale", "90000"]


def _paper_png(text, W, H, out, mmf):
    """ဘယ် 0.489W စက္ကူ + စာ (အလယ်)。 ညာဘက် ဖောက်ထားသည် (alpha 0)。"""
    import numpy as np
    from PIL import Image
    SL.setsize(W, H)
    pw = int(round(W * PAPER_W))
    rng = np.random.default_rng(len(text) * 7919 + W)
    base = np.empty((H, pw, 3), np.float32)
    base[:] = PAPER_RGB
    # စက္ကူ texture — အမှုန်သေး + အကွက်ကြီး ဖျော့ (ref မှာ fibre အစက် မြင်ရ)
    base += rng.normal(0, 3.2, (H, pw, 1))
    coarse = rng.normal(0, 2.0, (H // 24 + 2, pw // 24 + 2, 1))
    coarse = np.kron(coarse, np.ones((24, 24, 1)))[:H, :pw]
    base += coarse
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.paste(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)), (0, 0))
    px = int(round(H * PAPER_TXT))
    maxw = int(pw * 0.80)
    lines = SL._wrap(text, px, mmf, maxw)
    while len(lines) > 3 and px > int(H * 0.034):
        px = int(px * 0.9); lines = SL._wrap(text, px, mmf, maxw)
    arrs = [SL._text_png(l, px, mmf, PAPER_INK, align="center") for l in lines[:3]]
    lh = int(px * 1.55)
    y = int(H * 0.46 - lh * len(arrs) / 2)
    for a in arrs:
        SL._paste(im, a, (pw - a.shape[1]) // 2, y + (lh - a.shape[0]) // 2)
        y += lh
    im.save(out)
    return out


def _badge_png(ev, W, H, out, mmf, accent="#F5C543"):
    """ပြောသူပေါ် overlay — 3D ဆန် ရွှေဂဏန်း (qUCE 20 · 2022 · 100%) သို့မဟုတ်
    ဂျပန် ribbon (hrms めいし · おもてなし)。 ဘောင်အပြည့် RGBA။"""
    import numpy as np
    from PIL import Image, ImageFilter
    SL.setsize(W, H)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rgb = tuple(int(accent[i:i + 2], 16) for i in (1, 3, 5))
    if ev["kind"] == "number":
        px = int(H * 0.16)
        a = SL._text_png(ev["num"], px, "Figtree-Black", rgb)
        dark = SL._text_png(ev["num"], px, "Figtree-Black", (90, 48, 8))
        x, y = int(W * 0.10), int(H * 0.44 - a.shape[0] / 2)
        # extrusion (3D) — အောက်ညာ ၁၀ ထပ်
        for k in range(10, 0, -1):
            SL._paste(im, dark, x + k, y + k)
        SL._paste(im, a, x, y)
        sh = im.split()[3].filter(ImageFilter.GaussianBlur(H * 0.012))
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        shadow.putalpha(sh.point(lambda v: int(v * 0.55)))
        out_im = Image.alpha_composite(shadow, im)
        out_im.save(out)
        return out
    # jp ribbon — ဘယ်အောက် · အနီ ribbon · romaji သေး + かな ကြီး
    jp, ro = ev.get("jp") or "", ev.get("romaji") or ""
    big = SL._text_png(jp, int(H * 0.055), "HiraginoSans-W6", (255, 255, 255))
    sm = SL._text_png(ro, int(H * 0.024), "Figtree-Black", (255, 236, 236)) if ro else None
    bw = max(big.shape[1], sm.shape[1] if sm is not None else 0) + int(H * 0.09)
    bh = big.shape[0] + (sm.shape[0] + int(H * 0.012) if sm is not None else 0) + int(H * 0.05)
    x0, y0 = int(W * 0.06), int(H * 0.80 - bh)
    rib = Image.new("RGBA", (bw, bh), (196, 30, 36, 235))
    im.alpha_composite(rib, (x0, y0))
    yy = y0 + int(H * 0.025)
    if sm is not None:
        SL._paste(im, sm, x0 + int(H * 0.045), yy); yy += sm.shape[0] + int(H * 0.012)
    SL._paste(im, big, x0 + int(H * 0.045), yy)
    im.save(out)
    return out


def _frames(t, fps):
    return int(round(float(t) * fps))


def _seg_talk(cutv, f0, f1, fps, out, W=None, H=None):
    vf = ["-vf", f"scale={W}:{H},setsar=1"] if W else []
    _ff(["-ss", f"{f0 / fps:.6f}", "-i", cutv, "-frames:v", str(f1 - f0), *vf,
         *_enc(fps), out])


def _seg_broll(ev, nfr, W, H, fps, work, idx, out):
    ins, fc, k, left = [], [], 0, nfr
    for j, (clip, d) in enumerate(ev["clips"]):
        n = left if j == len(ev["clips"]) - 1 else min(left, _frames(d, fps))
        if n <= 0:
            break
        src = os.path.join(work, f"kb{idx}_{j}.mp4")
        BR.prep(clip, W, H, n / fps + 0.3, src, fps=fps)
        ins += ["-i", src]
        fc.append(f"[{k}:v]trim=end_frame={n},setpts=PTS-STARTPTS,"
                  f"scale={W}:{H},setsar=1,fps={fps}[c{k}]")
        k += 1; left -= n
    if left > 0 and k:                                  # clip တိုလျှင် နောက်ဆုံး frame ဆွဲ
        fc[-1] = fc[-1].replace(f"[c{k-1}]", f",tpad=stop_mode=clone:stop={left}[c{k-1}]")
    fc.append("".join(f"[c{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=0[v]")
    _ff([*ins, "-filter_complex", ";".join(fc), "-map", "[v]", "-frames:v", str(nfr),
         *_enc(fps), out])


def _seg_panel(ev, cutv, f0, nfr, W, H, fps, png, out, cx=0.5):
    """ညာဘက် ၀.၅၁W ထဲ ပြောသူ (1.10× · subject အလယ်)၊ ဘယ်ဘက် စက္ကူ。"""
    pw = int(round(W * PAPER_W)); rw = W - pw
    cw = int(rw / SPEAKER_ZOOM) // 2 * 2
    ch = int(H / SPEAKER_ZOOM) // 2 * 2
    x = int(_clamp(cx * W - cw / 2, 0, W - cw)) // 2 * 2
    fc = (f"[0:v]crop={cw}:{ch}:{x}:0,scale={rw}:{H},setsar=1[s];"
          f"color=c=black:s={W}x{H}:r={fps}[bg];"
          f"[bg][s]overlay={pw}:0:shortest=1[b];"
          f"[b][1:v]overlay=0:0[v]")
    _ff(["-ss", f"{f0 / fps:.6f}", "-i", cutv, "-loop", "1", "-i", png,
         "-filter_complex", fc, "-map", "[v]", "-frames:v", str(nfr), *_enc(fps), out])


def bake(P, cutv, work, TH, rc, log=print, cx=0.5):
    """cutaway ကို ဗီဒီယိုထဲ **segment အစားထိုး**ပြီး overlay (ဂဏန်း · ribbon)
    ထည့်သည်။ အသံကို မူရင်း cutv ကနေ `-c:a copy` — **မထိ**。

    ⚠️ frame grid ပေါ်မှာ တွက်သည် — segment အရှည်ပေါင်း = မူရင်း frame ရေ
       အတိအကျ ဖြစ်မှ အသံ-ရုပ် မလွဲ ([[zjl-render-spans]] AAC drift နှင့် ခွဲ —
       ဒီမှာ အသံကို concat မလုပ်ပါ)。
    """
    if not P or not P.get("events"):
        return cutv
    import numpy as np  # noqa: F401  (PIL/numpy ရှိမှ)
    # ⚠️ **cutv ရဲ့ အရွယ် အစစ်**နဲ့ လုပ်ရမည် — TH (1920×1080) မဟုတ်。 ⑦ အဆင့်မှာ
    #    cutv က source အရွယ် (test: 854×480) ဖြစ်နေသေးပြီး TH သို့ ချဲ့တာက
    #    နောက်ဆုံး composite မှာသာ。 TH နဲ့ လုပ်ခဲ့ရာ panel crop 890×980 က frame
    #    ထက် ကြီး၍ ကျပြီး、1080p B-roll + 480p talk ကို `-c copy` နဲ့ ဆက်မိကာ
    #    overlay pass က ရပ်သွားခဲ့သည် (render အစစ် ၂ ခု)。
    pv = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                         "-show_entries", "stream=width,height", "-of", "csv=p=0", cutv],
                        capture_output=True, text=True, stdin=subprocess.DEVNULL)
    try:
        W, H = [int(x) for x in pv.stdout.strip().split(",")[:2]]
    except Exception:
        W, H = int(TH["W"]), int(TH["H"])
    W, H = W // 2 * 2, H // 2 * 2
    fps = int(round(float(rc.get("fps") or 30)))
    mmf = rc.get("kn_panel_font") or rc.get("mmf") or "Pyidaungsu-Bold"
    pr = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0",
                         "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", cutv],
                        capture_output=True, text=True, stdin=subprocess.DEVNULL)
    total = int((pr.stdout or "0").strip().split(",")[0] or 0)
    if total <= 0:
        raise RuntimeError("cutv frame ရေ မတိုင်နိုင်")
    kd = os.path.join(work, "kn"); os.makedirs(kd, exist_ok=True)
    cuts = []
    for e in P["events"]:
        if e["kind"] not in CUTAWAY:
            continue
        f0 = _frames(e["at"], fps); f1 = min(total, f0 + _frames(e["dur"], fps))
        if cuts and f0 < cuts[-1][1]:
            f0 = cuts[-1][1]
        if f1 - f0 >= fps:                                 # ၁s အောက် မချ
            cuts.append((f0, f1, e))
    segs, f, t0 = [], 0, time.time()
    for i, (f0, f1, e) in enumerate(cuts):
        if f0 > f:
            p = os.path.join(kd, f"t{i:03d}.mp4"); _seg_talk(cutv, f, f0, fps, p, W, H); segs.append(p)
        p = os.path.join(kd, f"c{i:03d}.mp4")
        try:
            if e["kind"] == "broll":
                _seg_broll(e, f1 - f0, W, H, fps, kd, i, p)
            else:
                png = os.path.join(kd, f"p{i:03d}.png")
                _paper_png(e["text"], W, H, png, mmf)
                _seg_panel(e, cutv, f0, f1 - f0, W, H, fps, png, p, cx=cx)
        except Exception as ex:                            # တစ်ခု ကျလျှင် ပြောသူ ပြန်ထည့်
            log(f"  ⚠️ knowledge · {e['kind']} @{e['at']}s မရ — ပြောသူ ထားသည်: {ex}")
            _seg_talk(cutv, f0, f1, fps, p, W, H)
        segs.append(p); f = f1
    if f < total:
        p = os.path.join(kd, "t_end.mp4"); _seg_talk(cutv, f, total, fps, p, W, H); segs.append(p)
    # ⚠️ concat `-c copy` က အရွယ်/fps မတူလျှင် **အမှားမပြဘဲ** ပျက်သော stream
    #    ထုတ်သည် ⇒ ဆက်ခင် တစ်ခုချင်း စစ်သည်。
    for sp in segs:
        q = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0",
                            sp], capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if q.stdout.strip() != f"{W},{H},{fps}/1":
            raise RuntimeError(f"segment မကိုက်: {os.path.basename(sp)} {q.stdout.strip()} "
                               f"≠ {W},{H},{fps}/1")
    lst = os.path.join(kd, "list.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{s}'\n" for s in segs)
    vid = os.path.join(kd, "video.mp4")
    _ff(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid])
    # overlay — ဂဏန်း · ribbon (ပြောသူပေါ် · ဝင်ချိန် fade + တက်)
    ovs = [e for e in P["events"] if e["kind"] in ("number", "jp")]
    base = vid
    for b in range(0, len(ovs), 8):                       # ⚠️ input ကန့်သတ် — ၈ ခုစီ
        part = ovs[b:b + 8]
        ins, fc, last = ["-i", base], [], "0:v"
        for j, e in enumerate(part):
            png = os.path.join(kd, f"o{b + j:03d}.png")
            _badge_png(e, W, H, png, mmf)
            a, d = float(e["at"]), float(e["dur"])
            ins += ["-loop", "1", "-t", f"{a + d + 0.5:.2f}", "-i", png]
            fc.append(f"[{j+1}:v]format=rgba,fade=in:st={a:.2f}:d=0.22:alpha=1,"
                      f"fade=out:st={a + d - 0.25:.2f}:d=0.25:alpha=1[o{j}]")
            fc.append(f"[{last}][o{j}]overlay=0:'{int(H*0.03)}*max(0,1-(t-{a:.2f})/0.30)':"
                      f"enable='between(t,{a:.2f},{a + d:.2f})'[v{j}]")
            last = f"v{j}"
        nxt = os.path.join(kd, f"ov{b}.mp4")
        _ff([*ins, "-filter_complex", ";".join(fc), "-map", f"[{last}]",
             "-frames:v", str(total), *_enc(fps), nxt])
        base = nxt
    out = os.path.join(work, "cut_kn.mp4")
    _ff(["-i", base, "-i", cutv, "-map", "0:v:0", "-map", "1:a?", "-c", "copy",
         "-movflags", "+faststart", out])
    log(f"  knowledge · bake {len(cuts)} cutaway + {len(ovs)} overlay · "
        f"{time.time() - t0:.0f}s")
    return out


# ══ QC ════════════════════════════════════════════════════════
def checks(P):
    """worker QC ထဲ ထည့်ရန်。 `advisory=True` = ပိတ်မထား (သတိပေးသာ)。

    ⚠️ **အောက်ကျတာကို မပိတ်**ပါ — library မှာ ကိုက်တဲ့ B-roll မရှိတာက
       သုံးစွဲသူ့ ဗီဒီယိုကို ပို့မပေးရလောက်အောင် မဆိုးပါ (strict match က
       မဆိုင်တဲ့ရုပ် မထည့်ဘဲ ချန်တာ ပိုကောင်း)。 **ကျော်တာကိုသာ ပိတ်**သည် —
       ပြောသူ ပျောက်သွားသည်။
    """
    if not P:
        return []
    st, dur = P["stats"], float(P["dur"] or 0)
    if dur < 60:
        return []
    return [
        dict(key="kn_share_max", ok=st["share"] <= SPEC["share_max"], value=st["share"],
             want=f"≤ {SPEC['share_max']:.2f}"),
        dict(key="kn_share_min", ok=st["share"] >= SPEC["share_min"], value=st["share"],
             want=f"≥ {SPEC['share_min']:.2f} (ref 0.34–0.42)", advisory=True),
        dict(key="kn_max_talk", ok=st["max_talk"] <= SPEC["gap_max"] * 1.5,
             value=st["max_talk"], want=f"≤ {SPEC['gap_max'] * 1.5:.0f}s", advisory=True),
    ]


def summary(P):
    return dict(P["stats"]) if P else None
