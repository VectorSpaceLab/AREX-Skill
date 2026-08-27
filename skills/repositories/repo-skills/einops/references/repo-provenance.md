# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
`einops` repository. If the current repo commit, dirty state, package version,
public APIs, backend list, test runner, docs scripts, or major evidence paths
differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T18:54:43Z",
  "repository": {
    "name": "einops",
    "remote_url": "https://github.com/arogozhnikov/einops.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v0.9.0dev",
    "commit": "e0d5eb4fd535945ff65d309206d0f1754a926821",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "einops",
      "version": "0.9.0dev",
      "distribution_version": "0.9.0.dev0",
      "import_names": ["einops"]
    }
  ],
  "evidence": {
    "source_roots": [
      "einops/__init__.py",
      "einops/einops.py",
      "einops/packing.py",
      "einops/parsing.py",
      "einops/array_api.py",
      "einops/_backends.py",
      "einops/_torch_specific.py",
      "einops/layers/"
    ],
    "docs": [
      "README.md",
      "docs/1-einops-basics.ipynb",
      "docs/2-einops-for-deep-learning.ipynb",
      "docs/3-einmix-layer.ipynb",
      "docs/4-pack-and-unpack.ipynb",
      "docs_src/api/",
      "mkdocs.yml"
    ],
    "tests": [
      "einops/tests/run_tests.py",
      "einops/tests/__init__.py",
      "einops/tests/test_ops.py",
      "einops/tests/test_examples.py",
      "einops/tests/test_other.py",
      "einops/tests/test_einsum.py",
      "einops/tests/test_packing.py",
      "einops/tests/test_array_api.py",
      "einops/tests/test_layers.py",
      "einops/tests/test_parsing.py"
    ],
    "scripts": [
      "scripts/convert_readme.py",
      "scripts/test_notebooks.py",
      "scripts/pytorch_examples_source/converter.py"
    ],
    "ci": [
      ".github/workflows/run_tests.yml",
      ".github/workflows/test_notebooks.yml",
      ".github/workflows/deploy_docs.yml",
      ".github/workflows/deploy_to_pypi.yml"
    ],
    "existing_skills": [
      "skills/einops.log"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the current checkout has dirty source, docs, tests, scripts, or package
  metadata beyond generated `skills/` artifacts, run `refresh-repo-skill`.
- If `einops/__init__.py` changes `__version__` or `__all__`, refresh.
- If function signatures or public behavior change in `einops/einops.py`,
  `einops/packing.py`, `einops/array_api.py`, or `einops/layers/`, refresh.
- If backend classes, layer modules, torch compile integration, native test
  runner semantics, docs scripts, or CI matrices change, refresh.

## Public Version Notes

The source package version string is `0.9.0dev`; editable installation metadata
reported `0.9.0.dev0`. This difference is normal Python packaging normalization
for the inspected source state.
