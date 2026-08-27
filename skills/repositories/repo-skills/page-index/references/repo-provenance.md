# Repository Provenance

schema: disco.repo-provenance.v1

This file records the source snapshot used to build the generated PageIndex skill.

| Field | Value |
| --- | --- |
| Repository | PageIndex |
| Source commit | `b723c9f0a70bcf6b1dc16985063fa3b89f2d2441` |
| Branch | `main` |
| Exact tag | none |
| Working tree | dirty: untracked `skills/` directory |
| Package / distribution version | none declared in repository metadata |
| Public remote URL | omitted-private-or-unknown |

## Evidence paths

Relative evidence used for this distillation:

- `README.md`
- `requirements.txt`
- `run_pageindex.py`
- `pageindex/`
- `pageindex/flash/`
- `tests/`
- `examples/`
- `cookbook/`
- `.github/workflows/tests.yml`

## Refresh notes

- Re-check this provenance when the repository commit changes or when the PageIndex API, CLI flags, or example workflows change.
- Because the repository is source-first and has no package metadata, future refreshes should re-verify imports and CLI behavior from the source checkout or a path-aware environment.
- The generated skill is intended to be self-contained; do not rely on the original README or notebooks at runtime.
