FROM python:3.12-slim
WORKDIR /app
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ /app/api/
COPY web/ /app/web/
# ⚠️ store.py က stdlib ပဲ သုံးသည် — core တစ်ခုလုံး မကူးဘူး (image သေးစေရန်)。
#    မကူးမိလျှင် `ModuleNotFoundError: store` နှင့် **site တစ်ခုလုံး ကျသည်**
#    (တကယ် ဖြစ်ခဲ့ — Bad Gateway)。 main.py မှာလည်း fallback ထားသည်。
COPY core/store.py /app/core/store.py
COPY core/formats.py /app/core/formats.py
# ⚠️ API က recipes (ပုံစံ ဘောင်စစ်မှု) နှင့် fonts (ဖောင့် စာရင်း) လိုသည် —
#    မကူးလျှင် /api/styles က 500 ပြန်သည် (တကယ် ဖြစ်ခဲ့)。 နှစ်ခုလုံး
#    stdlib ပဲ သုံးသဖြင့် image မကြီးဘူး。
COPY core/recipes.py /app/core/recipes.py
COPY core/fonts.py /app/core/fonts.py
# ⚠️ palette = logo → brand အရောင် (Pillow လိုသည်) · gemguard = Gemini ခေါ်ရန်
#    (AI ဖောင့် ရွေးပေးခြင်း)。 မကူးလျှင် အဲဒီ endpoint ၂ ခု 500 ပြန်သည်。
COPY core/palette.py /app/core/palette.py
COPY core/gemguard.py /app/core/gemguard.py
COPY tools/ /app/tools/
ENV IKKI_DB=/data/ikki.db IKKI_DATA=/data IKKI_WEB=/app/web
EXPOSE 8080
CMD ["uvicorn","main:app","--app-dir","api","--host","0.0.0.0","--port","8080"]
