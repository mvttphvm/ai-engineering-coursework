#!/usr/bin/env bash
# Resolve — one-shot setup for Matt's Mac.
# Run from the project folder:   bash scripts/setup_mac.sh
# It is safe to re-run: every step is idempotent.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Resolve setup starting in: $(pwd)"

# 1) Python 3.11+ check -------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python 3.11+ from https://www.python.org/downloads/ and re-run."
  exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"ERROR: Python 3.11+ required, found {sys.version.split()[0]}")
print(f"==> Python OK: {sys.version.split()[0]}")
PY

# 2) Docker check (optional — the app falls back to an in-memory store) -------
if command -v docker >/dev/null 2>&1; then
  echo "==> Docker found."
  DOCKER_OK=1
else
  echo "WARNING: Docker not found. Resolve will still run (in-memory store),"
  echo "         but for the real Postgres + pgvector database install Docker"
  echo "         Desktop from https://www.docker.com/products/docker-desktop/"
  DOCKER_OK=0
fi

# 3) Virtual environment + dependencies ---------------------------------------
if [ ! -d .venv ]; then
  echo "==> Creating .venv ..."
  python3 -m venv .venv
fi
echo "==> Installing dependencies (first run downloads a lot — be patient)..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "==> Dependencies installed."

# 4) .env ----------------------------------------------------------------------
if [ ! -f .env ]; then
  cp .env.example .env
  echo "==> Created .env from .env.example (you'll add your free keys below)."
else
  echo "==> .env already exists — leaving it untouched."
fi

# 5) Database ------------------------------------------------------------------
if [ "$DOCKER_OK" = "1" ]; then
  echo "==> Starting the Postgres + pgvector database (docker compose)..."
  docker compose up -d db
else
  echo "==> Skipping database start (no Docker). App will use the in-memory store."
fi

# 6) Tests ---------------------------------------------------------------------
echo "==> Running the test suite (fully offline)..."
.venv/bin/python -m pytest tests/ -q

cat <<'EOF'

==> SETUP COMPLETE. Your next steps:

1) Add your FREE LLM keys to .env (no credit card for either):
   - Gemini: https://aistudio.google.com/apikey  -> paste into GEMINI_API_KEY=
   - Groq:   https://console.groq.com/keys       -> paste into GROQ_API_KEY=
   (Optional, fully local instead: install Ollama from https://ollama.com
    and run `ollama pull llama3.1:8b` — then no keys are needed at all.)

2) Load the sample knowledge base and start the server:
     source .venv/bin/activate
     uvicorn app.main:app --reload
   Then in another terminal:
     curl -X POST localhost:8000/ingest -H 'Content-Type: application/json' \
          -d '{"directory": "data/sample_kb"}'
     curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
          -d '{"question": "How do I reset my password?"}'
   Interactive API docs: http://localhost:8000/docs

3) Run the eval harness:
     python -m evals.run

4) Full Docker stack instead of local Python:
     docker compose up --build

5) Already wired in, nothing to do:
   - Caching is ON by default for /search and /ask (see CACHE_* in .env;
     responses carry an X-Cache: HIT/MISS header; set CACHE_ENABLED=false
     to turn it off).
   - Tracing is OPTIONAL and off: free Langfuse keys (no credit card)
     from https://cloud.langfuse.com go into LANGFUSE_PUBLIC_KEY /
     LANGFUSE_SECRET_KEY in .env; leave them blank and nothing is sent.
   - CI: if you push this folder to GitHub, Actions runs the test suite
     plus the eval regression gate on every push and PR
     (.github/workflows/ci.yml).
EOF
