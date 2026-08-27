# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of OpenFold. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-24T00:00:00Z",
  "repository": {
    "name": "openfold",
    "remote_url": "https://github.com/aqlaboratory/openfold",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "be2ec1841f16c966c65ae0e7599ebbadc725757d",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "openfold",
      "version": "2.2.0",
      "import_names": [
        "openfold"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "openfold",
      "run_pretrained_openfold.py",
      "train_openfold.py",
      "thread_sequence.py"
    ],
    "docs": [
      "README.md",
      "docs/source/Installation.md",
      "docs/source/Inference.md",
      "docs/source/Multimer_Inference.md",
      "docs/source/Single_Sequence_Inference.md",
      "docs/source/Training_OpenFold.md",
      "docs/source/OpenFold_Training_Setup.md",
      "docs/source/Aux_seq_files.md",
      "docs/source/OpenFold_Parameters.md"
    ],
    "examples": [
      "examples/monomer"
    ],
    "tests": [
      "tests",
      "tests/test_data"
    ],
    "configs": [
      "setup.py",
      "environment.yml",
      "Dockerfile",
      "deepspeed_config.json"
    ],
    "scripts": [
      "scripts",
      "scripts/alignment_db_scripts",
      "scripts/slurm_scripts"
    ],
    "existing_skill_evidence": [
      "skills/openfold"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ materially from `dirty_paths`, run `refresh-repo-skill` before relying on repo-sensitive details.
- If package metadata, public CLI flags, optional dependency behavior, or major evidence paths changed, run `refresh-repo-skill` even on the same commit.
- The snapshot intentionally records only relative evidence paths and public repository metadata; it omits local checkout paths and private inspection environment details.
