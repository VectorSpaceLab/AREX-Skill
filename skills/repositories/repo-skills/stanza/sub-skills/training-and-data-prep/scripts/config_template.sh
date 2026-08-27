#!/usr/bin/env bash
# Stanza training/data environment template.
# Copy this file into your run workspace, replace every <...> placeholder, then source it.
# This file intentionally does not download data or create directories.

set -euo pipefail

# Universal Dependencies root containing treebanks in CoNLL-U format.
export UDBASE="<absolute-or-project-relative-path-to-UD-data>"

# NER source root containing raw or converted named-entity corpora.
export NERBASE="<absolute-or-project-relative-path-to-NER-data>"

# Constituency source root containing treebanks before Stanza conversion.
export CONSTITUENCY_BASE="<absolute-or-project-relative-path-to-constituency-data>"

# Prepared Stanza training/evaluation outputs.
export DATA_ROOT="<absolute-or-project-relative-path-to-prepared-stanza-data>"
export TOKENIZE_DATA_DIR="$DATA_ROOT/tokenize"
export MWT_DATA_DIR="$DATA_ROOT/mwt"
export LEMMA_DATA_DIR="$DATA_ROOT/lemma"
export POS_DATA_DIR="$DATA_ROOT/pos"
export DEPPARSE_DATA_DIR="$DATA_ROOT/depparse"
export ETE_DATA_DIR="$DATA_ROOT/ete"
export NER_DATA_DIR="$DATA_ROOT/ner"
export CHARLM_DATA_DIR="$DATA_ROOT/charlm"
export CONSTITUENCY_DATA_DIR="$DATA_ROOT/constituency"
export SENTIMENT_DATA_DIR="$DATA_ROOT/sentiment"

# External word vectors/pretrains. Large downloads should be approved separately.
export WORDVEC_DIR="<absolute-or-project-relative-path-to-word-vectors>"

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  cat <<'EOF'
Usage: source scripts/config_template.sh

This template sets the standard Stanza training/data-prep environment variables
with placeholder roots. Replace every placeholder before running training or
corpus conversion.
EOF
  return 0 2>/dev/null || exit 0
fi

printf 'Stanza training template loaded. Replace placeholders before running training.\n'
for var in UDBASE NERBASE CONSTITUENCY_BASE DATA_ROOT WORDVEC_DIR; do
  value="${!var}"
  if [[ "$value" == *'<'* || "$value" == *'>'* ]]; then
    printf '  %s still has placeholder value: %s\n' "$var" "$value" >&2
  fi
done
