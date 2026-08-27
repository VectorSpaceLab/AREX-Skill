# Repository Provenance

Read this before deciding whether this skill is current for a checkout of Pytorch-UNet. If commit, dirty state, public entry points, dependencies, or evidence paths differ materially, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T16:54:24Z",
  "repository": {
    "name": "Pytorch-UNet",
    "remote_url": "https://github.com/milesial/Pytorch-UNet.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "21d7850f2af30a9695bbeea75f3136aa538cfc4a",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "Dirty state is limited to generated skill/test artifacts under skills/."
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "unet",
        "utils"
      ]
    },
    {
      "name": "torch",
      "version": "2.5.1+cu124 observed during inspection",
      "import_names": [
        "torch"
      ]
    },
    {
      "name": "torchvision",
      "version": "0.20.1+cu124 observed during inspection",
      "import_names": [
        "torchvision"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "unet/",
      "utils/"
    ],
    "docs": [
      "README.md"
    ],
    "scripts_and_clis": [
      "train.py",
      "predict.py",
      "evaluate.py",
      "hubconf.py",
      "scripts/download_data.sh",
      "scripts/download_data.bat"
    ],
    "metadata_and_runtime": [
      "requirements.txt",
      "Dockerfile"
    ],
    "tests": [],
    "configs": [
      "data/imgs/.keep",
      "data/masks/.keep"
    ]
  },
  "verification_summary": {
    "inspection_environment_status": "ok",
    "safe_native_cases": [
      "train.py -h",
      "predict.py -h",
      "UNet CPU forward smoke",
      "CUDA tensor smoke",
      "CarvanaDataset tiny fixture"
    ],
    "skipped_native_cases": [
      "Kaggle download helper: credentials/network/large writes",
      "full training: expensive/W&B/data required",
      "pretrained torch.hub: network/download"
    ]
  }
}
```

## Refresh guidance

- Refresh if `train.py`, `predict.py`, `evaluate.py`, `hubconf.py`, `unet/`, `utils/`, `requirements.txt`, or documented README workflows change.
- Refresh if packaging metadata is added, public CLI flags change, checkpoint format changes, or mask/data loading semantics change.
- The source checkout was dirty because generated skill artifacts were present under `skills/`; those artifacts are not repository source evidence.
