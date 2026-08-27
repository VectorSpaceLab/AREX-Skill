# TLLib Self-Training API Reference

This reference summarizes the runtime APIs used by TLLib semi-supervised and self-training workflows. All tensor examples assume PyTorch tensors on the same device. `N` is batch size and `C` is number of classes.

## Import map

```python
from tllib.self_training.pseudo_label import ConfidenceBasedSelfTrainingLoss
from tllib.self_training.pi_model import ConsistencyLoss, L2ConsistencyLoss, sigmoid_warm_up
from tllib.self_training.mean_teacher import EMATeacher, update_bn
from tllib.self_training.uda import StrongWeakConsistencyLoss
from tllib.self_training.mcc import MinimumClassConfusionLoss
from tllib.self_training.self_ensemble import ClassBalanceLoss
from tllib.self_training.flexmatch import DynamicThresholdingModule
from tllib.self_training.self_tuning import Classifier as SelfTuningClassifier, SelfTuning
from tllib.self_training.dst import ImageClassifier as DSTImageClassifier, WorstCaseEstimationLoss
from tllib.self_training.cc_loss import CCConsistency
```

Model backbones, transforms, datasets, and loaders are covered by [vision-data-models](../../vision-data-models/SKILL.md). Fine-tuning choices after checkpoint conversion are covered by [task-generalization](../../task-generalization/SKILL.md). Domain-adaptation use of MCC belongs in [domain-adaptation](../../domain-adaptation/SKILL.md).

## Confidence-based pseudo labels

### `ConfidenceBasedSelfTrainingLoss(threshold: float)`

Use this for Pseudo Label and FixMatch-style hard pseudo-label training.

**Inputs**

- `y`: unnormalized logits to train, shape `(N, C)`.
- `y_target`: unnormalized logits used to generate pseudo labels, shape `(N, C)`. The module detaches `y_target` internally.

**Returns**

- `self_training_loss`: scalar cross-entropy averaged over the full batch after multiplying each sample by a confidence mask.
- `mask`: float tensor of shape `(N,)`; `1` means `max(softmax(y_target)) > threshold`.
- `pseudo_labels`: long tensor of shape `(N,)` from `argmax(softmax(y_target))`.

**Important behavior**

- Pass logits, not probabilities. The module applies `softmax` to `y_target` and `cross_entropy` to `y`.
- The mask comparison is strict (`>`), so confidence exactly equal to the threshold is not selected.
- If no sample passes the threshold, the loss is zero-like because all per-sample terms are multiplied by zero. Training should log mask ratio to detect this.

```python
criterion = ConfidenceBasedSelfTrainingLoss(threshold=0.95)
loss_u, mask, pseudo = criterion(logits_strong, logits_weak)
loss = labeled_ce + lambda_u * loss_u
```

## Pi Model consistency

### `ConsistencyLoss(distance_measure: Callable, reduction='mean')`

Generic per-sample consistency loss. `distance_measure(p1, p2)` must return one value per sample, normally shape `(N,)`. `mask` can be a scalar or a tensor broadcastable to that shape.

```python
def kl_per_sample(p1, p2):
    return torch.nn.functional.kl_div(p1.log(), p2, reduction='none').sum(dim=1)
loss = ConsistencyLoss(kl_per_sample)(prob_aug1, prob_aug2, mask)
```

### `L2ConsistencyLoss(reduction='mean')`

Ready-to-use consistency loss with per-sample squared L2 distance:

```python
criterion = L2ConsistencyLoss()
loss = criterion(prob_view1, prob_view2, mask=torch.ones(prob_view1.size(0)))
```

**Shape rules**

- `p1`, `p2`: same shape `(N, C)`; these are usually probabilities or normalized predictions, not raw class indices.
- `mask`: scalar, `(N,)`, or broadcastable. If you use `(N, 1)`, verify reduction semantics because the internal per-sample loss is `(N,)`.

### `sigmoid_warm_up(current_epoch, warm_up_epochs)`

Returns a scalar ramp-up coefficient between 0 and 1. Use it to gradually enable a consistency weight, e.g. `lambda_t = lambda_max * sigmoid_warm_up(epoch, 10)`.

## Mean Teacher

### `EMATeacher(model, alpha)`

Wraps a student model with an exponential-moving-average teacher. The teacher is a deep copy of the student and its parameters do not require gradients.

**Methods**

- `teacher(x)`: forward through the EMA teacher.
- `teacher.update()`: update teacher parameters with `teacher = alpha * teacher + (1 - alpha) * student`.
- `teacher.set_alpha(alpha)`: change EMA decay; `alpha` must be non-negative.
- `teacher.train(mode=True)` / `teacher.eval()`: set teacher mode.
- `teacher.state_dict()` / `teacher.load_state_dict(...)`: checkpoint the EMA teacher.
- `update_bn(student, teacher_model)`: copy BatchNorm running statistics from student to teacher model when needed.

**Recommended order in one training step**

1. Forward student and teacher; compute supervised and consistency losses.
2. Backpropagate through the student only.
3. `optimizer.step()` updates student weights.
4. `teacher.update()` moves the EMA teacher toward the new student weights.
5. Optionally call `update_bn(student, teacher.teacher)` if you intentionally sync BatchNorm statistics.

Calling `teacher.update()` before the optimizer step makes the teacher track stale weights.

## UDA weak/strong consistency

### `StrongWeakConsistencyLoss(threshold: float, temperature: float)`

Use for UDA-style consistency where weakly augmented predictions provide soft targets and strongly augmented predictions are trained.

**Inputs**

- `y_strong`: logits on strongly augmented unlabeled samples, shape `(N, C)`.
- `y`: logits on weakly augmented unlabeled samples, shape `(N, C)`.

**Behavior**

- Confidence mask is derived from `softmax(y.detach())`.
- The strong branch is trained with KL divergence from `log_softmax(y_strong / temperature)` to `softmax(y.detach())`.
- The masked loss is normalized by `mask.sum()` with a lower bound of 1, so an empty mask produces a finite zero-like term.

## MCC and class-confusion consistency

### `MinimumClassConfusionLoss(temperature: float)`

Takes logits `(N, C)` and returns a scalar class-confusion penalty. Temperature must be greater than 0. MCC is often used in domain adaptation; route DA-specific target-domain MCC wiring to [domain-adaptation](../../domain-adaptation/SKILL.md). In SSL, use it only as a regularizer on the relevant unlabeled/target prediction batch and keep its trade-off explicit.

### `CCConsistency(temperature: float, thr=0.7)`

Computes a class-confusion consistency term between weak and strong logits. Inputs are `logits` and `logits_strong`, both `(N, C)`. The weak branch is detached and thresholded. If no samples pass the threshold, the implementation returns `(0, 0)` rather than two tensor scalars, so training code should normalize that case before combining with tensor losses.

## Class-balance regularization

### `ClassBalanceLoss(num_classes)`

Penalizes batch-level predicted class imbalance. It expects probabilities `p` of shape `(N, C)`, not logits.

```python
p = torch.softmax(logits_u, dim=1)
loss_balance = ClassBalanceLoss(num_classes=C)(p)
```

If you pass logits directly, `binary_cross_entropy` can fail or produce meaningless values because inputs must be probability-like values in `[0, 1]`.

## FlexMatch dynamic thresholding

### `DynamicThresholdingModule(threshold, warmup, mapping_func, num_classes, n_unlabeled_samples, device)`

Maintains per-unlabeled-sample pseudo-label history and returns class-dependent thresholds.

**State and calls**

- `net_outputs`: length `n_unlabeled_samples`, initialized to `-1`.
- `get_threshold(pseudo_labels)`: returns a threshold tensor matching `pseudo_labels` shape.
- `update(idxes, selected_mask, pseudo_labels)`: updates history for selected samples only.

**Required inputs**

- `idxes`: stable integer indices into the unlabeled dataset. A FlexMatch loader must return these indices; otherwise the threshold history cannot be updated correctly.
- `selected_mask`: binary mask from the fixed base threshold, not the dynamic threshold, when following the TLLib workflow.
- `mapping_func`: increasing function over a tensor, e.g. `lambda x: x / (2 - x)` for a convex mapping.

**Common training pattern**

```python
with torch.no_grad():
    logits_weak = model(x_u_weak)
confidence, pseudo = torch.softmax(logits_weak, dim=1).max(dim=1)
dynamic_threshold = thresholding.get_threshold(pseudo)
mask = (confidence > dynamic_threshold).float()
selected_mask = (confidence > base_threshold).long()
thresholding.update(unlabeled_indices, selected_mask, pseudo)
loss_u = (F.cross_entropy(logits_strong, pseudo, reduction='none') * mask).mean()
```

## Self-Tuning

### `SelfTuningClassifier(backbone, num_classes, projection_dim=1024, bottleneck_dim=1024, finetune=True, pool_layer=None)`

Classifier with a projection head. In training mode it returns `(h, y)` where `h` is normalized projection `(N, projection_dim)` and `y` is logits `(N, C)`. In eval mode it returns logits only.

The `backbone` must expose `out_features`. For shared backbone/model factory details, use [vision-data-models](../../vision-data-models/SKILL.md).

### `SelfTuning(encoder_q, encoder_k, num_classes, K=32, m=0.999, T=0.07)`

Momentum contrastive self-tuning module. It owns a per-class queue of size `K` and updates the key encoder internally during forward.

**Forward**

```python
pgc_logits, pgc_labels, y_q = module(im_q, im_k, labels)
```

- `im_q`, `im_k`: paired augmented views.
- `labels`: class labels for the labeled/minibatch samples, shape `(N,)`.
- `pgc_logits`: log-softmax contrastive logits.
- `pgc_labels`: soft labels for positive queue entries.
- `y_q`: classifier logits from the query encoder.

Use a batch/queue configuration that keeps per-class queue updates meaningful; very small queues can make the contrastive part noisy.

## Debiased Self-Training (DST)

### `DSTImageClassifier(backbone, num_classes, bottleneck_dim=1024, width=2048, **kwargs)`

Classifier with three heads:

- Main head `h` for normal predictions.
- Pseudo head `h_pseudo` for pseudo-label supervision.
- Worst-case head `h_worst` connected through a warm-start gradient reverse layer.

In training mode, forward returns `(outputs, outputs_adv, outputs_pseudo)`. In eval mode, forward returns only `outputs`. Call `classifier.step()` each training iteration to advance the GRL schedule.

### `WorstCaseEstimationLoss(eta_prime)`

Inputs are all logits with shape `(N, C)`:

```python
loss_wce = WorstCaseEstimationLoss(eta_prime)(y_l, y_l_adv, y_u, y_u_adv)
```

- `y_l`: main-head logits on labeled samples.
- `y_l_adv`: worst-case-head logits on labeled samples.
- `y_u`: main-head logits on unlabeled samples.
- `y_u_adv`: worst-case-head logits on unlabeled samples.

The loss derives labels from `argmax(y_l)` and `argmax(y_u)`, so input shape and class order must match across main and adversarial heads.

## Noisy Student pattern

TLLib's Noisy Student workflow uses the generic classifier/model stack plus a pretrained teacher checkpoint rather than a dedicated `tllib.self_training` class. The reusable API pattern is:

1. Load a teacher model/checkpoint and run it in eval mode.
2. Generate soft or hard pseudo labels for unlabeled examples.
3. Train a student with stronger augmentation/noise and explicit supervised + pseudo-label trade-offs.
4. Optionally promote the student to teacher for another round.

Checkpoint selection and fine-tuning details cross over with [task-generalization](../../task-generalization/SKILL.md).
