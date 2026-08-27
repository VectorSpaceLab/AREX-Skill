#!/usr/bin/env bash
set -euo pipefail

readonly DISCO_PACKAGE="@auto-ml-skills/disco"
readonly LEGACY_VERSION_RANGE="0.0.x"
readonly DEFAULT_REGISTRY="https://registry.npmjs.org/"

apply=false
yes=false
registry="${NPM_CONFIG_REGISTRY:-${NPM_REGISTRY:-$DEFAULT_REGISTRY}}"
otp="${NPM_CONFIG_OTP:-${NPM_OTP:-}}"

usage() {
	cat <<'EOF'
Usage: deprecate-legacy-disco-npm.sh [options]

Preview or deprecate the legacy DisCo 0.0.x packages on npm.

Options:
  --apply                Apply the deprecations. The default is preview-only.
  --yes                  Skip the interactive confirmation used with --apply.
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
		--registry)
			shift
			(($# > 0)) || fail "--registry requires a URL"
			registry="$1"
			;;
		--otp)
			shift
			(($# > 0)) || fail "--otp requires a code"
			otp="$1"
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

latest_version="$(npm view "${DISCO_PACKAGE}@latest" version --registry "$registry")"
[[ -n "$latest_version" ]] || fail "could not resolve ${DISCO_PACKAGE}@latest"

case "$latest_version" in
	0.0.*)
		fail "${DISCO_PACKAGE}@latest is still ${latest_version}; publish the standalone release before deprecating 0.0.x"
		;;
esac

legacy_packages=(
	"@auto-ml-skills/disco-agent-core"
	"@auto-ml-skills/disco-ai"
	"@auto-ml-skills/disco-tui"
)

latest_dependencies="$(npm view "${DISCO_PACKAGE}@latest" dependencies --json --registry "$registry")"
for package in "${legacy_packages[@]}"; do
	if grep -Fq "\"$package\"" <<<"$latest_dependencies"; then
		fail "${DISCO_PACKAGE}@latest still depends on $package"
	fi
done

package_specs=(
	"${DISCO_PACKAGE}@${LEGACY_VERSION_RANGE}"
	"${legacy_packages[0]}@${LEGACY_VERSION_RANGE}"
	"${legacy_packages[1]}@${LEGACY_VERSION_RANGE}"
	"${legacy_packages[2]}@${LEGACY_VERSION_RANGE}"
)

messages=(
	"Legacy monorepo release. Upgrade to ${DISCO_PACKAGE}@latest; the 0.0.x line is no longer supported."
	"Deprecated internal package from the legacy DisCo monorepo. Do not install directly; use ${DISCO_PACKAGE}@latest."
	"Deprecated internal package from the legacy DisCo monorepo. Do not install directly; use ${DISCO_PACKAGE}@latest."
	"Deprecated internal package from the legacy DisCo monorepo. Do not install directly; use ${DISCO_PACKAGE}@latest."
)

echo "Mode: $([[ "$apply" == true ]] && echo apply || echo preview)"
echo "Registry: $registry"
echo "Current ${DISCO_PACKAGE}@latest: $latest_version"
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

echo "==> Legacy DisCo npm packages deprecated"
