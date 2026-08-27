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
