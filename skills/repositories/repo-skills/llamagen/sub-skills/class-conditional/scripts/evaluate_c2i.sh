#!/usr/bin/env bash
set -euo pipefail

# c2i evaluation wrapper for a reference .npz and a sample .npz.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"

exec python3 evaluations/c2i/evaluator.py "$@"
