---
name: cli-and-maintenance
description: "Use PyMuPDF CLI, safe package checks, and maintenance guidance for
  installed-package verification, wheel/source-build triage, optional
  components, and focused test selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# CLI and Maintenance

Use this sub-skill for the installed PyMuPDF command line, package health checks, wheel/source-build triage, optional component readiness, and focused maintenance-test scoping after PyMuPDF edits.

## Read or run

- [references/cli-reference.md](references/cli-reference.md) covers `pymupdf` and `python -m pymupdf` commands: `show`, `clean`, `join`, `extract`, `embed-*`, `gettext`, and `internal`.
- [references/installation-and-maintenance.md](references/installation-and-maintenance.md) covers wheels, source builds, non-default MuPDF, optional packages, and focused tests.
- [references/source-script-inventory.md](references/source-script-inventory.md) classifies repo-owned scripts as wrapped, reference-only, or excluded.
- [references/troubleshooting.md](references/troubleshooting.md) covers CLI, install, source-build, and optional component failures.
- Run [scripts/pymupdf_cli_smoke.py](scripts/pymupdf_cli_smoke.py) for a safe CLI smoke in an explicit output directory.

## Safety rule

Do not run release automation, sudo/system installs, Docker/cibuildwheel, broad environment mutation, or network-heavy source builds without explicit authorization.

