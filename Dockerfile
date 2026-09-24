# IKKI production images.  The public API and renderer intentionally have
# separate targets: a failed/heavy render cannot take the editor UI offline.
FROM python:3.12-slim AS base
WORKDIR /app

# ffmpeg/ffprobe make the actual edit; librsvg + open fonts are the Linux
# implementation of Motion Kit's text renderer.  Do not copy the macOS
# CoreText binary (`cttext`) into this image.
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ffmpeg librsvg2-bin fontconfig fonts-noto-core fonts-noto-cjk fonts-sil-padauk ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt /tmp/api-requirements.txt
COPY worker/requirements.txt /tmp/worker-requirements.txt
RUN pip install --no-cache-dir -r /tmp/api-requirements.txt -r /tmp/worker-requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/core

FROM base AS api
COPY api/ /app/api/
COPY web/ /app/web/
# The API imports a few core modules today.  Copying the complete source keeps
# an API feature from silently disappearing when a new safe core import is added.
COPY core/ /app/core/
COPY tools/ /app/tools/
ENV IKKI_DB=/data/ikki.db IKKI_DATA=/data IKKI_WEB=/app/web
EXPOSE 8080
CMD ["uvicorn", "main:app", "--app-dir", "api", "--host", "0.0.0.0", "--port", "8080"]

FROM base AS worker
COPY worker/ /app/worker/
COPY core/ /app/core/
COPY tools/ /app/tools/
RUN mkdir -p /app/assets /scratch /worker-home
ENV HOME=/worker-home \
    IKKI_ASSETS=/app/assets \
    IKKI_SCRATCH=/scratch \
    IKKI_BIG=/scratch/big \
    IKKI_BUSY=/scratch/busy \
    MK_TEXT=rsvg
CMD ["python", "/app/worker/run.py"]
