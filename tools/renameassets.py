#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset ဖိုင်အမည်များကို **စနစ်တကျ** ပြောင်းသည် — ကိုးကားမှု အားလုံးပါ ပြင်။

    python3 tools/renameassets.py plan     # ဘာဖြစ်မလဲ ပြရုံ
    python3 tools/renameassets.py apply

⚠️ ဖိုင်အမည် ပြောင်းရုံနဲ့ **မလုံလောက်** — မပြင်လျှင် ပျက်မည့်နေရာ ၄ ခု:
     ၁။ motionkit `assets/stock/catalog.json`   (file လမ်းကြောင်း)
     ၂။ IKKI `assets/broll/index.json`          (path — B-roll လုံးဝ ပျက်မည်)
     ၃။ preview `stock/` proxy + manifest       (gallery ကွက်လပ် ဖြစ်မည်)
     ၄။ mixkit ရဲ့ role flat link               (hard link — ပြန်ဖန်တီးရမည်)
⚠️ ရှိပြီးသား နာမည်နဲ့ တိုက်မိလျှင် **မရေးရ** — အရင်ဖိုင် ပျောက်မည်。
"""
import json, os, re, shutil, sys, subprocess

MK   = os.environ.get("IKKI_MOTIONKIT",
       "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")
IKKI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE  = os.path.expanduser("~/Downloads/motionkit_preview")

# style → တိုတောင်းသော ကုဒ် (IKKI edit style နဲ့ တိုက်ရိုက် ချိတ်)
# ⚠️ IKKI ရဲ့ UI စာရင်းအတိုင်း အတိအကျ (၁၀ ခု) — `headtop_motion` ဖယ်ပြီး
#    `talking_head_motion` ထဲ ပေါင်းထားသည်。
STYLE = {"cinematic_vlog":"CINE","vlog":"VLOG","podcast":"POD",
         "knowledge_sharing":"KNOW","talking_head_motion":"TALK",
         "short_video":"SHORT","promotional":"PROMO","brand_review":"BRAND",
         "business_short":"BIZ","course":"COURSE",
         "animation":"ANIM","animation_v":"ANIM-V"}
MOOD  = {"ambient_cine":"AMBIENT","lofi_chill":"LOFI","corporate":"CORP","piano":"PIANO",
         "epic":"EPIC","dark":"DARK","electronic":"ELEC","acoustic":"ACOUSTIC","folk":"FOLK"}


def probe(p, keys="stream=width,height:format=duration"):
    o = subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
                        "-show_entries",keys,"-of","json",p],
                       capture_output=True, text=True).stdout
    try:
        j = json.loads(o); s = (j.get("streams") or [{}])[0]
        return int(s.get("width") or 0), int(s.get("height") or 0), float(j["format"]["duration"])
    except Exception:
        return 0, 0, 0.0


def plan_stock():
    """[(မူရင်း, အသစ်)] — `<STYLE>-<seq>_<res>_<dur>s.mp4`"""
    D = os.path.join(MK, "assets", "stock"); out = []
    for st in sorted(os.listdir(D)):
        d = os.path.join(D, st)
        if not os.path.isdir(d) or st.startswith("."): continue
        code = STYLE.get(st, st.upper()[:6])
        fs = sorted(f for f in os.listdir(d) if f.endswith(".mp4") and not f.startswith("."))
        for i, f in enumerate(fs, 1):
            p = os.path.join(d, f)
            if re.match(rf"^{re.escape(code)}-\d{{3}}_", f): continue      # ပြောင်းပြီးသား
            w, h, sec = probe(p)
            res = f"{h}p" if h else "na"
            new = f"{code}-{i:03d}_{res}_{int(round(sec))}s.mp4"
            if new != f: out.append((p, os.path.join(d, new)))
    return out


def plan_music():
    D = os.path.join(MK, "assets", "music", "cc0_2026"); out = []
    if not os.path.isdir(D): return out
    for mo in sorted(os.listdir(D)):
        d = os.path.join(D, mo)
        if not os.path.isdir(d) or mo.startswith("."): continue
        code = MOOD.get(mo, mo.upper()[:6])
        fs = sorted(f for f in os.listdir(d) if f.endswith(".m4a") and not f.startswith("."))
        for i, f in enumerate(fs, 1):
            if re.match(rf"^{re.escape(code)}-\d{{3}}_", f): continue
            p = os.path.join(d, f)
            sec = probe(p, "format=duration")[2]
            new = f"{code}-{i:03d}_{int(round(sec))}s.m4a"
            if new != f: out.append((p, os.path.join(d, new)))
    return out


def plan_mixkit():
    D = os.path.join(MK, "assets", "sfx", "mixkit_free"); out = []
    if not os.path.isdir(D): return out
    for cat in sorted(os.listdir(D)):
        d = os.path.join(D, cat)
        if not os.path.isdir(d) or cat.startswith("."): continue
        code = cat.upper().replace("-", "_")
        fs = sorted(f for f in os.listdir(d) if f.endswith(".mp3") and not f.startswith("."))
        for i, f in enumerate(fs, 1):
            if re.match(rf"^{re.escape(code)}-\d{{3}}\.", f): continue
            out.append((os.path.join(d, f), os.path.join(d, f"{code}-{i:03d}.mp3")))
    return out


def apply(pairs):
    done = {}
    for old, new in pairs:
        if old == new or not os.path.exists(old): continue
        if os.path.exists(new):                    # ⚠️ တိုက်မိလျှင် မရေးရ
            print(f"  ⚠️ ရှိနှင့်ပြီး — ကျော်: {os.path.basename(new)}"); continue
        os.rename(old, new); done[old] = new
    return done


def fix_refs(done):
    """ကိုးကားမှု အားလုံး ပြင် — မပြင်လျှင် B-roll · gallery ပျက်မည်。"""
    n = 0
    # ၁+၂။ JSON ထဲက လမ်းကြောင်းများ
    for jp in (os.path.join(MK, "assets", "stock", "catalog.json"),
               os.path.join(IKKI, "assets", "broll", "index.json"),
               os.path.join(MK, "assets", "music", "cc0_2026", "catalog.json")):
        if not os.path.exists(jp): continue
        try: txt = open(jp, encoding="utf-8").read()
        except Exception: continue
        before = txt
        for old, new in done.items():
            if old in txt: txt = txt.replace(old, new)
            ob, nb = os.path.basename(old), os.path.basename(new)
            if ob in txt: txt = txt.replace(ob, nb)
        if txt != before:
            open(jp, "w", encoding="utf-8").write(txt); n += 1
            print(f"  ✓ ပြင်ပြီး {os.path.relpath(jp, os.path.dirname(MK))}")
    return n


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "plan"
    which = set(sys.argv[2:]) or {"stock", "music", "mixkit"}
    pairs = []
    if "stock"  in which: pairs += plan_stock()
    if "music"  in which: pairs += plan_music()
    if "mixkit" in which: pairs += plan_mixkit()
    print(f"ပြောင်းမည့် ဖိုင် {len(pairs)} ခု")
    for old, new in pairs[:6]:
        print(f"  {os.path.basename(old):28s} → {os.path.basename(new)}")
    if mode != "apply":
        print("PLANDONE — တကယ် ပြောင်းရန် `apply`"); return
    done = apply(pairs)
    print(f"ပြောင်းပြီး {len(done)} ခု")
    fix_refs(done)
    print(f"RENAMEDONE {len(done)}")


if __name__ == "__main__":
    main()
