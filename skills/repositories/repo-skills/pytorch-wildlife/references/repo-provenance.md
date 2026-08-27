# Repository Provenance

Read this before deciding whether the skill is current for a checkout of
Microsoft Biodiversity. If the source commit, package version, public entry
points, or evidence roots differ, use `refresh-repo-skill` rather than
assuming this operating graph is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T19:48:02Z",
  "repository": {
    "name": "Biodiversity",
    "remote_url": "https://github.com/microsoft/Biodiversity",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d3e0a0697167bb859a6f1c97b2e81344ff86c28a",
    "working_tree": "clean at source inspection baseline",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "PytorchWildlife",
      "version": "1.3.0",
      "import_names": ["PytorchWildlife"]
    }
  ],
  "evidence": {
    "source_roots": [
      "PytorchWildlife",
      "PW_Bioacoustics",
      "PW_FT_classification",
      "PW_FT_detection"
    ],
    "docs": [
      "README.md",
      "docs/installation.md",
      "docs/model_zoo",
      "docs/base",
      "docs/bioacoustics.md",
      "docs/demo_and_ui",
      "docs/fine_tuning_modules"
    ],
    "examples": ["demo", "PW_Bioacoustics/demo"],
    "tests": [],
    "configs": [
      "PW_Bioacoustics/template.yaml",
      "PW_FT_classification/configs/config.yaml",
      "PW_FT_detection/config.yaml"
    ],
    "scripts": [
      "PW_Bioacoustics/prepare_dataset.py",
      "PW_Bioacoustics/inference.py",
      "PW_Bioacoustics/train.py",
      "PW_FT_classification/main.py",
      "PW_FT_detection/main.py"
    ]
  }
}
```

## Refresh checks

- If `git rev-parse HEAD` differs from `d3e0a0697167bb859a6f1c97b2e81344ff86c28a`,
  treat the skill as potentially stale.
- If source files under the listed roots, `setup.py`, `requirements.txt`,
  `version.txt`, public docs, or model wrapper entry points changed, refresh
  before relying on exact signatures or dependency claims.
- The source repository contained no dedicated `tests/` directory at the
  inspection baseline. Safe verification therefore uses public scripts,
  source-backed signatures, tiny fixtures, and documented examples rather than
  claiming a native unit-test suite.
- This file describes the public source baseline only. It intentionally omits
  temporary inspection interpreters, environment prefixes, cache locations,
  and generated review artifacts.
