# -*- coding: utf-8 -*-
"""R-G5 (ค) — **နမူနာ တိုက်စစ်ခြင်း**。 tool ပြင်လို့ derived ဖိုင် ဟောင်းသွားရာ
ဈေးကြီးလွန်းလို့ အပြည့် ပြန်မတိုင်းနိုင်သည့် အခါ — ကြိုကြေညာထားသော နမူနာကို
tool အသစ်နဲ့ ပြန်တိုင်းပြီး သိမ်းထားတဲ့ တန်ဖိုးနဲ့ **bit-exact** တိုက်သည်。

    python3 tools/rebless_sample.py gfx_verify
    python3 tools/rebless_sample.py gfx_textsens

⛔ စည်းမျဉ်း (Zin · ၂၀၂၆-၀၉-၂၆):
  ① နမူနာ ရွေးနည်းကို **ကိန်း မမြင်ခင်** ကြေညာရမည် —
     `sorted(id)` ရဲ့ index 0,25,50,… (every 25th) · ≥25 ခု · လက်ရွေးစင် မရွေးရ。
     ဒီ tool က ကြေညာဖိုင်ထဲ စာရင်းကို **ပြန်တွက်ပြီး တိုက်**သည် ⇒ လက်နဲ့
     ပြောင်းထားလျှင် ငြင်းမည်。
  ② row **အပြည့်** အတိအကျ တိုက်သည် (ဖယ်ထားသော field **မရှိ** — field
     အားလုံးက တိုင်းချက် ချည်းသာ; timestamp/duration မပါ · ၂၀၂၆-၀၉-၂၆ စစ်ပြီး)。
  ③ ကွာတာ ၁ ခု ပေါ်လျှင် — ဖိုင်ကို snapshot ကနေ **ပြန်ထား**ပြီး
     「အပြည့် ပြန်တိုင်းရမည်」 ဟု ထွက်သည်。 ငြင်းခုံစရာ မရှိ。
  ④ 「template က သူ့ဘာသာ မတည်ငြိမ်」 ဟု ဆိုလျှင် — **tool ဟောင်း**နဲ့ ၂ ခါ
     ပြေးပြီး ကွာကြောင်း ပြရမည်。 ဒီ tool က အလိုအလျောက် မဖယ်ပါ。
  ⑤ ရလဒ်ကို `reports/rebless_proof_<name>.json` ထဲ ရေးသည် — `derived_check.py
     --rebless` က **ဒီဖိုင် မပါဘဲ ဂိတ် မဖွင့်**ပါ (စာသား သက်သက် ⇒ ငြင်း)。
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import derived_check as DC                                    # noqa: E402

DECL = os.path.join(HERE, "reports", "rebless_sample_2026-09-26.json")
STEP = 25                                                     # ① ကြေညာထားသော နှုန်း
MINN = 25                                                     # ① အနည်းဆုံး နမူနာ

#: tool ကို နမူနာ id များနဲ့ ပြေးနည်း — name အလိုက်
RUN = {
    "gfx_verify":   lambda ids: (["python3", "tools/gfx_verify.py"],
                                 {"GFX_ONLY": ",".join(ids)}),
    "gfx_textsens": lambda ids: (["python3", "tools/gfxtextsens.py",
                                  "--only", ",".join(ids)], {}),
}


def _rows(path):
    return {r["id"]: r for r in json.load(open(path, encoding="utf-8"))}


def main(argv):
    if len(argv) < 2 or argv[1] not in RUN:
        raise SystemExit("သုံးနည်း: rebless_sample.py {%s}" % "|".join(RUN))
    name = argv[1]
    spec = DC.REG[name]
    out = DC.out_path(spec)

    # ── ① ကြေညာချက် တိုက် — ပြန်တွက်ပြီး တူမှ ခွင့်ပြု ──
    decl = json.load(open(DECL, encoding="utf-8"))
    d = (decl.get("samples") or {}).get(name)
    if not d:
        raise SystemExit("⛔ ကြေညာဖိုင်ထဲ `%s` မပါ: %s" % (name, DECL))
    stored = _rows(out)
    recomputed = sorted(stored)[::STEP]
    if list(d["ids"]) != recomputed:
        raise SystemExit(
            "⛔ ① နမူနာ စာရင်း မကိုက် — ကြေညာထားတာ %d ခု · ပြန်တွက် %d ခု。\n"
            "   လက်ရွေးစင် ရွေးထားတာ (သို့) ဖိုင် ပြောင်းသွားတာ ⇒ ငြင်းသည်。"
            % (len(d["ids"]), len(recomputed)))
    ids = list(d["ids"])
    if len(ids) < MINN:
        raise SystemExit("⛔ ① နမူနာ %d ခု — အနည်းဆုံး %d လိုသည်" % (len(ids), MINN))
    print("  ① ကြေညာချက် ✓ — နမူနာ %d ခု (sorted(id)[::%d] · ပြန်တွက်ပြီး တူ)"
          % (len(ids), STEP), flush=True)

    old_tools = dict(DC.load_prov(spec).get("tools") or {})
    new_tools = DC.tool_hashes(spec)
    print("  tool hash: %s ⇒ %s"
          % (json.dumps(old_tools, ensure_ascii=False),
             json.dumps(new_tools, ensure_ascii=False)), flush=True)

    # ── snapshot (③ ကွာလျှင် ပြန်ထားရန်) ──
    snap = out + ".rebless_snap"
    shutil.copyfile(out, snap)
    psnap = None
    if os.path.exists(DC.prov_path(spec)):
        psnap = DC.prov_path(spec) + ".rebless_snap"
        shutil.copyfile(DC.prov_path(spec), psnap)
    print("  snapshot ✓ %s" % os.path.basename(snap), flush=True)

    # ── ② tool အသစ်နဲ့ နမူနာ ပြန်တိုင်း ──
    cmd, env = RUN[name](ids)
    e = dict(os.environ); e.update(env)
    print("  ② ပြန်တိုင်းမည်: %s %s" % (" ".join(cmd[:2]),
          "GFX_ONLY=%d ခု" % len(ids) if env else "--only %d ခု" % len(ids)),
          flush=True)
    r = subprocess.run(cmd, cwd=HERE, env=e, capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copyfile(snap, out); os.unlink(snap)
        raise SystemExit("⛔ tool ကျသည် (rc=%s) — ဖိုင် ပြန်ထားပြီး\n%s"
                         % (r.returncode, (r.stderr or r.stdout)[-600:]))

    # ── ② bit-exact တိုက် (row အပြည့်) ──
    fresh = _rows(out)
    miss, diff = [], []
    for i in ids:
        a, b = stored.get(i), fresh.get(i)
        if b is None:
            miss.append(i)
        elif a != b:
            diff.append({"id": i, "stored": a, "fresh": b,
                         "fields": sorted(k for k in set(a) | set(b)
                                          if a.get(k) != b.get(k))})
    ok = not miss and not diff
    print("  ② ကိုက်ချက် **%d/%d** · မတွေ့ %d · ကွာ %d"
          % (len(ids) - len(miss) - len(diff), len(ids), len(miss), len(diff)),
          flush=True)
    for x in diff[:6]:
        print("     🔴 %-28s field: %s" % (x["id"], ",".join(x["fields"])))

    proof = {
        "name": name, "rule": decl["rule"], "step": STEP,
        "declared_file": os.path.relpath(DECL, HERE),
        "sample_ids": ids, "n": len(ids),
        "matched": len(ids) - len(miss) - len(diff),
        "missing": miss, "mismatch": diff,
        "old_tools": old_tools, "new_tools": new_tools,
        "out_sha": DC._fh(out), "verdict": "ok" if ok else "full-remeasure",
    }
    pp = os.path.join(HERE, "reports", "rebless_proof_%s.json" % name)
    json.dump(proof, open(pp, "w"), ensure_ascii=False, indent=1)
    print("  ⑤ သက်သေ → %s" % os.path.relpath(pp, HERE), flush=True)

    if not ok:
        # ③ ကွာလျှင် — ရောနေတဲ့ ဖိုင် မထားရ ⇒ snapshot ပြန်
        shutil.copyfile(snap, out)
        if psnap: shutil.copyfile(psnap, DC.prov_path(spec))
        os.unlink(snap)
        if psnap: os.unlink(psnap)
        raise SystemExit(
            "⛔ ③ ကွာချက် ရှိသည် ⇒ ဖိုင် snapshot ကနေ ပြန်ထားပြီး。\n"
            "   `%s` ကို **အပြည့် ပြန်တိုင်းရမည်**。 ငြင်းခုံစရာ မရှိ。\n"
            "   ④ 「template က သူ့ဘာသာ မတည်ငြိမ်」 ဟု ဆိုလျှင် — tool **ဟောင်း**နဲ့\n"
            "      ၂ ခါ ပြေးပြီး အဲဒါလည် ကွာကြောင်း ပြရမည် (စာရင်းနဲ့)。" % name)

    os.unlink(snap)
    if psnap: os.unlink(psnap)
    print("\n  ✅ နမူနာ %d/%d bit-exact ⇒ `derived_check.py --rebless %s` "
          "ပြေးလို့ ရပါသည်" % (len(ids), len(ids), name))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
