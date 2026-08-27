# Repository Provenance

## Purpose

Read this before deciding whether this Maestro skill is current for a checkout or installed package. If the current repo commit, dirty state, package version, public entry points, or evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T09:00:00Z",
  "repository": {
    "name": "maestro",
    "remote_url": "https://github.com/roboflow/maestro.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "9460df359611564c43af79038070022a3ca1ede8",
    "working_tree": "clean-at-source-evidence-capture-before-generated-skill-files",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "maestro",
      "version": "1.1.0rc3",
      "import_names": ["maestro"]
    }
  ],
  "evidence": {
    "source_roots": [
      "maestro/cli",
      "maestro/trainer/common",
      "maestro/trainer/models/florence_2",
      "maestro/trainer/models/paligemma_2",
      "maestro/trainer/models/qwen_2_5_vl"
    ],
    "docs": [
      "README.md",
      "docs/index.md",
      "docs/datasets/jsonl.md",
      "docs/models/florence_2.md",
      "docs/models/paligemma_2.md",
      "docs/models/qwen_2_5_vl.md"
    ],
    "examples": [
      "cookbooks/maestro_florence_2_object_detection.ipynb",
      "cookbooks/maestro_paligemma_2_json_extraction.ipynb",
      "cookbooks/maestro_qwen2_5_vl_json_extraction.ipynb",
      "cookbooks/maestro_qwen2_5_vl_object_detection.ipynb"
    ],
    "tests": [
      "test/meastro/trainer/common/datasets/test_roboflow.py",
      "test/meastro/trainer/models/florence_2/test_detection.py"
    ],
    "configs": [
      "pyproject.toml",
      "tox.ini",
      "mkdocs.yaml"
    ],
    "existing_repo_local_skills": [
      "skills/maestro.log"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, optional dependency groups, CLI entry points, or model routes change, refresh even when the commit is similar.
- If a future checkout has new model families, new dataset formats, changed Qwen utility compatibility, or altered train/inference signatures, refresh before relying on this skill.
- Generated skill files and review artifacts are not part of the source-evidence dirty state above.
