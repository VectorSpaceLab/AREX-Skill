#!/usr/bin/env bash
# Safe AIMET GenAILab checkpoint/artifact downloader.
# Distilled from scripts/all/download_genai_checkpoint.sh, but this version
# does not auto-install AWS CLI or saml2aws and supports dry-run validation.
set -euo pipefail

AWS_PROFILE="${AWS_PROFILE:-genai-laboratory}"
EXPORTS_DIR="GenAILab/artifacts/exports"
DO_LOGIN=false
DRY_RUN=false
FORCE=false

usage() {
  cat <<'EOF'
Usage:
  download_genai_checkpoint.sh [options] <s3-url-or-https-s3-url>

Options:
  --profile NAME       AWS CLI profile to use (default: genai-laboratory or AWS_PROFILE)
  --exports-dir DIR    Destination export root (default: GenAILab/artifacts/exports)
  --login              Run `saml2aws login --profile NAME` before aws s3 cp
  --force              Re-download even if the destination directory exists
  --dry-run            Validate URL/tools and print planned operations only
  -h, --help           Show this help

Accepted URL forms:
  s3://bucket/path/checkpoint.zip
  https://bucket.s3.amazonaws.com/path/checkpoint.zip
  https://bucket.s3.region.amazonaws.com/path/checkpoint.zip

The script prints `model_id: <extracted-dir>` on success so the path can be
used in a GenAILab YAML config as `model.model_id`.
EOF
}

fail() { echo "ERROR: $*" >&2; exit 1; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"; }

url_to_s3() {
  local url="$1"
  if [[ "$url" == s3://* ]]; then
    printf '%s\n' "$url"
  elif [[ "$url" =~ ^https://([^./]+)\.s3[^/]*\.amazonaws\.com/(.+)$ ]]; then
    printf 's3://%s/%s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
  else
    return 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) AWS_PROFILE="$2"; shift 2 ;;
    --exports-dir) EXPORTS_DIR="$2"; shift 2 ;;
    --login) DO_LOGIN=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --force) FORCE=true; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    -*) fail "unknown option: $1" ;;
    *) break ;;
  esac
done

[[ $# -eq 1 ]] || { usage >&2; exit 1; }
URL="$1"
ZIP_NAME="$(basename "$URL")"
[[ "$ZIP_NAME" == *.zip ]] || fail "URL must point to a .zip file: $URL"
DIR_NAME="${ZIP_NAME%.zip}"
S3_URI="$(url_to_s3 "$URL")" || fail "unsupported URL; expected s3://... or https://bucket.s3[.region].amazonaws.com/..."
DEST="$EXPORTS_DIR/$DIR_NAME"

cat <<EOF
checkpoint_url: $URL
s3_uri: $S3_URI
aws_profile: $AWS_PROFILE
exports_dir: $EXPORTS_DIR
planned_model_id: $DEST
EOF

if $DRY_RUN; then
  echo "dry_run: true"
  if command -v aws >/dev/null 2>&1; then
    echo "aws_cli: $(command -v aws)"
  else
    echo "aws_cli: missing (required for real download)"
  fi
  if $DO_LOGIN; then
    if command -v saml2aws >/dev/null 2>&1; then
      echo "saml2aws: $(command -v saml2aws)"
    else
      echo "saml2aws: missing (required because --login was set)"
    fi
  fi
  exit 0
fi

need_cmd aws
need_cmd unzip
if $DO_LOGIN; then
  need_cmd saml2aws
  saml2aws login --profile "$AWS_PROFILE"
fi

if [[ -d "$DEST" && "$FORCE" == false ]]; then
  echo "Checkpoint already exists at $DEST"
  echo
  echo "model_id: $DEST"
  exit 0
fi

mkdir -p "$EXPORTS_DIR"
TMP_ZIP="$(mktemp)"
trap 'rm -f "$TMP_ZIP"' EXIT

echo "Downloading $S3_URI with AWS profile '$AWS_PROFILE'..." >&2
aws --profile "$AWS_PROFILE" s3 cp "$S3_URI" "$TMP_ZIP"

echo "Extracting to $EXPORTS_DIR..." >&2
unzip -q "$TMP_ZIP" -d "$EXPORTS_DIR"
INNER_DIR="$(unzip -Z1 "$TMP_ZIP" | head -1 | cut -d/ -f1)"
EXTRACTED_DIR="$EXPORTS_DIR/${INNER_DIR:-$DIR_NAME}"

if [[ ! -d "$EXTRACTED_DIR" ]]; then
  echo "warning: expected extracted directory not found; using planned destination $DEST" >&2
  EXTRACTED_DIR="$DEST"
fi

echo
echo "model_id: $EXTRACTED_DIR"
