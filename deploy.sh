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

# ⚠️ **job လည်နေစဉ် deploy မလုပ်ရ — rsync မလုပ်ခင်ကတည်းက**。
#    ၂၀၂၆-၀၉-၂၀: ကာကွယ်ချက်ကို worker restart ရှေ့မှာသာ ထားမိပြီး
#    `docker compose up -d --build` က အဲဒီထက် အရင် ဖြစ်သဖြင့် မကာကွယ်နိုင်ခဲ့。
#    container ပြန်တက်နေစဉ် Caddy က **404** ပြန်သည် (502 မဟုတ်) —
#    j_bd28f6df827f က `6/7 sound` ပြီးပြီး stage 7 ပို့ချိန် 02:58:44 မှာ
#    container ပြန်တက်ချိန်နဲ့ တိုက်ပြီး render တစ်ခုလုံး ဆုံးရှုံးခဲ့သည်。
#    ⇒ scratch ပေါ် အလုပ်လုပ်နေသော process ရှိသရွေ့ **ဘာမှ မလုပ်ဘဲ စောင့်**သည်。
#    IKKI_DEPLOY_NOWAIT=1 ပေးမှ ကျော်သည် (တမင် ဆုံးဖြတ်မှသာ)。
# ⚠️ **ffmpeg ကို မစစ်ရ**。 ၂၀၂၆-၀၉-၂၀: ဂရပ်ဖစ် ၂ ခု ကြားမှာ ffmpeg
#    မရှိသော ခဏလေး ရှိသဖြင့် `pgrep -f scratch` က 「job ပြီးပြီ」ဟု
#    ထင်ကာ deploy စပြီး worker ကို pkill လုပ်ရာ render တစ်ခုလုံး
#    သေခဲ့သည် (j_e45a95bd33ea)。 ⇒ worker ကိုယ်တိုင် ချန်ထားသော
#    အမှတ်ဖိုင်ကို စစ်သည် — pid ပါသဖြင့် worker သေပြီးကျန်ခဲ့သော
#    အမှတ်ဟောင်းကို ခွဲခြားပြီး လျစ်လျူရှုနိုင်သည်。
_busy() {
  # ၁) worker ရဲ့ အမှတ်ဖိုင် — အဓိက、မှန်ကန်သော စစ်ချက်
  if [ -f "$HOME/.ikki/busy" ]; then
    _bp=$(awk '{print $1}' "$HOME/.ikki/busy" 2>/dev/null)
    if [ -n "$_bp" ] && kill -0 "$_bp" 2>/dev/null; then return 0; fi
    echo "  ℹ️  အမှတ်ဟောင်း ကျန်နေသည် (pid ${_bp:-?} မရှိတော့) — ရှင်းလိုက်သည်"
    rm -f "$HOME/.ikki/busy"
  fi
  # ၂) အရန် — ffmpeg လည်နေလျှင်လည်း စောင့်သည်。 ဒါက **အလစ်မိတတ်**
  #    (ကတ် ၂ ခုကြား ကွက်လပ် ရှိသည်) ⇒ တစ်ခုတည်း အားမကိုးရ、ဒါပေမယ့်
  #    အမှတ်ဖိုင် မရေးတတ်သေးသော worker ဟောင်းအတွက် အကာအကွယ် ဖြစ်သည်。
  pgrep -f "$HOME/.ikki/scratch" >/dev/null 2>&1
}

if [ "${IKKI_DEPLOY_NOWAIT:-0}" != "1" ]; then
  _w=0
  while _busy; do
    if [ "$_w" -eq 0 ]; then
      echo "⏸  job လည်နေသည် — deploy မစသေးဘဲ စောင့်နေသည် (အများဆုံး ၄၅ မိနစ်)"
      echo "   ကျော်ချင်လျှင် Ctrl-C ပြီး  IKKI_DEPLOY_NOWAIT=1 ./deploy.sh"
    fi
    _w=$((_w + 15))
    if [ "$_w" -gt 2700 ]; then
      echo "⚠️ ၄၅ မိနစ် ကျော်သွားပြီ — deploy ကို **မလုပ်ဘဲ** ရပ်လိုက်သည်。"
      exit 1
    fi
    sleep 15
  done
  [ "$_w" -gt 0 ] && echo "✓ job ပြီးပြီ ($((_w / 60)) မိနစ် စောင့်ခဲ့) — deploy စသည်"
fi

echo "── asset version ──"
~/.ikki/venv/bin/python tools/stamp.py

# ⚠️ **ချန်ထားချက်ကို လက်နဲ့ စာရင်းလုပ်ထားသည် ⇒ repo ပုံစံ ပြောင်းတိုင်း
#    ဟောင်းသွားသည်**。 ၂၀၂၆-၀၉-၂၁ မှာ ဖြစ်ခဲ့သည် —
#      `.git`  — B-roll ၁ GB commit လုပ်လိုက်တော့ ၉၂၈ MB ဖြစ်ပြီး
#                deploy တိုင်း တင်နေသည် (VPS မှာ ၂၀၄ MB ရောက်မှ တွေ့)。
#      `work/` — render scratch ၄၄၁ MB。 VPS မှာ render မလုပ်ပါ。
#    ⚠️ နှစ်ခုလုံး `.gitignore` ထဲ ပါပြီးသား — ဒါပေမယ့် **rsync က
#       gitignore မဖတ်ပါ**。 ချန်ထားချက် နှစ်နေရာ သီးသန့် ထိန်းရသည်。
# ⚠️ မှတ်ချက်ကို backtick (`# …`) နဲ့ command ထဲ မထည့်ရ — မှတ်ချက်ထဲ
#    backtick တစ်လုံး ပါမိလျှင် script တစ်ခုလုံး ပျက်သည် (တကယ် ဖြစ်ခဲ့ပြီး
#    worker ပြန်မစဘဲ ကျန်ခဲ့သည်)。 `sh -n` ကလည်း မဖမ်းမိပါ。
#    2026-09-26: assets/broll_bank (3.7 GB) + music_bank (876 MB) were being
#    shipped although only the Mac worker reads them and .dockerignore drops
#    assets/ from the image anyway.
echo "── rsync (.env ချန်) ──"
rsync -az \
  --exclude='.env' --exclude='.env.*' \
  --exclude='.venv' --exclude='data' --exclude='__pycache__' \
  --exclude='._*' \
  --exclude='assets/broll/clips' --exclude='assets/broll/stock_ja' \
  --exclude='assets/broll_bank' --exclude='assets/music_bank' \
  --exclude='.git' --exclude='tests' \
  --exclude='work' --exclude='scratch' --exclude='reports' \
  ./ root@srv1866621.hstgr.cloud:/srv/ikki/

# ── which worker renders — exactly ONE ─────────────────────────────────
# ⚠️ 2026-09-26: `docker compose up -d --build` started the VPS worker too,
#    then this script restarted the Mac worker; the worker guard (53c07a7)
#    rightly refused to run a second one, so production silently switched to
#    the VPS worker — which has no CoreText and no Pyidaungsu.  The guard was
#    right; this script was wrong.  Now one worker is chosen by config:
#      ~/.ikki/worker_host  →  mac | vps      (IKKI_WORKER_HOST overrides)
#    default mac — Burmese shaping (CoreText) is IKKI's foundation (Zin).
WH="${IKKI_WORKER_HOST:-$(cat "$HOME/.ikki/worker_host" 2>/dev/null || echo mac)}"
case "$WH" in mac|vps) ;; *) echo "⚠️ worker_host '$WH' — mac သို့ vps သာ"; exit 1 ;; esac
echo "── worker host: $WH ──"

echo "── rebuild ──"
if [ "$WH" = "vps" ]; then
  ssh root@srv1866621.hstgr.cloud 'cd /srv/ikki && docker compose up -d --build 2>&1 | tail -2'
else
  ssh root@srv1866621.hstgr.cloud 'cd /srv/ikki && docker compose up -d --build ikki 2>&1 | tail -2 && docker compose stop ikki-worker 2>&1 | tail -1'
fi
sleep 8

# ⚠️ worker က Mac မှာ **ကုဒ်ကို တစ်ခါပဲ ဖတ်**သည် — ဖိုင် ပြင်ရုံနှင့် မရ、
#    process ကို ပြန်စရမည်。 မလုပ်မိသဖြင့် ပုံစံ ပြင်ချက်က render ကို
#    မရောက်ခဲ့ပြီး "override အလုပ်မလုပ်ဘူး" ဟု ထင်မှားခဲ့သည်。
# ⚠️ shell ကနေ လည်နေသော worker ရှိလျှင် **launchd ကို မတင်ရ** — worker
#    နှစ်ခု ဖြစ်ပြီး job ချင်း လုယက်မည်。 shell worker ကို သုံးရခြင်းက
#    launchd agent မှာ Full Disk Access မရှိ၍ `/Volumes` ကို မရေးနိုင်သောကြောင့်
#    (၂၀၂၆-၀၉-၂၀: Mac ထဲ ၃ GB ပဲ ကျန်ပြီး job တစ်ခုက ၂.၇ GB လိုသည်)。
#    ⇒ ဒီအခြေအနေမှာ shell worker ကိုပဲ ပြန်စသည်。
_SHW=$(pgrep -f "IKKI_SHELL_WORKER=1" 2>/dev/null | head -1)
_LOG0=$(wc -l < "$HOME/.ikki/worker.log" 2>/dev/null || echo 0)
if [ "$WH" = "vps" ]; then
  echo "── Mac worker ရပ် (VPS worker သုံးသည်) ──"
  pkill -f "worker/run.py" 2>/dev/null || true
  if launchctl list | grep -q com.ikki.worker; then
    launchctl unload ~/Library/LaunchAgents/com.ikki.worker.plist 2>/dev/null || true
  fi
elif [ -n "$_SHW" ] || [ -f "$HOME/.ikki/shell_worker" ]; then
  echo "── worker ပြန်စ (shell) ──"
  pkill -f "worker/run.py" 2>/dev/null || true
  sleep 2
  # ⚠️ **fd သုံးခုလုံး ဖြတ်ရမည်** — ၂၀၂၆-၀၉-၂၀: worker က deploy.sh ရဲ့
  #    stdout pipe ကို အမွေဆက်ခံပြီး ဖွင့်ထားသဖြင့် `./deploy.sh | tail`
  #    က **၅၄ မိနစ် မပြီးဘဲ** ကျန်နေခဲ့သည် (health · R2 စစ်ချက် မရောက်)。
  #    `setsid` ရှိလျှင် session ခွဲသည် — မရှိလျှင် nohup + fd ပိတ်။
  if command -v setsid >/dev/null 2>&1; then _SS=setsid; else _SS=""; fi
  ( cd "$HOME/ikki" && env $(cat "$HOME/.ikki/shell_worker" | tr '\n' ' ') \
      $_SS nohup "$HOME/.ikki/venv/bin/python" worker/run.py \
      < /dev/null >> "$HOME/.ikki/worker.log" 2>&1 & ) &
  # ⚠️ pgrep alone lied: a worker the guard refused was still alive for a
  #    few seconds and got a ✓.  Wait past the guard, then read its log.
  sleep 15
  if tail -n +"$((_LOG0 + 1))" "$HOME/.ikki/worker.log" 2>/dev/null | grep -q "⛔"; then
    echo "  ⛔ Mac worker က စတင်ရန် ငြင်းသည်:"
    tail -n +"$((_LOG0 + 1))" "$HOME/.ikki/worker.log" | grep "⛔" | tail -2
    exit 1
  fi
  pgrep -f "worker/run.py" >/dev/null && echo "  ✓ shell worker တက်ပြီ" || { echo "  ⚠️ worker မတက်"; exit 1; }
  echo "  ℹ️  Full Disk Access ပေးပြီးလျှင် rm ~/.ikki/shell_worker ⇒ launchd ပြန်သုံးမည်"
else
echo "── worker ပြန်စ ──"
if launchctl list | grep -q com.ikki.worker; then
  launchctl unload ~/Library/LaunchAgents/com.ikki.worker.plist 2>/dev/null || true
fi
launchctl load ~/Library/LaunchAgents/com.ikki.worker.plist
sleep 6
launchctl list | grep com.ikki.worker || echo "  ⚠️ worker မတက်"
fi

echo "── health ──"
curl -s -m 15 https://ikki.srv1866621.hstgr.cloud/api/health; echo
echo "── R2 ──"
ssh root@srv1866621.hstgr.cloud 'docker exec ikki python -c "
import sys; sys.path.insert(0,\"/app/core\")
import store as S
print(\"   R2:\", \"ဖွင့်ထား\" if S.on() else \"ပိတ်ထား (local disk mode)\")"'
