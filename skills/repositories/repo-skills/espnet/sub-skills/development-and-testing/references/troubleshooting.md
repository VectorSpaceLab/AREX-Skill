# Development Troubleshooting

## Focused test selection

- Do not start broad CI for a small file change. Map changed paths to the closest test file or helper smoke.
- If pytest is unavailable, report the missing test extra rather than treating tests as passing.
- Optional import-heavy tests should be skipped or gated the same way CI gates k2, mir_eval, S3PRL, Whisper, and specialized paths.

## Common maintainer failures

- **Parser test fails after CLI change**: update `get_parser` expectations, help text, and docs/examples that mention flags.
- **Config dry-run fails**: check placeholder token lists, `--iterator_type none`, task-specific required options, and optional dependency gates.
- **Recipe PR diffs shared files**: restore `utils`, `steps`, task scripts, `cmd.sh`, and scheduler configs from the template unless the change is intentional.
- **Style failure**: run focused pycodestyle/formatters on changed files; avoid broad automatic rewrites outside scope.
- **Shellcheck failure**: fix quoting, sourced files, and variable expansion rather than suppressing broad warnings.
- **Timeouts**: reduce fixtures/models or add a justified timeout marker to a narrow test.

## Publication and credentials

Recipe results, model packing, Hugging Face upload, and demo publication require maintainer decisions and credentials. Do not run upload commands during ordinary verification.
