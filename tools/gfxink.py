#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""template ရဲ့ peak frame မှာ **စာသား တကယ် ပါမပါ** နှင့် **ဘောင်ပြင် ထွက်မထွက်**
   ကို ဘာသာစကား မဆိုင်ဘဲ တိုင်းသည်。

⚠️ Vision OCR ကို **မသုံးရ** — မြန်မာစာကို မဖတ်နိုင်သဖြင့် စာသား ရှိပါလျက်
   ၀ ပြန်ပြီး ကောင်းသော template ကို မှားငြင်းမိသည် (၂၀၂၆-၀၉-၂၀ တိုင်း၍ တွေ့)。
⚠️ `alpha` ဖုံးအုပ်မှုနဲ့လည်း **မတိုင်းရ** — အရောင်တုံးကြီးက alpha ပြည့်နေသဖြင့်
   စာသား လုံးဝ မပါသော template များ အောင်သွားခဲ့သည် (infogfx.pyramid ·
   prem.glass_stat · titles.label_pill)。 Zin: 「quality 0」。
⇒ **gradient** နဲ့ တိုင်းသည် — စာလုံးက အနားသတ် များပြီး အရောင်တုံးက မရှိ。
"""
import sys, json
import numpy as np
from PIL import Image

BG = (24, 26, 32)            # တိုင်းရန် နောက်ခံ (မှောင်)
G_THR = 28                   # gradient အနိမ့်ဆုံး
EDGE_BAND = 0.012            # ဘောင် အနားသတ် အလျား (အချိုး)


def stats(path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    a = np.asarray(im, dtype=np.int16)
    al = a[..., 3]
    rgb = a[..., :3]
    # မှောင်သော နောက်ခံပေါ် ပေါင်းစပ်
    f = al[..., None] / 255.0
    comp = rgb * f + np.array(BG)[None, None, :] * (1 - f)
    g = comp.mean(axis=2)
    gx = np.abs(np.diff(g, axis=1)); gy = np.abs(np.diff(g, axis=0))
    grad = np.zeros_like(g)
    grad[:, :-1] = np.maximum(grad[:, :-1], gx)
    grad[:-1, :] = np.maximum(grad[:-1, :], gy)
    opaque = al > 16
    area = max(1, int(opaque.sum()))
    edges = (grad > G_THR) & opaque
    detail = float(edges.sum()) / area          # စာသား/အသေးစိတ် အချိုး
    # ဘောင် အနားမှာ အသေးစိတ် ရှိလျှင် **ဖြတ်ခံထား**သည်
    # ⚠️ 「အနားက အသေးစိတ် ÷ အသေးစိတ် စုစုပေါင်း」 ဟု တိုင်းလျှင် **မတွေ့**。
    #    ကျယ်သော စာတန်းတစ်ခု ၂ ဖက်စလုံး ဖြတ်ခံထားပေမယ့် အနားက အချိုးက
    #    ၀.၀၀၁၅ သာ ဖြစ်သည် (kinetic3.burst_scale — တကယ် တိုင်း၍ တွေ့)。
    #    ⇒ **အနား တစ်ဖက်ချင်းရဲ့ သိပ်သည်းမှု**ကို တိုင်းပြီး အမြင့်ဆုံး ယူသည်。
    bw = max(1, int(round(min(w, h) * EDGE_BAND)))
    sides = [edges[:bw, :], edges[-bw:, :], edges[:, :bw], edges[:, -bw:]]
    clipped = max(float(x.sum()) / max(1, x.size) for x in sides)
    return dict(w=w, h=h, alpha=round(area / (w * h), 4),
                detail=round(detail, 5), clip=round(clipped, 4))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        try:
            print(json.dumps(dict(f=p.split("/")[-1], **stats(p)), ensure_ascii=False))
        except Exception as e:
            print(json.dumps(dict(f=p.split("/")[-1], err=f"{type(e).__name__}: {e}")))
