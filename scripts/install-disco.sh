#!/usr/bin/env sh
set -eu

# DisCo managed installer for macOS, Linux, WSL, and other Unix-like shells.
# It installs the published npm package into a private release tree and never
# replaces an unrelated `disco` command.

PACKAGE_NAME="@arex-skill/disco"
DEFAULT_NODE_VERSION="22.19.0"
DEFAULT_INSTALLER_URL="https://github.com/VectorSpaceLab/AREX-Skill/releases/latest/download/install-disco.sh"

die() {
	printf 'error: %s\n' "$*" >&2
	exit 1
}

usage() {
	cat <<'EOF'
DisCo managed installer

Usage:
  install-disco.sh [--version VERSION] [--install-dir DIR]
  install-disco.sh --update [--version VERSION]
  install-disco.sh --uninstall [--install-dir DIR]

Environment:
  DISCO_CODING_AGENT_DIR      Override ~/.disco/agent
  DISCO_INSTALL_DIR           Override the managed install directory
  DISCO_NPM_REGISTRY          Use an alternate npm registry
  DISCO_MANAGED_NODE_VERSION  Node.js version used when node is absent
  DISCO_INSTALLER_URL         URL used to persist the updater script
EOF
}

command_exists() {
	command -v "$1" >/dev/null 2>&1
}

absolute_path() {
	case "$1" in
		~/*) printf '%s/%s\n' "${HOME:?HOME is not set}" "${1#~/}" ;;
		/*) printf '%s\n' "$1" ;;
		*) printf '%s/%s\n' "$(pwd)" "$1" ;;
	esac
}

validate_install_dir() {
	case "$INSTALL_DIR" in
		/|"$HOME"|"$AGENT_DIR"|"${TMPDIR:-/tmp}")
			die "refusing to use a broad managed install directory: $INSTALL_DIR"
			;;
	esac
	case "$INSTALL_DIR" in
		*/.) die "managed install directory must name a child directory: $INSTALL_DIR" ;;
		*) : ;;
	esac
}

resolve_existing_path() {
	if command_exists realpath; then
		realpath "$1" 2>/dev/null && return
	fi
	if command_exists readlink; then
		readlink -f "$1" 2>/dev/null && return
	fi
	printf '%s\n' "$1"
}

shell_quote() {
	printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
}

json_escape() {
	printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

sha256_file() {
	if command_exists sha256sum; then
		sha256sum "$1" | awk '{print $1}'
		return
	fi
	if command_exists shasum; then
		shasum -a 256 "$1" | awk '{print $1}'
		return
	fi
	if command_exists openssl; then
		openssl dgst -sha256 "$1" | awk -F'= ' '{print $2}'
		return
	fi
	die "no SHA-256 implementation found; install sha256sum, shasum, or openssl"
}

download_file() {
	url="$1"
	destination="$2"
	if command_exists curl; then
		curl -fL --retry 3 --retry-delay 1 --connect-timeout 15 --silent --show-error "$url" -o "$destination"
		return
	fi
	if command_exists wget; then
		wget --https-only --tries=3 --timeout=15 -O "$destination" "$url"
		return
	fi
	die "curl or wget is required to download DisCo"
}

validate_version() {
	awk -v version="$1" 'BEGIN { exit (version ~ /^[0-9]+\.[0-9]+\.[0-9]+$/) ? 0 : 1 }' || die "invalid DisCo version: $1"
}

node_version_is_sufficient() {
	awk -v version="$1" 'BEGIN {
		if (version !~ /^[0-9]+\.[0-9]+\.[0-9]+$/) exit 1;
		split(version, p, "."); major=p[1]+0; minor=p[2]+0; patch=p[3]+0;
		if (major > 22 || (major == 22 && minor > 19) || (major == 22 && minor == 19 && patch >= 0)) exit 0;
		exit 1;
	}'
}

resolve_node_runtime() {
	if command_exists node && command_exists npm; then
		candidate_node="$(command -v node)"
		candidate_version="$($candidate_node --version 2>/dev/null | sed 's/^v//' || true)"
		if [ -n "$candidate_version" ] && node_version_is_sufficient "$candidate_version"; then
			NODE_PATH="$candidate_node"
			NPM_PATH="$(command -v npm)"
			NODE_SOURCE=system
			NODE_VERSION="$candidate_version"
			return
		fi
	fi

	command_exists curl || command_exists wget || die "Node.js >=22.19.0 is unavailable and curl/wget is missing"
	command_exists tar || die "tar is required to install a managed Node.js runtime"
	command_exists awk || die "awk is required to verify the managed Node.js checksum"
	managed_node_version="${DISCO_MANAGED_NODE_VERSION:-$DEFAULT_NODE_VERSION}"
	validate_version "$managed_node_version"
	node_version_is_sufficient "$managed_node_version" || die "managed Node.js version must be >=22.19.0: $managed_node_version"
	case "$(uname -s | tr '[:upper:]' '[:lower:]')" in
		linux) node_os=linux ;;
		darwin) node_os=darwin ;;
		*) die "managed Node.js is not supported on $(uname -s)" ;;
	esac
	case "$(uname -m)" in
		x86_64|amd64) node_arch=x64 ;;
		aarch64|arm64) node_arch=arm64 ;;
		*) die "managed Node.js is not supported on $(uname -m)" ;;
	esac

	node_root="$INSTALL_DIR/node/v$managed_node_version"
	managed_node="$node_root"
	if [ -x "$managed_node/bin/node" ] && [ -x "$managed_node/bin/npm" ]; then
		managed_version="$($managed_node/bin/node --version 2>/dev/null | sed 's/^v//' || true)"
		if [ "$managed_version" = "$managed_node_version" ]; then
			NODE_PATH="$managed_node/bin/node"
			NPM_PATH="$managed_node/bin/npm"
			NODE_SOURCE=managed
			NODE_VERSION="$managed_node_version"
			return
		fi
	fi

	tmp_node="$TMP_DIR/node"
	mkdir -p "$tmp_node"
	archive_name="node-v$managed_node_version-$node_os-$node_arch.tar.gz"
	download_file "https://nodejs.org/dist/v$managed_node_version/$archive_name" "$tmp_node/$archive_name" || die "failed to download Node.js $managed_node_version"
	download_file "https://nodejs.org/dist/v$managed_node_version/SHASUMS256.txt" "$tmp_node/SHASUMS256.txt" || die "failed to download Node.js checksum manifest"
	expected_checksum="$(awk -v file="$archive_name" '$2 == file { print $1; exit }' "$tmp_node/SHASUMS256.txt")"
	[ -n "$expected_checksum" ] || die "Node.js checksum manifest does not contain $archive_name"
	[ "$(sha256_file "$tmp_node/$archive_name")" = "$expected_checksum" ] || die "Node.js checksum mismatch for $archive_name"
	mkdir -p "$tmp_node/extracted"
	tar -xzf "$tmp_node/$archive_name" -C "$tmp_node/extracted"
	extracted_root="$tmp_node/extracted/node-v$managed_node_version-$node_os-$node_arch"
	[ -x "$extracted_root/bin/node" ] && [ -x "$extracted_root/bin/npm" ] || die "downloaded Node.js archive is incomplete"
	mkdir -p "$INSTALL_DIR/node"
	if [ -e "$node_root.new" ]; then rm -rf "$node_root.new"; fi
	mv "$extracted_root" "$node_root.new"
	if [ -e "$node_root" ]; then rm -rf "$node_root"; fi
	mv "$node_root.new" "$node_root"
	NODE_PATH="$node_root/bin/node"
	NPM_PATH="$node_root/bin/npm"
	NODE_SOURCE=managed
	NODE_VERSION="$managed_node_version"
}

resolve_package_version() {
	if [ -z "$REQUESTED_VERSION" ] || [ "$REQUESTED_VERSION" = latest ]; then
		if [ -n "${DISCO_NPM_REGISTRY:-}" ]; then
			version="$($NPM_PATH view "$PACKAGE_NAME@latest" version --json --registry "$DISCO_NPM_REGISTRY" 2>/dev/null | tr -d '"[:space:]' || true)"
		else
			version="$($NPM_PATH view "$PACKAGE_NAME@latest" version --json 2>/dev/null | tr -d '"[:space:]' || true)"
		fi
		[ -n "$version" ] || die "could not resolve the latest $PACKAGE_NAME version from npm"
		REQUESTED_VERSION="$version"
	fi
	validate_version "$REQUESTED_VERSION"
}

prepend_node_bin_to_path() {
	node_bin_dir="${NODE_PATH%/*}"
	case ":${PATH:-}:" in
		*":$node_bin_dir:"*) : ;;
		*) PATH="$node_bin_dir${PATH:+:$PATH}"; export PATH ;;
	esac
}

ensure_persisted_installer() {
	INSTALLER_PATH="$INSTALL_DIR/install-disco.sh"
	case "$0" in
		sh|bash|-sh|-bash|/bin/sh|/bin/bash|/dev/fd/*) use_download=1 ;;
		*) use_download=0 ;;
	esac
	if [ "$use_download" -eq 0 ] && [ -f "$0" ]; then
		source_path="$(resolve_existing_path "$0")"
		destination_path="$(resolve_existing_path "$INSTALLER_PATH")"
		if [ "$source_path" != "$destination_path" ]; then cp "$0" "$INSTALLER_PATH"; fi
	else
		download_file "${DISCO_INSTALLER_URL:-$DEFAULT_INSTALLER_URL}" "$INSTALLER_PATH" || die "could not persist the managed updater"
	fi
	chmod 700 "$INSTALLER_PATH"
}

write_atomic() {
	destination="$1"
	content="$2"
	temporary="$destination.tmp.$$"
	if ! printf '%s' "$content" > "$temporary"; then
		rm -f "$temporary"
		return 1
	fi
	if ! mv -f "$temporary" "$destination"; then
		rm -f "$temporary"
		return 1
	fi
}

backup_file() {
	source="$1"
	destination="$2"
	if [ -e "$source" ] || [ -L "$source" ]; then
		if ! cp -p "$source" "$destination"; then
			return 1
		fi
		return 0
	fi
	return 1
}

restore_file() {
	destination="$1"
	backup="$2"
	was_present="$3"
	if [ "$was_present" -eq 1 ]; then
		if ! cp -p "$backup" "$destination"; then
			return 1
		fi
	else
		if ! rm -f "$destination"; then
			return 1
		fi
	fi
}

write_launcher() {
	launcher_dir="$AGENT_DIR/bin"
	launcher="$launcher_dir/disco"
	mkdir -p "$launcher_dir"
	if [ -e "$launcher" ] || [ -L "$launcher" ]; then
		if ! grep -Fq "$INSTALL_DIR" "$launcher" 2>/dev/null; then
			printf 'error: %s already exists and is not owned by the DisCo managed installer\n' "$launcher" >&2
			return 1
		fi
	fi
	launcher_tmp="$launcher.$$"
	install_literal="$(shell_quote "$INSTALL_DIR")"
	agent_literal="$(shell_quote "$AGENT_DIR")"
if ! cat > "$launcher_tmp" <<EOF
#!/usr/bin/env sh
set -eu
INSTALL_DIR=$install_literal
AGENT_DIR=$agent_literal
CURRENT_FILE="\$INSTALL_DIR/current-version"
NODE_FILE="\$INSTALL_DIR/node-path"
MARKER="\$INSTALL_DIR/managed-install.json"
[ -s "\$CURRENT_FILE" ] || { echo "error: DisCo managed install has no current release" >&2; exit 1; }
current=\$(tr -d '\\r\\n' < "\$CURRENT_FILE")
case "\$current" in ''|*[!A-Za-z0-9._+-]*) echo "error: invalid DisCo managed release pointer" >&2; exit 1;; esac
node_path=\$(tr -d '\\r\\n' < "\$NODE_FILE" 2>/dev/null || true)
[ -x "\$node_path" ] || node_path=\$(command -v node 2>/dev/null || true)
[ -x "\$node_path" ] || { echo "error: managed Node.js runtime is missing" >&2; exit 1; }
release="\$INSTALL_DIR/releases/\$current"
entrypoint="\$release/node_modules/@arex-skill/disco/dist/cli.js"
[ -f "\$MARKER" ] || { echo "error: invalid DisCo managed install marker" >&2; exit 1; }
grep -Fq '"packageName": "@arex-skill/disco"' "\$MARKER" || { echo "error: invalid DisCo managed package marker" >&2; exit 1; }
[ -f "\$entrypoint" ] || { echo "error: DisCo managed release \$current is incomplete" >&2; exit 1; }
export DISCO_MANAGED_INSTALL=1
export DISCO_MANAGED_INSTALL_DIR="\$INSTALL_DIR"
export DISCO_MANAGED_INSTALLER="\$INSTALL_DIR/install-disco.sh"
export DISCO_MANAGED_INSTALL_MARKER="\$MARKER"
export DISCO_CODING_AGENT_DIR="\$AGENT_DIR"
exec "\$node_path" "\$entrypoint" "\$@"
EOF
then
	rm -f "$launcher_tmp"
	return 1
fi
	if ! chmod 700 "$launcher_tmp"; then
		rm -f "$launcher_tmp"
		return 1
	fi
	if ! mv -f "$launcher_tmp" "$launcher"; then
		rm -f "$launcher_tmp"
		return 1
	fi
}

write_marker() {
	package_dir="$1"
	install_escaped="$(json_escape "$INSTALL_DIR")"
	entrypoint_escaped="$(json_escape "$package_dir/dist/cli.js")"
	node_escaped="$(json_escape "$NODE_PATH")"
	installer_escaped="$(json_escape "$INSTALLER_PATH")"
	marker_tmp="$INSTALL_DIR/managed-install.json.tmp.$$"
if ! cat > "$marker_tmp" <<EOF
{
  "schemaVersion": 1,
  "packageName": "$PACKAGE_NAME",
  "activeVersion": "$REQUESTED_VERSION",
  "installDir": "$install_escaped",
  "entrypoint": "$entrypoint_escaped",
  "nodeSource": "$NODE_SOURCE",
  "nodeVersion": "$NODE_VERSION",
  "nodePath": "$node_escaped",
  "installerPath": "$installer_escaped",
  "platform": "$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)"
}
EOF
then
	rm -f "$marker_tmp"
	return 1
fi
	if ! mv -f "$marker_tmp" "$INSTALL_DIR/managed-install.json"; then
		rm -f "$marker_tmp"
		return 1
	fi
}

check_command_conflict() {
	existing="$(command -v disco 2>/dev/null || true)"
	if [ -z "$existing" ]; then
		return 0
	fi
	existing_real="$(resolve_existing_path "$existing")"
	launcher_real="$(resolve_existing_path "$AGENT_DIR/bin/disco")"
	if [ "$existing_real" != "$launcher_real" ] && [ "$existing" != "$AGENT_DIR/bin/disco" ]; then
		die "disco already resolves to $existing; refusing to overwrite an unrelated installation"
	fi
}

acquire_lock() {
	LOCK_DIR="$INSTALL_DIR/.lock"
	if ! mkdir "$LOCK_DIR" 2>/dev/null; then
		die "another DisCo managed installer is already modifying $INSTALL_DIR"
	fi
	printf '%s\n' "$$" > "$LOCK_DIR/pid"
}

cleanup() {
	if [ -n "${RELEASE_STAGE:-}" ] && [ -e "$RELEASE_STAGE" ]; then rm -rf "$RELEASE_STAGE"; fi
	if [ -n "${LOCK_DIR:-}" ] && [ -d "$LOCK_DIR" ]; then rm -rf "$LOCK_DIR"; fi
	if [ -n "${TMP_DIR:-}" ] && [ -d "$TMP_DIR" ]; then rm -rf "$TMP_DIR"; fi
}

uninstall_managed_install() {
	marker="$INSTALL_DIR/managed-install.json"
	[ -f "$marker" ] || die "$INSTALL_DIR is not a recognized DisCo managed install"
	grep -Fq '"packageName": "@arex-skill/disco"' "$marker" || die "managed install marker package name does not match $PACKAGE_NAME"
	if [ -f "$AGENT_DIR/bin/disco" ] && grep -Fq "$INSTALL_DIR" "$AGENT_DIR/bin/disco" 2>/dev/null; then rm -f "$AGENT_DIR/bin/disco"; fi
	rm -rf "$INSTALL_DIR"
	printf 'Removed DisCo managed files under %s; user settings, credentials, sessions, and skills were preserved.\n' "$INSTALL_DIR"
}

install_release() {
	mkdir -p "$INSTALL_DIR/releases"
	RELEASE_STAGE="$INSTALL_DIR/releases/.stage-$REQUESTED_VERSION-$$"
	release_dir="$INSTALL_DIR/releases/$REQUESTED_VERSION"
	rm -rf "$RELEASE_STAGE"
	mkdir -p "$RELEASE_STAGE"
	if [ -n "${DISCO_NPM_REGISTRY:-}" ]; then
		"$NPM_PATH" install --prefix "$RELEASE_STAGE" --ignore-scripts --omit=dev --no-audit --no-fund "$PACKAGE_NAME@$REQUESTED_VERSION" --registry "$DISCO_NPM_REGISTRY" || die "failed to install $PACKAGE_NAME@$REQUESTED_VERSION"
	else
		"$NPM_PATH" install --prefix "$RELEASE_STAGE" --ignore-scripts --omit=dev --no-audit --no-fund "$PACKAGE_NAME@$REQUESTED_VERSION" || die "failed to install $PACKAGE_NAME@$REQUESTED_VERSION"
	fi
	package_dir="$RELEASE_STAGE/node_modules/@arex-skill/disco"
	[ -f "$package_dir/package.json" ] && [ -f "$package_dir/dist/cli.js" ] || die "managed npm install did not produce a complete DisCo package"
	actual_version="$($NODE_PATH -e 'const p=require(process.argv[1]); process.stdout.write(String(p.version||""))' "$package_dir/package.json")"
	[ "$actual_version" = "$REQUESTED_VERSION" ] || die "managed package version mismatch: expected $REQUESTED_VERSION, got $actual_version"
	"$NODE_PATH" "$package_dir/dist/cli.js" --version >/dev/null || die "managed DisCo smoke check failed"

	old_release="$TMP_DIR/previous-release"
	old_marker="$TMP_DIR/previous-marker"
	old_current="$TMP_DIR/previous-current"
	old_node="$TMP_DIR/previous-node"
	old_launcher="$TMP_DIR/previous-launcher"
	old_release_present=0; old_marker_present=0; old_current_present=0; old_node_present=0; old_launcher_present=0
	if [ -e "$release_dir" ]; then mv "$release_dir" "$old_release"; old_release_present=1; fi
	if backup_file "$INSTALL_DIR/managed-install.json" "$old_marker"; then old_marker_present=1; fi
	if backup_file "$INSTALL_DIR/current-version" "$old_current"; then old_current_present=1; fi
	if backup_file "$INSTALL_DIR/node-path" "$old_node"; then old_node_present=1; fi
	if backup_file "$AGENT_DIR/bin/disco" "$old_launcher"; then old_launcher_present=1; fi

	if ! mv "$RELEASE_STAGE" "$release_dir"; then
		[ "$old_release_present" -eq 1 ] && mv "$old_release" "$release_dir"
		die "could not activate managed DisCo release $REQUESTED_VERSION"
	fi
	package_dir="$release_dir/node_modules/@arex-skill/disco"
	activation_failed=0
	write_atomic "$INSTALL_DIR/node-path" "$(printf '%s\n' "$NODE_PATH")" || activation_failed=1
	if [ "$activation_failed" -eq 0 ]; then
		write_marker "$package_dir" || activation_failed=1
	fi
	if [ "$activation_failed" -eq 0 ]; then
		write_launcher || activation_failed=1
	fi
	if [ "$activation_failed" -eq 0 ]; then
		write_atomic "$INSTALL_DIR/current-version" "$(printf '%s\n' "$REQUESTED_VERSION")" || activation_failed=1
	fi
	if [ "$activation_failed" -ne 0 ]; then
		rm -rf "$release_dir"
		[ "$old_release_present" -eq 1 ] && mv "$old_release" "$release_dir"
		restore_file "$INSTALL_DIR/managed-install.json" "$old_marker" "$old_marker_present"
		restore_file "$INSTALL_DIR/current-version" "$old_current" "$old_current_present"
		restore_file "$INSTALL_DIR/node-path" "$old_node" "$old_node_present"
		restore_file "$AGENT_DIR/bin/disco" "$old_launcher" "$old_launcher_present"
		die "could not activate managed DisCo release $REQUESTED_VERSION; previous release restored"
	fi
	RELEASE_STAGE=""
}

REQUESTED_VERSION=""
INSTALL_DIR=""
UPDATE=0
UNINSTALL=0
while [ "$#" -gt 0 ]; do
	case "$1" in
		--help|-h) usage; exit 0 ;;
		--yes) shift ;;
		--update) UPDATE=1; shift ;;
		--uninstall) UNINSTALL=1; shift ;;
		--version) [ "$#" -ge 2 ] || die "--version requires a value"; REQUESTED_VERSION="$2"; shift 2 ;;
		--install-dir) [ "$#" -ge 2 ] || die "--install-dir requires a value"; INSTALL_DIR="$2"; shift 2 ;;
		*) die "unknown argument: $1" ;;
	esac
done

AGENT_DIR="${DISCO_CODING_AGENT_DIR:-${HOME:?HOME is not set}/.disco/agent}"
AGENT_DIR="$(absolute_path "$AGENT_DIR")"
if [ -n "${DISCO_INSTALL_DIR:-}" ] && [ -z "$INSTALL_DIR" ]; then INSTALL_DIR="$DISCO_INSTALL_DIR"; fi
INSTALL_DIR="$(absolute_path "${INSTALL_DIR:-$AGENT_DIR/install}")"
validate_install_dir
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/disco-install.XXXXXX")"
LOCK_DIR=""
RELEASE_STAGE=""
trap cleanup 0 1 2 3 15

if [ "$UNINSTALL" -eq 1 ]; then
	[ -d "$INSTALL_DIR" ] || die "$INSTALL_DIR is not a recognized DisCo managed install"
	acquire_lock
	uninstall_managed_install
	exit 0
fi

mkdir -p "$INSTALL_DIR"
acquire_lock
if [ "$UPDATE" -eq 1 ]; then
	[ -f "$INSTALL_DIR/managed-install.json" ] || die "$INSTALL_DIR is not a recognized DisCo managed install"
	grep -Fq '"packageName": "@arex-skill/disco"' "$INSTALL_DIR/managed-install.json" || die "managed install marker package name does not match $PACKAGE_NAME"
fi
check_command_conflict
resolve_node_runtime
prepend_node_bin_to_path
resolve_package_version
ensure_persisted_installer
install_release

printf 'Installed %s@%s using %s Node.js under %s\n' "$PACKAGE_NAME" "$REQUESTED_VERSION" "$NODE_SOURCE" "$INSTALL_DIR"
printf 'DisCo launcher: %s\n' "$AGENT_DIR/bin/disco"
printf 'Add %s to PATH if it is not already present, then run: disco --version\n' "$AGENT_DIR/bin"
