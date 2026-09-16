# VPS ချိတ်ဆက်မှု — လုပ်ပြီးပါပြီ

```
https://ikki.srv1866621.hstgr.cloud
```

## ဘယ်လို ချိတ်ထားလဲ

```
        သုံးစွဲသူ (browser)
              │ HTTPS
              ▼
   ┌──────────────────────────┐
   │  VPS · 187.77.128.229    │   traefik (TLS အလိုအလျောက်)
   │  ├── traefik             │   ကုဒ်: /srv/ikki
   │  ├── n8n  ────────────┐  │   volume: ikki_ikki_data
   │  ├── ikki  ← web+API  │  │
   │  └── network n8n_default  │
   └──────────┬───────────────┘
              │ ① worker က ဆွဲယူ (HTTPS · ၆s တစ်ကြိမ်)
              │ ② မြန်မာ ASR — n8n Gemini proxy
              ▼
        Mac M1 (အိမ်) · render
```

⚠️ **worker က ဆွဲယူသည် — VPS က မခေါ်**。 အိမ်က Mac သည် NAT နောက်တွင် ရှိ၍
   အပြင်မှ ခေါ်၍ မရ။ port forward မလို · VPN မလို。

## DNS

`*.srv1866621.hstgr.cloud` က VPS IP ကို ညွှန်ပြီးသား (wildcard) —
**DNS လုပ်စရာ မလို**。 `getikki.com` သုံးချင်လျှင် A record တစ်ခု ထည့်ရုံ:

```
app.getikki.com   A   187.77.128.229
```
ပြီးလျှင် `.env` ထဲ `IKKI_HOST=app.getikki.com` ပြောင်း၊ `docker compose up -d`。
traefik က Let's Encrypt ကို အလိုအလျောက် ယူသည်။

## Token

`.env` ထဲမှာ ရှိသည် (VPS ရော Mac ရော)。

| | |
|---|---|
| `IKKI_USER_TOKEN` | web ဝင်ရန် — ပထမအကြိမ် browser က တောင်းသည် |
| `IKKI_WORKER_TOKEN` | Mac worker အတွက် |

⚠️ token မပါလျှင် **401** ပြန်သည် (စစ်ပြီး)。

## Mac worker စတင်ရန်

```bash
cd "/Volumes/i/Editing Application/ikki"
IKKI_API=https://ikki.srv1866621.hstgr.cloud \
IKKI_WORKER_TOKEN=$(grep IKKI_WORKER_TOKEN .env | cut -d= -f2) \
  ~/.ikki/venv/bin/python worker/run.py
```

## ပြင်ပြီး ပြန်တင်ရန်

```bash
rsync -az --exclude='.venv' --exclude='data' ./ root@srv1866621.hstgr.cloud:/srv/ikki/
ssh root@srv1866621.hstgr.cloud 'cd /srv/ikki && docker compose up -d --build'
```

## စစ်ဆေးပြီးသား

| | |
|---|---|
| HTTPS + TLS | ✅ HTTP/2 200 |
| token မပါ → 401 | ✅ |
| ဖိုင်တင် → job → worker → ဒေါင်း | ✅ (VPS နှင့် ၈၉.၅s) |
| ဖြတ်ချက် ၁၂ ခု · စကားထဲ **၀/၂၄** | ✅ |

## Data ဘယ်မှာ ရှိလဲ

| | |
|---|---|
| **VPS** `ikki_ikki_data` volume | database · တင်ထားသော ဗီဒီယို · ပြီးသား ဗီဒီယို |
| **Mac** `~/.ikki/scratch` | render လုပ်နေစဉ် ယာယီ — ပြီးလျှင် ဖျက် |
| **Mac** `~/.ikki/data` | စက်တွင်း စမ်းသပ်မှုအတွက်သာ (VPS နှင့် မဆိုင်) |

⚠️ **အားလုံး Mac ထဲမှာပဲ ထားချင်လျှင်** — VPS ကို မသုံးဘဲ Mac ပေါ်မှာ API
   run ပြီး Cloudflare Tunnel ဖြင့် အပြင်ကို ဖွင့်လို့ရသည် (port forward မလို)。
   အဲဒီအခါ ဖိုင်တစ်ခုမှ VPS ကို မရောက်။

---

## R2 (object storage) ချိတ်ခြင်း

ဗီဒီယိုက VPS ကို မဖြတ်တော့ဘဲ Cloudflare R2 ကို တိုက်ရိုက် သွားစေရန်။
**ဘာလို့ လိုအပ်လဲ** — တိုင်းထားသည်: output က ၇၃ MB/မိနစ်၊ VPS↔Mac လိုင်းက
၆ Mbps ပဲ။ ၄၁၉ MB ဖိုင်တစ်ခုက ဆွဲချရုံ ၈ မိနစ် ကြာခဲ့သည် (job စုစုပေါင်း
၆၃၈s ထဲ ၄၈၀s)။ R2 မှာ egress အလကား၊ VPS ကို လုံးဝ မဖြတ်ဘူး။

### ၁။ Cloudflare မှာ လုပ်ရန်
1. R2 → Create bucket → နာမည် `ikki`
2. R2 → Manage API Tokens → **Object Read & Write** token ဖန်တီး
3. Account ID · Access Key ID · Secret Access Key ကို မှတ်ထား

### ၂။ VPS မှာ
`/srv/ikki/.env` ထဲ ထည့်:
```
R2_ACCOUNT_ID=xxxxxxxx
R2_ACCESS_KEY_ID=xxxxxxxx
R2_SECRET_ACCESS_KEY=xxxxxxxx
R2_BUCKET=ikki
```
ပြီးလျှင်:
```
docker compose up -d --build
docker exec -e R2_ACCOUNT_ID=… -e R2_ACCESS_KEY_ID=… \
  -e R2_SECRET_ACCESS_KEY=… -e R2_BUCKET=ikki \
  ikki python tools/r2_setup.py
```
`r2_setup.py` က CORS (ETag ဖတ်လို့ရအောင်) + retention (uploads ၂ ရက် ·
out ၇ ရက်) သတ်မှတ်ပြီး တင်/ဖတ်/multipart ကို စမ်းသပ်ပြသည်။

### ၃။ Mac worker မှာ
R2 env **မလိုပါ** — worker က API ဆီက presigned URL ကို ယူသုံးသည်။

### ၄။ ပြန်ပိတ်ချင်လျှင်
`.env` ထဲက R2_* ကို ဖျက်ပြီး `docker compose up -d` — local disk mode ပြန်ရသည်။
ရှိပြီးသား R2 ဖိုင်တွေက `out_key` နဲ့ မှတ်ထားသဖြင့် ဆက်ဒေါင်းလို့ ရသည်။
