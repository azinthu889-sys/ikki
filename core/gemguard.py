"""
gemguard — Gemini ကို ခေါ်တဲ့အခါ ပိုက်ဆံ မဖြုန်းအောင် ကာကွယ်ပေးသည်။

ဖြစ်ခဲ့တာ (2026-09-08, JST 23:00): credit ကုန်သွားပြီးမှ script တွေက
retry ဆက်လုပ်နေလို့ တစ်နာရီအတွင်း request ~950 ခု ပစ်မိသည် — အားလုံး 429၊
အလကား။ AI Studio ဂရပ်မှာ ကြီးမားတဲ့ အနီရောင် တံတိုင်းအဖြစ် မြင်ရသည်။

ဤ module က နှစ်ခု လုပ်ပေးသည်:
  1. QUOTA သေပြီဆိုတာ တစ်ကြိမ်တည်း သိလျှင် thread အားလုံး ချက်ချင်း ရပ်သည်။
     (rate-limit 429 နှင့် credit-depleted 429 က မတူ — ပထမတစ်ခုကသာ စောင့်ထိုက်သည်)
  2. chunk တစ်ခုကို တစ်ကြိမ်ပဲ ခေါ်စေရန် cache လုပ်သည်။ ပြန် run လျှင်
     ဖိုင်ထဲကဖတ်၍ token ထပ်မကုန်။
"""
import hashlib, json, os, re, threading

_dead = threading.Event()
_reason = [""]

# credit ကုန်ခြင်း / billing ပိတ်ခြင်း — ဘယ်လောက်စောင့်စောင့် ပြန်မလာ
_FATAL = ("credits are depleted", "prepayment", "billing account",
          "api key not valid", "has been suspended", "consumer_suspended")


# ⚠️ **တိုင်းတာမှုသာ** — retry logic ကို မထိပါ (အဆင့် ၁.၃ မှာ စုမည်)。
#    render report ရဲ့ GEMINI အပိုင်းကို ဖြည့်ရန် ok/fail ရေတွက်သည်。
TALLY = {}


def tally(tag, ok, err=None):
    t = TALLY.setdefault(tag, {"ok": 0, "fail": 0, "last": None})
    t["ok" if ok else "fail"] += 1
    if not ok and err: t["last"] = str(err)[:80]


def tally_reset():
    TALLY.clear()


# ⚠️ **ကျတဲ့ ခေါ်ဆိုမှုကို ဖိုင်မှာ မှတ်တမ်းတင်ရမည်** — ၂၀၂၆-၀၉-၁၆: retake prompt
#    ၈ ခုမှာ ၆ ခု None ပြန်ပြီး status/error မသိခဲ့ (TALLY က process ထဲမှာသာ)。
#    ⇒ ကျတိုင်း tag · attempt/tries · HTTP code · error · နောက်ဆုံးလား ကို JSONL နဲ့ ထည့်。
FAIL_LOG = os.path.expanduser(os.environ.get("IKKI_GEMINI_FAIL_LOG", "~/.ikki/gemini_fail.jsonl"))
_fail_lock = threading.Lock()

def log_fail(tag, attempt, tries, code=None, err="", final=False):
    import time as _t
    rec = {"t": _t.strftime("%Y-%m-%dT%H:%M:%S"), "tag": tag, "attempt": attempt,
           "tries": tries, "code": code, "err": str(err or "")[:300], "final": bool(final)}
    try:
        with _fail_lock:
            os.makedirs(os.path.dirname(FAIL_LOG), exist_ok=True)
            with open(FAIL_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def fatal(code, body):
    """429/403 က ပြန်ထူမလာတဲ့ အမျိုးအစားလား စစ်သည်။ ဟုတ်လျှင် အားလုံး ရပ်။"""
    b = (body or "").lower()
    if code in (401, 403) or (code == 429 and any(k.lower() in b for k in _FATAL)):
        if not _dead.is_set():
            _reason[0] = (body or "")[:200]
        _dead.set()
        return True
    return False


def dead():
    return _dead.is_set()


def reason():
    return _reason[0]


def stop_if_dead():
    if _dead.is_set():
        raise SystemExit(
            f"\n  ⛔ Gemini quota ကုန်နေသည် — retry မလုပ်တော့ဘဲ ရပ်လိုက်သည်။\n"
            f"     {_reason[0]}\n"
            f"     credit ဖြည့်ပြီးမှ ထပ် run ပါ။ cache ရှိသဖြင့် ပြီးပြီးသား\n"
            f"     chunk တွေကို ထပ်မခေါ်တော့ပါ။")


# ── cache ────────────────────────────────────────────────────────────────
def _dir():
    d = os.path.join("work", ".gemcache")
    os.makedirs(d, exist_ok=True)
    return d


def key(model, prompt, audio_bytes):
    h = hashlib.sha256()
    h.update(model.encode()); h.update(b"\0")
    h.update(prompt.encode()); h.update(b"\0")
    h.update(audio_bytes)
    return h.hexdigest()[:32]


def get(k):
    p = os.path.join(_dir(), k + ".json")
    if os.path.exists(p):
        try:
            return json.load(open(p))["text"]
        except Exception:
            return None
    return None


def put(k, text):
    try:
        json.dump({"text": text}, open(os.path.join(_dir(), k + ".json"), "w"))
    except Exception:
        pass


def drop(k):
    """မှားနေသော အဖြေကို cache မှ ဖယ်သည် — မဖယ်လျှင် ထပ် run တိုင်း
    အမှားကိုပဲ ပြန်ဖတ်နေမည်။"""
    try: os.remove(os.path.join(_dir(), k + ".json"))
    except Exception: pass


def stats():
    d = _dir()
    n = len([f for f in os.listdir(d) if f.endswith(".json")])
    return n


# ── endpoint ရွေးချယ်ခြင်း + free-tier rate limit ────────────────────────
# key ဖိုင် ရှိလျှင် တိုက်ရိုက် Gemini ကို၊ မရှိလျှင် n8n proxy ကို သွားသည်။
# proxy က `ZJL Editing Workflow free` credential ကို သုံးသဖြင့် key ကို
# ဤစက်ထဲ ကူးထားစရာ မလို။
import time as _time

PROXY = os.environ.get(
    "ZJL_GEMINI_PROXY",
    "https://n8n.srv1866621.hstgr.cloud/webhook/zjl-gemini")

# gemini.key (paid) ကို မထည့်ထား — credit ကုန်နေသည်။ free key ဖိုင်
# ရှိမှသာ တိုက်ရိုက်သွား၊ မရှိလျှင် n8n proxy က free credential ကို သုံးသည်။
_KEYFILES = ["~/.config/zae/gemini_free.key"]
# key ၂ ခု စနစ် (၂၀၂၆-၀၉-၁၆) — production worker က env မထား ⇒ အပေါ်က ဖိုင်။
# စမ်းသပ် script တွေက IKKI_GEMINI_KEYFILE ကို သီးခြား project key ဖိုင်သို့ ညွှန်
# ⇒ စမ်းသပ်ချက်က production quota ကို မကုန်စေ。
if os.environ.get("IKKI_GEMINI_KEYFILE"):
    _KEYFILES = [os.environ["IKKI_GEMINI_KEYFILE"]]


def local_key():
    if os.environ.get("ZJL_FORCE_PROXY"):
        return None
    for p in _KEYFILES:
        f = os.path.expanduser(p)
        if os.path.exists(f):
            k = open(f).read().strip()
            if k:
                return k
    return None


def endpoint(model):
    k = local_key()
    if k:
        return (f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={k}")
    return f"{PROXY}?model={model}"


# free tier က မိနစ်လျှင် ခေါ်ဆိုမှု အကန့်အသတ် ရှိသည် (≈10 RPM)။
# thread အားလုံးအတွက် တစ်ခုတည်းသော အကွာအဝေး ထိန်းသည်။
_MIN_GAP = float(os.environ.get("ZJL_MIN_GAP", "5.0"))
_lock = threading.Lock()
_last = [0.0]


def throttle(gap=None):
    """ခေါ်ဆိုမှု နှစ်ခုကြား အနည်းဆုံး ကြာချိန်。

    ⚠️ `gap` ကို ခေါ်သူက **သီးသန့် ပေးနိုင်**သည် — ASR က chunk အများကြီး
       ခေါ်ရသဖြင့် ၅s က ရှည်လွန်းသည် (၂၀၂၆-၀၉-၁၉ တိုင်းချက်: ခေါ်ဆိုမှု ၁၂ ခု
       တစ်ပြိုင်နက် · gap ၀ → ၁၂/၁၂ အောင် · 429 မရှိ)。 အခြား ခေါ်ဆိုမှုများ
       (slide · broll · retake) ကို မထိခိုက်စေရန် global ကို မပြောင်းပါ。
    """
    g = _MIN_GAP if gap is None else float(gap)
    with _lock:
        wait = g - (_time.monotonic() - _last[0])
        if wait > 0:
            _time.sleep(wait)
        _last[0] = _time.monotonic()


# ── retry backoff ────────────────────────────────────────────────────────
# free tier က 503 "high demand" ကို မကြာခဏ ပြန်ပေးသည် — ယာယီသာဖြစ်၍
# ကြာကြာစောင့်လျှင် ရသည်။ retry ၅ ကြိမ် (၂၀၀ စက္ကန့်) နှင့် မလုံလောက်ခဲ့။
import random as _rnd

TRIES = int(os.environ.get("ZJL_TRIES", "12"))


def retryable(code):
    # 408/499 = proxy ဘက် connection ပြတ်ခြင်း — ယာယီသာ
    return code in (408, 429, 499, 500, 502, 503, 504)


_DELAY_RE = re.compile(r'"retryDelay"\s*:\s*"?(\d+(?:\.\d+)?)s')


def server_delay(body):
    """Gemini က ဘယ်လောက်စောင့်ရမည် ပြောလျှင် အဲဒါကို နာခံသည်။"""
    m = _DELAY_RE.search(body or "")
    return float(m.group(1)) if m else 0.0


def backoff(i, body=""):
    """၈s ကနေ စ၍ တဖြည်းဖြည်း တိုး၊ ၉၀s မှာ ရပ်။ jitter ထည့်၍ တစ်ပြိုင်တည်း
    ပြန်မတိုးစေရန် ကာကွယ်သည်။"""
    return max(server_delay(body) + 1.0,
               min(90.0, 8.0 * (1.6 ** i)) * (0.75 + 0.5 * _rnd.random()))
