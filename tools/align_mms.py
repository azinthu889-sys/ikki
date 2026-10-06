#!/usr/bin/env python3
"""Forced alignment — Meta MMS (torchaudio MMS_FA) · မြန်မာစာ စကားလုံးအချိန် (Zin ၂၀၂၆-၁၀-၀၆ B)

ASR (Gemini) ရဲ့ စကားလုံးအချိန်က **ခန့်မှန်းချက်** ⇒ ဗီဒီယို ရှည်လေ လွဲလေ。 ဒီ tool က
**စာသားကို အသံနဲ့ တိုက်ရိုက် ချိန်**သည် (CTC forced alignment · uroman romanize)。
ဝါကျ တစ်ခုချင်း (±၀.၃၅s ဘောင်) ⇒ memory ကန့်သတ် · ဗီဒီယို အရှည် မရွေး linear。

သုံးပုံ (alignment venv ဖြင့်):
  ~/ikki-align/.venv/bin/python tools/align_mms.py audio.wav sentences.json out.json
  sentences.json = [{"n":1,"start":1.2,"end":4.5,"text":"..."}, ...]
  out.json       = {"1": [{"w":"...","s":1.31,"e":1.62,"score":0.83}, ...], ...}
"""
import json
import os
import subprocess
import sys
import wave

# ⚠️ model (~1.2GB) ကို Mac disk မပြည့်စေရန် drive ပေါ်ထား (TORCH_HOME)
os.environ.setdefault("TORCH_HOME", "/Volumes/a/ikki-cache/torch"
                      if os.path.isdir("/Volumes/a/ikki-cache/torch") else os.path.expanduser("~/.cache/torch"))
import numpy as np
import torch
import torchaudio
from torchaudio.pipelines import MMS_FA as BUNDLE

PAD = 0.35
SR = BUNDLE.sample_rate  # 16000


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return torch.from_numpy(np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0)


def main(audio, sents_json, out_json):
    import uroman as ur
    U = ur.Uroman()
    model = BUNDLE.get_model(with_star=False)
    model.eval()
    tok = BUNDLE.get_tokenizer()
    align = BUNDLE.get_aligner()
    wav = load(audio)
    out = {}
    for s in json.load(open(sents_json)):
        words = [w for w in str(s.get("text") or "").split() if w.strip()]
        if not words:
            continue
        a = max(0.0, float(s["start"]) - PAD)
        b = min(len(wav) / SR, float(s["end"]) + PAD)
        seg = wav[int(a * SR):int(b * SR)]
        if len(seg) < SR * 0.2:
            continue
        roman, keep = [], []
        for w in words:
            r = "".join(c for c in U.romanize_string(w).lower() if c in BUNDLE.get_dict())
            if r:
                roman.append(r)
                keep.append(w)
        if not roman:
            continue
        try:
            with torch.inference_mode():
                em, _ = model(seg.unsqueeze(0))
                spans = align(em[0], tok(roman))
        except Exception as e:  # noqa: BLE001 — ဝါကျ တစ်ခု ကျလည်း ကျန်တာ ဆက်
            print(f"  ⚠️ ဝါကျ {s.get('n')} ({type(e).__name__})", file=sys.stderr)
            continue
        ratio = seg.shape[0] / em.shape[1] / SR
        res = []
        for w, sp in zip(keep, spans):
            if not sp:
                continue
            sc = float(sum(t.score * len(t) for t in sp) / max(1, sum(len(t) for t in sp)))
            res.append(dict(w=w, s=round(a + sp[0].start * ratio, 3),
                            e=round(a + sp[-1].end * ratio, 3), score=round(sc, 3)))
        out[str(s.get("n"))] = res
    json.dump(out, open(out_json, "w"), ensure_ascii=False)
    print(f"aligned {len(out)} sentences")


if __name__ == "__main__":
    main(*sys.argv[1:4])
