# Task-Adaptation and Fine-Tuning Workflows

Use this when the user has a pretrained model and a labeled target task, and wants safer fine-tuning or task adaptation. For target unlabeled data or domain-adversarial adaptation, route to [domain-adaptation](../../domain-adaptation/SKILL.md). For datasets, model factories, and transforms, route to [vision-data-models](../../vision-data-models/SKILL.md). For semi-supervised target data, route to [self-training](../../self-training/SKILL.md).

## Common fine-tuning setup

A TLLib-style task-adaptation loop usually has:

1. A pretrained backbone or classifier.
2. A target-task classifier head with target classes.
3. A dataloader for labeled target samples; optionally a source head, source logits, relationship cache, or two-view augmentations depending on the method.
4. A classification loss on the target labels plus one method-specific regularization or distillation term.
5. Parameter groups where pretrained backbone layers often use a smaller learning rate than newly initialized heads.

Distilled training-command shape:

```text
python train_task_adaptation.py <data-root> -d <dataset-name> --pretrained <checkpoint> --finetune \
  --batch-size <n> --epochs <n> --iters-per-epoch <n> --lr <value> --wd <value> \
  --seed <seed> --log <output-dir> --phase train
```

This is a recipe, not a bundled executable. Full runs need datasets, checkpoints, and usually CUDA; the bundled smoke script verifies only small CPU components.

## Method selection quick guide

| User goal or symptom | Method | Use when | Avoid or adjust when |
| --- | --- | --- | --- |
| Simple safe baseline | ERM fine-tuning | Need reference performance | No negative-transfer controls |
| Keep weights near pretrained starting point | L2-SP | Architecture and parameter names match pretrained model | New head has different shape/name |
| Preserve intermediate behavior | DELTA | Feature-map transfer is important | Source and target layers do not align |
| Reduce negative transfer in feature subspace | BSS | Features collapse or overfit with limited labels | `k`/trade-off too high hurts useful directions |
| Transfer source-category relationships | Co-Tuning | Source classifier predicts meaningful source classes for target data | Relationship matrix is noisy or labels are misordered |
| Keep old source behavior while learning target | LwF | Source logits can be collected consistently | Dataset order or saved logits are unstable |
| Try stochastic normalization fine-tuning | StochNorm | CUDA training available and model has BatchNorm | CPU-only training with TLLib 0.4 StochNorm forward |
| Contrastive tuning from pretrained representations | Bi-Tuning | Paired strong/weak augmentations and queue training are acceptable | Memory/augmentation/checkpoint setup is not ready |

## ERM fine-tuning baseline

Before adding regularizers, establish a target-only fine-tuning baseline:

```python
logits, features = classifier(images)  # or y = classifier(images) depending on classifier class
loss = torch.nn.functional.cross_entropy(logits, labels)
```

Operational notes:

- Use `--finetune`-style parameter groups when available: lower LR for pretrained backbone, full LR for bottleneck/head.
- Keep weight decay consistent when comparing methods. DELTA/L2-SP examples may set head and backbone penalties separately.
- Do not tune on held-out test labels.

## L2 and L2-SP

L2 penalizes parameter magnitude; L2-SP penalizes distance from the pretrained starting point.

```python
from tllib.regularization.delta import L2Regularization, SPRegularization

source_model.eval()
regularizer = SPRegularization(source_model, target_model)
loss = target_ce + trade_off * regularizer()
```

Checklist:

- `source_model` and `target_model` must expose the same parameter names for `SPRegularization`.
- Freeze or detach source weights; the implementation stores detached source tensors.
- If the target head has a new number of classes, regularize only matching backbone components or use a separate head regularizer.
- A too-large trade-off causes under-adaptation; a too-small value behaves like ERM.

## DELTA feature-map regularization

DELTA regularizes feature maps from a pretrained source model and a target model.

```python
from tllib.regularization.delta import BehavioralRegularization, IntermediateLayerGetter

source_getter = IntermediateLayerGetter(source_model, return_layers=["layer3", "layer4"])
target_getter = IntermediateLayerGetter(target_model, return_layers=["layer3", "layer4"])
features_source, _ = source_getter(images)
features_target, logits = target_getter(images)
loss_reg = BehavioralRegularization()(features_source, features_target)
loss = target_ce + trade_off_backbone * loss_reg
```

Attention variant:

```python
from tllib.regularization.delta import AttentionBehavioralRegularization

loss_reg = AttentionBehavioralRegularization(channel_attention)(features_source, features_target)
```

Checklist:

- Layer names are string paths resolved by `getattr` traversal; verify each layer exists.
- Source and target feature maps must have identical channel and spatial shapes.
- Source model should be in eval mode for stable reference features.
- Attention weights must match channel counts for each selected feature map.
- Cache attention only after confirming it was computed with the same model, dataset, and layer list.

## BSS

Batch Spectral Shrinkage penalizes small singular values of the feature matrix.

```python
from tllib.regularization.bss import BatchSpectralShrinkage

bss = BatchSpectralShrinkage(k=1)
logits, features = classifier(images)
loss = cross_entropy(logits, labels) + trade_off * bss(features)
```

Checklist:

- Use the penultimate feature matrix, not class logits.
- `features` should be two-dimensional `[batch, feature_dim]`.
- Start with `k=1` and a small trade-off; increase only with validation evidence.
- If loss becomes NaN, inspect feature shape, batch size, and singular values.

## Co-Tuning

Co-Tuning transfers source-label relationships into target fine-tuning.

```python
from tllib.regularization.co_tuning import CoTuningLoss, Relationship, Classifier

relationship = Relationship(target_loader, source_classifier, device, cache="relationship.npy")
criterion = CoTuningLoss()
y_source, y_target = classifier(images)
relationship_target = torch.as_tensor(relationship[target_labels.cpu().numpy()], device=device, dtype=y_source.dtype)
loss = cross_entropy(y_target, target_labels) + trade_off * criterion(y_source, relationship_target)
```

Checklist:

- Relationship rows index target class labels; labels must be contiguous from `0` to `num_target_classes - 1`.
- `relationship_target` shape must match source-head logits `[batch, num_source_classes]`.
- Cache invalidation matters: recompute the relationship if source classifier, target dataset, transforms, or label mapping changes.
- During eval, the Co-Tuning classifier returns only target logits.

## LwF

Learning without Forgetting uses source-model logits as distillation targets while training target classes.

```python
from tllib.regularization.knowledge_distillation import KnowledgeDistillationLoss

kd = KnowledgeDistillationLoss(T=3)
y_source, y_target = classifier(images)
loss = cross_entropy(y_target, target_labels) + trade_off * kd(y_source, saved_source_logits)
```

Checklist:

- Saved source logits must align exactly with the current sample order.
- Use the same preprocessing and model mode when collecting logits and training.
- Temperature `T` smooths source probabilities; common task-adaptation recipes use values above `1`.
- During eval, the LwF classifier returns only target logits.

## StochNorm fine-tuning

StochNorm replaces BatchNorm layers before fine-tuning.

```python
from tllib.normalization.stochnorm import convert_model

classifier = convert_model(classifier, p=0.5)
```

Checklist:

- Convert after constructing/loading the BatchNorm model and before creating optimizer parameter groups.
- Confirm that BatchNorm modules were replaced by StochNorm modules.
- In TLLib 0.4, StochNorm training forward uses CUDA for its stochastic mask. CPU-only users should not select StochNorm training unless they patch the implementation or run on CUDA.
- Use `eval()` for CPU sanity checks, because evaluation uses running statistics and avoids stochastic CUDA mask creation.

## Bi-Tuning

Bi-Tuning uses paired augmentations, query/key encoders, class-wise queues, and contrastive objectives.

```python
from tllib.regularization.bi_tuning import Classifier, BiTuning

encoder_q = Classifier(backbone_q, num_classes, projection_dim=128)
encoder_k = Classifier(backbone_k, num_classes, projection_dim=128)
bituning = BiTuning(encoder_q, encoder_k, num_classes=num_classes, K=40, m=0.999, T=0.07)
y_q, logits_z, logits_y, labels_c = bituning(view_q, view_k, labels)
loss_cls = cross_entropy(y_q, labels)
loss_contrast = kl_or_ce_for_log_probs(logits_z, labels_c) + kl_or_ce_for_log_probs(logits_y, labels_c)
loss = loss_cls + trade_off * loss_contrast
```

Checklist:

- Provide two transformed views per image.
- Keep queue size `K`, temperature `T`, and momentum `m` stable in checkpoints/logs.
- If loading MoCo-style pretraining, first convert checkpoint keys as described in [checkpoint conversion](checkpoint-conversion.md).
- Ensure the classifier head and projector dimensions match the target classes and contrastive setup.

## Negative transfer triage

When fine-tuning performs worse than a from-scratch or ERM baseline:

1. Confirm dataset labels, transforms, and model head size through [vision-data-models](../../vision-data-models/SKILL.md).
2. Compare ERM fine-tuning with and without a lower backbone LR.
3. If the pretrained weights are close but overfitting occurs, try L2-SP or DELTA.
4. If feature collapse or low-rank features appear, try BSS with small `k` and trade-off.
5. If source categories are semantically related to target classes, try Co-Tuning.
6. If source behavior must be preserved, try LwF.
7. If the pretrained checkpoint is MoCo-style, verify conversion before blaming the regularizer.
