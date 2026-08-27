# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of RFdiffusion. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, refresh the skill from repository evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "RFdiffusion",
    "remote_url": "https://github.com/RosettaCommons/RFdiffusion",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2d0c003df46b9db41d119321f15403dec3716cd9",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "rfdiffusion",
      "version": "1.1.0",
      "import_names": ["rfdiffusion"]
    },
    {
      "name": "se3-transformer",
      "version": "1.0.0",
      "import_names": ["se3_transformer"]
    }
  ],
  "entry_points": {
    "scripts": ["run_inference.py"]
  },
  "evidence": {
    "source_roots": ["rfdiffusion/"],
    "docs": ["README.md", "tutorials/protein_binder_design/README.md"],
    "examples": ["examples/", "tutorials/protein_binder_design/"],
    "tests": ["tests/test_diffusion.py"],
    "configs": ["config/inference/base.yaml", "config/inference/symmetry.yaml"],
    "scripts": ["scripts/run_inference.py", "scripts/download_models.sh", "helper_scripts/make_secstruc_adj.py"],
    "packaging": ["setup.py", "env/SE3nv.yml", "docker/Dockerfile"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If package metadata changes from `rfdiffusion` 1.1.0 or the `run_inference.py` script changes behavior, refresh this skill.
- If config groups, example scripts, checkpoint names, public module imports, or contig/potential APIs change, refresh this skill.
- The snapshot was generated from a checkout whose only recorded dirty path category was `skills/`, so changes to source, configs, examples, docs, packaging, or tests should trigger refresh.

## Evidence Boundaries

The generated skill distilled source docs, examples, configs, and helper scripts into self-contained runtime guidance. It intentionally excludes generated caches, local environments, downloaded model weights, prior review artifacts, and vendored SE(3)-Transformer implementation internals except as dependency context.
