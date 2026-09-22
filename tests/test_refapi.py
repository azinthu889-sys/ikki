# -*- coding: utf-8 -*-
"""Reference Style DNA + recorder အသံ — **API အဆင့်**。

⚠️ account အလိုက် သီးသန့် — သူတစ်ပါးရဲ့ reference မမြင်ရ · မဖျက်ရ · မသုံးရ。
⚠️ **တိတ်တဆိတ် မဖွင့်ရ** — `apply` ခေါ်မှ job ထဲ ဝင်သည်。
⚠️ ဖျက်လျှင် **media ပါ ဖျက်ရမည်** (profile ပဲ ဖျက်လျှင် 「ဖျက်ပြီး」မှားရာ)。
⚠️ သီးသန့် DB/DATA နဲ့ ပြေးရမည်。
"""
import os, sys, tempfile, json

_T = tempfile.mkdtemp(prefix="ikki_ref_")
os.environ["IKKI_DATA"] = _T
os.environ["IKKI_DB"] = os.path.join(_T, "t.db")

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "api"))
sys.path.insert(0, os.path.join(_R, "core"))
try:
    import fastapi  # noqa: F401
except ImportError:
    print("  ⊘ fastapi မရှိ — ကျော်သည် (venv နဲ့ ပြေးပါ)"); sys.exit(0)
import time, asyncio
import main as M, db
from fastapi import HTTPException

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

def raises(fn, *a, **k):
    try: fn(*a, **k); return None
    except HTTPException as e: return e.status_code
    except Exception as e: return type(e).__name__

class Req:
    def __init__(self, d): self._d = d
    async def json(self): return self._d

def run(c): return asyncio.get_event_loop().run_until_complete(c)

dflt = (db.one("SELECT token FROM accounts WHERE id='a_default'") or {})["token"]
H = "Bearer " + dflt
W = "Bearer " + M.WTOKEN
a2 = run(M.account_new(Req({"name": "Other"}), authorization=H))
H2 = "Bearer " + a2["token"]

# ── upload row (ဖိုင် တကယ် ရှိစေရန်) ──
UP = "u_ref1"
_f = os.path.join(_T, "ref.mp4"); open(_f, "wb").write(b"\x00" * 2048)
db.run("INSERT INTO uploads(id,name,size,received,done,path,created) "
       "VALUES(?,?,?,?,?,?,?)", UP, "ref.mp4", 2048, 2048, 1, _f, time.time())

print("── ① ဆောက် · စာရင်း · account ခွဲ ──")
r = run(M.ref_new(Req({"upload_id": UP, "name": "sample"}), authorization=H))
RID = r["ref_id"]
ck("status = queued", r["status"] == "queued")
ck("ကိုယ်ပိုင် စာရင်းမှာ ပေါ်",
   RID in [x["id"] for x in M.ref_list(authorization=H)["refs"]])
ck("အခြား account မှာ **မပေါ်**",
   RID not in [x["id"] for x in M.ref_list(authorization=H2)["refs"]])
ck("အခြား account ဖတ် ⇒ 404", raises(M.ref_get, RID, authorization=H2) == 404)
ck("အခြား account ဖျက် ⇒ 404", raises(M.ref_del, RID, authorization=H2) == 404)
ck("upload မရှိ ⇒ 400",
   raises(run, M.ref_new(Req({"upload_id": "nope"}), authorization=H)) == 400)

print("\n── ② အပိုင်း ကန့်သတ်ချက် ──")
ck("၁၅s အောက် ⇒ 400",
   raises(run, M.ref_new(Req({"upload_id": UP, "range": [0, 9]}),
                         authorization=H)) == 400)
ck("၃ မိနစ် ထက် ⇒ 400",
   raises(run, M.ref_new(Req({"upload_id": UP, "range": [0, 400]}),
                         authorization=H)) == 400)
_ok = run(M.ref_new(Req({"upload_id": UP, "range": [10, 90]}), authorization=H))
ck("၈၀s အပိုင်း ⇒ လက်ခံ", bool(_ok.get("ref_id")))
db.run("DELETE FROM refs WHERE id=?", _ok["ref_id"])

print("\n── ③ worker လမ်းကြောင်း ──")
c = run(M.w_refclaim(Req({}), authorization=W))
ck("claim ရ", (c.get("ref") or {}).get("id") == RID, c)
ck("running ဖြစ်ပြီး",
   db.one("SELECT status FROM refs WHERE id=?", RID)["status"] == "running")
ck("ထပ် claim ⇒ မရ", run(M.w_refclaim(Req({}), authorization=W))["ref"] is None)
ck("user token နဲ့ claim ⇒ 401",
   raises(run, M.w_refclaim(Req({}), authorization=H)) == 401)
DNA = dict(pace="fast", cut="tight", captions="frequent", motion="dynamic",
           broll="unknown", audio="standard", music="unknown", aspect="9:16",
           confidence=0.83, dur=80.0,
           _conf={"pace": .9, "cut": .9, "captions": .8, "motion": .7, "audio": .8})
run(M.w_ref_result(RID, Req({"meas": {"probe": {"aspect": "9:16"}}, "dna": DNA,
                             "compat": ["adapted", "အချိုး မတူ", "aspect differs"]}),
                   authorization=W))
g = M.ref_get(RID, authorization=H)
ck("status = done", g["status"] == "done", g["status"])
ck("dna ပါလာ", (g.get("dna") or {}).get("pace") == "fast")
ck("compat ပါလာ", (g.get("compat") or [None])[0] == "adapted")
ck("conf မှတ်ပြီး", abs((g.get("conf") or 0) - 0.83) < 0.01)
ck("meas က ပုံမှန် မပါ (label သာ)", "meas" not in g)
ck("full=1 ဆို meas ပါ", "meas" in M.ref_get(RID, full=1, authorization=H))
ck("dna မပါ ⇒ 400",
   raises(run, M.w_ref_result(RID, Req({}), authorization=W)) == 400)

print("\n── ④ job ဆီ apply — **ခေါ်မှ** သက်ဝင် ──")
JID = "j_reftest"
db.run("INSERT INTO jobs(id,title,upload_id,brand_id,recipe,status,stage,created) "
       "VALUES(?,?,?,?,?,?,?,?)", JID, "t", UP, "ikki", "knowledge",
       "review", 2, time.time())
db.run("UPDATE jobs SET acct='a_default' WHERE id=?", JID)
_ov = json.loads(db.one("SELECT over FROM jobs WHERE id=?", JID)["over"] or "{}")
ck("မခေါ်ခင် _dna မရှိ", "_dna" not in _ov)
run(M.job_ref(JID, Req({"ref_id": RID}), authorization=H))
_ov = json.loads(db.one("SELECT over FROM jobs WHERE id=?", JID)["over"])
ck("_dna snapshot ဝင်ပြီး", (_ov.get("_dna") or {}).get("pace") == "fast")
ck("_ref version မှတ်ပြီး", (_ov.get("_ref") or {}).get("ver") == 1)
run(M.job_ref(JID, Req({"ref_id": None}), authorization=H))
_ov = json.loads(db.one("SELECT over FROM jobs WHERE id=?", JID)["over"] or "{}")
ck("ဖယ်လျှင် ပျောက်", "_dna" not in _ov and "_ref" not in _ov)
ck("အခြား account ⇒ 404",
   raises(run, M.job_ref(JID, Req({"ref_id": RID}), authorization=H2)) == 404)

print("\n── ⑤ unsuitable ⇒ သုံးလို့ မရ ──")
db.run("UPDATE refs SET compat=? WHERE id=?",
       json.dumps(["unsuitable", "တိုင်းချက် နည်း", "too few"]), RID)
ck("unsuitable ⇒ 400",
   raises(run, M.job_ref(JID, Req({"ref_id": RID}), authorization=H)) == 400)
db.run("UPDATE refs SET status='running' WHERE id=?", RID)
ck("မပြီးသေး ⇒ 409",
   raises(run, M.job_ref(JID, Req({"ref_id": RID}), authorization=H)) == 409)
db.run("UPDATE refs SET status='done',compat=NULL WHERE id=?", RID)

print("\n── ⑥ POST /api/jobs မှာ ref_id ──")
ck("မရှိသော ref ⇒ 404",
   raises(run, M.job_new(Req({"upload_id": UP, "recipe": "knowledge",
                              "brand_id": "ikki", "vfmt": "camera",
                              "ref_id": "r_nope"}), authorization=H)) == 404)

print("\n── ⑦ 「ငါ့ပုံစံအဖြစ် သိမ်း」— **server မှာ တကယ် သိမ်းရမည်** ──")
# ⚠️ local flag ပဲ ပြောင်းလျှင် refresh နဲ့ ပျောက်ပြီး 「သိမ်းပြီး」က လိမ်ရာ ကျသည်
ck("စတင် saved=False", M.ref_get(RID, authorization=H)["saved"] is False)
run(M.ref_save(RID, Req({"saved": True}), authorization=H))
ck("သိမ်းပြီး ⇒ DB မှာ ကျန်", M.ref_get(RID, authorization=H)["saved"] is True)
ck("စာရင်းမှာလည်း ပေါ်",
   [x for x in M.ref_list(authorization=H)["refs"] if x["id"] == RID][0]["saved"] is True)
run(M.ref_save(RID, Req({"saved": False}), authorization=H))
ck("ပြန်ဖြုတ်ရ", M.ref_get(RID, authorization=H)["saved"] is False)
ck("အခြား account ⇒ 404",
   raises(run, M.ref_save(RID, Req({"saved": True}), authorization=H2)) == 404)

print("\n── ⑧ ဖျက် — **media ပါ** ──")
ck("ဖိုင် ရှိနေဆဲ", os.path.exists(_f))
d = M.ref_del(RID, authorization=H)
ck("row ပျောက်", db.one("SELECT 1 FROM refs WHERE id=?", RID) is None)
ck("media ဖျက်ပြီး", d.get("media_deleted") is True and not os.path.exists(_f),
   (d, os.path.exists(_f)))
ck("upload row ပါ ပျောက်", db.one("SELECT 1 FROM uploads WHERE id=?", UP) is None)
ck("ထပ်ဖျက် ⇒ 404", raises(M.ref_del, RID, authorization=H) == 404)

print("\n── ⑨ recorder အသံ sync ရလဒ် ──")
JID2 = "j_syn"
db.run("INSERT INTO jobs(id,title,upload_id,recipe,status,stage,created) "
       "VALUES(?,?,?,?,?,?,?)", JID2, "t", "u_x", "knowledge", "running", 1, time.time())
db.run("UPDATE jobs SET acct='a_default' WHERE id=?", JID2)
run(M.w_sync(JID2, Req(dict(selected=True, used=False, offset=0.0, corr=0.21,
                            dur_video=120.0, dur_audio=180.0, dur_diff=60.0,
                            why="အသံ ၂ ခု မကိုက်", nonsense="ဖယ်ရမည်")),
             authorization=W))
sy = json.loads(db.one("SELECT sync FROM jobs WHERE id=?", JID2)["sync"])
ck("selected မှတ်ပြီး", sy.get("selected") is True)
ck("used=False (ကင်မရာ အသံ)", sy.get("used") is False)
ck("အကြောင်းရင်း ပါ", bool(sy.get("why")))
ck("ကြာချိန် နှိုင်းယှဉ်ချက် ပါ", sy.get("dur_diff") == 60.0)
ck("မသိသော field ဖယ်ပြီး", "nonsense" not in sy, sy)
ck("အချိန် မှတ်ပြီး", (sy.get("at") or 0) > 0)
ck("user token နဲ့ ⇒ 401",
   raises(run, M.w_sync(JID2, Req({"used": True}), authorization=H)) == 401)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
