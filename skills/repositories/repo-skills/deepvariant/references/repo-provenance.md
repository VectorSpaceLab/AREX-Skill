# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of DeepVariant. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T16:50:59Z",
  "repository": {
    "name": "deepvariant",
    "remote_url": "https://github.com/google/deepvariant",
    "vcs": "git",
    "branch": "r1.10",
    "tag": null,
    "commit": "45f2627504c59785ea2b88d0256a2ec347bce7b4",
    "working_tree": "dirty-untracked",
    "dirty_paths": [
      "deepvariant.egg-info/",
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "deepvariant",
      "version": "1.10.0",
      "import_names": ["deepvariant", "deeptrio"]
    }
  ],
  "evidence": {
    "source_roots": [
      "deepvariant/",
      "deeptrio/",
      "third_party/nucleus/io/",
      "third_party/nucleus/util/"
    ],
    "docs": [
      "README.md",
      "deeptrio/README.md",
      "docs/"
    ],
    "scripts": [
      "scripts/run_deepvariant.py",
      "scripts/run_deeptrio.py",
      "scripts/run_pangenome_aware_deepvariant.py",
      "tools/print_f1.py",
      "tools/preprocess_truth.py",
      "tools/shuffle_tfrecords_beam.py"
    ],
    "tests": [
      "deepvariant/*_test.py",
      "deeptrio/*_test.py",
      "scripts/*_test.py",
      "deepvariant/testdata/",
      "deeptrio/testdata/"
    ],
    "configs": [
      "BUILD",
      "WORKSPACE",
      "setup.py",
      "deepvariant/cohort_best_practice/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is clean while this snapshot was dirty, or dirty paths differ materially from `dirty_paths`, run `refresh-repo-skill` before relying on changed evidence.
- If package metadata, official wrapper flags, model types, public docs, generated helper scripts, or DeepVariant entry points changed even on the same commit, run `refresh-repo-skill`.
- If a newer DeepVariant release is the target, refresh rather than editing this `1.10.0` skill by hand.
