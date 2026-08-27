# office-benchmarks Troubleshooting

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The runtime cannot find the split files | The packaged runtime was not installed, the unpackaged launcher was bypassed, or the bundled data tree was damaged | Use `python scripts/main.py ...` or install with `python scripts/install_office_runtime.py`; keep both `references/data_txt/` and `scripts/office_runtime/src/libmtl_office_benchmark/data_txt/` intact. |
| Image paths from a split file do not resolve | `--dataset_path` does not point at the raw Office image root | Point `--dataset_path` at the dataset root that contains all domain images. |
| `multi_input` is false | The office benchmark is multi-input by design | Pass `--multi_input`. |
| The backbone download stalls | `resnet18(pretrained=True)` needs ImageNet weights | Allow a network download or prefill the cache. |
| Dataset names are rejected | The `--dataset` value is not `office-31` or `office-home` | Pick one of the two supported dataset families. |

## Office-31 vs Office-Home

- Office-31 has three tasks and 31 classes per task.
- Office-Home has four tasks and 65 classes per task.
- The task names differ, so validate the split file names before running.

## Recovery path

If the dataloaders still fail after layout validation, run the bundled office
layout checker with `--check-runtime-package` and inspect the first missing
image path that it reports. If the installed console entry point is missing,
re-run `python scripts/install_office_runtime.py --python "$(command -v python)"`
from this sub-skill directory.
