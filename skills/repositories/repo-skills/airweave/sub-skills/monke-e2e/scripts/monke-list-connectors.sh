#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Monke connector discovery helper (safe, discovery-only)

Usage:
  monke-list-connectors.sh [options]

Options:
  --repo-root PATH        Airweave checkout root. Defaults to AIRWEAVE_REPO or
                          the nearest ancestor of the current directory with
                          monke/configs and monke/bongos.
  --list                 Pretty-print available connectors from monke/configs.
                          This is the default mode.
  --print-connectors     Print connector names space-separated for scripts.
  --changed              Report connectors changed versus a git base ref.
  --base-ref REF         Git ref for --changed (default: BASE_REF, or
                          origin/$BASE_BRANCH in CI, otherwise BASE_BRANCH,
                          falling back to main).
  --include-core         With --changed, include Monke core connectors
                          (github and asana) when they have configs.
  --min N                With --changed, pad the candidate set from available
                          connectors until at least N names are printed.
  --include-worktree     With --changed, include unstaged, staged, and untracked
                          relevant files in addition to base-ref...HEAD.
  --verbose              Explain ignored changed files to stderr.
  --help, -h             Show this help.

Examples:
  # List all connector configs safely.
  monke-list-connectors.sh --repo-root "$AIRWEAVE_REPO" --list

  # Print all available connectors as one space-separated line.
  monke-list-connectors.sh --repo-root "$AIRWEAVE_REPO" --print-connectors

  # Print changed testable connectors only.
  monke-list-connectors.sh --repo-root "$AIRWEAVE_REPO" \
    --print-connectors --changed --base-ref origin/main

  # CI-style candidate set without running tests.
  monke-list-connectors.sh --repo-root "$AIRWEAVE_REPO" \
    --print-connectors --changed --include-core --min 4

Safety:
  This helper only reads connector/config/generation file names and optional git
  diffs. It does not create virtualenvs, install packages, load .env files,
  resolve credentials, call Composio, call external APIs, start Airweave, or run
  Monke tests.
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 2
}

note() {
  printf '%s\n' "$*" >&2
}

repo_root="${AIRWEAVE_REPO:-}"
print_connectors=false
changed=false
include_core=false
include_worktree=false
verbose=false
min_count=0
base_ref="${BASE_REF:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      [[ $# -ge 2 ]] || die "--repo-root requires a path"
      repo_root="$2"
      shift 2
      ;;
    --repo-root=*)
      repo_root="${1#--repo-root=}"
      shift
      ;;
    --list)
      print_connectors=false
      shift
      ;;
    --print-connectors)
      print_connectors=true
      shift
      ;;
    --changed)
      changed=true
      shift
      ;;
    --base-ref)
      [[ $# -ge 2 ]] || die "--base-ref requires a ref"
      base_ref="$2"
      shift 2
      ;;
    --base-ref=*)
      base_ref="${1#--base-ref=}"
      shift
      ;;
    --include-core)
      include_core=true
      shift
      ;;
    --min)
      [[ $# -ge 2 ]] || die "--min requires a number"
      min_count="$2"
      [[ "$min_count" =~ ^[0-9]+$ ]] || die "--min must be a non-negative integer"
      shift 2
      ;;
    --min=*)
      min_count="${1#--min=}"
      [[ "$min_count" =~ ^[0-9]+$ ]] || die "--min must be a non-negative integer"
      shift
      ;;
    --include-worktree)
      include_worktree=true
      shift
      ;;
    --verbose|-v)
      verbose=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
done

find_repo_root() {
  local start="$1"
  local dir
  dir="$(cd "$start" 2>/dev/null && pwd -P)" || return 1
  while [[ "$dir" != "/" ]]; do
    if [[ -d "$dir/monke/configs" && -d "$dir/monke/bongos" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

if [[ -n "$repo_root" ]]; then
  repo_root="$(cd "$repo_root" 2>/dev/null && pwd -P)" || die "repo root not found: $repo_root"
else
  repo_root="$(find_repo_root "$PWD")" || die "cannot find Airweave repo root; pass --repo-root PATH"
fi

[[ -d "$repo_root/monke/configs" ]] || die "missing monke/configs under repo root: $repo_root"
[[ -d "$repo_root/monke/bongos" ]] || die "missing monke/bongos under repo root: $repo_root"

connector_exists() {
  local connector="$1"
  [[ -f "$repo_root/monke/configs/${connector}.yaml" || -f "$repo_root/monke/configs/${connector}.yml" ]]
}

list_available() {
  find "$repo_root/monke/configs" -maxdepth 1 -type f \( -name '*.yaml' -o -name '*.yml' \) -print |
    while IFS= read -r path; do
      local name
      name="$(basename "$path")"
      name="${name%.yaml}"
      name="${name%.yml}"
      printf '%s\n' "$name"
    done |
    LC_ALL=C sort -u
}

map_file_to_connector() {
  local file="$1"
  local connector=""

  if [[ "$file" =~ ^monke/bongos/([^/]+)\.py$ ]]; then
    connector="${BASH_REMATCH[1]}"
  elif [[ "$file" =~ ^monke/configs/([^/]+)\.ya?ml$ ]]; then
    connector="${BASH_REMATCH[1]}"
  elif [[ "$file" =~ ^monke/generation/schemas/([^/]+)\.py$ ]]; then
    connector="${BASH_REMATCH[1]}"
  elif [[ "$file" =~ ^monke/generation/([^/]+)\.py$ ]]; then
    connector="${BASH_REMATCH[1]}"
  elif [[ "$file" =~ ^backend/airweave/platform/sources/([^/]+)\.py$ ]]; then
    connector="${BASH_REMATCH[1]}"
  elif [[ "$file" =~ ^backend/airweave/platform/entities/([^/]+)\.py$ ]]; then
    connector="${BASH_REMATCH[1]}"
  fi

  case "$connector" in
    ""|__init__|base_bongo|registry|_base)
      return 1
      ;;
  esac

  if connector_exists "$connector"; then
    printf '%s\n' "$connector"
    return 0
  fi

  if [[ "$verbose" == true ]]; then
    note "ignored changed file without matching Monke config: $file"
  fi
  return 1
}

resolve_base_ref() {
  if [[ -n "$base_ref" ]]; then
    printf '%s\n' "$base_ref"
    return 0
  fi

  local branch="${BASE_BRANCH:-main}"
  if [[ "${CI:-}" == "true" || "${GITHUB_ACTIONS:-}" == "true" ]]; then
    printf 'origin/%s\n' "$branch"
  else
    printf '%s\n' "$branch"
  fi
}

changed_files() {
  local ref="$1"

  git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
    die "--changed requires a git checkout: $repo_root"

  if ! git -C "$repo_root" rev-parse --verify "${ref}^{commit}" >/dev/null 2>&1; then
    if [[ "$ref" != origin/* ]] && git -C "$repo_root" rev-parse --verify "origin/${ref}^{commit}" >/dev/null 2>&1; then
      ref="origin/${ref}"
    else
      die "cannot find base ref '$ref'; fetch it or pass --base-ref REF"
    fi
  fi

  if ! git -C "$repo_root" diff --name-only "${ref}...HEAD" >/dev/null 2>&1; then
    die "cannot diff ${ref}...HEAD; check merge base and pass --base-ref REF if needed"
  fi

  git -C "$repo_root" diff --name-only "${ref}...HEAD"

  if [[ "$include_worktree" == true ]]; then
    git -C "$repo_root" diff --name-only
    git -C "$repo_root" diff --cached --name-only
    git -C "$repo_root" ls-files --others --exclude-standard
  fi
}

list_changed() {
  local ref
  ref="$(resolve_base_ref)"

  changed_files "$ref" |
    while IFS= read -r file; do
      map_file_to_connector "$file" || true
    done |
    LC_ALL=C sort -u
}

core_connectors() {
  local core=(github asana)
  local connector
  for connector in "${core[@]}"; do
    if connector_exists "$connector"; then
      printf '%s\n' "$connector"
    fi
  done
}

build_candidate_list() {
  if [[ "$changed" == true ]]; then
    {
      if [[ "$include_core" == true ]]; then
        core_connectors
      fi
      list_changed
    } | LC_ALL=C sort -u
  else
    list_available
  fi
}

connector_output="$(build_candidate_list)" || exit $?
connectors=()
if [[ -n "$connector_output" ]]; then
  while IFS= read -r connector; do
    [[ -n "$connector" ]] && connectors+=("$connector")
  done <<< "$connector_output"
fi

if [[ "$changed" == true && "$min_count" -gt 0 && "${#connectors[@]}" -lt "$min_count" ]]; then
  declare -A seen=()
  for connector in "${connectors[@]}"; do
    seen["$connector"]=1
  done
  while IFS= read -r connector; do
    [[ "${#connectors[@]}" -ge "$min_count" ]] && break
    if [[ -z "${seen[$connector]+x}" ]]; then
      connectors+=("$connector")
      seen["$connector"]=1
    fi
  done < <(list_available)
fi

if [[ "$print_connectors" == true ]]; then
  if [[ "${#connectors[@]}" -gt 0 ]]; then
    printf '%s' "${connectors[0]}"
    for connector in "${connectors[@]:1}"; do
      printf ' %s' "$connector"
    done
  fi
  printf '\n'
else
  if [[ "$changed" == true ]]; then
    printf 'Changed testable Monke connectors:\n'
  else
    printf 'Available Monke connectors:\n'
  fi
  if [[ "${#connectors[@]}" -eq 0 ]]; then
    printf '  (none)\n'
  else
    for connector in "${connectors[@]}"; do
      printf '  - %s\n' "$connector"
    done
  fi
fi
