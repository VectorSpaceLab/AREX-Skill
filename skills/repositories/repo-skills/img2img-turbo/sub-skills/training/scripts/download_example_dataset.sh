#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Download an img2img-turbo example training dataset with explicit confirmation.

Usage:
  download_example_dataset.sh --dataset fill50k|horse2zebra --output-dir DIR --yes [--keep-archive]
  download_example_dataset.sh --help

Options:
  --dataset NAME     Dataset to download: fill50k or horse2zebra.
  --output-dir DIR   Directory to receive the extracted dataset folder, e.g. data.
  --yes              Required before any network download or extraction.
  --keep-archive     Keep the downloaded zip instead of removing it after extraction.
  -h, --help         Print this help. Safe: performs no network action.

Expected extracted folders:
  fill50k      -> DIR/my_fill50k
  horse2zebra  -> DIR/my_horse2zebra
USAGE
}

die() {
  echo "error: $*" >&2
  exit 2
}

dataset=""
output_dir=""
yes="0"
keep_archive="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dataset)
      [[ $# -ge 2 ]] || die "--dataset requires a value"
      dataset="$2"
      shift 2
      ;;
    --output-dir)
      [[ $# -ge 2 ]] || die "--output-dir requires a value"
      output_dir="$2"
      shift 2
      ;;
    --yes)
      yes="1"
      shift
      ;;
    --keep-archive)
      keep_archive="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "$dataset" ]] || die "missing --dataset fill50k|horse2zebra"
[[ -n "$output_dir" ]] || die "missing --output-dir DIR"
[[ "$yes" == "1" ]] || die "refusing network action without --yes"
[[ "$output_dir" != "/" ]] || die "refusing to extract into filesystem root"

case "$dataset" in
  fill50k)
    url="https://www.cs.cmu.edu/~img2img-turbo/data/my_fill50k.zip"
    archive="my_fill50k.zip"
    expected_dir="my_fill50k"
    ;;
  horse2zebra)
    url="https://www.cs.cmu.edu/~img2img-turbo/data/my_horse2zebra.zip"
    archive="my_horse2zebra.zip"
    expected_dir="my_horse2zebra"
    ;;
  *)
    die "unsupported dataset '$dataset' (expected fill50k or horse2zebra)"
    ;;
esac

command -v unzip >/dev/null 2>&1 || die "unzip is required"
if command -v curl >/dev/null 2>&1; then
  downloader=(curl -fL "$url" -o)
elif command -v wget >/dev/null 2>&1; then
  downloader=(wget "$url" -O)
else
  die "curl or wget is required"
fi

mkdir -p "$output_dir"
archive_path="$output_dir/$archive"
extract_path="$output_dir/$expected_dir"

[[ ! -e "$extract_path" ]] || die "refusing to overwrite existing dataset directory: $extract_path"
[[ ! -e "$archive_path" ]] || die "refusing to overwrite existing archive: $archive_path"

cleanup() {
  if [[ "$keep_archive" != "1" && -f "$archive_path" ]]; then
    rm -f "$archive_path"
  fi
}
trap cleanup EXIT

echo "Dataset: $dataset"
echo "URL: $url"
echo "Archive: $archive_path"
echo "Extract to: $output_dir"

if [[ "${downloader[0]}" == "curl" ]]; then
  "${downloader[@]}" "$archive_path"
else
  "${downloader[@]}" "$archive_path"
fi

unzip -q "$archive_path" -d "$output_dir"

if [[ -d "$extract_path" ]]; then
  echo "Downloaded and extracted: $extract_path"
else
  echo "warning: extraction completed, but expected directory was not found: $extract_path" >&2
  echo "Inspect output directory: $output_dir" >&2
fi

if [[ "$keep_archive" == "1" ]]; then
  trap - EXIT
  echo "Kept archive: $archive_path"
else
  echo "Removed archive after extraction."
fi
