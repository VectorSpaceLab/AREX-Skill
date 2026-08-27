# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T17:32:11Z",
  "repository": {
    "name": "PyDESeq2",
    "remote_url": "https://github.com/scverse/PyDESeq2",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "8c0d057684a144e409f55ea989b0f8a1322288f8",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "pydeseq2",
      "version": "0.5.4",
      "import_names": [
        "pydeseq2"
      ],
      "requires_python": ">=3.11"
    }
  ],
  "evidence": {
    "package_metadata": [
      "pyproject.toml",
      "README.md"
    ],
    "source_roots": [
      "pydeseq2/"
    ],
    "docs": [
      "docs/source/index.rst",
      "docs/source/api/",
      "docs/source/usage/"
    ],
    "examples": [
      "examples/plot_minimal_pydeseq2_pipeline.py",
      "examples/plot_pandas_io_example.py",
      "examples/plot_step_by_step.py"
    ],
    "datasets": [
      "datasets/synthetic/"
    ],
    "tests": [
      "tests/test_pydeseq2.py",
      "tests/test_edge_cases.py",
      "tests/test_utils.py",
      "tests/data/"
    ],
    "excluded": [
      ".github/",
      ".binder/",
      "docs/source/_static/",
      "docs/Makefile",
      "docs/make.bat",
      "skills/tests/",
      "skills/pydeseq2/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, metadata, docs, examples, tests, or dependency changes not represented by the dirty paths above, run `refresh-repo-skill`.
- If `pyproject.toml` changes the package version, dependencies, Python support, or public entry points, run `refresh-repo-skill`.
- If `DeseqDataSet`, `DeseqStats`, `DefaultInference`, `preprocessing`, or `utils.load_example_data` signatures change, run `refresh-repo-skill`.
- If examples or tests change the recommended workflows, validation behavior, contrast rules, VST behavior, or supported feature scope, run `refresh-repo-skill`.

## Evidence Notes

The generated skill is based on source files, documentation, examples, tests, package metadata, and live package inspection. Original repository examples and tests were treated as evidence and verification candidates only; runnable future-agent helpers were adapted into this skill's own `scripts/` directories.
