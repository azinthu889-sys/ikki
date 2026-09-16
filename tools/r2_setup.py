#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 bucket ကို IKKI အတွက် သတ်မှတ်ခြင်း + စမ်းသပ်ခြင်း。

    R2_ACCOUNT_ID=… R2_ACCESS_KEY_ID=… R2_SECRET_ACCESS_KEY=… R2_BUCKET=ikki \
      python3 tools/r2_setup.py

⚠️ CORS မထည့်လျှင် browser upload က **ETag ဖတ်လို့ မရ**ဘဲ ကျဘမ်း ဖြစ်မည်。
⚠️ lifecycle မထည့်လျှင် ဖိုင်တွေ အမြဲ ကျန်ပြီး storage ဖိုး တက်မည် —
   ၇၃ MB/မိနစ် နှုန်းနှင့် customer ၁၀၀ ဆို လစဥ် ၂ TB ရောက်သည် (တိုင်းထားသည်)。
"""
import os, sys, urllib.error, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
import store as ST

ORIGINS = [o for o in (os.environ.get("R2_CORS_ORIGINS") or
    "https://ikki.srv1866621.hstgr.cloud,https://app.getikki.com,http://127.0.0.1:8080"
    ).split(",") if o.strip()]
UP_DAYS  = int(os.environ.get("R2_UPLOAD_DAYS", "2"))
OUT_DAYS = int(os.environ.get("R2_OUT_DAYS", "7"))

def cors():
    rules = "".join(
        "<CORSRule>" + "".join(f"<AllowedOrigin>{o.strip()}</AllowedOrigin>" for o in ORIGINS) +
        "<AllowedMethod>PUT</AllowedMethod><AllowedMethod>GET</AllowedMethod>"
        "<AllowedMethod>HEAD</AllowedMethod>"
        "<AllowedHeader>*</AllowedHeader>"
        # ⚠️ ဒီ ExposeHeader က multipart upload အတွက် **မရှိမဖြစ်**
        "<ExposeHeader>ETag</ExposeHeader>"
        "<MaxAgeSeconds>3600</MaxAgeSeconds></CORSRule>" for _ in (1,))
    xml = f'<CORSConfiguration>{rules}</CORSConfiguration>'
    ST.call("PUT", "", body=xml.encode(), query={"cors": ""},
            headers={"content-type": "application/xml"})
    print(f"  ✓ CORS · origin {len(ORIGINS)} ခု · ExposeHeader ETag")

def lifecycle():
    xml = ("<LifecycleConfiguration>"
      f"<Rule><ID>uploads</ID><Status>Enabled</Status>"
      f"<Filter><Prefix>uploads/</Prefix></Filter>"
      f"<Expiration><Days>{UP_DAYS}</Days></Expiration>"
      f"<AbortIncompleteMultipartUpload><DaysAfterInitiation>1</DaysAfterInitiation>"
      f"</AbortIncompleteMultipartUpload></Rule>"
      f"<Rule><ID>out</ID><Status>Enabled</Status>"
      f"<Filter><Prefix>out/</Prefix></Filter>"
      f"<Expiration><Days>{OUT_DAYS}</Days></Expiration></Rule>"
      "</LifecycleConfiguration>")
    ST.call("PUT", "", body=xml.encode(), query={"lifecycle": ""},
            headers={"content-type": "application/xml"})
    print(f"  ✓ retention · uploads {UP_DAYS} ရက် · out {OUT_DAYS} ရက် · မပြီးသော MPU ၁ ရက်")

def selftest():
    k = "ikki-selftest.txt"; data = b"ikki ok"
    ST.put_bytes(k, data, "text/plain")
    sz = ST.head(k)
    assert sz == len(data), f"အရွယ် မတူ {sz}"
    with urllib.request.urlopen(ST.get_url(k, 300), timeout=30) as f:
        got = f.read()
    assert got == data, "အကြောင်းအရာ မတူ"
    print("  ✓ တင် · HEAD · presigned GET ဖြင့် ဖတ် — အားလုံး ကိုက်")
    # multipart လမ်းကြောင်းကိုပါ စမ်း (browser က သုံးမည့် လမ်း)
    mk = "ikki-selftest-mpu.bin"
    up = ST.mpu_create(mk)
    part = b"0" * (5 * 1024 * 1024)          # S3 အနိမ့်ဆုံး part = 5 MiB
    url = ST.mpu_part_url(mk, up, 1)
    r = urllib.request.Request(url, data=part, method="PUT")
    r.add_header("Content-Length", str(len(part)))
    with urllib.request.urlopen(r, timeout=300) as f:
        et = f.headers.get("ETag")
    assert et, "ETag မရ"
    ST.mpu_complete(mk, up, [(1, et)])
    assert ST.head(mk) == len(part), "multipart အရွယ် မတူ"
    print("  ✓ multipart တင် (5 MiB) · ETag · complete — အလုပ်လုပ်")
    ST.delete(k); ST.delete(mk)
    print("  ✓ ဖျက်ပြီး")

if __name__ == "__main__":
    if not ST.on():
        print("❌ R2 env မပြည့်စုံ — R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / "
              "R2_SECRET_ACCESS_KEY / R2_BUCKET လိုသည်")
        sys.exit(1)
    print(f"bucket {ST.BUCKET} · {ST.ENDPOINT}")
    warn = []
    try:
        # ⚠️ CORS/lifecycle က **bucket အဆင့် permission** လိုသည် —
        #    "Object Read & Write" token နှင့် 403 AccessDenied ရသည် (တကယ်)。
        #    ⇒ ကျဘမ်းမလုပ်ဘဲ သတိပေးပြီး object စမ်းသပ်မှုကို ဆက်လုပ်သည်。
        for fn, lbl in ((cors, "CORS"), (lifecycle, "retention")):
            try:
                fn()
            except urllib.error.HTTPError as e:
                if e.code in (403, 401):
                    e.read()
                    warn.append(lbl)
                    print(f"  ⚠️ {lbl} — token မှာ bucket permission မရှိ (dashboard မှာ လုပ်ပါ)")
                else:
                    raise
        selftest()
        if warn:
            print("\n⚠️ R2 အလုပ်လုပ်သည် — ဒါပေမဲ့ " + " နှင့် ".join(warn) +
                  " ကို dashboard မှာ သတ်မှတ်ရမည်")
            print("   R2 → ikki → Settings → CORS Policy / Object lifecycle rules")
        else:
            print("\n✅ R2 အသင့်")
    except urllib.error.HTTPError as e:
        print(f"\n❌ HTTP {e.code}\n{e.read().decode('utf-8','replace')[:600]}")
        sys.exit(1)
