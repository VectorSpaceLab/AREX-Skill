#!/usr/bin/env bash
set -euo pipefail

python_bin="${PYTHON_BIN:-python}"
doccano_bin="${DOCCANO_BIN:-doccano}"

printf '== pip check ==\n'
"$python_bin" -m pip check

printf '\n== installed package version ==\n'
"$python_bin" -I -c "from importlib.metadata import version; print(version('doccano'))"

printf '\n== import check ==\n'
"$python_bin" -I -c "import backend; import backend.cli; import backend.config.settings.base; print(backend.__file__); print(backend.cli.main.__name__)"

for args in \
  "--help" \
  "createuser --help" \
  "webserver --help" \
  "task --help" \
  "flower --help"; do
  printf '\n== %s %s ==\n' "$doccano_bin" "$args"
  # shellcheck disable=SC2086
  "$doccano_bin" $args
done
