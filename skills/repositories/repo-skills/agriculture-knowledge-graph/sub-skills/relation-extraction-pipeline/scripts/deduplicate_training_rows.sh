#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  deduplicate_training_rows.sh [--mode MODE] [--has-header] INPUT_TSV OUTPUT_TSV
  deduplicate_training_rows.sh --help

Deduplicate relation-extraction training rows with explicit input and output paths.
The script never appends to the output file.

Modes:
  keep-first           Preserve input order and keep the first copy of each exact row. (default)
  sort-unique          Sort rows bytewise and keep one copy of each exact row.
  drop-all-duplicates  Sort rows and keep only rows that occur exactly once; this matches
                       the original repository helper's `sort | uniq -u` behavior.

Options:
  --has-header         Preserve the first line as a header and deduplicate only body rows.
  --help, -h           Show this help message.

Examples:
  deduplicate_training_rows.sh raw.tsv dedup.tsv
  deduplicate_training_rows.sh --mode sort-unique --has-header raw.tsv dedup.tsv
USAGE
}

mode="keep-first"
has_header=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --mode)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --mode requires a value" >&2
        exit 2
      fi
      mode="$2"
      shift 2
      ;;
    --has-header)
      has_header=1
      shift
      ;;
    --)
      shift
      break
      ;;
    -* )
      echo "ERROR: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -ne 2 ]]; then
  echo "ERROR: expected INPUT_TSV and OUTPUT_TSV" >&2
  usage >&2
  exit 2
fi

input=$1
output=$2

case "$mode" in
  keep-first|sort-unique|drop-all-duplicates) ;;
  *)
    echo "ERROR: unsupported mode: $mode" >&2
    usage >&2
    exit 2
    ;;
esac

if [[ ! -f "$input" ]]; then
  echo "ERROR: input file does not exist: $input" >&2
  exit 1
fi

input_abs=$(cd "$(dirname "$input")" && pwd -P)/$(basename "$input")
output_dir=$(dirname "$output")
mkdir -p "$output_dir"
output_abs=$(cd "$output_dir" && pwd -P)/$(basename "$output")

if [[ "$input_abs" == "$output_abs" ]]; then
  echo "ERROR: input and output paths must differ" >&2
  exit 2
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
body="$tmpdir/body.tsv"
body_out="$tmpdir/body.dedup.tsv"
header="$tmpdir/header.tsv"

if [[ "$has_header" -eq 1 ]]; then
  if IFS= read -r first_line < "$input"; then
    printf '%s\n' "$first_line" > "$header"
    tail -n +2 "$input" > "$body"
  else
    : > "$header"
    : > "$body"
  fi
else
  : > "$header"
  cp "$input" "$body"
fi

case "$mode" in
  keep-first)
    awk '!seen[$0]++' "$body" > "$body_out"
    ;;
  sort-unique)
    LC_ALL=C sort -u "$body" > "$body_out"
    ;;
  drop-all-duplicates)
    LC_ALL=C sort "$body" | uniq -u > "$body_out"
    ;;
esac

{
  if [[ "$has_header" -eq 1 && -s "$header" ]]; then
    cat "$header"
  fi
  cat "$body_out"
} > "$output"

input_rows=$(wc -l < "$input" | tr -d ' ')
output_rows=$(wc -l < "$output" | tr -d ' ')
printf 'deduplicate_training_rows: mode=%s input_rows=%s output_rows=%s output=%s\n' \
  "$mode" "$input_rows" "$output_rows" "$output"
