# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, dependency files, configs, source modules, notebooks, or public workflows differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:24:41Z",
  "repository": {
    "name": "StyleTTS2",
    "remote_url": "https://github.com/yl4579/StyleTTS2.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5cedc71c333f8d8b8551ca59378bdcc7af4c9529",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "models",
        "meldataset",
        "utils",
        "losses",
        "optimizers",
        "text_utils",
        "Modules",
        "Utils"
      ],
      "note": "The repository has no pyproject.toml, setup.py, or setup.cfg; it is source-checkout code rather than an installable distribution."
    }
  ],
  "evidence": {
    "source_roots": [
      "models.py",
      "meldataset.py",
      "utils.py",
      "losses.py",
      "optimizers.py",
      "text_utils.py",
      "Modules/",
      "Utils/"
    ],
    "docs": ["README.md"],
    "examples": [
      "Demo/Inference_LJSpeech.ipynb",
      "Demo/Inference_LibriTTS.ipynb",
      "Colab/StyleTTS2_Demo_LJSpeech.ipynb",
      "Colab/StyleTTS2_Demo_LibriTTS.ipynb",
      "Colab/StyleTTS2_Finetune_Demo.ipynb"
    ],
    "tests": [],
    "configs": [
      "Configs/config.yml",
      "Configs/config_ft.yml",
      "Configs/config_libritts.yml",
      "Utils/ASR/config.yml",
      "Utils/PLBERT/config.yml"
    ],
    "data_examples": [
      "Data/train_list.txt",
      "Data/val_list.txt",
      "Data/OOD_texts.txt"
    ],
    "training_entrypoints": [
      "train_first.py",
      "train_second.py",
      "train_finetune.py",
      "train_finetune_accelerate.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If public files listed in `evidence` changed materially, refresh even if the commit is the same.
- If packaging metadata is added later, refresh because install and import instructions will change.
- The dirty path recorded here is the repository-local `skills/` area created during skill production; source-code evidence files were not modified for this skill.
