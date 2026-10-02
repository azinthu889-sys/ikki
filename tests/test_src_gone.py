# -*- coding: utf-8 -*-
"""Source expiry (2026-10-02 audit): an upload whose stored source is gone must
be reported as src_gone, and re-edit / preview must be refused with 410 before
any minute or free preview is counted. The list must not hang on slow storage."""
import os, sys, tempfile, json, time, asyncio
_T = tempfile.mkdtemp(prefix="ikki_sg_")
os.environ["IKKI_DATA"] = _T; os.environ["IKKI_DB"] = os.path.join(_T, "t.db")
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "api")); sys.path.insert(0, os.path.join(_R, "core"))
try:
    import fastapi  # noqa: F401
except ImportError:
    print("  ⊘ fastapi မရှိ — ကျော်သည်"); sys.exit(0)
import main as M, db
from fastapi import HTTPException
OK = FAIL = 0
def ck(n, c, x=""):
    global OK, FAIL
    if c: OK += 1; print("  ✓", n)
    else: FAIL += 1; print("  ✗", n, x)
class Req:
    def __init__(s, d): s._d = d
    async def json(s): return s._d
run = lambda c: asyncio.get_event_loop().run_until_complete(c)
H = "Bearer " + db.one("SELECT token FROM accounts WHERE id='a_default'")["token"]

class FakeST:
    gone = {"uploads/u_gone.mp4"}; slow = {"uploads/u_slow.mp4"}
    @staticmethod
    def on(): return True
    @staticmethod
    def head(k):
        if k in FakeST.slow: time.sleep(10)
        return k not in FakeST.gone
M.ST = FakeST
segs = [{"text": "က", "start": 0.0, "end": 1.0}, {"text": "ခ", "start": 2.0, "end": 3.0}]
for u in ("u_ok", "u_gone", "u_slow"):
    db.run("INSERT INTO uploads(id,name,size,received,path,done,created,key,acct) VALUES(?,?,1,1,'',1,?,?,'a_default')",
           u, u, time.time(), f"uploads/{u}.mp4")
for j, u in (("j_ok", "u_ok"), ("j_gone", "u_gone"), ("j_slow", "u_slow")):
    db.run("INSERT INTO jobs(id,title,upload_id,brand_id,recipe,status,stage,segs,segs_all,src_dur,acct,created)"
           " VALUES(?,?,?,'ikki','headtop','done',7,?,?,5,'a_default',?)", j, j, u, json.dumps(segs), json.dumps(segs), time.time())

t0 = time.time(); L = {r["id"]: r["src_gone"] for r in M.job_list(authorization=H)["jobs"]}; dt = time.time() - t0
ck("list marks the gone source", L.get("j_gone") is True, L)
ck("list keeps the present source", L.get("j_ok") is False, L)
ck("slow storage = unknown, not gone", L.get("j_slow") is False, L)
ck("list answers within the deadline", dt < 5.0, f"{dt:.1f}s")
def code(c):
    try: run(c); return 200
    except HTTPException as e: return e.status_code
ck("re-edit refused 410 when the source is gone",
   code(M.job_reedit("j_gone", Req({"segs": [{"i": 0, "text": "က"}]}), authorization=H)) == 410)
ck("re-edit still allowed when the source is present",
   code(M.job_reedit("j_ok", Req({"segs": [{"i": 0, "text": "က"}]}), authorization=H)) == 200)
print(f"\n{OK} ✓ · {FAIL} ✗"); sys.stdout.flush(); os._exit(1 if FAIL else 0)
