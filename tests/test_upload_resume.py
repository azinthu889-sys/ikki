# -*- coding: utf-8 -*-
"""Multipart resume — bytes are recovered from R2, never from a progress bar."""
import asyncio, os, sys, tempfile, time

T = tempfile.mkdtemp(prefix="ikki_resume_")
os.environ["IKKI_DATA"] = T
os.environ["IKKI_DB"] = os.path.join(T, "test.db")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))
sys.path.insert(0, os.path.join(ROOT, "core"))
try:
    import fastapi  # noqa: F401
except ImportError:
    print("  ⊘ fastapi မရှိ — ကျော်သည်")
    raise SystemExit(0)
import main as M, db, store
from fastapi import HTTPException

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond:
        OK += 1; print("  ✓", name)
    else:
        FAIL += 1; print("  ✗", name, extra)

def code(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except HTTPException as e:
        return e.status_code
    return None

# R2 returns quoted ETags. Preserve that exact value for CompleteMultipartUpload.
old_call = store.call
store.call = lambda *a, **kw: (200, {}, b'''<ListPartsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Part><PartNumber>1</PartNumber><ETag>"aaa"</ETag><Size>8</Size></Part><Part><PartNumber>2</PartNumber><ETag>"bbb"</ETag><Size>4</Size></Part></ListPartsResult>''')
p = store.mpu_list_parts("uploads/u.mp4", "mpu")
store.call = old_call
ck("R2 ListParts parses parts", [(x["n"], x["size"]) for x in p] == [(1, 8), (2, 4)], p)
ck("ETag quotes preserved", p[0]["etag"] == '"aaa"', p)

class FakeStore:
    @staticmethod
    def on(): return True
    @staticmethod
    def mpu_create(key, content_type): return "mpu_new"
    @staticmethod
    def mpu_list_parts(key, mpu):
        return [{"n": 1, "etag": '"one"', "size": 32},
                {"n": 2, "etag": '"two"', "size": 16}]

M.ST = FakeStore
tok = db.one("SELECT token FROM accounts WHERE id='a_default'")["token"]
H = "Bearer " + tok
db.run("INSERT INTO uploads(id,name,size,received,path,done,created,key,mpu,acct) "
       "VALUES(?,?,?,?,?,?,?,?,?,?)", "u_resume", "same.mp4", 96, 0, "", 0,
       time.time(), "uploads/u_resume.mp4", "mpu_resume", "a_default")
r = M.up_resumable("same.mp4", 96, authorization=H)["upload"]
ck("same account finds interrupted upload", r["upload_id"] == "u_resume", r)
ck("only R2-confirmed bytes counted", r["received"] == 48, r)
ck("part list returned to browser", len(r["parts"]) == 2, r)
ck("DB receives measured count", db.one("SELECT received FROM uploads WHERE id=?", "u_resume")["received"] == 48)

class Req:
    async def json(self): return {"name": "Other"}

other = asyncio.get_event_loop().run_until_complete(M.account_new(Req(), authorization=H))
ck("other account cannot resume", code(M.up_resume, "u_resume", authorization="Bearer "+other["token"]) == 404)
ck("other account cannot get presigned parts", code(M.up_parts, "u_resume", authorization="Bearer "+other["token"]) == 404)

# A Mac worker can index its own absolute path while the production renderer
# runs on the VPS.  R2 must win over that tempting-but-unreachable `have`
# shortcut, otherwise the upload is falsely marked complete and fails later.
class InitReq:
    async def json(self): return {"name": "camera.mp4", "size": 1234}
M._WIDX.clear()
M._WIDX[("camera.mp4", 1234)] = "/Users/editor/Downloads/camera.mp4"
M._WIDX_AT[0] = time.time()
created = asyncio.get_event_loop().run_until_complete(M.up_init(InitReq(), authorization=H))
new_u = db.one("SELECT * FROM uploads WHERE id=?", created["upload_id"])
ck("R2 enabled ⇒ Mac worker path ကို မသိမ်း", created["mode"] == "r2" and
   new_u["done"] == 0 and not new_u.get("local") and bool(new_u.get("key")), created)

# Local fallback bytes live in the API volume, not necessarily in the worker
# container.  The worker must receive a private HTTP file response, never an
# API-only `/data/...` pathname.
server_file = os.path.join(T, "server-source.mp4")
open(server_file, "wb").write(b"source")
db.run("INSERT INTO uploads(id,name,size,received,path,done,local,acct,created) "
       "VALUES(?,?,?,?,?,?,?,?,?)", "u_server", "server.mp4", 6, 6,
       server_file, 1, 1, "a_default", time.time())
db.run("INSERT INTO jobs(id,title,upload_id,brand_id,recipe,status,acct,created) "
       "VALUES(?,?,?,?,?,?,?,?)", "j_server", "server", "u_server", "ikki",
       "talking-head", "queued", "a_default", time.time())
src_response = M.w_src("j_server", authorization="Bearer " + M.WTOKEN)
ck("API-volume source ⇒ private file stream", type(src_response).__name__ == "FileResponse" and
   getattr(src_response, "path", None) == server_file, type(src_response).__name__)
db.run("UPDATE uploads SET path=? WHERE id=?", "/Users/editor/Downloads/missing.mp4", "u_server")
ck("မမြင်နိုင်သော Mac path ⇒ 404 (false success မဟုတ်)",
   code(M.w_src, "j_server", authorization="Bearer " + M.WTOKEN) == 404)

print("\n  ⇒ အောင် %d · ကျ %d" % (OK, FAIL))
raise SystemExit(1 if FAIL else 0)
