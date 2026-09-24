#!/bin/sh
# Deploy IKKI's API and the single production render worker to the VPS.
# This stages only runtime material: it never transfers .env, render caches,
# git history, or Motion Kit's macOS-only CoreText binary.
set -eu

REPO_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VPS_HOST=${IKKI_VPS_HOST:-ikki.srv1866621.hstgr.cloud}
VPS_USER=${IKKI_VPS_USER:-root}
REMOTE="${VPS_USER}@${VPS_HOST}"
REMOTE_DIR=${IKKI_REMOTE_DIR:-/srv/ikki}
MOTIONKIT_SOURCE=${IKKI_MOTIONKIT_SOURCE:-/Applications/my\ file/My\ bussiness/ZAE\ NEW　OPERATION/N8N\ Work\ Flow/n8n\ All\ Workflow/motionkit}
PYTHON_BIN=${IKKI_PYTHON:-python3}
SSH_KNOWN_HOSTS=${IKKI_SSH_KNOWN_HOSTS:-/private/tmp/ikki-vps-known-hosts}
SSH_OPTS="-o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=$SSH_KNOWN_HOSTS"

cd "$REPO_DIR"

if [ ! -d "$MOTIONKIT_SOURCE" ]; then
  echo "Motion Kit source not found: $MOTIONKIT_SOURCE" >&2
  exit 1
fi

# A busy marker is created by worker/run.py for the entire final render.  A
# marker without a live process is harmless in this first rollout; later
# deployments may explicitly use IKKI_DEPLOY_NOWAIT=1 after checking logs.
worker_busy() {
  ssh $SSH_OPTS "$REMOTE" 'cid=$(docker ps -q --filter "name=^/ikki-worker$"); [ -n "$cid" ] || exit 1; docker exec "$cid" test -f /scratch/busy' >/dev/null 2>&1
}

if [ "${IKKI_DEPLOY_NOWAIT:-0}" != "1" ]; then
  waited=0
  while worker_busy; do
    if [ "$waited" -eq 0 ]; then
      echo "Render is active; waiting before deployment (set IKKI_DEPLOY_NOWAIT=1 only to override)."
    fi
    if [ "$waited" -ge 2700 ]; then
      echo "Timed out after 45 minutes without interrupting the render." >&2
      exit 1
    fi
    sleep 15
    waited=$((waited + 15))
  done
fi

echo "== Stamp browser assets =="
"$PYTHON_BIN" tools/stamp.py

echo "== Stage code (secrets and local output excluded) =="
rsync -az -e "ssh $SSH_OPTS" \
  --exclude='.env' --exclude='.env.*' \
  --exclude='.git' --exclude='.venv' --exclude='data' --exclude='runtime' \
  --exclude='assets' --exclude='work' --exclude='scratch' --exclude='reports' \
  --exclude='__pycache__' --exclude='._*' --exclude='.DS_Store' \
  ./ "$REMOTE:$REMOTE_DIR/"

echo "== Stage curated IKKI assets =="
ssh $SSH_OPTS "$REMOTE" "mkdir -p '$REMOTE_DIR/runtime/assets' '$REMOTE_DIR/runtime/motionkit/work'"
rsync -a --partial --inplace -e "ssh $SSH_OPTS" \
  --exclude='._*' --exclude='.DS_Store' --exclude='__pycache__' \
  assets/ "$REMOTE:$REMOTE_DIR/runtime/assets/"

echo "== Stage portable Motion Kit runtime =="
rsync -a --partial --inplace -e "ssh $SSH_OPTS" \
  --exclude='.git' --exclude='work' --exclude='out' --exclude='docs' \
  --exclude='cttext' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='._*' --exclude='.DS_Store' \
  "$MOTIONKIT_SOURCE/" "$REMOTE:$REMOTE_DIR/runtime/motionkit/"

# A prior manual deployment may have left this macOS executable behind.
# Preserve it under a timestamped backup rather than deleting an unknown file.
ssh $SSH_OPTS "$REMOTE" "if [ -f '$REMOTE_DIR/runtime/motionkit/cttext' ]; then mkdir -p '$REMOTE_DIR/runtime/backup'; mv '$REMOTE_DIR/runtime/motionkit/cttext' '$REMOTE_DIR/runtime/backup/cttext.macos.'\$(date +%Y%m%d%H%M%S); fi"

echo "== Build and start API + render worker =="
ssh $SSH_OPTS "$REMOTE" "cd '$REMOTE_DIR' && docker compose up -d --build"

echo "== Verify worker runtime =="
ssh $SSH_OPTS "$REMOTE" "docker exec ikki-worker python /app/tools/worker_preflight.py"

echo "== Verify API and containers =="
ssh $SSH_OPTS "$REMOTE" "cd '$REMOTE_DIR' && docker compose ps && docker exec ikki python -c 'import urllib.request; print(urllib.request.urlopen(\"http://127.0.0.1:8080/api/health\", timeout=10).read().decode())' && docker logs --tail 35 ikki-worker"

echo "Deployment complete: https://$VPS_HOST"
