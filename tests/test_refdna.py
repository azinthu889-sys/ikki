# -*- coding: utf-8 -*-
"""Reference **Style DNA** — တိုင်းချက် · label · **ဘောင်ခံ** apply。

⚠️ Zin ၂၀၂၆-၀၉-၂၁: 「လမ်းကြောင်းသာ · ပုံတူ မဟုတ်」 ·
   「Unknown must remain unknown」 · 「ဂိတ် မလျှော့ရ」。
⚠️ reference က brand · format · မြန်မာစာ ဖတ်ရလွယ်မှု · LUFS · အတည်ပြုပြီးသော
   ဖြတ်ချက် တွေကို **ဘယ်တော့မှ မထိရ**。
⚠️ numpy/ffmpeg မရှိလျှင် ကျော်သည်。
"""
import os, sys, subprocess, tempfile

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))
try:
    import numpy  # noqa: F401
except ImportError:
    print("  ⊘ numpy မရှိ — ကျော်သည်"); sys.exit(0)
import refdna as RD
import recipes as RC

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

BASE = RC.get("knowledge")

print("── ① မသိတာက **unknown** ဖြစ်နေရမည် ──")
empty = RD.labels({})
for k in ("pace", "cut", "captions", "motion", "graphics", "broll", "audio", "music"):
    ck(f"{k} = unknown", empty.get(k) == RD.UNK, empty.get(k))
ck("confidence = 0", empty.get("confidence") == 0.0, empty.get("confidence"))
ck("ဂရပ်ဖစ်က **အမြဲ** unknown (စာတန်း/B-roll နဲ့ ခွဲလို့ မရ)",
   RD.labels({"probe": {}, "audio": {"speak_ratio": .7, "lufs": -16},
              "shots": {"per_min": 10}, "motion": 0.02})["graphics"] == RD.UNK)

print("\n── ② မသိလျှင် override **မလုပ်ရ** ──")
ov, nt = RD.apply_to(empty, BASE)
ck("override ဗလာ", ov == {}, ov)
ck("အကြောင်းရင်း ပါ", len(nt) >= 4, nt)

print("\n── ③ ဘောင်ခံ apply — ခွင့်ပြုသော key သာ ──")
full = dict(pace="fast", cut="tight", captions="frequent", motion="dynamic",
            broll="high", audio="energetic", music="unlikely", aspect="9:16",
            confidence=1.0,
            _conf={"pace": .9, "cut": .9, "captions": .9, "motion": .9,
                   "broll": .9, "audio": .9, "music": .9})
ov, nt = RD.apply_to(full, BASE, fmt="9:16")
ck("key အားလုံး ALLOW ထဲ", all(k in RD.ALLOW for k in ov), ov)
for bad in ("brand_id", "fmt", "font", "cap", "cap_pct", "cap_base", "lufs",
            "mmf", "latin", "captions", "_spans", "_cuthash"):
    ck(f"«{bad}» မပါ", bad not in ov)
ck("ဖြတ်ချက် အထိမခံမှု ပါလာ (cut choice)", ov.get("cut") in RC.CUTS, ov.get("cut"))
ck("Motion Kit profile က အထွေထွေသာ",
   ov.get("motionkit_profile") in RC.BOUNDS["motionkit_profile"][1], ov.get("motionkit_profile"))
_r = RC.apply("knowledge", dict(ov))
ck("**မြန်မာစာ အရွယ် မထိ**", _r.get("cap_pct") == BASE.get("cap_pct"),
   (_r.get("cap_pct"), BASE.get("cap_pct")))
ck("**LUFS ဂိတ် မထိ**", _r.get("lufs") == BASE.get("lufs"))
ck("**စာတန်း နေရာ မထိ**", _r.get("cap_base") == BASE.get("cap_base"))
ck("ဖောင့် မထိ", _r.get("mmf") == BASE.get("mmf"))
ck("zoom က ZOOM ဘောင်အတွင်း",
   0 <= float(_r.get("zoom_amt") or 0) <= RC.BOUNDS["zoom_amt"][2], _r.get("zoom_amt"))

print("\n── ④ 「captions off」ဆိုလည်း **စာတန်း မဖြုတ်ရ** ──")
off = dict(full, captions="off")
ov2, nt2 = RD.apply_to(off, BASE, fmt="9:16")
ck("cap_cover > 0 (အနည်းဆုံးသာ)", float(ov2.get("cap_cover") or 0) > 0, ov2.get("cap_cover"))
ck("အကြောင်းရင်း ပြောထား", any("ဖတ်ရလွယ်" in x for x in nt2), nt2)

print("\n── ⑤ ယုံကြည်မှု နိမ့်လျှင် IKKI ပုံသေ ──")
low = dict(full, _conf={k: 0.2 for k in full.get("_conf", {})})
ov3, nt3 = RD.apply_to(low, BASE)
ck("override ဗလာ (music မပါ)",
   all(k == "music" for k in ov3) or ov3 == {}, ov3)
ck("ယုံကြည်မှု နိမ့်ကြောင်း ပြောထား",
   any("ယုံကြည်မှု" in x for x in nt3), nt3)

print("\n── ⑥ သုံးစွဲသူ ရွေးချက်က **အထက်တန်း** ──")
# ⚠️ worker မှာ စစ်သည် — ဒီမှာ apply_to ရဲ့ ထွက်ချက်ကို လွှမ်းနိုင်ကြောင်း
_user = {"zoom_amt": 0.02}
_merged = dict(_user)
for k, v in ov.items():
    if k not in _user: _merged[k] = v
ck("သုံးစွဲသူ zoom ကျန်", _merged["zoom_amt"] == 0.02)

print("\n── ⑦ compat — ပုံတူ ဟု ဘယ်တော့မှ မဆိုရ ──")
st, why, en = RD.compat(full, fmt="16:9")
ck("အချိုး မတူ ⇒ adapted", st == "adapted", st)
ck("အကြောင်းရင်း မြန်မာ ပါ", bool(why) and len(why) > 10)
ck("အကြောင်းရင်း အင်္ဂလိပ် ပါ", bool(en))
ck("အချိုး တူ ⇒ compatible", RD.compat(full, fmt="9:16")[0] == "compatible")
ck("ယုံကြည်မှု နိမ့် ⇒ unsuitable",
   RD.compat(dict(full, confidence=0.2))[0] == "unsuitable")
ck("အချိုး မသိ ⇒ adapted",
   RD.compat(dict(full, aspect=RD.UNK), fmt="9:16")[0] == "adapted")

print("\n── ⑧ အပိုင်း ကန့်သတ်ချက် ──")
ck("RANGE_MIN = 15s", RD.RANGE_MIN == 15.0)
ck("RANGE_MAX = 180s (၃ မိနစ်)", RD.RANGE_MAX == 180.0)

print("\n── ⑨ တကယ့် clip နဲ့ တိုင်းချက် ──")
if not subprocess.run(["which", "ffmpeg"], capture_output=True).stdout:
    print("  ⊘ ffmpeg မရှိ — ကျော်သည်")
else:
    T = tempfile.mkdtemp(prefix="refdna_t_")
    cap = os.path.join(T, "cap.mp4")
    plain = os.path.join(T, "plain.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "testsrc2=size=640x360:rate=24:duration=20",
                    "-vf", "drawbox=y=ih*0.80:h=ih*0.10:w=iw*0.6:x=iw*0.2:"
                           "color=white@0.9:t=fill",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "32",
                    "-an", cap], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=navy:size=640x360:rate=24:duration=20",
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "34",
                    "-an", plain], check=True)
    p1 = RD.probe(cap)
    ck("probe အချိုး 16:9", p1.get("aspect") == "16:9", p1)
    ck("probe ကြာချိန် ≈20s", abs((p1.get("dur") or 0) - 20) < 1.5, p1.get("dur"))
    c1 = RD.band_text(cap)
    c2 = RD.band_text(plain)
    # ⚠️ ဤ တိုင်းချက်က resolution/ကြာချိန် အပေါ် မူတည်သည် ⇒ **「မရှိ」ဟု
    #    မှားပြခြင်း က အဆိုးဆုံး**。 ရှိသည် (True) ဒါမှမဟုတ် မရေရာ (None)
    #    ဖြစ်ရမည် — False **မဖြစ်ရ**。
    ck("စာတန်း ပါသော clip ⇒ «မရှိ» ဟု မမှားပြ",
       bool(c1) and c1.get("present") is not False, c1)
    ck("ဗလာ clip ⇒ present False (ရှင်းရှင်း)",
       bool(c2) and c2.get("present") is False, c2)
    ck("မရေရာလျှင် အကြောင်းရင်း ပါ",
       c1.get("present") is not None or bool(c1.get("why")), c1)
    ck("စာတန်း **စာသား မဖတ်ပါ** (key မရှိ)",
       not any(k in (c1 or {}) for k in ("text", "ocr", "words")), list(c1 or {}))
    ck("လှုပ်ရှားမှု — testsrc > ဗလာ",
       (RD.motion(cap) or 0) > (RD.motion(plain) or 0))
    import shutil; shutil.rmtree(T, ignore_errors=True)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
