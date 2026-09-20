#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI · SQLite — အစမ်းအဆင့်မှာ Postgres မလိုသေး。

⚠️ ဖိုင်ကို volume ထဲ ထားရမည် — container ပြန်စလျှင် ပျောက်သွားမည်。
"""
import json, os, sqlite3, time, uuid

DB = os.environ.get("IKKI_DB", "/data/ikki.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS uploads(
  id TEXT PRIMARY KEY, name TEXT, size INTEGER, received INTEGER DEFAULT 0,
  path TEXT, done INTEGER DEFAULT 0, created REAL);

CREATE TABLE IF NOT EXISTS brands(
  id TEXT PRIMARY KEY, name TEXT, aspect TEXT,
  colors TEXT, mmf TEXT, latin TEXT, jp TEXT,
  top INTEGER, bot INTEGER, created REAL);

CREATE TABLE IF NOT EXISTS jobs(
  id TEXT PRIMARY KEY, title TEXT, upload_id TEXT, brand_id TEXT,
  recipe TEXT, font TEXT, status TEXT, stage INTEGER DEFAULT 0, stage_name TEXT,
  err TEXT, src_dur REAL, out_dur REAL, out_path TEXT, cuts INTEGER,
  captions INTEGER, flags INTEGER DEFAULT 0, minutes REAL DEFAULT 0,
  created REAL, claimed REAL, finished REAL);

CREATE TABLE IF NOT EXISTS versions(
  id TEXT PRIMARY KEY, job_id TEXT, n INTEGER, note TEXT,
  out_path TEXT, dur REAL, created REAL);

CREATE TABLE IF NOT EXISTS usage(
  ym TEXT PRIMARY KEY, minutes REAL DEFAULT 0, quota REAL DEFAULT 300);
"""

def conn():
    os.makedirs(os.path.dirname(DB) or ".", exist_ok=True)
    c = sqlite3.connect(DB, timeout=20)
    c.row_factory = sqlite3.Row
    # ⚠️ worker နှင့် web က တစ်ပြိုင်တည်း ရေးသည် — WAL မရှိလျှင် "database is locked"
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=8000")
    return c

def init():
    c = conn(); c.executescript(SCHEMA)
    # ⚠️ ရှိပြီးသား DB မှာ column အသစ် ထည့်ရန် (migration)
    cols = [r[1] for r in c.execute("PRAGMA table_info(jobs)")]
    if "font" not in cols:
        c.execute("ALTER TABLE jobs ADD COLUMN font TEXT")
    if "flags" not in cols:
        c.execute("ALTER TABLE jobs ADD COLUMN flags INTEGER DEFAULT 0")
    if "flag_list" not in cols:
        c.execute("ALTER TABLE jobs ADD COLUMN flag_list TEXT")
    # ⚠️ `over` = **job တစ်ခုချင်းရဲ့** ပြင်ချက် (style_over က style တစ်ခုလုံးအတွက်)。
    #    ပြန်ထုတ်တိုင်း style ကို မထိဘဲ ဒီတစ်ခုပဲ ပြောင်းနိုင်ရန်。
    for extra, ddl in (("segs","TEXT"), ("srt_path","TEXT"),
                       ("parent","TEXT"), ("approved","TEXT"), ("over","TEXT"),
                       ("deleted","REAL"), ("gone","INTEGER"), ("checked","REAL")):
        if extra not in cols:
            c.execute(f"ALTER TABLE jobs ADD COLUMN {extra} {ddl}")
    # ⚠️ R2 (object storage) mode — ဗီဒီယိုက VPS မဖြတ်ဘဲ တိုက်ရိုက် သွားသည်。
    #    key = R2 object key · mpu = multipart upload id
    # ⚠️ fmt = ထုတ်မည့် အရွယ် (9:16 · 3:4 …)。 brand နှင့် ခွဲထားသည်。
    # ⚠️ **transcript-first လုပ်ငန်းစဉ်**。 `mode`:
    #      review = ASR ပြီးလျှင် **ရပ်**ပြီး သုံးစွဲသူကို စာတမ်း ပြသည်
    #      go     = သုံးစွဲသူ အတည်ပြုပြီး — ဖြတ်ပြီး Edit ဆက်လုပ်သည်
    #      auto   = အရင်ပုံစံ (အကုန် အလိုအလျောက်)
    #    `plan` = worker တွက်ထားသော ဖြတ်မှတ် အကြံပြုချက် (JSON)
    #    ⚠️ Zin: "ဗီဒီယိုထည့်လိုက်တာနဲ့ အရင်ဆုံး Edit မလုပ်ခင် user ကို
    #      transcript ပြ" — ဖြတ်ချက်ကို **သုံးစွဲသူက ဆုံးဖြတ်ရမည်**、app က မဟုတ်。
    for extra, ddl in (("mode","TEXT"), ("plan","TEXT")):
        if extra not in cols:
            c.execute(f"ALTER TABLE jobs ADD COLUMN {extra} {ddl}")
    for extra, ddl in (("out_key","TEXT"), ("fmt","TEXT"), ("cap","TEXT")):
        if extra not in cols:
            c.execute(f"ALTER TABLE jobs ADD COLUMN {extra} {ddl}")
    # ⚠️ `vfmt` = သုံးစွဲသူ ပြောသော **ဗီဒီယို ပုံစံ** (camera · podcast · other)。
    #    ပြန်စ (retake) ရှာဖွေမှုက `camera` မှသာ — ဂိတ် (P≥၈၅) က vlog ၅/၅ အောင်ပြီး
    #    podcast ကျသည် (၇၉.၆% · ၂၀၂၆-၀၉-၁၆)。 ⇒ သုံးစွဲသူ ပေးသော label က
    #    ground truth label လည်း ဖြစ်သွားသည် (ပုံစံအလိုက် ခွဲတိုင်းနိုင်ရန်)。
    for extra, ddl in (("vfmt","TEXT"),):
        if extra not in cols:
            c.execute(f"ALTER TABLE jobs ADD COLUMN {extra} {ddl}")
    # ⚠️ brand ရဲ့ logo — ဖိုင်နာမည်သာ သိမ်းသည် (ဖိုင်က DATA/logos/ ထဲ)
    bcols = [r[1] for r in c.execute("PRAGMA table_info(brands)")]
    if "logo" not in bcols:
        c.execute("ALTER TABLE brands ADD COLUMN logo TEXT")
    # ⚠️ worker အများကြီး သုံးလျှင် **ဘယ် worker ယူသွားလဲ မှတ်ရမည်** —
    #    မမှတ်လျှင် claim က race ဖြစ်ပြီး worker ၂ ခု job တစ်ခုတည်းကို
    #    ယူမိနိုင်သည် (`db.run` က rowcount ကို ပစ်ပယ်၍ · ၂၀၂၆-၀၉-၁၉ တွေ့)。
    jcols2 = [r[1] for r in c.execute("PRAGMA table_info(jobs)")]
    if "worker" not in jcols2:
        c.execute("ALTER TABLE jobs ADD COLUMN worker TEXT")
    # ⚠️ **မူရင်း စာတမ်းကို ဖျက်မပစ်ရ**。 `approve` က `segs` ကို ချန်ထားသော
    #    ဝါကျများနှင့် အစားထိုးခဲ့သဖြင့် — ပြန်ပြင်တဲ့အခါ အရင် ဖျက်ထားတဲ့
    #    ဝါကျတွေ **ပြန်ပါလာ**ပြီး ဗီဒီယိုက ကြောင်တောင်တောင် ဖြစ်ခဲ့သည်
    #    (Zin ၂၀၂၆-၀၉-၂၀ · j_dd56e503c95c: ချန် ၁၁၂s ဖြစ်ပါလျက် ၃၂၂s ထွက်)。
    #    ⇒ `segs_all` = ASR ရဲ့ **အပြည့်** · `keep_n` = ချန်ခဲ့သော နံပါတ်များ。
    # ⚠️ `edit_plan` က **Headtop ရဲ့ HeadtopEditPlan** — ရှိပြီးသား `plan`
    #    (ဖြတ်မှတ် · retake အကြံပြုချက်) နဲ့ **လုံးဝ မတူ**。 worker က
    #    `st["plan"]` ဟု ရေးခဲ့သဖြင့် နာမည်တူပြီး `w_result` ကလည်း
    #    မသိမ်းသဖြင့် plan က တိတ်တဆိတ် ပျောက်ခဲ့သည် (၂၀၂၆-၀၉-၂၁ တိုင်းချက်:
    #    job ထဲက `plan` မှာ ဖြတ်မှတ်သာ ပါပြီး template event ၀ ခု)。
    #    ⇒ သုံးစွဲသူက event တစ်ခုချင်း ပြင်နိုင်ရန် **သီးသန့် ကော်လံ** လိုသည်。
    for _c, _d in (("segs_all", "TEXT"), ("keep_n", "TEXT"),
                   ("edit_plan", "TEXT")):
        if _c not in jcols2: c.execute(f"ALTER TABLE jobs ADD COLUMN {_c} {_d}")
    ucols = [r[1] for r in c.execute("PRAGMA table_info(uploads)")]
    for extra, ddl in (("key","TEXT"), ("mpu","TEXT"),
                       ("local","INTEGER DEFAULT 0")):
        if extra not in ucols:
            c.execute(f"ALTER TABLE uploads ADD COLUMN {extra} {ddl}")
    # ⚠️ notify ဆက်တင် — Telegram chat id
    c.execute("CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT)")
    # ⚠️ အကောင့် — အရင်က token တစ်ခုတည်းသာ ရှိ၍ **link ရသူတိုင်း အပြည့် ရ**ခဲ့
    #    (ဖျက်ခွင့်အပါ)。 ယခု အကောင့်တစ်ခုချင်း token ရှိပြီး data ခွဲထားသည်。
    c.execute("CREATE TABLE IF NOT EXISTS accounts("
              "id TEXT PRIMARY KEY, name TEXT, token TEXT UNIQUE,"
              "quota REAL, created REAL)")
    # ⚠️ ရှိပြီးသား data အားလုံးကို **ပုံသေအကောင့်** ပိုင်ဆိုင်စေရမည် —
    #    မဟုတ်လျှင် အဆင့်မြှင့်လိုက်တာနဲ့ ဗီဒီယိုအားလုံး ပျောက်သွားသလို ဖြစ်မည်。
    import os as _os
    dtok = _os.environ.get("IKKI_USER_TOKEN", "dev-user")
    row = c.execute("SELECT id FROM accounts WHERE id='a_default'").fetchone()
    if not row:
        c.execute("INSERT INTO accounts(id,name,token,quota,created) VALUES(?,?,?,?,?)",
                  ("a_default", "ZAE", dtok, 300.0, time.time()))
    else:
        c.execute("UPDATE accounts SET token=? WHERE id='a_default'", (dtok,))
    # ⚠️ UI ကနေ တင်လာသော ရုပ်ကြမ်း/ပုံ — worker က ဆွဲပြီး index လုပ်သည်
    # ⚠️ ဒီဇယားကို acct migration ရဲ့ **အရင်** ဆောက်ရမည်。 အောက်မှာ ထားခဲ့သဖြင့်
    #    DB အသစ် (volume အသစ်) မှာ "no such table: brollq" နဲ့ API တစ်ခုလုံး
    #    တက်မလာခဲ့ — server ဟောင်းမှာ ဇယား ရှိနှင့်ပြီး၍ မပေါ်ခဲ့ခြင်း ဖြစ်သည်。
    c.execute("CREATE TABLE IF NOT EXISTS brollq("
              "id TEXT PRIMARY KEY, name TEXT, ext TEXT, status TEXT,"
              "tags TEXT, note TEXT, created REAL)")
    for tbl in ("jobs", "brands", "uploads", "brollq"):
        cols2 = [r[1] for r in c.execute(f"PRAGMA table_info({tbl})")]
        if "acct" not in cols2:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN acct TEXT")
            c.execute(f"UPDATE {tbl} SET acct='a_default' WHERE acct IS NULL")
    # ⚠️ `acct` မပါဘဲ ဆောက်မိသော job ကို **ပျောက်နေစေလို့ မရ** — စာရင်းက
    #    `WHERE acct=?` နဲ့ စစ်သဖြင့် NULL တစ်ခုက ဗီဒီယိုတစ်ခုလုံး ပျောက်သည်。
    #    parent ရှိလျှင် အဲဒီက ယူ၊ မရှိလျှင် ပုံသေအကောင့်。 (reedit မှာ
    #    ထည့်ရန် ကျန်ခဲ့ဖူးသည် — ဒါက ဒုတိယအလွှာ ကာကွယ်မှု)
    try:
        c.execute("UPDATE jobs SET acct=(SELECT p.acct FROM jobs p WHERE p.id=jobs.parent)"
                  " WHERE acct IS NULL AND parent IS NOT NULL")
        c.execute("UPDATE jobs SET acct='a_default' WHERE acct IS NULL")
    except sqlite3.OperationalError:
        pass
    # ⚠️ ငွေလွှဲ တောင်းဆိုချက် — KBZPay / Wave / CB Pay。 **card gateway မဟုတ်**
    #    ⇒ server က ငွေရပြီးမပြီး **မသိနိုင်**。 သုံးစွဲသူက ငွေလွှဲပြီး ငွေလွှဲနံပါတ်
    #    ရိုက်ထည့် → ပိုင်ရှင်က bank app ထဲ စစ်ပြီးမှ အတည်ပြုမှ မိနစ် တက်သည်。
    #    အလိုအလျောက် အတည်ပြုခြင်း **လုံးဝ မလုပ်ရ** — လိမ်ခံရမည်。
    c.execute("CREATE TABLE IF NOT EXISTS pays("
              "id TEXT PRIMARY KEY, acct TEXT, method TEXT, amount REAL,"
              "minutes REAL, ref TEXT, note TEXT, status TEXT,"
              "created REAL, decided REAL, by TEXT, why TEXT)")
    # ⚠️ ငွေလွှဲနံပါတ် တစ်ခုကို **တစ်ခါပဲ** သုံးခွင့်ပြုရမည် — မဟုတ်လျှင်
    #    တစ်ခါလွှဲပြီး အကြိမ်ကြိမ် တင်၍ မိနစ် အလကား ရသွားနိုင်သည်。
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS pays_ref ON pays(ref)")
    # ⚠️ ပုံစံ ပြင်ချက် — **ပြင်ထားတဲ့ field ကိုပဲ** သိမ်းသည်。 အားလုံး
    #    သိမ်းလျှင် recipe ရဲ့ တိုင်းထားသော ပုံသေ ပြောင်းလည်း လိုက်မပြောင်းဘူး。
    c.execute("CREATE TABLE IF NOT EXISTS style_over("
              "style TEXT PRIMARY KEY, data TEXT, updated REAL)")
    # ⚠️ ပြန်စ အကြံပြုချက် တစ်ခုချင်းရဲ့ **လူ့ဆုံးဖြတ်ချက်** — ground truth စုရန်。
    #    C0736 တစ်ခုတည်း (FP n=၃) နဲ့ စည်းမျဉ်း ချလျှင် overfit ⇒ ဗီဒီယိုတိုင်းက
    #    လက်ခံ/ပယ် နမူနာ တိုးစေရန် (၂၀၂၆-၀၉-၁၆)。 `to` က SQL keyword ⇒ at_s/to_s。
    c.execute("CREATE TABLE IF NOT EXISTS retake_review("
              "id TEXT PRIMARY KEY, job_id TEXT, new_job TEXT, upload_id TEXT, acct TEXT,"
              "rid TEXT, at_s REAL, to_s REAL, sentences TEXT, finals TEXT, conf REAL,"
              "text TEXT, keep TEXT, decision TEXT, reason TEXT, created REAL)")
    # ⚠️ review v2 — **အုပ်စု တစ်ခုချင်းရဲ့ ရွေးချယ်ချက်**。 v1 (`retake_review`) ကို
    #    မဖျက် — ယခင် ဒေတာ ထိန်းရန်。 `picked` = ချန်လိုက်သော take နံပါတ် ·
    #    `none` = ဘာမှ မဖျက် (ပုံသေ)。 `takes` = take တစ်ခုချင်း (JSON) ⇒ ဗီဒီယို
    #    တင်တိုင်း ground truth တိုးလာစေရန် — ဒါက ဤ feature ရဲ့ **အဓိက ရည်ရွယ်ချက်**。
    c.execute("CREATE TABLE IF NOT EXISTS retake_pick("
              "id TEXT PRIMARY KEY, job_id TEXT, upload_id TEXT, acct TEXT, vfmt TEXT,"
              "cluster_id TEXT, takes TEXT, picked TEXT, dropped TEXT, drop_s REAL,"
              "conf REAL, created REAL)")
    if not c.execute("SELECT 1 FROM brands LIMIT 1").fetchone():
        for b in (dict(id="zjl", name="ZIN JAPAN LIFE", aspect="16:9",
                       colors=["#101014","#1C1C22","#FFE000","#5B9BD5","#E8102A"],
                       mmf="MyanmarYinmar", latin="Figtree-Black", jp="HiraginoSans-W7",
                       top=170, bot=830),
                  dict(id="zae", name="Zin Apex Education", aspect="3:4",
                       colors=["#0B1B33","#16304C","#F5C543","#4FA8DC","#E5484D"],
                       mmf="MyanmarHeadOne", latin="Figtree-Black", jp="HiraginoSans-W7",
                       top=300, bot=940)):
            c.execute("INSERT INTO brands(id,name,aspect,colors,mmf,latin,jp,top,bot,created)"
                      " VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (b["id"],b["name"],b["aspect"],json.dumps(b["colors"]),
                       b["mmf"],b["latin"],b["jp"],b["top"],b["bot"],time.time()))
    ym = time.strftime("%Y-%m")
    c.execute("INSERT OR IGNORE INTO usage(ym,minutes,quota) VALUES(?,0,300)", (ym,))
    c.commit(); c.close()

def nid(p=""): return (p+uuid.uuid4().hex[:12])
def rows(q, *a):
    c = conn(); r = [dict(x) for x in c.execute(q, a).fetchall()]; c.close(); return r
def one(q, *a):
    r = rows(q, *a); return r[0] if r else None
def run(q, *a):
    c = conn(); c.execute(q, a); c.commit(); c.close()
