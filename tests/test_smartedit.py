# -*- coding: utf-8 -*-
"""IKKI Smart Edit ↔ ကိုယ်ပိုင် brand — **product-level ခွဲခြားမှု**。

⚠️ ယခင်က `GET /api/brands` က `OR id IN ('zae','zjl')` နဲ့ **ပိုင်ရှင်ရဲ့
   သီးသန့် preset ၂ ခုကို account အသစ်တိုင်း** ပြခဲ့သည် — အသုံးပြုသူ အသစ်က
   「ZIN JAPAN LIFE」နဲ့ စရမလို ဖြစ်ခဲ့သည်。
⚠️ `ikki` က customer kit **မဟုတ်** — neutral system mode (logo/watermark
   မထည့်ပါ) ⇒ ပြင်/ဖျက်/logo တင် **မရ**。
⚠️ brand operation တိုင်း **account အလိုက် ကန့်သတ်** ရမည် — `ON CONFLICT
   DO UPDATE` က id တူရုံနဲ့ လွှမ်းသဖြင့် သူတစ်ပါးရဲ့ kit ကို ပြင်လိုက်နိုင်သည်。

⚠️ **သီးသန့် DB/DATA နဲ့ ပြေးရမည်** — `api/main.py` က import ချိန်
   `/data` ကို ဆောက်သဖြင့် env မသတ်မှတ်လျှင် ကျသည်。
"""
import os, sys, tempfile

_T = tempfile.mkdtemp(prefix="ikki_smart_")
os.environ["IKKI_DATA"] = _T
os.environ["IKKI_DB"] = os.path.join(_T, "t.db")

import json, asyncio

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "api"))
sys.path.insert(0, os.path.join(_R, "core"))
# ⚠️ **fastapi လိုသည်** — venv မဟုတ်လျှင် import မရ ⇒ ကျဘမ်း မဟုတ်ဘဲ ကျော်သည်
try:
    import fastapi  # noqa: F401
except ImportError:
    print("  ⊘ fastapi မရှိ — ဤ test ကို ကျော်သည် (venv နဲ့ ပြေးပါ)")
    sys.exit(0)
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

def post(d, tok):
    return asyncio.get_event_loop().run_until_complete(
        M.brand_new(Req(d), authorization="Bearer " + tok))

# ── အကောင့် ၂ ခု ──
dflt = (db.one("SELECT token FROM accounts WHERE id='a_default'") or {})["token"]
a2 = asyncio.get_event_loop().run_until_complete(
    M.account_new(Req({"name": "New User"}), authorization="Bearer " + dflt))
t2 = a2["token"]

print("\n── ① အကောင့်အသစ်က IKKI Smart Edit သာ မြင်ရမည် ──")
bs = M.brands(authorization="Bearer " + t2)["brands"]
ids = [b["id"] for b in bs]
ck("ikki ရှေ့ဆုံး", ids[:1] == ["ikki"], ids)
ck("ZIN preset မပါ", "zjl" not in ids and "zae" not in ids, ids)
ck("ikki က is_system", bs[0].get("is_system") is True)
ck("ikki မှာ logo မရှိ", bs[0].get("logo") is None)
ck("my/en ဖော်ပြချက် ပါ", bool(bs[0].get("my")) and bool(bs[0].get("en")))

print("\n── ② a_default က သူ့ ZIN preset မြင်ရမည် ──")
bd = M.brands(authorization="Bearer " + dflt)["brands"]
idd = [b["id"] for b in bd]
ck("ikki ရှေ့ဆုံး", idd[0] == "ikki", idd)
ck("zjl · zae ပါ", "zjl" in idd and "zae" in idd, idd)

print("\n── ③ ikki ကို ပြင်/ဖျက်/logo မရ ──")
ck("POST ikki ⇒ 400", raises(post, {"id": "ikki", "name": "x"}, dflt) == 400)
ck("DELETE ikki ⇒ 400",
   raises(M.brand_del, "ikki", authorization="Bearer " + dflt) == 400)
ck("DELETE ikki logo ⇒ 400",
   raises(M.brand_logo_del, "ikki", authorization="Bearer " + dflt) == 400)

print("\n── ④ ကိုယ်ပိုင် kit — ဆောက် · ခွဲ · ဖျက် ──")
r = post({"name": "My Kit", "aspect": "9:16"}, t2)
nid = r["id"]
ck("ဆောက်ပြီး id ရ", bool(nid))
i2 = [b["id"] for b in M.brands(authorization="Bearer " + t2)["brands"]]
ck("acct2 မှာ ပေါ်", nid in i2, i2)
i1 = [b["id"] for b in M.brands(authorization="Bearer " + dflt)["brands"]]
ck("a_default မှာ မပေါ် (account ခွဲ)", nid not in i1, i1)

print("\n── ⑤ account ခွဲ — သူတစ်ပါးရဲ့ kit မပြင်ရ ──")
ck("acct2 က zjl ပြင် ⇒ 403", raises(post, {"id": "zjl", "name": "hack"}, t2) == 403)
ck("zjl နာမည် မပျက်",
   (db.one("SELECT name FROM brands WHERE id='zjl'") or {})["name"] == "ZIN JAPAN LIFE")
M.brand_del(nid, authorization="Bearer " + t2)
ck("ဖျက်ပြီး ပျောက်", nid not in [b["id"] for b in
                                   M.brands(authorization="Bearer " + t2)["brands"]])
ck("a_default ရဲ့ zjl မထိ", db.one("SELECT 1 FROM brands WHERE id='zjl'") is not None)

print("\n── ⑥ logo ဖတ်ခြင်း — ကိုယ်ပိုင်ဟာသာ မြင်ရမည် ──")
# ⚠️ ယခင်က `tok not in (UTOKEN, WTOKEN)` ⇒ account token ကို ပယ်သဖြင့်
#    ဖောက်သည် ရဲ့ logo မပေါ်; မျှဝေ UTOKEN ရှိသူက brand တိုင်း ဖတ်နိုင်ခဲ့
k2 = post({"name": "Logo Kit", "aspect": "16:9"}, t2)["id"]
os.makedirs(M.LOGO, exist_ok=True)
open(os.path.join(M.LOGO, f"{k2}.png"), "wb").write(b"\x89PNG\r\n\x1a\n")
ck("ပိုင်ရှင် (acct2) ဖတ်ရ",
   raises(M.brand_logo_get, k2, authorization="Bearer " + t2) is None)
ck("အခြား account (a_default) ⇒ 404",
   raises(M.brand_logo_get, k2, authorization="Bearer " + dflt) == 404)
ck("worker token ⇒ ဖတ်ရ (ဗီဒီယိုထဲ ထည့်ရန်)",
   raises(M.brand_logo_get, k2, authorization="Bearer " + M.WTOKEN) is None)
ck("token မှား ⇒ 401",
   raises(M.brand_logo_get, k2, authorization="Bearer nope") == 401)
ck("t= query နဲ့လည်း ပိုင်ရှင် ဖတ်ရ",
   raises(M.brand_logo_get, k2, authorization=None, t=t2) is None)
M.brand_del(k2, authorization="Bearer " + t2)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
