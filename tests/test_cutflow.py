# -*- coding: utf-8 -*-
"""**clean-cut preview** — ဒုတိယ အတည်ပြုချက် လုပ်ငန်းစဉ် (၂၀၂၆-၀၉-၂၁ Zin)。

⚠️ ယခင်က စာတမ်း အတည်ပြုလိုက်တာနဲ့ `mode='go'` ⇒ ဂရပ်ဖစ် · တီးလုံး · SFX ·
   စာတန်း အားလုံး ပါသော နောက်ဆုံး ဗီဒီယို တန်းထွက်ခဲ့သည်。 ဖြတ်ချက် မှားလျှင်
   အဲဒီ အလုပ်အားလုံး အလဟဿ (render မိနစ်ပါ ကုန်)。
⚠️ ဖြတ်မှတ်ကို **အေးခဲ**ရမည် — နောက်ဆုံး render က ပြန်တွက်လျှင် သုံးစွဲသူ
   ကြည့်ပြီး အိုကေပေးခဲ့တာနဲ့ အနည်းငယ် လွဲပြီး ဂရပ်ဖစ် နေရာ ရွှေ့သွားမည်。
⚠️ **quota နှစ်ခါ မကောက်ရ** — proxy က ခေတ္တ ကြည့်ရန်သာ。

⚠️ သီးသန့် DB/DATA နဲ့ ပြေးရမည် (`api/main.py` က import ချိန် `/data` ဆောက်သည်)。
"""
import os, sys, tempfile, json

_T = tempfile.mkdtemp(prefix="ikki_cut_")
os.environ["IKKI_DATA"] = _T
os.environ["IKKI_DB"] = os.path.join(_T, "t.db")

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "api"))
sys.path.insert(0, os.path.join(_R, "core"))
try:
    import fastapi  # noqa: F401
except ImportError:
    print("  ⊘ fastapi မရှိ — ဤ test ကို ကျော်သည် (venv နဲ့ ပြေးပါ)")
    sys.exit(0)
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
a2 = run(M.account_new(Req({"name": "Other"}), authorization=H))
H2 = "Bearer " + a2["token"]

# ── review အဆင့်မှာ ရပ်နေသော job တစ်ခု ဆောက် ──
SEGS = [dict(text="မင်္ဂလာပါ", start=0.0, end=2.0),
        dict(text="ဒီနေ့ ပြောမယ်", start=2.4, end=5.0),
        dict(text="ဖျက်မယ့် ဝါကျ", start=5.4, end=7.0)]
JID = "j_cuttest"
def mkjob(status="review", mode="review"):
    db.run("DELETE FROM jobs WHERE id=?", JID)
    db.run("INSERT INTO jobs(id,title,upload_id,brand_id,recipe,status,stage,created) "
           "VALUES(?,?,?,?,?,?,?,?)", JID, "t", "u_x", "ikki", "knowledge",
           status, 2, time.time())
    db.run("UPDATE jobs SET acct=?,mode=?,segs=?,segs_all=?,src_dur=? WHERE id=?",
           "a_default", mode, json.dumps(SEGS, ensure_ascii=False),
           json.dumps(SEGS, ensure_ascii=False), 7.0, JID)
mkjob()
j = db.one("SELECT * FROM jobs WHERE id=?", JID)
ck("job ဆောက်ပြီး", j and j["status"] == "review")

print("\n── ① စာတမ်း အတည်ပြု ⇒ **ဖြတ်ချက် proxy** (render မဟုတ်) ──")
run(M.job_approve(JID, Req({"segs": [{"i": 0, "text": "မင်္ဂလာပါ"},
                                     {"i": 1, "text": "ဒီနေ့ ပြောမယ်"}]}),
                  authorization=H))
j = db.one("SELECT * FROM jobs WHERE id=?", JID)
ck("status = queued", j["status"] == "queued", j["status"])
ck("mode = cut (go မဟုတ်)", j["mode"] == "cut", j["mode"])
ck("ဖျက်ခိုင်းချက် သိမ်းပြီး",
   "_drop" in json.loads(j["over"] or "{}"), j["over"])
ck("အေးခဲသော ဖြတ်မှတ် မရှိသေး",
   "_spans" not in json.loads(j["over"] or "{}"))
ck("cut_* ရှင်းပြီး", j["cut_hash"] is None and j["cut_spans"] is None)

print("\n── ② worker က proxy ပို့ ⇒ cut_review ──")
SP = [[0.0, 2.1], [2.35, 5.05]]
_pv = os.path.join(_T, "p.mp4"); open(_pv, "wb").write(b"\x00" * 64)
class _F:
    def __init__(self, p): self.file = open(p, "rb")
db.run("UPDATE jobs SET status='running',minutes=1.5 WHERE id=?", JID)
r = run(M.w_cut(JID, file=_F(_pv),
                meta=json.dumps(dict(spans=SP, out_dur=4.8, src_dur=7.0, cuts=1)),
                authorization="Bearer " + M.WTOKEN))
j = db.one("SELECT * FROM jobs WHERE id=?", JID)
ck("status = cut_review", j["status"] == "cut_review", j["status"])
ck("hash က server ဘက် တွက်", r["hash"] == M._cuthash(SP)[0])
ck("ဖြတ်မှတ် ၂ ခု သိမ်းပြီး", j["cut_n"] == 2 and len(json.loads(j["cut_spans"])) == 2)
ck("**မိနစ် သုညသို့** (quota နှစ်ခါ မကောက်)", (j["minutes"] or 0) == 0, j["minutes"])
ck("ဖိုင် ရောက်ပြီး", os.path.exists(j["cut_path"]))
ck("ဖြတ်မှတ် မပါလျှင် 400",
   raises(run, M.w_cut(JID, file=_F(_pv), meta="{}",
                       authorization="Bearer " + M.WTOKEN)) == 400)

print("\n── ③ အခြား account — မကြည့်ရ · မဆုံးဖြတ်ရ ──")
ck("proxy ဖတ် ⇒ 404", raises(M.job_cut_file, JID, authorization=H2) == 404)
ck("cutok ⇒ 404",
   raises(run, M.job_cut_ok(JID, Req({}), authorization=H2)) == 404)
ck("recut ⇒ 404", raises(M.job_recut, JID, authorization=H2) == 404)
ck("ပိုင်ရှင် ဖတ်ရ", raises(M.job_cut_file, JID, authorization=H) is None)

print("\n── ④ ဖြတ်ချက် ပြန်ပြင် ⇒ စာတမ်း ဆုံးဖြတ်ချက် **မပျက်** ──")
_ov_before = json.loads(db.one("SELECT over FROM jobs WHERE id=?", JID)["over"] or "{}")
M.job_recut(JID, authorization=H)
j = db.one("SELECT * FROM jobs WHERE id=?", JID)
ck("status = review", j["status"] == "review", j["status"])
ck("mode = review", j["mode"] == "review", j["mode"])
ck("cut_* ရှင်းပြီး", j["cut_spans"] is None and j["cut_path"] is None)
ck("proxy ဖိုင် ဖျက်ပြီး", not os.path.exists(os.path.join(M.OUT, f"{JID}_cut.mp4")))
ck("segs_all မထိ", len(json.loads(j["segs_all"])) == 3)
ck("keep_n မထိ", json.loads(j["keep_n"] or "[]") == [1, 2], j["keep_n"])
ck("ဖျက်ခိုင်းချက် မထိ",
   json.loads(j["over"] or "{}").get("_drop") == _ov_before.get("_drop"))
ck("cut_review မဟုတ်ဘဲ cutok ⇒ 409",
   raises(run, M.job_cut_ok(JID, Req({}), authorization=H)) == 409)

print("\n── ⑤ ဖြတ်ချက် အိုကေ ⇒ **အေးခဲသော ဖြတ်မှတ်** နဲ့ render ──")
run(M.job_approve(JID, Req({"segs": [{"i": 0, "text": "မင်္ဂလာပါ"},
                                     {"i": 1, "text": "ဒီနေ့ ပြောမယ်"}]}),
                  authorization=H))
db.run("UPDATE jobs SET status='running' WHERE id=?", JID)
run(M.w_cut(JID, file=_F(_pv),
            meta=json.dumps(dict(spans=SP, out_dur=4.8, src_dur=7.0, cuts=1)),
            authorization="Bearer " + M.WTOKEN))
r = run(M.job_cut_ok(JID, Req({}), authorization=H))
j = db.one("SELECT * FROM jobs WHERE id=?", JID)
ov = json.loads(j["over"] or "{}")
ck("status = queued", j["status"] == "queued", j["status"])
ck("mode = go", j["mode"] == "go", j["mode"])
ck("over._spans = အတည်ပြုခဲ့သော ဖြတ်မှတ်", ov.get("_spans") == SP, ov.get("_spans"))
ck("over._cuthash ပါ", ov.get("_cuthash") == M._cuthash(SP)[0])
ck("cut_ok အချိန် မှတ်ပြီး", (j["cut_ok"] or 0) > 0)
ck("motion မရွေးလျှင် auto (recipe ပုံသေ)", r.get("motion") == "auto", r)
ck("auto ⇒ over._motion မသိမ်း", "_motion" not in ov)
ck("ထပ် cutok ⇒ 409",
   raises(run, M.job_cut_ok(JID, Req({}), authorization=H)) == 409)

print("\n── ⑥ hash မကိုက်လျှင် **ရပ်ရမည်** ──")
db.run("UPDATE jobs SET status='cut_review',cut_spans=?,cut_hash=? WHERE id=?",
       json.dumps([[0.0, 9.9]]), "deadbeefdeadbeef", JID)
ck("hash မကိုက် ⇒ 409",
   raises(run, M.job_cut_ok(JID, Req({}), authorization=H)) == 409)

print("\n── ⑦ quota — proxy က မကောက်ရ ──")
_u = db.one("SELECT minutes FROM usage WHERE ym=?", time.strftime("%Y-%m"))
ck("usage မိနစ် မတိုး", (_u or {"minutes": 0})["minutes"] in (0, 0.0, None),
   (_u or {}).get("minutes"))

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
