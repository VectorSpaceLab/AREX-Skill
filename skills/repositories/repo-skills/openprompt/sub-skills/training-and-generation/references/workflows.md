# Workflows: Training and Generation

These workflows avoid starting expensive training until the config, paths, backend, and checkpoint/logging behavior are understood.

## 1. Inspect a config without training

From the sub-skill root:

```bash
python scripts/inspect_training_config.py \
  --config-yaml experiments/classification_manual_prompt.yaml
```

Useful variants:

```bash
# Machine-readable output
python scripts/inspect_training_config.py \
  --config-yaml experiments/generation_manual_template.yaml --json

# Also probe torch/CUDA availability; still does not load a PLM or dataset
python scripts/inspect_training_config.py \
  --config-yaml experiments/lmbff.yaml --probe-torch

# Parse only raw YAML if importing OpenPrompt is currently broken
python scripts/inspect_training_config.py \
  --config-yaml experiments/classification_proto_verbalizer.yaml --no-openprompt-merge
```

Check the report for:

- Selected runner and reason.
- `learning_setting` branch: `full`, `few_shot`, or `zero_shot`.
- CUDA expectations from `environment.num_gpus`, `cuda_visible_devices`, `local_rank`, and `model_parallel`.
- Dataset/template/verbalizer file paths that must exist before training.
- Whether `train.clean` will suppress checkpoint/TensorBoard writes.

## 2. Run a standard classification config

Preflight:

```bash
python scripts/inspect_training_config.py \
  --config-yaml experiments/classification_manual_prompt.yaml --probe-torch
```

If the config requests CUDA but the host only has CPU, either prepare a CUDA PyTorch/model-cache environment or create a CPU inspection/debug config with:

```yaml
environment:
  num_gpus: 0
  cuda_visible_devices:
  local_rank: 0
train:
  clean: True
```

Then run the native CLI only after dataset/model prerequisites are ready:

```bash
python experiments/cli.py --config_yaml experiments/classification_manual_prompt.yaml
```

Standard classification uses:

1. `load_dataset(config)`.
2. `load_plm_from_config(config)`.
3. `load_template(...)` and `load_verbalizer(..., classes=Processor.labels)`.
4. `PromptForClassification(...)`.
5. `ClassificationRunner(...).run()`.

Outputs normally appear under a generated `logs/...` experiment directory containing `log.txt`, `config.yaml`, `tensorboard/`, `checkpoints/last.ckpt`, `checkpoints/best.ckpt`, and split result files unless `train.clean: True`.

## 3. Run a generation config

Preflight:

```bash
python scripts/inspect_training_config.py \
  --config-yaml experiments/generation_manual_template.yaml --probe-torch
```

Before training, verify:

- Dataset examples include `tgt_text`.
- Train dataloader uses `teacher_forcing=True` when learning generation.
- `predict_eos_token=True` is used when the template does not otherwise create a stopping token.
- `dataloader.decoder_max_length` is appropriate for target truncation.
- `generation.max_length` or `max_new_tokens` is appropriate for evaluation; `max_length` includes the input/prompt length.

Run:

```bash
python experiments/cli.py --config_yaml experiments/generation_manual_template.yaml
```

Generation uses `PromptForGeneration(..., gen_config=config.generation)` and `GenerationRunner`. Validation/test writes generated strings and targets, then evaluates metrics such as `sentence_bleu`.

## 4. Few-shot runs

For `learning_setting: few_shot`, `experiments/cli.py` requires `few_shot.few_shot_sampling` and loops through every `sampling_from_train.seed`:

```yaml
learning_setting: few_shot
few_shot:
  parent_config: learning_setting
  few_shot_sampling: sampling_from_train
sampling_from_train:
  parent_config: few_shot_sampling
  num_examples_per_label: 10
  also_sample_dev: True
  num_examples_per_label_dev: 10
  seed: [123, 456]
```

Each seed writes to a child experiment directory such as `seed-123`. If the dev split is too small or labels are missing, fix the dataset/sampler config before blaming the runner.

## 5. Zero-shot evaluation

Use the exact value `zero_shot`:

```yaml
learning_setting: zero_shot
```

The native CLI passes `zero=True` into `trainer()`, constructs the model and dataloaders, and calls `runner.test()` without fitting. This is useful for prompt-only or pretrained evaluation, but it still needs the model cache and test dataset.

Do not use `zero-shot` with a hyphen for the config-driven CLI; that string does not match the branch in `experiments/cli.py`.

## 6. LM-BFF workflow

LM-BFF is selected when either flag is true:

```yaml
classification:
  auto_t: True
  auto_v: False
```

Typical preflight:

```bash
python scripts/inspect_training_config.py \
  --config-yaml experiments/lmbff.yaml --probe-torch
```

Read the report carefully: LM-BFF may load both the classifier PLM (`plm.*`) and template generator PLM (`template_generator.plm.*`). Repository examples request large checkpoints (`roberta-large`, `t5-large`) and multiple GPUs.

Runtime behavior:

1. If `auto_t`, generate candidate templates from the training dataset using the provided manual verbalizer.
2. If `auto_v`, generate candidate label words using the provided template.
3. Train/evaluate candidates with clean temporary `ClassificationRunner` instances.
4. Train/test the best prompt with a final `ClassificationRunner`.

Avoid this workflow in a minimum CPU-only environment unless using tiny cached models and tiny data for logic debugging.

## 7. ProtoVerb workflow

ProtoVerb is selected by:

```yaml
verbalizer: proto_verbalizer
train:
  train_verblizer: post   # native spelling in repo code
```

Preflight:

```bash
python scripts/inspect_training_config.py \
  --config-yaml experiments/classification_proto_verbalizer.yaml --probe-torch
```

Check that the active `proto_verbalizer.file_path` exists and that the config includes expected ProtoVerb settings (`lr`, `mid_dim`, `epochs`, `multi_verb`). The runner calls `verbalizer.train_proto(...)` before, after, or between epochs depending on `train.train_verblizer`.

## 8. Resume or test an existing run

Resume from `last.ckpt`:

```bash
python experiments/cli.py --config_yaml path/to/config.yaml --resume logs/path/to/run
```

Test from `best.ckpt`:

```bash
python experiments/cli.py --config_yaml path/to/config.yaml --test logs/path/to/run
```

Rules:

- `--resume` and `--test` cannot be combined.
- The CLI sets `config.logging.path` to the supplied run path.
- `--resume` falls back to training from scratch if `last.ckpt` is absent.
- `--test` exits on missing `best.ckpt`.
- If checkpoints were suppressed with `train.clean: True`, use in-memory testing in the same run or rerun without clean mode.

## 9. Tutorial-only generation scripts

Use tutorials as evidence or starting points, not as safe defaults:

- `tutorial/2.1_conditional_generation.py`: prefix-tuning WebNLG generation; writes generated sentences after training.
- `tutorial/4.1_all_tasks_are_generation.py`: soft prompt generation objective for SuperGLUE-style classification; manually saves/removes transient checkpoints.
- `tutorial/8_CoT.py`: chain-of-thought style generation over a few CSQA examples; primarily inference/demo.
- `tutorial/9_UltraChat.py`: optional GPT-J/UltraChat workflow using `accelerate`, `torchmetrics`, and `accelerator.save_state()`.

Before running any tutorial, rewrite hard-coded data/model/output paths and confirm backend, model cache, and dependency requirements. These scripts are not no-download smoke tests.
