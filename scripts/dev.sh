#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$repo_dir/.venv/bin/python"

if [[ ! -x "$python_bin" ]]; then
  echo "Missing .venv. Follow the installation steps in README.md." >&2
  exit 1
fi

cleanup() {
  kill "$solver_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "$repo_dir"
"$python_bin" -m uvicorn app:app --app-dir solver --reload --host 127.0.0.1 --port 8000 &
solver_pid=$!
npm run dev:mock --workspace add-on
