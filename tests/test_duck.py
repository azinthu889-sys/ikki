# -*- coding: utf-8 -*-
"""SFX က စကားကို မဖုံးစေရန် (SFX audit P0)

⚠️ `mix()` က cue တိုင်းကို ပုံသေ dB နဲ့ ထပ်ခဲ့သည် — စကားပေါ်လား
   တိတ်နေချိန်လား မကြည့်ပါ。
"""
import os
import subprocess
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))
import dress as D    # noqa: E402

FAILED = []
TMP = os.path.join(HERE, "_duck_tmp.wav")


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


def make_wav():
    """၀–၅s တိတ် · ၅–၁၅s စကားအစား −၁၃ dB အသံ · ၁၅–၂၀s တိတ်

    ⚠️ ffmpeg filter နဲ့ မဆောက်ရ — `volume=enable=…` ရဲ့ ကိန်းက linear
       ဖြစ်ပြီး အဆင့်ကို အတိအကျ မထိန်းနိုင်ပါ。 test က **အဆင့်ကို**
       စစ်သဖြင့် အဆင့်ကို ကိုယ်တိုင် ချုပ်ကိုင်ရမည်。
    """
    import array
    import math
    import random
    SR, DUR = 16000, 20.0
    a = array.array("h")
    rnd = random.Random(7)
    amp = int(32767 * (10 ** (-13.0 / 20.0)) * 1.414)   # RMS ≈ −13 dBFS
    for i in range(int(SR * DUR)):
        t = i / float(SR)
        if 5.0 <= t < 15.0:
            v = int(amp * (rnd.random() * 2 - 1) * 0.58)
        else:
            v = int(32767 * 1e-4 * (rnd.random() * 2 - 1))
        a.append(max(-32767, min(32767, v)))
    with wave.open(TMP, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes(a.tobytes())
    return TMP


def main():
    w = make_wav()
    print("── ၁ · စကားသံ တိုင်းချက် ──")
    q = D.speech_db(w, 2.0)
    s = D.speech_db(w, 10.0)
    check("တိတ်ချိန် နိမ့်", q is not None and q < -45, q)
    check("စကားချိန် မြင့်", s is not None and s > -30, s)
    check("ကွာဟမှု ကြီး", (s - q) > 25, (s, q))

    print("\n── ၂ · asset အား (catalog ကနေ) ──")
    # ⚠️ cue ရဲ့ `db` က **အား မဟုတ် — လျှော့ချက်**。 asset ရဲ့ ပစ်မှတ်
    #    အားနဲ့ ပေါင်းမှ တကယ့်အား ရသည်。 မပေါင်းဘဲ တွက်လျှင် cue တိုင်း
    #    လျှော့ခံရပြီး SFX မကြားရတော့ (ပထမ ရေးဆွဲချက်မှာ ဖြစ်ခဲ့)。
    for r in ("whoosh_in", "latch", "impact"):
        v = D._asset_db(r)
        check(f"{r} အား ရှိ", -40 < v < 0, v)

    print("\n── ၃ · တိတ်ချိန် cue ⇒ မထိရ ──")
    out, n = D.duck_cues([(2.0, "whoosh_in", -2)], w)
    check("မလျှော့ပါ", n == 0 and out[0][2] == -2, (n, out))

    print("\n── ၄ · ပုံမှန် အဆင့် ⇒ မလျှော့ရ ──")
    # planner က −၁၅…−၁၇ dB သုံးသည် — အဲဒါက စကားအောက် အများကြီး ရှိပြီးသား
    cues = [(10.0, "whoosh_in", -15), (10.0, "latch", -17)]
    out, n = D.duck_cues(cues, w)
    check("မလျှော့ပါ", n == 0, (n, out))

    print("\n── ၅ · ကျယ်လွန်းလျှင် ⇒ လျှော့ရမည် ──")
    out, n = D.duck_cues([(10.0, "whoosh_in", +4)], w)
    check("လျှော့သည်", n == 1 and out[0][2] < 4, (n, out))
    check("ကန့်သတ်ထက် မကျော်", out[0][2] >= 4 - D.DUCK_MAX - 0.5, out)

    print("\n── ၆ · အချိန် မရွှေ့ရ ──")
    # ⚠️ cue က ဂရပ်ဖစ်နဲ့ တွဲနေသည် — ရွှေ့လျှင် ပုံနဲ့ အသံ ကွဲသွားမည်
    cues = [(10.0, "whoosh_in", +4), (12.0, "impact", +4)]
    out, _ = D.duck_cues(cues, w)
    check("အချိန် တူညီ", [c[0] for c in out] == [10.0, 12.0], out)
    check("role တူညီ", [c[1] for c in out] == ["whoosh_in", "impact"], out)

    print("\n── ၇ · ဗလာ / ဖိုင်မရှိ ──")
    check("cues ဗလာ", D.duck_cues([], w) == ([], 0))
    c1 = [(1.0, "whoosh_in", -15)]
    check("wav မရှိ ⇒ မထိ", D.duck_cues(c1, "/no/such.wav") == (c1, 0))

    os.path.exists(TMP) and os.remove(TMP)
    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
