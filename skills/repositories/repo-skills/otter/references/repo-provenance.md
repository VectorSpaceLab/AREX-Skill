# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the Otter repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T16:38:30Z",
  "repository": {
    "name": "Otter",
    "remote_url": "https://github.com/EvolvingLMMs-Lab/Otter.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1e7eb9a6fb12ef410082e796c463b99495637b85",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "otter-ai",
      "version": "0.0.0-alpha-7",
      "import_names": ["otter_ai"]
    }
  ],
  "evidence": {
    "source_roots": ["src/otter_ai", "xformers_model"],
    "docs": ["README.md", "docs/OtterHD.md", "docs/benchmark_eval.md", "docs/huggingface_compatible.md", "docs/mimicit_format.md", "docs/server_host.md", "mimic-it/README.md", "mimic-it/convert-it/README.md"],
    "examples": ["pipeline/demos", "shared_scripts"],
    "tests": ["unit_tests/test_prerun.py", "unit_tests/test_mmc4_dataset.py"],
    "configs": ["environment.yml", "requirements.txt", "pyproject.toml", "setup.py", "pipeline/accelerate_configs", "pipeline/train/config.yaml"],
    "workflow_sources": ["pipeline/train", "pipeline/mimicit_utils", "pipeline/benchmarks", "pipeline/serve", "pipeline/utils", "mimic-it/convert-it", "mimic-it/syphus"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the dirty paths are not just generated skill/test artifacts, review whether the changed source/docs/config paths affect this skill.
- If package metadata, public imports, model signatures, training flags, benchmark registry names, or serving command flags changed even on the same commit, run `refresh-repo-skill`.
- If `requirements.txt` changes around `transformers`, `tokenizers`, `huggingface_hub`, `accelerate`, or `peft`, re-run the import compatibility checks in [installation](installation.md).
