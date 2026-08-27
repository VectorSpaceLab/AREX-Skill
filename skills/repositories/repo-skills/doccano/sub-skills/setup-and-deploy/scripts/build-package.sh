#!/usr/bin/env bash
set -euo pipefail

repo_root="${1:-$(pwd)}"
frontend_dir="$repo_root/frontend"
backend_dir="$repo_root/backend"
temp_pyproject="$repo_root/pyproject.toml"

command -v yarn >/dev/null 2>&1 || {
  echo "yarn is required for the frontend build step" >&2
  exit 1
}
command -v poetry >/dev/null 2>&1 || {
  echo "poetry is required for the backend package build step" >&2
  exit 1
}

cleanup() {
  rm -f "$temp_pyproject"
}
trap cleanup EXIT

mkdir -p "$backend_dir/client"

echo "== frontend build =="
cd "$frontend_dir"
export PUBLIC_PATH="/static/_nuxt/"
yarn install
yarn build
cp -r dist "$backend_dir/client/"

echo "== backend install and static collection =="
cd "$backend_dir"
poetry install
poetry run task collectstatic

echo "== package build =="
cd "$repo_root"
cp "$backend_dir/pyproject.toml" "$temp_pyproject"
python_bin="${PYTHON_BIN:-python}"
"$python_bin" - "$temp_pyproject" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
path.write_text(path.read_text().replace(', from = ".."', ''))
PY
poetry build

echo "Built sdist and wheel under $repo_root/dist/"
