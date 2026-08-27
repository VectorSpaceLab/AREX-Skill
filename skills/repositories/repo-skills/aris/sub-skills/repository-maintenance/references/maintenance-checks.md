# Maintenance Checks

## Skill Corpus

- Every mainline `skills/<name>/` directory intended as a skill has exactly one `SKILL.md`.
- `tools/skill-groups.tsv` contains every mainline skill exactly once, no stale entries, valid groups, and valid dependency names.
- If a skill invokes a helper, use the documented resolver chain and declare the failure policy.
- Shared references should remain canonical; avoid copying stale policy into many skills.

## Mirrors and Overlays

- Codex mirrors should preserve semantics while adapting reviewer/executor mechanics.
- Claude-review and Gemini-review overlays should only override the intended skills.
- Run mirror/overlay tests after changing a mirrored skill or generation script.

## Integrity and Provenance

- `tools/provenance.py` fails closed on unknown or colliding model-family names.
- Same-family review may be recorded as provisional but cannot grant auto-curation authority.
- Auto-authored artifacts need tamper-evident sidecars; human/canonical files should not be treated as auto-curatable by accident.
- Audit and trace files must not contain credentials.

## Installer and Tooling

- Installer changes need synthetic temporary-project tests for create, reconcile, uninstall, selection, manifest, pointer, and symlink safety.
- Research Wiki changes need helper-resolution and temp-project tests.
- Watchdog changes need mocked session/GPU/download tests rather than real daemons.
- MCP server changes need JSON-RPC schema tests and mocked API/error paths.
