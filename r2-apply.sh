#!/bin/sh
# IKKI · .env ထဲက R2 key ကို စစ်ပြီး အသက်သွင်းခြင်း
#
# ⚠️ stdin · paste · prompt **လုံးဝ မသုံးပါ**。 paste လမ်းကြောင်းက
#    အခါခါ မအောင်မြင်ခဲ့သည် (bracketed paste · blank line · tty)。
#    ⇒ .env ကို editor နှင့် ကိုယ်တိုင် ရေးပြီး ဒါကို run ရုံ。
#    ဒီနည်းက မြင်ရသည်၊ ပြန်ပြင်လို့ ရသည်၊ တိတ်တဆိတ် မကျဘမ်းဘူး。
set -e
cd "$(dirname "$0")"

[ -f .env ] || { echo "❌ .env မရှိ"; exit 1; }

get() { grep -m1 "^$1=" .env 2>/dev/null | cut -d= -f2- | tr -d ' \r\n\t'; }
A=$(get R2_ACCOUNT_ID); K=$(get R2_ACCESS_KEY_ID)
S=$(get R2_SECRET_ACCESS_KEY); B=$(get R2_BUCKET)
[ -z "$B" ] && B=ikki

# ⚠️ endpoint URL ကို ACCOUNT_ID အနေနဲ့ ရေးမိတာ ဖြစ်လွယ် — ထုတ်ပေးသည်
case "$A" in
  *r2.cloudflarestorage.com*)
    A=$(printf '%s' "$A" | sed -E 's#^https?://##; s#\..*$##')
    echo "  → endpoint URL မှ Account ID ထုတ်ပြီး" ;;
esac

fail=0
chk() {
  n=$(printf '%s' "$2" | wc -c | tr -d ' ')
  if [ "$n" = 0 ]; then echo "❌ $3 — .env ထဲ မရှိ / အလွတ်"; fail=1
  elif [ "$n" != "$4" ]; then echo "❌ $3 က $n လုံး — $4 လုံး ဖြစ်ရမည်"; fail=1
  elif ! printf '%s' "$2" | grep -qE '^[0-9a-f]+$'; then
    echo "❌ $3 က hex (0-9 a-f) သာ ဖြစ်ရမည် — cfut_… ဆိုလျှင် Token value ယူမိတာ"; fail=1
  else echo "✓ $3 · $n လုံး"; fi
}
chk R2_ACCOUNT_ID        "$A" "Account ID"        32
chk R2_ACCESS_KEY_ID     "$K" "Access Key ID"     32
chk R2_SECRET_ACCESS_KEY "$S" "Secret Access Key" 64
# ⚠️ နှစ်ခုလုံး ၃၂ လုံး hex ဖြစ်သဖြင့် နေရာလွဲမိတာ အရှည်နှင့် မဖမ်းမိ
if [ -n "$A" ] && [ "$A" = "$K" ]; then
  echo "❌ Account ID နှင့် Access Key ID တူနေသည် — နေရာ လွဲထားသည်"; fail=1
fi
echo "✓ Bucket · $B"
[ "$fail" = 1 ] && { echo; echo "nano .env နှင့် ပြန်ပြင်ပါ"; exit 1; }

# ⚠️ ထုတ်ထား account id ကို ပြန်ရေးရမည် (URL ကနေ ထုတ်ခဲ့လျှင်)
grep -v '^R2_' .env > .env.new 2>/dev/null || true
{ echo "R2_ACCOUNT_ID=$A"; echo "R2_ACCESS_KEY_ID=$K"
  echo "R2_SECRET_ACCESS_KEY=$S"; echo "R2_BUCKET=$B"; } >> .env.new
mv .env.new .env; chmod 600 .env

echo "── container ပြန်တက်နေသည် ──"
docker compose up -d 2>&1 | tail -2
sleep 4
echo "── R2 သတ်မှတ် + စမ်းသပ် ──"
docker exec ikki python tools/r2_setup.py
