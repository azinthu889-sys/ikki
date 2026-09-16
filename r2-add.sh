#!/bin/sh
# IKKI · R2 key ထည့်ခြင်း
#
# ⚠️ ကွက်လပ်တစ်ခုချင်း ရိုက်တာ **မှားလွယ်သည်** — Account ID နှင့်
#    Access Key ID နှစ်ခုလုံး ၃၂ လုံး hex ဖြစ်သဖြင့် နေရာလွဲမိလျှင်
#    အရှည်စစ်ရုံနှင့် မဖမ်းမိ (Zin ၂ ခါ မှားခဲ့သည်)。
#    ⇒ Cloudflare ရဲ့ credential အပိုင်းလုံးကို **တစ်ခါတည်း paste** လုပ်ပြီး
#      label ကနေ ခွဲယူသည်。
set -e
cd "$(dirname "$0")"

cat <<'HOWTO'
┌────────────────────────────────────────────────────────────────┐
│ Cloudflare → R2 → Manage API tokens → Create API token         │
│   Permissions: Object Read & Write     ·    bucket: ikki       │
│                                                                │
│ ဖန်တီးပြီးလျှင် "credentials for S3 clients" အပိုင်းကို        │
│ **အပိုင်းလုံး ကော်ပီ** ပြီး ဒီမှာ paste လုပ်ပါ။               │
│ (Access Key ID · Secret Access Key · Endpoint — အစီအစဥ် မလို)  │
│                                                                │
│ ပြီးလျှင် Enter နှစ်ချက် ဒါမှမဟုတ် Ctrl-D နှိပ်ပါ။           │
└────────────────────────────────────────────────────────────────┘
HOWTO
echo "paste ↓"

# ⚠️ stdin တစ်ခုလုံး ဖတ်သည် — အလွတ်လိုင်း ၂ ခု ဒါမှမဟုတ် EOF အထိ
BLOB=$(mktemp); trap 'rm -f "$BLOB"' EXIT
blank=0
while IFS= read -r line; do
  case "$line" in "") blank=$((blank+1)); [ "$blank" -ge 2 ] && break ;; *) blank=0 ;; esac
  printf '%s\n' "$line" >> "$BLOB"
done
echo

# ─ label ကနေ ခွဲယူ ─
# ⚠️ Secret က ၆၄ လုံး · Access Key က ၃၂ လုံး — အရှည်ဖြင့်လည်း ခွဲနိုင်သည်。
#    label မပါလည်း ရစေရန် နှစ်မျိုးလုံး စမ်းသည်。
K=$(grep -iE 'access[ _-]*key[ _-]*id' "$BLOB" | grep -oE '[0-9a-f]{32}' | head -1)
S=$(grep -iE 'secret' "$BLOB" | grep -oE '[0-9a-f]{64}' | head -1)
A=$(grep -oE '[0-9a-f]{32}\.r2\.cloudflarestorage\.com' "$BLOB" | grep -oE '^[0-9a-f]{32}' | head -1)
[ -z "$S" ] && S=$(grep -oE '[0-9a-f]{64}' "$BLOB" | head -1)
if [ -z "$K" ]; then
  # ⚠️ Secret (၆၄ လုံး) ရဲ့ အပိုင်းအစတွေ ၃၂ လုံး hex အနေနဲ့ ပါလာသည် —
  #    Secret ကို အရင် ဖယ်ပြီးမှ ရှာရမည်၊ မဟုတ်လျှင် Secret ရဲ့ ရှေ့ခြမ်းကို
  #    Access Key ဟု ယူမိမည်。
  K=$(sed "s/$S//g" "$BLOB" 2>/dev/null | grep -oE '[0-9a-f]{32}' \
      | grep -v "^${A:-zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz}$" | head -1)
fi

# ⚠️ stdin က paste block အတွက် ကုန်သွားသဖြင့် bucket ကို tty ကနေ ဖတ်သည်。
#    tty မရှိလျှင် (pipe ဖြင့် စမ်းသပ်ခြင်း) ပုံသေ သုံးသည် — ကျဘမ်း မလုပ်ဘူး。
B=""
if [ -r /dev/tty ] 2>/dev/null; then
  printf 'Bucket နာမည် [ikki] : '
  read B </dev/tty 2>/dev/null || B=""
  echo
fi
B=$(printf '%s' "$B" | tr -d ' \r\n\t'); [ -z "$B" ] && B=ikki

fail=0
show() { [ -n "$2" ] && echo "✓ $1 · $(printf '%s' "$2" | wc -c | tr -d ' ') လုံး" \
         || { echo "❌ $1 — paste ထဲ မတွေ့"; fail=1; }; }
show "Account ID"        "$A"
show "Access Key ID"     "$K"
show "Secret Access Key" "$S"
[ -n "$A" ] && [ "$A" = "$K" ] && { echo "❌ Account ID နှင့် Access Key ID တူနေသည်"; fail=1; }
if [ "$fail" = 1 ]; then
  echo
  echo "paste ထဲ ဒီ ၃ ခု ရှိရမည် —"
  echo "  Access Key ID      32 လုံး hex"
  echo "  Secret Access Key  64 လုံး hex"
  echo "  Endpoint           https://<32 လုံး>.r2.cloudflarestorage.com"
  exit 1
fi

cp .env .env.bak
grep -v '^R2_' .env > .env.new 2>/dev/null || true
{ echo "R2_ACCOUNT_ID=$A"
  echo "R2_ACCESS_KEY_ID=$K"
  echo "R2_SECRET_ACCESS_KEY=$S"
  echo "R2_BUCKET=$B"; } >> .env.new
mv .env.new .env
chmod 600 .env
echo "✓ .env ထည့်ပြီး (backup: .env.bak)"

echo "── container ပြန်တက်နေသည် ──"
docker compose up -d 2>&1 | tail -2
echo "── R2 ကို သတ်မှတ်ပြီး စမ်းသပ်နေသည် ──"
docker exec ikki python tools/r2_setup.py
echo
echo "✅ ပြီးပါပြီ — UI မှာ ဗီဒီယို တင်ကြည့်ပါ"
