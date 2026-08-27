# SaProt Configuration Reference

SaProt task YAML files use four main sections: `setting`, `model`, `dataset`, and `Trainer`. This reference focuses on safely editing and validating those sections before routing execution to the training/evaluation sub-skill.

## Top-Level Sections

| Section | Purpose | Common keys |
| --- | --- | --- |
| `setting` | Reproducibility, environment variables, WandB metadata, and task-specific output roots. | `seed`, `os_environ`, `wandb_config`, `out_path`, `dataset_dir` |
| `model` | Dynamic model module path and constructor kwargs. | `model_py_path`, `kwargs.config_path`, `kwargs.load_pretrained`, `save_path`, optimizer/scheduler kwargs |
| `dataset` | Dynamic dataset module path, LMDB split paths, dataloader kwargs, and dataset-specific kwargs. | `dataset_py_path`, `train_lmdb`, `valid_lmdb`, `test_lmdb`, `dataloader_kwargs`, `kwargs.tokenizer` |
| `Trainer` | PyTorch Lightning trainer settings. | `accelerator`, `devices`, `num_nodes`, `precision`, `strategy`, `logger`, `max_epochs`, `max_steps` |

## Path Conventions

Paths are normally written relative to the directory where SaProt commands are run. A validator should therefore use the intended run base as `--base-dir`.

- `model.model_py_path` resolves under a `model/` package-style directory, without `.py`. Example: `saprot/saprot_regression_model`.
- `dataset.dataset_py_path` resolves under a `dataset/` package-style directory, without `.py`. Example: `saprot/saprot_regression_dataset`.
- `model.kwargs.config_path` points to a local Hugging Face model/tokenizer directory, usually under `weights/PLMs/`.
- `dataset.kwargs.tokenizer` points to the tokenizer directory used by `EsmTokenizer.from_pretrained`, usually the same directory as `model.kwargs.config_path`.
- `dataset.train_lmdb`, `dataset.valid_lmdb`, and `dataset.test_lmdb` point to LMDB split directories, usually under `LMDB/`.
- `model.save_path` points to a checkpoint output path, often under `weights/<Task>/`.

The generated skill must not assume the original checkout still exists. When future agents edit a config, they should copy or create the YAML inside the active project and validate paths against that project’s run base.

## Common Dataset Mappings

| Task family | SaProt-style dataset | Typical model path | Required assets |
| --- | --- | --- | --- |
| Thermostability regression | `saprot/saprot_regression_dataset` | `saprot/saprot_regression_model` | regression LMDB, SaProt tokenizer/model directory |
| DeepLoc / MetalIonBinding classification | `saprot/saprot_classification_dataset` | `saprot/saprot_classification_model` | classification LMDB, tokenizer/model directory |
| EC / GO annotation | `saprot/saprot_annotation_dataset` | `saprot/saprot_annotation_model` | annotation LMDB, tokenizer/model directory |
| HumanPPI | `saprot/saprot_ppi_dataset` | `saprot/saprot_ppi_model` | paired-sequence LMDB, tokenizer/model directory |
| Contact prediction | `saprot/saprot_contact_dataset` | `saprot/saprot_contact_model` | contact LMDB with `valid_mask` and `tertiary` |
| Pretraining | `saprot/saprot_foldseek_dataset` or `saprot/saprot_lm_dataset` | `saprot/saprot_lm_model` | pretraining LMDB and tokenizer/model directory |
| Zero-shot mutation | `mutation_zeroshot_dataset` | mutation model path | mutation dataset directory and local model assets |

## CPU Smoke-Test Adaptation

For a lightweight config sanity check or tiny CPU smoke run, edit the YAML before handing execution to training/evaluation:

- Set `Trainer.accelerator: cpu`.
- Set `Trainer.devices: 1`.
- Consider `Trainer.precision: 32`, because 16-bit precision is usually GPU-oriented.
- Set `dataset.dataloader_kwargs.num_workers: 0` to avoid multiprocessing surprises.
- Set `Trainer.logger: False` or configure offline logging if WandB should not run.
- Reduce `dataset.dataloader_kwargs.batch_size` if memory is constrained.
- Use tiny LMDB split directories with matching `length` keys and valid row schemas.

This adaptation validates configuration and data plumbing only. It does not prove model quality or benchmark correctness.

## Bundled Config Validator

Use `scripts/validate_config.py` for static checks without importing heavy ML modules:

```bash
python scripts/validate_config.py --config task.yaml --base-dir .
```

Add stricter local asset checks when the machine should already contain the required directories:

```bash
python scripts/validate_config.py --config task.yaml --base-dir . --require-assets
```

The validator checks:

- YAML parseability and required top-level sections.
- `model_py_path` and `dataset_py_path` syntax and whether matching source files exist when a base directory is provided.
- LMDB split paths and, when available, presence of `data.mdb`, `lock.mdb`, and the `length` key.
- Tokenizer/model paths under model and dataset kwargs.
- Trainer accelerator, devices, CUDA visibility, precision, and distributed strategy choices.
- pLDDT-related kwargs that require pLDDT fields in the underlying JSON rows.

## Editing Rules

- Do not add `.py` to `model_py_path` or `dataset_py_path`.
- Do not prefix module paths with `model/` or `dataset/` inside the YAML.
- Keep SaProt model/tokenizer directories local; examples use `weights/PLMs/` as a convention, not as a downloadable dependency.
- Treat `LMDB/` and `weights/PLMs/` as placement conventions: users must supply their own datasets and model assets.
- Validate config paths before launching expensive training or evaluation.
