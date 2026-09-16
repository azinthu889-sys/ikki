#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI tools · ပုံငယ် backfill。

⚠️ API image မှာ ffmpeg မပါ ⇒ ပုံငယ်ကို **ဒီစက်ကနေ** ထုတ်ပြီး တင်ရသည်。
   worker ရဲ့ `post_thumb()` က render ပြီးတိုင်း လုပ်သည်; ဒီ script က
   အဲဒီ code မတိုင်ခင် ထုတ်ခဲ့သော job ဟောင်းများအတွက်。

⚠️ ဗီဒီယိုတစ်ခုလုံး **မဆွဲရ** — presigned URL ကို ffmpeg ကို တိုက်ရိုက်
   ပေးလိုက်လျှင် range request နဲ့ လိုတဲ့ အပိုင်းလေးပဲ ဆွဲသည်。
   ၇၀ MB × ၆၈ ခု = ၄.၈ GB ဆွဲစရာ မလို。

    python3 tools/thumbs.py            # မရှိသေးတာတွေ အကုန်
    python3 tools/thumbs.py --limit 5  # စမ်းကြည့်
"""
import argparse, json, os, subprocess, sys, tempfile, time
import urllib.request, urllib.error

API = os.environ.get("IKKI_API", "https://ikki.srv1866621.hstgr.cloud")
UT  = os.environ.get("IKKI_USER_TOKEN", "rTzxqhL7n-mKPoClDrXu32vdXojFNAya")
WT  = os.environ.get("IKKI_WORKER_TOKEN", "")


def get(path, tok):
    r = urllib.request.Request(API + path)
    r.add_header("Authorization", "Bearer " + tok)
    with urllib.request.urlopen(r, timeout=60) as f:
        return json.loads(f.read())


def has_thumb(jid):
    r = urllib.request.Request(f"{API}/api/jobs/{jid}/thumb?t={UT}", method="GET")
    try:
        with urllib.request.urlopen(r, timeout=30) as f:
            return len(f.read()) > 0
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


def src_url(jid):
    """/file က presigned URL သို့ 302 — redirect ကို **မလိုက်ဘဲ** လိပ်စာ ယူသည်。"""
    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    op = urllib.request.build_opener(NoRedir)
    r = urllib.request.Request(f"{API}/api/jobs/{jid}/file?t={UT}")
    try:
        with op.open(r, timeout=60) as f:
            return f.geturl()                      # local mode — တိုက်ရိုက်
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            return e.headers.get("Location")
        raise


def put_thumb(jid, path):
    raw = open(path, "rb").read()
    bnd = "----ikki" + os.urandom(8).hex()
    body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"t.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() \
           + raw + f"\r\n--{bnd}--\r\n".encode()
    r = urllib.request.Request(f"{API}/api/w/{jid}/thumb", data=body, method="POST")
    r.add_header("Authorization", "Bearer " + WT)
    r.add_header("Content-Type", f"multipart/form-data; boundary={bnd}")
    with urllib.request.urlopen(r, timeout=120) as f:
        return json.loads(f.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="ရှိပြီးသားလည်း ပြန်ထုတ်")
    a = ap.parse_args()
    if not WT:
        raise SystemExit("IKKI_WORKER_TOKEN မရှိ — plist ထဲက တန်ဖိုးကို env မှာ ထည့်ပါ")
    jobs = [j for j in get("/api/jobs", UT)["jobs"] if j.get("status") == "done"]
    print(f"  ပြီးသွားသော job {len(jobs)} ခု")
    todo = []
    for j in jobs:
        if a.force or not has_thumb(j["id"]):
            todo.append(j)
    if a.limit: todo = todo[:a.limit]
    print(f"  ပုံငယ် မရှိသေးတာ {len(todo)} ခု\n")
    ok = fail = 0
    for i, j in enumerate(todo, 1):
        jid = j["id"]
        try:
            u = src_url(jid)
            if not u: raise RuntimeError("URL မရ")
            at = max(0.5, float(j.get("out_dur") or 4) * 0.15)
            fd, p = tempfile.mkstemp(suffix=".jpg"); os.close(fd)
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.2f}",
                                "-i", u, "-frames:v", "1", "-vf", "scale=480:-2",
                                "-q:v", "5", p], capture_output=True, timeout=180)
            if r.returncode or not os.path.getsize(p):
                raise RuntimeError(r.stderr.decode()[:100] or "ffmpeg မရ")
            put_thumb(jid, p)
            os.unlink(p)
            ok += 1
            print(f"  [{i:3}/{len(todo)}] ✅ {jid}  {(j.get('title') or '')[:34]}")
        except Exception as e:
            fail += 1
            print(f"  [{i:3}/{len(todo)}] ✗ {jid}  {str(e)[:70]}")
        time.sleep(0.2)
    print(f"\n  ရပြီး {ok} · မရ {fail}")


if __name__ == "__main__":
    main()
