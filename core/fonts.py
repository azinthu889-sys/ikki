#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · မြန်မာ ဖောင့် စာရင်း。

⚠️ ဤစာရင်းက **တိုင်းစစ်ပြီးသား** — ဖောင့်တစ်ခုချင်းကို cttext နဲ့ တကယ်
   ဆွဲကြည့်ပြီး (① ink ရာခိုင်နှုန်း > 1.5% ② အကျယ် > 400px) စစ်ထားသည်。
   tofu ဒါမှမဟုတ် ဗလာ ထွက်တဲ့ ဖောင့်ကို စာရင်းထဲ မထည့်ပါ。

⚠️ ဖောင့်က **Mac worker ပေါ်မှာ** ရှိသည် — VPS မှာ မရှိ。 ဒါကြောင့် ဤစာရင်းက
   ပုံသေ ဖြစ်ရသည် (API က worker ကို မမေးနိုင်)。 ဖောင့် အသစ် တပ်လျှင်
   `python3 -c "import fonts; fonts.verify()"` ဖြင့် စစ်ပြီး ဒီထဲ ထည့်ပါ。
"""
import json, os, subprocess

MK = os.environ.get("IKKI_MOTIONKIT",
     "/Applications/my file/My bussiness/ZAE NEW　OPERATION/N8N Work Flow/n8n All Workflow/motionkit")

# (id, ပြသမည့်နာမည်, အသွင်, ဘယ်အတွက် ကောင်း)
LIST = [
 ("Pyidaungsu",          "Pyidaungsu",            "ပါးလွှာ · ရုပ်ရှင်ဆန်",   "Cinematic · Podcast"),
 ("Pyidaungsu-Bold",     "Pyidaungsu Bold",       "ထူ · ဝေးကကြည့်ရ",        "Short Video · ZAE"),
 ("MasterpieceUniRound", "Masterpiece Uni Round", "လုံးဝိုင်း · ချောမွေ့",   "ZJL house font"),
 ("MyanmarYinmar",       "Myanmar Yinmar",        "အသားရ · ခေါင်းစဉ်ဆန်",   "Vlog · ခေါင်းစဉ်"),
 ("MyanmarSansPro",      "Myanmar Sans Pro",      "ပြတ်သား · သန့်",         "Knowledge · infographic"),
 ("MyanmarHeadOne",      "Myanmar Head One",      "ခေါင်းစဉ် အသွင်",        "ZAE ခေါင်းစဉ်"),
 ("PadaukBook-Bold",     "Padauk Book Bold",      "စာအုပ်ဆန် · ဖတ်ရလွယ်",   "Course · စာရှည်"),
 ("Padauk",              "Padauk",                "ရိုးရိုး · ယုံကြည်ရ",     "Brand Review"),
 ("NotoSansMyanmar-Bold","Noto Sans Myanmar Bold","ကျယ် · corporate",       "Promotional"),
 ("MyanmarPonenyet",     "Myanmar Ponenyet",      "အခြေခံ · box/marker",    "ZJL box · marker"),
 ("MyanmarBlack",        "Myanmar Black",         "အထူဆုံး",                "စာလုံးကြီး"),
 ("MyanmarSagar",        "Myanmar Sagar",         "သေးသွယ်",                "ကြောင်းသေး"),
]
IDS = [f[0] for f in LIST]

def api():
    return [dict(id=a, name=b, look=c, good=d) for a,b,c,d in LIST]

def ok(name):
    return name in IDS

# ── per-renderer whitelist (tools/font_whitelist.py) ─────────────────────
# ⚠️ Zin, 2026-09-26: "render the chosen font, or refuse — no silent
#    substitution".  motionkit's Linux renderer (cttext_rsvg FONT_MAP) turns
#    Pyidaungsu and 8 others into Noto Sans Myanmar without a word, and
#    CoreText falls back to a system font for an unknown name.  So a worker
#    checks every Burmese font a job will use against the list MEASURED for
#    its own renderer, and refuses the job naming the font otherwise.
_RJ = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api",
                    "fonts_render.json"), "/app/api/fonts_render.json"]


def renderer():
    """'coretext' when motionkit's cttext binary will be used, else 'pango'
    (same rule motionkit/infogfx.py applies)."""
    if os.environ.get("MK_TEXT") == "rsvg":
        return "pango"
    return "coretext" if os.path.exists(os.path.join(MK, "cttext")) else "pango"


def whitelist(r=None):
    r = r or renderer()
    for p in _RJ:
        if os.path.exists(p):
            try:
                return list(json.load(open(p, encoding="utf-8")).get(r) or [])
            except Exception:
                return []
    return []          # not measured ⇒ nothing is allowed on that renderer


def allowed(name, r=None):
    return name in whitelist(r)


class FontRefused(RuntimeError):
    pass


def guard(names, log=print, r=None):
    """raise FontRefused when any Burmese font in `names` is not measured-good
    on this worker's renderer.  Non-picker names (Latin, CJK) are not checked —
    the whitelist covers the Burmese picker fonts only."""
    r = r or renderer()
    wl = whitelist(r)
    bad = [n for n in dict.fromkeys(n for n in names if n) if n in IDS and n not in wl]
    if bad:
        msg = (f"ဖောင့် {', '.join(bad)} ကို ဒီ worker ({r}) မှာ မှန်မှန်ကန်ကန် မရေးနိုင်ပါ — "
               f"တခြားဖောင့် ရွေးပါ (အစားထိုးပြီး မထုတ်ပါ) · "
               f"font {', '.join(bad)} cannot be rendered faithfully on the {r} worker")
        log(f"  ⛔ {msg}")
        raise FontRefused(msg)
    log(f"  ✓ ဖောင့် စစ်ပြီး ({r}) · {', '.join(n for n in dict.fromkeys(names) if n in IDS) or '—'}")
    return True


def verify(cand=None, text="ကျွန်တော်တို့ ဇင်ဂျပန်လိုက် — JLPT N5 · 日本語", size=64):
    """ဖောင့်တစ်ခုချင်း တကယ် ရေးတတ်လား စစ်သည် (ink% + အကျယ်)。"""
    out=[]
    for f in (cand or IDS):
        p = f"/tmp/_ft_{abs(hash(f))%99999}.png"
        sp = dict(text=text, font=f, fallback="Figtree-Black,HiraginoSans-W7",
                  size=size, w=1400, h=150, fill="#FFFFFF", unit="cluster",
                  align="center", frames=[{"out":p,"words":[]}])
        r = subprocess.run([os.path.join(MK,"cttext")], input=json.dumps(sp).encode(),
                           capture_output=True)
        if r.returncode or not os.path.exists(p):
            out.append((f, 0.0, 0, False)); continue
        a = subprocess.run(["ffmpeg","-v","error","-i",p,"-vf","alphaextract",
            "-pix_fmt","gray","-f","rawvideo","-"], capture_output=True).stdout
        ink = sum(1 for b in a if b > 40)/max(1,len(a))*100
        try:
            w = json.loads(subprocess.run([os.path.join(MK,"cttext")], input=json.dumps(
                dict(text="", font=f, fallback="Figtree-Black,HiraginoSans-W7",
                     size=size, w=10, h=10, fill="#FFF", frames=[], measure=[text])
                ).encode(), capture_output=True).stdout)[0]
        except Exception: w = 0
        os.path.exists(p) and os.remove(p)
        out.append((f, round(ink,1), w, ink > 1.5 and w > 400))
    return out

if __name__ == "__main__":
    for f, ink, w, good in verify():
        print(f"  {f:24}{ink:6.1f}%{w:7}  {'✅' if good else '❌'}")
