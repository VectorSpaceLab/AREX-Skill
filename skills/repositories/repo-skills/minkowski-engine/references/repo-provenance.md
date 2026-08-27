# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MinkowskiEngine. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T06:49:26Z",
  "repository": {
    "name": "MinkowskiEngine",
    "remote_url": "https://github.com/NVIDIA/MinkowskiEngine.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "02fc608bea4c0549b0a7b00ca1bf15dee4a0b228",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "MinkowskiEngine",
      "version": "0.5.4",
      "import_names": ["MinkowskiEngine"]
    }
  ],
  "evidence": {
    "source_roots": ["MinkowskiEngine", "src", "pybind"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests/python", "tests/cpp"],
    "package_metadata": ["setup.py", "requirements.txt", "MANIFEST.in"],
    "build_and_container": ["Makefile", "docker/Dockerfile"],
    "existing_skills": ["skills/MinkowskiEngine.log"]
  }
}
```

## Verified Inspection Baseline

- A private CPU-only inspection environment successfully imported `MinkowskiEngine==0.5.4`.
- The inspection smoke created a tiny CPU `SparseTensor` and ran `MinkowskiConvolution`.
- CUDA-specific behavior was not verified during this creation run and should be rechecked in a CUDA-enabled build before claiming GPU coverage.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the dirty state changes in user-facing source, docs, examples, tests, or build metadata, refresh the skill.
- If `MinkowskiEngine.__version__`, setup flags, public imports, layer signatures, or data/coordinate semantics change, refresh the skill.
