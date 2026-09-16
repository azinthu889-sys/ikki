#!/bin/sh
# IKKI · VPS ကို တင်ခြင်း
#
# ⚠️ **.env ကို ဘယ်တော့မှ မတင်ရ**。 အဲဒါ server ပိုင်ဆိုင်သော
#    secret ဖိုင် — တင်လိုက်လျှင် R2 key တွေ **ပျက်သွားသည်** (တကယ်
#    ဖြစ်ခဲ့ပြီး Zin ရဲ့ R2 token ပျက်ခဲ့သည်、ပြန်ရလည်း မရ)。
# ⚠️ stamp.py ကို အရင် run ရမည် — မလုပ်လျှင် browser က အရင် app.js ကို
#    ဆက်သုံးပြီး ပြင်ထားတာ မမြင်ရဘူး。
set -e
cd "$(dirname "$0")"

echo "── asset version ──"
~/.ikki/venv/bin/python tools/stamp.py

echo "── rsync (.env ချန်) ──"
rsync -az \
  --exclude='.env' --exclude='.env.*' \
  --exclude='.venv' --exclude='data' --exclude='__pycache__' \
  --exclude='._*' --exclude='assets/broll/clips' \
  ./ root@srv1866621.hstgr.cloud:/srv/ikki/

echo "── rebuild ──"
ssh root@srv1866621.hstgr.cloud 'cd /srv/ikki && docker compose up -d --build 2>&1 | tail -2'
sleep 8

# ⚠️ worker က Mac မှာ **ကုဒ်ကို တစ်ခါပဲ ဖတ်**သည် — ဖိုင် ပြင်ရုံနှင့် မရ、
#    process ကို ပြန်စရမည်。 မလုပ်မိသဖြင့် ပုံစံ ပြင်ချက်က render ကို
#    မရောက်ခဲ့ပြီး "override အလုပ်မလုပ်ဘူး" ဟု ထင်မှားခဲ့သည်。
echo "── worker ပြန်စ ──"
if launchctl list | grep -q com.ikki.worker; then
  launchctl unload ~/Library/LaunchAgents/com.ikki.worker.plist 2>/dev/null || true
fi
launchctl load ~/Library/LaunchAgents/com.ikki.worker.plist
sleep 6
launchctl list | grep com.ikki.worker || echo "  ⚠️ worker မတက်"

echo "── health ──"
curl -s -m 15 https://ikki.srv1866621.hstgr.cloud/api/health; echo
echo "── R2 ──"
ssh root@srv1866621.hstgr.cloud 'docker exec ikki python -c "
import sys; sys.path.insert(0,\"/app/core\")
import store as S
print(\"   R2:\", \"ဖွင့်ထား\" if S.on() else \"ပိတ်ထား (local disk mode)\")"'
