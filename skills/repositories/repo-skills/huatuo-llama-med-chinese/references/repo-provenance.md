# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Huatuo-Llama-Med-Chinese / BenTsao. If the current commit, dirty state, source layout, templates, data schemas, scripts, or dependency files differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:42:52Z",
  "repository": {
    "name": "Huatuo-Llama-Med-Chinese",
    "remote_url": "https://github.com/SCIR-HI/Huatuo-Llama-Med-Chinese.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ba9b3d65b33ba346e3d60979019abe6fa2ac741a",
    "working_tree": "dirty-generated-skill-output",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "utils.prompter"
      ],
      "notes": "The repository is script-based and has no pyproject.toml, setup.py, or setup.cfg distribution metadata."
    }
  ],
  "evidence": {
    "source_roots": [
      "utils/",
      "finetune.py",
      "infer.py",
      "infer_literature.py",
      "generate.py",
      "export_hf_checkpoint.py",
      "export_state_dict_checkpoint.py"
    ],
    "docs": [
      "README.md",
      "README_EN.md",
      "benchmark/README.md",
      "utils/README.md"
    ],
    "examples_and_scripts": [
      "scripts/finetune.sh",
      "scripts/infer.sh",
      "scripts/infer-literature-single.sh",
      "scripts/infer-literature-multi.sh",
      "scripts/test.sh"
    ],
    "configs_and_templates": [
      "templates/med_template.json",
      "templates/literature_template.json",
      "templates/bloom_deploy.json"
    ],
    "data_and_benchmarks": [
      "data/infer.json",
      "data/llama_data.json",
      "data/knowledge_tuning_data_sample.txt",
      "data-literature/liver_cancer.json",
      "benchmark/question.json"
    ],
    "dependencies": [
      "requirements.txt"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If templates, data schemas, script arguments, dependency files, or export logic changed, refresh even when the commit is otherwise familiar.
- If a future checkout adds package metadata, console entry points, new model families, new benchmark runners, or new safe tests, refresh the skill so routing and validation can cover them.
- The recorded dirty path reflects generated skill output, not a source-code modification in the original workflows.
