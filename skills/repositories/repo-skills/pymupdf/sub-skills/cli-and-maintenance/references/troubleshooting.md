# CLI and Maintenance Troubleshooting

- `pymupdf` command missing: use `python -m pymupdf` or confirm script installation path.
- CLI option error: run subcommand `--help`; command flags use single hyphen forms such as `-metadata`, `-output`, `-pages`.
- Source build failure: prefer wheel unless a source build is required; inspect compiler/MuPDF/version constraints.
- Optional feature missing: verify optional package or external binary before claiming support.
- Broad tests install packages through test setup and can be slow; run focused safe checks first.
