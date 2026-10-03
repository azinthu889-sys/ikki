#!/bin/sh
# IKKI test runner
#
# ⚠️⚠️ ၂၀၂၆-၁၀-၀၄ — ဒီ ဖိုင် မရှိခင်က test တွေကို **ဘယ် python နဲ့ ပြေးရမလဲ
#    သတ်မှတ်ထားခြင်း မရှိ**ခဲ့ပါ。 system `python3` မှာ `fastapi` မရှိသဖြင့်
#    API test တွေက
#
#        try: import fastapi
#        except ImportError: print("  ⊘ ..."); sys.exit(0)
#
#    နဲ့ ထွက်သွားပြီး shell က **exit 0 = အောင်** ဟု ရေတွက်ခဲ့သည်。
#    ⇒ 「ဖိုင် ၁၀၈ · ကျ ၀」 ဆိုတာ **မမှန်**ခဲ့ပါ — test_cutflow ·
#      test_vplan · test_upload_resume သုံးခုက ရက်အတော်ကြာ ကျနေခဲ့သည်。
#
#    ⇒ ① venv ကို ဦးစားပေး သုံးသည် ② ကျော်သွားတာကို **သီးသန့် ရေတွက်**ပြီး
#      ပြသည် — 「ကျ ၀」 က 「အကုန် စစ်ပြီး」 ဟု အဓိပ္ပာယ် မသက်ရောက်စေရန်。
set -u
cd "$(dirname "$0")/.."

PY="${IKKI_PY:-$HOME/.ikki/venv/bin/python}"
[ -x "$PY" ] || PY="$(command -v python3)"
echo "── python: $PY"
"$PY" -c "import fastapi" 2>/dev/null \
  && echo "── fastapi: ရှိ" \
  || echo "── ⚠️ fastapi မရှိ — API test တွေ ကျော်သွားမည် (IKKI_PY နဲ့ venv ကို ညွှန်ပါ)"

n=0; bad=0; skip=0; badf=""; skipf=""
for f in tests/test_*.py; do
  n=$((n + 1))
  out="$("$PY" "$f" 2>&1)"; rc=$?
  if [ $rc -ne 0 ]; then
    bad=$((bad + 1)); badf="$badf $f"
    [ -n "${IKKI_QUIET:-}" ] || { echo "✗ $f"; echo "$out" | tail -12 | sed 's/^/    /'; }
  elif printf '%s' "$out" | grep -q '⊘\|skipped\|OK (skipped'; then
    skip=$((skip + 1)); skipf="$skipf $f"
  fi
done

echo
echo "── ဖိုင် $n · ကျ $bad · ကျော် $skip ──"
[ -n "$badf" ] && { echo "ကျသည်:"; for f in $badf; do echo "  ✗ $f"; done; }
[ -n "$skipf" ] && { echo "ကျော်သည် (စစ်ခြင်း မရှိ):"; for f in $skipf; do echo "  ⊘ $f"; done; }
[ "$bad" -eq 0 ] || exit 1
# ⚠️ ကျော်လိုက်သော test က **မစစ်ရသေးသော ဂိတ်** ဖြစ်သည် — CI မှာ
#    `IKKI_STRICT=1` နဲ့ အမှားအဖြစ် ယူပါ。 စက်ထဲမှာ venv မရှိသူလည်း
#    ကျန်တာ ပြေးနိုင်ရန် ပုံသေက ခွင့်ပြုထားသည်。
if [ -n "${IKKI_STRICT:-}" ] && [ "$skip" -ne 0 ]; then
  echo "⚠️ IKKI_STRICT — ကျော်လိုက်တာ $skip ဖိုင် ရှိသည် ⇒ ကျသည်"
  exit 2
fi
exit 0
