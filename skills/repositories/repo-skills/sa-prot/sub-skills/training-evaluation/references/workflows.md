# Training and Evaluation Workflows

This reference explains SaProt training and evaluation flows in operational terms so an agent can adapt configs safely without launching unnecessary expensive runs.

## Dynamic Loader Flow

SaProt launchers treat YAML as the source of truth. The loader utilities copy the config section, pull out `kwargs`, merge those kwargs into the top level, and pass the result into a registry-backed interface:

1. `load_model(config.model)` initializes the registered model named by `model.model_py_path` through `ModelInterface.init_model`.
2. `load_dataset(config.dataset)` initializes the registered datamodule named by `dataset.dataset_py_path` through `DataInterface.init_dataset`.
3. `load_trainer(config)` copies `config.Trainer`, replaces truthy `Trainer.logger` with a WandB logger, builds a `DDPStrategy` from `Trainer.strategy`, and returns a PyTorch Lightning `Trainer`.
4. `load_wandb(config)` uses `setting.wandb_config.project` and `setting.wandb_config.name`, and passes the full config into the WandB run.
5. `load_strategy(config.Trainer.strategy)` converts a numeric `timeout` value to a `datetime.timedelta` before building the DDP strategy.

Implication: a YAML typo in `model_py_path`, `dataset_py_path`, `kwargs`, or `Trainer.strategy` usually fails only when the real launcher imports modules. Run `saprot_config_check.py` first to catch structural and path risks without importing heavy dependencies.

## Training Launcher Flow

The training/fine-tuning launcher performs the following steps:

1. Read the YAML config.
2. Seed the run when `setting.seed` is truthy.
3. For every key in `setting.os_environ`, set it only if the process environment does not already define it; if the process already defines it, the process value wins and is written back into the in-memory config.
4. Disable Lightning logging on non-root nodes when `NODE_RANK` is not `0`.
5. Load model, datamodule, and trainer.
6. Run `trainer.fit(model=model, datamodule=data_module)`.
7. If the model exposes `save_path`, reload the saved checkpoint before testing. LoRA configs reload by setting `model.kwargs.lora_config_path`; normal configs call `model.load_checkpoint(model.save_path, load_prev_scheduler=model.load_prev_scheduler)`.
8. Run `trainer.test(model=model, datamodule=data_module)`.

Treat step 6 as expensive by default. The provided pretraining config has a million-step schedule; downstream configs often request multiple GPUs, fp16 precision, and many dataloader workers.

## Zero-Shot Mutation Flow

The zero-shot launcher uses the same model/dataset/trainer loading path, then evaluates every child entry of `setting.dataset_dir`:

1. Optionally creates the parent of `setting.out_path` and writes a `dataset\tspearman` header on root node.
2. Creates `model.kwargs.log_dir` when present; this is needed for ClinVar per-protein CSV logs.
3. For each dataset name under `setting.dataset_dir`, sets `data_module.test_lmdb` to that child path.
4. Runs `trainer.test(model=model, datamodule=data_module)` and reads the returned `spearman` metric.
5. Appends one row to `setting.out_path` on root node when an output path is configured.

ProteinGym uses this flow to write a Spearman TSV when `setting.out_path` is configured. ClinVar uses this flow to populate CSV logs that are later merged with labels for ROC AUC.

## ClinVar AUC Flow

ClinVar zero-shot evaluation is two-stage:

1. Run the zero-shot mutation launcher with a ClinVar config whose model kwargs include `log_clinvar: true` and a writable `log_dir`.
2. Aggregate all CSV logs in that log directory with the label CSV and compute ROC AUC.

The mutation model writes log files with columns `protein_name`, `mutations`, and `evol_indices`. The original aggregation logic right-joins predictions with label rows on `protein_name` and `mutations`, removes `ClinVar_labels == 0.5`, and calculates ROC AUC from `ClinVar_labels` and `evol_indices`. The bundled aggregation script preserves that intent but makes paths explicit, validates columns, and reports duplicates and missing joins.

## Checkpoint and Optimizer Behavior

All SaProt task models inherit checkpoint behavior from `AbstractModel`:

- `save_path` controls whether validation can save a best checkpoint and whether the training launcher tries to reload a checkpoint before testing.
- `save_weights_only: true` saves only the wrapped model state dictionary; `false` also saves global step, epoch, best metric, optimizer state, and scheduler state.
- `load_prev_scheduler: true` requires optimizer and scheduler state in the checkpoint; if those fields are absent, checkpoint loading raises an error and the config should use `load_prev_scheduler: false`.
- `check_save_condition(now_value, mode)` saves only on distributed rank 0 and compares the current validation metric against the previous best value.
- Optimizer setup uses AdamW, applies weight decay to non-bias/non-LayerNorm parameters, and attaches the repository's ESM-style scheduler at step interval.

Task models choose their validation save metric: language-model and regression tasks minimize validation loss, classification and PPI maximize validation accuracy, annotation maximizes validation Fmax, and contact prediction maximizes a contact precision metric.

## Distributed and Logging Behavior

The provided configs often define `CUDA_VISIBLE_DEVICES`, `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, and `NODE_RANK` under `setting.os_environ`. The training launcher respects existing process environment values over YAML defaults. This means scheduler or shell-provided DDP values can silently override YAML values.

Use these rules when adapting configs:

- Keep `WORLD_SIZE: 1`, `num_nodes: 1`, and `NODE_RANK: 0` for a single-machine smoke run.
- Match `Trainer.devices` to the visible CUDA device count, not the total hardware count.
- Set `Trainer.logger: false` for dry-runs, CI, or non-interactive environments.
- Provide `WANDB_API_KEY` only through the user environment or a private config copy; do not bake secrets into shared runtime instructions.
- If using multiple nodes, ensure each node has a consistent `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, and correct `NODE_RANK`.

## Config Family Notes

- Pretraining: uses language-model config settings, `saprot_lm_model`, long schedules, scheduler state, `save_weights_only: false`, and Foldseek-tokenized pretraining LMDBs.
- Supervised fine-tuning: Thermostability, EC, GO, DeepLoc, MetalIonBinding, HumanPPI, and Contact configs share the training launcher but vary model class, dataset class, batch size, validation metric, device count, and pLDDT kwargs.
- Zero-shot mutation: ProteinGym and ClinVar configs use `mutation_zeroshot.py`, mutation datasets, a Foldseek-aware mutation model, and `trainer.test` loops rather than `trainer.fit`.

## Safety Checklist Before a Real Run

- Confirm all model weights, tokenizers, LMDB directories, Foldseek binary paths, and output directories are local and intentional.
- Confirm the working directory matches relative paths in the YAML, or convert copied configs to absolute paths chosen by the user.
- Reduce devices, batch sizes, workers, and precision before a smoke test.
- Disable WandB unless the user explicitly wants external logging.
- Run a diagnostic pass with `saprot_config_check.py` and review warnings.
- Ask for explicit confirmation before launching full pretraining, full downstream fine-tuning, ProteinGym-wide evaluation, or ClinVar-wide evaluation.
