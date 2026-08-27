#!/usr/bin/env bash
# Safer wrapper for MineContext's backend PyInstaller build.
# It delegates to the checkout's build.sh/build.bat-equivalent flow on Unix-like
# hosts, verifies the expected onedir executable, and can copy it into
# frontend/backend/. It intentionally warns before mutating build outputs.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: build_backend.sh [--repo-root DIR] [--yes] [--copy-to-frontend] [--skip-preflight]

Build the MineContext PyInstaller backend executable from a checkout root.

Options:
  --repo-root DIR       Repository root. If omitted, search upward from $PWD.
  --yes                 Acknowledge that the build mutates dist/ and build/.
  --copy-to-frontend    After backend build, run frontend/scripts/copy-prebuilt-backend.js.
  --skip-preflight      Do not run the bundled packaging preflight first.
  -h, --help            Show this help.

Mutation warning:
  The underlying build removes and recreates root dist/ and build/. The optional
  copy step removes and recreates frontend/backend/.
USAGE
}

repo_root=""
yes=false
copy_to_frontend=false
skip_preflight=false
while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo-root)
      [ "$#" -ge 2 ] || { echo "ERROR: --repo-root requires a directory" >&2; exit 2; }
      repo_root="$2"
      shift 2
      ;;
    --yes)
      yes=true
      shift
      ;;
    --copy-to-frontend)
      copy_to_frontend=true
      shift
      ;;
    --skip-preflight)
      skip_preflight=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

find_repo_root() {
  local dir="$PWD"
  while [ "$dir" != "/" ]; do
    if [ -f "$dir/opencontext.spec" ] && [ -f "$dir/build.sh" ] && [ -f "$dir/frontend/package.json" ]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir=$(dirname "$dir")
  done
  return 1
}

if [ -z "$repo_root" ]; then
  if ! repo_root=$(find_repo_root); then
    echo "ERROR: could not infer repo root; pass --repo-root DIR" >&2
    exit 2
  fi
fi

repo_root=$(cd "$repo_root" && pwd)
if [ ! -f "$repo_root/build.sh" ] || [ ! -f "$repo_root/opencontext.spec" ]; then
  echo "ERROR: repo root does not look like MineContext packaging root: $repo_root" >&2
  exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
preflight="$script_dir/check_packaging_env.sh"

cat <<WARN
About to build the MineContext backend executable.
Repo root: $repo_root
This mutates root dist/ and build/ via the checkout's build.sh.
WARN
if [ "$copy_to_frontend" = true ]; then
  echo "The requested copy step also recreates frontend/backend/."
fi

if [ "$yes" != true ]; then
  if [ -t 0 ]; then
    printf 'Continue? [y/N] '
    read -r answer
    case "$answer" in
      y|Y|yes|YES) ;;
      *) echo "Aborted."; exit 3 ;;
    esac
  else
    echo "ERROR: non-interactive use requires --yes" >&2
    exit 3
  fi
fi

if [ "$skip_preflight" != true ] && [ -x "$preflight" ]; then
  echo "== Preflight (non-mutating) =="
  "$preflight" --repo-root "$repo_root" || {
    echo "ERROR: preflight reported required packaging errors; fix them or rerun with --skip-preflight if intentionally bypassing." >&2
    exit 1
  }
fi

cd "$repo_root"

if [ "$(uname -s 2>/dev/null || echo unknown)" = "Darwin" ] || [ "$(uname -s 2>/dev/null || echo unknown)" = "Linux" ]; then
  chmod +x ./build.sh 2>/dev/null || true
  echo "== Running backend build.sh =="
  ./build.sh
else
  echo "ERROR: this wrapper is for Unix-like shells. On Windows, run build.bat from the repository root and verify dist\\main\\main.exe." >&2
  exit 2
fi

exe=""
if [ -f "$repo_root/dist/main/main" ]; then
  exe="$repo_root/dist/main/main"
elif [ -f "$repo_root/dist/main/main.exe" ]; then
  exe="$repo_root/dist/main/main.exe"
fi

if [ -z "$exe" ]; then
  echo "ERROR: backend build finished but dist/main/main(.exe) was not found" >&2
  exit 1
fi

echo "Backend executable verified: ${exe#$repo_root/}"

if [ "$copy_to_frontend" = true ]; then
  if ! command -v node >/dev/null 2>&1; then
    echo "ERROR: node is required for frontend/scripts/copy-prebuilt-backend.js" >&2
    exit 1
  fi
  echo "== Copying backend into frontend/backend/ =="
  (cd "$repo_root/frontend" && node scripts/copy-prebuilt-backend.js)
  if [ -f "$repo_root/frontend/backend/main" ] || [ -f "$repo_root/frontend/backend/main.exe" ]; then
    echo "Frontend backend copy verified."
  else
    echo "ERROR: copy step completed but frontend/backend/main(.exe) was not found" >&2
    exit 1
  fi
fi

echo "Done."
