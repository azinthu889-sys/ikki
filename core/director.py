#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI Director — စကားလုံး ချိန်ပါ transcript ⇒ infographic **beat** JSON (Zin ၂၀၂၆-၁၀-၀၇ roadmap ①)

「စကားလုံးအလိုက် Animation infographic · 2026 talking-head」 အတွက် ဦးနှောက်。

  1. Gemini (`gemguard` — cache · quota ကာကွယ်) က ဝါကျ စာရင်းကို ဖတ်ပြီး beat ရွေး
     (type · anchor စကားလုံး · params)。
  2. မရ/ပိတ်ထား (`IKKI_DIRECTOR_AI=0`) ⇒ **rule-based** (ဂဏန်း · ငွေ · ရာခိုင်နှုန်း · ရက်စွဲ ·
     brand · မြို့ · စာရင်း · မေးခွန်း · သတိ · CTA)。
  3. **registry schema** (`beat_registry.json` — Remotion kit နဲ့ တစ်ခုတည်း) နဲ့ စစ်ပြီး
     density · spacing · variety · placement (မျက်နှာ ရှောင်) စည်းမျဉ်း ချသည်。

⚠️ beat `at` = anchor စကားလုံး **စချိန်** (ထွက်ဗီဒီယို timeline `o0`) ⇒ SFX hit + motion peak
   က စကားလုံးနဲ့ တိတိ ကျသည်。
⚠️ busy window (IKKI ကတ် · Remotion scene · B-roll) ကို ရှောင်သည် ⇒ ရုပ်/အသံ မထပ်။
"""
import json
import os
import re
import urllib.request

try:
    import gemguard as G
except ImportError:  # pragma: no cover
    from core import gemguard as G

HERE = os.path.dirname(os.path.abspath(__file__))
REG_PATH = os.path.join(HERE, "beat_registry.json")
MODEL = os.environ.get("IKKI_GEMINI_MODEL", "gemini-flash-latest")
_REG = None


def registry():
    global _REG
    if _REG is None:
        with open(REG_PATH, encoding="utf-8") as f:
            _REG = json.load(f)
    return _REG


def types():
    return registry()["types"]


# ── density / spacing (style pack အလိုက်) ───────────────────────────────
PACKS = {
    # per_min = တစ်မိနစ် beat အများဆုံး · gap = beat ကြား အနည်းဆုံး (s) · center_gap = cutaway ကြား
    "calm":    dict(per_min=4.0, gap=5.0, center_gap=25.0, first=2.0),
    "default": dict(per_min=6.0, gap=3.6, center_gap=16.0, first=1.2),
    "hype":    dict(per_min=9.0, gap=2.6, center_gap=10.0, first=0.8),
}
TAIL = 2.4          # ဗီဒီယို အဆုံး မတိုင်ခင် ကင်း
MAX_STR = 42        # params စာသား အရှည် (Burmese overflow ကာကွယ် — kit က auto-fit ထပ်လုပ်)
MAX_SAME = 2        # type တစ်ခု အများဆုံး (ဗီဒီယို ၁ မိနစ်လျှင်)

_D = str.maketrans("၀၁၂၃၄၅၆၇၈၉", "0123456789")
BRANDS = (("western union", "Western Union"), ("kbz pay", "KBZ Pay"), ("kbzpay", "KBZ Pay"),
          ("kpay", "KBZ Pay"), ("wave pay", "Wave Pay"), ("wavemoney", "Wave Money"),
          ("aya pay", "AYA Pay"), ("cb pay", "CB Pay"), ("paypay", "PayPay"), ("line pay", "LINE Pay"),
          ("youtube", "YouTube"), ("facebook", "Facebook"), ("tiktok", "TikTok"), ("zin apex", "Zin Apex"))
CITIES = (("tokyo", "Tokyo"), ("တိုကျို", "Tokyo"), ("osaka", "Osaka"), ("အိုဆာကာ", "Osaka"),
          ("fukuoka", "Fukuoka"), ("ဖူကူအိုကာ", "Fukuoka"), ("nagoya", "Nagoya"), ("နာဂိုယာ", "Nagoya"),
          ("kyoto", "Kyoto"), ("ကျိုတို", "Kyoto"), ("sapporo", "Sapporo"), ("ဆပ်ပိုရို", "Sapporo"),
          ("yokohama", "Yokohama"), ("ယိုကိုဟားမား", "Yokohama"), ("kobe", "Kobe"), ("ကိုဘေ", "Kobe"),
          ("ရန်ကုန်", "Yangon"), ("yangon", "Yangon"), ("မန္တလေး", "Mandalay"), ("mandalay", "Mandalay"))
MONTHS = (("ဇန်နဝါရီ", "JAN"), ("ဖေဖော်ဝါရီ", "FEB"), ("မတ်", "MAR"), ("ဧပြီ", "APR"), ("မေ", "MAY"),
          ("ဇွန်", "JUN"), ("ဇူလိုင်", "JUL"), ("ဩဂုတ်", "AUG"), ("သြဂုတ်", "AUG"), ("စက်တင်ဘာ", "SEP"),
          ("အောက်တိုဘာ", "OCT"), ("နိုဝင်ဘာ", "NOV"), ("ဒီဇင်ဘာ", "DEC"))
UNITS = ("သိန်း", "သောင်း", "ထောင်", "ကျပ်", "ယန်း", "yen", "¥", "$", "ဒေါ်လာ", "ရက်", "လ", "နှစ်",
         "ယောက်", "ဦး", "ခု", "ကြိမ်", "မိနစ်", "နာရီ", "%", "ရာခိုင်နှုန်း")
_NUM = re.compile(r"([0-9၀-၉][0-9၀-၉,\.]*)\s*(" + "|".join(map(re.escape, UNITS)) + r")?")
WARN_KW = ("သတိ", "အန္တရာယ်", "လိမ်", "မလုပ်ပါနဲ့", "မလုပ်နဲ့", "ရှောင်", "ပြဿနာ", "warning", "scam")
CTA_KW = ("subscribe", "follow", "like", "share", "ဆပ်စ်ကရိုက်", "ဖော်လို", "လိုက်ခ်", "ရှဲ")
LIST_KW = ("လိုအပ်", "ပါဝင်", "အချက်", "စာရွက်စာတမ်း", "ပြင်ဆင်")
STEP_KW = ("အဆင့်", "ပထမ", "ဒုတိယ", "တတိယ", "step")
VS_KW = (" vs ", "နဲ့ ယှဉ်", "ထက်", "ကွာခြား", "ယှဉ်ကြည့်")
EMPH_KW = ("အရေးကြီး", "သေချာ", "အဓိက", "လျှို့ဝှက်", "secret", "အမှန်တကယ်")


_MARK = re.compile(r"[\u102B-\u103E\u1056-\u1059\u105E-\u1060\u1062-\u1064\u1067-\u106D\u1071-\u1074\u1082-\u108D\u108F\u109A-\u109D]")


def _safe(s, n):
    """မြန်မာ အက္ခရာ အဆက် (ုံ ် ့ ္ …) မပြတ်အောင် `n` နေရာ ညှိ"""
    while n < len(s) and (_MARK.match(s[n]) or (n > 0 and s[n - 1] == "\u1039")):
        n += 1
    return s[:n]


def _clip(s, n=MAX_STR):
    s = " ".join(str(s or "").split())
    if len(s) <= n:
        return s
    head = _safe(s, n)
    cut = head.rsplit(" ", 1)[0] if " " in head else head
    return (cut if len(cut) > n * 0.5 else head).rstrip("၊။,. ")


def _short(s, n=5):
    w = [x for x in str(s or "").replace("။", " ").replace("၊", " ").split() if x]
    return _clip(" ".join(w[:n]))


def _t0(seg):
    return float(seg.get("o0", seg.get("start", 0)) or 0)


def _t1(seg):
    return float(seg.get("o1", seg.get("end", 0)) or 0)


def _words(seg):
    """(စကားလုံး, ထွက်ဗီဒီယို စချိန်) — word timing မရှိလျှင် အက္ခရာ အချိုးနဲ့ ခန့်မှန်း"""
    out = []
    for w in seg.get("words") or []:
        t = w.get("o0", w.get("s"))
        if t is None:
            continue
        out.append((str(w.get("w") or ""), float(t)))
    if out:
        return out
    a, b = _t0(seg), _t1(seg)
    toks = str(seg.get("text") or "").split()
    tot = sum(len(x) for x in toks) or 1
    acc = 0
    for x in toks:
        out.append((x, a + (b - a) * acc / tot))
        acc += len(x)
    return out


def anchor_time(seg, token):
    """`token` ပါသော စကားလုံး စချိန် — မတွေ့လျှင် ဝါကျ အချိုးဖြင့်"""
    tok = str(token or "").translate(_D).lower().strip()
    ws = _words(seg)
    if tok:
        for w, t in ws:
            k = w.translate(_D).lower()
            if k and (tok in k or (len(k) >= 2 and k in tok)):
                return t
        txt = str(seg.get("text") or "")
        i = txt.translate(_D).lower().find(tok)
        if i >= 0 and len(txt):
            a, b = _t0(seg), _t1(seg)
            return a + (b - a) * i / len(txt)
    return ws[0][1] if ws else _t0(seg)


# ── rule-based candidates ───────────────────────────────────────────────
def _num_beats(seg, txt):
    out = []
    for mm in _NUM.finditer(txt):
        v = mm.group(1).translate(_D).strip(",.")
        if not v or (len(v) == 4 and v.startswith("20") and not mm.group(2)):
            continue  # ခုနှစ် ⇒ date/timeline ဘက်
        r = _num_one(txt, mm)
        if r:
            out.append(r)
    return out


def _num_one(txt, m):
    v, u = m.group(1).translate(_D).strip(",."), (m.group(2) or "")
    if u in ("%", "ရာခိုင်နှုန်း"):
        try:
            pct = float(v)
        except ValueError:
            return None
        if 0 < pct <= 100:
            return dict(type="ring", anchor=m.group(1), pct=pct, label=_short(txt.replace(m.group(0), ""), 4))
        return None
    if u in ("ရက်", "နာရီ", "မိနစ်") and len(v) <= 3:
        return dict(type="countdown", anchor=m.group(1), value=v, label=_clip(u + " " + _short(txt, 3), 24))
    try:
        fv = float(v.replace(",", ""))
    except ValueError:
        return None
    if fv < 3 and not u:
        return None
    mult = {"သိန်း": 100000, "သောင်း": 10000}.get(u)
    if mult and fv * mult < 1e9:
        v, u = f"{int(round(fv * mult)):,}", "ကျပ်"
    pre = txt[:m.start()].split()
    post = txt[m.end():].split()
    ctx = [w for w in pre[-2:] if w not in ("ကျပ်",)] or post[:2]
    sup = [w for w in ctx if re.search(r"အနည်းဆုံး|အများဆုံး", w)]
    ctx = sup or ctx
    return dict(type="stat", anchor=m.group(1), value=v, unit=u, label=_clip(" ".join(ctx), 26),
                _prio=(6 if mult else 5) + (1 if re.search(r"အနည်းဆုံး|အများဆုံး|သာ|ထိ", " ".join(ctx)) else 0))


def _brand_hits(t):
    k = " ".join(t.lower().split())
    seen = []
    for b, d in BRANDS:
        if b in k and d not in seen:
            seen.append(d)
    return seen


def _item_clean(p):
    p = re.sub(r"^.*?ဆိုရင်\s*", "", p)
    p = re.sub(r"(စတဲ့|တို့).*$", "", p)
    p = re.sub(r"(ရယ်|တွေ|များ)$", "", p.strip(" ။,"))
    return p.strip(" ။,")


def _list_items(txt):
    if len(re.findall(r"[၊,]", txt)) < 2:
        return []
    parts = [_item_clean(p) for p in re.split(r"[၊,]|\s(?:နဲ့|နှင့်|and)\s", txt)]
    parts = [p for p in parts if p]
    parts = [_clip(p, 22) for p in parts if 1 <= len(p.split()) <= 4]
    return parts if len(parts) >= 3 else []


def rules(segs, dur):
    out = []
    n = len(segs)
    for i, s in enumerate(segs):
        txt = str(s.get("text") or "").strip()
        if not txt:
            continue
        low = txt.lower()
        cand = []
        br = _brand_hits(txt)
        if len(br) >= 1 and any(k in txt for k in ("လွှဲ", "ပို့", "transfer")):
            cand.append(dict(type="transfer", anchor=br[0].split()[0], **{"from": "JP", "to": "MM"},
                             label=_clip(br[0], 20)))
        elif br:
            cand.append(dict(type="brand", anchor=br[0].split()[0], name=br[0], sub=_short(txt, 2)))
        cand.extend(_num_beats(s, txt))
        hits = []
        for mk, ab in MONTHS:
            for dm in re.finditer(re.escape(mk) + r"\s*(?:လ)?\s*([0-9၀-၉]{1,2})?(?![0-9၀-၉])", txt):
                hits.append((dm.start(), mk, ab, (dm.group(1) or "").translate(_D)))
        hits.sort()
        if len(hits) >= 2:
            cand.append(dict(type="timeline", anchor=hits[0][1], _prio=5,
                             items=[[f"{ab} {d}".strip(), lab] for (_, _, ab, d), lab in
                                    zip(hits[:4], ("စတင်", "ပြီးဆုံး", "", ""))]))
            for it in cand[-1]["items"]:
                it[1] = it[1] or "•"
        elif hits:
            _, mk, ab, d = hits[0]
            cand.append(dict(type="date", anchor=mk, month=ab, day=d or ab[:1], label=""))
        for ck, cd in CITIES:
            if ck in low:
                cand.append(dict(type="location", anchor=ck, place=cd, sub=_short(txt, 2)))
                break
        if any(k in low for k in WARN_KW):
            kw = next(k for k in WARN_KW if k in low)
            rest = low.split(kw, 1)[1].split() if kw in low else []
            rest = [w for w in txt.split()[len(txt.split()) - len(rest):]][:7]
            body = " ".join(w for w in rest if not re.match(r"^(တော့|ကတော့|ရမှာ|ကို|က)$", w))
            cand.append(dict(type="warning", anchor=kw, title="သတိ!", body=_clip(re.sub(r"^\S*တော့\s*", "", body), 30), _prio=5))
        if any(k in low for k in CTA_KW) and _t0(s) > dur * 0.6:
            cand.append(dict(type="cta", anchor=next(k for k in CTA_KW if k in low), text="Subscribe"))
        items = _list_items(txt)
        if items:
            if any(k in txt for k in STEP_KW):
                cand.append(dict(type="steps", anchor=items[0].split()[0], steps=items[:4]))
            elif any(k in txt for k in LIST_KW):
                cand.append(dict(type="checklist", anchor=items[0].split()[0], head=_short(txt, 2), items=items[:4]))
            else:
                cand.append(dict(type="list", anchor=items[0].split()[0], items=items[:4]))
        if (txt.endswith("?") or re.search(r"(လဲ|လား|သလဲ)[။?]?$", txt)) and i + 1 < n:
            nxt = str(segs[i + 1].get("text") or "")
            if 2 <= len(nxt.split()) <= 8:
                cand.append(dict(type="qa", anchor=txt.split()[0], q=_clip(txt, 34), a=_clip(nxt, 30)))
        if any(k in txt for k in EMPH_KW):
            kw = next(k for k in EMPH_KW if k in txt)
            cand.append(dict(type="big_caption", anchor=kw, text=_short(txt, 4), kw=kw, _prio=0))
        for c in cand:
            c.setdefault("_prio", PRIO.get(c["type"], 1))
            c["_seg"] = i
            out.append(c)
    return out


PRIO = {"stat": 5, "transfer": 5, "ring": 5, "brand": 4, "date": 4, "steps": 4, "checklist": 4, "vs": 5,
        "countdown": 3, "location": 3, "warning": 4, "qa": 2, "list": 3, "cta": 3, "big_caption": 1}


# ── Gemini ──────────────────────────────────────────────────────────────
PROMPT = """You are the motion-graphics director for a 2026-style talking-head video (Burmese speaker).
Pick moments where an animated infographic / realistic UI element makes the point land.
Available types (name: params) — use ONLY these:
%s
Rules: at most %d beats; never two beats within %.1fs; prefer concrete facts (numbers, money, dates,
brands, places, lists, comparisons, questions). Keep every text param SHORT (<= 28 chars), in the
speaker's language (Burmese), numbers as Western digits. `anchor` = the exact word from the line that
the graphic should hit on.
Return ONLY a JSON array: [{"line": <n>, "type": "...", "anchor": "...", ...params}]

Lines (n. [start s] text):
%s
"""


def _type_doc():
    T = types()
    return "\n".join(f"- {k}: {json.dumps(v['params'], ensure_ascii=False)}" for k, v in T.items())


def gemini(segs, dur, pack, log=print):
    if os.environ.get("IKKI_DIRECTOR_AI", "1") == "0" or not segs:
        return None
    if getattr(G, "dead", lambda: False)():
        return None
    lines = "\n".join(f"{i + 1}. [{_t0(s):.1f}] {s.get('text', '')}" for i, s in enumerate(segs[:220]))
    mx = max(2, int(round(pack["per_min"] * dur / 60.0)))
    prompt = PROMPT % (_type_doc(), mx, pack["gap"], lines)
    k = None
    try:
        k = G.key(MODEL, prompt, b"director-v1")
        txt = G.get(k)
    except Exception:
        txt = None
    if not txt:
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}}
        try:
            G.throttle()
            r = urllib.request.Request(G.endpoint(MODEL), data=json.dumps(body).encode(),
                                       headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(r, timeout=120) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
            if k:
                G.put(k, txt)
        except Exception as e:
            try:
                G.log_fail("director", 1, 1, None, str(e)[:120], final=True)
            except Exception:
                pass
            log(f"  ⓘ director · Gemini မရ ({type(e).__name__}) ⇒ rule-based")
            return None
    m = re.search(r"\[.*\]", txt or "", re.S)
    if not m:
        return None
    try:
        arr = json.loads(m.group(0))
    except ValueError:
        return None
    out = []
    for it in arr if isinstance(arr, list) else []:
        if not isinstance(it, dict):
            continue
        try:
            li = int(it.pop("line")) - 1
        except (KeyError, TypeError, ValueError):
            continue
        if not (0 <= li < len(segs)):
            continue
        it["_seg"] = li
        it["_prio"] = PRIO.get(str(it.get("type")), 2) + 2   # AI ရွေးချက် ဦးစားပေး
        out.append(it)
    return out


# ── schema validation ───────────────────────────────────────────────────
def validate(b):
    """registry schema နဲ့ စစ် + coerce — မမှန်လျှင် `None`"""
    T = types()
    t = str(b.get("type") or "")
    if t not in T:
        return None
    out = {"type": t}
    for name, kind in T[t]["params"].items():
        opt = kind.endswith("?")
        kind = kind.rstrip("?")
        v = b.get(name)
        if v in (None, "", []):
            if opt:
                continue
            return None
        try:
            if kind == "str":
                v = _clip(str(v).translate(_D) if re.fullmatch(r"[0-9၀-၉,\.%]+", str(v)) else v)
            elif kind == "num":
                v = float(str(v).translate(_D).replace(",", "").rstrip("%"))
            elif kind == "str[]":
                v = [_clip(x, 26) for x in list(v) if str(x).strip()][:5]
                if len(v) < 2:
                    return None
            elif kind.startswith("["):
                rows = []
                for row in list(v)[:5]:
                    a, c = list(row)[:2]
                    if kind == "[label,num][]":
                        rows.append([_clip(a, 16), float(str(c).translate(_D).replace(",", ""))])
                    else:
                        rows.append([_clip(a, 16), _clip(c, 18)])
                if len(rows) < 2:
                    return None
                v = rows
            elif kind == "num[]":
                v = [float(str(x).translate(_D)) for x in list(v)][:12]
                if len(v) < 2:
                    return None
            elif kind == "a|b":
                v = "a" if str(v).lower().startswith("a") else "b"
        except (TypeError, ValueError):
            return None
        out[name] = v
    if t == "ring" and not (0 < out["pct"] <= 100):
        return None
    return out


# ── schedule: density · spacing · variety · placement ─────────────────────
def _free(t0, t1, busy):
    return all(t1 <= a or t0 >= b for a, b in busy)


def schedule(cands, segs, dur, pack="default", busy=(), face_x=None, max_n=None):
    P = PACKS.get(pack, PACKS["default"])
    T = types()
    cap = max(1, int(round(P["per_min"] * max(dur, 20.0) / 60.0)))
    if max_n is not None:
        cap = max(0, min(cap, int(max_n)))
    same_cap = max(MAX_SAME, int(round(MAX_SAME * dur / 60.0)))
    taken, used, last_center, seen = [], {}, -1e9, set()
    # ဦးစားပေး မြင့် ⇒ ရှေ့ · တူလျှင် အစောပိုင်း
    for c in sorted(cands, key=lambda x: (-x.get("_prio", 1), x.get("_seg", 0))):
        if len(taken) >= cap:
            break
        v = validate(c)
        if not v:
            continue
        seg = segs[c["_seg"]] if 0 <= c.get("_seg", -1) < len(segs) else None
        if seg is None:
            continue
        at = anchor_time(seg, c.get("anchor") or "")
        meta = T[v["type"]]
        d = float(meta["dur"][1])
        if at < P["first"] or at + d > dur - TAIL + 1.0 or at > dur - TAIL:
            continue
        if used.get(v["type"], 0) >= same_cap:
            continue
        if any(abs(at - x["at"]) < max(P["gap"], 0.5 * (d + x["dur"])) for x in taken):
            continue
        if not _free(at - 0.2, at + d, busy):
            continue
        sig = (v["type"], json.dumps({k: v[k] for k in v if k in ("value", "name", "place", "items", "pct", "label", "steps")},
                                     ensure_ascii=False, sort_keys=True))
        if v["type"] == "stat":
            sig = ("stat", v.get("value"))
        if sig in seen:
            continue
        seen.add(sig)
        center = meta["zone"] == "center"
        if center and at - last_center < P["center_gap"]:
            continue
        v.update(at=round(at, 3), dur=d)
        taken.append(v)
        used[v["type"]] = used.get(v["type"], 0) + 1
        if center:
            last_center = at
    taken.sort(key=lambda x: x["at"])
    # variety — type တူ ဆက်တိုက် ⇒ နောက်တစ်ခုကို variant ပြောင်း
    for a, b in zip(taken, taken[1:]):
        if a["type"] == b["type"]:
            b["variant"] = "light" if a.get("variant") != "light" else "glass"
    # placement — မျက်နှာ ဘယ်ဘက်ဆို ညာ · ညာဘက်ဆို ဘယ် · အလယ်ဆို အလှည့်ကျ
    flip = 0
    for b in taken:
        z = T[b["type"]]["zone"]
        if z != "side":
            continue
        if face_x is None or 0.4 <= face_x <= 0.6:
            b["pos"] = "right" if flip % 2 == 0 else "left"
            flip += 1
        else:
            b["pos"] = "right" if face_x < 0.5 else "left"
    return taken


def direct(segs, dur, pack="default", busy=(), face_x=None, log=print, ai=True, cta_end=False, max_n=None,
           avoid=()):
    """ဝါကျ (`o0/o1` · `words`) ⇒ beat စာရင်း。 `busy` = [(a, b)] ရှောင်ရမည့် အချိန်"""
    segs = [s for s in (segs or []) if str(s.get("text") or "").strip()]
    if not segs or dur <= 0:
        return []
    cands = rules(segs, dur)
    src = "rules"
    if ai:
        g = gemini(segs, dur, PACKS.get(pack, PACKS["default"]), log=log)
        if g:
            cands = g + cands
            src = "gemini+rules"
    # ⚠️ user taste — ခဏခဏ ဖြုတ်/လဲခဲ့သော type ကို မရွေး (`taste.avoid_types`)
    if avoid:
        av = set(avoid)
        n0 = len(cands)
        cands = [c for c in cands if str(c.get("type")) not in av]
        if n0 != len(cands):
            log(f"  ♡ taste · {', '.join(sorted(av))} ရှောင် ({n0 - len(cands)} ခု)")
    out = schedule(cands, segs, dur, pack=pack, busy=busy, face_x=face_x, max_n=max_n)
    # ⚠️ CTA ကိုလည်း `max_n` (gfx_share ဘောင်) ထဲက ယူရမည် — ဘောင်ပြင်ပ ထည့်မိ၍ smoke 37s မှာ
    #    gfx_share 0.253 > 0.18 ⇒ QC ကျ (၂၀၂၆-၁၀-၀၇)
    room = max_n is None or len(out) < int(max_n)
    if cta_end and room and dur > 20 and not any(b["type"] == "cta" for b in out):
        at = round(dur - 3.2, 3)
        if _free(at - 0.2, dur, busy) and all(abs(at - b["at"]) >= b["dur"] + 0.3 for b in out if b["at"] < at):
            out.append(dict(type="cta", text="Subscribe", at=at, dur=3.0))
    log(f"  🎬 director ({src}) · beat {len(out)} ခု · "
        + " · ".join(f"{b['type']}@{b['at']:.1f}" for b in out))
    return out


def face_x_of(frames):
    xs = [float(f.get("fx")) for f in (frames or []) if f.get("nf") and f.get("fx") is not None]
    if not xs:
        return None
    xs.sort()
    return xs[len(xs) // 2]
