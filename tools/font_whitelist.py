#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-renderer font whitelist — which picker fonts really render, and where.

Zin, 2026-09-26: "render the chosen font, or refuse — never substitute
silently", and "⛔ no VPS until the whitelist exists".  So every font in the
picker is rendered on BOTH renderers from the SAME font file and compared:

  CoreText (Mac worker, motionkit `cttext`)
  Pango    (VPS worker image, rsvg-convert — called DIRECTLY, because
            motionkit's cttext_rsvg FONT_MAP rewrites 9 of these names to
            Noto Sans Myanmar before Pango ever sees them)

Five words with stacked consonants and reordering vowels, 120 px each.

A font passes a renderer only if
  · the renderer really used that font — CoreText: the render differs from
    a nonexistent-font render (CoreText substitutes silently); Pango: the
    container sees ONLY this one file (FONTCONFIG_FILE) and fc-match returns it
  · shaping matches: ink IoU vs the CoreText render of the same file ≥ GATE on
    every word.  Calibrated 2026-09-26 on this same test: Noto (correct on
    both) 0.80–0.86, Pyidaungsu under Pango (dotted circles) 0.15–0.20.
  · and a person has looked at the sheet (IoU alone lied once already: across
    different faces it measures design, not shaping).

CoreText itself is the reference, so its own pass = "used, not substituted,
not blank".

Writes api/fonts_render.json (read by API + worker), reports/fonts_mac.txt,
reports/fonts_vps.txt and reports/fonts_sheet.png.

    python3 tools/font_whitelist.py            # needs ssh to the VPS
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "core"))
import fonts as FN                                        # noqa: E402

WORDS = ["ကျွန်တော်", "ကြိုဆို", "ဖြစ်ပါတယ်", "ကျောင်း", "လျှောက်"]
SIZE = 120
GATE = 0.70
VPS = "root@srv1866621.hstgr.cloud"
IMAGE = "ikki-ikki-worker"
OUT_JSON = os.path.join(ROOT, "api", "fonts_render.json")
REP = os.path.join(ROOT, "reports")


def measure_ids():
    """the picker fonts PLUS every Burmese font a recipe, theme or the cine
    engine uses.  ⚠️ picker-only missed `promotional` (mmf "NotoSansMyanmar",
    not a picker id), so the guard never checked it (TH session, 2026-09-26)."""
    ids = list(FN.IDS)
    try:
        import recipes as R
        for k in R.R:
            v = (R.get(k) or {}).get("mmf")
            if v and v not in ids: ids.append(v)
    except Exception as e:
        print("⚠️ recipes:", e)
    try:
        sys.path.insert(0, FN.MK); import theme as T
        for tid in list(getattr(T, "THEMES", {}) or {}):
            T.use(tid); v = T.t().get("MMF")
            if v and v not in ids: ids.append(v)
    except Exception as e:
        print("⚠️ themes:", e)
    src = open(os.path.join(ROOT, "worker", "run.py"), encoding="utf-8").read()
    m = re.search(r'CINE_FONTS = \{"my": "([^"]+)"', src)
    if m and m.group(1) not in ids: ids.append(m.group(1))
    return ids


def ct(text, font, out):
    sp = dict(text=text, font=font, fallback="Figtree", size=SIZE, w=900, h=300,
              fill="#FFFFFF", unit="cluster", align="center",
              frames=[{"out": out, "words": []}])
    r = subprocess.run([os.path.join(FN.MK, "cttext")], input=json.dumps(sp).encode(),
                       capture_output=True)
    return r.returncode == 0 and os.path.exists(out)


def files_for(ps):
    out = subprocess.run(["fc-list", ":", "postscriptname", "file"], capture_output=True,
                         text=True).stdout
    return sorted({ln.split(": ")[0] for ln in out.splitlines()
                   if re.search(rf"postscriptname={re.escape(ps)}$", ln.strip())})


def scan(path):
    # ⚠️ a collection file prints one record per face — take the first
    out = subprocess.run(["fc-scan", "--format", "%{family[0]}|%{style[0]}\n", path],
                         capture_output=True, text=True).stdout.splitlines()
    fam, style = (out[0].split("|") + [""])[:2] if out else ("", "")
    return fam.strip(), style.strip()


def weight(style):
    s = style.lower()
    return 900 if "black" in s or "heavy" in s else 700 if "bold" in s else \
        300 if "light" in s else 400


def ink(p):
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(p).convert("RGBA"))[:, :, 3]
    ys, xs = np.nonzero(a > 40)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else None


def iou(a, b):
    import numpy as np
    from PIL import Image
    if a is None or b is None:
        return 0.0
    bb = np.asarray(Image.fromarray(b).resize((a.shape[1], a.shape[0]), Image.BILINEAR))
    A, B = a > 128, bb > 128
    return float((A & B).sum() / max(1, (A | B).sum()))


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


PROV_JSON = os.path.join(ROOT, "api", "fonts_render.prov.json")
CTPATH = os.path.join(ROOT, "tools", "ctfontpath")          # tools/ctfontpath.swift


def _fileinfo(path):
    ver = subprocess.run(["fc-scan", "--format", "%{fontversion}\n", path],
                         capture_output=True, text=True).stdout.split()
    return dict(file=path, sha256=hashlib.sha256(open(path, "rb").read()).hexdigest(),
                fontversion=int(ver[0]) if ver and ver[0].isdigit() else None,
                bytes=os.path.getsize(path))


def provenance():
    """R-G3 (Zin, 2026-09-26): the file each verdict depends on.

    Recording every file installed under a name proves nothing — CoreText
    could switch from one to another with no hash changing.  So CoreText is
    asked which file it LOADS (tools/ctfontpath: CTFontCreateWithName →
    kCTFontURLAttribute, the same call cttext.swift:53 makes); that one is
    `used`, the rest `also_present`.  A later guard compares `used.sha256`.
    """
    if not os.path.exists(CTPATH):
        subprocess.run(["swiftc", "-O", CTPATH + ".swift", "-o", CTPATH], check=True)
    res = {}
    ids = measure_ids()
    for ln in subprocess.run([CTPATH, *ids], capture_output=True, text=True,
                             check=True).stdout.splitlines():
        r = json.loads(ln)
        res[r["asked"]] = r
    out = {}
    for fid in ids:
        r = res.get(fid) or {}
        used = r.get("file") or ""
        out[fid] = dict(
            substituted=bool(r.get("substituted")), resolved_ps=r.get("resolved_ps"),
            used=_fileinfo(used) if used and os.path.exists(used) else None,
            also_present=[_fileinfo(p) for p in files_for(fid) if p != used])
    return out


def write_prov():
    """a separate .prov.json, the project convention — the result file the
    guard reads is not touched"""
    d = dict(of="api/fonts_render.json", by="tools/font_whitelist.py",
             at=int(__import__("time").time()), fonts=provenance())
    tmp = PROV_JSON + ".part"
    json.dump(d, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, PROV_JSON)
    return d


def write_json(d):
    """atomic — the worker's guard reads this file and fails closed (R-G1)"""
    tmp = OUT_JSON + ".part"
    json.dump(d, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT_JSON)


PANGO = r'''
import subprocess, sys, json
fam, wt, out = sys.argv[1], sys.argv[2], sys.argv[3]
W = WORDS_JSON
m = subprocess.run(["fc-match", "-f", "%{file}", f"{fam}:weight={wt}"],
                   capture_output=True, text=True).stdout
print("MATCH", m)
for i, t in enumerate(W):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300">'
           f'<text x="450" y="190" text-anchor="middle" font-family="{fam}" '
           f'font-weight="{wt}" font-size="{int(sys.argv[5])}" fill="#FFFFFF">{t}</text></svg>')
    open(f"{out}/{i}.svg", "w").write(svg)
    subprocess.run(["rsvg-convert", "-o", f"{out}/{i}.png", f"{out}/{i}.svg"], check=True)
'''


def pango_render(path, fam, wt, work):
    """one offline container per file; fontconfig sees ONLY that file."""
    rdir = f"/tmp/fw_{hashlib.md5(path.encode()).hexdigest()[:8]}"
    subprocess.run(["ssh", VPS, f"rm -rf {rdir} && mkdir -p {rdir}/f {rdir}/o"], check=True)
    subprocess.run(["scp", "-q", path, f"{VPS}:{rdir}/f/font.ttf"], check=True)
    conf = ('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
            '<dir>/fw</dir><cachedir>/tmp/fc</cachedir></fontconfig>')
    open("/tmp/claude-fw.conf", "w").write(conf)
    # ⚠️ the words live IN the script: passed as argv through ssh → sh -c the
    #    JSON lost its quotes and every Pango render silently produced nothing
    open("/tmp/claude-fw.py", "w").write(
        PANGO.replace("WORDS_JSON", json.dumps(WORDS, ensure_ascii=False)))
    subprocess.run(["scp", "-q", "/tmp/claude-fw.conf", f"{VPS}:{rdir}/fonts.conf"], check=True)
    subprocess.run(["scp", "-q", "/tmp/claude-fw.py", f"{VPS}:{rdir}/r.py"], check=True)
    cmd = (f"docker run --rm --network none --entrypoint sh "
           f"-e FONTCONFIG_FILE=/cfg/fonts.conf -v {rdir}/fonts.conf:/cfg/fonts.conf:ro "
           f"-v {rdir}/f:/fw:ro -v {rdir}/o:/o -v {rdir}/r.py:/r.py:ro {IMAGE} -c "
           f"\"fc-cache -f >/dev/null 2>&1; python /r.py '{fam}' {wt} /o x {SIZE}\"")
    r = subprocess.run(["ssh", VPS, cmd], capture_output=True, text=True)
    match = ""
    for ln in r.stdout.splitlines():
        if ln.startswith("MATCH"):
            match = ln[5:].strip()
    os.makedirs(work, exist_ok=True)
    subprocess.run(["scp", "-q", f"{VPS}:{rdir}/o/*.png", work + "/"])
    subprocess.run(["ssh", VPS, f"rm -rf {rdir}"])
    if not all(os.path.exists(f"{work}/{i}.png") for i in range(len(WORDS))):
        raise RuntimeError(f"Pango render produced no images for {path}: {r.stderr[-400:]}")
    return match == "/fw/font.ttf", match, r.stderr[-300:]


def main():
    if not os.path.exists(CTPATH):       # needed before the first verdict
        subprocess.run(["swiftc", "-O", CTPATH + ".swift", "-o", CTPATH], check=True)
    work = tempfile.mkdtemp(prefix="fontwl_")
    os.makedirs(REP, exist_ok=True)
    # CoreText's silent fallback, for the "was the font really used" test
    bogus = []
    for i, w in enumerate(WORDS):
        p = f"{work}/bogus_{i}.png"; ct(w, "NoSuchFont-ZZZ", p); bogus.append(md5(p))
    rows = []
    for fid in measure_ids():
        mac = [f"{work}/{fid}_mac_{i}.png" for i in range(len(WORDS))]
        ok_ct = all(ct(w, fid, p) for w, p in zip(WORDS, mac))
        subst = ok_ct and all(md5(p) == b for p, b in zip(mac, bogus))
        blank = ok_ct and any(ink(p) is None for p in mac)
        ct_pass = ok_ct and not subst and not blank
        best = None
        ct_used = (json.loads(subprocess.run([CTPATH, fid], capture_output=True, text=True)
                              .stdout or "{}").get("file")
                   if os.path.exists(CTPATH) else None)
        for path in sorted(files_for(fid), key=lambda x: x != ct_used):
            fam, style = scan(path)
            wt = weight(style)
            vdir = f"{work}/{fid}_vps_{hashlib.md5(path.encode()).hexdigest()[:6]}"
            used, match, err = pango_render(path, fam, wt, vdir)
            ious = [iou(ink(m), ink(f"{vdir}/{i}.png")) if os.path.exists(f"{vdir}/{i}.png")
                    else 0.0 for i, m in enumerate(mac)]
            cand = dict(file=path, family=fam, style=style, weight=wt, used=used,
                        ious=[round(x, 3) for x in ious], dir=vdir)
            # ⚠️ judge the file CoreText LOADS, not the best-scoring one: the
            #    first run judged Pyidaungsu on the 1.3 file (IoU 0.54) while
            #    CoreText renders 1.8.3 (IoU 0.15–0.20 under Pango)
            if path == ct_used:
                best = cand; break
            if best is None or min(ious) > min(best["ious"]):
                best = cand
        pg_pass = bool(best and best["used"] and ct_pass and min(best["ious"]) >= GATE)
        rows.append(dict(id=fid, coretext=ct_pass, ct_note=("substituted" if subst else
                         "blank" if blank else "" if ok_ct else "cttext failed"),
                         pango=pg_pass, pango_best=best))
        print(f"{fid:22} CoreText {'✓' if ct_pass else '✗'}  Pango {'✓' if pg_pass else '✗'}  "
              f"min IoU {min(best['ious']) if best else 0:.2f}  used={best and best['used']}  "
              f"{os.path.basename(best['file']) if best else ''}", flush=True)
    # sheet for the eye check
    from PIL import Image, ImageDraw
    sh = Image.new("RGB", (200 + len(WORDS) * 2 * 190, 40 + len(rows) * 90), (30, 30, 30))
    d = ImageDraw.Draw(sh)
    for r_i, r in enumerate(rows):
        y = 40 + r_i * 90
        d.text((8, y + 30), f"{r['id']}\nCT {'ok' if r['coretext'] else 'NO'} "
                            f"PG {'ok' if r['pango'] else 'NO'}", fill=(255, 220, 120))
        for i in range(len(WORDS)):
            for k, p in enumerate([f"{work}/{r['id']}_mac_{i}.png",
                                   f"{r['pango_best']['dir']}/{i}.png" if r["pango_best"] else ""]):
                if not p or not os.path.exists(p):
                    continue
                im = Image.open(p).convert("RGBA"); im.thumbnail((180, 80))
                bg = Image.new("RGB", im.size, (30, 30, 30) if k == 0 else (45, 30, 30))
                bg.paste(im, (0, 0), im)
                sh.paste(bg, (200 + (i * 2 + k) * 190, y))
    d.text((200, 10), "each word: CoreText (grey)  |  Pango same file (red-tinted)",
           fill=(200, 200, 200))
    sh.save(os.path.join(REP, "fonts_sheet.png"))
    write_json(dict(method="5 words · 120 px · same file · Pango sees only that file · "
                          f"IoU ≥ {GATE} on every word + eye check",
                   words=WORDS, gate=GATE,
                   coretext=[r["id"] for r in rows if r["coretext"]],
                   pango=[r["id"] for r in rows if r["pango"]],
                   detail=[{k: v for k, v in r.items() if k != "pango_best"} |
                           {"pango_ious": (r["pango_best"] or {}).get("ious"),
                            "pango_file": os.path.basename((r["pango_best"] or {}).get("file", "")),
                            "pango_used": (r["pango_best"] or {}).get("used")}
                           for r in rows]))
    write_prov()
    open(os.path.join(REP, "fonts_mac.txt"), "w").write(
        "\n".join(r["id"] for r in rows if r["coretext"]) + "\n")
    open(os.path.join(REP, "fonts_vps.txt"), "w").write(
        "\n".join(r["id"] for r in rows if r["pango"]) + "\n")
    print(f"\nCoreText {sum(r['coretext'] for r in rows)}/{len(rows)} · "
          f"Pango {sum(r['pango'] for r in rows)}/{len(rows)} → {OUT_JSON}")
    print(f"sheet → {os.path.join(REP, 'fonts_sheet.png')}  (look at it before trusting the list)")


if __name__ == "__main__":
    if "--provenance" in sys.argv:
        # provenance only, without re-rendering; the verdict file is untouched
        d = write_prov()
        for k, v in d["fonts"].items():
            u = v["used"] or {}
            print(f"{k:22} used {os.path.basename(u.get('file', '—')):30} "
                  f"v{u.get('fontversion')} {str(u.get('sha256'))[:12]}  "
                  f"+{len(v['also_present'])} also present"
                  + ("  ⚠️ SUBSTITUTED" if v["substituted"] else ""))
    else:
        main()
