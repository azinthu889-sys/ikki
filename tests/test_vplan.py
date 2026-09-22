# -*- coding: utf-8 -*-
"""Visual Plan · Motion Kit catalog · Fine tune — **API အဆင့်**。

⚠️ browser က port 8765 ကို မဆွဲရ ⇒ worker က snapshot တင် · API က ဖြန့်。
   snapshot မရှိလျှင် **တိတ်တဆိတ် ဗလာ မပြရ** — အကြောင်းရင်း ပါရမည်。
⚠️ သုံးစွဲသူ ရွေးသော template က **စစ်ပြီးသား စာရင်းထဲ** မှသာ。
⚠️ အလှအပ ပြန်ထုတ်လျှင် **ဖြတ်ချက် မထိရ** (အေးခဲသော ဖြတ်မှတ် ရှိရမည်)。
⚠️ သီးသန့် DB/DATA နဲ့ ပြေးရမည်。
"""
import os, sys, tempfile, json

_T = tempfile.mkdtemp(prefix="ikki_vp_")
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
W = "Bearer " + M.WTOKEN
a2 = run(M.account_new(Req({"name": "Other"}), authorization=H))
H2 = "Bearer " + a2["token"]

print("── ① catalog မရှိခင် — **အကြောင်းရင်း ပါရမည်** ──")
r = M.motion_catalog(authorization=H)
ck("ok=False", r["ok"] is False)
ck("items ဗလာ", r["items"] == [])
ck("why ပါ (မြန်မာ)", bool(r.get("why")), r)
ck("why_en ပါ", bool(r.get("why_en")))

print("\n── ② worker က တင် ──")
SNAP = dict(ok=True, n=3, total=479, fmt="16:9",
            cats=[dict(id="text", en="Text motion", my="စာလုံး"),
                  dict(id="info", en="Infographics", my="အချက်အလက်")],
            items=[dict(id="kinetic.word_pop", name="Word Pop", cat="text",
                        shape="", slots=[], role="overlay"),
                   dict(id="infogfx.pyramid", name="Pyramid", cat="info",
                        shape="pair", slots=[], role="overlay"),
                   dict(id="charts.bar_race", name="Bar Race", cat="info",
                        shape="pair", slots=[], role="overlay")])
run(M.w_catalog(Req(SNAP), authorization=W))
r = M.motion_catalog(authorization=H)
ck("ok=True", r["ok"] is True)
ck("၃ ခု", r["n"] == 3, r["n"])
ck("total ပါ (၄၇၉ ကနေ စစ်ထားကြောင်း)", r["total"] == 479)
ck("အုပ်စုနဲ့ စစ်နိုင်", M.motion_catalog(cat="info", authorization=H)["n"] == 2)
ck("စကားလုံးနဲ့ ရှာနိုင်", M.motion_catalog(q="pyramid", authorization=H)["n"] == 1)
ck("ok=False payload ⇒ 400",
   raises(run, M.w_catalog(Req(dict(ok=False, why="မရ")), authorization=W)) == 400)
ck("items ဗလာ ⇒ 400",
   raises(run, M.w_catalog(Req(dict(ok=True, items=[])), authorization=W)) == 400)
ck("user token နဲ့ တင်လို့ မရ",
   raises(run, M.w_catalog(Req(SNAP), authorization=H)) == 401)

# ── job တစ်ခု (ပြီးဆုံးပြီး · အေးခဲသော ဖြတ်မှတ် ရှိ) ──
JID = "j_vptest"
SP = [[0.0, 2.1], [2.35, 5.05]]
db.run("INSERT INTO jobs(id,title,upload_id,brand_id,recipe,status,stage,created) "
       "VALUES(?,?,?,?,?,?,?,?)", JID, "t", "u_x", "ikki", "knowledge",
       "done", 7, time.time())
db.run("UPDATE jobs SET acct=?,mode='go',over=?,vplan=? WHERE id=?",
       "a_default",
       json.dumps({"_spans": SP, "_cuthash": M._cuthash(SP)[0]}),
       json.dumps([dict(id="g1.20", at=1.2, dur=3.0, tpl="kinetic.word_pop"),
                   dict(id="g4.00", at=4.0, dur=2.5, tpl="infogfx.pyramid")]),
       JID)

print("\n── ③ Visual Plan ဆုံးဖြတ်ချက် ──")
run(M.job_vplan(JID, Req({"ev": {"g1.20": {"mode": "none"},
                                 "g4.00": {"mode": "tpl", "tpl": "charts.bar_race"}}}),
                authorization=H))
ov = json.loads(db.one("SELECT over FROM jobs WHERE id=?", JID)["over"])
ck("ဖြုတ်ချက် သိမ်းပြီး", ov["_ev"]["g1.20"] == {"mode": "none"})
ck("လဲချက် သိမ်းပြီး",
   ov["_ev"]["g4.00"] == {"mode": "tpl", "tpl": "charts.bar_race"})
ck("အေးခဲသော ဖြတ်မှတ် မထိ", ov.get("_spans") == SP)
ck("auto ⇒ မသိမ်း (ပုံသေ)",
   (run(M.job_vplan(JID, Req({"ev": {"g1.20": {"mode": "auto"}}}), authorization=H)),
    "_ev" not in json.loads(db.one("SELECT over FROM jobs WHERE id=?", JID)["over"]))[1])
ck("စစ်ပြီးသား စာရင်းထဲ မပါသော template ⇒ 400",
   raises(run, M.job_vplan(JID, Req({"ev": {"g1.20": {"mode": "tpl",
                                                      "tpl": "nope.nope"}}}),
                           authorization=H)) == 400)
ck("mode မမှန် ⇒ 400",
   raises(run, M.job_vplan(JID, Req({"ev": {"g1.20": {"mode": "zap"}}}),
                           authorization=H)) == 400)
ck("tpl မပါ ⇒ 400",
   raises(run, M.job_vplan(JID, Req({"ev": {"g1.20": {"mode": "tpl"}}}),
                           authorization=H)) == 400)
ck("ev မပါ ⇒ 400",
   raises(run, M.job_vplan(JID, Req({}), authorization=H)) == 400)
ck("event ၂၀၀ ထက် ⇒ 400",
   raises(run, M.job_vplan(JID, Req({"ev": {f"g{i}": {"mode": "none"}
                                            for i in range(201)}}),
                           authorization=H)) == 400)
ck("အခြား account ⇒ 404",
   raises(run, M.job_vplan(JID, Req({"ev": {}}), authorization=H2)) == 404)

print("\n── ④ အလှအပ ပြန်ထုတ် — ဖြတ်ချက် မထိ ──")
r = M.job_revis(JID, authorization=H)
j = db.one("SELECT * FROM jobs WHERE id=?", JID)
ck("status = queued", j["status"] == "queued", j["status"])
ck("mode = go", j["mode"] == "go")
ck("အေးခဲသော ဖြတ်မှတ် ကျန်နေ (ပြန်အတည်ပြုစရာ မလို)", r["spans"] == 2)
ck("ပြီးဆုံးမထားလျှင် ⇒ 409", raises(M.job_revis, JID, authorization=H) == 409)
db.run("UPDATE jobs SET status='done',over=? WHERE id=?", json.dumps({}), JID)
ck("အေးခဲသော ဖြတ်မှတ် မရှိလျှင် ⇒ 409",
   raises(M.job_revis, JID, authorization=H) == 409)
ck("အခြား account ⇒ 404", raises(M.job_revis, JID, authorization=H2) == 404)

print("\n── ⑤ Fine tune ──")
import recipes as RC
_cap = list(RC.CAPSIZE)[0]
run(M.job_finetune(JID, Req({"cap": _cap, "music_off": True}), authorization=H))
j = db.one("SELECT * FROM jobs WHERE id=?", JID)
ck("စာတန်း အရွယ် သိမ်းပြီး", j["cap"] == _cap, j["cap"])
ck("တီးလုံး ပိတ် ⇒ over.music = None",
   json.loads(j["over"] or "{}").get("music", "X") is None,
   j["over"])
run(M.job_finetune(JID, Req({"music_off": False}), authorization=H))
ck("ပြန်ဖွင့် ⇒ over.music ဖယ်",
   "music" not in json.loads(db.one("SELECT over FROM jobs WHERE id=?", JID)["over"] or "{}"))
ck("စာတန်း အရွယ် မမှန် ⇒ 400",
   raises(run, M.job_finetune(JID, Req({"cap": "huge-nope"}), authorization=H)) == 400)
run(M.job_finetune(JID, Req({"cap": ""}), authorization=H))
ck("ဗလာ ⇒ ပုံစံ ပုံသေ ပြန်",
   db.one("SELECT cap FROM jobs WHERE id=?", JID)["cap"] is None)
ck("အခြား account ⇒ 404",
   raises(run, M.job_finetune(JID, Req({"cap": ""}), authorization=H2)) == 404)

print("\n── ⑥ cutok မှာ အလှအပ အဆင့် ──")
db.run("UPDATE jobs SET status='cut_review',cut_spans=?,cut_hash=?,over=? WHERE id=?",
       json.dumps(SP), M._cuthash(SP)[0], None, JID)
run(M.job_cut_ok(JID, Req({"motion": "high"}), authorization=H))
ov = json.loads(db.one("SELECT over FROM jobs WHERE id=?", JID)["over"])
ck("over._motion = high", ov.get("_motion") == "high", ov)
db.run("UPDATE jobs SET status='cut_review',over=? WHERE id=?", None, JID)
run(M.job_cut_ok(JID, Req({"motion": "auto"}), authorization=H))
ck("auto ⇒ မသိမ်း (recipe ပုံသေ)",
   "_motion" not in json.loads(db.one("SELECT over FROM jobs WHERE id=?", JID)["over"]))
db.run("UPDATE jobs SET status='cut_review' WHERE id=?", JID)
ck("အဆင့် မမှန် ⇒ 400",
   raises(run, M.job_cut_ok(JID, Req({"motion": "turbo"}), authorization=H)) == 400)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
