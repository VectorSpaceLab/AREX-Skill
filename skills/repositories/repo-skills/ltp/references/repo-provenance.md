# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an LTP checkout. If the current commit, dirty state, package versions, package split, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T08:20:00Z",
  "repository": {
    "name": "ltp",
    "remote_url": "https://github.com/HIT-SCIR/ltp.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1f042d48b0a785ff7875b2e63c1439ef8c78995c",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "ltp",
      "version": "4.2.15",
      "import_names": ["ltp"]
    },
    {
      "name": "ltp-core",
      "version": "0.1.4",
      "import_names": ["ltp_core"]
    },
    {
      "name": "ltp-extension",
      "version": "0.1.13",
      "import_names": ["ltp_extension"]
    },
    {
      "name": "ltp-rust-crate",
      "version": "0.1.9",
      "import_names": ["ltp"]
    },
    {
      "name": "ltp-cffi",
      "version": "0.1.0",
      "import_names": ["ltp"]
    }
  ],
  "evidence": {
    "source_roots": [
      "python/interface/ltp",
      "python/core/ltp_core",
      "python/extension/ltp_extension",
      "python/extension/src",
      "rust/ltp/src",
      "rust/ltp-cffi/src"
    ],
    "docs": [
      "README.md",
      "python/interface/README.md",
      "python/interface/docs",
      "python/extension/README.md",
      "rust/ltp/README.md",
      "rust/ltp-cffi/README.md"
    ],
    "examples": [
      "python/interface/examples",
      "python/extension/examples",
      "rust/ltp/examples",
      "rust/ltp-cffi/examples"
    ],
    "tests": [
      "python/core/tests/test_crf.py",
      "rust/ltp/test"
    ],
    "configs": [
      "python/core/configs",
      "python/core/data",
      "Cargo.toml",
      "python/core/setup.py",
      "python/interface/setup.py",
      "python/extension/Cargo.toml",
      "rust/ltp/Cargo.toml",
      "rust/ltp-cffi/Cargo.toml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current working tree is dirty and the snapshot above is clean, refresh before relying on API, packaging, or routing details.
- If any of the three Python distributions (`ltp`, `ltp-core`, `ltp-extension`) changed dependency metadata, public APIs, model-loading behavior, or output shapes, refresh the Python sub-skills.
- If Rust crate features, exported model aliases, C FFI symbols, or Cargo versions changed, refresh `rust-bindings`.
- If new model families, tasks, label sets, config groups, or examples were added, update `model-catalog-and-tasks.md`, the relevant sub-skill references, and routing metadata.
