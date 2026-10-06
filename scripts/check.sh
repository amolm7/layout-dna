#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

npm run typecheck
npm run lint
npm test
npm run build

python_bin="python3"
if [[ -x "$repo_dir/.venv/bin/python" ]]; then
  python_bin="$repo_dir/.venv/bin/python"
fi

"$python_bin" -m ruff check solver
"$python_bin" -m pytest solver/tests

