# IKKI 一気

မလိုတာ အမြန် ဖြတ်။ တစ်ချက်တည်းနဲ့ အကုန်။

```
ikki/
├── api/      FastAPI + SQLite — web နှင့် worker နှစ်ဖက်စလုံး ဒီကို ခေါ်သည်
├── web/      static frontend (build step မလို)
├── worker/   Mac worker — HTTPS ဖြင့် job ဆွဲယူသည်
└── Dockerfile · docker-compose.yml
```

## ⚠️ ဒီ disk က ExFAT — သိထားရမည်

**ကုဒ်ပဲ ဒီမှာ ထားပါ။** အောက်ပါတို့ကို Mac ထဲမှာ ထားရမည် —

| | ဘာလို့ |
|---|---|
| `~/.ikki/venv` | ExFAT မှာ `.pth` ဖိုင် corrupt ဖြစ်သည် (**တကယ် ဖြစ်ခဲ့**) |
| `~/.ikki/data` | SQLite — journal/fsync မယုံရ |
| `~/.ikki/scratch` | PNG သေးသေး ရေးတာ **၂၀ ဆ နှေး** (တိုင်းပြီး) |

`._*` ဖိုင်တွေက macOS က permission အတုလုပ်ထားတာ — `find . -name "._*" -delete`

## စက်တွင်း စမ်းရန်

```bash
python3 -m venv ~/.ikki/venv
~/.ikki/venv/bin/pip install -r api/requirements.txt

IKKI_DB=$HOME/.ikki/data/ikki.db IKKI_DATA=$HOME/.ikki/data IKKI_WEB="$PWD/web" \
  ~/.ikki/venv/bin/uvicorn main:app --app-dir api --host 127.0.0.1 --port 8080

IKKI_API=http://127.0.0.1:8080 ~/.ikki/venv/bin/python worker/run.py
```

`http://127.0.0.1:8080` ဖွင့်ပါ။

## VPS သို့ တင်ရန်

```bash
cp .env.example .env && nano .env      # TOKEN ၂ ခု ပြောင်းပါ
docker compose up -d --build
```

traefik က `n8n_default` network ပေါ်မှာ ရှိပြီးသားမို့ TLS အလိုအလျောက် ရသည်။

Mac worker က —

```bash
IKKI_API=https://app.getikki.com IKKI_WORKER_TOKEN=<token> \
  ~/.ikki/venv/bin/python worker/run.py
```

## API

| | |
|---|---|
| `POST /api/upload/init` → `PUT /chunk?offset=` | ပြတ်လျှင် ဆက်တင် — offset ကို **server က ဖိုင်အရွယ်နဲ့ တိုင်း** |
| `POST /api/jobs` · `GET /api/jobs/{id}` | job |
| `POST /api/jobs/{id}/cancel` | **သုံးထားသော မိနစ် ပြန်ထည့်** |
| `POST /api/w/claim` | worker က ဆွဲယူ (server က NAT နောက်က Mac ကို မခေါ်နိုင်) |
| `POST /api/w/{id}/fail` | **မိနစ် ပြန်ထည့်** — ပျက်သွားတာအတွက် မယူ |

## core/ — တိုင်းထားသော အပိုင်း

| ဖိုင် | ဘာလုပ်လဲ |
|---|---|
| `measure.py` | အသံ band RMS · ကြမ်းပြင်အဆင့် · တိတ်ဆိတ်မှု · စကားပြောချိန် |
| `cut.py` | ဖြတ်တောက် အစီအစဉ် — **တိတ်ဆိတ်မှုအထဲမှာသာ** |
| `spans.py` | span အလိုက် ဖြတ်/ပေါင်း · အသံအဆင့် ညှိ |
| `recipes.py` | ၉ ပုံစံ — parameter ပဲ၊ ကုဒ် မဟုတ် |

### တိုင်းထားသော ရလဒ် (podcast စကားပြောသံ ၇၄၆s)

| recipe | ဖြတ် | ဖြုတ် | ကျန် | **စကားထဲ** |
|---|---|---|---|---|
| cinematic-vlog | 11 | 19.3s | 94% | **0** |
| vlog | 23 | 25.7s | 91% | **0** |
| podcast | 61 | 36.5s | 88% | **0** |
| short-video | 78 | 42.0s | 86% | **0** |
| course | 0 | 0.0s | 100% | **0** |

⚠️ `in_speech > 0` ဖြစ်လျှင် worker က **မထုတ်ဘဲ ပျက်သွားသည်** — ကတိကို ကုဒ်ထဲ ထည့်ထားသည်။

### တိုင်းပြီးမှ သိရသော အချက် ၃ ခု

1. **module နာမည် တိုက်ခြင်း** — motionkit မှာလည်း `render.py` ရှိ၍ မှားယူသွားသည်။ `spans.py` ဟု ခွဲထားသည်။
2. **loudnorm ကို နှစ်ကြိမ် တိုင်းရမည်** — တစ်ကြိမ်တည်းဆို ပစ်မှတ် −14.0 အစား **−15.9** ထွက်သည်။ နှစ်ကြိမ်ဆို −14.4။
3. **ExFAT မှာ venv မဆောက်ရ** — `.pth` corrupt ဖြစ်ပြီး Python မတက်တော့။

## ကျန်နေသေးသည်

- **မြန်မာ ASR** — whisper က မြန်မာလို **လုံးဝ မရ** (model ၂ ခုလုံး စမ်းပြီး)။ Gemini လမ်းကြောင်း ဆက်တပ်ရန်
- ထပ်နေတဲ့စကား ဖြုတ်ခြင်း — `findrepeat.py` (အသံ ဆင်တူမှု ၀.၈၇+) ဆက်တပ်ရန်
- စာတန်း PNG ကို တကယ် ထပ်ရန် (ယခု lower third ပဲ)
- login (ယခု token တစ်ခုတည်း) · ဖြတ်စာရင်း အတည်ပြု UI ↔ API
