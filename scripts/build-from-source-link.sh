#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_DIR="$REPO_ROOT/cli"

if [[ ! -f "$PACKAGE_DIR/package.json" ]]; then
	echo "error: expected DisCo package at $PACKAGE_DIR" >&2
	exit 1
fi

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
	echo "error: Node.js and npm must be available on PATH" >&2
	exit 1
fi

# Honor HTTP_PROXY/HTTPS_PROXY during dependency installation when supported by Node.
export NODE_USE_ENV_PROXY="${NODE_USE_ENV_PROXY:-1}"

echo "==> Installing DisCo source dependencies"
npm --prefix "$PACKAGE_DIR" ci --include=dev --ignore-scripts

echo "==> Building DisCo from cli"
npm --prefix "$PACKAGE_DIR" run build

if [[ ! -x "$PACKAGE_DIR/dist/cli.js" ]]; then
	echo "error: build did not create executable $PACKAGE_DIR/dist/cli.js" >&2
	exit 1
fi

echo "==> Linking disco globally"
global_prefix="$(npm prefix --global)"
global_node_modules="$global_prefix/lib/node_modules"
global_bin="$global_prefix/bin/disco"
global_bin_target=""
global_bin_is_previous_disco_link=false

if [[ -L "$global_bin" ]]; then
	# `readlink -m` also resolves a dangling symlink, which lets the cleanup
	# recover from an interrupted scope migration.
	global_bin_target="$(readlink -m "$global_bin")"
fi

# The package was previously linked as @auto-ml-skills/disco. Both scopes
# expose the same `disco` binary, so remove only source links that resolve to
# this checkout before creating the new @arex-skill/disco link.
for package_link in \
	"$global_node_modules/@auto-ml-skills/disco" \
	"$global_node_modules/@arex-skill/disco"; do
	if [[ -L "$package_link" ]] && [[ "$(readlink -f "$package_link")" == "$PACKAGE_DIR" ]]; then
		echo "==> Removing previous DisCo source link: $package_link"
		if [[ "$global_bin_target" == "$package_link/dist/cli.js" ]]; then
			global_bin_is_previous_disco_link=true
		fi
		rm "$package_link"
	elif [[ ! -e "$package_link" ]] && [[ "$global_bin_target" == "$package_link/dist/cli.js" ]]; then
		# Recover a dangling bin link left by an interrupted previous run.
		global_bin_is_previous_disco_link=true
	fi
done

if [[ "$global_bin_target" == "$PACKAGE_DIR/dist/cli.js" ]] || [[ "$global_bin_is_previous_disco_link" == true ]]; then
	echo "==> Removing previous DisCo command link: $global_bin"
	rm "$global_bin"
elif [[ -e "$global_bin" || -L "$global_bin" ]]; then
	echo "error: $global_bin already exists and does not point to this DisCo checkout" >&2
	echo "error: remove or rename that existing disco command, then rerun this script" >&2
	exit 1
fi

(
	cd "$PACKAGE_DIR"
	npm link --ignore-scripts
)

if ! command -v disco >/dev/null 2>&1; then
	global_prefix="$(npm prefix --global)"
	echo "error: npm linked DisCo, but disco is not on PATH" >&2
	echo "error: add $global_prefix/bin to PATH and rerun this script" >&2
	exit 1
fi

echo "==> Verifying linked CLI"
disco --version
disco --help >/dev/null

echo "==> Done"
echo "disco is built from source and linked globally. Try: disco --help"
