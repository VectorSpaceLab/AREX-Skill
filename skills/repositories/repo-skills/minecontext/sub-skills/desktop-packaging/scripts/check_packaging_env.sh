#!/usr/bin/env bash
# Report MineContext desktop packaging prerequisites without installing anything.
# This script is intentionally read-only: it checks tools, platform, and paths.
set -u

usage() {
  cat <<'USAGE'
Usage: check_packaging_env.sh [--repo-root DIR]

Reports packaging tool/path status for a MineContext checkout. It does not
install dependencies, delete files, or run build commands.
USAGE
}

repo_root=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo-root)
      [ "$#" -ge 2 ] || { echo "ERROR: --repo-root requires a directory" >&2; exit 2; }
      repo_root="$2"
      shift 2
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
    if [ -f "$dir/opencontext.spec" ] && [ -f "$dir/frontend/package.json" ]; then
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

if [ ! -d "$repo_root" ]; then
  echo "ERROR: repo root is not a directory: $repo_root" >&2
  exit 2
fi

repo_root=$(cd "$repo_root" && pwd)
frontend_dir="$repo_root/frontend"
errors=0
warnings=0

status() {
  local level="$1"; shift
  printf '%-6s %s\n' "[$level]" "$*"
}

need_file() {
  local rel="$1"
  if [ -f "$repo_root/$rel" ]; then
    status OK "$rel"
  else
    status ERROR "missing required file: $rel"
    errors=$((errors + 1))
  fi
}

need_dir() {
  local rel="$1"
  if [ -d "$repo_root/$rel" ]; then
    status OK "$rel/"
  else
    status ERROR "missing required directory: $rel/"
    errors=$((errors + 1))
  fi
}

warn_file() {
  local rel="$1"
  if [ -f "$repo_root/$rel" ]; then
    status OK "$rel"
  else
    status WARN "missing optional/reference file: $rel"
    warnings=$((warnings + 1))
  fi
}

check_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    local path
    path=$(command -v "$cmd")
    local version=""
    case "$cmd" in
      python3|python|node|npm|pnpm|uv)
        version=$($cmd --version 2>/dev/null | head -n 1 || true)
        ;;
      pyinstaller)
        version=$($cmd --version 2>/dev/null | head -n 1 | sed 's/^/PyInstaller /' || true)
        ;;
    esac
    if [ -n "$version" ]; then
      status OK "$cmd: $version ($path)"
    else
      status OK "$cmd: found at $path"
    fi
  else
    status WARN "$cmd: not found on PATH"
    warnings=$((warnings + 1))
  fi
}

printf 'MineContext desktop packaging preflight\n'
printf 'Repo root: %s\n' "$repo_root"
printf 'Platform: %s / %s\n' "$(uname -s 2>/dev/null || echo unknown)" "$(uname -m 2>/dev/null || echo unknown)"
printf '\n== Tools ==\n'
check_cmd python3
check_cmd python
check_cmd uv
check_cmd pyinstaller
check_cmd node
check_cmd npm
check_cmd pnpm

printf '\n== Required packaging files ==\n'
need_file pyproject.toml
need_file opencontext.spec
need_file hook-opencontext.py
need_file build.sh
warn_file build.bat
need_dir opencontext
need_dir config
need_file frontend/package.json
need_file frontend/pnpm-lock.yaml
need_file frontend/electron-builder.yml
need_file frontend/scripts/copy-prebuilt-backend.js
need_file frontend/build-python.js
warn_file frontend/build-python.sh

printf '\n== Helper binary projects ==\n'
for component in window_inspector window_capture; do
  need_dir "frontend/externals/python/$component"
  need_file "frontend/externals/python/$component/$component.py"
  need_file "frontend/externals/python/$component/$component.spec"
  warn_file "frontend/externals/python/$component/requirements.txt"
  helper="$repo_root/frontend/externals/python/$component/dist/$component/$component"
  if [ -f "$helper" ]; then
    status OK "built helper present: frontend/externals/python/$component/dist/$component/$component"
  else
    case "$(uname -s 2>/dev/null || echo unknown)" in
      Darwin)
        status WARN "macOS helper not built yet: frontend/externals/python/$component/dist/$component/$component"
        warnings=$((warnings + 1))
        ;;
      *)
        status OK "helper build may be skipped on this non-macOS platform: $component"
        ;;
    esac
  fi
done

printf '\n== Backend build outputs ==\n'
if [ -f "$repo_root/dist/main/main" ]; then
  status OK "root backend executable exists: dist/main/main"
elif [ -f "$repo_root/dist/main/main.exe" ]; then
  status OK "root backend executable exists: dist/main/main.exe"
else
  status WARN "root backend executable missing: build backend before copy-backend/package"
  warnings=$((warnings + 1))
fi

if [ -d "$repo_root/dist/config" ]; then
  status OK "root dist/config/ exists"
else
  status WARN "root dist/config/ missing; build.sh normally copies config after a successful backend build"
  warnings=$((warnings + 1))
fi

printf '\n== Frontend backend copy ==\n'
if [ -f "$frontend_dir/backend/main" ]; then
  status OK "frontend/backend/main exists"
elif [ -f "$frontend_dir/backend/main.exe" ]; then
  status OK "frontend/backend/main.exe exists"
else
  status WARN "frontend backend copy missing: run copy-backend after backend build"
  warnings=$((warnings + 1))
fi

if [ -d "$frontend_dir/backend/config" ]; then
  status OK "frontend/backend/config/ exists"
else
  status WARN "frontend/backend/config/ missing until copy-backend copies dist/config"
  warnings=$((warnings + 1))
fi

printf '\n== Frontend package scripts ==\n'
if command -v node >/dev/null 2>&1 && [ -f "$frontend_dir/package.json" ]; then
  node - <<'NODE' "$frontend_dir/package.json" || errors=$((errors + 1))
const fs = require('fs')
const packagePath = process.argv[2]
const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'))
const required = ['copy-backend', 'build', 'build:mac', 'build:win', 'build:linux']
for (const key of required) {
  if (pkg.scripts && pkg.scripts[key]) {
    console.log(`[OK]     script ${key}: ${pkg.scripts[key]}`)
  } else {
    console.log(`[ERROR]  missing frontend package script: ${key}`)
    process.exitCode = 1
  }
}
NODE
else
  status WARN "node unavailable or frontend/package.json missing; skipped script inspection"
  warnings=$((warnings + 1))
fi

printf '\n== Platform notes ==\n'
case "$(uname -s 2>/dev/null || echo unknown)" in
  Darwin)
    status OK "macOS target can build Quartz helper binaries when PyObjC dependencies install successfully"
    if command -v codesign >/dev/null 2>&1; then
      status OK "codesign available for ad-hoc/local signing checks"
    else
      status WARN "codesign not found; macOS signing checks may fail"
      warnings=$((warnings + 1))
    fi
    ;;
  Linux)
    status OK "Linux host: JavaScript helper build skips macOS Quartz helpers by design"
    status WARN "package.json build:linux does not run copy-backend; copy backend explicitly before Linux packaging"
    warnings=$((warnings + 1))
    ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    status OK "Windows host: expect main.exe and build.bat for backend build"
    ;;
  *)
    status WARN "unknown platform; verify target-specific packaging manually"
    warnings=$((warnings + 1))
    ;;
esac

printf '\nSummary: %d error(s), %d warning(s)\n' "$errors" "$warnings"
if [ "$errors" -gt 0 ]; then
  exit 1
fi
exit 0
