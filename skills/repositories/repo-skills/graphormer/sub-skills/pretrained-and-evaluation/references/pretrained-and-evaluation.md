# Pretrained And Evaluation Reference

This sub-skill covers three related workflows:

1. loading an official pretrained checkpoint,
2. fine-tuning the MolHIV FLAG recipe,
3. evaluating either a pretrained model or a directory of saved checkpoints.

It is intentionally narrow: it does not explain base Graphormer training, custom dataset registration, or model architecture changes.

## Pretrained model names

Graphormer ships a small checkpoint registry in `graphormer.pretrain`.
The loader resolves a name to a URL, downloads the checkpoint through `torch.hub.load_state_dict_from_url`, and returns the saved `model` state.
If distributed training is already initialized, each rank downloads with a rank-specific cache file name and then synchronizes.

| Name | Purpose | Typical use | Status |
| --- | --- | --- | --- |
| `pcqm4mv1_graphormer_base` | Base checkpoint trained on PCQM4M v1 | Pretrained evaluation or transfer to another graph task | Available |
| `pcqm4mv2_graphormer_base` | Base checkpoint trained on PCQM4M v2 | Pretrained evaluation or transfer to another graph task | Available |
| `pcqm4mv1_graphormer_base_for_molhiv` | PCQM4M v1 checkpoint adapted for MolHIV fine-tuning | FLAG fine-tuning on `ogbg-molhiv` | Available |
| `oc20is2re_graphormer3d_base` | Graphormer3D IS2RE checkpoint | 3D OC20 orientation only | Source marks the URL temporarily unavailable |

If a pretrained name is unknown, the loader raises an error immediately.

## Loading semantics

### `--pretrained-model-name`

This flag selects the checkpoint name.
The model is loaded before task-specific inference or fine-tuning begins.

### `--load-pretrained-model-output-layer`

This flag controls whether the final output layer from the checkpoint is kept.

- When the flag is set, the checkpoint output head is loaded as-is.
- When the flag is omitted, Graphormer loads the checkpoint and then resets the output layer parameters.

Use the flag when you want the pretrained head to stay aligned with the source task.
Omit it when the target task needs a fresh prediction head.

## Evaluate a pretrained checkpoint

The official evaluation script builds a Graphormer model, loads the pretrained state, moves the model and samples to CUDA, and then evaluates one split.
Its behavior depends on `--pretrained-model-name`:

- `pcqm4mv1_graphormer_base` uses the PCQM4M v1 evaluator.
- `pcqm4mv2_graphormer_base` uses the PCQM4M v2 evaluator.
- Other names do not have a dedicated pretrained-evaluation branch in the script.

The script also strict-loads the state dict into the constructed model.
That means architecture flags, hidden sizes, and output-head shape must line up with the checkpoint.

Recommended command pattern:

```bash
python scripts/build_graphormer_eval_or_finetune_command.py \
  --mode evaluate-pretrained \
  --user-dir graphormer \
  --pretrained-model-name pcqm4mv1_graphormer_base \
  --load-output-layer \
  --split valid
```

## Evaluate saved checkpoints

When `--pretrained-model-name` is not used, `graphormer/evaluate/evaluate.py` iterates over every entry in `--save-dir` and evaluates each checkpoint file it finds.
The script does not sort or filter the directory contents, so keep the directory clean and checkpoint-only.

For checkpoint evaluation, the script accepts the metric choice directly:

- `auc` for classification-style outputs,
- `mae` for regression-style outputs.

The rendered command should match the task type and data split:

- use `auc` for MolHIV-style classification runs,
- use `mae` for regression tasks.

Recommended command pattern:

```bash
python scripts/build_graphormer_eval_or_finetune_command.py \
  --mode evaluate-checkpoints \
  --user-dir graphormer \
  --save-dir ckpts \
  --split test \
  --metric auc
```

## MolHIV FLAG fine-tuning

The maintained MolHIV recipe uses the FLAG variant of graph prediction:

- task: `graph_prediction_with_flag`
- criterion: `binary_logloss_with_flag`
- architecture: `graphormer_base`
- pretrained checkpoint: `pcqm4mv1_graphormer_base_for_molhiv`
- optimizer: Adam
- scheduler: polynomial decay
- precision: FP16
- evaluation metric after training: AUC

Core knobs from the source recipe:

| Knob | Source value | Notes |
| --- | --- | --- |
| `--dataset-name` | `ogbg-molhiv` | OGB binary classification dataset |
| `--dataset-source` | `ogb` | OGB loader path |
| `--num-classes` | `1` | Binary prediction head |
| `--attention-dropout` | `0.1` | FLAG recipe value |
| `--act-dropout` | `0.1` | FLAG recipe value |
| `--dropout` | `0.0` | FLAG recipe value |
| `--lr` | `2e-4` | Fine-tuning learning rate |
| `--end-learning-rate` | `1e-5` | Source recipe value |
| `--batch-size` | `128` | Source recipe value |
| `--encoder-layers` | `12` | Base Graphormer depth |
| `--encoder-embed-dim` | `768` | Base Graphormer width |
| `--encoder-ffn-embed-dim` | `768` | Base Graphormer width |
| `--encoder-attention-heads` | `32` | Base Graphormer head count |
| `--flag-m` | `3` | FLAG perturbation count |
| `--flag-step-size` | `0.01` | FLAG step size |
| `--flag-mag` | `0` | FLAG magnitude from the example script |
| `--pre-layernorm` | set | Required by the maintained fine-tune script |

The checkpoint output-layer choice matters here too:
use a fresh head for the downstream task unless you intentionally want the pretrained head preserved.

Recommended command pattern:

```bash
python scripts/build_graphormer_eval_or_finetune_command.py \
  --mode finetune-molhiv \
  --user-dir graphormer \
  --save-dir ckpts \
  --pretrained-model-name pcqm4mv1_graphormer_base_for_molhiv
```

## Practical rules

- Use `--split valid` for pretrained validation-style checks and `--split test` for final checkpoint evaluation when the downstream protocol expects it.
- Keep the save directory checkpoint-only when using checkpoint iteration.
- Prefer the official pretrained names exactly as written; the loader does not guess aliases.
- Treat `oc20is2re_graphormer3d_base` as reference-only unless the source URL becomes available again.
- If a shape mismatch appears, the most common cause is a missing or incorrect output-layer choice.
