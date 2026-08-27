#!/usr/bin/env bash
# Safe standalone secret scanner adapted for the generated PyCaret repo-development skill.
# Scans a checkout or arbitrary directory for common credential shapes.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check_secrets.sh [--root DIR] [--allowlist FILE]

Scan files under DIR for accidental credentials. If DIR is a git checkout,
tracked files are scanned; otherwise regular files are discovered with find.

Options:
  --root DIR          Directory to scan (default: current directory).
  --allowlist FILE    File of relative path globs to skip. Defaults to
                      DIR/scripts/.secrets-allowlist when present.
  -h, --help          Show this help.

Allow a single known-safe fixture line by appending:
  # pragma: allow-secret

Exit codes:
  0  clean
  1  suspected secret found or invalid arguments
EOF
}

ROOT="."
ALLOWLIST=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      [[ $# -ge 2 ]] || { echo "error: --root needs a directory" >&2; usage; exit 1; }
      ROOT="$2"
      shift 2
      ;;
    --allowlist)
      [[ $# -ge 2 ]] || { echo "error: --allowlist needs a file" >&2; usage; exit 1; }
      ALLOWLIST="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -d "$ROOT" ]]; then
  echo "error: root is not a directory: $ROOT" >&2
  exit 1
fi

ROOT="$(cd "$ROOT" && pwd -P)"
if [[ -z "$ALLOWLIST" && -f "$ROOT/scripts/.secrets-allowlist" ]]; then
  ALLOWLIST="$ROOT/scripts/.secrets-allowlist"
elif [[ -n "$ALLOWLIST" ]]; then
  if [[ "$ALLOWLIST" != /* ]]; then
    ALLOWLIST="$PWD/$ALLOWLIST"
  fi
fi

# ANSI colors only for terminals.
if [[ -t 1 ]]; then
  RED=$'\033[31m'; YELLOW=$'\033[33m'; GREEN=$'\033[32m'; RESET=$'\033[0m'
else
  RED=""; YELLOW=""; GREEN=""; RESET=""
fi

ALLOWED_FILES=()
if [[ -n "$ALLOWLIST" && -f "$ALLOWLIST" ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    ALLOWED_FILES+=("$line")
  done < "$ALLOWLIST"
fi

is_allowed() {
  local rel="$1"
  local pat
  for pat in "${ALLOWED_FILES[@]:-}"; do
    # Intentional glob match for simple allowlist patterns.
    # shellcheck disable=SC2053
    [[ "$rel" == $pat ]] && return 0
  done
  return 1
}

list_files() {
  # Scan files under ROOT directly instead of relying on git path semantics;
  # this also catches untracked files a contributor may be about to add.
  (cd "$ROOT" && find . \
    -path './.git' -prune -o \
    -path './node_modules' -prune -o \
    -path './.venv' -prune -o \
    -path './dist' -prune -o \
    -path './build' -prune -o \
    -path './.pytest_cache' -prune -o \
    -path './.mypy_cache' -prune -o \
    -path './.ruff_cache' -prune -o \
    -type f -print | sed 's#^./##')
}

# <name><tab><extended-regex>. Keep patterns conservative; false positives are
# safer than leaked credentials, but exact-line pragmas are supported.
PATTERNS=(
  $'Anthropic API key\tsk-ant-[A-Za-z0-9_-]{20,}'
  $'OpenAI API key (sk-)\t(^|[^A-Za-z0-9_-])sk-[A-Za-z0-9]{32,}([^A-Za-z0-9_-]|$)'
  $'OpenAI API key (sk-proj-)\tsk-proj-[A-Za-z0-9_-]{40,}'
  $'OpenAI API key (sk-svcacct-)\tsk-svcacct-[A-Za-z0-9_-]{40,}'
  $'PyCaret API key\tpck_[A-Za-z0-9_-]{32,}'
  $'Stripe live secret\tsk_live_[A-Za-z0-9]{20,}'
  $'Slack token\txox[abprs]-[A-Za-z0-9-]{20,}'
  $'GitHub PAT\tghp_[A-Za-z0-9]{36,}'
  $'GitHub fine-grained PAT\tgithub_pat_[A-Za-z0-9_]{50,}'
  $'AWS access key id\t(^|[^A-Z0-9])AKIA[0-9A-Z]{16}([^A-Z0-9]|$)'
  $'AWS secret access key assignment\taws_secret_access_key[[:space:]]*=[[:space:]]*[A-Za-z0-9/+=]{40,}'
  $'Google API key\tAIza[A-Za-z0-9_-]{35}'
  $'Fernet-encrypted blob in source\tENC:v1:[A-Za-z0-9_+=/-]{40,}'
  $'PEM private key block\t-----BEGIN [A-Z ]*PRIVATE KEY-----'
)

mapfile -t FILES < <(list_files | sed '/^$/d' | sort -u)
if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "${GREEN}check-secrets: nothing to scan${RESET}"
  exit 0
fi

echo "${GREEN}check-secrets: scanning ${#FILES[@]} files under ${ROOT}${RESET}"
violations=0

for rel in "${FILES[@]}"; do
  [[ -f "$ROOT/$rel" ]] || continue
  is_allowed "$rel" && continue
  # Skip binary files and very large files to keep the scanner predictable.
  if ! grep -Iq . "$ROOT/$rel" 2>/dev/null; then
    continue
  fi
  size=$(wc -c < "$ROOT/$rel" 2>/dev/null || echo 0)
  if [[ "$size" -gt 2097152 ]]; then
    continue
  fi

  for entry in "${PATTERNS[@]}"; do
    name="${entry%%$'\t'*}"
    regex="${entry#*$'\t'}"
    matches=$(grep -nE -- "$regex" "$ROOT/$rel" 2>/dev/null || true)
    if [[ -n "$matches" ]]; then
      filtered=$(printf '%s\n' "$matches" | grep -v '# pragma: allow-secret' || true)
      if [[ -n "$filtered" ]]; then
        echo "${RED}✗ ${name}${RESET} in ${YELLOW}${rel}${RESET}:"
        printf '%s\n' "$filtered" | sed 's/^/    /'
        violations=$((violations + 1))
      fi
    fi
  done
done

if (( violations > 0 )); then
  echo
  echo "${RED}check-secrets: ${violations} suspected secret pattern(s) found.${RESET}"
  echo "Remove and rotate real credentials. For fixtures, use '# pragma: allow-secret' on the exact line."
  exit 1
fi

echo "${GREEN}check-secrets: clean.${RESET}"
