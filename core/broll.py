#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · B-roll စာကြည့်တိုက်。

⚠️ B-roll ရဲ့ အခက်ဆုံး အပိုင်းက **ဘယ်ရုပ်က ဘယ်စကားကို ဆိုလိုလဲ သိရတာ**ပါ。
   ဖိုင်နာမည် (C0825.MP4) က ဘာမှ မပြော。 ⇒ clip တစ်ခုချင်းရဲ့ frame ကို
   Gemini ကို ပြပြီး **ဘာမြင်ရလဲ** မေးသည် (မြန်မာ + English keyword)。

⚠️ index လုပ်တာက Mac ပေါ်မှာသာ လုပ်ရသည် — footage က ဒီမှာ ရှိသည်。
   VPS မှာ မရှိ。 ⇒ CLI:  python3 core/broll.py index "<folder>"

⚠️ ပြီးသား ဗီဒီယိုတွေကို **မထည့်ရ** — ၁၀ မိနစ်ထက် ရှည်တာ၊ စာတန်း/ဂရပ်ဖစ်
   ပါပြီးသားတာတွေ B-roll မဟုတ်。 ၁.၅s–၆၀s သာ လက်ခံသည်。
"""
import base64, json, os, re, subprocess, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gemguard as G

ROOT  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "broll")
INDEX = os.path.join(ROOT, "index.json")
MODEL = os.environ.get("IKKI_GEMINI_MODEL", "gemini-3.1-flash-lite")
MIN_D, MAX_D = 1.5, 60.0
CLIPS = os.path.join(ROOT, "clips")     # ⚠️ သုံးဖြစ်တဲ့ clip ကို ဒီထဲ ကူးသည်
MAX_KEEP = 12.0                          # clip တစ်ခုလျှင် သိမ်းမည့် အရှည်
EXT = (".mp4",".mov",".m4v",".MP4",".MOV")
# ⚠️ **ပုံ (still) ကိုပါ လက်ခံသည်** — Zin: "သက်ဆိုင်ရာ section နဲ့ လိုက်ဖက်မယ့်
#    Graphic Photo သို့ Stock လေးတွေ ထည့်ပေးပါ"。 ပုံက ရုပ်ရှင်ထဲ တည်ငြိမ်နေလျှင်
#    frame သေနေသလို ဖြစ်၍ **နှေးနှေး ရွေ့ပေး**ရသည် (prep ကို ကြည့်ပါ)。
IMG = (".jpg",".jpeg",".png",".webp",".JPG",".JPEG",".PNG",".WEBP")
STILL_DUR = 6.0          # ပုံတစ်ခုကို ဘယ်လောက်ထိ ဆန့်နိုင်လဲ

# ⚠️ usable ရဲ့ စည်းမျဉ်းကို **ပြန်ရေးထားသည်**。 ပထမ version က
#    "လူပုံ အနီးကပ်" နှင့် "screen" ကို ငြင်းခိုင်းမိသဖြင့် ကျောင်းသား ·
#    လက်ပ်တော့ · စာရေးနေသည် စတဲ့ ရုပ်တွေ **အားလုံး ပယ်ခံခဲ့ရသည်** —
#    အဲဒါတွေက ZAE ရဲ့ N5 ONLINE ကြော်ငြာမှာ တကယ် သုံးထားတဲ့ ရုပ်များ。
#    ⇒ တကယ် ပယ်ရမှာက **ပြီးသွားပြီးသား ဗီဒီယို** (စာတန်း burn ထားတာ ·
#      watermark · logo) နှင့် ပုံရိပ် မကောင်းတာ ချည်းသာ。
PROMPT = """ဤဗီဒီယိုဖရိမ်းထဲ ဘာမြင်ရလဲ ဖြေပါ။

JSON တစ်ခုသာ ပြန်ပါ:
{"my": ["မြန်မာ keyword 3-6 လုံး"], "en": ["english keywords 3-6"],
 "kind": "place|people|object|screen|food|nature|city|indoor|document",
 "usable": true}

keyword စည်းကမ်း:
- **တိတိကျကျ** ဖြစ်ရမည် ("မြင်ကွင်း" မဟုတ်၊ "တိုကျိုလမ်း" လို)
- လူ · လုပ်ဆောင်ချက် · ပစ္စည်း · နေရာ ကို ခွဲပြောပါ
  (ဥပမာ "ကျောင်းသား" + "လက်ပ်တော့" + "စာရေးနေသည်")

usable=false ဖြစ်ရမည့် အခြေအနေ — **ဒီ ၄ မျိုးသာ**:
1. ပြီးသွားပြီးသား ဗီဒီယို — စာတန်း (subtitle) burn ထားသည် ·
   lower third · progress bar · watermark · channel logo ပါနေသည်
2. မျက်နှာပြင်တစ်ခုလုံး စာ/slide/presentation ဖြစ်နေသည်
3. အလွန်မှောင် (ဘာမှ မမြင်ရ) ဒါမှမဟုတ် focus လုံးဝ လွဲနေသည်
4. ဓာတ်ပုံ အသေ (လှုပ်ရှားမှု မရှိ) ဒါမှမဟုတ် frame ဗလာ

⚠️ လူ ပါနေတာ · အနီးကပ် ရိုက်ထားတာ · laptop/ဖုန်း screen ပါတာ ·
   နောက်ခံ ဝါးနေတာ (bokeh) — **ဒါတွေ usable=true**。 B-roll ဆိုတာ
   အဲဒီလို ရုပ်တွေပါ。

ရှင်းလင်းချက် မထည့်ရ။ JSON ချည်းသာ"""

def probe(p):
    o = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height","-show_entries","format=duration",
        "-of","json",p], capture_output=True, text=True).stdout
    try:
        j = json.loads(o); s = j["streams"][0]
        return dict(w=s["width"], h=s["height"], dur=float(j["format"]["duration"]))
    except Exception:
        return None

def _frame(p, at, out):
    subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{at:.2f}","-i",p,
        "-frames:v","1","-vf","scale=768:-2","-q:v","4",out], check=True)

def _ask(img):
    b64 = base64.b64encode(open(img,"rb").read()).decode()
    body = {"contents":[{"parts":[{"text":PROMPT},
            {"inline_data":{"mime_type":"image/jpeg","data":b64}}]}],
            "generationConfig":{"temperature":0.1}}
    for i in range(3):
        G.throttle()
        r = urllib.request.Request(G.endpoint(MODEL), data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=120) as f:
                d = json.loads(f.read())
            t = "".join(x.get("text","") for x in d["candidates"][0]["content"]["parts"])
            m = re.search(r"\{.*\}", t, re.S)
            if not m: G.log_fail("broll_describe", i + 1, 3, None, "JSON မတွေ့", final=True)
            return json.loads(m.group(0)) if m else None
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8","replace")
            G.log_fail("broll_describe", i + 1, 3, e.code, raw, final=G.fatal(e.code, raw))
            if G.fatal(e.code, raw): return None
            mm = re.search(r'"retryDelay"\s*:\s*"(\d+)s"', raw)
            time.sleep(int(mm.group(1)) if mm else 6*(i+1))
        except Exception as e:
            G.log_fail("broll_describe", i + 1, 3, None, f"{type(e).__name__}: {e}")
            time.sleep(5*(i+1))
    G.log_fail("broll_describe", 3, 3, None, "retry ကုန် — None ပြန်", final=True)
    return None

def load():
    try:
        d = json.load(open(INDEX, encoding="utf-8"))
        # ⚠️ ကူးထားတဲ့ ဖိုင် မရှိတော့တာတွေ ဖယ်ရမည် — မဖယ်လျှင် render ပျက်သည်
        d["clips"] = [c for c in d.get("clips") or [] if os.path.exists(c.get("path",""))]
        return d
    except Exception: return {"clips": []}

def index(folder, limit=None, log=print):
    os.makedirs(ROOT, exist_ok=True)
    db = load()
    seen = {c["path"]: c for c in db["clips"]}
    files=[]
    for r,_,fs in os.walk(folder):
        for f in fs:
            if f.endswith(EXT + IMG) and not f.startswith("."):
                files.append(os.path.join(r,f))
    files.sort()
    log(f"  {len(files)} ဖိုင် တွေ့သည်")
    new=skip=bad=0
    for p in files:
        if limit and new >= limit: break
        try: sz = os.path.getsize(p)
        except OSError: continue
        old = seen.get(p)
        if old and old.get("size") == sz: skip += 1; continue
        is_img = p.endswith(IMG)
        if is_img:
            # ⚠️ ပုံမှာ dur မရှိ — `STILL_DUR` ဖြင့် ယူသည်。 Gemini ကို
            #    frame ထုတ်စရာ မလို、ပုံကိုယ်တိုင်က frame ဖြစ်သည်。
            try:
                from PIL import Image as _I
                with _I.open(p) as _im: w0, h0 = _im.size
            except Exception:
                bad += 1; continue
            m = dict(dur=STILL_DUR, w=w0, h=h0)
            img = os.path.join(ROOT, "_f.jpg")
            try:
                subprocess.run(["ffmpeg","-v","error","-y","-i",p,
                    "-vf","scale=640:-1","-frames:v","1",img], check=True)
            except Exception: bad += 1; continue
        else:
            m = probe(p)
            if not m or not (MIN_D <= m["dur"] <= MAX_D):
                bad += 1; continue                  # ⚠️ ပြီးသား ဗီဒီယို ဖယ်
            img = os.path.join(ROOT, "_f.jpg")
            try: _frame(p, m["dur"]*0.4, img)
            except Exception: bad += 1; continue
        tags = _ask(img)
        if not tags or not tags.get("usable"):
            bad += 1
            log(f"  ✗ {os.path.basename(p)[:34]:36} {'မသုံးရ' if tags else 'မရ'}")
            continue
        # ⚠️ **clip ကို စာကြည့်တိုက်ထဲ ကူးရမည်** — index က ပြင်ပ disk ရဲ့
        #    လမ်းကြောင်းကိုသာ သိမ်းလျှင် disk ခွာတာနဲ့ B-roll ပျောက်သည်
        #    (တကယ် ဖြစ်ခဲ့ — disk ခွာပြီး အလုပ် ရပ်သွားခဲ့)。
        #    အရှည်ကို ၁၂s ဖြတ်ပြီး ချုံ့သိမ်းသဖြင့် နေရာ သိပ်မကုန်။
        os.makedirs(CLIPS, exist_ok=True)
        if is_img:
            lp = os.path.join(CLIPS, f"{abs(hash(p))%10**10}.jpg")
            try:
                subprocess.run(["ffmpeg","-v","error","-y","-i",p,
                    "-vf","scale=-2:1280:force_divisible_by=2","-q:v","3",lp], check=True)
            except Exception:
                bad += 1; log(f"  ✗ {os.path.basename(p)[:34]:36} ကူးမရ"); continue
            c = dict(path=lp, src=p, size=sz, dur=STILL_DUR, w=m["w"], h=m["h"],
                     my=tags.get("my") or [], en=tags.get("en") or [],
                     kind=tags.get("kind","object"), still=True)
            seen[p] = c; new += 1
            log(f"  ✓ {os.path.basename(p)[:34]:36} ပုံ · {' · '.join(c['my'][:3])}")
            db["clips"] = list(seen.values())
            json.dump(db, open(INDEX,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
            continue
        lp = os.path.join(CLIPS, f"{abs(hash(p))%10**10}.mp4")
        keep = min(MAX_KEEP, m["dur"])
        ss = max(0.0, min(m["dur"]-keep, m["dur"]*0.2))
        try:
            subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{ss:.2f}","-i",p,
                "-t",f"{keep:.2f}","-an","-vf","scale=-2:1080:force_divisible_by=2",
                # ⚠️ B-roll က crop ခံရမှာမို့ 1080 လုံလောက် — 1440 ဆို
                #    clip တစ်ခု ၁၅ MB ဖြစ်ပြီး ၂၀၀ ခုဆို ၃ GB ကုန်သည်。
                "-c:v","h264_videotoolbox","-b:v","6M",lp], check=True)
        except Exception as e:
            bad += 1; log(f"  ✗ {os.path.basename(p)[:34]:36} ကူးမရ"); continue
        c = dict(path=lp, src=p, size=sz, dur=round(keep,2), w=m["w"], h=m["h"],
                 my=tags.get("my") or [], en=tags.get("en") or [],
                 kind=tags.get("kind","object"))
        seen[p] = c; new += 1   # key က မူရင်း လမ်းကြောင်း
        log(f"  ✓ {os.path.basename(p)[:34]:36} {c['kind']:9} {' · '.join(c['my'][:3])}")
        db["clips"] = list(seen.values())
        json.dump(db, open(INDEX,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"\n  အသစ် {new} · ရှိပြီး {skip} · မသုံးရ {bad} · စုစုပေါင်း {len(seen)}")
    return len(seen)

# ── ရုပ် ↔ စကား တွဲခြင်း ─────────────────────────────────────
# ══ မြန်မာ cluster အဆင့် တူမှု ═══════════════════════════
# ⚠️ မြန်မာစာမှာ **စကားလုံးခွဲ space မရှိ** — "ကားအတွင်းခန်း" နဲ့ "ကား" ကို
#    token အတိအကျ နှိုင်းလျှင် ဘယ်တော့မှ မတူ။ ပထမ version က အဲဒီလို
#    လုပ်မိသဖြင့် စာကြောင်း ၄ ခုမှ ၁ ခုသာ တွဲမိခဲ့သည်。
#    ⇒ cluster စာရင်းချပြီး **အရှည်ဆုံး တူသော အပိုင်း** ကို ရှာသည်。
_CL = re.compile(r"[\u1000-\u1021\u103F\u1040-\u1049\u104C-\u104F]"
                 r"(?:\u1039[\u1000-\u1021]|[\u102B-\u103E])*"
                 r"|[A-Za-z0-9]+|[^\s]")
# အဓိပ္ပာယ် မရှိသော cluster — တူလျှင် အမှား တွဲမှု ဖြစ်စေသည်
_SKIP = set("ပါ တယ် သည် မယ် နေ ဖြစ် လို့ တာ ကို က မှာ နဲ့ ရ တဲ့ တွေ လဲ ပြီး ဒီ အဲ ဒါ ချင် နိုင် လျှင် ဆို".split())

def _cl(t):
    return [c for c in _CL.findall((t or "").strip()) if c.strip()]

def _lcs(a, b):
    """cluster စာရင်း နှစ်ခုရဲ့ အရှည်ဆုံး တူသော အပိုင်း အရှည် (cluster အရေအတွက်)"""
    if not a or not b: return 0
    prev=[0]*(len(b)+1); best=0
    for i in range(1, len(a)+1):
        cur=[0]*(len(b)+1)
        for j in range(1, len(b)+1):
            if a[i-1]==b[j-1]:
                cur[j]=prev[j-1]+1
                if cur[j]>best: best=cur[j]
        prev=cur
    return best

def _score(text, clip):
    """စာကြောင်း ↔ clip tag တူမှု အမတ်。 ၂ cluster အထက် တူမှ ရေတွက်သည်。"""
    tc = _cl(text); tot = 0
    for tag in (clip.get("my") or []):
        for w in re.split(r"[\s·,။၊]+", tag):
            w = w.strip()
            if len(w) < 2 or w in _SKIP: continue
            n = _lcs(tc, _cl(w))
            if n >= 2: tot += n          # ၂ cluster = "ကား"+"အ" စသဖြင့်
    for tag in (clip.get("en") or []):
        for w in re.findall(r"[A-Za-z]{4,}", tag.lower()):
            if w in (text or "").lower(): tot += 2
    return tot

def _toks(t):
    return set(x for x in re.split(r"[\s·,။၊]+", (t or "").lower()) if len(x) > 1)

def pick(segs, want, used=None, min_score=3):
    """(seg_index, clip, score) စာရင်း — keyword တူမှုဖြင့် တွဲသည်。

    ⚠️ **keyword တူမှုဖြင့်သာ** တွဲသည် — Gemini ကို "ဘယ်ရုပ်က ဘယ်စကား"
       ဟု မမေးပါ。 မေးလျှင် index မှားပြီး မဆိုင်တဲ့ရုပ် ဝင်လာနိုင်သည်。
       tag တွေက Gemini ကနေ လာပြီးသား — အဲဒီမှာ ဆင်ခြင်မှု လိုသည်。
    """
    db = load(); clips = db.get("clips") or []
    if not clips or want <= 0: return []
    used = set(used or [])
    out=[]
    for i,s in enumerate(segs):
        st = _toks(s.get("text"))
        if not st: continue
        best=None; bs=0
        for c in clips:
            if c["path"] in used: continue
            score = _score(s.get("text"), c)
            if score > bs: bs=score; best=c
        if best and bs >= min_score:
            out.append((i, best, bs)); used.add(best["path"])
    out.sort(key=lambda x: -x[2])
    return out[:want]

def prep(clip, W, H, dur, out, fps=30):
    """B-roll ကို theme frame အရွယ် ဖြတ်/ချုံ့ပြီး အသံမပါ clip လုပ်သည်。

    ⚠️ **အသံ မထည့်ရ** — စကားသံက အောက်မှာ ဆက်နေရမည်。 B-roll ရဲ့ အသံ
       ထည့်လျှင် စကား ထပ်ပြီး ဘာမှ မကြားရ။
    """
    if clip.get("still"):
        # ⚠️ ပုံကို **တည်ငြိမ် မထားရ** — frame သေနေသလို ဖြစ်သည် (skill
        #    `ikki-presentation` §5: "the element should never fully stop")。
        #    ⇒ နှေးနှေး တိုးဝင် + ဘေးတိုက် ရွေ့ (Ken Burns)。 အရှိန်က
        #    ရုပ်ရှင်ဆန်အောင် ဒီလောက်ပဲ — ပိုလျှင် မူးသည်。
        z0, z1 = 1.04, 1.13
        n = max(2, int(dur*fps))
        subprocess.run(["ffmpeg","-v","error","-y","-loop","1","-i",clip["path"],
            "-t",f"{dur:.2f}","-an","-vf",
            f"scale={W*3}:{H*3}:force_original_aspect_ratio=increase,"
            f"crop={W*3}:{H*3},"
            f"zoompan=z='{z0}+({z1}-{z0})*on/{n}':"
            f"x='iw/2-(iw/zoom/2)+(on/{n}-0.5)*iw*0.012':"
            f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={fps},"
            f"format=yuv420p",
            "-c:v","h264_videotoolbox","-b:v","12M",out], check=True)
        return out
    ss = max(0.0, min(clip["dur"]-dur, clip["dur"]*0.25))
    subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{ss:.2f}","-i",clip["path"],
        "-t",f"{dur:.2f}","-an",
        "-vf",f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"format=yuv420p,fps={fps}",
        "-c:v","h264_videotoolbox","-b:v","12M",out], check=True)
    return out

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "index":
        lim = int(sys.argv[3]) if len(sys.argv) > 3 else None
        index(sys.argv[2], limit=lim)
    else:
        db = load()
        print(f"  clip {len(db.get('clips') or [])} ခု · {INDEX}")
        from collections import Counter
        print("  ", dict(Counter(c["kind"] for c in db.get("clips") or [])))

# ══ Gemini semantic တွဲမှု ════════════════════════════════
MPROMPT = """မြန်မာဗီဒီယိုတစ်ခု၏ စာတမ်းနှင့် B-roll ရုပ်ကြမ်း စာရင်း ပေးထားသည်။

စာကြောင်းတစ်ခု ပြောနေချိန်တွင် **အဲဒီစာကြောင်းက ပြောတဲ့အရာကို မြင်ရမယ့်**
ရုပ်ကြမ်းကို တွဲပေးပါ။

စည်းကမ်း:
- အများဆုံး %d တွဲ
- ရုပ်က စာကြောင်းရဲ့ အကြောင်းအရာနှင့် **တကယ် ကိုက်မှသာ** တွဲရမည်
- **မကိုက်လျှင် မတွဲရ** — အလွတ် array ပြန်ပေးလို့ ရသည်။ မဆိုင်တဲ့ရုပ်
  ထည့်လိုက်ရင် ဗီဒီယိုတစ်ခုလုံး ယုတ်လျော့သွားသည်
- ရုပ်တစ်ခုကို တစ်ခါသာ သုံးရမည်
- `confidence` ကို ၀–၁ အတွင်း အမှန်တကယ်ကိုက်ညီမှုအတိုင်း ပေးရမည်
- JSON array ကိုသာ ပြန်ပါ

ပုံစံ: [{"line": 3, "clip": "c07", "confidence": 0.92, "why": "ကားပြောနေ"}, ...]

ရုပ်ကြမ်း စာရင်း:
%s

စာတမ်း:
%s"""

def match(segs, want, used=None, log=print, strict=False):
    """Gemini ဖြင့် စာကြောင်း↔ရုပ် တွဲသည်。

    `strict=True` (premium talking head) မှာ LLM semantic match ကိုသာ လက်ခံသည်။
    Transcript နဲ့မဆိုင်သော stock ကို budget ပြည့်ရန် မထည့်ခြင်းက clip နည်းသွားတာ
    ထက် ပိုကောင်းသည်။ Legacy styles မှာသာ lexical fallback ကို ဆက်ထားသည်。

    ⚠️ Gemini ပြန်ပေးသော clip id ကို **ရှိမရှိ စစ်ရမည်** — ဖန်လာလျှင်
       မဆိုင်တဲ့ရုပ် ဝင်သွားမည်。 ဒါက ပထမက Gemini မမေးဘဲ ထားခဲ့တဲ့ အကြောင်းရင်း；
       ခုတော့ စစ်လိုက်သဖြင့် မေးလို့ ရသည်。
    """
    import json, re, time, urllib.request, urllib.error
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gemguard as G
    import topics as T

    db = load(); clips = db.get("clips") or []
    used = set(used or [])
    av = [c for c in clips if c["path"] not in used]
    # Semantic မှန်နေလည်း အမှောင်/ဗလာ clip က premium မဖြစ်နိုင်။ match path
    # က အရင် screen() မဖြတ်ခဲ့လို့ generic-fill နဲ့ မတူသော quality gate ဖြစ်နေခဲ့သည်။
    av = screen(av, log=log)
    if not av or want <= 0 or not segs: return []

    ids = {}
    rows = []
    # ⚠️ ၆၀ ကန့်သတ်ချက်က **အသစ် ထည့်ထားသော clip တွေကို Gemini မမြင်**စေခဲ့
    #    (၂၀၂၆-၀၉-၁၇ — stock ၁၈ ခု ထည့်ပြီးနောက် index ၇၉ ဖြစ်သွားပြီး
    #     အသစ်တွေက စာရင်း အောက်ဆုံးမှာ ကျန်ခဲ့သည်)。 ⇒ ၁၂၀ သို့ တိုးသည်。
    for i, c in enumerate(av[:120]):
        cid = "c%02d" % i; ids[cid] = c
        rows.append(f'{cid}: {" · ".join((c.get("my") or [])[:4])}  [{c["dur"]:.0f}s]')
    lines = "\n".join(f"{i+1}. {s['text']}" for i, s in enumerate(segs[:80]))
    body = {"contents":[{"parts":[{"text": MPROMPT % (want, "\n".join(rows), lines)}]}],
            "generationConfig":{"temperature":0.1}}
    for k in range(2):
        G.throttle()
        r = urllib.request.Request(G.endpoint(T.MODEL), data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text","") for p in d["candidates"][0]["content"]["parts"])
            m = re.search(r"\[.*\]", txt, re.S)
            if not m:
                G.log_fail("broll_match", k + 1, 2, None, "JSON မတွေ့", final=True); break
            out = []; seen = set()
            bad = 0
            for x in json.loads(m.group(0)):
                n = int(x.get("line", 0)) - 1
                cid = str(x.get("clip", ""))
                if cid not in ids: bad += 1; continue      # ⚠️ ဖန်လာတာ ဖြုတ်
                if not (0 <= n < len(segs)): bad += 1; continue
                if cid in seen or n in {o[0] for o in out}: continue
                # Prompt က confidence မပေးလျှင် legacy matching ကို မပျက်စေရန် 0.9
                # လို့ယူသည်။ New prompt/strict pipeline က low-confidence ကို ပယ်သည်။
                try: conf = float(x.get("confidence", 0.9))
                except (TypeError, ValueError): conf = 0.0
                if strict and conf < 0.80:
                    continue
                seen.add(cid); out.append((n, ids[cid], round(conf * 10, 2)))
            if bad: log(f"  B-roll · Gemini id မှား {bad} ခု ဖြုတ်ပြီး")
            if out:
                G.tally("broll", True)
                log(f"  B-roll · Gemini တွဲ {len(out)} ခု")
                return out[:want]
            break
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8","replace")
            G.log_fail("broll_match", k + 1, 2, e.code, raw, final=G.fatal(e.code, raw) or k == 1)
            if G.fatal(e.code, raw): break
            time.sleep(6*(k+1))
        except Exception as e:
            G.log_fail("broll_match", k + 1, 2, None, f"{type(e).__name__}: {e}", final=(k == 1))
            time.sleep(4*(k+1))
    G.tally("broll", False, "Gemini တွဲ မရ")
    # ⚠️ Gemini မရလျှင် စာလုံးတူမှုဖြင့် ဖြည့်သည် — ဒါပေမဲ့ **အမှတ် နိမ့်တာကို
    #    မယူရ**。 ၃ နဲ့ ယူတော့ "ROLEX နာရီ" · "Hakone ကားလမ်း" တို့ ဂျပန်စာ
    #    သင်တန်း ဗီဒီယိုထဲ ဝင်လာခဲ့သည် (Zin ၂၀၂၆-၀၉-၁၇)。 ⇒ ၆ သို့ တင်。
    if strict:
        log("  B-roll · strict semantic match မရ — lexical fallback မသုံး")
        return []
    lex = pick(segs, want, used, min_score=6)
    if lex: log(f"  B-roll · စာလုံးတူမှုဖြင့် {len(lex)} ခု (Gemini မရ)")
    return lex


# ══ ဗီဒီယိုနှင့် လိုက်ဖက်သော clip ရွေးခြင်း ══════════════════
# ⚠️ စာလုံးတူမှု အမှတ်ဖြင့် **မရွေးရ**。 တိုင်းကြည့်ရာ ဂျပန်စာသင်တန်း
#    ကြော်ငြာအတွက် အမြင့်ဆုံး အမှတ် (၁၀) က "ဂျပန်ပုံစံ ထမင်းစားခန်း"
#    ဖြစ်နေပြီး "ကျောင်းသား · လက်ပ်တော့" က ၈ သာ ရသည် — "ဂျပန်" ဆိုတဲ့
#    စာလုံး ထပ်တာကို ရေတွက်နေလို့。 ⇒ **အဓိပ္ပာယ်ကို Gemini ကို မေးရမည်**。
SUIT = """မြန်မာဗီဒီယိုတစ်ခု၏ စာတမ်းနှင့် ရုပ်ကြမ်း စာရင်း ပေးထားသည်။

ဤဗီဒီယိုရဲ့ **အကြောင်းအရာနှင့် လိုက်ဖက်သော** ရုပ်ကြမ်းများကို ရွေးပေးပါ။

စည်းကမ်း:
- ဗီဒီယိုက ဘာအကြောင်းလဲ အရင် ဆုံးဖြတ်ပါ
- အဲဒီအကြောင်းအရာနှင့် **တကယ် လိုက်ဖက်မှသာ** ရွေးရမည်
- ဥပမာ — ပညာရေး/သင်တန်း ဗီဒီယိုဆိုလျှင် စာလေ့လာနေသူ · လက်ပ်တော့ ·
  မှတ်စုစာအုပ် · စာသင်ခန်း က လိုက်ဖက်သည်；ကားမောင်းနေတာ ·
  အိမ်တွင်း ဒီဇိုင်း · အပန်းဖြေခရီး က **မလိုက်ဖက်**
- သံသယ ရှိလျှင် **မရွေးပါနှင့်** — မဆိုင်တဲ့ရုပ် ထည့်တာထက် ပြောသူကို
  ပြထားတာ ပိုကောင်းသည်
- JSON array ကိုသာ ပြန်ပါ

ပုံစံ: ["c03", "c11", ...]

ရုပ်ကြမ်း စာရင်း:
%s

စာတမ်း:
%s"""

# ══ clip ရဲ့ ရုပ်အရည်အသွေး ═══════════════════════════════════
# ⚠️ ဒီကိန်းနှစ်ခုကို **N5 ONLINE reference ကို တိုင်း၍** ယူထားသည် —
#    အဲဒီမှာ B-roll shot ၁၀ ခုရှိပြီး အနိမ့်ဆုံး အလင်း ၆၉ · အနိမ့်ဆုံး
#    အသေးစိတ် ၄.၁ ဖြစ်သည်。 IKKI ထုတ်ခဲ့သော ZAE short မှာ **ဗလာစာအုပ်**
#    clip (အသေးစိတ် ၂.၁) က အစ ၁၆ စက္ကန့်လုံး ဖုံးခဲ့ပြီး ၄၅s မှာ
#    **မှောင်မည်း** clip (အလင်း ၃၀) ပါခဲ့သည် — Zin က "အရုပ်တွေ ပျောက်" ဟု
#    ပြောခဲ့သော render ပင်。
QLUM = 60.0     # အလင်း ပျမ်းမျှ အနည်းဆုံး
# ⚠️ QDET ကို ၄.၀ (reference ရဲ့ အနိမ့်ဆုံး) မှာ ထားလျှင် **တင်းလွန်း**သည် —
#    စာကြည့်တိုက် ၄၄ ခုလုံးကို ဖြတ်ပြီး တိုင်းတော့ အလေ့အလာ စာရေးနေသော
#    clip တွေက ၃.၄–၃.၉ ဖြစ်ပြီး ဗလာစာအုပ်/မှောင်သော ဟာတွေက ၂.၄ အောက်
#    ဖြစ်သည် — **၂.၄ နဲ့ ၃.၄ ကြားမှာ သဘာဝ ကွာဟချက်** ရှိသည်。 ၄.၀ မှာ
#    ဖြတ်တော့ B-roll က ၅၁% အစား ၁၈% ပဲ ကျန်ခဲ့သည် (တကယ် ဖြစ်ခဲ့)。
#    reference ရဲ့ အနိမ့်ဆုံး တစ်ခုတည်းကို floor လုပ်လျှင် ကိန်း ၁၀ ခုထဲက
#    အစွန်းတစ်ခုကို ချိန်နေသလို ဖြစ်သည် ⇒ ကွာဟချက် အလယ်မှာ ချသည်。
QDET = 3.2      # အလျားလိုက် gradient ပျမ်းမျှ (ပုံထဲ ဘာမှ မရှိလျှင် နိမ့်သည်)

def quality(c, ar=0.75):
    """(အလင်း, အသေးစိတ်) — index ထဲ cache လုပ်သည်。

    ⚠️ **ဗဟို crop ပြီးမှ တိုင်းရမည်**。 prep() က clip ကို ဒေါင်လိုက်
       အချိုးသို့ ဗဟိုမှ ဖြတ်သည် — 16:9 ရဲ့ အလယ် ၄၂% သာ ကျန်သည်。
       အပြည့်ကို တိုင်းလျှင် ဘေးက အသေးစိတ်တွေ ရေတွက်မိပြီး **ဗလာစာအုပ်**
       clip က ၄.၂ ရသည်၊ တကယ် ထွက်လာတဲ့ frame မှာတော့ ၂.၈ ပဲ (v25 မှာ
       တကယ် ဖြစ်ခဲ့ — gate ကို ဖြတ်သွားခဲ့သည်)。
    """
    if c.get("lum") is not None and c.get("det") is not None:
        return float(c["lum"]), float(c["det"])
    try:
        import numpy as np
        from PIL import Image
    except Exception:
        return 255.0, 99.0                      # တိုင်းလို့ မရလျှင် ခွင့်ပြု
    d = float(c.get("dur") or 3.0)
    lums=[]; dets=[]
    for f in (0.25, 0.5, 0.75):
        q = os.path.join(ROOT, "_q.png")
        try:
            _ss = [] if c.get("still") else ["-ss", f"{d*f:.2f}"]
            subprocess.run(["ffmpeg","-v","error","-y"] + _ss + ["-i", c["path"],
                "-frames:v","1","-vf",
                f"crop='min(iw,ih*{ar})':ih,scale=160:-1", q], check=True)
            a = np.asarray(Image.open(q).convert("RGB")).astype(np.int32)
        except Exception:
            continue
        lum = (a[:,:,0]*299 + a[:,:,1]*587 + a[:,:,2]*114)//1000
        lums.append(float(lum.mean()))
        dets.append(float(np.abs(np.diff(lum.astype(float), axis=1)).mean()))
    if not lums: return 255.0, 99.0
    c["lum"] = round(sum(lums)/len(lums), 1)
    c["det"] = round(sum(dets)/len(dets), 1)
    return c["lum"], c["det"]

def screen(clips, log=print):
    """မှောင်လွန်း/ဗလာလွန်းသော clip များကို ဖယ်သည်。"""
    ok=[]; cut=[]
    for c in clips:
        lum, det = quality(c)
        if lum < QLUM or det < QDET:
            cut.append((c, lum, det)); continue
        ok.append(c)
    if cut:
        log(f"  B-roll · ရုပ်အရည် မမီ၍ ဖယ် {len(cut)} ခု "
            + " · ".join(f"{(c.get('my') or ['?'])[0][:10]}(လင်း{l:.0f}/သေး{d:.1f})"
                         for c,l,d in cut[:4]))
        try:
            db = load()
            by = {x["path"]: x for x in db.get("clips") or []}
            for c in clips:
                if c["path"] in by and c.get("lum") is not None:
                    by[c["path"]]["lum"] = c["lum"]; by[c["path"]]["det"] = c["det"]
            json.dump(db, open(INDEX,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
        except Exception: pass
    return ok

def suitable(segs, clips, log=print):
    """ဗီဒီယိုနှင့် လိုက်ဖက်သော clip စာရင်း — မရလျှင် [] (ဖြည့်စရာ မရှိ)。"""
    import json, re, time, urllib.request, urllib.error
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gemguard as G, topics as T
    clips = screen(clips, log)
    if not clips or not segs: return []
    ids = {}
    rows = []
    for i, c in enumerate(clips[:80]):
        cid = "c%02d" % i; ids[cid] = c
        rows.append(f'{cid}: {" · ".join((c.get("my") or [])[:4])}')
    lines = "\n".join(f"{i+1}. {s['text']}" for i, s in enumerate(segs[:60]))
    body = {"contents": [{"parts": [{"text": SUIT % ("\n".join(rows), lines)}]}],
            "generationConfig": {"temperature": 0.1}}
    for k in range(2):
        G.throttle()
        r = urllib.request.Request(G.endpoint(T.MODEL), data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                d = json.loads(f.read())
            txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
            m = re.search(r"\[.*\]", txt, re.S)
            if not m:
                G.log_fail("broll_suit", k + 1, 2, None, "JSON မတွေ့", final=True); break
            out = [ids[x] for x in json.loads(m.group(0)) if x in ids]
            log(f"  B-roll · လိုက်ဖက်သော clip {len(out)} / {len(clips)} ခု (Gemini)")
            return out
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            G.log_fail("broll_suit", k + 1, 2, e.code, raw, final=G.fatal(e.code, raw) or k == 1)
            if G.fatal(e.code, raw): break
            time.sleep(5 * (k + 1))
        except Exception as e:
            G.log_fail("broll_suit", k + 1, 2, None, f"{type(e).__name__}: {e}", final=(k == 1))
            time.sleep(4 * (k + 1))
    # ⚠️ Gemini မရလျှင် **ဖြည့်စရာ မရှိ** ဟု ယူဆသည် — စာလုံးတူမှုဖြင့်
    #    ရွေးလျှင် မဆိုင်တဲ့ရုပ် ဝင်မည် (တိုင်းပြီး သိရသည်)。
    log("  B-roll · Gemini မရ — ကွက်လပ် မဖြည့်တော့ပါ")
    return []
