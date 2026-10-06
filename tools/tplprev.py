#!/usr/bin/env python3
"""Template picker preview — `web/tplprev/<id>.mp4|.jpg` (256px · 3s loop · ~50KB)

Zin ၂၀၂၆-၁၀-၀၆ 「Template လဲမယ် မှာ စာနဲ့ မဟုတ်ဘဲ ပုံစံကို animation နဲ့ ပြ」。
motionkit gallery (`IKKI_GALLERY` · `<module>/<fn>.mp4`) ကနေ သေးသေး ပြန် encode。
"""
import os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, "core"))
import mkcat as MC

G = os.environ.get("IKKI_GALLERY", "/Volumes/a/Downloads-archive-20261006/motionkit_preview")
OUT = os.path.join(R, "web", "tplprev")


def one(tid):
    m, f = tid.split(".", 1)
    src = os.path.join(G, m, f + ".mp4")
    if not os.path.exists(src):
        return tid, "miss"
    o = os.path.join(OUT, tid)
    if not os.path.exists(o + ".mp4"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", "3.2", "-i", src, "-an",
                        "-vf", "fps=15,scale=256:-2:flags=lanczos", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "31", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", o + ".mp4"], check=False)
    if not os.path.exists(o + ".jpg"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.2", "-i", src, "-frames:v", "1",
                        "-vf", "scale=256:-2", "-q:v", "6", o + ".jpg"], check=False)
    return tid, "ok"


def main():
    os.makedirs(OUT, exist_ok=True)
    d = MC.build(sys.argv[1] if len(sys.argv) > 1 else "16:9")
    ids = [i["id"] for i in (d.get("items") if isinstance(d, dict) else d) if "." in i["id"]]
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(one, ids))
    ok = sum(1 for _, s in res if s == "ok")
    print(f"preview {ok}/{len(ids)} · miss {[t for t, s in res if s != 'ok']}")


if __name__ == "__main__":
    main()
