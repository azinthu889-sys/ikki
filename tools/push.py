#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI tools · စက်ထဲက ဖိုင်ကို တင်ပြီး job ဖွင့်ခြင်း。

browser ကနေ GB အများကြီး ဆွဲတင်ရတာ ခက်သဖြင့် — ဒီကနေ တန်းတင်နိုင်သည်。
R2 mode ဖြစ်လျှင် presigned multipart နဲ့ **R2 ကို တိုက်ရိုက်** တင်သည်
(VPS မဖြတ်ဘူး)。

    python3 tools/push.py video.mp4 --recipe knowledge --brand zjl --title "…"

⚠️ 4K/PCM ဖိုင်ကြီးကို တိုက်ရိုက် မတင်သင့် — 1080p master အရင် ထုတ်ပါ。
   worker ကလည်း 1080p proxy ပြန်လုပ်မှာမို့ အရည်အသွေး မကျပါ。
"""
import argparse, hashlib, json, os, sys, time
import urllib.request, urllib.error

API = os.environ.get("IKKI_API", "https://ikki.srv1866621.hstgr.cloud")
UT  = os.environ.get("IKKI_USER_TOKEN", "")


def req(method, path, body=None, ctype="application/json"):
    d = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=d, method=method)
    r.add_header("Authorization", "Bearer " + UT)
    if d: r.add_header("Content-Type", ctype)
    with urllib.request.urlopen(r, timeout=120) as f:
        return json.loads(f.read() or b"{}")


def put_part(url, chunk):
    """presigned PUT — ETag ကို **header ကနေ** ဖတ်ရသည်。"""
    r = urllib.request.Request(url, data=chunk, method="PUT")
    with urllib.request.urlopen(r, timeout=600) as f:
        et = f.headers.get("ETag") or f.headers.get("etag")
    if not et:
        raise RuntimeError("ETag မရ — bucket CORS မှာ ExposeHeaders ထည့်ပါ")
    return et.strip('"')


def bar(done, total, t0):
    pc = done / total if total else 0
    el = time.time() - t0
    sp = done / el / 1e6 if el > 0 else 0
    eta = (total - done) / (done / el) if done and el > 0 else 0
    sys.stdout.write(f"\r  [{'█'*int(pc*28):<28}] {pc*100:5.1f}%  "
                     f"{done/1e6:7.1f}/{total/1e6:.0f} MB  {sp:5.1f} MB/s  "
                     f"ကျန် {eta/60:4.1f} မိနစ်   ")
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--recipe", default="knowledge")
    ap.add_argument("--brand", default="zjl")
    ap.add_argument("--title", default="")
    ap.add_argument("--fmt", default="")
    ap.add_argument("--cap", default="")
    ap.add_argument("--font", default="")
    ap.add_argument("--no-job", action="store_true", help="တင်ရုံ — job မဖွင့်")
    a = ap.parse_args()
    if not UT:
        raise SystemExit("IKKI_USER_TOKEN env မရှိ")
    path = a.file
    if not os.path.exists(path): raise SystemExit(f"ဖိုင် မတွေ့: {path}")
    size = os.path.getsize(path)
    name = os.path.basename(path)
    print(f"  {name} · {size/1e6:.0f} MB → {API}")

    ini = req("POST", "/api/upload/init", {"name": name, "size": size})
    uid, mode = ini["upload_id"], ini.get("mode", "local")
    # ⚠️ R2 multipart က part တစ်ခုလျှင် အနည်းဆုံး ၅ MB လိုသည် (နောက်ဆုံး
    #    part မှလွဲ၍)。 ဒါပေမယ့် part အရေအတွက်က ၁၀၀၀၀ ထက် မကျော်ရ ⇒
    #    ဖိုင်ကြီးလျှင် chunk ကို တင်ပေးရသည်。
    chunk = max(int(ini.get("chunk", 8 << 20)), (size // 9000) + 1)
    print(f"  mode={mode} · upload={uid} · chunk={chunk/1e6:.0f} MB")

    t0 = time.time(); done = 0
    try:
        if mode == "r2":
            parts, n = [], 1
            with open(path, "rb") as f:
                while True:
                    buf = f.read(chunk)
                    if not buf: break
                    url = req("POST", f"/api/upload/{uid}/part?n={n}")["url"]
                    parts.append({"n": n, "etag": put_part(url, buf)})
                    done += len(buf); n += 1
                    bar(done, size, t0)
            print()
            r = req("POST", f"/api/upload/{uid}/complete", {"parts": parts})
        else:
            with open(path, "rb") as f:
                while True:
                    buf = f.read(chunk)
                    if not buf: break
                    rq = urllib.request.Request(
                        f"{API}/api/upload/{uid}/chunk?offset={done}", data=buf, method="PUT")
                    rq.add_header("Authorization", "Bearer " + UT)
                    rq.add_header("Content-Type", "application/octet-stream")
                    with urllib.request.urlopen(rq, timeout=600) as fh: fh.read()
                    done += len(buf)
                    bar(done, size, t0)
            print()
            r = {"done": True}
    except KeyboardInterrupt:
        req("POST", f"/api/upload/{uid}/abort"); raise SystemExit("\n  ရပ်လိုက်သည်")
    print(f"  တင်ပြီး · {time.time()-t0:.0f}s · {r}")
    if a.no_job: return

    body = {"upload_id": uid, "brand_id": a.brand, "recipe": a.recipe,
            "title": a.title or os.path.splitext(name)[0]}
    for k in ("fmt", "cap", "font"):
        if getattr(a, k): body[k] = getattr(a, k)
    j = req("POST", "/api/jobs", body)
    print(f"  job: {j['job_id']}  ({a.recipe} · {a.brand})")
    print(f"  {API}/#job/{j['job_id']}")


if __name__ == "__main__":
    main()
