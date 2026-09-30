# -*- coding: utf-8 -*-
"""Script Editor re-render (2026-10-01, Zin: "not the settings I chose in the UI").

1. the style/format/brand/font/caption picked in the UI reach the new job
   (before: always the parent's -- a 9:16 short came out 16:9 headtop)
2. `_drop_exact` (every by-ear cut: in-phrase trims, sound events, waveform
   cuts) and `_keep` survive into job.over (before: recipes.clean() dropped
   them, so no in-phrase cut ever reached the worker)
3. unknown style / format keep the parent's instead of breaking the render
"""
import os, sys, tempfile, json, asyncio
_T = tempfile.mkdtemp(prefix="ikki_sr_")
os.environ["IKKI_DATA"] = _T
os.environ["IKKI_DB"] = os.path.join(_T, "t.db")
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "api")); sys.path.insert(0, os.path.join(_R, "core"))
try:
    import fastapi  # noqa: F401
except ImportError:
    print("  ⊘ fastapi မရှိ — ကျော်သည်"); sys.exit(0)
import time
import main as M, db

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")
class Req:
    def __init__(self, d): self._d = d
    async def json(self): return self._d
def run(c): return asyncio.get_event_loop().run_until_complete(c)

H = "Bearer " + (db.one("SELECT token FROM accounts WHERE id='a_default'") or {})["token"]
segs = [{"text": f"ဝါကျ {i}", "start": 10.0 * i, "end": 10.0 * i + 5} for i in range(1, 5)]
db.run("INSERT INTO uploads(id,name,size,received,path,done,created,acct) VALUES('u1','a.mp4',10,10,'',1,?,'a_default')", time.time())
db.run("INSERT INTO jobs(id,title,upload_id,brand_id,recipe,font,fmt,cap,status,stage,segs,segs_all,src_dur,acct,created)"
       " VALUES('j_par','t','u1','ikki','headtop','','','','done',7,?,?,50,'a_default',?)",
       json.dumps(segs), json.dumps(segs), time.time())

def render(body):
    r = run(M.script_render("j_par", Req(body), authorization=H))
    return db.one("SELECT * FROM jobs WHERE id=?", r["job_id"])

j = render({"keep": [1, 2, 4], "drop_spans": [[12.1, 13.0], [41.0, 41.5]],
            "over": {"_keep": [[15.0, 16.0]]},
            "recipe": "short-916", "brand_id": "zjl", "fmt": "9:16",
            "font": "NotoSansMyanmar-Bold", "cap": "xl"})
ck("style from UI", j["recipe"] == "short-916", j["recipe"])
ck("format from UI", j["fmt"] == "9:16", j["fmt"])
ck("brand from UI", j["brand_id"] == "zjl", j["brand_id"])
ck("font from UI", j["font"] == "NotoSansMyanmar-Bold", j["font"])
ck("caption size from UI", j["cap"] == "xl", j["cap"])
ov = json.loads(j["over"] or "{}")
ck("in-phrase cuts survive (_drop_exact)", ov.get("_drop_exact") == [[12.1, 13.0], [41.0, 41.5]], ov)
ck("restored pauses survive (_keep)", ov.get("_keep") == [[15.0, 16.0]], ov)
ck("deleted sentence still dropped", any(abs(a - 30.0) < 1e-6 for a, _b in (ov.get("_drop") or [])), ov)

j2 = render({"keep": [1, 2, 3, 4], "recipe": "no-such-style", "fmt": "7:3"})
ck("unknown style keeps parent's", j2["recipe"] == "headtop", j2["recipe"])
ck("unknown format keeps parent's", (j2["fmt"] or "") == "", j2["fmt"])
j3 = render({"keep": [1, 2, 3, 4], "over": {"_drop_exact": [["x", 1], [5, 4], [1, 1.01]]}})
ck("junk cut pairs rejected", "_drop_exact" not in json.loads(j3["over"] or "{}"), j3["over"])

print(f"\n{OK} ✓ · {FAIL} ✗"); sys.exit(1 if FAIL else 0)
