#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · object storage (Cloudflare R2 / S3-နှင့် တွဲဖက်နိုင်သော)。

⚠️ **ဗီဒီယိုကို VPS မဖြတ်ရ**。 အရင်စနစ်မှာ ဖိုင်တစ်ခုက VPS ကို ၄ ခါ ဖြတ်ခဲ့သည် —
   user upload → Mac ဆွဲချ → Mac output တင် → user download。 ၄၁၉ MB ဖိုင်
   တစ်ခုက ၆ Mbps လိုင်းနှင့် ဆွဲချရုံ ၁၀ မိနစ် ကြာခဲ့သည် (တကယ် တိုင်းထားသည်)。
   ⇒ presigned URL ဖြင့် browser/worker က R2 ကို **တိုက်ရိုက်** သွားသည်。

⚠️ boto3 **မသုံးပါ** — SigV4 ကို ကိုယ်တိုင် လုပ်သည်。 container ထဲ
   dependency မတိုးစေရန်；stdlib ပဲ သုံးသည်。

R2 မရှိလျှင် `on()` က False ပြန်ပြီး app က **local disk mode** ဖြင့် ဆက်လုပ်သည် —
ဒါကြောင့် key မရှိဘဲလည်း စနစ်တစ်ခုလုံး အလုပ်လုပ်နေသည်。
"""
import datetime, hashlib, hmac, json, os, urllib.parse, urllib.request, urllib.error, xml.etree.ElementTree as ET

ACCOUNT = os.environ.get("R2_ACCOUNT_ID", "")
KEY     = os.environ.get("R2_ACCESS_KEY_ID", "")
SECRET  = os.environ.get("R2_SECRET_ACCESS_KEY", "")
BUCKET  = os.environ.get("R2_BUCKET", "ikki")
REGION  = os.environ.get("R2_REGION", "auto")
# ⚠️ endpoint ကို env နဲ့ ပြောင်းလို့ရသည် — S3/B2/MinIO နဲ့လည်း တွဲလို့ရအောင်
ENDPOINT = os.environ.get("R2_ENDPOINT") or (
    "https://%s.r2.cloudflarestorage.com" % ACCOUNT if ACCOUNT else "")
# public / custom domain (ရှိလျှင် download ကို အဲဒီကနေ ပေးသည်)
PUBLIC = os.environ.get("R2_PUBLIC_BASE", "").rstrip("/")

def on():
    return bool(ACCOUNT and KEY and SECRET and BUCKET and ENDPOINT)

# ══ SigV4 ═════════════════════════════════════════════════
_UNRESERVED = "-_.~"

def _q(s, safe=""):
    """S3 ရဲ့ စည်းကမ်းအတိုင်း encode — urllib ရဲ့ default က "~" ကို ခြွင်းချက်
    မလုပ်သဖြင့် signature မှားနိုင်သည်。"""
    return urllib.parse.quote(str(s), safe=_UNRESERVED + safe)

# R2 က path-style (bucket ကို လမ်းကြောင်းထဲ)、S3 က virtual-hosted style。
# ⚠️ ဒီနှစ်မျိုး canonical URI ကွာသဖြင့် **လက်မှတ် မတူ** — မှားလျှင်
#    403 SignatureDoesNotMatch ပဲ ရမည်၊ အကြောင်းရင်း မပြဘူး。
PATH_STYLE = os.environ.get("R2_PATH_STYLE", "1") not in ("0", "false", "no")

def _key_path(key):
    tail = "/".join(_q(p) for p in str(key).split("/") if p != "")
    if PATH_STYLE:
        return "/" + _q(BUCKET) + ("/" + tail if tail else "")
    return "/" + tail

def _sign(k, msg):
    return hmac.new(k, msg.encode(), hashlib.sha256).digest()

def _skey(date):
    k = _sign(("AWS4" + SECRET).encode(), date)
    for p in (REGION, "s3", "aws4_request"):
        k = _sign(k, p)
    return k

def _now():
    t = datetime.datetime.now(datetime.timezone.utc)
    return t.strftime("%Y%m%dT%H%M%SZ"), t.strftime("%Y%m%d")

def _host():
    return urllib.parse.urlsplit(ENDPOINT).netloc

def _canon_q(q):
    items = []
    for k, v in q.items():
        if v is None: continue
        items.append((_q(k), _q(v)))
    items.sort()
    return "&".join(f"{k}={v}" for k, v in items)

def presign(method, key, expires=3600, query=None, headers=None):
    """query-string presigned URL — browser/worker က တိုက်ရိုက် သုံးနိုင်သည်。"""
    amz, date = _now()
    path = _key_path(key)
    sh = {"host": _host()}
    for k, v in (headers or {}).items(): sh[k.lower()] = v
    signed = ";".join(sorted(sh))
    q = dict(query or {})
    q.update({
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{KEY}/{date}/{REGION}/s3/aws4_request",
        "X-Amz-Date": amz,
        "X-Amz-Expires": str(int(expires)),
        "X-Amz-SignedHeaders": signed,
    })
    cq = _canon_q(q)
    ch = "".join(f"{k}:{sh[k]}\n" for k in sorted(sh))
    creq = f"{method}\n{path}\n{cq}\n{ch}\n{signed}\nUNSIGNED-PAYLOAD"
    sts = "\n".join(["AWS4-HMAC-SHA256", amz,
                     f"{date}/{REGION}/s3/aws4_request",
                     hashlib.sha256(creq.encode()).hexdigest()])
    sig = hmac.new(_skey(date), sts.encode(), hashlib.sha256).hexdigest()
    return f"{ENDPOINT}{path}?{cq}&X-Amz-Signature={sig}"

def call(method, key="", body=b"", query=None, headers=None, timeout=60):
    """header-auth ဖြင့် လက်မှတ်ထိုးထားသော တောင်းဆိုမှု (multipart စသည်အတွက်)。"""
    amz, date = _now()
    path = _key_path(key) if key else _key_path("")
    body = body or b""
    ph = hashlib.sha256(body).hexdigest()
    sh = {"host": _host(), "x-amz-content-sha256": ph, "x-amz-date": amz}
    for k, v in (headers or {}).items(): sh[k.lower()] = str(v)
    signed = ";".join(sorted(sh))
    cq = _canon_q(query or {})
    ch = "".join(f"{k}:{sh[k]}\n" for k in sorted(sh))
    creq = f"{method}\n{path}\n{cq}\n{ch}\n{signed}\n{ph}"
    sts = "\n".join(["AWS4-HMAC-SHA256", amz, f"{date}/{REGION}/s3/aws4_request",
                     hashlib.sha256(creq.encode()).hexdigest()])
    sig = hmac.new(_skey(date), sts.encode(), hashlib.sha256).hexdigest()
    sh["authorization"] = ("AWS4-HMAC-SHA256 "
        f"Credential={KEY}/{date}/{REGION}/s3/aws4_request, "
        f"SignedHeaders={signed}, Signature={sig}")
    url = f"{ENDPOINT}{path}" + (f"?{cq}" if cq else "")
    r = urllib.request.Request(url, data=(body if method in ("PUT","POST") else None),
                               method=method)
    for k, v in sh.items():
        if k != "host": r.add_header(k, v)
    with urllib.request.urlopen(r, timeout=timeout) as f:
        return f.status, dict(f.headers), f.read()

# ══ လွယ်ကူသော အသုံး ═══════════════════════════════════════
def put_url(key, expires=7200, ctype=None):
    return presign("PUT", key, expires,
                   query={"Content-Type": ctype} if False else None)

def get_url(key, expires=7200, filename=None):
    # ⚠️ public domain ရှိလျှင်လည်း **presigned ကို သုံးသည်** — bucket ကို
    #    public မလုပ်ထားလျှင် ဖိုင်တွေ မြင်လို့ မရစေရန်。
    q = None
    if filename:
        q = {"response-content-disposition":
             "attachment; filename=\"%s\"" % str(filename).replace('"', "")}
    return presign("GET", key, expires, query=q)

def head(key):
    try:
        st, h, _ = call("HEAD", key)
        return int(h.get("Content-Length") or 0)
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        raise

def delete(key):
    try:
        call("DELETE", key); return True
    except urllib.error.HTTPError as e:
        return e.code == 404

def _x(b, tag):
    root = ET.fromstring(b)
    ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
    el = root.find(ns + tag)
    return el.text if el is not None else None

def mpu_create(key, ctype="application/octet-stream"):
    st, h, b = call("POST", key, query={"uploads": ""}, headers={"content-type": ctype})
    return _x(b, "UploadId")

def mpu_part_url(key, upload_id, n, expires=7200):
    return presign("PUT", key, expires,
                   query={"partNumber": str(int(n)), "uploadId": upload_id})

def mpu_list_parts(key, upload_id):
    """Return R2's authoritative multipart parts, not browser memory.

    A renderer crash loses JavaScript state but does not necessarily lose the
    already-uploaded R2 parts.  ListParts is therefore the only safe resume
    source: never guess from the old progress bar or from a client claim.
    """
    _, _, body = call("GET", key, query={"uploadId": upload_id, "max-parts": "1000"})
    root = ET.fromstring(body)
    parts = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "Part":
            continue
        values = {}
        for child in node:
            values[child.tag.rsplit("}", 1)[-1]] = child.text or ""
        try:
            parts.append({"n": int(values["PartNumber"]),
                          "etag": values["ETag"].strip(),
                          "size": int(values.get("Size") or 0)})
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(parts, key=lambda p: p["n"])

def mpu_complete(key, upload_id, parts):
    """parts: [(n, etag), ...] — n အစီအစဥ်အတိုင်း"""
    def _etag(v):
        v = str(v).strip()
        return v if v.startswith('"') and v.endswith('"') else '"' + v + '"'
    xml = "<CompleteMultipartUpload>" + "".join(
        f"<Part><PartNumber>{int(n)}</PartNumber><ETag>{_etag(e)}</ETag></Part>"
        for n, e in sorted(parts, key=lambda p: int(p[0]))) + "</CompleteMultipartUpload>"
    st, h, b = call("POST", key, body=xml.encode(),
                    query={"uploadId": upload_id}, headers={"content-type": "application/xml"})
    return True

def mpu_abort(key, upload_id):
    try:
        call("DELETE", key, query={"uploadId": upload_id}); return True
    except urllib.error.HTTPError:
        return False

def put_bytes(key, data, ctype="application/octet-stream"):
    call("PUT", key, body=data, headers={"content-type": ctype}, timeout=600)
    return key
