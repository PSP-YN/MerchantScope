#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ ! -d backend/.venv ]]; then python3 -m venv backend/.venv; fi
source backend/.venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
[[ -f backend/.env ]] || cp backend/.env.example backend/.env
[[ -f frontend/.env.local ]] || cp frontend/.env.example frontend/.env.local
(cd backend && exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000) &
API_PID=$!
(cd frontend && npm install && exec npm run dev) &
WEB_PID=$!
cleanup(){ kill "$API_PID" "$WEB_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
wait
