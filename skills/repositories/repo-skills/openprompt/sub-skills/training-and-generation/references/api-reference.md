# API Reference: Training and Generation

This reference covers OpenPrompt runners, safe runner selection, runtime device placement, checkpoint/logging behavior, and generation/few-shot/zero-shot caveats. It assumes dataset processors, templates, verbalizers, and prompt asset formats have already been selected.

## Core imports

```python
from openprompt.trainer import ClassificationRunner, GenerationRunner
from openprompt.lm_bff_trainer import LMBFFClassificationRunner
from openprompt.protoverb_trainer import ProtoVerbClassificationRunner
from openprompt.utils.cuda import model_to_device
from openprompt.pipeline_base import PromptForClassification, PromptForGeneration
```

Top-level `openprompt` also exports `ClassificationRunner`, `GenerationRunner`, `LMBFFClassificationRunner`, and `ProtoVerbClassificationRunner`.

## Runner selection contract

`experiments/cli.py::trainer()` is the canonical config-driven selection point.

| Config condition | Runner | Notes |
| --- | --- | --- |
| `task: classification` and `classification.auto_t: true` or `classification.auto_v: true` | `LMBFFClassificationRunner` | Loads a PLM internally, generates/searches templates or label words, trains candidate classifiers, then trains/tests the best prompt. |
| `task: classification` and `verbalizer: proto_verbalizer` | `ProtoVerbClassificationRunner` | Runs prototypical verbalizer training according to `train.train_verblizer` (repository spelling). |
| `task: classification` otherwise | `ClassificationRunner` | Standard prompt classification with configured template/verbalizer and metrics. |
| `task: generation` | `GenerationRunner` | Standard prompt generation training/evaluation with `PromptForGeneration` and `config.generation`. |

Unsupported `task` values raise `NotImplementedError` in the native CLI.

## `BaseRunner` lifecycle

`ClassificationRunner`, `GenerationRunner`, and `ProtoVerbClassificationRunner` inherit most behavior from `BaseRunner`.

Constructor side effects:

1. Stores model, config, and train/dev/test dataloaders.
2. Calls `wrap_model()`, which delegates to `model_to_device(model, config.environment)`.
3. Creates a TensorBoard writer at `config.logging.path/tensorboard`.
4. Ensures `config.logging.path/checkpoints` exists.
5. Copies `config.train.clean` into `runner.clean`.

Training/test methods:

```python
runner.fit(ckpt=None)       # train, validate each epoch, save last/best unless clean
runner.test(ckpt=None)      # optionally load checkpoint, run test split
runner.run(ckpt=None)       # fit, then test best checkpoint unless clean
```

Stop criterion:

- If `train.num_training_steps` is set, it overrides `train.num_epochs`; `num_epochs` is internally set to a large sentinel.
- Otherwise `train.num_epochs` must be set.
- `steps_per_epoch = len(train_dataloader) // train.gradient_accumulation_steps`.

Optimizer groups:

- PLM optimizer is added unless `plm.optimize.freeze_para` is true.
- Template optimizer is added when the active template config has `optimize`; templates with a custom `.optimize()` method are wrapped as a dummy optimizer.
- Verbalizer optimizer is added when the active verbalizer config has `optimize` and the model has a verbalizer.
- Schedulers are linear warmup schedulers where configured. T5-style tutorial code may use `Adafactor`, but the config runner only implements the optimizer branches present in `trainer.py`.

## Device placement with `model_to_device`

`model_to_device(model, config.environment)` implements this order:

1. If `CUDA_VISIBLE_DEVICES` is absent and `environment.cuda_visible_devices` is not `None`, set the environment variable from that list.
2. If `environment.model_parallel` is true, call `model.parallelize()` or `model.parallelize(environment.device_map)`. The model must expose `.parallelize()`.
3. Else if `environment.num_gpus > 1`, move to `cuda:{local_rank}` and wrap `torch.nn.DataParallel(output_device=local_rank_device)`.
4. Else if `environment.num_gpus > 0`, call `model.cuda()`.
5. Else leave the model on CPU.

Important caveats:

- No automatic CPU fallback exists for `num_gpus > 0`; CUDA must be available and compatible.
- `local_rank` should be valid for the visible devices.
- DataParallel and model parallel are mutually exclusive in this helper.
- If `CUDA_VISIBLE_DEVICES` is already set externally, the config value is not used to overwrite it.

## Checkpoints and logging

`BaseRunner.checkpoint_path(ckpt)` resolves to:

```text
{config.logging.path}/checkpoints/{ckpt}.ckpt
```

During `fit()`:

- Every epoch saves `last.ckpt` with model state, optimizer/scheduler state, `cur_epoch`, `best_score`, `global_step`, and `validation_metric` unless `train.clean: True`.
- When validation improves according to `checkpoint.higher_better`, `last.ckpt` is copied to `best.ckpt`.
- `runner.run()` tests `best.ckpt` when `clean` is false; in clean mode it tests the in-memory model without reloading `best`.

Declared config flags `checkpoint.save_latest` and `checkpoint.save_best` exist in `default_config.py`, but `BaseRunner.save_checkpoint()` does not consult them. Use `train.clean: True` to suppress TensorBoard and checkpoint writes.

Resume/test entry points in `experiments/cli.py`:

```bash
python experiments/cli.py --config_yaml experiments/classification_manual_prompt.yaml --resume logs/run_dir
python experiments/cli.py --config_yaml experiments/classification_manual_prompt.yaml --test logs/run_dir
```

`--resume` loads `last.ckpt`; `--test` loads `best.ckpt`. They cannot be used together.

## `ClassificationRunner`

Constructor:

```python
ClassificationRunner(
    model: PromptForClassification,
    config,
    train_dataloader=None,
    valid_dataloader=None,
    test_dataloader=None,
    loss_function=None,
    id2label=None,
)
```

Behavior:

- Uses `classification.loss_function`: `cross_entropy` or `nll_loss`.
- `training_step()` computes logits from `PromptForClassification` and loss against `batch['label']`.
- `inference_step()` returns argmax predictions and labels.
- `inference_epoch_end()` saves `{split}_preds.txt` and `{split}_labels.txt`, then computes every metric in `classification.metric` with `classification_metrics`.
- `on_fit_start()` calls `prompt_initialize()` if the template or verbalizer exposes `optimize_to_initialize()`.

## `GenerationRunner`

Constructor:

```python
GenerationRunner(
    model: PromptForGeneration,
    config,
    train_dataloader=None,
    valid_dataloader=None,
    test_dataloader=None,
)
```

Behavior:

- `training_step()` calls `PromptForGeneration(batch)` and expects it to return a generation loss.
- `inference_step()` calls `PromptForGeneration.generate(batch, **config.generation)` and compares generated strings with `batch['tgt_text']`.
- `inference_epoch_end()` saves `{split}_preds.txt` and `{split}_targets.txt`, then computes every metric in `generation.metric` with `generation_metric`.

Generation config keys from `default_config.py` include `max_length`, `max_new_tokens`, `min_length`, `temperature`, `do_sample`, `top_k`, `top_p`, `repetition_penalty`, `num_beams`, and `bad_words_ids`. In OpenPrompt's tutorial guidance, `generation.max_length` includes input/prompt tokens, so keep it larger than the dataloader input length when using native generation.

`PromptForGeneration.generate()` handles encoder-decoder and decoder-only PLMs differently. For decoder-only PLMs it generates instances one by one because the compatible transformers generation path expects left padding or a single sample.

## `LMBFFClassificationRunner`

Constructor:

```python
LMBFFClassificationRunner(
    train_dataset,
    valid_dataset,
    test_dataset,
    verbalizer=None,
    template=None,
    config=None,
)
```

Behavior:

- Loads the PLM/tokenizer/wrapper internally using `load_plm_from_config(config)`.
- `classification.auto_t` requires an input verbalizer and ignores a provided template.
- `classification.auto_v` requires an input template and ignores a provided verbalizer.
- `_auto_t()` loads `config.template_generator`, creates a template generator, and returns candidate template texts.
- `_auto_v(template)` deep-copies the PLM, registers train-set buffers with the verbalizer generator, and returns candidate label-word lists.
- Candidate evaluation trains a temporary `ClassificationRunner` with `runner.clean = True`.
- Final training uses a standard `ClassificationRunner` with `runner.clean = False`.

LM-BFF configs often require large cached models such as `roberta-large` and `t5-large`, and may request multiple GPUs. Treat these as optional heavy workflows unless the environment proves CUDA/model-cache readiness.

## `ProtoVerbClassificationRunner`

Constructor and inference/training behavior are classification-like, but `on_fit_start()` and `fit()` drive prototypical verbalizer training.

`train.train_verblizer` (native misspelling) controls timing:

- Any value other than `post`: train prototypes before fitting.
- `alternate`: retrain prototypes after each epoch.
- `post`: train prototypes after the main fit loop.

The configured `proto_verbalizer` node carries ProtoVerb-specific settings such as `lr`, `mid_dim`, `epochs`, `multi_verb`, `file_path`, and `choice` in the repository examples.

## Few-shot and zero-shot in `experiments/cli.py`

- `learning_setting: full`: call `trainer()` once with full train/dev/test datasets.
- `learning_setting: few_shot`: require `few_shot.few_shot_sampling`; loop over `sampling_from_train.seed`, sample train/dev splits with `FewShotSampler`, run a per-seed subdirectory, and average results.
- `learning_setting: zero_shot`: call `trainer(..., zero=True)` and run `runner.test()` without `fit()`.

The code checks the string `zero_shot` with an underscore. A hyphenated value such as `zero-shot` does not match this branch.

## Tutorial-only generation variants

- `tutorial/2.1_conditional_generation.py` demonstrates prefix tuning for WebNLG and explicitly uses `teacher_forcing=True` and `predict_eos_token=True` for train dataloaders.
- `tutorial/4.1_all_tasks_are_generation.py` uses `GenerationVerbalizer` to turn classification labels or metadata fields into `tgt_text`, trains soft prompts, and stores a transient best checkpoint manually.
- `tutorial/8_CoT.py` uses a few-shot reasoning prompt plus `PromptForGeneration.generate()` for chain-of-thought style inference.
- `tutorial/9_UltraChat.py` is an optional `accelerate`/`torchmetrics` large-model workflow that manages checkpointing with `accelerator.save_state()` rather than `BaseRunner`.
