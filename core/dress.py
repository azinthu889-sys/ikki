#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IKKI core · ဂရပ်ဖစ် ရွေးချယ်မှု + SFX cue。

⚠️ template ၉၀ ရှိသည် — အားလုံး တပ်လျှင် ရုပ်ဆိုးသည်。 recipe ရဲ့ `gfx`
   ကိန်းအရ **အရေအတွက် ကန့်သတ်**ပြီး တိတ်ဆိတ်မှုကြီးများ (စကားခေတ္တရပ်သည့်
   အချိန်) မှာသာ ချသည် — စကားပြောနေတုန်း ဂရပ်ဖစ် တက်လာလျှင် စာဖတ်မရ。

⚠️ ffmpeg input ကန့်သတ်ချက် — ဂရပ်ဖစ် PNG တွေကိုပါ input အဖြစ် ထည့်လျှင်
   ၁၄၀ ခန့်မှာ ပျက်သည်。 ⇒ စာတန်းလိုပဲ **alpha track တစ်ခု** ဆောက်ရမည်。
"""
import os

def pick(rc, dur, sil, segs):
    """(when, kind) စာရင်း — ဂရပ်ဖစ် ဘယ်အချိန် ဘယ်ဟာ ချမလဲ。"""
    want = int(rc.get("gfx") or 0)
    if want <= 0 or dur < 12: return []
    # ⚠️ ရှည်သော တိတ်ဆိတ်မှုမှာသာ ချသည် — စကားပြောနေတုန်း မချရ
    cand = sorted([s for s in sil if s[1]-s[0] >= 0.45], key=lambda s: -(s[1]-s[0]))
    cand = [s for s in cand if 2.0 <= s[2] <= dur-3.0]
    if not cand: return []
    # အချိန် အညီအမျှ ဖြန့် — အစုအစု မဖြစ်စေရန်
    cand.sort(key=lambda s: s[2])
    step = max(1, len(cand)//max(1,want))
    picked = cand[::step][:want]
    # ⚠️ အရင်က template **၁၂ ခု**ကို hardcode လုပ်ပြီး အလှည့်ကျ သုံးခဲ့သည် —
    #    motionkit မှာ ၂၇၆ ခု ရှိပါလျက်。 ထုတ်လာတဲ့ ဗီဒီယိုတိုင်း တစ်ပုံစံတည်း
    #    ဖြစ်စေခဲ့သည်。
    # ⚠️ ဒါပေမဲ့ **တကယ် render စမ်းပြီးသားကိုသာ** သုံးရမည် — argument ပုံစံ
    #    တစ်ခုချင်း ကွာသဖြင့် အားလုံးက အလိုအလျောက် ဖြည့်လို့ မရ。
    #    `assets/gfx_ok.txt` = တစ်ခုချင်း သီးသန့် process နဲ့ စမ်းပြီး
    #    အောင်မြင်ခဲ့သော စာရင်း (၅၉/၁၉၄)。
    KINDS = _verified() or ["headline_bar","locator","big_number","pull_quote",
             "label_pill","kicker_title","section","chapter","stat_title",
             "fact_box","list_title","topic_bar"]
    return [dict(at=round(s[2],2), kind=KINDS[i % len(KINDS)])
            for i,s in enumerate(picked)]

_VER = None
def _verified():
    """စမ်းပြီးသား template စာရင်း — id ("titles.title_card") မှ fn နာမည်သို့"""
    global _VER
    if _VER is not None: return _VER
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "assets", "gfx_ok.txt")
    out = []
    try:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or "." not in line: continue
            out.append(line.split(".", 1)[1])
    except OSError:
        pass
    # ⚠️ အလှည့်ကျ သုံးသဖြင့် စာရင်းကို **ရောရမည်** — မရောလျှင် ဗီဒီယိုတိုင်း
    #    ပထမ ၅ ခုပဲ သုံးပြီး ကွဲပြားမှု မရှိဘူး。
    import random
    random.Random(7).shuffle(out)
    _VER = out
    return _VER

# ── SFX ─────────────────────────────────────────────────────
# ⚠️ cue ကို ဂရပ်ဖစ် **အပြည့်ပေါ်တဲ့ အချိန်**နဲ့ ကိုက်ရမည်၊ စတဲ့အချိန် မဟုတ်။
#    settle ချိန်ကို နုတ်ရသည် — မနုတ်လျှင် အသံက ပုံထက် စောသည်。
SETTLE = 0.22

def sfx(gfx, caps, rc):
    """[(offset, role, dB)] — sfxlib ရဲ့ role နာမည်များ"""
    out=[]
    for g in gfx:
        out.append((max(0.0, g["at"]-SETTLE), "whoosh_in", -13))
        out.append((g["at"], "click", -16))
    # ⚠️ စာတန်းတိုင်းမှာ အသံ မထည့်ရ — Zin ရဲ့ spec: "no per-word SFX"
    if rc.get("captions") == "big" and caps:
        for c in caps[:6]:
            out.append((c["start"], "type_tick", -20))
    out.sort(key=lambda x: x[0])
    # ⚠️ playbook က style တစ်ခုချင်း **မိနစ်လျှင် ဘယ်နှစ်ချက်** သတ်မှတ်သည် —
    #    podcast ၀.၃ · ZAE short ၂၀ — ၆၀ ဆ ကွာသည်。 ကန့်သတ် မထားလျှင်
    #    ဂရပ်ဖစ် အရေအတွက်အလိုက် ပဲ ဖြစ်ပြီး ပုံစံ ကွဲမသွားဘူး。
    #    ⚠️ playbook: "SFX ကို သတိထားမိလောက်အောင် ကြားရရင် ၆ dB ကျယ်နေပြီ"
    per = rc.get("sfx_per_min")
    dur = rc.get("_dur") or 0
    if per is None or dur <= 0 or not out:
        return out

    # ⚠️ **အထပ်ကို မခွဲရ**。 whoosh_in နဲ့ click က ဂရပ်ဖစ်တစ်ခုအတွက်
    #    အသံ **တစ်ခု၏ အထပ်နှစ်ခု** ဖြစ်သည် (0.22s ကွာ)。 အရင်က စာရင်း
    #    ပြားပြားကနေ N ခုခြား ယူခဲ့သဖြင့် whoosh ကျန်ပြီး click ပျောက်တာမျိုး
    #    ဖြစ်နိုင်ခဲ့သည် — အသံက မပြည့်စုံဘဲ ထောက်နေမည်。
    LAYER_W = 0.60
    moments = []
    for c in out:
        if moments and c[0] - moments[-1][0] <= LAYER_W:
            moments[-1][1].append(c)
        else:
            moments.append((c[0], [c]))

    # ⚠️ အသံနှစ်ခု **၈ စက္ကန့်အတွင်း မရှိရ** (playbook P3 · QC gate ကလည်း
    #    ဒီအတိုင်း စစ်သည်)。 generator က မလိုက်နာလျှင် render ပြီးမှ QC မှာ
    #    ကျဘမ်း ဖြစ်ပြီး အလုပ်အားလုံး အလကား ဖြစ်သည် (တကယ် ဖြစ်ခဲ့)。
    MIN_GAP = 8.0
    keep, last = [], None
    for at, layers in moments:
        if last is None or at - last >= MIN_GAP:
            keep.append((at, layers)); last = at

    cap = max(0, int(round(float(per) * dur / 60.0)))
    if cap == 0: return []
    if len(keep) > cap:
        step = len(keep) / float(cap)
        keep = [keep[int(i * step)] for i in range(cap)]

    out = [c for _at, layers in keep for c in layers]
    out.sort(key=lambda x: x[0])
    return out

def mix(base, cues, out, cue_path, log=print):
    """SFX များကို အသံပေါ် ထပ်သည်。

    ⚠️ input ၁၄၀ ကန့်သတ်ချက် — cue များကို **အုပ်စုလိုက် ခွဲ**ပြီး ပေါင်းရသည်。
    """
    import subprocess
    ins=[]; fc=[]; k=0
    use=[]
    for at, role, db in cues:
        p = cue_path(role)
        if p and os.path.exists(p): use.append((at,p,db))
    if not use:
        subprocess.run(["ffmpeg","-v","error","-y","-i",base,"-c","copy",out],check=True)
        return out, 0
    use = use[:60]                      # ⚠️ ကန့်သတ် — ၆၀ ထက် ပို မလို
    for i,(at,p,db) in enumerate(use):
        ins += ["-i",p]; ms=int(at*1000)
        fc.append(f"[{i+1}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
                  f"volume={db}dB,adelay={ms}|{ms}[s{i}]")
    fc.append("[0:a]" + "".join(f"[s{i}]" for i in range(len(use))) +
              f"amix=inputs={len(use)+1}:normalize=0:dropout_transition=0,"
              f"alimiter=limit=0.94[a]")
    subprocess.run(["ffmpeg","-v","error","-y","-i",base]+ins+
        ["-filter_complex",";".join(fc),"-map","0:v","-map","[a]",
         "-c:v","copy","-c:a","aac","-b:a","192k",out],check=True)
    return out, len(use)


# ── ဂရပ်ဖစ် alpha track ─────────────────────────────────────
ARGS = {
 "headline_bar": lambda b,r: ("သတင်း", b),
 "locator":      lambda b,r: (b, r),
 "big_number":   lambda b,r: ("100%", b, r),
 "pull_quote":   lambda b,r: (b, r),
 "label_pill":   lambda b,r: (b,),
 "kicker_title": lambda b,r: (r, b),
 "section":      lambda b,r: (b,),
 "chapter":      lambda b,r: ("၀၁", b),
 "stat_title":   lambda b,r: ("100%", b),
 "fact_box":     lambda b,r: (b, r),
 "list_title":   lambda b,r: (b, [r, "—", "—"]),
 "topic_bar":    lambda b,r: (b,),
}

def _ybox(el, H):
    """element ရဲ့ ဒေါင်လိုက် အကွာအဝေး (alpha bbox)。"""
    y0, y1 = H, 0
    try:
        import numpy as _np
        from PIL import Image as _Im
        seq = list(el["anim"][len(el["anim"])//2:]) + \
              [(q, x, y) for q, x, y, _d in el.get("statics", [])]
        for _p, _x, _y in seq:
            _a = _np.asarray(_Im.open(_p).convert("RGBA"))[:, :, 3]
            _ys = _np.nonzero(_a.max(axis=1) > 8)[0]
            if len(_ys):
                y0 = min(y0, _y + int(_ys.min())); y1 = max(y1, _y + int(_ys.max()))
    except Exception:
        return 0, int(H*0.32)
    if y1 <= y0: return 0, int(H*0.32)
    return max(0, int(y0)), min(int(H), int(y1))


def _yparam(fn):
    """template က နေရာ ရွှေ့လို့ရသော param ရှိလား (`cy` · `y`)。"""
    import inspect
    try: ps = inspect.signature(fn).parameters
    except Exception: return None
    for k in ("cy", "y"):
        if k in ps: return k
    return None


# ⚠️ card ကျော်သွားရခြင်း အကြောင်းရင်းကို **ရေတွက်ရမည်** — "ရွေး ၈ · တပ်ပြီး ၅"
#    ဆိုပြီး ဘာလို့ ၃ ခု ပျောက်လဲ မပြနိုင်ခဲ့。 render report အတွက် ဒီမှာ စုသည်。
LAST = {}


def track(gfx, out, work, W, H, fps, T1, T2, brand, label, log=print,
          avoid=None, capy=None, hold=None):
    """ရွေးထားသော ဂရပ်ဖစ်များကို alpha overlay ဗီဒီယို **တစ်ခု** အဖြစ် ဆောက်သည်。

    ⚠️ template တစ်ခုလျှင် PNG ၈၀–၂၀၀ ရှိသည်。 အားလုံး input အဖြစ် ထည့်လျှင်
       ffmpeg ပျက်သည် ⇒ တစ်ခုချင်း အရင် alpha .mov လုပ်ပြီး concat လုပ်ရသည်。
    """
    import subprocess
    os.makedirs(work, exist_ok=True)
    blank = os.path.join(work, "_g0.png")
    subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi",
        "-i",f"color=c=black:s=16x16:d=1","-frames:v","1","-pix_fmt","rgba",blank],check=True)
    made=[]
    LAST.clear()
    LAST.update(want=len(gfx), no_template=0, build_fail=0,
                no_room=0, out_of_frame=0, overlap=0, moved=0, placed=0)
    for i,g in enumerate(gfx):
        # ⚠️ အရင်က module ၂ ခု (titles · titles2) ထဲမှာပဲ ရှာသဖြင့်
        #    typo · kinetic · callouts · infogfx ထဲက template တွေ
        #    **တိတ်တဆိတ် ပယ်ခံခဲ့ရသည်** — "ရွေး ၈ ခု · တပ်ပြီး ၂ ခု"
        #    ဆိုပြီး အကြောင်းရင်း မပြဘူး。 ⇒ catalog ကနေ ရှာသည်。
        fn = getattr(T2, g["kind"], None) or getattr(T1, g["kind"], None) or _fn(g["kind"])
        if not fn:
            LAST["no_template"] += 1
            log(f"  ⊘ template မတွေ့: {g['kind']} @ {g.get('at',0):.1f}s "
                f"(catalog {len(_CIDX or {})} ခု)")
            continue
        try:
            # ⚠️ topics.py က args ပေးလာလျှင် **အဲဒါကို** သုံးရမည် —
            #    အကြောင်းအရာနဲ့ ကိုက်တဲ့ စာသားပါ。
            # ⚠️ ARGS မှာ ၁၂ ခုပဲ ရှိ — စမ်းပြီးသား ၅၉ ခုအတွက် catalog ရဲ့
            #    signature ကနေ ဖြည့်ရမည်。 မဖြည့်ဘဲ (b,) ပေးလျှင် template
            #    အများစု ကျဘမ်း ဖြစ်မည်。
            a = g.get("args") or (ARGS[g["kind"]](brand, label)
                                  if g["kind"] in ARGS else _cargs(g["kind"], brand, label))
            # ⚠️ titles/titles2 ရဲ့ template တွေက ပထမ param အဖြစ် `tag`
            #    ယူသည်၊ typo · kinetic · callouts တွေက **မယူ**。 tag ကို
            #    အားလုံးမှာ ရှေ့က ထည့်လျှင် argument တစ်နေရာစီ ရွေ့သွားပြီး
            #    စာသားက number param ထဲ ကျသည် ("can't multiply sequence by
            #    non-int" · "invalid literal for int()" — တကယ် ဖြစ်ခဲ့)。
            el = fn(f"g{i}", *a) if _wants_tag(g["kind"]) else fn(*a)
        except Exception as e:
            LAST["build_fail"] += 1
            log(f"  ⊘ ဆောက်မရ: {g['kind']} @ {g.get('at',0):.1f}s "
                f"{type(e).__name__}: {e}"); continue
        # ⚠️ **မျက်နှာကို မဖုံးရ** — Zin: "Infography ကိုမျက်နှာကိုမဖုန်းစေနဲ့
        #    သေချာ Fitting ကျမည့်နေရာကို ရွေးပြီးလုပ်စေချင်တယ်"。
        # ⚠️ template ရဲ့ `y`/`cy` param ကို မှီခို၍ **မရ** — အများစုမှာ မရှိ။
        #    ⇒ element တစ်ခုလုံးကို **ဒေါင်လိုက် ရွှေ့**သည် (alpha overlay
        #      ဖြစ်၍ ရွှေ့လို့ ရသည်)。 N5 က ဂရပ်ဖစ်ကို ခေါင်းအထက်
        #      နံရံဗလာမှာ ချသည် ⇒ အပေါ်ကို ဦးစားပေး。
        dy = 0
        if avoid:
            ay0, ay1 = avoid
            _y0, _y1 = _ybox(el, H)
            ih = _y1 - _y0
            TOP = int(H*0.075)
            if _y1 > ay0:                       # မျက်နှာဇုန်ထဲ ဒါမှမဟုတ် အောက်
                if ih <= ay0 - TOP - 8:         # ခေါင်းအထက် ဝင်လျှင် — အပေါ်
                    dy = TOP - _y0
                elif capy and (ay1 + 16 + ih) <= capy - 12:
                    dy = (ay1 + 16) - _y0       # မဝင်လျှင် — မျက်နှာအောက်
                elif (ay1 + 16 + ih) <= H - 12:
                    dy = (ay1 + 16) - _y0
                else:
                    LAST["no_room"] += 1
                    log(f"  ⊘ နေရာ မတည့်: {g['kind']} @ {g.get('at',0):.1f}s "
                        f"(ကတ်အမြင့် {ih} · မျက်နှာဇုန် {ay0}–{ay1} · "
                        f"စာတန်းထိပ် {capy} · ဘောင်အမြင့် {H})")
                    continue
                # ဘောင်ထဲ ဝင်မဝင် စစ်
                if _y0 + dy < 0 or _y1 + dy > H:
                    LAST["out_of_frame"] += 1
                    log(f"  ⊘ ဘောင်ကျော်: {g['kind']} @ {g.get('at',0):.1f}s "
                        f"(y {_y0+dy}–{_y1+dy} · dy={dy} · ဘောင် {W}×{H})")
                    continue
        seq = os.path.join(work, f"g{i}_%04d.png")
        # ⚠️ os.link က filesystem ကွဲလျှင် ပျက်သည် — copy ဖြင့် ပြန်ဆုတ်ရမည်
        import shutil as _sh
        for k,(p,x,y) in enumerate(el["anim"]):
            dst = seq % k
            if os.path.exists(dst): continue
            try: os.link(p, dst)
            except OSError: _sh.copyfile(p, dst)
        ax, ay = el["anim"][0][1], el["anim"][0][2] + dy
        ins=["-framerate",str(fps),"-i",seq]
        fc=[f"[0:v]pad={W}:{H}:{ax}:{max(0,ay)}:color=black@0[b0]"]; last="b0"; n=0
        for p,x,y,d in el["statics"]:
            ins += ["-loop","1","-i",p]; n+=1
            fc.append(f"[{last}][{n}:v]overlay={x}:{y+dy}:enable='gte(t,{d:.2f})'[b{n}]")
            last=f"b{n}"
        y0, y1 = _ybox(el, H); y0 += dy; y1 += dy
        mov = os.path.join(work, f"g{i}.mov")
        # ⚠️ ကတ်ကို **ကြာကြာ ရပ်စေရန်** — template ရဲ့ ကိုယ်ပိုင် အရှည်က
        #    ~၂.၂s ပဲ ရှိသည်。 reference ရဲ့ full-screen slide က ကြာကြာ
        #    ရပ်နေသဖြင့် gfx_share ၁၃–၁၄% ရသည် — ကတ် ၂.၂s တွေ အများကြီး
        #    လျှပ်တပြက် ပြ၍ မရ (၅၄ ခု လိုမည်、ပုံစံ လုံးဝ ကွဲသွားမည်)。
        #    ⇒ နောက်ဆုံး frame ကို `tpad` နဲ့ ဆွဲထားသည်。
        gdur = float(el["dur"])
        fc2 = list(fc); last2 = last
        if hold and hold > gdur + 0.05:
            fc2.append(f"[{last2}]tpad=stop_mode=clone:"
                       f"stop_duration={hold-gdur:.2f}[hp]")
            last2 = "hp"; gdur = float(hold)
        try:
            subprocess.run(["ffmpeg","-v","error","-y"]+ins+["-filter_complex",";".join(fc2),
                "-map",f"[{last2}]","-t",f"{gdur:.2f}","-r",str(fps),
                "-c:v","qtrle","-pix_fmt","argb",mov],check=True)
            made.append((g["at"], mov, gdur, bool(g.get("fixed")),
                         max(0,int(y0)), min(int(H),int(y1))))
        except subprocess.CalledProcessError as e:
            log(f"  ⚠️ {g['kind']} render မရ")
    if not made: return None, 0
    # ⚠️ **မရွှေ့ရသူကို အရင် နေရာချ**ရမည် — typography က စကားလုံးနဲ့
    #    ချိတ်ထားသည်。 အချိန်အလိုက်သာ စဉ်ပြီး ရှေ့ကလာသူကို ဦးစားပေးလျှင်
    #    ခေါင်းစဉ်ဂရပ်ဖစ်က typography ကို ဖယ်ပစ်သည် (v24 မှာ ၈ ခုထဲ ၃ ခု
    #    ပျောက်ခဲ့သည်)。
    made.sort(key=lambda x: (0 if x[3] else 1, x[0]))
    placed=[]                                   # (start, end) — ယူပြီးသား
    def _free(a, b):
        return all(b <= x or a >= y for x, y in placed)
    # ⚠️ ထပ်နေသော ဂရပ်ဖစ် မရှိစေရ — နောက်ဟာက ရှေ့ဟာ ပြီးမှ စရမည်。
    # ⚠️ ဒါပေမဲ့ ထပ်နေရုံနဲ့ **တိတ်တဆိတ် မဖျက်ရ** — ZAE short မှာ ရွေး ၈ ခု
    #    ထဲက ၄ ခု ဒီနေရာမှာ ပျောက်သွားပြီး Zin က "အရုပ်တွေ ပျောက်သွားတယ်"
    #    ဟု ပြောခဲ့သည် (တကယ်)。 ⇒ အနည်းငယ် ရွှေ့၍ ရလျှင် ရွှေ့ရမည်၊
    #    တကယ် မရမှ ဖျက်ပြီး **အကြောင်းရင်း ပြရ**မည်。
    keep=[]; moved=0; dropped=[]
    for at,mov,d,fixed,y0,y1 in made:
        if not _free(at-0.2, at+d+0.2):
            if fixed:                             # မရွှေ့ရ — ဖျက်ရုံသာ
                dropped.append(round(at,1)); continue
            for step in (0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, -0.5, -1.0, -1.5):
                if _free(at+step-0.2, at+step+d+0.2):
                    at = round(at+step, 2); moved += 1; break
            else:
                dropped.append(round(at,1)); continue
        keep.append((at,mov,d,y0,y1)); placed.append((at-0.2, at+d+0.2))
    keep.sort(key=lambda x: x[0])
    LAST["overlap"] = len(dropped); LAST["moved"] = moved; LAST["placed"] = len(keep)
    if moved:   log(f"  ဂရပ်ဖစ် {moved} ခု ထပ်နေ၍ ရွှေ့လိုက်သည်")
    if dropped: log(f"  ⊘ ထပ်နေ၍ ဖျက် {len(dropped)} ခု (ရွှေ့၍ မရ): {dropped}")
    return keep, len(keep)


_CIDX = None
def _cargs(kind, brand, label):
    """catalog ရဲ့ signature ကနေ argument ဖြည့်သည် (ARGS မှာ မရှိသော template)。"""
    global _CIDX
    if _CIDX is None:
        _CIDX = {}
        try:
            import gfxcat as GC
            for e in GC.catalog(): _CIDX[e["fn"]] = e
        except Exception:
            _CIDX = {}
    e = _CIDX.get(kind)
    if not e: return (brand,)
    try:
        import gfxcat as GC
        return GC.fill(e, brand, label) or (brand,)
    except Exception:
        return (brand,)


_FNC = {}
def _fn(name):
    """catalog ကနေ template function ရှာသည် (module ဘယ်ဟာမဆို)。"""
    if name in _FNC: return _FNC[name]
    f = None
    try:
        import importlib, sys as _s
        import gfxcat as GC
        for e in GC.catalog():
            if e["fn"] == name:
                cwd = os.getcwd()
                try:
                    if GC.MK not in _s.path: _s.path.insert(0, GC.MK)
                    os.chdir(GC.MK)
                    f = getattr(importlib.import_module(e["module"]), name, None)
                finally:
                    try: os.chdir(cwd)
                    except Exception: pass
                break
    except Exception:
        f = None
    _FNC[name] = f
    return f

def resolves(name):
    """template ကို တကယ် ရှာလို့ရလား — caption ဖယ်ခင် စစ်ရန်"""
    try:
        import titles as _t1, titles2 as _t2
        if getattr(_t2, name, None) or getattr(_t1, name, None): return True
    except Exception:
        pass
    return _fn(name) is not None


_TAGQ = {}
def _wants_tag(name):
    """template က ပထမ param အဖြစ် `tag` ယူလား"""
    if name in _TAGQ: return _TAGQ[name]
    # ⚠️ catalog ရဲ့ params က `tag` ကို **ဖယ်ထားသည်** (auto-supplied ဟု
    #    သတ်မှတ်၍)。 ဒါကြောင့် catalog နဲ့ စစ်လျှင် အားလုံး "မလို" ထွက်ပြီး
    #    တကယ် လိုတဲ့ ၁၂ ခုပါ ချိုးမိသည်。 ⇒ signature ကို တိုက်ရိုက် ကြည့်ရမည်。
    want = True
    try:
        import inspect
        fn = getattr(T2, name, None) or getattr(T1, name, None) or _fn(name)
        if fn:
            ps = list(inspect.signature(fn).parameters)
            want = bool(ps) and ps[0] == "tag"
    except Exception:
        want = True
    _TAGQ[name] = want
    return want
