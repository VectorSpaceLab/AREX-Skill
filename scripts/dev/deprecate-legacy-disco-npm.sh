#!/usr/bin/env bash
set -euo pipefail

readonly LEGACY_PACKAGE="@auto-ml-skills/disco"
readonly NEW_PACKAGE="@arex-skill/disco"
readonly LEGACY_PACKAGE_SPEC="${LEGACY_PACKAGE}@*"
readonly LEGACY_VERSION_RANGE="0.0.x"
readonly DEFAULT_REGISTRY="https://registry.npmjs.org/"
readonly DEFAULT_ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.env"

apply=false
yes=false
registry="${NPM_CONFIG_REGISTRY:-${NPM_REGISTRY:-}}"
otp="${NPM_CONFIG_OTP:-${NPM_OTP:-}}"
env_file="$DEFAULT_ENV_FILE"
registry_from_args=false
otp_from_args=false

usage() {
	cat <<'EOF'
Usage: deprecate-legacy-disco-npm.sh [options]

Preview or deprecate the legacy DisCo package and its 0.0.x companion packages on npm.

Options:
  --apply                Apply the deprecations. The default is preview-only.
  --yes                  Skip the interactive confirmation used with --apply.
  --env-file PATH        Read npm credentials and defaults from a dotenv file
                         (defaults to scripts/dev/.env).
  --registry URL         npm registry URL (defaults to the configured registry).
  --otp CODE             npm two-factor authentication code.
  -h, --help             Show this help.
EOF
}

fail() {
	echo "error: $*" >&2
	exit 1
}

while (($# > 0)); do
	case "$1" in
		--apply)
			apply=true
			;;
		--yes)
			yes=true
			;;
		--env-file)
			shift
			(($# > 0)) || fail "--env-file requires a path"
			env_file="$1"
			;;
		--registry)
			shift
			(($# > 0)) || fail "--registry requires a URL"
			registry="$1"
			registry_from_args=true
			;;
		--otp)
			shift
			(($# > 0)) || fail "--otp requires a code"
			otp="$1"
			otp_from_args=true
			;;
		-h | --help)
			usage
			exit 0
			;;
		*)
			fail "unknown argument: $1"
			;;
	esac
	shift
done

command -v npm >/dev/null 2>&1 || fail "npm must be available on PATH"

dotenv_value() {
	local key="$1"
	local path="$2"

	[[ -f "$path" ]] || return 0
	command -v python3 >/dev/null 2>&1 || fail "python3 is required to parse $path"

	python3 - "$path" "$key" <<'PY'
import shlex
import sys

path, wanted_key = sys.argv[1:]
for lineno, raw_line in enumerate(open(path, encoding="utf-8"), start=1):
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue

    try:
        parts = shlex.split(line, comments=True, posix=True)
    except ValueError as exc:
        print(f"{path}:{lineno}: cannot parse .env line: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if parts and parts[0] == "export":
        parts = parts[1:]
    if len(parts) != 1 or "=" not in parts[0]:
        print(f"{path}:{lineno}: expected KEY=VALUE syntax", file=sys.stderr)
        raise SystemExit(1)

    key, value = parts[0].split("=", 1)
    if key == wanted_key:
        print(value)
        break
PY
}

if [[ "$registry_from_args" != true && -z "$registry" ]]; then
	dotenv_registry="$(dotenv_value NPM_CONFIG_REGISTRY "$env_file")"
	if [[ -n "$dotenv_registry" ]]; then
		registry="$dotenv_registry"
	else
		registry="$(dotenv_value NPM_REGISTRY "$env_file")"
	fi
fi
registry="${registry:-$DEFAULT_REGISTRY}"

if [[ "$otp_from_args" != true && -z "$otp" ]]; then
	otp="$(dotenv_value NPM_CONFIG_OTP "$env_file")"
	if [[ -z "$otp" ]]; then
		otp="$(dotenv_value NPM_OTP "$env_file")"
	fi
fi

auth_token="${NODE_AUTH_TOKEN:-${NPM_TOKEN:-}}"
if [[ -z "$auth_token" ]]; then
	auth_token="$(dotenv_value NODE_AUTH_TOKEN "$env_file")"
	if [[ -z "$auth_token" ]]; then
		auth_token="$(dotenv_value NPM_TOKEN "$env_file")"
	fi
fi

npmrc_path=""
cleanup_npmrc() {
	if [[ -n "$npmrc_path" && -f "$npmrc_path" ]]; then
		rm -f "$npmrc_path"
	fi
}
trap cleanup_npmrc EXIT

if [[ -n "$auth_token" ]]; then
	export NODE_AUTH_TOKEN="$auth_token"
	npm_registry_for_auth="$registry"
	if [[ "$npm_registry_for_auth" != *://* ]]; then
		npm_registry_for_auth="https://$npm_registry_for_auth"
	fi
	npm_registry_for_auth="${npm_registry_for_auth#*://}"
	npm_registry_for_auth="${npm_registry_for_auth%/}"
	npmrc_path="$(mktemp "${TMPDIR:-/tmp}/disco-npmrc-XXXXXX")"
	chmod 600 "$npmrc_path"
	{
		printf 'registry=%s\n' "$registry"
		printf '//%s/:_authToken=${NODE_AUTH_TOKEN}\n' "$npm_registry_for_auth"
	} > "$npmrc_path"
	export NPM_CONFIG_USERCONFIG="$npmrc_path"
	echo "npm auth: using token from environment or $env_file via a temporary npmrc"
else
	echo "npm auth: no NPM_TOKEN or NODE_AUTH_TOKEN found; using existing npm login if available"
fi

latest_version="$(npm view "${LEGACY_PACKAGE}@latest" version --registry "$registry")"
[[ -n "$latest_version" ]] || fail "could not resolve ${LEGACY_PACKAGE}@latest"

case "$latest_version" in
	0.0.*)
		fail "${LEGACY_PACKAGE}@latest is still ${latest_version}; verify the standalone 0.2.x release before deprecating the legacy package"
		;;
esac

legacy_packages=(
	"@auto-ml-skills/disco-agent-core"
	"@auto-ml-skills/disco-ai"
	"@auto-ml-skills/disco-tui"
)

latest_dependencies="$(npm view "${LEGACY_PACKAGE}@latest" dependencies --json --registry "$registry")"
for package in "${legacy_packages[@]}"; do
	if grep -Fq "\"$package\"" <<<"$latest_dependencies"; then
		fail "${LEGACY_PACKAGE}@latest still depends on $package"
	fi
done

package_specs=(
	"$LEGACY_PACKAGE_SPEC"
	"${legacy_packages[0]}@${LEGACY_VERSION_RANGE}"
	"${legacy_packages[1]}@${LEGACY_VERSION_RANGE}"
	"${legacy_packages[2]}@${LEGACY_VERSION_RANGE}"
)

messages=(
	"This package is no longer maintained. Install ${NEW_PACKAGE}@latest instead."
	"Deprecated internal package from the legacy DisCo monorepo. Do not install directly; use ${NEW_PACKAGE}@latest."
	"Deprecated internal package from the legacy DisCo monorepo. Do not install directly; use ${NEW_PACKAGE}@latest."
	"Deprecated internal package from the legacy DisCo monorepo. Do not install directly; use ${NEW_PACKAGE}@latest."
)

echo "Mode: $([[ "$apply" == true ]] && echo apply || echo preview)"
echo "Registry: $registry"
echo "Current ${LEGACY_PACKAGE}@latest: $latest_version"
echo "Planned deprecations:"
for index in "${!package_specs[@]}"; do
	printf '  - %s\n    %s\n' "${package_specs[$index]}" "${messages[$index]}"
done

if [[ "$apply" != true ]]; then
	echo "==> Preview complete; rerun with --apply to make these npm changes"
	exit 0
fi

npm whoami --registry "$registry" >/dev/null || fail "npm authentication check failed for $registry"

if [[ "$yes" != true ]]; then
	echo
	read -r -p "Type 'deprecate' to continue: " answer || fail "deprecation cancelled"
	[[ "$answer" == "deprecate" ]] || fail "deprecation cancelled"
fi

for index in "${!package_specs[@]}"; do
	command=(
		npm deprecate
		"${package_specs[$index]}"
		"${messages[$index]}"
		--registry "$registry"
	)
	if [[ -n "$otp" ]]; then
		command+=(--otp "$otp")
	fi

	echo "==> Deprecating ${package_specs[$index]}"
	"${command[@]}"
done

echo "==> Legacy DisCo npm packages deprecated; install ${NEW_PACKAGE}@latest instead"
