# -*- coding: utf-8 -*-
"""တွက်ထုတ်ထားသော (derived) ဖိုင်ကို **လုံခြုံစွာ** ရေးသည်。

⚠️ ဘာကြောင့် ရှိရသလဲ — ၂၀၂၆-၀၉-၂၆: `tools/gfxsize.py` က catalog ကနေ id
   စာရင်း ဗလာ ရလာပြီး `gfx_size_16x9.json` (၅၉၃ entry · တိုင်းချက် ~၄၀ မိနစ်) ကို
   **ဗလာနဲ့ လွှမ်းပစ်**ခဲ့သည်。 backup မရှိ。 ထို script ရဲ့ ကိုယ်ပိုင် မှတ်ချက်ထဲမှာ
   ဒီအခြေအနေက အန္တရာယ် ရှိတယ်ဆိုတာ ၂၀၂၆-၀၉-၂၁ ကတည်းက ရေးထားပြီး guard မထည့်ခဲ့。
   ⇒ ဒါက **တစ်ဖိုင်တည်းရဲ့ ပြဿနာ မဟုတ်、အလေ့အထ ပြဿနာ** (Zin)。
   တိုင်းချက်: derived ရေးသူ script ၄၈ ခုထဲ **၄၄ ခုမှာ ဗလာ-guard မရှိ · ၄၅ ခုမှာ
   atomic write မရှိ** ⇒ script တစ်ခုချင်း ပြင်တာထက် ဒီ helper ကနေ သွားရမည်。

စည်းမျဉ်း ၄ ခု — `write_derived()` က အားလုံး အလိုအလျောက် လုပ်သည်:

  W-1 **ဗလာ ⇒ မရေး** — entry ၀ ခု ဆိုလျှင် `DerivedRefused`。 (ရှိပြီးသား ဒေတာက
      ဗလာ ရလဒ်ထက် အမြဲ ပိုတန်သည်; ပြန်တိုင်းလို့ရသည် · ပြန်ဖေါ်လို့ မရ)
  W-2 **ယုတ်လျှင် ⇒ မရေး** (shrink guard) — အသစ် M < အရှိ N ဆိုလျှင် ငြင်းသည်;
      တကယ် ယုတ်သင့်တဲ့ အခါ `--shrink-ok` (သို့) `shrink_ok=True` နဲ့ ခွင့်ပြုရမည်。
      ⚠️ ချုံးမှု ရှိလျှင် ဘယ် key တွေ ပျောက်မှာလဲ **နာမည် တပ်ပြီး** ပြသည်。
  W-3 **atomic** — တူညီသော directory ထဲ `.tmp` ⇒ `flush` ⇒ `fsync` ⇒
      `os.replace`。 ရေးရင်း ပြုတ်လျှင် မူရင်း ဖိုင် အတိအကျ ကျန်သည် (တစ်ဝက် မဖြစ်)。
  W-4 **provenance** — `<path>.prov.json` ထဲ `wrote_by` · `wrote_at` ·
      `count` · `prev_count` · `bytes` မှတ်သည်。
      ⚠️ `tools/derived_check.record()` နဲ့ **တစ်ဖိုင်တည်း** မှီသည် ⇒ key နာမည်
         တွေ ခွဲထားရမည် (`record()` က `by`/`at`/`out_hash`/`templates`;
         ဒီဟာက `wrote_*`/`count`/`prev_count`/`bytes`)。 နှစ်ခုစလုံး
         「ဖတ် ⇒ ဖြည့် ⇒ ရေး」 ပုံစံ ဖြစ်သဖြင့် တစ်ခုက တစ်ခုကို မဖျက်ပါ。

`want` (တစ်ပိုင်း run) — id အနည်းငယ်သာ ပြန်တိုင်းလျှင် `want=[id,…]` ပေးရမည်:
ရှိပြီးသား ဒေတာနဲ့ **merge** လုပ်ပြီး၊ ချုံးမှုကို merge အလွန် အရေအတွက်နဲ့ တိုင်းသည်
(မဟုတ်လျှင် တစ်ပိုင်း run တိုင်း W-2 ကို ထိမည်)。
"""

import json
import os
import sys
import time

__all__ = ["DerivedRefused", "write_derived", "count_of", "shrink_ok_flag"]

#: wrapper dict ထဲ **ဒေတာ** ကို ဖေါ်သော key (ပထမ တွေ့သူ အလိုက်)
_DATA = ("items", "templates", "entries", "rows", "data")

#: derived wrapper ဖိုင်တွေရဲ့ အပေါ်လွှာ meta key — ဒေတာ **မဟုတ်**
_META = {"fmt", "meta", "generated", "generated_at", "tag", "W", "H",
         "by", "at", "version", "note"}

#: repo root — ဒီ module က `<root>/core/` ထဲ ရှိသည်
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DerivedRefused(Exception):
    """W-1/W-2 — ရေးခြင်းကို ငြင်းသည်。 ရှိပြီးသား ဖိုင် မထိပါ。"""


# ── ရေတွက်ခြင်း ─────────────────────────────────────────────────────────
def _items(obj):
    """(entry dict/list · count) — payload အမျိုးအစား ၄ မျိုး ခွဲသည်。

    ⚠️ `{"items": {...}}` က motionkit derived ဖိုင်တွေရဲ့ ပုံစံ — အပေါ်လွှာမှာ
       `meta`/`fmt` ရှိသဖြင့် `len(obj)` နဲ့ ရေတွက်လျှင် **အမြဲ ၂-၃** ရမည်
       (ဒေတာ ဗလာ ဖြစ်နေလျှင်တောင်) ⇒ ဗလာ-guard က တစ်ခါမှ မဖွင့်ပါ。
    """
    if isinstance(obj, dict):
        # ⚠️ ဒေတာ key ရဲ့ နာမည်က ဖိုင်ကို လိုက်ကွဲသည် — `gfx_size_*` က `items`、
        #    `thm_manifest` က `templates`。 `templates` ကို မသိလျှင် `version`
        #    (meta) ကို မြင်ပြီး **မှန်ကန်တဲ့ ရေးမှုကို ငြင်းမည်** (apply မလုပ်ခင်
        #    တိုင်းပြီး တွေ့ · ၂၀၂၆-၀၉-၂၆)。
        for _k in _DATA:
            _v = obj.get(_k)
            if isinstance(_v, (dict, list)):
                return _v, len(_v)
        # ⚠️ `items` **ပျောက်နေတဲ့** wrapper — `len(obj)` နဲ့ ရေတွက်လျှင်
        #    meta key တွေကို entry လို့ ရေတွက်မိသည် (တိုင်းပြီး တွေ့: `{"fmt":…}`
        #    က entry ၁ ခု ရလာပြီး W-1 မဖွင့်ဘဲ ဖိုင် အသစ်ဆိုလျှင် ရေးမိမည်)。
        #    ⇒ meta key တွေ ပါလျှင် ဒေတာ ဗလာ အဖြစ် သတ်မှတ်သည်。
        if _META & set(obj):
            return {}, 0
        return obj, len(obj)
    if isinstance(obj, (list, tuple)):
        return obj, len(obj)
    if isinstance(obj, str):
        rows = [l.strip() for l in obj.splitlines()
                if l.strip() and not l.lstrip().startswith("#")]
        return rows, len(rows)
    raise TypeError("payload အမျိုးအစား မသိ: %r" % type(obj))


def count_of(obj):
    return _items(obj)[1]


def _keys(entries):
    """ချုံးမှု တိုင်းရန် key အစု。 မရလျှင် **ဗလာ အစု** (ရေတွက်သာ တိုင်းမည်)。

    ⚠️ `gfx_verify`/`gfx_textsens` က **list of dict** ရေးသည် ⇒ `set(entries)`
       က `TypeError: unhashable type: 'dict'` နဲ့ ပြုတ်သည် — ချုံးမှု စစ်ချိန်
       (ဒါဟာ guard က တကယ် အလုပ်လုပ်ရမည့် အချိန်) မှာ ပြုတ်တာ ဖြစ်သဖြင့်
       အဆိုးဆုံး。 တိုင်းပြီး တွေ့သည် (၂၀၂၆-၀၉-၂၆)。
    """
    if isinstance(entries, dict):
        return set(entries)
    out = set()
    for e in entries:
        if isinstance(e, dict):
            k = e.get("id") or e.get("key") or e.get("name")
            if k is None:
                return set()          # နာမည် မရှိ ⇒ key နဲ့ မတိုင်း
            out.add(k)
            continue
        try:
            hash(e)
        except TypeError:
            return set()
        out.add(e)
    return out


def _read_old(path):
    """(payload · entries · count) — ဖတ်လို့ မရလျှင် (None, set(), None)。

    ⚠️ count `None` က 「baseline မသိ」 — `0` နဲ့ မတူ。 မသိလျှင် W-2 မစစ်ပါ
       (ဖတ်မရတာကို 「ဗလာ ဖြစ်နေတယ်」 လို့ ဖတ်လျှင် ချုံးမှု တိုင်းတာ လွဲမည်)。
    """
    if not os.path.exists(path):
        return None, set(), None
    try:
        raw = open(path, encoding="utf-8").read()
    except OSError:
        return None, set(), None
    if path.endswith(".json"):
        try:
            old = json.loads(raw)
        except ValueError:
            return None, set(), None
    else:
        old = raw
    try:
        ent, n = _items(old)
    except TypeError:
        return None, set(), None
    return old, _keys(ent), n


def shrink_ok_flag(argv=None):
    return "--shrink-ok" in (argv if argv is not None else sys.argv)


# ── ရေးခြင်း ────────────────────────────────────────────────────────────
def write_derived(path, obj, want=None, writer=None, shrink_ok=None,
                  indent=1, quiet=False):
    """derived ဖိုင် ရေးသည် — W-1…W-4 အားလုံးနဲ့。

    path      — ရေးမည့် ဖိုင် (`.json` ⇒ JSON · မဟုတ်လျှင် text)
    obj       — dict · list · str。 `{"items": {...}}` ကို သိသည်。
    want      — တစ်ပိုင်း run ဆိုလျှင် ပြန်တိုင်းလိုက်တဲ့ id စာရင်း (merge လုပ်မည်)
    writer    — ရေးသူ script (`__file__` ထည့်ပါ)
    shrink_ok — `None` ⇒ `--shrink-ok` argv ကနေ ယူသည်
    ⇒ ရေးလိုက်သော entry အရေအတွက် (int)。 ငြင်းလျှင် `DerivedRefused`。
    """
    if shrink_ok is None:
        shrink_ok = shrink_ok_flag()
    say = (lambda *a: None) if quiet else (lambda s: print(s, flush=True))
    base = os.path.basename(path)

    old, old_keys, old_n = _read_old(path)

    # ── want: တစ်ပိုင်း run ⇒ merge ──
    if want:
        if old is None:
            raise DerivedRefused(
                "⛔ W-2 %s — တစ်ပိုင်း run (`want` %d) ဖြစ်ပြီး ရှိပြီးသား ဖိုင်ကို "
                "ဖတ်လို့ မရ ⇒ merge မရ。 အပြည့် ပြန်ပြေးပါ (`want` မပါဘဲ)。"
                % (base, len(want)))
        new_ent, _ = _items(obj)
        old_ent, _ = _items(old)
        if not (isinstance(new_ent, dict) and isinstance(old_ent, dict)):
            raise DerivedRefused(
                "⛔ %s — `want` က dict payload အတွက်သာ (key နဲ့ merge လုပ်ရသည်)。"
                % base)
        merged = dict(old_ent)
        merged.update(new_ent)
        if isinstance(obj, dict) and isinstance(obj.get("items"), dict):
            obj = dict(obj); obj["items"] = merged
        else:
            obj = merged
        say("  ⋯ %s — တစ်ပိုင်း: အသစ် %d ⊕ အရှိ %d ⇒ %d"
            % (base, len(new_ent), len(old_ent), len(merged)))

    ent, n = _items(obj)

    # ── W-1 ဗလာ ⇒ မရေး ──
    if n == 0:
        raise DerivedRefused(
            "⛔ W-1 %s — ရလဒ် **၀ ခု** ⇒ ဖိုင် မရေးပါ (အရှိ %s ခု မထိ)。\n"
            "   အကြောင်းရင်း ရှာပါ — id စာရင်း ဗလာလား · catalog ကျလား · "
            "filter မှားလား。" % (base, "မသိ" if old_n is None else old_n))

    # ── W-2 ချုံး ⇒ မရေး ──
    if old_n is not None and n < old_n and not shrink_ok:
        # ⚠️ key က str မဟုတ်လည်း ဖြစ်နိုင် (int · အမျိုးအစား ရော) ⇒ `sorted`
        #    နဲ့ `join` နှစ်ခုစလုံး ပြုတ်နိုင်သည် — guard ကိုယ်တိုင် ပြုတ်လျှင်
        #    ရေးမှုကို တားတာ မဟုတ်တော့ဘဲ traceback သာ ရမည် (တိုင်းပြီး တွေ့)
        try:
            lost = sorted(old_keys - _keys(ent), key=str)
        except TypeError:
            lost = list(old_keys - _keys(ent))
        lost = [str(x) for x in lost]
        raise DerivedRefused(
            "⛔ W-2 %s — အရှိ %d ⇒ အသစ် %d (**%d ယုတ်**) ⇒ မရေးပါ。\n"
            "   ပျောက်မည့် key %d: %s%s\n"
            "   တကယ် ယုတ်သင့်လျှင် `--shrink-ok` ထည့်ပြီး ပြန်ပြေးပါ。"
            % (base, old_n, n, old_n - n, len(lost),
               ", ".join(lost[:12]), " …" if len(lost) > 12 else ""))
    if old_n is not None and n < old_n:
        say("  ⚠️ %s — %d ⇒ %d (%d ယုတ်) · `--shrink-ok` ရှိသဖြင့် ဆက်ရေးမည်"
            % (base, old_n, n, old_n - n))

    # ── W-3 atomic: တူညီ dir ထဲ tmp ⇒ fsync ⇒ replace ──
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, ".%s.tmp%d" % (base, os.getpid()))
    text = obj if isinstance(obj, str) else json.dumps(
        obj, ensure_ascii=False, indent=indent, sort_keys=True)
    if not isinstance(obj, str):
        text += "\n"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)          # ⚠️ တူညီ filesystem ⇒ atomic
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise

    nb = os.path.getsize(path)
    say("  ✓ %s — entry %d · %d B%s"
        % (base, n, nb, "" if old_n is None else " (အရင် %d)" % old_n))

    # ── W-4 provenance (record() ရဲ့ key တွေ မထိ) ──
    pp = path + ".prov.json"
    try:
        pv = json.load(open(pp, encoding="utf-8")) if os.path.exists(pp) else {}
        if not isinstance(pv, dict):
            pv = {}
    except (OSError, ValueError):
        pv = {}
    if writer:
        # ⚠️ repo root နဲ့ တိုင်းရမည် — ရေးမည့် ဖိုင်ရဲ့ dir နဲ့ တိုင်းလျှင်
        #    scratch လို အပြင် dir မှာ `../../../..` အသုံးမဝင် path ထွက်သည်
        try:
            pv["wrote_by"] = os.path.relpath(os.path.abspath(writer), _ROOT)
        except ValueError:                      # drive/mount ကွဲလျှင်
            pv["wrote_by"] = os.path.abspath(writer)
    pv["wrote_at"] = int(time.time())
    pv["wrote_at_h"] = time.strftime("%Y-%m-%dT%H:%M")
    pv["count"] = n
    pv["prev_count"] = old_n
    pv["bytes"] = nb
    if want:
        pv["partial_want"] = sorted(want)[:200]
    try:
        with open(pp + ".tmp", "w", encoding="utf-8") as f:
            json.dump(pv, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.flush(); os.fsync(f.fileno())
        os.replace(pp + ".tmp", pp)
    except OSError as e:
        say("  ⚠️ provenance ရေးမရ: %s (ဒေတာ ဖိုင် ရေးပြီးသား)" % e)
    return n
