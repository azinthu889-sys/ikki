"""place — keyword pop နေရာချမှု test

⚠️ ကိန်းများကို `docs/HEADTALK_STYLE.md` (reference KCN4-2hyUBM ရဲ့ full-res
   တိုင်းချက်) ကနေ ယူထားသည်。 ဒီဖိုင်က အဲဒီ ဘောင်တွေ မပျက်အောင် ကာကွယ်သည်。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "core"))

import place as PL      # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print(f"  ✓ {name}")
    else:
        FAILED.append(name)
        print(f"  ✗ {name}  {detail}")


# ⚠️ တိုင်းထားသော မျက်နှာ (headtop_clean16.mp4 · pose ဖရိန် ၃၂ ခု)
FACE = (0.392, 0.347, 0.622, 0.604)
# ⚠️ reference ရဲ့ **တကယ့်** နေရာများ — ဒါတွေ အားလုံး ခွင့်ပြုခံရမည်
REF = [("2.DEVELOP", 0.777, 0.258), ("3.EXECUTE", 0.777, 0.276),
       ("Controlable", 0.174, 0.274), ("WHY? a", 0.121, 0.503),
       ("WHY? b", 0.863, 0.350), ("WHY? c", 0.500, 0.811)]
TW, TH = 0.24, PL.TEXT_H


def main():
    print("── ၁ · တိုင်းထားသော ဘောင် ──")
    check("စာလုံး အမြင့် ၈–၁၆.၅%H ကြား",
          PL.TEXT_H_MIN <= PL.TEXT_H <= PL.TEXT_H_MAX, PL.TEXT_H)
    check("အလယ်တန်း ≈ ၁၀.၁%H", abs(PL.TEXT_H - 0.101) < 0.002, PL.TEXT_H)
    check("x ဘောင် ၁၂–၈၆%", (PL.CX_MIN, PL.CX_MAX) == (0.12, 0.86))
    check("y ဘောင် ၂၀–၈၁%", (PL.CY_MIN, PL.CY_MAX) == (0.20, 0.81))
    check("တစ်ပြိုင်နက် ၃ ခုအထိ", PL.MAX_AT_ONCE == 3)

    print("\n── ၂ · မျက်နှာ အကွက် ──")
    fr = [dict(t=i * 0.5, nf=1, fa=0.0158, fx=0.505, fy=0.474) for i in range(8)]
    b = PL.face_box(fr, 0, 4)
    check("အကွက် ထွက်သည်", b is not None, b)
    check("အလယ်မှာ ရှိသည်", 0.35 < (b[0] + b[2]) / 2 < 0.65, b)
    check("အနားကွက် ပါသည်", (b[2] - b[0]) > 0.10, b[2] - b[0])
    check("မျက်နှာ မရှိလျှင် None", PL.face_box([], 0, 1) is None)
    # ⚠️ ရွေ့သွားလျှင် **အကုန် ဖုံးရမည်** — frame တစ်ခုတည်းနဲ့ မတွက်ရ
    mv = [dict(t=0, nf=1, fa=0.0158, fx=0.35, fy=0.45),
          dict(t=2, nf=1, fa=0.0158, fx=0.65, fy=0.45)]
    b2 = PL.face_box(mv, 0, 2)
    check("ရွေ့သွားတာကို အကုန် ဖုံးသည်", b2[0] < 0.30 and b2[2] > 0.70, b2)

    print("\n── ၃ · reference နေရာများ ခွင့်ပြုခံရမည် ──")
    # ⚠️ ဒါက အရေးကြီးဆုံး — ကိုယ့်စည်းမျဉ်းက reference ကို ပယ်လျှင် စည်းမျဉ်း မှားသည်
    for nm, cx, cy in REF:
        r = (cx - TW / 2, cy - TH / 2, cx + TW / 2, cy + TH / 2)
        check(f"{nm} မျက်နှာနဲ့ မထပ်", not PL._hit(r, FACE), (r, FACE))
        check(f"{nm} ဘောင်ထဲ",
              PL.CX_MIN - 0.01 <= cx <= PL.CX_MAX + 0.01 and
              PL.CY_MIN - 0.01 <= cy <= PL.CY_MAX + 0.01, (cx, cy))

    print("\n── ၄ · ရွေးချယ်မှု ──")
    used = []
    got = []
    for _ in range(PL.MAX_AT_ONCE):
        p = PL.pick(None, 0, 1, TW, TH, used=used, box=FACE)
        check("နေရာ ရသည်", p is not None)
        if not p:
            break
        got.append(p); used.append((p[0], p[1], TW, TH))
    for cx, cy in got:
        r = (cx - TW / 2, cy - TH / 2, cx + TW / 2, cy + TH / 2)
        check(f"({cx:.2f},{cy:.2f}) မျက်နှာနဲ့ မထပ်", not PL._hit(r, FACE))
    for i in range(len(got)):
        for j in range(i + 1, len(got)):
            a = (got[i][0] - TW/2, got[i][1] - TH/2, got[i][0] + TW/2, got[i][1] + TH/2)
            c = (got[j][0] - TW/2, got[j][1] - TH/2, got[j][0] + TW/2, got[j][1] + TH/2)
            check(f"{i+1}↔{j+1} အချင်းချင်း မထပ်", not PL._hit(a, c))

    print("\n── ၅ · စာတန်းဇုန် ရှောင် ──")
    band = PL.caption_band(0.92, 0.13)
    used = []
    for _ in range(4):
        p = PL.pick(None, 0, 1, TW, TH, used=used, box=FACE, avoid=[band])
        if not p:
            break
        bot = p[1] + TH / 2
        check(f"({p[0]:.2f},{p[1]:.2f}) စာတန်းဇုန် မထိ", bot <= band[1] + 1e-6, bot)
        used.append((p[0], p[1], TW, TH))

    print("\n── ၆ · နေရာ မရှိလျှင် None ──")
    check("ကြီးလွန်းသော အကွက် → None",
          PL.pick(None, 0, 1, 0.95, 0.9, box=FACE) is None)

    print()
    if FAILED:
        print(f"  ✗ ကျသည် {len(FAILED)}: {FAILED}")
        return 1
    print("  ✓ အားလုံး အောင်")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
