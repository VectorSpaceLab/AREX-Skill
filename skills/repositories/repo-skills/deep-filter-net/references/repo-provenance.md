# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of DeepFilterNet. If the current repo commit, source dirty state, package metadata, source layout, or public entry points differ materially from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:50:20Z",
  "repository": {
    "name": "DeepFilterNet",
    "remote_url": "https://github.com/Rikorose/DeepFilterNet.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d375b2d8309e0935d165700c91da9de862a99c31",
    "working_tree": "clean-source-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "DeepFilterNet",
      "version": "0.5.7-pre (source metadata; editable inspection normalized to 0.5.7rc0)",
      "import_names": ["df"],
      "entry_points": ["deepFilter", "deep-filter-py"]
    },
    {
      "name": "DeepFilterLib",
      "version": "0.5.7-pre source / 0.5.6 prebuilt inspection wheel",
      "import_names": ["libdf"]
    },
    {
      "name": "DeepFilterDataLoader",
      "version": "0.5.7-pre source (optional training component, not installed in inspection env)",
      "import_names": ["libdfdata"]
    }
  ],
  "evidence": {
    "source_roots": [
      "DeepFilterNet/df",
      "pyDF",
      "pyDF-data/libdfdata",
      "libDF/src",
      "ladspa/src",
      "demo/src"
    ],
    "docs": [
      "README.md",
      "ladspa/README.md",
      "demo/README.md",
      "assets/README.md"
    ],
    "examples_and_scripts": [
      "scripts/external_usage.py",
      "DeepFilterNet/df/scripts/prepare_data.py",
      "DeepFilterNet/df/scripts/export.py",
      "DeepFilterNet/df/scripts/test_voicebank_demand.py",
      "DeepFilterNet/df/scripts/test_dns_2020.py",
      "DeepFilterNet/df/scripts/dnsmos.py",
      "scripts/set_batch_size.py",
      "ladspa/filter-chain-configs/deepfilter-mono-source.conf",
      "ladspa/filter-chain-configs/deepfilter-stereo-sink.conf"
    ],
    "tests": [
      "DeepFilterNet/tests/test_dflib.py"
    ],
    "configs": [
      "DeepFilterNet/pyproject.toml",
      "pyDF/pyproject.toml",
      "pyDF-data/pyproject.toml",
      "Cargo.toml",
      "libDF/Cargo.toml",
      "ladspa/Cargo.toml",
      "demo/Cargo.toml",
      "assets/dataset.cfg"
    ],
    "binary_or_large_artifacts_not_copied": [
      "models/*.zip",
      "models/*.tar.gz",
      "assets/*.hdf5",
      "assets/*.wav"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If source files in the evidence paths changed, refresh even when the commit is the same.
- Ignore this generated skill directory and review artifacts when comparing the source dirty state; they are production outputs, not upstream DeepFilterNet evidence.
- If package entry points, extras, model names, CLI flags, or Rust workspace features change, refresh the affected sub-skills.
