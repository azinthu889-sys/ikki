#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI API — FastAPI。 web က ဒီကို ခေါ်သည်၊ Mac worker ကလည်း ဒီကိုပဲ ခေါ်သည်。

⚠️ worker က အိမ်က Mac ပေါ်မှာ ဖြစ်ပြီး NAT နောက်မှာ ရှိသည် — server က
   worker ကို **ပြန်မခေါ်နိုင်**။ ဒါကြောင့် worker က ဆွဲယူသည် (claim)。
"""
import json, sys, os, shutil, time
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Header, Form
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import db
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
try:
    import store as ST
except Exception as _e:
    # ⚠️ store.py မပါလျှင် **site တစ်ခုလုံး မကျစေရ** — local disk mode ဖြင့်
    #    ဆက်လုပ်သည်。 image ထဲ core/store.py ကူးမမိသဖြင့် Bad Gateway
    #    ဖြစ်ခဲ့သည် (တကယ်)。
    class ST:                      # type: ignore
        @staticmethod
        def on(): return False
    print(f"⚠️ store မရ ({_e}) → local disk mode", flush=True)
try:
    import formats as FM
except Exception as _e:
    # ⚠️ formats မပါလျှင်လည်း site မကျစေရ — brand ရဲ့ native အရွယ်ကိုပဲ သုံးမည်
    class FM:                      # type: ignore
        NATIVE = {"zae": "3:4", "zjl": "16:9"}
        @staticmethod
        def keys(): return []
        @staticmethod
        def listing(): return []
    print(f"⚠️ formats မရ ({_e})", flush=True)

DATA   = os.environ.get("IKKI_DATA", "/data")
UP     = os.path.join(DATA, "uploads")
OUT    = os.path.join(DATA, "out")
WEB    = os.environ.get("IKKI_WEB", os.path.join(os.path.dirname(__file__), "..", "web"))
UTOKEN = os.environ.get("IKKI_USER_TOKEN", "dev-user")
WTOKEN = os.environ.get("IKKI_WORKER_TOKEN", "dev-worker")
STAGES = ["ingest","transcribe","cut","captions","graphics","sound","render"]

LOGO   = os.path.join(DATA, "logos")
BROLLIN= os.path.join(DATA, "broll_in")      # UI ကနေ တင်လာတာ — worker က ဆွဲသည်
THUMB  = os.path.join(DATA, "thumbs")

for d in (UP, OUT, LOGO, THUMB, BROLLIN): os.makedirs(d, exist_ok=True)
db.init()
app = FastAPI(title="IKKI")

def auth(h, tok):
    """token စစ်သည်。

    ⚠️ UTOKEN ဖြင့် ခေါ်လျှင် **အကောင့်တိုင်း၏ token** ကို လက်ခံသည် —
       အကောင့် များစွာ ရှိနိုင်၍。 worker token ကတော့ တစ်ခုတည်း。
    """
    t = (h or "").replace("Bearer ", "")
    if tok == UTOKEN:
        if t and db.one("SELECT id FROM accounts WHERE token=?", t): return
        # ⚠️ env token ကိုလည်း လက်ခံရမည် — accounts မဆောက်မီ ဝင်နိုင်ရန်
        if t and t == UTOKEN: return
        raise HTTPException(401, "unauthorised")
    if not t or t != tok:
        raise HTTPException(401, "unauthorised")


def who(h, t2=""):
    """(acct dict) — token ကနေ အကောင့် ရှာသည်。 မတွေ့လျှင် ပုံသေ。"""
    t = (h or "").replace("Bearer ", "") or t2
    a = db.one("SELECT * FROM accounts WHERE token=?", t) if t else None
    return a or (db.one("SELECT * FROM accounts WHERE id='a_default'") or {"id": "a_default", "name": "—"})


def aid(h, t2=""):
    return who(h, t2)["id"]


@app.get("/api/me")
def me(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    a = dict(who(authorization))
    a.pop("token", None)                 # ⚠️ token ကို ပြန်မပို့ရ
    n = db.one("SELECT COUNT(*) n FROM jobs WHERE acct=? AND deleted IS NULL", a["id"])
    a["videos"] = (n or {}).get("n", 0)
    # ⚠️ UI က ပိုင်ရှင်သာ မြင်ရမည့် ခလုတ်များ (အကောင့် အသစ် · Telegram) ကို
    #    ဒီ field နဲ့ ဖွင့်/ပိတ်သည်。 မပါလျှင် **ပိုင်ရှင်ပါ မမြင်ရ**တော့ပါ
    #    (၂၀၂၆-၀၉-၂၁: UI အသစ်က `a.owner` ကို မျှော်ပြီး API က မပို့ခဲ့)。
    #    ⚠️ ဒါက **ပြသရန်သာ**。 တကယ့် ခွင့်ပြုချက်ကို server ဘက် `_need_owner()`
    #    က စစ်သည် — UI ကို မယုံရ。
    a["owner"] = _owner(authorization)
    return a


def mine(h, jid, t2=""):
    """job က ဒီအကောင့်ရဲ့ဟာ ဟုတ်မဟုတ်。 မဟုတ်လျှင် **404** (401 မဟုတ်) —
    တခြားသူရဲ့ id ရှိမရှိ မသိစေရန်。"""
    j = db.one("SELECT * FROM jobs WHERE id=?", jid)
    if not j or (j.get("acct") or "a_default") != aid(h, t2):
        raise HTTPException(404, "မတွေ့ပါ")
    return j


@app.get("/api/accounts")
def accounts(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    rows = db.rows("SELECT id,name,quota,created FROM accounts ORDER BY created")
    return {"accounts": rows}


@app.post("/api/accounts")
async def account_new(req: Request, authorization: str = Header(None)):
    """အကောင့် အသစ် — token ကို **တစ်ခါပဲ** ပြသည်。"""
    auth(authorization, UTOKEN)
    b = await req.json()
    nm = (b.get("name") or "").strip()[:40]
    if not nm: raise HTTPException(400, "အမည် လိုသည်")
    import secrets
    tok = secrets.token_urlsafe(24)
    aid_ = db.nid("a_")
    db.run("INSERT INTO accounts(id,name,token,quota,created) VALUES(?,?,?,?,?)",
           aid_, nm, tok, float(b.get("quota") or 300.0), time.time())
    return {"id": aid_, "name": nm, "token": tok}


@app.delete("/api/accounts/{a}")
def account_del(a: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    if a == "a_default": raise HTTPException(400, "ပုံသေ အကောင့်ကို မဖျက်ရ")
    db.run("DELETE FROM accounts WHERE id=?", a)
    return {"ok": True}

# ══ ဖိုင်တင်ခြင်း — ပြတ်သွားလျှင် ဆက်တင်နိုင်ရမည် ═══════════

# ── worker ရဲ့ စက်ထဲမှာ ရှိပြီးသား ဖိုင် အညွှန်း ──────────────
# ⚠️ worker က **သုံးစွဲသူရဲ့ Mac ပေါ်မှာပဲ** မောင်းနေသည်。 ဖိုင်က အဲဒီစက်ထဲ
#    ရှိပြီးသားဆို R2 ကို ၅၆၂ MB တင်ပြီး **ပြန်ဆွဲချ**နေတာ အလကား —
#    တိုင်းချက် (၂၀၂၆-၀၉-၁၉): upload 4.1 MB/s ⇒ ၅၆၂ MB = ၁၃၇ စက္ကန့်。
#    parallel တင်ကြည့်တော့ **ပိုနှေး** (3.2 MB/s) — link ကိုယ်တိုင် ပြည့်နေ၍。
#    ⇒ တစ်ခုတည်းသော နည်းလမ်း = **byte မပို့ရအောင် လုပ်ခြင်း**。
_WIDX = {}          # (name, size) → path
_WIDX_AT = [0.0]

@app.post("/api/w/index")
async def w_index(req: Request, authorization: str = Header(None)):
    auth(authorization, WTOKEN)
    b = await req.json()
    _WIDX.clear()
    for f in (b.get("files") or [])[:20000]:
        try: _WIDX[(str(f["name"]), int(f["size"]))] = str(f["path"])
        except Exception: pass
    _WIDX_AT[0] = time.time()
    return {"ok": True, "n": len(_WIDX)}


@app.post("/api/upload/init")
async def up_init(req: Request, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    b = await req.json()
    uid = db.nid("u_")
    ext = os.path.splitext(b.get("name",""))[1][:8]
    # ⚠️ worker ရဲ့ စက်ထဲ ဤဖိုင် ရှိပြီးသားဆို **တစ် byte မှ မတင်ရ**。
    #    အညွှန်းက ၁ နာရီထက် ဟောင်းလျှင် မယုံ (ဖိုင် ရွှေ့/ဖျက်ထားနိုင်)。
    _lp = _WIDX.get((b.get("name",""), int(b.get("size",0) or 0)))
    if _lp and (time.time() - _WIDX_AT[0]) < 3600:
        db.run("INSERT INTO uploads(id,name,size,received,path,done,created,acct,local)"
               " VALUES(?,?,?,?,?,1,?,?,1)",
               uid, b.get("name",""), int(b.get("size",0)), int(b.get("size",0)),
               _lp, time.time(), aid(authorization))
        return {"upload_id": uid, "received": int(b.get("size",0)),
                "size": int(b.get("size",0)), "mode": "have", "chunk": 8*1024*1024}
    if ST.on():
        # ⚠️ R2 mode — browser က R2 ကို **တိုက်ရိုက်** တင်သည်。 VPS မဖြတ်ဘူး。
        #    ၄၁၉ MB ဖိုင်တစ်ခုက VPS ကို ၄ ခါ ဖြတ်ခဲ့ပြီး ဆွဲချရုံ ၈ မိနစ်
        #    ကြာခဲ့သည် (တိုင်းထားသည်)。
        key = f"uploads/{uid}{ext}"
        mpu = ST.mpu_create(key, "video/mp4")
        db.run("INSERT INTO uploads(id,name,size,received,path,done,created,key,mpu,acct)"
               " VALUES(?,?,?,0,'',0,?,?,?,?)",
               uid, b.get("name",""), int(b.get("size",0)), time.time(), key, mpu,
               aid(authorization))
        return {"upload_id": uid, "received": 0, "chunk": 32*1024*1024, "mode": "r2"}
    p = os.path.join(UP, uid + ext)
    open(p, "wb").close()
    db.run("INSERT INTO uploads(id,name,size,received,path,done,created,acct)"
           " VALUES(?,?,?,0,?,0,?,?)",
           uid, b.get("name",""), int(b.get("size",0)), p, time.time(), aid(authorization))
    return {"upload_id": uid, "received": 0, "chunk": 8*1024*1024, "mode": "local"}

@app.get("/api/upload/{uid}")
def up_state(uid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    u = db.one("SELECT * FROM uploads WHERE id=?", uid)
    if not u: raise HTTPException(404, "no upload")
    # ⚠️ DB မဟုတ်ဘဲ **ဖိုင်အရွယ်ကို တိုင်း**ရမည် — chunk တစ်ခု ရေးပြီး DB မရေးမီ
    #    ပြတ်သွားလျှင် ကိန်း ၂ ခု ကွဲသည်。
    got = os.path.getsize(u["path"]) if os.path.exists(u["path"]) else 0
    return {"upload_id": uid, "received": got, "size": u["size"], "done": bool(u["done"])}

@app.put("/api/upload/{uid}/chunk")
async def up_chunk(uid: str, req: Request, offset: int = 0, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    u = db.one("SELECT * FROM uploads WHERE id=?", uid)
    if not u: raise HTTPException(404, "no upload")
    got = os.path.getsize(u["path"]) if os.path.exists(u["path"]) else 0
    if offset != got:
        return JSONResponse({"error":"offset", "received": got}, status_code=409)
    body = await req.body()
    with open(u["path"], "ab") as f: f.write(body)
    got += len(body)
    done = 1 if (u["size"] and got >= u["size"]) else 0
    db.run("UPDATE uploads SET received=?,done=? WHERE id=?", got, done, uid)
    return {"received": got, "done": bool(done)}

@app.post("/api/upload/{uid}/part")
def up_part(uid: str, n: int = 1, authorization: str = Header(None)):
    """R2 mode · part တစ်ခုအတွက် presigned PUT URL。

    ⚠️ browser က PUT ရဲ့ **ETag response header ကို ဖတ်ရမည်** — bucket ရဲ့
       CORS မှာ ExposeHeaders: ["ETag"] မထည့်လျှင် ဖတ်လို့ မရဘဲ
       complete က ကျဘမ်း ဖြစ်မည် (tools/r2_setup.py က သတ်မှတ်ပေးသည်)。
    """
    auth(authorization, UTOKEN)
    u = db.one("SELECT * FROM uploads WHERE id=?", uid)
    if not u or not u.get("mpu"): raise HTTPException(404, "no upload")
    if n < 1 or n > 10000: raise HTTPException(400, "part မှား")
    return {"url": ST.mpu_part_url(u["key"], u["mpu"], n)}

@app.post("/api/upload/{uid}/parts")
def up_parts(uid: str, frm: int = 1, n: int = 50, authorization: str = Header(None)):
    """presigned URL **အစုလိုက်** — အပိုင်းတိုင်း သီးသန့် တောင်းစရာ မလို。

    ⚠️ တိုင်းချက် (၂၀၂၆-၀၉-၁၉): presign အသွားအပြန် အလယ်တန်း **၂၀၀ ms**
       (အများဆုံး ၆၇၆ ms)。 ၄.၅ GB ကို ၈ MB အပိုင်းနဲ့ ⇒ အပိုင်း ၅၆၂ ခု ×
       ၂၀၀ ms = **၁၁၂ စက္ကန့်** — byte တစ်ခုမှ မပို့ဘဲ စောင့်နေရခြင်း。
       ⇒ အစုလိုက် တောင်းလျှင် ၅၆၂ ကြိမ် → ၁၂ ကြိမ်。
    """
    auth(authorization, UTOKEN)
    u = db.one("SELECT * FROM uploads WHERE id=?", uid)
    if not u or not u.get("mpu"): raise HTTPException(404, "no upload")
    n = max(1, min(100, int(n)))
    if frm < 1 or frm + n - 1 > 10000: raise HTTPException(400, "part မှား")
    return {"from": frm,
            "urls": [ST.mpu_part_url(u["key"], u["mpu"], frm + i) for i in range(n)]}

@app.post("/api/upload/{uid}/complete")
async def up_complete(uid: str, req: Request, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    u = db.one("SELECT * FROM uploads WHERE id=?", uid)
    if not u or not u.get("mpu"): raise HTTPException(404, "no upload")
    b = await req.json()
    parts = [(int(x["n"]), str(x["etag"])) for x in (b.get("parts") or []) if x.get("etag")]
    if not parts: raise HTTPException(400, "part မရှိ")
    ST.mpu_complete(u["key"], u["mpu"], parts)
    # ⚠️ အရွယ်ကို **R2 ကို ပြန်မေး**ရမည် — browser ရဲ့ ကိန်းကို မယုံရ
    sz = ST.head(u["key"]) or 0
    db.run("UPDATE uploads SET received=?,done=1,size=CASE WHEN size>0 THEN size ELSE ? END"
           " WHERE id=?", sz, sz, uid)
    return {"received": sz, "done": True}

@app.post("/api/upload/{uid}/abort")
def up_abort(uid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    u = db.one("SELECT * FROM uploads WHERE id=?", uid)
    if u and u.get("mpu"): ST.mpu_abort(u["key"], u["mpu"])
    return {"ok": True}

# ══ job ═══════════════════════════════════════════════════
@app.post("/api/jobs")
async def job_new(req: Request, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    b = await req.json()
    # A recording often has several good takes. Treat them as one project, not
    # unrelated uploads: the worker joins them before transcription and keeps
    # the source-take provenance in the transcript.
    raw_sources = b.get("source_upload_ids")
    if raw_sources is None:
        source_ids = [str(b.get("upload_id") or "").strip()]
    elif isinstance(raw_sources, list):
        source_ids = [str(x or "").strip() for x in raw_sources]
    else:
        raise HTTPException(400, "source_upload_ids က စာရင်းဖြစ်ရမည်")
    source_ids = [x for x in source_ids if x]
    if not source_ids or len(source_ids) > 4:
        raise HTTPException(400, "source video ၁ ခုမှ ၄ ခုအထိသာ ထည့်နိုင်သည်")
    if len(set(source_ids)) != len(source_ids):
        raise HTTPException(400, "တူညီသော source video ကို နှစ်ခါ ထည့်ထားသည်")
    stated = str(b.get("upload_id") or "").strip()
    if stated and stated != source_ids[0]:
        raise HTTPException(400, "ပထမ source video မကိုက်")
    sources = []
    for sid in source_ids:
        su = db.one("SELECT * FROM uploads WHERE id=?", sid)
        if not su: raise HTTPException(400, "source upload မရှိ")
        if not su["done"]: raise HTTPException(400, "source upload မပြီးသေး")
        sources.append(su)
    u = sources[0]
    ym = time.strftime("%Y-%m")
    q = db.one("SELECT * FROM usage WHERE ym=?", ym) or {"minutes":0,"quota":300}
    if q["minutes"] >= q["quota"]:
        # ⚠️ error တစ်ကြောင်းနဲ့ ရပ်လျှင် **ဘာလုပ်ရမလဲ မသိ**。 လမ်းညွှန်ပါ ပေးရမည်。
        raise HTTPException(402, "ဒီလအတွက် မိနစ် ကုန်သွားပါပြီ — "
                                 "Account စာမျက်နှာက “မိနစ် ထပ်တောင်းမယ်” ကို နှိပ်ပါ")
    jid = db.nid("j_")
    # ⚠️ format ကို **စစ်ရမည်** — မရှိတာ ပေးလိုက်လျှင် worker က render ခါမှ
    #    ကျဘမ်းဖြစ်ပြီး သုံးစွဲသူက အကြောင်းရင်း မသိဘူး。
    fmt = (b.get("fmt") or "").strip()
    if fmt and fmt not in FM.keys():
        raise HTTPException(400, f"အရွယ် မရှိ: {fmt}")
    # ⚠️ စာတန်း အရွယ်ကိုလည်း **server မှာ** စစ်ရမည် — UI ကို မယုံရ
    import recipes as _RC
    cap = (b.get("cap") or "").strip()
    if cap and cap not in _RC.CAPSIZE:
        raise HTTPException(400, f"စာတန်း အရွယ် မရှိ: {cap}")
    # ⚠️ **ပုံမှန်က `review`** — ASR ပြီးလျှင် ရပ်ပြီး စာတမ်းကို သုံးစွဲသူ ပြသည်。
    #    ဖြတ်ချက်ကို app က ဆုံးဖြတ်လျှင် "လုံးဝ အဆင်မပြေဘူး" ဖြစ်ခဲ့သည် —
    #    ဘယ်စာလုံး ကျန်မလဲ ဆိုတာ **သုံးစွဲသူသာ** သိသည်。
    #    `mode=auto` ပေးလျှင်သာ အရင်ပုံစံအတိုင်း တန်းဖြတ်သည်。
    mode = (b.get("mode") or "review").strip()
    if mode not in ("review", "auto"): mode = "review"
    # ⚠️ ဗီဒီယို ပုံစံ — ပြန်စ ရှာဖွေမှုက `camera` မှသာ (ဂိတ်: vlog ၅/၅ အောင် ·
    #    podcast ကျ ၇၉.၆% · ၂၀၂၆-၀၉-၁၆)。 မပေးလျှင် "" = မသိ ⇒ ပြန်စ **ပိတ်**。
    vfmt = (b.get("vfmt") or "").strip().lower()
    if vfmt not in ("camera", "podcast", "other", ""): vfmt = "other"
    # ⚠️ dual-system — အသံ သီးသန့် ဖိုင် (recorder)。 schema မပြောင်းဘဲ `over` ထဲ ထားသည်。
    #    ကင်မရာ အသံက −53 LUFS ဖြစ်တတ်ပြီး သီချင်းက စကားကို ဖုံးသည် (၂၀၂၆-၀၉-၁၉)。
    over = {}
    au = (b.get("audio_upload_id") or "").strip()
    if au:
        a = db.one("SELECT * FROM uploads WHERE id=?", au)
        if not a: raise HTTPException(400, "အသံ upload မရှိ")
        if not a["done"]: raise HTTPException(400, "အသံ upload မပြီးသေး")
        # One external recorder track cannot be safely aligned against several
        # takes. Refuse clearly instead of silently using it on take one only.
        if len(sources) > 1:
            raise HTTPException(400, "take များစွာနဲ့ recorder အသံတစ်ဖိုင်ကို မပေါင်းနိုင်သေးပါ — take တစ်ခုတည်းသုံးပါ၊ သို့မဟုတ် camera audio ကိုသုံးပါ")
        over["_audio"] = au
    if len(sources) > 1:
        # The primary source remains in jobs.upload_id for old jobs/routes;
        # only additional takes live in the job-local override.
        over["_sources"] = source_ids[1:]
    # Speed is opt-in. These small pitch-preserving values deliberately keep
    # the default at 1.00× for business, education and calmer delivery.
    try: speech_speed = round(float(b.get("speech_speed", 1.0)), 2)
    except (TypeError, ValueError): speech_speed = 1.0
    if speech_speed not in (1.0, 1.03, 1.06):
        raise HTTPException(400, "စကားပြောအရှိန် 1.00×၊ 1.03× သို့မဟုတ် 1.06× သာ ရွေးနိုင်သည်")
    if speech_speed != 1.0: over["_speech_speed"] = speech_speed
    db.run("INSERT INTO jobs(id,title,upload_id,brand_id,recipe,font,fmt,cap,status,stage,"
           "mode,vfmt,over,acct,created) VALUES(?,?,?,?,?,?,?,?,'queued',0,?,?,?,?,?)",
           # ⚠️ ပုံသေ brand က **`"zjl"`** ဟု ရေးထားခဲ့သည် — IKKI ထုတ်ကုန်မှာ
           #    ZJL ရဲ့ အရောင်နဲ့ ဖောင့် ပုံသေ ဖြစ်နေကာ style ရဲ့ theme ကိုပါ
           #    ကျော်ပစ်သည် (`run.py`: `bid = job.brand_id or rc["theme"]`)。
           #    ⇒ IKKI ကိုယ်ပိုင် theme ကို ပုံသေ ထားသည် (Zin ၂၀၂၆-၀၉-၂၀)。
           jid, b.get("title") or u["name"], u["id"], b.get("brand_id","ikki"),
           b.get("recipe","cinematic-vlog"), (b.get("font") or "")[:48], fmt, cap,
           mode, vfmt, json.dumps(over, ensure_ascii=False) if over else None,
           aid(authorization), time.time())
    return {"job_id": jid, "mode": mode, "vfmt": vfmt, "audio": bool(au),
            "sources": len(sources), "speech_speed": speech_speed}

@app.get("/api/jobs")
def job_list(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    # ⚠️ အမှိုက်ပုံးထဲက ၂၄ နာရီ ကျော်တာကို ဒီမှာပဲ ရှင်းသည် (cron မလို)。
    try: _sweep()
    except Exception: pass
    try: _verify()
    except Exception: pass
    return {"jobs": db.rows(
        "SELECT * FROM jobs WHERE deleted IS NULL AND acct=? "
        "ORDER BY created DESC LIMIT 200", aid(authorization))}

@app.get("/api/jobs/{jid}")
def job_get(jid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    j = mine(authorization, jid)
    j["stages"] = STAGES
    try: j["flag_list"] = json.loads(j.get("flag_list") or "[]")
    except Exception: j["flag_list"] = []
    j["versions"] = db.rows("SELECT * FROM versions WHERE job_id=? ORDER BY n DESC", jid)
    return j

@app.post("/api/jobs/{jid}/cancel")
def job_cancel(jid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    j = mine(authorization, jid)
    if j["status"] in ("done","failed"): return {"ok": False, "why": "ပြီးသွားပြီ"}
    # ⚠️ ရပ်လိုက်လျှင် သုံးထားသော မိနစ်ကို **ပြန်ထည့်ပေးရမည်** — UI က ကတိပေးထားသည်
    db.run("UPDATE usage SET minutes=max(0,minutes-?) WHERE ym=?",
           j["minutes"] or 0, time.strftime("%Y-%m"))
    db.run("UPDATE jobs SET status='cancelled',finished=?,minutes=0 WHERE id=?", time.time(), jid)
    return {"ok": True, "refunded": j["minutes"] or 0}

@app.post("/api/jobs/{jid}/retry")
def job_retry(jid: str, authorization: str = Header(None)):
    """ကျဘမ်းဖြစ်သွားသော job ကို **ပြန်စ**ခြင်း。

    ⚠️ အရင်က retry မရှိခဲ့ ⇒ worker ဘက်မှာ disk ပြည့်တာမျိုး ယာယီ ပြဿနာ
       တစ်ခုနဲ့ ကျဘမ်းဖြစ်လျှင် သုံးစွဲသူက **ဗီဒီယိုကြီး ပြန်တင်ရ**သည်。
       upload က R2 ပေါ် ရှိပြီးသားမို့ ပြန်တင်စရာ မလို。
    ⚠️ ကျဘမ်းဖြစ်တုန်းက စားထားသော မိနစ်ကို **ပြန်ထည့်ပေးရမည်** — ထွက်လာတဲ့
       ဗီဒီယို မရှိဘဲ မိနစ် ကုန်သွားလျှင် ငွေယူပြီး ပစ္စည်း မပေးရာ ကျသည်。
    """
    auth(authorization, UTOKEN)
    j = mine(authorization, jid)
    if j["status"] not in ("failed", "cancelled"):
        raise HTTPException(409, f"ကျဘမ်း မဖြစ်ထားပါ ({j['status']})")
    u = db.one("SELECT * FROM uploads WHERE id=?", j.get("upload_id"))
    if not u or not u["done"]:
        raise HTTPException(410, "မူရင်းဖိုင် မရှိတော့ပါ — ပြန်တင်ပါ")
    back = float(j.get("minutes") or 0)
    if back > 0:
        db.run("UPDATE usage SET minutes=max(0,minutes-?) WHERE ym=?",
               back, time.strftime("%Y-%m"))
    db.run("UPDATE jobs SET status='queued',stage=0,minutes=0,err=NULL,"
           "claimed=NULL,finished=NULL WHERE id=?", jid)
    return {"ok": True, "refunded": round(back, 2)}


@app.get("/api/jobs/{jid}/file")
def job_file(jid: str, authorization: str = Header(None), t: str = ""):
    # ⚠️ <a href> က header မပို့နိုင် — ဒေါင်းလုပ်အတွက် query token လက်ခံသည်
    auth(authorization or (f"Bearer {t}" if t else None), UTOKEN)
    j = mine(authorization, jid, t)
    if j.get("out_key") and ST.on():
        # browser က redirect လိုက်တဲ့အခါ ကိုယ်ပိုင် header မပို့သဖြင့် ရသည်
        return RedirectResponse(ST.get_url(j["out_key"], 3600, filename=f"{jid}.mp4"),
                                status_code=302)
    if not j["out_path"] or not os.path.exists(j["out_path"]):
        raise HTTPException(404, "ဖိုင် မရှိသေး")
    return FileResponse(j["out_path"], filename=f"{jid}.mp4")

@app.post("/api/jobs/{jid}/reedit")
async def job_reedit(jid: str, req: Request, authorization: str = Header(None)):
    """စာသား ပြင်ပြီး ပြန်ထုတ်ခြင်း。

    ⚠️ **ဖြတ်တာက ဖျက်ရုံပဲ ရသည်** — အသံထဲ မရှိတဲ့ စာလုံးက ဖြတ်စရာ မရှိ。
       `text` ထဲ ထည့်လာသမျှ မူရင်းထဲ ရှိရမည်。
    ⚠️ ဒါပေမယ့် **`fix` က စာတန်းစာလုံးကို ပြင်ဖို့** သီးသန့် ဖြစ်သည် —
       ASR က မှားဖတ်တာ (မြန်မာစာမှာ မကြာခဏ) ကို ပြင်ရန်。 `fix` က
       **အသံကို မထိ · ဖြတ်မှတ်ကို မထိ** — မျက်နှာပြင်ပေါ် ပေါ်မယ့် စာသားပဲ
       ပြောင်းသည်。 ဒါကြောင့် R1 (delete-only) နှင့် မဆန့်ကျင်。
    ⚠️ ASR ပြန်မလုပ်ပါ — ဖိုင်လည်း ပြန်မဆွဲပါ。 ဒါကြောင့် မြန်သည်。
    """
    auth(authorization, UTOKEN)
    b = await req.json()
    par = mine(authorization, jid)
    # ⚠️ **`segs_all` (ASR အပြည့်) ကနေ ယူရမည်**。 `segs` က အရင် ချန်ခဲ့သော
    #    ဝါကျများသာ ဖြစ်ပြီး — အဲဒါနဲ့ diff လုပ်လျှင် အရင် ဖျက်ထားတဲ့ ဝါကျတွေ
    #    `drop` ထဲ မပါဘဲ **ပြန်ပါလာ**သည် (Zin ၂၀၂၆-၀၉-၂၀: ချန် ၁၁၂s ဖြစ်ပါလျက်
    #    ၃၂၂s ထွက်ခဲ့)。 job အသစ်က မူရင်း upload ကနေ render လုပ်သဖြင့်
    #    `drop` က **မူရင်း အပြည့်နှင့် နှိုင်း**ရမည်。
    try: orig = json.loads(par.get("segs_all") or par.get("segs") or "[]")
    except Exception: orig = []
    if not orig: raise HTTPException(400, "မူရင်း စာသား မရှိ — ပြန်ထုတ်လို့ မရပါ")
    keep = b.get("segs")
    if not isinstance(keep, list) or not keep:
        raise HTTPException(400, "စာသား မပါ")
    # ── ဖျက်ရုံပဲ ရသည် — အသစ် ထည့်လာတာ ရှိလျှင် ငြင်းရမည် ──
    obyid = {i: s for i, s in enumerate(orig)}
    clean = []
    for k in keep:
        i = k.get("i")
        if i is None or i not in obyid: raise HTTPException(400, "စာကြောင်း အသစ် ထည့်လို့ မရပါ")
        o = obyid[i]; t = (k.get("text") or "").strip()
        if not t: continue                      # ဖျက်လိုက်တာ
        # ⚠️ space ဖယ်ပြီး အက္ခရာစဉ် တထပ်တည်း တူရမည် — မတူလျှင် ဖွဲ့ထားသည်
        if t.replace(" ","") not in o["text"].replace(" ",""):
            raise HTTPException(400, f"စာလုံး အသစ် ပါနေသည်: {t[:30]}")
        e = dict(text=t, start=o["start"], end=o["end"])
        # Source provenance is not editable, but preserving it keeps Script
        # Editor labels correct after approval and the second worker pass.
        for _k in ("source", "take"):
            if o.get(_k) is not None: e[_k] = o[_k]
        fx = (k.get("fix") or "").strip()
        if fx and fx != t:
            if len(fx) > len(t) * 3 + 40:
                raise HTTPException(400, "ပြင်ချက် ရှည်လွန်းသည် — စာတန်းက အသံနဲ့ လွဲမည်")
            e["fix"] = fx                      # ← စာတန်းအတွက်သာ
        clean.append(e)
    if not clean: raise HTTPException(400, "အားလုံး ဖျက်ထားသည်")
    # ⚠️ ဖျက်လိုက်သော စာကြောင်းတွေရဲ့ **အချိန်အပိုင်း**ကို worker ဆီ ပို့ရမည် —
    #    မပို့လျှင် စာတန်းပဲ ပျောက်ပြီး ရုပ်နဲ့ အသံ ကျန်နေမည် (တကယ် ဖြစ်ခဲ့)。
    kept_i = {k.get("i") for k in keep if (k.get("text") or "").strip()}
    drop = [[float(o["start"]), float(o["end"])]
            for i, o in enumerate(orig) if i not in kept_i]
    ym = time.strftime("%Y-%m")
    q = db.one("SELECT * FROM usage WHERE ym=?", ym) or {"minutes":0,"quota":300}
    if q["minutes"] >= q["quota"]:
        raise HTTPException(402, "ဒီလအတွက် မိနစ် ကုန်သွားပါပြီ — "
                                 "Account စာမျက်နှာက “မိနစ် ထပ်တောင်းမယ်” ကို နှိပ်ပါ")
    # ⚠️ ပြင်ချက်ကို **server မှာ ဘောင်စစ်ရမည်** — UI ကို မယုံရ。
    #    `recipes.clean()` က ဘောင်ပြင်ထွက်တာကို ဖြုတ်ပစ်သည်。
    import recipes as _RC
    over = b.get("over") or {}
    if not isinstance(over, dict): over = {}
    over = _RC.clean(over)
    fnt = (b.get("font") or par.get("font") or "")[:48]
    capz = (b.get("cap") or par.get("cap") or "").strip()
    if capz and capz not in _RC.CAPSIZE:
        raise HTTPException(400, f"စာတန်း အရွယ် မရှိ: {capz}")
    nid = db.nid("j_")
    # ⚠️ **`acct` ကို မဖြစ်မနေ ထည့်ရမည်**。 ထည့်ရန် ကျန်ခဲ့သဖြင့် ပြန်ပြင်ထားသော
    #    job တိုင်း `acct=NULL` ဖြစ်ပြီး `/api/jobs` ရဲ့ `WHERE acct=?` က
    #    မမိသဖြင့် **စာရင်းထဲ ဘယ်တော့မှ မပေါ်**ခဲ့。 worker ကတော့ ယူပြီး
    #    render လုပ်ပြီးသား — သုံးစွဲသူက "ပြီးပြီ ပြောပေမယ့် ထွက်မလာဘူး" ဟု
    #    မြင်ရသည် (တကယ် ဖြစ်ခဲ့: j_ec2e57a93bc7)。
    _nbrand = (b.get("brand_id") or "").strip() or par["brand_id"]
    if _nbrand != par["brand_id"]:
        # ⚠️ `theme` module က **motionkit ထဲမှာ ရှိပြီး API image ထဲ မပါ** —
        #    `core/grade.py` နဲ့ တူညီသော ထောင်ချောက် (၂၀၂၆-၀၉-၂၀ တကယ် ဖြစ်)。
        #    ⇒ import မရလျှင် house theme စာရင်းကို ကိန်းသေနဲ့ စစ်သည်。
        HOUSE = {"ikki", "zjl", "zae"}
        _ok = (_nbrand in HOUSE) or db.one("SELECT id FROM brands WHERE id=?", _nbrand)
        if not _ok: _nbrand = par["brand_id"]
    db.run("INSERT INTO jobs(id,title,upload_id,brand_id,recipe,font,fmt,cap,status,stage,"
           "segs,segs_all,keep_n,plan,src_dur,parent,over,acct,created)"
           " VALUES(?,?,?,?,?,?,?,?,'queued',0,?,?,?,?,?,?,?,?,?)",
           # ⚠️ brand ကို ပြင်ခွင့် ပေးသည် — မဟုတ်လျှင် အဟောင်း job ရဲ့ brand
           #    (များသောအားဖြင့် `zjl`) က ထာဝရ ကပ်နေမည်。 မသိသော brand ကို
           #    လက်မခံဘဲ မူရင်းကို ဆက်သုံးသည်。
           nid, (par["title"] or "") + " · ပြင်ပြီး", par["upload_id"], _nbrand,
           b.get("recipe") or par["recipe"], fnt, par.get("fmt") or "", capz,
           json.dumps(clean, ensure_ascii=False),
           json.dumps(orig, ensure_ascii=False),
           json.dumps(sorted({int(k.get("i")) + 1 for k in keep
                              if k.get("i") is not None
                              and (k.get("text") or "").strip()})),
           par.get("plan"), par.get("src_dur"), jid,
           json.dumps(dict(over, _drop=drop) if drop else over,
                      ensure_ascii=False) if (over or drop) else None,
           par.get("acct") or aid(authorization), time.time())
    return {"job_id": nid, "kept": len(clean), "removed": len(orig)-len(clean),
            "fixed": sum(1 for c in clean if c.get("fix")), "over": over,
            "cut_s": round(sum(b - a for a, b in drop), 1)}

@app.get("/api/retake_review")
def retake_review(authorization: str = Header(None), job: str = ""):
    """ပြန်စ အကြံပြုချက်အပေါ် **လူ့ဆုံးဖြတ်ချက် မှတ်တမ်း** — ground truth ထုတ်ယူရန်。

    ⚠️ ဒီအကောင့်ရဲ့ ဟာသာ。 ဗီဒီယိုတိုင်းက နမူနာ တိုးလာမှ detection စည်းမျဉ်း
       ချမှတ်ရမည် (C0736 တစ်ခုတည်းနဲ့ ချလျှင် overfit)。
    """
    auth(authorization, UTOKEN)
    q, args = "SELECT * FROM retake_review WHERE acct=?", [aid(authorization)]
    if job: q += " AND job_id=?"; args.append(job)
    rows = db.rows(q + " ORDER BY created DESC LIMIT 2000", *args)
    return {"n": len(rows), "rows": rows}

@app.get("/api/retake_picks")
def retake_picks(authorization: str = Header(None), job: str = "", vfmt: str = ""):
    """review v2 — **အုပ်စု တစ်ခုချင်း ဘယ် take ချန်လဲ** မှတ်တမ်း (ground truth)。

    ⚠️ ဗီဒီယိုတိုင်းက take ရွေးချယ်မှု တိုးလာမှ "ဘယ် take ချန်မလဲ" ကို သင်နိုင်မည် —
       တိုင်းချက်: ချန်သော take က ရှေ့မှာ ဖြစ်တာ ၃၄% (podcast ၅၂%) ⇒ စက်နဲ့ မရွေးရ。
    """
    auth(authorization, UTOKEN)
    q, args = "SELECT * FROM retake_pick WHERE acct=?", [aid(authorization)]
    if job: q += " AND job_id=?"; args.append(job)
    if vfmt: q += " AND vfmt=?"; args.append(vfmt)
    rows = db.rows(q + " ORDER BY created DESC LIMIT 5000", *args)
    return {"n": len(rows), "picked": sum(1 for r in rows if (r.get("picked") or "none") != "none"),
            "rows": rows}

@app.get("/api/jobs/{jid}/editplan")
def job_editplan(jid: str, authorization: str = Header(None)):
    """Headtop ရဲ့ edit plan (JSON) — UI က event တစ်ခုချင်း ပြရန်。

    ⚠️ `/plan` **မဟုတ်**。 `plan` ကော်လံက ဖြတ်မှတ်/retake အတွက် ရှိပြီးသား。
    """
    j = mine(authorization, jid)
    try:
        p = json.loads(j.get("edit_plan") or "{}")
    except Exception:
        p = {}
    if not p:
        raise HTTPException(404, "edit plan မရှိပါ (headtop ပုံစံမှသာ ထွက်သည်)")
    return p


@app.get("/api/jobs/{jid}/srt")
def job_srt(jid: str, authorization: str = Header(None), t: str = ""):
    """စာတန်း ဖိုင် — SRT (ဗီဒီယို မလိုဘဲ သီးသန့် သုံးရန်)"""
    auth(authorization or (f"Bearer {t}" if t else None), UTOKEN)
    j = mine(authorization, jid, t)
    if not j: raise HTTPException(404, "no job")
    try: segs = json.loads(j.get("segs") or "[]")
    except Exception: segs = []
    if not segs: raise HTTPException(404, "စာသား မရှိ")
    def ts(x):
        h=int(x//3600); mm=int(x%3600//60); ss=int(x%60); ms=int((x-int(x))*1000)
        return f"{h:02d}:{mm:02d}:{ss:02d},{ms:03d}"
    body = "".join(f"{i+1}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text']}\n\n"
                   for i,s in enumerate(segs))
    p = os.path.join(OUT, f"{jid}.srt")
    open(p, "w", encoding="utf-8").write(body)
    return FileResponse(p, filename=f"{jid}.srt", media_type="text/plain; charset=utf-8")

@app.get("/api/settings")
def get_settings(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    return {r["k"]: r["v"] for r in db.rows("SELECT * FROM settings")}

@app.post("/api/settings")
async def set_settings(req: Request, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    b = await req.json()
    for k, v in b.items():
        db.run("INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=?",
               str(k)[:40], str(v)[:200], str(v)[:200])
    return {"ok": True}

@app.post("/api/brands")
async def brand_new(req: Request, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    b = await req.json()
    bid = (b.get("id") or db.nid("b_"))[:24]
    db.run("INSERT INTO brands(id,name,aspect,colors,mmf,latin,jp,top,bot,acct,created)"
           " VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET"
           " name=?,aspect=?,colors=?,mmf=?,latin=?,jp=?,top=?,bot=?",
           bid, b.get("name","Brand"), b.get("aspect","16:9"),
           json.dumps(b.get("colors") or ["#101014","#1C1C22","#FFE000","#5B9BD5","#E8102A"]),
           b.get("mmf","Pyidaungsu"), b.get("latin","Figtree-Black"),
           b.get("jp","HiraginoSans-W7"), int(b.get("top",170)), int(b.get("bot",830)),
           aid(authorization), time.time(),
           b.get("name","Brand"), b.get("aspect","16:9"),
           json.dumps(b.get("colors") or ["#101014","#1C1C22","#FFE000","#5B9BD5","#E8102A"]),
           b.get("mmf","Pyidaungsu"), b.get("latin","Figtree-Black"),
           b.get("jp","HiraginoSans-W7"), int(b.get("top",170)), int(b.get("bot",830)))
    return {"id": bid}

@app.get("/api/brands")
def brands(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    # ⚠️ house brand (zae · zjl) က အားလုံးအတွက် — recipe တွေက ရည်ညွှန်းထားသည်
    bs = db.rows("SELECT * FROM brands WHERE acct=? OR id IN ('zae','zjl')",
                 aid(authorization))
    for b in bs: b["colors"] = json.loads(b["colors"])
    return {"brands": bs}

@app.get("/api/styles")
def styles(authorization: str = Header(None)):
    """ပုံစံတိုင်း — တိုင်းထားသော ပုံသေ + သုံးစွဲသူ ပြင်ချက်။"""
    auth(authorization, UTOKEN)
    import recipes as RC
    over = {r["style"]: json.loads(r["data"] or "{}")
            for r in db.rows("SELECT * FROM style_over")}
    # ⚠️ ရွေးစရာ စာရင်းကို **UI ထဲ ပြန်မရေးရ** — `BOUNDS` က တစ်ခုတည်းသော
    #    အမှန်。 နှစ်နေရာ ရေးထားလျှင် တစ်ဖက် ပြောင်းပြီး တစ်ဖက် ကျန်ခဲ့မည်
    #    (style ထည့်တိုင်း နှစ်နေရာ ထည့်ရတဲ့ ဒုက္ခ ကြုံပြီးသား)。
    _ch = {k: v[1] for k, v in RC.BOUNDS.items()
           if isinstance(v, tuple) and v and v[0] == "choice"}
    _bl = sorted(k for k, v in RC.BOUNDS.items()
                 if isinstance(v, tuple) and v and v[0] == "bool")
    return {"styles": RC.listing(), "over": over,
            "choices": _ch, "bools": _bl,
            "cuts": [{"id": k, "my": v[0], "en": v[1]} for k, v in RC.CUT_LABEL.items()],
            "lufs": [{"v": k, "my": v[0], "en": v[1]} for k, v in RC.LUFS.items()],
            "music": RC.MUSIC, "captions": RC.CAPSTYLE, "latin": RC.LATIN}

@app.post("/api/styles/{sid}")
async def style_save(sid: str, req: Request, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    import recipes as RC
    if sid not in RC.R: raise HTTPException(404, "ပုံစံ မရှိ")
    b = await req.json()
    # ⚠️ ဘောင်စစ်မှုကို **server မှာ** လုပ်ရမည် — UI ကို မယုံရ
    o = RC.clean(b.get("over") or b)
    db.run("INSERT INTO style_over(style,data,updated) VALUES(?,?,?)"
           " ON CONFLICT(style) DO UPDATE SET data=?,updated=?",
           sid, json.dumps(o, ensure_ascii=False), time.time(),
           json.dumps(o, ensure_ascii=False), time.time())
    return {"ok": True, "over": o}

@app.delete("/api/styles/{sid}")
def style_reset(sid: str, authorization: str = Header(None)):
    """တိုင်းထားသော ပုံသေ ပြန်သုံးခြင်း"""
    auth(authorization, UTOKEN)
    db.run("DELETE FROM style_over WHERE style=?", sid)
    return {"ok": True}

@app.get("/api/capsizes")
def capsizes(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    import recipes as RC
    return {"sizes": [dict(id=k, pct=v[0], my=v[1], en=v[2])
                      for k, v in RC.CAPSIZE.items()]}

@app.get("/api/formats")
def formats(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    return {"formats": FM.listing(), "native": FM.NATIVE}

@app.delete("/api/brands/{bid}")
def brand_del(bid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    # ⚠️ house brand ၂ ခုကို မဖျက်ရ — recipe တွေက သူတို့ကို ရည်ညွှန်းသည်
    if bid in ("zae", "zjl"): raise HTTPException(400, "house brand ကို မဖျက်ရ")
    db.run("DELETE FROM brands WHERE id=?", bid)
    return {"ok": True}

# ⚠️ ဖောင့်က Mac worker ပေါ်မှာ ရှိသည် — VPS မှာ မရှိသဖြင့် စာရင်းက ပုံသေ。
#    အားလုံး cttext နဲ့ တကယ် ဆွဲကြည့်ပြီး စစ်ထားသည်。
# ⚠️ `/api/fonts` နှင့် `/api/fonts/suggest` **တစ်ခုတည်းကို** သုံးရမည် —
#    နှစ်နေရာ ခွဲရေးလျှင် AI က UI မှာ မရှိတဲ့ ဖောင့် ရွေးမိနိုင်သည်。
FONTS = [
      dict(id="Pyidaungsu",           name="Pyidaungsu",             look="ပါးလွှာ · ရုပ်ရှင်ဆန်",  good="Cinematic · Podcast"),
      dict(id="Pyidaungsu-Bold",      name="Pyidaungsu Bold",        look="ထူ · ဝေးကကြည့်ရ",       good="Short Video · ZAE"),
      dict(id="MasterpieceUniRound",  name="Masterpiece Uni Round",  look="လုံးဝိုင်း · ချောမွေ့",  good="ZJL house font"),
      dict(id="MyanmarYinmar",        name="Myanmar Yinmar",         look="အသားရ · ခေါင်းစဉ်ဆန်",  good="Vlog · ခေါင်းစဉ်"),
      dict(id="MyanmarSansPro",       name="Myanmar Sans Pro",       look="ပြတ်သား · သန့်",        good="Knowledge"),
      dict(id="MyanmarHeadOne",       name="Myanmar Head One",       look="ခေါင်းစဉ် အသွင်",       good="ZAE ခေါင်းစဉ်"),
      dict(id="PadaukBook-Bold",      name="Padauk Book Bold",       look="စာအုပ်ဆန် · ဖတ်ရလွယ်",  good="Course"),
      dict(id="Padauk",               name="Padauk",                 look="ရိုးရိုး · ယုံကြည်ရ",    good="Brand Review"),
      dict(id="NotoSansMyanmar-Bold", name="Noto Sans Myanmar Bold", look="ကျယ် · corporate",      good="Promotional"),
      dict(id="MyanmarPonenyet",      name="Myanmar Ponenyet",       look="အခြေခံ · box",          good="ZJL box"),
      dict(id="MyanmarBlack",         name="Myanmar Black",          look="အထူဆုံး",               good="စာလုံးကြီး"),
      dict(id="MyanmarSagar",         name="Myanmar Sagar",          look="သေးသွယ်",               good="ကြောင်းသေး"),
    ]

@app.get("/api/fonts")
def fonts(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    return {"fonts": FONTS}

@app.get("/api/usage")
def usage(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    ym = time.strftime("%Y-%m")
    return db.one("SELECT * FROM usage WHERE ym=?", ym) or {"ym":ym,"minutes":0,"quota":300}

# ══ worker ════════════════════════════════════════════════
def _beat():
    """worker ရှင်နေသည် ဟု မှတ်သည်。

    ⚠️ claim တစ်ခုတည်းမှာ မမှတ်ရ — worker က job လုပ်နေတုန်း poll မလုပ်သဖြင့်
       heartbeat ရိုးသွားသည် (render တစ်ခုမှာ ၇၅၆s ရိုးခဲ့သည်)。
       ⇒ stage · result · fail အားလုံးမှာ မှတ်သည်。
    ⚠️ မမှတ်လျှင် Mac ပိတ်/အိပ်နေချိန် job က queued အနေနဲ့ **ဘာမှ မပြဘဲ
       ရပ်နေသည်** — Zin က "upload တင်ပြီး ရပ်နေတယ်" ဟု ပြောခဲ့သည်。
    """
    t = str(time.time())
    db.run("INSERT INTO settings(k,v) VALUES('worker_seen',?)"
           " ON CONFLICT(k) DO UPDATE SET v=?", t, t)

@app.post("/api/w/reclaim")
def w_reclaim(authorization: str = Header(None)):
    """worker စတင်ချိန် — **လုပ်နေဆဲ ဟု မှတ်ထားသော job ကို ပြန်တန်းစီ**သည်。

    ⚠️ worker က render လုပ်နေရင်း ပြန်စတင်သွားလျှင် (crash · launchd ·
       deploy · Mac အိပ်ပျော်) job က `running` အတိုင်း **ထာဝရ ကျန်နေ**သည် —
       ဘယ်သူမှ မလုပ်တော့ဘဲ သုံးစွဲသူက ထာဝရ စောင့်နေရသည် (တကယ် ဖြစ်ခဲ့:
       j_a90653f06ad6 ၁၃၆ မိနစ်)。
    ⚠️ worker **တစ်ခုတည်း** ရှိသဖြင့် စတင်ချိန်မှာ လုပ်နေဆဲ job မရှိနိုင် —
       ဒါကြောင့် `running` တွေ့လျှင် သေနေတာ **သေချာ**သည်。 အချိန် မှန်းစရာ မလို。
    ⚠️ စားထားသော မိနစ်ကို ပြန်ထည့်ပေးရမည် — ထွက်လာတဲ့ ဗီဒီယို မရှိ。
    """
    auth(authorization, WTOKEN)
    _beat()
    rows = db.rows("SELECT id,minutes FROM jobs WHERE status='running'") or []
    ym = time.strftime("%Y-%m")
    for r in rows:
        back = float(r["minutes"] or 0)
        if back > 0:
            db.run("UPDATE usage SET minutes=max(0,minutes-?) WHERE ym=?", back, ym)
        db.run("UPDATE jobs SET status='queued',stage=0,stage_name=NULL,minutes=0,"
               "claimed=NULL WHERE id=?", r["id"])
    return {"ok": True, "requeued": [r["id"] for r in rows]}


@app.post("/api/w/{jid}/plan")
async def w_plan(jid: str, req: Request, authorization: str = Header(None)):
    """worker က **ASR ပြီးလျှင်** စာတမ်းနဲ့ ဖြတ်မှတ် အကြံပြုချက်ကို တင်သည်。

    ⚠️ ဤအဆင့်မှာ ဗီဒီယို **မထုတ်ရသေး**。 သုံးစွဲသူ စာတမ်းကို ကြည့်ပြီး
       ဘယ်အပိုင်း ကျန်မလဲ ဆုံးဖြတ်ပြီးမှသာ ဆက်လုပ်သည်。
    ⚠️ မိနစ်ကို **ဤအဆင့်မှာ မရေတွက်ရ** — ဗီဒီယို မထွက်သေး。
    """
    auth(authorization, WTOKEN)
    _beat()
    b = await req.json()
    segs = b.get("segs") or []
    # ⚠️ `segs_all` = ASR ရဲ့ **အပြည့်** — ဘယ်တော့မှ မပြောင်းရ (ပြန်ပြင်ရန်)
    db.run("UPDATE jobs SET status='review',stage=2,stage_name='စာတမ်း အတည်ပြုရန်',"
           "segs=?,segs_all=?,keep_n=NULL,plan=?,src_dur=?,minutes=0 WHERE id=?",
           json.dumps(segs, ensure_ascii=False),
           json.dumps(segs, ensure_ascii=False),
           json.dumps(b.get("plan") or {}, ensure_ascii=False),
           float(b.get("src_dur") or 0), jid)
    return {"ok": True, "segs": len(segs)}


@app.post("/api/jobs/{jid}/approve")
async def job_approve(jid: str, req: Request, authorization: str = Header(None)):
    """သုံးစွဲသူက စာတမ်းကို အတည်ပြု — **ကျန်သော စာလုံးအတိုင်း** ဖြတ်ပြီး ဆက်လုပ်သည်。

    ⚠️ **ဖျက်ရုံသာ ရသည်**。 အသံထဲ မရှိသော စာလုံးကို ဖြတ်၍ မရ ⇒ ပေးလာသော
       စာကြောင်းတိုင်း မူရင်းထဲ ရှိရမည်。 `fix` ကတော့ စာတန်းစာလုံးကိုသာ
       ပြင်သည် (အသံ · ဖြတ်မှတ် မထိ)。
    """
    auth(authorization, UTOKEN)
    j = mine(authorization, jid)
    if j.get("status") != "review":
        raise HTTPException(409, f"အတည်ပြုရန် အဆင့်မှာ မရှိပါ ({j.get('status')})")
    b = await req.json()
    try: orig = json.loads(j.get("segs") or "[]")
    except Exception: orig = []
    if not orig: raise HTTPException(400, "မူရင်း စာတမ်း မရှိ")
    keep = b.get("segs")
    if not isinstance(keep, list) or not keep:
        raise HTTPException(400, "စာသား မပါ")
    # ── ပြန်စ အကြံပြုချက် — **တစ်ခုချင်း ဆုံးဖြတ်ချက် မဖြစ်မနေ** ──
    # ⚠️ ဆုံးဖြတ်ချက်က ground truth ဖြစ်၍ ကျော်ခွင့် မပေး (UI ကိုလည်း မယုံ)。
    try: plan = json.loads(j.get("plan") or "{}") or {}
    except Exception: plan = {}
    rts = {str(r.get("id")): r for r in (plan.get("retakes") or []) if r.get("id")}
    RT_REASONS = ("not_retake", "keeps_content", "bad_boundary", "other")
    dmap = {}
    for d in (b.get("retakes") or []):
        rid = str((d or {}).get("id") or "")
        if rid not in rts: continue
        dec = d.get("decision")
        if dec not in ("accept", "reject"):
            raise HTTPException(400, f"ပြန်စ {rid} — ဆုံးဖြတ်ချက် မမှန်")
        rsn = str(d.get("reason") or "") if dec == "reject" else ""
        if rsn and rsn not in RT_REASONS: rsn = "other"
        dmap[rid] = (dec, rsn)
    undecided = [rid for rid in rts if rid not in dmap]
    if undecided:
        raise HTTPException(400, f"ပြန်စ အကြံပြုချက် {len(undecided)} ခု မဆုံးဖြတ်ရသေး — ✓ / ✗ ရွေးပါ")
    acc = [rts[r] for r, (dec, _) in dmap.items() if dec == "accept"]
    covered = {int(x) - 1 for r in acc for x in (r.get("sentences") or [])}
    # ── review v2 — အုပ်စု တစ်ခုချင်း **ဘယ် take ချန်မလဲ** (၂၀၂၆-၀၉-၁၆) ──
    # ⚠️ ပုံသေ = **ဘာမှ မဖျက်**。 ရွေးလိုက်သော take ကို ချန်ပြီး ကျန်တာသာ ဖျက်。
    #    ဖြတ်မှတ်ကို worker က ကြိုတွက်ပြီး (F2 စစ်ပြီးသား) — API က တွက်စရာ မလို。
    cls = {str(c.get("id")): c for c in (plan.get("clusters") or []) if c.get("id")}
    cpick = {}
    for d in (b.get("clusters") or []):
        cid = str((d or {}).get("id") or "")
        if cid not in cls: continue
        k = d.get("keep")
        if k in (None, "", "none"): cpick[cid] = None; continue
        k = str(k)
        if k not in (cls[cid].get("options") or {}):
            raise HTTPException(400, f"အုပ်စု {cid} — take {k} ကို ရွေးလို့ မရပါ")
        cpick[cid] = k
    # ⚠️ `clusters` ကို **လုံးဝ မပါလျှင်** = script editor မှ လာသည် ⇒ ပုံသေ
    #    「ဘာမှ မဖျက်」。 အဲဒီ editor မှာ သုံးစွဲသူက ဝါကျ တစ်ခုချင်း ကိုယ်တိုင်
    #    ဖျက်သည် — cluster က ထပ်ဖျက်လျှင် **သူ မတောင်းဘဲ ဖျက်ရာ** ကျသည်
    #    (Zin: 「user အတည်ပြုမှ ဖျက်ပေး · script editor မှာပဲ အနီပြထား」)。
    #    ⚠️ အရင်က 400 ပြန်ခဲ့ပြီး editor မှာ ရွေးစရာ ကိရိယာ မရှိသဖြင့်
    #       **ထွက်လမ်း လုံးဝ မရှိ**ဘဲ ပိတ်မိခဲ့သည် (၂၀၂၆-၀၉-၁၉ Zin တွေ့)。
    if "clusters" not in b:
        cpick = {cid: None for cid in cls}
    und_c = [cid for cid in cls if cid not in cpick]
    if und_c:
        raise HTTPException(400, f"ပြန်စ အုပ်စု {len(und_c)} ခု မရွေးရသေး — take ရွေးပါ (သို့) «ဘာမှ မဖျက်»")
    cl_exact = [list(iv) for cid, k in cpick.items() if k
                for iv in (cls[cid]["options"][k] or [])]
    covered |= {int(t["i"]) - 1 for cid, k in cpick.items() if k
                for t in cls[cid]["takes"] if str(t["n"]) != k}
    # ⚠️ လက်ခံထားသော ပြန်စ ဝါကျကို ချန်ထားလျှင် **ဆန့်ကျင်** — ဘယ်ဟာ မှန်လဲ မခွဲနိုင်
    if any(k.get("i") in covered and (k.get("text") or "").strip() for k in keep):
        raise HTTPException(400, "လက်ခံထားသော ပြန်စ ဝါကျကို ချန်ထား၍ မရ")
    exact = [[float(r["at"]), float(r["to"])] for r in acc if float(r["to"]) > float(r["at"])]
    exact += [[float(a), float(bb)] for a, bb in cl_exact if float(bb) > float(a)]
    obyid = {i: s for i, s in enumerate(orig)}
    clean = []
    for k in keep:
        i = k.get("i")
        if i is None or i not in obyid:
            raise HTTPException(400, "စာကြောင်း အသစ် ထည့်လို့ မရပါ")
        o = obyid[i]; t = (k.get("text") or "").strip()
        if not t: continue
        if t.replace(" ", "") not in o["text"].replace(" ", ""):
            raise HTTPException(400, f"စာလုံး အသစ် ပါနေသည်: {t[:30]}")
        e = dict(text=t, start=o["start"], end=o["end"])
        fx = (k.get("fix") or "").strip()
        if fx and fx != t:
            if len(fx) > len(t) * 3 + 40:
                raise HTTPException(400, "ပြင်ချက် ရှည်လွန်းသည်")
            e["fix"] = fx
        clean.append(e)
    if not clean: raise HTTPException(400, "အားလုံး ဖျက်ထားသည်")
    kept_i = {k.get("i") for k in keep if (k.get("text") or "").strip()}
    # ⚠️ လက်ခံထားသော ပြန်စ ဝါကျ — ဝါကျ start/end (မတိကျ) **မသုံး** · retake ရဲ့ [at,to] သာ
    drop = [[float(o["start"]), float(o["end"])]
            for i, o in enumerate(orig) if i not in kept_i and i not in covered]
    over = {}
    try: over = json.loads(j.get("over") or "{}") or {}
    except Exception: over = {}
    if drop: over["_drop"] = drop
    over.pop("_drop_exact", None)
    # ⚠️ **ဝါကျ အတွင်း အပိုင်း ဖျက်ချက်** — `_drop_exact` အဖြစ်သာ ပို့ရမည်。
    #    `_drop` ဆိုလျှင် worker က `CUT.guard` (အမြီး/ဦးခေါင်း) ဖြတ်ပြီး ဖြတ်မှတ်ကို
    #    စက္ကန့်များစွာ ရွှေ့ပစ်မည် — ဝါကျကြား အတွက် ဆောက်ထားသဖြင့် (၂၀၂၆-၀၉-၁၈
    #    F7 သင်ခန်းစာ)。 အပိုင်း နယ်နိမိတ်က တိတ်ဆိတ်မှု အလယ် ဖြစ်ပြီးသား ⇒ F2 = ၀。
    for a, bb in (b.get("drop_spans") or []):
        a, bb = float(a), float(bb)
        if bb - a > 0.02: exact.append([a, bb])
    if exact: over["_drop_exact"] = exact
    # The initial worker stores the take map in its review plan. Persist it for
    # the render pass, otherwise source labels (and cached-speed knowledge)
    # would be lost after the transcript is approved.
    if isinstance(plan.get("takes"), list): over["_take_map"] = plan["takes"]
    # ⚠️ `segs` က worker အတွက် (ချန်ထားသည်) · `segs_all` က **မထိရ** ·
    #    `keep_n` = ချန်ခဲ့သော နံပါတ် ⇒ ပြန်ဖွင့်လျှင် အရင် ဖျက်ချက် ပြန်မြင်ရ。
    _kn = sorted({int(k.get("i")) + 1 for k in keep
                  if k.get("i") is not None and (k.get("text") or "").strip()})
    db.run("UPDATE jobs SET status='queued',mode='go',stage=0,stage_name=NULL,"
           "segs=?,keep_n=?,over=?,approved=? WHERE id=?",
           json.dumps(clean, ensure_ascii=False),
           json.dumps(_kn),
           json.dumps(over, ensure_ascii=False) if over else None,
           str(time.time()), jid)
    # ── ဆုံးဖြတ်ချက် တစ်ခုချင်း မှတ်တမ်း (ground truth) ──
    _now = time.time()
    for rid, (dec, rsn) in dmap.items():
        r = rts[rid]
        db.run("INSERT INTO retake_review(id,job_id,new_job,upload_id,acct,rid,at_s,to_s,"
               "sentences,finals,conf,text,keep,decision,reason,created)"
               " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               db.nid("rr_"), jid, jid, j.get("upload_id"), j.get("acct") or aid(authorization),
               rid, float(r.get("at") or 0), float(r.get("to") or 0),
               json.dumps(r.get("sentences") or []), json.dumps(r.get("finals") or []),
               float(r.get("conf") or 0), str(r.get("text") or "")[:300],
               str(r.get("keep") or "")[:300], dec, rsn, _now)
    # ── v2 — အုပ်စု ရွေးချယ်ချက် မှတ်တမ်း (**ဤ feature ရဲ့ အဓိက ရည်ရွယ်ချက်**) ──
    for cid, k in cpick.items():
        c = cls[cid]
        iv = (c["options"][k] if k else [])
        db.run("INSERT INTO retake_pick(id,job_id,upload_id,acct,vfmt,cluster_id,takes,"
               "picked,dropped,drop_s,conf,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
               db.nid("rp_"), jid, j.get("upload_id"), j.get("acct") or aid(authorization),
               (j.get("vfmt") or ""), cid,
               json.dumps(c.get("takes") or [], ensure_ascii=False),
               (k or "none"), json.dumps(iv), round(sum(y - x for x, y in iv), 2),
               float(c.get("conf") or 0), _now)
    return {"ok": True, "kept": len(clean), "removed": len(orig) - len(clean),
            "cut_s": round(sum(b_ - a_ for a_, b_ in drop), 1),
            "retakes_accepted": len(acc), "retakes_rejected": len(dmap) - len(acc),
            "clusters": len(cls), "clusters_cut": sum(1 for v in cpick.values() if v),
            "retake_cut_s": round(sum(y - x for x, y in exact), 1)}


@app.post("/api/w/claim")
async def w_claim(req: Request, authorization: str = Header(None)):
    auth(authorization, WTOKEN)
    _beat()
    try: wb = await req.json()
    except Exception: wb = {}
    j = db.one("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1")
    if not j: return {"job": None}
    # ⚠️ **worker အများကြီး အတွက် အရေးကြီး**。 အရင်က status ကိုပဲ ပြန်စစ်ခဲ့ပြီး
    #    `db.run` က rowcount မပြန်သဖြင့် — worker A က UPDATE အောင်、B က မအောင်
    #    ဖြစ်သော်လည်း **B ရဲ့ ပြန်စစ်ချက်မှာလည်း 'running' တွေ့**ကာ နှစ်ခုလုံး
    #    job တစ်ခုတည်းကို ယူမိနိုင်သည် (၂၀၂၆-၀၉-၁၉ တွေ့)。
    #    ⇒ ကိုယ်ပိုင် အမှတ် ရိုက်ထည့်ပြီး **ကိုယ့်အမှတ် ဟုတ်မှ** ယူသည်。
    me = str((wb or {}).get("worker") or "") or f"w{int(time.time()*1000)%10**9}"
    db.run("UPDATE jobs SET status='running',claimed=?,worker=? WHERE id=? AND status='queued'",
           time.time(), me, j["id"])
    chk = db.one("SELECT * FROM jobs WHERE id=?", j["id"])
    if chk["status"] != "running" or (chk.get("worker") or "") != me:
        return {"job": None}   # တခြား worker က ယူသွားပြီ
    u = db.one("SELECT * FROM uploads WHERE id=?", j["upload_id"])
    b = db.one("SELECT * FROM brands WHERE id=?", j["brand_id"])
    if b: b["colors"] = json.loads(b["colors"])
    # ⚠️ ပုံစံ ပြင်ချက်ကို worker ဆီ **claim နဲ့ တစ်ခါတည်း** ပို့သည် —
    #    worker က DB ကို တိုက်ရိုက် မဖတ်နိုင်ဘူး (Mac မှာ ရှိသည်)。
    ov = db.one("SELECT data FROM style_over WHERE style=?", chk["recipe"])
    over = json.loads((ov or {}).get("data") or "{}")
    # ⚠️ job တစ်ခုချင်းရဲ့ ပြင်ချက်က style ရဲ့ ပြင်ချက်ကို **ဖုံးရမည်** —
    #    သုံးစွဲသူက ဒီဗီဒီယိုတစ်ခုတည်းအတွက် ပြောင်းတာမို့。
    source_uploads = [u] if u else []
    try:
        jo = json.loads(chk.get("over") or "{}")
        if isinstance(jo, dict):
            over.update(jo)
            for sid in (jo.get("_sources") or []):
                su = db.one("SELECT * FROM uploads WHERE id=?", sid)
                if not su: raise HTTPException(400, "multi-take source မရှိ")
                source_uploads.append(su)
    except Exception: pass
    return {"job": chk, "upload": u, "sources": source_uploads,
            "brand": b, "stages": STAGES, "over": over}

@app.get("/api/w/src2/{jid}")
def w_src2(jid: str, authorization: str = Header(None)):
    """dual-system အသံ ဖိုင် — မရှိလျှင် 404。"""
    auth(authorization, WTOKEN)
    j = db.one("SELECT * FROM jobs WHERE id=?", jid)
    try: over = json.loads((j or {}).get("over") or "{}") or {}
    except Exception: over = {}
    uid = over.get("_audio")
    if not uid: raise HTTPException(404, "no audio")
    u = db.one("SELECT * FROM uploads WHERE id=?", uid)
    if not u: raise HTTPException(404, "no audio")
    # ⚠️ worker ရဲ့ စက်ထဲက ဖိုင်ဆို **ဆွဲချစရာ မလို** — လမ်းကြောင်း ပဲ ပေးသည်
    if u.get("local"):
        return {"local": u["path"], "size": u["size"]}
    if u.get("key") and ST.on():
        return {"url": ST.get_url(u["key"], 7200), "size": u["received"]}
    if not u["path"] or not os.path.exists(u["path"]): raise HTTPException(404, "no audio")
    return FileResponse(u["path"])


@app.get("/api/w/src/{jid}")
def w_src(jid: str, authorization: str = Header(None), url: int = 0):
    """source ဖိုင် — local mode မှာ ဖိုင်၊ R2 mode မှာ presigned URL。

    ⚠️ 302 redirect **မသုံးရ** — urllib က redirect လိုက်တဲ့အခါ
       Authorization header ကိုပါ တစ်ခါတည်း ပို့သဖြင့် R2 က query-string auth
       နှစ်ခု တွေ့ပြီး 400 ပြန်သည်。 ⇒ URL ကို JSON နဲ့ ပေးပြီး worker က
       header မပါဘဲ သီးသန့် ဆွဲသည်。
    """
    auth(authorization, WTOKEN)
    j = db.one("SELECT * FROM jobs WHERE id=?", jid)
    u = db.one("SELECT * FROM uploads WHERE id=?", j["upload_id"]) if j else None
    if not u: raise HTTPException(404, "no source")
    # ⚠️ **worker ရဲ့ စက်ထဲက ဖိုင်** — လမ်းကြောင်း ပဲ ပေးရမည်。 ဤစစ်ချက်ကို
    #    အရင်က `w_src2` (အသံ route) ထဲ ထည့်မိပြီး ဒီမှာ ကျန်ခဲ့သဖြင့် —
    #    Mac လမ်းကြောင်းက VPS မှာ မရှိသည်အတွက် `os.path.exists` က False ဖြစ်ကာ
    #    **404** ပြန်ခဲ့သည်。 upload ကျော်တဲ့ လမ်းကြောင်း သုံးတိုင်း job ကျခဲ့
    #    (Zin ၂၀၂၆-၀၉-၂၀ · ၄ ကြိမ် · "ဘာလို့ တင်လို့ မရတာလဲ")。
    if u.get("local"):
        return {"local": u["path"], "size": u["size"]}
    if u.get("key") and ST.on():
        return {"url": ST.get_url(u["key"], 7200), "size": u["received"]}
    if not u["path"] or not os.path.exists(u["path"]): raise HTTPException(404, "no source")
    return FileResponse(u["path"])


@app.get("/api/w/src/{jid}/take/{n}")
def w_src_take(jid: str, n: int, authorization: str = Header(None)):
    """Additional camera take for a multi-take project (zero-based index)."""
    auth(authorization, WTOKEN)
    if n < 1: raise HTTPException(400, "additional take က 1 ကနေစသည်")
    j = db.one("SELECT * FROM jobs WHERE id=?", jid)
    try: over = json.loads((j or {}).get("over") or "{}") or {}
    except Exception: over = {}
    ids = over.get("_sources") or []
    if n > len(ids): raise HTTPException(404, "no take")
    u = db.one("SELECT * FROM uploads WHERE id=?", ids[n - 1])
    if not u: raise HTTPException(404, "no take")
    if u.get("local"):
        return {"local": u["path"], "size": u["size"]}
    if u.get("key") and ST.on():
        return {"url": ST.get_url(u["key"], 7200), "size": u["received"]}
    if not u.get("path") or not os.path.exists(u["path"]):
        raise HTTPException(404, "no take")
    return FileResponse(u["path"])

@app.post("/api/w/{jid}/puturl")
def w_puturl(jid: str, authorization: str = Header(None)):
    """render ပြီးသော ဖိုင်ကို R2 ကို တိုက်ရိုက် တင်ရန် presigned PUT URL。"""
    auth(authorization, WTOKEN)
    if not ST.on(): raise HTTPException(409, "R2 မဖွင့်ထား")
    n = (db.one("SELECT COALESCE(MAX(n),0) n FROM versions WHERE job_id=?", jid) or {"n":0})["n"] + 1
    key = f"out/{jid}_v{n}.mp4"
    return {"url": ST.presign("PUT", key, 7200), "key": key}

@app.post("/api/w/{jid}/stage")
async def w_stage(jid: str, req: Request, authorization: str = Header(None)):
    auth(authorization, WTOKEN)
    _beat()
    b = await req.json()
    db.run("UPDATE jobs SET stage=?,stage_name=?,minutes=? WHERE id=?",
           int(b.get("stage",0)), b.get("name",""), float(b.get("minutes",0)), jid)
    return {"ok": True}

@app.post("/api/w/{jid}/fail")
async def w_fail(jid: str, req: Request, authorization: str = Header(None)):
    auth(authorization, WTOKEN)
    _beat()
    b = await req.json()
    j = db.one("SELECT * FROM jobs WHERE id=?", jid)
    # ⚠️ ပျက်သွားသော အလုပ်အတွက် မိနစ် **မယူရ** — UI က ကတိပေးထားသည်
    db.run("UPDATE usage SET minutes=max(0,minutes-?) WHERE ym=?",
           (j or {}).get("minutes") or 0, time.strftime("%Y-%m"))
    db.run("UPDATE jobs SET status='failed',err=?,finished=?,minutes=0 WHERE id=?",
           b.get("err","")[:2000], time.time(), jid)
    return {"ok": True}

@app.post("/api/w/{jid}/result")
async def w_result(jid: str, file: UploadFile = File(None), meta: str = Form("{}"),
                   authorization: str = Header(None)):
    auth(authorization, WTOKEN)
    _beat()
    m = json.loads(meta or "{}")
    okey = m.get("out_key") or ""
    if okey and ST.on():
        # ⚠️ R2 mode — worker က ဖိုင်ကို R2 ကို တင်ပြီးသား၊ ဒီမှာ metadata ပဲ
        #    လာသည်。 ဖိုင် တကယ် ရောက်မရောက် **HEAD နဲ့ စစ်ရမည်** — မစစ်လျှင်
        #    တင်မရဘဲ "done" ပြနိုင်သည်。
        if not ST.head(okey): raise HTTPException(400, "R2 မှာ ဖိုင် မရှိ")
        p = okey
    else:
        if file is None: raise HTTPException(400, "ဖိုင် မပါ")
        p = os.path.join(OUT, f"{jid}.mp4")
        with open(p, "wb") as f: shutil.copyfileobj(file.file, f)
    n = (db.one("SELECT COALESCE(MAX(n),0) n FROM versions WHERE job_id=?", jid) or {"n":0})["n"] + 1
    db.run("INSERT INTO versions(id,job_id,n,note,out_path,dur,created) VALUES(?,?,?,?,?,?,?)",
           db.nid("v_"), jid, n, m.get("note",""), p, float(m.get("out_dur",0)), time.time())
    # ⚠️ flags ကို သိမ်းရမည် — worker က ပို့ပေမယ့် သိမ်းမထားလျှင် UI က
    #    "အတည်ပြုရန် N ခု" ပြလို့ မရဘူး (တိတ်တဆိတ် ပျောက်ခဲ့သည်)。
    db.run("UPDATE jobs SET status='done',stage=7,out_key=?,out_path=?,out_dur=?,src_dur=?,"
           "cuts=?,captions=?,flags=?,flag_list=?,minutes=?,finished=? WHERE id=?",
           (okey or None), p, float(m.get("out_dur",0)), float(m.get("src_dur",0)),
           int(m.get("cuts",0)), int(m.get("captions",0)),
           int(m.get("flags",0)), json.dumps(m.get("flag_list") or [], ensure_ascii=False),
           float(m.get("minutes",0)), time.time(), jid)
    if m.get("segs") is not None:
        db.run("UPDATE jobs SET segs=? WHERE id=?",
               json.dumps(m.get("segs"), ensure_ascii=False), jid)
    # ⚠️ Headtop ရဲ့ edit plan — **သိမ်းမှသာ** သုံးစွဲသူက event ပြင်နိုင်သည်。
    #    `flags` လိုပဲ worker က ပို့ပေမယ့် သိမ်းမထားလျှင် တိတ်တဆိတ် ပျောက်သည်。
    if m.get("edit_plan"):
        db.run("UPDATE jobs SET edit_plan=? WHERE id=?",
               json.dumps(m.get("edit_plan"), ensure_ascii=False), jid)
    db.run("UPDATE usage SET minutes=minutes+? WHERE ym=?",
           float(m.get("minutes",0)), time.strftime("%Y-%m"))
    _notify(jid, m)
    return {"ok": True, "version": n}

def _notify(jid, m):
    """⚠️ UI က "ပြီးရင် Telegram က အကြောင်းကြားပါမယ်" လို့ ကတိပေးထားသည် —
       ကုဒ်ထဲ တကယ် ရှိရမည်。 chat id/token မရှိလျှင် တိတ်တဆိတ် ကျော်သည်。"""
    try:
        st = {r["k"]: r["v"] for r in db.rows("SELECT * FROM settings")}
        tok = st.get("tg_token") or os.environ.get("IKKI_TG_TOKEN","")
        chat = st.get("tg_chat") or os.environ.get("IKKI_TG_CHAT","")
        if not tok or not chat: return
        j = db.one("SELECT * FROM jobs WHERE id=?", jid) or {}
        cut = max(0.0, (j.get("src_dur") or 0) - (j.get("out_dur") or 0))
        txt = (f"✅ {j.get('title') or jid}\n"
               f"{cut:.0f} စက္ကန့် ဖြတ်လိုက်ပါတယ် · စာတန်း {j.get('captions') or 0} ကြောင်း"
               f" · ဖြတ်ချက် {j.get('cuts') or 0} ခု")
        if (j.get("flags") or 0): txt += f"\n⚠️ အတည်ပြုရန် {j['flags']} ခု"
        import urllib.request as _u, urllib.parse as _p
        _u.urlopen(_u.Request(f"https://api.telegram.org/bot{tok}/sendMessage",
            data=_p.urlencode({"chat_id":chat,"text":txt}).encode()), timeout=15).read()
    except Exception:
        pass


def _tg(txt):
    """Telegram သို့ စာတစ်ကြောင်း — token/chat မရှိလျှင် False。"""
    try:
        st = {r["k"]: r["v"] for r in db.rows("SELECT * FROM settings")}
        tok = st.get("tg_token") or os.environ.get("IKKI_TG_TOKEN","")
        chat = st.get("tg_chat") or os.environ.get("IKKI_TG_CHAT","")
        if not tok or not chat: return False
        import urllib.request as _u, urllib.parse as _p
        _u.urlopen(_u.Request(f"https://api.telegram.org/bot{tok}/sendMessage",
            data=_p.urlencode({"chat_id":chat,"text":txt}).encode()), timeout=15).read()
        return True
    except Exception:
        return False


# ══ Plan · မိနစ် ═══════════════════════════════════════════
# ⚠️ **ငွေပေးချေမှု စနစ် မတပ်ရသေး** — card gateway မရှိ。 ဒါကြောင့် ဒီမှာ
#    "ဝယ်ပြီးပြီ" ဟု မပြရ。 plan ကို ကိုယ်တိုင် သတ်မှတ်ပြီး မိနစ် ကုန်လျှင်
#    **ဘာလုပ်ရမလဲ ရှင်းရှင်း ပြရမည်** — အရင်က error တစ်ကြောင်းနဲ့ ရပ်သွားသည်。
PLAN_DEF = dict(name="Starter", quota=300.0, price="", renews="", contact="")

def _plan():
    st = {r["k"]: r["v"] for r in db.rows("SELECT * FROM settings")}
    p = dict(PLAN_DEF)
    for k in p:
        v = st.get("plan_" + k)
        if v not in (None, ""):
            p[k] = float(v) if k == "quota" else v
    ym = time.strftime("%Y-%m")
    u = db.one("SELECT * FROM usage WHERE ym=?", ym) or {"ym": ym, "minutes": 0, "quota": p["quota"]}
    # ⚠️ usage.quota ကို plan နဲ့ **တစ်ထပ်တည်း** ထားရမည် — မဟုတ်လျှင်
    #    Account မှာ ၃၀၀ ပြပြီး render က တခြားကိန်းနဲ့ ပိတ်မည်。
    if abs(float(u.get("quota") or 0) - p["quota"]) > 0.01:
        db.run("INSERT INTO usage(ym,minutes,quota) VALUES(?,0,?) "
               "ON CONFLICT(ym) DO UPDATE SET quota=?", ym, p["quota"], p["quota"])
        u["quota"] = p["quota"]
    used = float(u.get("minutes") or 0)
    return dict(plan=p, ym=ym, used=round(used, 1),
                quota=p["quota"], left=round(max(0.0, p["quota"] - used), 1),
                pct=round(min(1.0, used / p["quota"]) if p["quota"] else 1.0, 3))


@app.get("/api/plan")
def plan_get(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    return _plan()


@app.post("/api/plan")
async def plan_set(req: Request, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    b = await req.json()
    for k in ("name", "quota", "price", "renews", "contact"):
        if k in b and b[k] is not None:
            db.run("INSERT INTO settings(k,v) VALUES(?,?) "
                   "ON CONFLICT(k) DO UPDATE SET v=?",
                   "plan_" + k, str(b[k]), str(b[k]))
    return _plan()


@app.post("/api/plan/topup")
async def plan_topup(req: Request, authorization: str = Header(None)):
    """မိနစ် ထပ်တောင်းခြင်း。

    ⚠️ **ဒီမှာ ငွေ မရှင်းပါ** — gateway မတပ်ရသေး。 Telegram ကနေ
       တောင်းဆိုချက် ပို့ပေးရုံသာ。 "ဝယ်ပြီးပြီ" ဟု မပြရ、လိမ်ရာ ကျသည်。
    """
    auth(authorization, UTOKEN)
    b = await req.json()
    p = _plan()
    want = b.get("minutes")
    txt = (f"💳 မိနစ် ထပ်တောင်းချက်\n"
           f"plan: {p['plan']['name']} · သုံးပြီး {p['used']}/{p['quota']} မိနစ်\n"
           f"တောင်းတာ: {want or '(မပြော)'} မိနစ်")
    if b.get("note"): txt += f"\nမှတ်ချက်: {str(b['note'])[:200]}"
    sent = _tg(txt)
    return {"ok": True, "sent": sent,
            "contact": p["plan"].get("contact") or "",
            "note": "Telegram သို့ ပို့ပြီး" if sent
                    else "Telegram မသတ်မှတ်ရသေး — Account မှာ ထည့်ပါ"}


# ══ ငွေပေးချေမှု · KBZPay / Wave / CB Pay ═══════════════════
# ⚠️ ဒါက **card gateway မဟုတ်**。 Stripe/PayPal က မြန်မာက လုပ်ငန်းကို
#    payout မပေး၍ မသုံးနိုင်。 ⇒ QR + ငွေလွှဲနံပါတ် + **လူကိုယ်တိုင်
#    အတည်ပြု** နည်း。 server က ငွေရပြီးမပြီး မသိနိုင်သဖြင့် —
#      ၁။ အလိုအလျောက် အတည်ပြုခြင်း လုံးဝ မလုပ်ရ (မိနစ် အလကား ရသွားမည်)
#      ၂။ ငွေလွှဲနံပါတ် တစ်ခုကို တစ်ခါပဲ သုံးခွင့်ပြု (DB unique index)
#      ၃။ "ငွေရပြီးပါပြီ" ဟု **မပြရ** — "စစ်ဆေးနေဆဲ" ဟုသာ ပြရမည်
PAY   = os.path.join(DATA, "pay")
os.makedirs(PAY, exist_ok=True)

# (id, မြန်မာ label, EN label)
PAYM = [("kbz", "KBZPay", "KBZPay"),
        ("wave", "Wave Pay", "Wave Pay"),
        ("cb",  "CB Pay",  "CB Pay")]
PAYIDS = [m[0] for m in PAYM]


def _owner(h, t2=""):
    """ပိုင်ရှင် ဟုတ်မဟုတ်。 env token ဒါမှမဟုတ် ပုံသေအကောင့် ဖြစ်ရမည်。

    ⚠️ ဆက်တင် ပြင်ခွင့်/အတည်ပြုခွင့်ကို **အကောင့်တိုင်း မပေးရ** — ပေးလျှင်
       customer က ကိုယ့်ငွေလွှဲကို ကိုယ်တိုင် အတည်ပြုပြီး မိနစ် ယူသွားမည်。
    """
    t = (h or "").replace("Bearer ", "") or t2
    return bool(t) and (t == UTOKEN or (who(h, t2) or {}).get("id") == "a_default")


def _need_owner(h):
    if not _owner(h): raise HTTPException(403, "ပိုင်ရှင်သာ လုပ်နိုင်သည်")


def _paycfg():
    st = {r["k"]: r["v"] for r in db.rows("SELECT * FROM settings")}
    try: rate = float(st.get("pay_rate") or 0)
    except ValueError: rate = 0.0
    out = []
    for mid, lab_my, lab_en in PAYM:
        out.append(dict(
            id=mid, my=lab_my, en=lab_en,
            name=st.get(f"pay_{mid}_name") or "",
            num=st.get(f"pay_{mid}_num") or "",
            on=(st.get(f"pay_{mid}_on") or "0") == "1",
            qr=os.path.exists(os.path.join(PAY, f"{mid}.png"))))
    return out, rate


def _payrow(r, my_acct=None, owner=False):
    d = dict(r)
    if not owner and my_acct is not None:
        d.pop("by", None)
    return d


@app.get("/api/pay")
def pay_get(authorization: str = Header(None)):
    """ငွေလွှဲ နည်းလမ်းများ + ကိုယ့်တောင်းဆိုချက်များ。"""
    auth(authorization, UTOKEN)
    ms, rate = _paycfg()
    a = aid(authorization)
    own = _owner(authorization)
    mine_ = db.rows("SELECT * FROM pays WHERE acct=? ORDER BY created DESC LIMIT 20", a)
    res = dict(methods=ms, rate=rate, owner=own,
               mine=[_payrow(r, a, own) for r in mine_])
    if own:
        res["pending"] = (db.one("SELECT COUNT(*) n FROM pays WHERE status='pending'")
                          or {}).get("n", 0)
    # ⚠️ ဖွင့်ထားပြီး နံပါတ် မထည့်ရသေးလျှင် customer က ဘယ်ကို လွှဲရမှန်း မသိ
    res["ready"] = any(m["on"] and (m["num"] or m["qr"]) for m in ms)
    return res


@app.post("/api/pay/settings")
async def pay_settings(req: Request, authorization: str = Header(None)):
    auth(authorization, UTOKEN); _need_owner(authorization)
    b = await req.json()
    def put(k, v):
        db.run("INSERT INTO settings(k,v) VALUES(?,?) "
               "ON CONFLICT(k) DO UPDATE SET v=?", k, str(v), str(v))
    if b.get("rate") is not None:
        try: put("pay_rate", float(b["rate"]))
        except (TypeError, ValueError): raise HTTPException(400, "rate က ဂဏန်း ဖြစ်ရမည်")
    for mid in PAYIDS:
        m = b.get(mid)
        if not isinstance(m, dict): continue
        if "name" in m: put(f"pay_{mid}_name", str(m["name"])[:60])
        if "num"  in m: put(f"pay_{mid}_num",  str(m["num"])[:40])
        if "on"   in m: put(f"pay_{mid}_on", "1" if m["on"] else "0")
    ms, rate = _paycfg()
    return {"ok": True, "methods": ms, "rate": rate}


@app.post("/api/pay/qr/{mid}")
async def pay_qr_put(mid: str, file: UploadFile = File(...),
                     authorization: str = Header(None)):
    auth(authorization, UTOKEN); _need_owner(authorization)
    if mid not in PAYIDS: raise HTTPException(404, "နည်းလမ်း မတွေ့")
    raw = await file.read()
    if len(raw) > 4 * 1024 * 1024: raise HTTPException(413, "၄ MB ထက် မကြီးရ")
    p = os.path.join(PAY, f"{mid}.png")
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.thumbnail((1200, 1200))
        im.save(p)
    except Exception as e:
        raise HTTPException(400, f"ပုံ ဖတ်မရ: {e}")
    return {"ok": True, "qr": True}


@app.get("/api/pay/qr/{mid}")
def pay_qr_get(mid: str, authorization: str = Header(None), t: str = ""):
    # ⚠️ <img> က header မပါ ⇒ ?t= token ကိုလည်း လက်ခံရသည် (logo နဲ့ တူ)
    auth(authorization or (f"Bearer {t}" if t else None), UTOKEN)
    if mid not in PAYIDS: raise HTTPException(404, "နည်းလမ်း မတွေ့")
    p = os.path.join(PAY, f"{mid}.png")
    if not os.path.exists(p): raise HTTPException(404, "QR မရှိ")
    return FileResponse(p, media_type="image/png")


@app.delete("/api/pay/qr/{mid}")
def pay_qr_del(mid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN); _need_owner(authorization)
    p = os.path.join(PAY, f"{mid}.png")
    if os.path.exists(p): os.unlink(p)
    return {"ok": True}


@app.post("/api/pay")
async def pay_new(req: Request, authorization: str = Header(None)):
    """ငွေလွှဲပြီးကြောင်း တင်ပြခြင်း。

    ⚠️ ဒီ endpoint က **မိနစ် မတိုး**。 `status='pending'` ပဲ ဖြစ်သည်。
       ပိုင်ရှင်က bank app ထဲ ငွေလွှဲနံပါတ် စစ်ပြီး `/approve` ခေါ်မှ တက်သည်。
    """
    auth(authorization, UTOKEN)
    b = await req.json()
    a = aid(authorization)
    mid = str(b.get("method") or "").strip()
    if mid not in PAYIDS: raise HTTPException(400, "နည်းလမ်း မမှန်")
    ms, rate = _paycfg()
    m = next(x for x in ms if x["id"] == mid)
    if not m["on"]: raise HTTPException(400, f"{m['my']} ကို ဖွင့်မထားပါ")
    try: amt = float(b.get("amount") or 0)
    except (TypeError, ValueError): raise HTTPException(400, "ငွေပမာဏ မမှန်")
    if amt <= 0: raise HTTPException(400, "ငွေပမာဏ ထည့်ပါ")
    ref = str(b.get("ref") or "").strip()
    # ⚠️ ငွေလွှဲနံပါတ် မပါလျှင် ပိုင်ရှင် စစ်လို့ မရ ⇒ လက်မခံရ
    if len(ref) < 4: raise HTTPException(400, "ငွေလွှဲနံပါတ် (အနည်းဆုံး ၄ လုံး) ထည့်ပါ")
    if db.one("SELECT id FROM pays WHERE ref=?", ref):
        raise HTTPException(409, "ဒီ ငွေလွှဲနံပါတ်ကို တင်ပြီးသားပါ")
    # ⚠️ စောင့်နေတာ များနေလျှင် ပိုင်ရှင် အလုပ်ရှုပ်မည် — ကန့်သတ်သည်
    n = (db.one("SELECT COUNT(*) n FROM pays WHERE acct=? AND status='pending'", a)
         or {}).get("n", 0)
    if n >= 5: raise HTTPException(429, "စောင့်ဆိုင်းနေတာ ၅ ခု ရှိပြီ — အတည်ပြုပြီးမှ ထပ်တင်ပါ")
    mins = None
    if b.get("minutes") not in (None, ""):
        try: mins = float(b["minutes"])
        except (TypeError, ValueError): mins = None
    if mins is None and rate > 0: mins = round(amt / rate, 1)
    pid = "p_" + os.urandom(5).hex()
    db.run("INSERT INTO pays(id,acct,method,amount,minutes,ref,note,status,created)"
           " VALUES(?,?,?,?,?,?,?,'pending',?)",
           pid, a, mid, amt, mins, ref, str(b.get("note") or "")[:300], time.time())
    acc = who(authorization)
    sent = _tg(f"💰 ငွေလွှဲ တင်ပြချက်\n"
               f"အကောင့်: {acc.get('name') or a}\n"
               f"{m['my']} · {amt:,.0f} MMK"
               + (f" ≈ {mins} မိနစ်" if mins else "") +
               f"\nငွေလွှဲနံပါတ်: {ref}"
               + (f"\nမှတ်ချက်: {b.get('note')}" if b.get("note") else "") +
               f"\n\n⚠️ bank app ထဲ စစ်ပြီးမှ Account → ငွေပေးချေမှု မှာ အတည်ပြုပါ")
    return {"ok": True, "id": pid, "status": "pending", "minutes": mins, "sent": sent,
            "note": "စစ်ဆေးနေပါတယ် — အတည်ပြုပြီးမှ မိနစ် တက်ပါမယ်"}


@app.get("/api/pay/all")
def pay_all(authorization: str = Header(None), status: str = ""):
    auth(authorization, UTOKEN); _need_owner(authorization)
    q = "SELECT * FROM pays"
    args = []
    if status:
        q += " WHERE status=?"; args.append(status)
    q += " ORDER BY (status='pending') DESC, created DESC LIMIT 200"
    rows = db.rows(q, *args)
    names = {a["id"]: a["name"] for a in db.rows("SELECT id,name FROM accounts")}
    for r in rows: r["acct_name"] = names.get(r.get("acct"), r.get("acct"))
    return {"pays": rows}


@app.post("/api/pay/{pid}/approve")
async def pay_approve(pid: str, req: Request, authorization: str = Header(None)):
    """အတည်ပြု → မိနစ် တက်。

    ⚠️ မိနစ်ကို **ဒီလရဲ့ ကန့်သတ်ချက် (plan quota)** ထဲ ပေါင်းထည့်သည် —
       `_plan()` က plan_quota ကို usage.quota နဲ့ တစ်ထပ်တည်း ထားသဖြင့်
       နှစ်နေရာလုံး တက်သွားသည်。
    """
    auth(authorization, UTOKEN); _need_owner(authorization)
    try: b = await req.json()
    except Exception: b = {}
    r = db.one("SELECT * FROM pays WHERE id=?", pid)
    if not r: raise HTTPException(404, "မတွေ့ပါ")
    if r["status"] != "pending": raise HTTPException(409, f"ဆုံးဖြတ်ပြီးသား ({r['status']})")
    mins = b.get("minutes", r.get("minutes"))
    try: mins = float(mins or 0)
    except (TypeError, ValueError): mins = 0.0
    if mins <= 0: raise HTTPException(400, "ဘယ်နှစ်မိနစ် ပေါင်းထည့်မလဲ ထည့်ပါ")
    p = _plan()
    newq = round(float(p["quota"]) + mins, 1)
    db.run("INSERT INTO settings(k,v) VALUES('plan_quota',?) "
           "ON CONFLICT(k) DO UPDATE SET v=?", str(newq), str(newq))
    db.run("INSERT INTO usage(ym,minutes,quota) VALUES(?,0,?) "
           "ON CONFLICT(ym) DO UPDATE SET quota=?", p["ym"], newq, newq)
    db.run("UPDATE pays SET status='ok',minutes=?,decided=?,by=? WHERE id=?",
           mins, time.time(), (who(authorization) or {}).get("id"), pid)
    _tg(f"✅ ငွေလွှဲ အတည်ပြုပြီး · {mins} မိနစ် ပေါင်းထည့်ပြီး\n"
        f"ငွေလွှဲနံပါတ်: {r['ref']} · ကန့်သတ်ချက် {newq} မိနစ်")
    return {"ok": True, "minutes": mins, "quota": newq, "plan": _plan()}


@app.post("/api/pay/{pid}/reject")
async def pay_reject(pid: str, req: Request, authorization: str = Header(None)):
    auth(authorization, UTOKEN); _need_owner(authorization)
    try: b = await req.json()
    except Exception: b = {}
    r = db.one("SELECT * FROM pays WHERE id=?", pid)
    if not r: raise HTTPException(404, "မတွေ့ပါ")
    if r["status"] != "pending": raise HTTPException(409, f"ဆုံးဖြတ်ပြီးသား ({r['status']})")
    db.run("UPDATE pays SET status='no',decided=?,by=?,why=? WHERE id=?",
           time.time(), (who(authorization) or {}).get("id"),
           str(b.get("why") or "")[:200], pid)
    return {"ok": True}


@app.delete("/api/pay/{pid}")
def pay_del(pid: str, authorization: str = Header(None)):
    """ကိုယ့်ဟာ + စောင့်ဆိုင်းဆဲ ဖြစ်မှ ပြန်ရုပ်သိမ်းနိုင်သည်。"""
    auth(authorization, UTOKEN)
    r = db.one("SELECT * FROM pays WHERE id=?", pid)
    if not r: raise HTTPException(404, "မတွေ့ပါ")
    if not _owner(authorization) and r.get("acct") != aid(authorization):
        raise HTTPException(404, "မတွေ့ပါ")
    if r["status"] != "pending" and not _owner(authorization):
        raise HTTPException(409, "ဆုံးဖြတ်ပြီးသား — ဖျက်လို့ မရပါ")
    db.run("DELETE FROM pays WHERE id=?", pid)
    return {"ok": True}


# ══ ဗီဒီယို ဖျက်ခြင်း ═══════════════════════════════════════
@app.delete("/api/jobs/{jid}")
def job_delete(jid: str, authorization: str = Header(None), purge: int = 0):
    """job ကို **အမှိုက်ပုံးထဲ ထည့်**သည် — ဖိုင်ကို ချက်ချင်း မဖျက်。

    ⚠️ အရင်က ချက်ချင်း အပြီးအပိုင် ဖျက်ခဲ့သည်。 တစ်ချိန်တည်းမှာ ဗီဒီယို ၂၆ ခု
       ပျောက်သွားပြီး **ဘယ်သူ ဖျက်လဲ log ကနေ ခွဲလို့ မရ**ခဲ့ (proxy တစ်ခုတည်း
       ဖြတ်လာ၍)。 ⇒ ပြန်ရနိုင်ရမည်。 `deleted` အချိန် မှတ်ထားပြီး
       ၂၄ နာရီကြာမှ ဖိုင်ကို တကယ် ဖျက်သည် (`purge`)。
    """
    auth(authorization, UTOKEN)
    j = mine(authorization, jid)
    if j.get("status") in ("queued", "running"):
        raise HTTPException(409, "လုပ်နေဆဲ — အရင် ရပ်ပါ")
    if not purge:
        db.run("UPDATE jobs SET deleted=? WHERE id=?", time.time(), jid)
        return {"ok": True, "trashed": True, "undo_until": time.time() + 86400}
    return _purge_job(j)


def _purge_job(j):
    """ဖိုင်တွေကို **တကယ်** ဖျက်သည် (R2 အပါအဝင်)。"""
    jid = j["id"]
    keys, paths, gone = [], [], []
    for v in db.rows("SELECT * FROM versions WHERE job_id=?", jid):
        (keys if (v.get("out_path") or "").startswith("out/") else paths).append(v.get("out_path"))
    if j.get("out_key"): keys.append(j["out_key"])
    if j.get("out_path") and not str(j["out_path"]).startswith("out/"): paths.append(j["out_path"])
    for k in set(x for x in keys if x):
        try:
            if ST.on() and ST.delete(k): gone.append(k)
        except Exception as e:
            print(f"⚠️ R2 ဖျက်မရ {k}: {e}", flush=True)
    for p in set(x for x in paths if x):
        try:
            if os.path.exists(p): os.unlink(p); gone.append(os.path.basename(p))
        except OSError as e:
            print(f"⚠️ ဖိုင် ဖျက်မရ {p}: {e}", flush=True)
    t = os.path.join(THUMB, jid + ".jpg")
    if os.path.exists(t):
        try: os.unlink(t)
        except OSError: pass
    db.run("DELETE FROM versions WHERE job_id=?", jid)
    db.run("DELETE FROM jobs WHERE id=?", jid)
    return {"ok": True, "deleted": len(gone)}


@app.post("/api/jobs/{jid}/restore")
def job_restore(jid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    j = mine(authorization, jid)
    db.run("UPDATE jobs SET deleted=NULL WHERE id=?", jid)
    return {"ok": True}


@app.get("/api/trash")
def trash(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    rows = db.rows("SELECT * FROM jobs WHERE deleted IS NOT NULL AND acct=?"
                   " ORDER BY deleted DESC", aid(authorization))
    return {"jobs": rows}


def _verify(n=8):
    """ဖိုင် တကယ် ရှိမရှိ စစ်သည် — "ပြီး" ပြနေပြီး ဒေါင်းလုပ် မရတာ မဖြစ်စေရန်。

    ⚠️ R2 lifecycle · မတော်တဆ ဖျက်မိတာ စသည်ဖြင့် output ပျောက်နိုင်သည်。
       စာရင်းမှာ "ပြီး" ပြနေပြီး နှိပ်မှ ကျလျှင် **ယုံကြည်မှု ပျက်**သည်。
    ⚠️ စာရင်း ခေါ်တိုင်း အားလုံး HEAD လုပ်လျှင် နှေးသည် ⇒ **အကြာဆုံး
       မစစ်ရသေးတာ n ခု**ကိုသာ စစ်သည် (၆ နာရီတစ်ခါ ပြန်စစ်)。
    """
    cut = time.time() - 21600
    rows = db.rows("SELECT * FROM jobs WHERE status='done' AND deleted IS NULL"
                   " AND (checked IS NULL OR checked < ?)"
                   " ORDER BY COALESCE(checked,0) LIMIT ?", cut, n)
    for j in rows:
        ok = True
        try:
            if j.get("out_key") and ST.on():
                ok = bool(ST.head(j["out_key"]))
            elif j.get("out_path"):
                ok = os.path.exists(j["out_path"])
        except Exception:
            continue                       # ⚠️ စစ်လို့ မရတာကို "ပျောက်" ဟု မမှတ်ရ
        db.run("UPDATE jobs SET gone=?, checked=? WHERE id=?",
               0 if ok else 1, time.time(), j["id"])


def _sweep():
    """၂၄ နာရီ ကျော်သွားသော အမှိုက်ကို တကယ် ဖျက်သည် (စာရင်း ခေါ်တိုင်း)。"""
    cut = time.time() - 86400
    for j in db.rows("SELECT * FROM jobs WHERE deleted IS NOT NULL AND deleted < ?", cut):
        try: _purge_job(j)
        except Exception as e: print(f"⚠️ sweep {j['id']}: {e}", flush=True)


# ══ ပုံငယ် (thumbnail) ══════════════════════════════════════
@app.post("/api/w/{jid}/thumb")
async def w_thumb(jid: str, file: UploadFile = File(...),
                  authorization: str = Header(None)):
    """worker က ထုတ်လိုက်သော ပုံငယ်ကို လက်ခံသည်。

    ⚠️ ဒီ route ကို **ဆောက်ရန် ကျန်ခဲ့**သည် — worker က render ပြီးတိုင်း
       ပို့နေပေမယ့် `405 Method Not Allowed` ပြန်ရပြီး ပုံငယ် တစ်ခါမှ
       မရောက်ခဲ့ ⇒ UI မှာ ဗီဒီယို ကဒ်တိုင်း ပုံမပါဘဲ ဗလာ ဖြစ်နေခဲ့သည်。
    ⚠️ API image မှာ ffmpeg မပါ ⇒ ပုံငယ်ကို **worker ကပဲ** ထုတ်နိုင်သည်。
    """
    auth(authorization, WTOKEN)
    if not db.one("SELECT id FROM jobs WHERE id=?", jid):
        raise HTTPException(404, "job မတွေ့")
    raw = await file.read()
    if not raw: raise HTTPException(400, "ဗလာ")
    if len(raw) > 4 * 1024 * 1024: raise HTTPException(413, "၄ MB ထက် မကြီးရ")
    os.makedirs(THUMB, exist_ok=True)
    with open(os.path.join(THUMB, f"{jid}.jpg"), "wb") as f:
        f.write(raw)
    return {"ok": True, "bytes": len(raw)}



@app.post("/api/w/{jid}/audio")
async def w_audio(jid: str, file: UploadFile = File(...),
                  authorization: str = Header(None)):
    """worker က ထုတ်လိုက်သော **အသံ proxy** (m4a) — Script Editor မှာ နားထောင်ရန်。

    ⚠️ ဖြတ်ချက် ဆုံးဖြတ်ဖို့ **နားထောင်ရမည်** — စာသား ဖတ်ရုံနဲ့ မလုံလောက်。
       (Zin: 「စကားလုံး တစ်လုံးချင်း နားထောက်ပြီး တိုင်းမှ ဖြတ်ချက် မှန်မယ်」)
    ⚠️ မူရင်း ဗီဒီယို (GB ချီ) ကို မပို့ရ — **၄၈ kbps mono m4a** သာ (၃ မိနစ် ≈ ၁ MB)。
    """
    auth(authorization, WTOKEN)
    if not db.one("SELECT id FROM jobs WHERE id=?", jid):
        raise HTTPException(404, "job မတွေ့")
    raw = await file.read()
    if not raw: raise HTTPException(400, "ဗလာ")
    if len(raw) > 60 * 1024 * 1024: raise HTTPException(413, "၆၀ MB ထက် မကြီးရ")
    d = os.path.join(DATA, "aud"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{jid}.m4a"), "wb") as f:
        f.write(raw)
    return {"ok": True, "bytes": len(raw)}


@app.get("/api/jobs/{jid}/audio")
def job_audio(jid: str, authorization: str = Header(None), t: str = ""):
    """Script Editor အတွက် အသံ proxy。 `?t=` နဲ့လည်း ရသည် (<audio> က header မပို့နိုင်၍)。"""
    auth(authorization or (f"Bearer {t}" if t else None), UTOKEN)
    mine(authorization, jid, t)
    p = os.path.join(DATA, "aud", f"{jid}.m4a")
    if not os.path.exists(p): raise HTTPException(404, "အသံ မရှိ")
    return FileResponse(p, media_type="audio/mp4")


@app.get("/api/jobs/{jid}/thumb")
def job_thumb(jid: str, authorization: str = Header(None), t: str = ""):
    """ပြီးသွားသော ဗီဒီယိုရဲ့ ပုံငယ် — disk မှာ cache လုပ်သည်。

    ⚠️ R2 mode မှာ ဖိုင်က server ပေါ် မရှိ ⇒ presigned URL ကို ffmpeg နဲ့
       တိုက်ရိုက် ဖတ်သည် (range request ဖြင့် အစပိုင်းလေးပဲ ဆွဲသည်)。
    ⚠️ ပထမ frame ကို **မယူရ** — အများအားဖြင့် မှောင်နေ ဒါမှမဟုတ် ဗလာ。
       ၁၅% နေရာက frame ကို ယူသည်。
    """
    auth(authorization or (f"Bearer {t}" if t else None), UTOKEN)
    cache = os.path.join(THUMB, f"{jid}.jpg")
    if os.path.exists(cache) and os.path.getsize(cache) > 0:
        return FileResponse(cache, media_type="image/jpeg")
    j = mine(authorization, jid, t)
    if j.get("status") != "done": raise HTTPException(404, "မရှိသေး")
    src = None
    if j.get("out_key") and ST.on():
        try: src = ST.get_url(j["out_key"], 600)
        except Exception: src = None
    if not src and j.get("out_path") and os.path.exists(j["out_path"]):
        src = j["out_path"]
    if not src: raise HTTPException(404, "ဖိုင် မရှိ")
    at = max(0.5, float(j.get("out_dur") or 4) * 0.15)
    import subprocess
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{at:.2f}", "-i", src,
                            "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "5",
                            "-y", cache], capture_output=True)
    except FileNotFoundError:
        # ⚠️ API image မှာ ffmpeg မပါ — worker က တင်ပေးမှ ရသည်。
        raise HTTPException(404, "ပုံငယ် မရှိသေး")
    if r.returncode or not os.path.exists(cache):
        raise HTTPException(500, "ပုံငယ် မထုတ်နိုင်: " + r.stderr.decode()[:120])
    return FileResponse(cache, media_type="image/jpeg")


# ══ ဘရန်း logo ═════════════════════════════════════════════
@app.post("/api/brands/{bid}/logo")
async def brand_logo_put(bid: str, file: UploadFile = File(...),
                         apply: int = 0, authorization: str = Header(None)):
    """logo တင်ခြင်း + အရောင် ထုတ်ခြင်း。

    `apply=1` ဆိုလျှင် ထုတ်လိုက်တဲ့ အရောင်ကို brand ထဲ **တန်းသွင်း**သည် —
    ထွက်လာမယ့် ဗီဒီယိုက သူ့ theme အတိုင်း ဖြစ်စေရန်。
    """
    auth(authorization, UTOKEN)
    if not db.one("SELECT id FROM brands WHERE id=?", bid):
        raise HTTPException(404, "ဘရန်း မတွေ့")
    raw = await file.read()
    if len(raw) > 4 * 1024 * 1024: raise HTTPException(413, "၄ MB ထက် မကြီးရ")
    p = os.path.join(LOGO, f"{bid}.png")
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(raw)).convert("RGBA")
        im.thumbnail((1024, 1024))
        im.save(p)
    except Exception as e:
        raise HTTPException(400, f"ပုံ ဖတ်မရ: {e}")
    cols, info = [], {}
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "core"))
        import palette as PA
        cols, info = PA.extract(p)
    except Exception as e:
        info = {"note": f"အရောင် မထုတ်နိုင်: {e}"}
    db.run("UPDATE brands SET logo=? WHERE id=?", f"{bid}.png", bid)
    if cols and apply:
        db.run("UPDATE brands SET colors=? WHERE id=?", json.dumps(cols), bid)
    return {"ok": True, "colors": cols, "info": info, "applied": bool(cols and apply)}


@app.get("/api/brands/{bid}/logo")
def brand_logo_get(bid: str, authorization: str = Header(None), t: str = ""):
    # ⚠️ worker ကလည်း ဆွဲသည် (ဗီဒီယိုထဲ ထည့်ရန်) ⇒ token နှစ်မျိုးလုံး လက်ခံ。
    h = authorization or (f"Bearer {t}" if t else None)
    tok = (h or "").replace("Bearer ", "")
    if tok not in (UTOKEN, WTOKEN): raise HTTPException(401, "unauthorised")
    p = os.path.join(LOGO, f"{bid}.png")
    if not os.path.exists(p): raise HTTPException(404, "logo မရှိ")
    return FileResponse(p, media_type="image/png")


@app.delete("/api/brands/{bid}/logo")
def brand_logo_del(bid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    p = os.path.join(LOGO, f"{bid}.png")
    if os.path.exists(p): os.unlink(p)
    db.run("UPDATE brands SET logo=NULL WHERE id=?", bid)
    return {"ok": True}


# ══ ဖောင့် — AI ရွေးပေးခြင်း ═════════════════════════════════
@app.post("/api/fonts/suggest")
async def font_suggest(req: Request, authorization: str = Header(None)):
    """အကြောင်းအရာ/ဘရန်းကို ကြည့်ပြီး ဖောင့် ရွေးပေးသည်。

    ⚠️ မော်ဒယ် ပြန်ပေးတဲ့ id ကို **စာရင်းနဲ့ တိုက်စစ်ရမည်** — ဖန်လာသော
       ဖောင့်နာမည်ကို ယုံပြီး သုံးလျှင် render မှာ ဖောင့် တိတ်တဆိတ်
       အစားထိုးခံရသည် (ယခင် ဖြစ်ဖူးသည်)。
    """
    auth(authorization, UTOKEN)
    b = await req.json()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "core"))
    lst = FONTS
    ids = {f["id"] for f in lst}
    want = (b.get("note") or "").strip()
    style = b.get("style") or ""
    brand = b.get("brand") or ""
    menu = "\n".join(f'{f["id"]} — {f.get("look","")} · {f.get("good","")}' for f in lst)
    prompt = (
        "မြန်မာ ဗီဒီယို စာတန်းအတွက် ဖောင့် တစ်ခု ရွေးပေးပါ。\n\n"
        f"ပုံစံ: {style}\nဘရန်း: {brand}\nလိုချင်ချက်: {want or '(မပြောထား)'}\n\n"
        f"ရွေးစရာ (id — ပုံစံ · သင့်တော်ရာ):\n{menu}\n\n"
        'JSON သာ ပြန်ပါ: {"id":"<id>","why":"<မြန်မာလို တစ်ကြောင်း>"}')
    out = None
    try:
        import gemguard as G, urllib.request, re
        G.throttle()
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.3}}
        # ⚠️ model နာမည်ကို **hardcode မလုပ်ရ** — pipeline တစ်ခုလုံးက
        #    `IKKI_GEMINI_MODEL` ကို သုံးသည်。 မတူလျှင် တစ်နေရာပဲ 404 ဖြစ်နေမည်
        #    (တကယ် ဖြစ်ခဲ့ — "gemini-2.0-flash" က 404)。
        _mdl = os.environ.get("IKKI_GEMINI_MODEL", "gemini-3.1-flash-lite")
        r = urllib.request.Request(G.endpoint(_mdl),
                                   data=json.dumps(body).encode(),
                                   headers={"Content-Type": "application/json"},
                                   method="POST")
        with urllib.request.urlopen(r, timeout=30) as f:
            d = json.loads(f.read())
        txt = d["candidates"][0]["content"]["parts"][0]["text"]
        m = re.search(r"\{.*\}", txt, re.S)
        if m: out = json.loads(m.group(0))
    except Exception as e:
        return {"ok": False, "err": f"AI မရ: {e}"}
    if not out or out.get("id") not in ids:
        return {"ok": False, "err": "AI က စာရင်းထဲ မရှိသော ဖောင့် ပြန်ပေးသည်",
                "raw": (out or {}).get("id")}
    return {"ok": True, "id": out["id"], "why": out.get("why", "")}



# ══ ရုပ်ကြမ်း စာကြည့်တိုက် (ပုံ · ဗီဒီယို) ══════════════════
# ⚠️ စာကြည့်တိုက်က **Mac worker ပေါ်မှာ** ရှိသည် (Gemini နဲ့ tag တပ်ရ၍)。
#    ဒါကြောင့် API က ဖိုင်ကို ခဏ ကိုင်ထားပြီး worker က ဆွဲယူသည်。
@app.post("/api/broll")
async def broll_add(file: UploadFile = File(...), authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    raw = await file.read()
    if len(raw) > 60 * 1024 * 1024: raise HTTPException(413, "၆၀ MB ထက် မကြီးရ")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".m4v"):
        raise HTTPException(400, "ပုံ (jpg·png·webp) ဒါမှမဟုတ် ဗီဒီယို (mp4·mov) သာ")
    bid = db.nid("k_")
    with open(os.path.join(BROLLIN, bid + ext), "wb") as f: f.write(raw)
    db.run("INSERT INTO brollq(id,name,ext,status,acct,created) VALUES(?,?,?,'pending',?,?)",
           bid, (file.filename or "")[:80], ext, aid(authorization), time.time())
    return {"ok": True, "id": bid, "queued": True}


@app.get("/api/broll")
def broll_list(authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    return {"items": db.rows("SELECT * FROM brollq WHERE acct=? ORDER BY created DESC LIMIT 200",
                             aid(authorization))}


@app.delete("/api/broll/{bid}")
def broll_del(bid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    r = db.one("SELECT * FROM brollq WHERE id=?", bid)
    if r:
        p = os.path.join(BROLLIN, bid + (r.get("ext") or ""))
        if os.path.exists(p):
            try: os.unlink(p)
            except OSError: pass
    db.run("DELETE FROM brollq WHERE id=?", bid)
    return {"ok": True}


@app.get("/api/w/broll/pending")
def w_broll_pending(authorization: str = Header(None)):
    auth(authorization, WTOKEN)
    return {"items": db.rows("SELECT * FROM brollq WHERE status='pending' LIMIT 20")}


@app.get("/api/w/broll/{bid}")
def w_broll_file(bid: str, authorization: str = Header(None)):
    auth(authorization, WTOKEN)
    r = db.one("SELECT * FROM brollq WHERE id=?", bid)
    if not r: raise HTTPException(404, "မရှိ")
    p = os.path.join(BROLLIN, bid + (r.get("ext") or ""))
    if not os.path.exists(p): raise HTTPException(404, "ဖိုင် မရှိ")
    return FileResponse(p)


@app.post("/api/w/broll/{bid}/done")
async def w_broll_done(bid: str, req: Request, authorization: str = Header(None)):
    auth(authorization, WTOKEN)
    b = await req.json()
    db.run("UPDATE brollq SET status=?, tags=?, note=? WHERE id=?",
           ("indexed" if b.get("ok") else "failed"),
           json.dumps(b.get("tags") or [], ensure_ascii=False), (b.get("note") or "")[:200], bid)
    # ⚠️ index ပြီးရင် ခဏသိမ်းထားတဲ့ ဖိုင်ကို **ဖျက်ရမည်** — worker ရဲ့
    #    စာကြည့်တိုက်ထဲ ကူးပြီးသား၊ VPS မှာ ထားလျှင် disk အလကား ကုန်သည်。
    r = db.one("SELECT ext FROM brollq WHERE id=?", bid)
    p = os.path.join(BROLLIN, bid + ((r or {}).get("ext") or ""))
    if os.path.exists(p):
        try: os.unlink(p)
        except OSError: pass
    return {"ok": True}


@app.get("/api/health")
def health():
    r = db.one("SELECT v FROM settings WHERE k='worker_seen'")
    seen = float(r["v"]) if r and r["v"] else 0.0
    ago = (time.time() - seen) if seen else None
    q = db.one("SELECT COUNT(*) n FROM jobs WHERE status='queued'")
    return {"ok": True, "t": time.time(),
            "worker": (ago is not None and ago < 60),
            "worker_ago": round(ago, 1) if ago is not None else None,
            "queued": (q or {}).get("n", 0)}

# ⚠️ index.html ကို cache မထားစေရ — ထားလျှင် deploy လုပ်လည်း သုံးစွဲသူက
#    **အရင် CSS/JS ကို ဆက်သုံးနေသည်** (တကယ် ဖြစ်ခဲ့ — ဖုန်း အကွက် ပြင်ပြီးမှ
#    browser က အရင်ဟာ ပြနေခဲ့သည်)。 asset တွေက ?v= ပါသဖြင့် cache ရသည်。
@app.middleware("http")
async def nocache_html(request, call_next):
    r = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith(".html"):
        r.headers["Cache-Control"] = "no-store, must-revalidate"
    elif ("?v=" in str(request.url)) or path.endswith((".css",".js")):
        r.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return r

@app.get("/api/script/{jid}")
def script_get(jid: str, authorization: str = Header(None)):
    auth(authorization, UTOKEN)
    j = mine(authorization, jid)
    # ⚠️ **အပြည့် စာတမ်းကို ပြရမည်** — `segs` က အရင် ချန်ခဲ့သော ဝါကျများသာ
    #    ဖြစ်သဖြင့် ပြန်ဖွင့်တဲ့အခါ အရင် ဖျက်ထားတာတွေ မမြင်ရဘဲ ပြန်ပြင်လျှင်
    #    ပြန်ပါလာခဲ့သည် (Zin ၂၀၂၆-၀၉-၂၀)。
    try: segs = json.loads(j.get("segs_all") or j.get("segs") or "[]")
    except Exception: segs = []
    if not segs: raise HTTPException(400, "စာသား မရှိ — ASR မပြီးသေး")
    try: plan = json.loads(j.get("plan") or "{}")
    except Exception: plan = {}
    sents, events = _script_of(segs, plan)
    # ⚠️ အရင် ဖျက်ခဲ့တာတွေကို **အနီ ကြိုရွေးထား** ⇒ သုံးစွဲသူက ဘာ ဖျက်ခဲ့လဲ
    #    မြင်ရပြီး ဆက်ပြင်လို့ ရသည် (ပြန်ပါလာမှာ မဟုတ်)。
    try: _kn = set(json.loads(j.get("keep_n") or "null") or [])
    except Exception: _kn = set()
    if _kn:
        for _s in sents:
            if _s["n"] not in _kn:
                _s["suggest"] = "delete"
                _s["prev_cut"] = True
    # ── ရေးထားသော script ရှိလျှင် ချိန်ညှိပြီး **အမှတ်အသား** ထည့် (ဖျက်ခြင်း မလုပ်) ──
    smark = {}
    try:
        over = json.loads(j.get("over") or "{}") or {}
    except Exception:
        over = {}
    stext = over.get("_script") or ""
    if stext:
        import script as _SC
        for o in _SC.align(stext, segs):
            if o["mark"]:
                sents[o["n"]-1]["script_mark"] = o["mark"]
                sents[o["n"]-1]["script_match"] = o["match"]
                smark[o["mark"]] = smark.get(o["mark"], 0) + 1
    ng = len({s["group_id"] for s in sents if s["group_id"]})
    return {"job": jid, "title": j.get("title"), "src_dur": j.get("src_dur"),
            # ⚠️ ထုတ်ပြီးသား job မှာ **ခန့်မှန်းချက် မပြရ** — segs က ချန်ထားပြီးသား
            #    ဝါကျများသာ ဖြစ်ပြီး `src_dur` က မူရင်း အတိုင်း ကျန်နေသဖြင့်
            #    တွက်ချက်ချက်က မှားသည် (Zin ၂၀၂၆-၀၉-၁၉: 「၆:၀၇ → ၆:၀၇ ဘာလို့လဲ」
            #    — တကယ့် ရလဒ်က ၂:၂၀)。 ⇒ **တိုင်းထားသော ထွက်ရှည်** ကို ပေးသည်。
            "out_dur": j.get("out_dur"),
            # ⚠️ `status` — `review` ဖြစ်လျှင် Script Editor က **approve** လမ်းကြောင်း
            #    သုံးရမည် (job တစ်ခုတည်း · render တစ်ခါပဲ)。 `done` ဆိုမှ reedit。
            "status": j.get("status"),
            "script": (dict(chars=len(stext), **smark) if stext else None),
            "sentences": sents, "events": events,
            "stat": {"n": len(sents), "groups": ng,
                     "silence": len(events),
                     "repeat": sum(1 for s in sents if s["cat"] == "repeat"),
                     "section": sum(1 for s in sents if s["cat"] == "section"),
                     "suggest_delete": sum(1 for s in sents if s["suggest"] == "delete")}}


@app.post("/api/script/{jid}/render")
async def script_render(jid: str, req: Request, authorization: str = Header(None)):
    """Script Editor → ဗီဒီယို ထုတ်ခြင်း。  body: `{"keep": [ဝါကျ နံပါတ် …]}`

    ⚠️ ဖြတ်နည်း · ဘောင်စစ်ခြင်း · quota · `_drop` တွက်ခြင်း — အားလုံး
       **`job_reedit()` ကိုပဲ ပြန်သုံး**သည် (code ထပ်မရေး) ⇒ လမ်းကြောင်း ၂ ခု
       ကွဲသွားပြီး ဖြတ်ချက် မတူဖြစ်စရာ မရှိ。
    ⚠️ transcript စာသား **မပြင်ရ** (R7) — မူရင်း စာသားကိုပဲ ပြန်ပို့သည်;
       `fix` မထည့်ပါ。
    ⚠️ F2 = ၀ ကို **engine က ထိန်း**သည် (`CUT.subtract` က ဖြတ်မှတ်ကို
       တိတ်ဆိတ်မှုဆီ ကပ်ပေးသည်) — ဤနေရာမှာ ဘာမှ မထိပါ。
    """
    auth(authorization, UTOKEN)
    b = await req.json()
    keep = b.get("keep")
    if not isinstance(keep, list) or not keep:
        raise HTTPException(400, "ချန်မည့် ဝါကျ မပါ")
    j = mine(authorization, jid)
    # ⚠️ editor က `segs_all` (အပြည့်) ကို ပြသဖြင့် နံပါတ်လည်း အဲဒီအတိုင်း
    try: segs = json.loads(j.get("segs_all") or j.get("segs") or "[]")
    except Exception: segs = []
    if not segs: raise HTTPException(400, "စာသား မရှိ — ASR မပြီးသေး")
    try: ks = sorted({int(n) for n in keep})
    except Exception: raise HTTPException(400, "ဝါကျ နံပါတ် မှားနေသည်")
    if not ks or ks[0] < 1 or ks[-1] > len(segs):
        raise HTTPException(400, f"ဝါကျ နံပါတ် ဘောင်ပြင် ({len(segs)} ကြောင်းသာ ရှိသည်)")
    over = dict(b.get("over") or {})
    ds = [[float(a), float(bb)] for a, bb in (b.get("drop_spans") or [])
          if float(bb) - float(a) > 0.02]
    if ds: over["_drop_exact"] = (over.get("_drop_exact") or []) + ds
    payload = dict(segs=[dict(i=n - 1, text=segs[n - 1].get("text") or "") for n in ks],
                   over=over, font=b.get("font"), cap=b.get("cap"))

    class _Shim:                       # `job_reedit` က `await req.json()` ခေါ်သည်
        async def json(self): return payload

    r = await job_reedit(jid, _Shim(), authorization)
    r["kept_n"] = ks
    r["dropped_n"] = [n for n in range(1, len(segs) + 1) if n not in set(ks)]
    return r


@app.post("/api/script/{jid}/source")
async def script_source(jid: str, req: Request, authorization: str = Header(None)):
    """ရေးထားသော script တင်ခြင်း — `{"text": "…"}` (txt/docx ကို UI က စာသား ပြောင်းပြီး ပို့)。

    ⚠️ **ဖျက်ခြင်း မလုပ်ပါ** — Script Editor မှာ **အနီ ပြရုံ**、
       သုံးစွဲသူ အတည်ပြုမှသာ ဖျက်သည် (Zin ၂၀၂၆-၀၉-၁၉)。
    """
    auth(authorization, UTOKEN)
    j = mine(authorization, jid)
    b = await req.json()
    t = (b.get("text") or "").strip()
    # ⚠️ `.docx` က zip ⇒ browser မှာ ဖွင့်၍ မရ ⇒ base64 နဲ့ ပို့ပြီး **server မှာ** ဖတ်သည်
    if t.startswith("__DOCX__"):
        import base64, tempfile
        import script as _SC
        try:
            raw = base64.b64decode(t[8:])
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
                f.write(raw); tmp = f.name
            t = _SC.read(tmp).strip()
            os.unlink(tmp)
        except Exception as e:
            raise HTTPException(400, f".docx ဖတ်၍ မရပါ: {type(e).__name__}")
    if len(t) > 400000: raise HTTPException(400, "script ရှည်လွန်းသည်")
    try: over = json.loads(j.get("over") or "{}") or {}
    except Exception: over = {}
    if t: over["_script"] = t
    else: over.pop("_script", None)
    db.run("UPDATE jobs SET over=? WHERE id=?",
           json.dumps(over, ensure_ascii=False) if over else None, jid)
    return {"ok": True, "chars": len(t)}


# ⚠️ **Script Editor route များကို `app.mount("/")` ရှေ့မှာ ထားရမည်** —
#    Starlette က route ကို **အစီအစဉ်အလိုက်** တိုက်သဖြင့် mount("/") နောက်မှာ
#    ရှိသော route အားလုံး **မရောက်တော့ဘဲ 404** ဖြစ်သည် (၂၀၂၆-၀၉-၁၉ တကယ် ဖြစ်ခဲ့:
#    `GET /api/script/{jid}` က ၄ ကြိမ်လုံး 404 — 「transcript မပေါ်ဘူး」)。
# ⚠️ `script.html` ကို **cache မထားရ** — `?v=` မပါသဖြင့် browser က အဟောင်းကို
#    ဆက်ကိုင်ထားပြီး ပြင်ချက်တွေ မရောက်ခဲ့ (၂၀၂၆-၀၉-၁၉: 「Edit နှိပ်လို့ မရ」 —
#    တကယ်က ပြင်ပြီးသား ဖြစ်ပြီး browser မှာ အဟောင်း ကျန်နေခြင်း)。
#    ⇒ mount ရှေ့မှာ သီးသန့် route ထား · no-store header တပ်。
@app.get("/script.html")
def script_page():
    from fastapi.responses import FileResponse as _FR
    return _FR(os.path.join(WEB, "script.html"), media_type="text/html",
               headers={"Cache-Control": "no-store, must-revalidate", "Pragma": "no-cache"})


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")


# ══ Script Editor (၂၀၂၆-၀၉-၁၇ Zin) ═══════════════════════════
# ⚠️ **engine မထိ** — ဤအလွှာက job ရဲ့ `segs` + `plan` ကို ဖတ်ပြီး
#    UI အတွက် ပုံစံ ပြောင်းရုံသာ。 ဖြတ်စက် · ASR · detector · render
#    အားလုံး အလုပ်ဖြစ်နေပြီးဖြစ်၍ ဘာမှ မပြင်ရ。
# ⚠️ R7 — `text` ကို **စာလုံး တစ်လုံးမှ မပြင်ရ · မဖြည့်ရ**。
#
# အမျိုးအစား —
#   silence  🔵 အသံတိတ် (ဖြတ်ပြီးသား)        suggest=delete
#   repeat   🟡 ဝါကျ ၁–၂ ခု ထပ်               suggest=delete
#   section  🔴 အုပ်စုတစ်ခုမှာ ဖျက်စရာ ≥၃ ခု   suggest=**keep** (ကြိုမဖျက်ရ)
#   noise    🟢 — **ယခု မဆောက်ရ**
SECTION_MIN = 3        # ⚠️ ဤကိန်း ပြောင်းလိုလျှင် Zin ကို အရင် မေးရမည်


def _script_of(segs, plan):
    """(sentences, events) — UI အတွက် ပုံစံ。 plan မရှိလည်း အလုပ်ဖြစ်ရမည်。"""
    sents = [dict(n=i + 1, start=round(float(s.get("start") or 0), 2),
                  end=round(float(s.get("end") or 0), 2),
                  text=s.get("text") or "", suggest="keep", cat=None, group_id=None)
             for i, s in enumerate(segs or [])]
    plan = plan or {}
    # ⚠️ `parts` — ဝါကျ အတွင်း ဖြတ်လို့ရသော အပိုင်းများ (တိတ်ဆိတ်မှု အလယ်မှာ ခွဲ)。
    #    ရှိမှ ပြရမည် — မရှိလျှင် ထိုဝါကျကို သပ်သပ် ခွဲ၍ မရ (ရိုးသားစွာ ပြောရန်)。
    for k, pts in (plan.get("splits") or {}).items():
        try: i = int(k)
        except Exception: continue
        if not (0 <= i < len(sents)) or not pts: continue
        a, b = sents[i]["start"], sents[i]["end"]
        cuts = [float(x) for x in pts if a < float(x) < b]
        if not cuts: continue
        edges = [a] + sorted(cuts) + [b]
        parts = [[round(edges[j], 2), round(edges[j+1], 2)] for j in range(len(edges)-1)]
        # ⚠️ စာသားကို အပိုင်းအလိုက် ခွဲပေးရန် ASR ရဲ့ `words` ကို သုံးသည် —
        #    **ပြဖို့သာ**。 ဖြတ်မှတ်က တိတ်ဆိတ်မှု အလယ်မှာသာ (F2 = ၀ အာမခံ) ·
        #    စကားလုံး အချိန်မှတ်ကို ဖြတ်ဖို့ **ဘယ်တော့မှ မသုံးရ** (၂၀၂၆-၀၉-၁၈ တိုင်းချက်)。
        ws = (segs[i] or {}).get("words") or []
        for k, (pa, pb) in enumerate(parts):
            txt = " ".join((w.get("w") or "") for w in ws
                           if pa <= (float(w.get("s", 0)) + float(w.get("e", 0)))/2.0 < pb)
            parts[k] = dict(start=pa, end=pb, text=txt.strip())
        sents[i]["parts"] = parts
    # ── ဟန်ပျက် — 「ကင်မရာရှေ့ စကားပြောနေဟန် မဟုတ်」 ──
    # ⚠️ **ကိုယ်တိုင် မဖျက်ရ** (Zin: 「user အတည်ပြုမှ ဖျက်ပေး · script editor မှာပဲ
    #    အနီပြထား」) ⇒ `suggest="delete"` (ကြိုရွေးထား · **user ပြန်ဖြုတ်လို့ရ**)
    #    + အကြောင်းရင်း。 render မလုပ်မချင်း ဘာမှ မဖျက်ရသေးပါ。
    for k, why in (plan.get("pose") or {}).items():
        try: i = int(k) - 1
        except Exception: continue
        if 0 <= i < len(sents):
            sents[i]["suggest"] = "delete"
            sents[i]["pose"] = why or "ဟန်ပျက်"

    # ── ① တိတ်ဆိတ်မှု — **`plan["spans"]` (ချန်မည့် အပိုင်း) ကြားက ကွက်လပ်** ──
    # ⚠️ `plan["cuts"]` က **ကိန်း** (အရေအတွက်) ဖြစ်သည် — စာရင်း **မဟုတ်**。
    #    ၂၀၂၆-၀၉-၁၉: စာရင်း ထင်ပြီး loop ပတ်မိ၍ `TypeError: 'int' object is not
    #    iterable` ⇒ 500 ⇒ 「transcript မပေါ်ဘူး」 ဖြစ်ခဲ့သည်。
    events = []
    spans = plan.get("spans") or []
    if spans:
        prev = None
        for sp_ in spans:
            try: a0, b0 = float(sp_[0]), float(sp_[1])
            except Exception: continue
            if prev is not None and a0 - prev > 0.02:
                events.append(dict(type="silence", start=round(prev, 2), end=round(a0, 2),
                                   dur=round(a0 - prev, 2)))
            prev = b0
        # ဖိုင် အစ ကွက်လပ်
        try:
            f0 = float(spans[0][0])
            if f0 > 0.02:
                events.insert(0, dict(type="silence", start=0.0, end=round(f0, 2),
                                      dur=round(f0, 2)))
        except Exception: pass
    elif isinstance(plan.get("cuts"), list):        # ယခင် ပုံစံ (backward compatible)
        for c in plan["cuts"]:
            if not isinstance(c, dict): continue
            if (c.get("kind") or "silence") != "silence": continue
            a, b = float(c.get("at") or 0), float(c.get("to") or 0)
            if b - a <= 0: continue
            events.append(dict(type="silence", start=round(a, 2), end=round(b, 2),
                               dur=round(b - a, 2)))
    # ── ①b စကား မဟုတ်သော အသံ — ချောင်းဆိုး · ခေါက်သံ · အသက်ရှူ ──
    for a, b, d in (plan.get("sounds") or []):
        a, b = float(a), float(b)
        if b - a <= 0: continue
        events.append(dict(type="sound", start=round(a, 2), end=round(b, 2),
                           dur=round(b - a, 2), db=d))
    events.sort(key=lambda e: e["start"])
    # ── ② ပြန်စ အုပ်စု — `plan.clusters` ──
    for cl in (plan.get("clusters") or []):
        takes = cl.get("takes") or []
        idx = [int(t.get("i") or 0) for t in takes if t.get("i")]
        idx = [i for i in idx if 1 <= i <= len(sents)]
        if len(idx) < 2: continue
        # ⚠️ ဘယ် take ချန်မလဲ — **ယာယီ** စည်းမျဉ်း: အရှည်ဆုံး (စာလုံး အများဆုံး)。
        #    စက်က မဆုံးဖြတ်ရ ⇒ ဤသည် **အကြံပြုချက်** သာ · လူက ပြင်နိုင်သည်。
        keep_n = max(idx, key=lambda i: len(sents[i - 1]["text"]))
        drop = [i for i in idx if i != keep_n]
        cat = "section" if len(drop) >= SECTION_MIN else "repeat"
        for i in idx:
            s = sents[i - 1]
            s["group_id"] = cl.get("id")
            s["cat"] = cat
            if i == keep_n:
                s["suggest"] = "keep"
            else:
                # 🔴 က **ကြိုမဖျက်ရ** — လူ ကြည့်ပြီးမှ
                s["suggest"] = "keep" if cat == "section" else "delete"
    return sents, events
