# Repository Provenance

## Purpose

Read this before deciding whether the m2cgen skill still matches a checkout. If the commit, dirty paths, package version, public entry points, or major evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T17:30:08Z",
  "repository": {
    "name": "m2cgen",
    "remote_url": "https://github.com/BayesWitnesses/m2cgen.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "9784632311986234032673cdbfd29fc4c5cb429d",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "m2cgen",
      "version": "0.10.1",
      "import_names": ["m2cgen"]
    }
  ],
  "evidence": {
    "source_roots": ["m2cgen"],
    "docs": ["README.md", "setup.py", "MANIFEST.in", "setup.cfg"],
    "examples": ["generated_code_examples"],
    "tests": ["tests/test_cli.py", "tests/test_exporters.py", "tests/test_fallback_expressions.py", "tests/assemblers", "tests/interpreters", "tests/e2e"],
    "configs": ["requirements-test.txt", "Makefile", "Dockerfile"]
  }
}
```

## Historical verification warning

This snapshot describes the source evidence used to create the skill; it is not a claim that every repository test passed. Historical verification of `tests/e2e/test_cli.py` recorded one pass, three failures, and one intentional skip. The three failures were legacy hard-coded expected-score assertions whose fixture value differed from the model/dependency result in that verification environment.

Those failures are unresolved evidence, not a successful end-to-end result. They were **not rerun** while maintaining this bundle. Do not describe the legacy e2e fixture as passing, and do not use it as confirmation of numerical equivalence. Before relying on it, reproduce it in the intended dependency environment, identify the fixture/model-version provenance, and reconcile the expected value with the intended baseline rather than changing it merely to obtain a pass.

The bundled `sub-skills/model-export/scripts/smoke_export.py` is deliberately narrower: it checks public export calls and, when requested, selected CLI serialization paths. It does not replace the unresolved e2e fixture or validate generated code in non-Python target runtimes.

## Refresh guidance

When refreshing this skill, keep the e2e warning until the fixture mismatch has been independently reproduced, reconciled, and rerun with recorded results. Record any remaining failure as a warning or failure, never as an implied pass.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If the working tree becomes clean or the changed paths differ from `skills/`, refresh the skill baseline.
- Refresh if `setup.py`, `m2cgen/exporters.py`, `m2cgen/cli.py`, assembler dispatch, interpreter dispatch, or public README support tables change.
