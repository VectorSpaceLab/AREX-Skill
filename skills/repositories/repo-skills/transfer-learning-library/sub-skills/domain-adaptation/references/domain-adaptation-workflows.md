# Domain Adaptation Workflows

This file turns the public APIs into workflow decisions. The benchmark scripts in the repository are reference-only; the goal here is to explain which family to use, what knobs matter, and which questions belong to sibling skills.

## 1. Pick the setting first

| Setting | Typical families | What the user usually needs |
| --- | --- | --- |
| Closed-set image classification | DANN, CDAN, ADDA, DAN, JAN, CORAL, BSP, MCD, MDD | A source/target pair, a backbone, and the correct loss wiring. |
| Partial domain adaptation | PADA, IWAN, AFN | Reweighting logic that suppresses source-only classes. |
| Open-set domain adaptation | OSBP | An unknown-class slot and an explicit confidence boundary. |
| Regression domain adaptation | DD / MDD-regression / RSD | Normalized labels and a regressor wrapper. |
| Keypoint adaptation | RegDA | Heatmap-based pseudo labels and adversarial regression heads. |
| Object detection adaptation | D-adapt | Detectron2, proposal feedback, and optional translated datasets. |
| WILDS domain adaptation | DANN, DAN, JAN, CDAN, MDD, FixMatch | A modality-specific benchmark recipe with optional AMP/DDP stacks. |

## 2. Closed-set image-classification workflows

Use this branch when source and target share the same label space.

### Common CLI shape

The benchmark launchers in this family usually expose:

- one dataset root positional argument,
- `-d/--data` for the dataset name,
- `-s/--source` and `-t/--target` for the domain labels,
- `-a/--arch` for the backbone,
- batch size, learning rate, weight decay, epoch count, and logging flags,
- `--phase` for train/test/analysis-style operation.

### Method-specific choices

| Method | When to choose it | Important flags or expectations |
| --- | --- | --- |
| DANN | You want the simplest adversarial alignment baseline. | `--trade-off` controls the adversarial term. The discriminator works on 2-D feature tensors. |
| CDAN | You want conditioning on class predictions as well as features. | `--randomized`, `--randomized-dim`, and `--entropy` are the key switches. Pass logits and features, not labels. |
| ADDA | You want the two-stage source-pretrain / target-adapt pattern. | `--pretrain`, `--pretrain-epochs`, and a separate adversarial loss stage. |
| DAN | You want kernel matching on feature distributions. | `--non-linear` toggles the feature alignment style; the loss is MK-MMD. |
| JAN | You want joint multi-layer alignment. | `--linear` and `--adversarial` change the map family. Use tuples of layer activations. |
| CORAL | You want a covariance-matching baseline with minimal machinery. | Usually the simplest choice when the feature space is already strong. |
| BSP | You want to penalize dominant singular directions. | `--trade-off-bsp` scales the extra penalty. The workflow often uses a source-only pretrain stage. |
| MCD | You want a two-head discrepancy loop. | `--trade-off`, `--trade-off-entropy`, and `--num-k` matter. Use class probabilities for discrepancy. |
| MDD | You want a margin-disparity objective and a classifier with a main and adversarial head. | `--margin` is the main knob. Remember to call `step()` after each training forward. |

### AFN and MCC in DA workflows

- **AFN** is used in the partial-DA and closed-set DA recipes when the task needs feature-norm growth. Its workflow knobs are `--num-blocks`, `--bottleneck-dim`, `--delta`, `--trade-off-norm`, and sometimes `--trade-off-entropy`.
- **MCC** is used as a target-side regularizer when the DA loop benefits from less class confusion. Its key knob is `--temperature`.

If the user only wants the standalone AFN or MCC module mechanics, route that part to the owning sibling skill and keep this branch focused on the DA recipe.

## 3. Partial domain adaptation workflows

Use this branch when the target label set is a subset of the source label set.

### The main actors

- **PADA**: class weights from classifier outputs.
- **IWAN**: instance weights from a discriminator.
- **AFN**: often used as a source/target regularizer in the same family of benchmark scripts.

### Workflow shape

1. Train a source model or source-aware baseline on source and target loaders.
2. Estimate which source classes matter for the target side.
3. Apply class or instance weights when computing the final loss.
4. Keep the `partial_classes_index` debugging hooks out of real user guidance; they are only for inspection.

### Practical flags

- PADA uses a class-weight refresh interval plus a temperature.
- IWAN uses a gamma-like score and a higher-level trade-off for the weighting term.
- The examples usually take a single source and a single target domain.

## 4. Open-set domain adaptation workflows

Use this branch when the target contains unknown classes.

### Main decision

- **OSBP** is the canonical open-set path.
- DANN can be used as a baseline, but it does not model the unknown class explicitly.

### What to watch

- The classifier needs an explicit unknown-class output slot.
- The threshold controls the boundary between known and unknown predictions.
- HOS / OS / UNK-style reporting is common in the benchmark notes.

### Good guidance to give users

- Do not treat open-set target accuracy like a closed-set task.
- Use the unknown-class loss and a threshold-based evaluation metric.
- Be explicit that DANN is a baseline, not an open-set solution.

## 5. Regression domain adaptation workflows

Use this branch when the output is continuous rather than categorical.

### Typical tasks

- dSprites and MPI3D-style regression DA.
- Any task where the label is a scalar or factor vector rather than a class index.

### Workflow rules

- Normalize labels to `[0, 1]` when the benchmark recipe expects it.
- Keep source and target regression shapes aligned.
- Use `Regressor` or the MDD regression wrapper when the recipe needs a structured adversarial head.

### Common knobs

- normalization mode (`BN` or `IN` in the benchmark scripts),
- margin-like settings for DD/MDD regression,
- learning-rate schedule and batch size.

## 6. Keypoint adaptation workflows

Use this branch for RegDA-style heatmap regression tasks.

### Core sequence

1. Load source and target roots.
2. Build a pose backbone and upsampling path.
3. Construct a main heatmap head and an adversarial heatmap head.
4. Generate pseudo heatmaps from the current prediction.
5. Apply regression disparity in min/max modes for source and target updates.
6. Call `step()` after each training forward.

### Important knobs

- `--resize-scale`
- `--rotation`
- `--image-size`
- `--heatmap-size`
- `--num-head-layers`
- `--margin`
- `--debug` for visual inspection

### What not to forget

- Heatmaps must stay in `(B, K, H, W)` form.
- The criterion should match heatmap regression, not classification.
- If the user asks about the underlying dataset or model family, route that part to `../vision-data-models/SKILL.md`.

## 7. WILDS workflows

Use this branch when the task is a WILDS benchmark adaptation recipe rather than a small tensor smoke.

### Image-classification WILDS

This family covers fmow, iwildcam, camelyon17, and similar image tasks.

Common flags include:

- `data_dir`
- `-d/--data`
- `--unlabeled-list`
- `--test-list`
- `--metric`
- `--img-size`
- `--arch`
- `--no-pool`
- `--scratch`
- `--smoothing`
- `--bottleneck-dim`
- `--trade-off`
- `--lr`, `--momentum`, `--weight-decay`, `--min-lr`
- `--epochs`, `--batch-size`, `--deterministic`, `--seed`
- `--sync-bn`, `--opt-level`, `--keep-batchnorm-fp32`, `--loss-scale`, `--channels-last`
- `--phase`

### Text, poverty regression, and molecule workflows

These are optional-stack recipes and should stay reference-only unless the user explicitly has the dependencies.

- **Text**: CivilComments / Amazon, with token-length and group-by-field flags.
- **Poverty regression**: official split scheme, fold selection, and multi-spectral backbones.
- **Molecule classification**: OGB-MolPCBA and graph-network extras such as sparse graph dependencies.

### How to describe them safely

- Reuse the same DA loss family names when the modality is still classification/regression adaptation.
- Mention `apex` / AMP / distributed training only as optional benchmark infrastructure.
- Do not promise that the CPU smoke helper reproduces these benchmark settings.

## 8. Quick routing reminders

- If the user is asking about dataset layout, transforms, or model factories, route to `../vision-data-models/SKILL.md`.
- If the user is asking about translation or style transfer as the adaptation mechanism, route to `../translation/SKILL.md`.
- If the user is actually asking for pseudo-labeling or teacher/student logic, route to `../self-training/SKILL.md`.
- If the user is asking about a fine-tuning or DG regularizer, route to `../task-generalization/SKILL.md`.
- If the request involves object detection, use `object-detection-adaptation.md` and keep Detectron2 / CUDA as an optional stack.
