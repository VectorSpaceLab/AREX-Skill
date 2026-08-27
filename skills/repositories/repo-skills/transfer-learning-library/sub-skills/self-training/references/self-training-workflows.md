# Self-Training Workflows

This guide turns TLLib self-training APIs into reusable operating patterns. It intentionally avoids benchmark trainer execution: full training requires external datasets, checkpoints, augmentations, logs, and usually CUDA. Use this reference to build or review a user's own training loop with installed `tllib` APIs.

For datasets, transforms, model factories, class-balanced labeled subsets, and dataloaders, first consult [vision-data-models](../../vision-data-models/SKILL.md). For converted checkpoints and fine-tuning choices, consult [task-generalization](../../task-generalization/SKILL.md).

## Common SSL setup checklist

Before choosing a method, confirm:

1. **Dataset/task**: image classification dataset, number of classes, train/validation/test split, and whether automatic downloads are acceptable. Treat dataset downloads as external side effects.
2. **Labeled subset**: `num_samples_per_class` or a fixed labeled-index file; use the same random seed when comparing algorithms.
3. **Unlabeled subset**: all remaining train samples or a user-provided unlabeled list. FlexMatch requires stable per-sample indices for unlabeled examples.
4. **Transforms**: weak augmentation for pseudo-label targets; strong augmentation for student training. UDA/FixMatch/FlexMatch/DST depend on weak/strong pairs.
5. **Model/backbone**: architecture, `num_classes`, `bottleneck_dim`, optional pooling, and whether to fine-tune a pretrained backbone.
6. **Runtime**: CPU is enough for API checks, but full SSL training is normally GPU- and data-heavy.
7. **Logging**: always log supervised loss, unsupervised/self-training loss, mask ratio, pseudo-label accuracy if labels are available only for diagnostics, learning rate, and validation accuracy.

Common trainer knobs seen across TLLib SSL workflows include dataset root/name, `num_samples_per_class`, train/validation resizing, normalization mean/std, architecture, bottleneck dimension, optional pretrained backbone, `finetune`, batch size, learning rate/scheduler, weight decay, epochs, iterations per epoch, random seed, threshold, and method-specific trade-off weights.

## Baseline ERM

Use ERM as the comparison point: train only on labeled samples, optionally with strong augmentation consistency to the true labels.

```python
model.train()
y_l = model(x_l_weak)
y_l_strong = model(x_l_strong)
loss = F.cross_entropy(y_l, labels_l) + lambda_strong * F.cross_entropy(y_l_strong, labels_l)
```

Do not call pseudo-label losses until ERM can overfit a tiny labeled fixture and validate data/model shapes.

## Pseudo Label

Use when you want the simplest self-training loop and can tolerate hard pseudo labels.

```python
pseudo_criterion = ConfidenceBasedSelfTrainingLoss(threshold=0.95)

# labeled branch
y_l = model(x_l)
loss_l = F.cross_entropy(y_l, labels_l)

# unlabeled branch: the same logits can both generate and consume pseudo labels
logits_u = model(x_u)
loss_u, mask, pseudo = pseudo_criterion(logits_u, logits_u)
loss = loss_l + lambda_u * loss_u
```

Operational notes:

- Start with a high threshold only if the model is already reasonably calibrated. Lower threshold (for example 0.7) may be needed for harder datasets or early training.
- Log `mask.float().mean()`. If it is near zero for many iterations, the unsupervised term is inactive.
- Do not use validation labels to select pseudo labels; pseudo-label accuracy is only a diagnostic when ground truth is available in a controlled experiment.

## Pi Model

Use when you want consistency between two stochastic predictions of the same input rather than hard pseudo labels.

```python
criterion = L2ConsistencyLoss()
weight = max_weight * sigmoid_warm_up(epoch, warm_up_epochs=10)

p1 = torch.softmax(model(x_aug1), dim=1)
p2 = torch.softmax(model(x_aug2), dim=1)
loss_u = criterion(p1, p2)
loss = loss_l + weight * loss_u
```

Operational notes:

- Feed probabilities or normalized outputs to the L2 consistency term; it is not a cross-entropy loss.
- Ramp up the consistency weight to avoid destabilizing early training.
- If using a custom `ConsistencyLoss`, make sure the distance function returns one scalar per sample.

## Mean Teacher

Use when a smoothed teacher should provide stable targets for the student.

```python
teacher = EMATeacher(model, alpha=0.999)
criterion = L2ConsistencyLoss(reduction='sum')

# inside each iteration
model.train()
teacher.eval()

logits_l = model(x_l)
loss_l = F.cross_entropy(logits_l, labels_l)

with torch.no_grad():
    teacher_prob = torch.softmax(teacher(x_u_weak), dim=1)
student_prob = torch.softmax(model(x_u_strong), dim=1)
loss_u = criterion(student_prob, teacher_prob) / x_u_strong.size(0)

loss = loss_l + lambda_u * sigmoid_warm_up(epoch, warm_up_epochs) * loss_u
loss.backward()
optimizer.step()
teacher.update()
```

Operational notes:

- Call `teacher.update()` after `optimizer.step()`, not before.
- Keep teacher gradients disabled; use `torch.no_grad()` around teacher predictions.
- BatchNorm behavior matters. If evaluation is unstable, consider whether teacher BatchNorm running statistics should be updated/synced intentionally.

## UDA

Use when weak augmentation supplies soft targets and strong augmentation is trained with KL consistency.

```python
criterion = StrongWeakConsistencyLoss(threshold=0.7, temperature=0.85)

with torch.no_grad():
    logits_weak = model(x_u_weak)
logits_strong = model(x_u_strong)
loss_u = criterion(logits_strong, logits_weak)
loss = loss_l + lambda_u * loss_u
```

Operational notes:

- `temperature` applies to the strong branch log-softmax in TLLib's implementation.
- The threshold is derived from the weak branch confidence.
- Empty masks return a finite loss but contribute no useful unlabeled learning; log mask ratio separately if you implement custom diagnostics.

## FixMatch

Use when you want hard pseudo labels from weak augmentation and train them through strong augmentation.

```python
criterion = ConfidenceBasedSelfTrainingLoss(threshold=0.95)

with torch.no_grad():
    logits_weak = model(x_u_weak)
logits_strong = model(x_u_strong)
loss_u, mask, pseudo = criterion(logits_strong, logits_weak)
loss = loss_l + lambda_u * loss_u
```

Operational notes:

- This is pseudo-label loss with a different source/consumer pair: weak logits produce labels, strong logits are trained.
- Strong augmentation must preserve class identity. If it is too destructive, pseudo-label accuracy collapses even with a high confidence threshold.
- Use the same class ordering for labeled and unlabeled loaders.

## FlexMatch

Use when a fixed threshold rejects too many samples for slow-learning classes. FlexMatch keeps a per-unlabeled-index history and produces class-specific dynamic thresholds.

```python
thresholding = DynamicThresholdingModule(
    threshold=0.95,
    warmup=False,
    mapping_func=lambda x: x / (2 - x),
    num_classes=num_classes,
    n_unlabeled_samples=len(unlabeled_dataset),
    device=device,
)

with torch.no_grad():
    logits_weak = model(x_u_weak)
confidence, pseudo = torch.softmax(logits_weak, dim=1).max(dim=1)
dynamic_threshold = thresholding.get_threshold(pseudo)
mask = (confidence > dynamic_threshold).float()
selected_mask = (confidence > 0.95).long()
thresholding.update(unlabeled_indices, selected_mask, pseudo)

logits_strong = model(x_u_strong)
loss_u = (F.cross_entropy(logits_strong, pseudo, reduction='none') * mask).mean()
```

Operational notes:

- The unlabeled dataset must return stable `idxes`; shuffled loaders are fine only if the sample index travels with the batch.
- `n_unlabeled_samples` must match the size of the index space. If it is too small or too large, updates silently hit wrong history slots or never update many slots.
- `selected_mask` in the TLLib workflow uses the fixed base threshold, while `mask` for training uses the dynamic threshold.

## DebiasMatch-style class balancing

Use when pseudo labels become naturally imbalanced and the model collapses toward frequent predicted classes.

TLLib exposes `ClassBalanceLoss(num_classes)`, which expects probabilities:

```python
prob_u = torch.softmax(logits_u, dim=1)
loss_balance = ClassBalanceLoss(num_classes)(prob_u)
loss = loss_l + lambda_u * loss_u + lambda_balance * loss_balance
```

Operational notes:

- Balance loss should not replace sample-level confidence checks.
- Track predicted class histogram on unlabeled samples. A low supervised loss with a one-class pseudo-label histogram is a collapse symptom.

## Self-Tuning

Use when the user has a self-supervised or pretrained backbone and wants a contrastive/self-tuning objective during data-efficient fine-tuning.

```python
encoder_q = SelfTuningClassifier(backbone_q, num_classes, projection_dim=1024, bottleneck_dim=1024)
encoder_k = SelfTuningClassifier(backbone_k, num_classes, projection_dim=1024, bottleneck_dim=1024)
self_tuning = SelfTuning(encoder_q, encoder_k, num_classes=num_classes, K=32, m=0.999, T=0.07)

pgc_logits, pgc_labels, y_q = self_tuning(im_q, im_k, labels)
loss_cls = F.cross_entropy(y_q, labels)
loss_pgc = -(pgc_labels * pgc_logits).sum(dim=1).mean()
loss = loss_cls + lambda_pgc * loss_pgc
```

Operational notes:

- `backbone.out_features` must be defined. Use [vision-data-models](../../vision-data-models/SKILL.md) for compatible factories.
- Queue size `K`, momentum `m`, and temperature `T` control stability. Very small queues are only useful for smoke tests.
- If the starting checkpoint is MoCo-style, convert it first using [checkpoint conversion](checkpoint-conversion.md).

## DST

Use when the method needs a main head, pseudo head, and adversarial worst-case head to debias pseudo labels.

```python
classifier = DSTImageClassifier(backbone, num_classes, bottleneck_dim=1024, width=2048)
pseudo_criterion = ConfidenceBasedSelfTrainingLoss(threshold=0.7)
wce_criterion = WorstCaseEstimationLoss(eta_prime=2.0)

outputs_l, outputs_l_adv, outputs_l_pseudo = classifier(x_l)
outputs_u, outputs_u_adv, outputs_u_pseudo = classifier(x_u)

loss_l = F.cross_entropy(outputs_l, labels_l)
loss_pseudo, mask, pseudo = pseudo_criterion(outputs_u_pseudo, outputs_u)
loss_wce = wce_criterion(outputs_l, outputs_l_adv, outputs_u, outputs_u_adv)
loss = loss_l + lambda_u * loss_pseudo + eta * loss_wce
loss.backward()
optimizer.step()
classifier.step()
```

Operational notes:

- In eval mode `DSTImageClassifier` returns only the main output. Do not write validation code that expects three outputs.
- Call `classifier.step()` each iteration to advance the warm-start gradient reverse layer.
- The main and adversarial heads must use the same class ordering and batch shape.

## Noisy Student

Use when a trained teacher checkpoint is available or can be produced first.

1. Train or load a teacher and put it in eval mode.
2. Run weak or clean unlabeled images through the teacher to produce pseudo labels or softened logits.
3. Train a student with stronger augmentation/noise using supervised labeled loss plus pseudo-label loss.
4. Optionally repeat with the student as the next teacher.

Operational notes:

- A `pretrained_teacher` checkpoint must match the architecture and class count.
- If the teacher is weak or miscalibrated, high-confidence pseudo labels can be confidently wrong. Validate on a labeled holdout before promoting a student.
- Noisy Student is a workflow pattern in this skill; the reusable TLLib components are classifier/model utilities, pseudo-label losses, and data/model loaders from sibling skills.

## MCC in self-training vs domain adaptation

`MinimumClassConfusionLoss` can regularize unlabeled predictions by penalizing class confusion. If the user's request is explicitly source/target domain adaptation, route the workflow to [domain-adaptation](../../domain-adaptation/SKILL.md). If the task is SSL within one dataset/task, keep MCC as an auxiliary term:

```python
mcc = MinimumClassConfusionLoss(temperature=2.0)
loss = loss_l + lambda_u * loss_u + lambda_mcc * mcc(logits_unlabeled)
```

Use a small explicit `lambda_mcc` and monitor both accuracy and predicted class histogram.

## Minimal non-benchmark validation plan

For a new user workflow, validate in this order:

1. Import `tllib` and run `scripts/tllib_self_training_smoke.py`.
2. Run a one-batch labeled-only ERM step and ensure the loss decreases on a tiny fixture.
3. Add unlabeled weak/strong pairs and print shapes before applying any loss.
4. Add pseudo-label/consistency loss with a permissive threshold and log mask ratio.
5. Restore intended threshold/augmentations and run a short dry run.
6. Only then scale to full dataset/GPU training.
