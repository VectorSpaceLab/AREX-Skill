# API Reference: Task Generalization

This reference covers TLLib public APIs used for domain generalization and task adaptation. Import the installed `tllib` package; the benchmark trainers remain evidence for patterns only and are not runtime dependencies.

## Normalization and style modules

### MixStyle

```python
from tllib.normalization.mixstyle import MixStyle

mix = MixStyle(p=0.5, alpha=0.1)
mix.train()   # active only in training mode
y = mix(x)    # x: [batch, channels, height, width]
```

- Purpose: domain generalization by mixing per-instance feature-map statistics between samples.
- Inputs/outputs: 4D feature maps; output shape equals input shape.
- Important behavior: `eval()` returns the input unchanged. If validation accuracy unexpectedly changes, confirm no MixStyle module is left in training mode.
- Batch caution: use normal mini-batches with at least two samples. The implementation permutes the batch and works best with even, multi-domain batches.

### IBN layers and IBN-ResNet factories

```python
from tllib.normalization.ibn import InstanceBatchNorm2d, resnet50_ibn_a, resnet50_ibn_b

layer = InstanceBatchNorm2d(planes=64, ratio=0.5)
backbone = resnet50_ibn_a(pretrained=False)
```

- `InstanceBatchNorm2d(planes, ratio=0.5)` splits channels into an instance-normalized branch and a batch-normalized branch.
- `resnet18/34/50/101_ibn_a` and `_ibn_b` construct IBN backbones. `pretrained=True` downloads external IBN checkpoints; use `pretrained=False` for offline smoke checks.
- Route model factory and dataset questions to [vision-data-models](../../vision-data-models/SKILL.md).

### StochNorm and BatchNorm conversion

```python
from tllib.normalization.stochnorm import StochNorm2d, convert_model

layer = StochNorm2d(num_features=64, p=0.5)
converted_model = convert_model(model_with_batchnorm, p=0.5)
```

- `StochNorm1d/2d/3d` replace BatchNorm behavior with a stochastic mixture of running-stat and batch-stat branches during training.
- `convert_model(module, p)` recursively replaces PyTorch BatchNorm modules with StochNorm modules and copies running statistics/affine weights.
- CPU caveat: in TLLib 0.4, StochNorm training forward creates the Bernoulli branch mask on CUDA. CPU-only smoke checks should set StochNorm modules to `eval()`; real StochNorm training expects CUDA or a patched local implementation.
- Conversion caution: convert after constructing/loading the BatchNorm model, then verify the converted model's state dict and training/eval behavior before long training.

## Domain-generalization losses and reweighting

### CORAL loss as a DG penalty

```python
from tllib.alignment.coral import CorrelationAlignmentLoss

coral = CorrelationAlignmentLoss()
penalty = coral(features_domain_a, features_domain_b)
```

- Purpose: match second-order feature statistics between domains. In DG, compute pairwise penalties among labeled source domains.
- Inputs: feature matrices with shape `[batch, feature_dim]` for each domain.
- If the user task includes unlabeled target-domain adaptation, route to [domain-adaptation](../../domain-adaptation/SKILL.md).

### GroupDRO domain weights

```python
from tllib.reweight.groupdro import AutomaticUpdateDomainWeightModule

module = AutomaticUpdateDomainWeightModule(num_domains=3, eta=1e-2, device=device)
loss_per_domain = torch.stack([loss_a, loss_b, loss_c])
idxes = [0, 1, 2]
module.update(loss_per_domain, idxes)
weights = module.get_domain_weight(idxes)
objective = (loss_per_domain * weights).sum()
```

- Purpose: emphasize high-loss source domains for worst-case DG robustness.
- Inputs: one scalar loss per sampled source domain plus matching domain indices.
- `update()` changes stored global weights; `get_domain_weight()` normalizes the selected subset.
- Keep domain ordering stable across epochs and logs.

### IRM, VREx, and MLDG patterns

TLLib's reusable package APIs do not expose standalone IRM/VREx/MLDG loss classes. Use these patterns when implementing custom loops:

- **IRM**: compute cross-entropy through a learnable scalar/dummy classifier per domain; penalize the product of gradients from disjoint mini-batch halves; anneal the penalty trade-off after warmup.
- **VREx**: compute cross-entropy per domain, minimize mean CE plus variance of per-domain CE values.
- **MLDG**: split source domains into support/query groups, take inner optimization steps on support domains, then optimize query loss through the inner update. This usually requires an optional differentiable-optimization helper such as `higher`.

## Task-adaptation regularization APIs

### L2 and L2-SP

```python
from tllib.regularization.delta import L2Regularization, SPRegularization

l2 = L2Regularization(target_model)()
l2_sp = SPRegularization(source_model, target_model)()
```

- `L2Regularization(model)` returns `0.5 * sum(||w||^2)` across parameters.
- `SPRegularization(source_model, target_model)` returns `0.5 * sum(||w_target - w_source||^2)` using matching parameter names.
- Use L2-SP only when the target model architecture and parameter names match the pretrained source model. Head replacement often means the head should be regularized separately or excluded.

### DELTA feature-map regularization

```python
from tllib.regularization.delta import (
    BehavioralRegularization,
    AttentionBehavioralRegularization,
    IntermediateLayerGetter,
)

getter_src = IntermediateLayerGetter(source_model, return_layers=["layer3", "layer4"])
getter_tgt = IntermediateLayerGetter(target_model, return_layers=["layer3", "layer4"])
f_src, _ = getter_src(images)
f_tgt, logits = getter_tgt(images)
loss = BehavioralRegularization()(f_src, f_tgt)
```

- `BehavioralRegularization()` penalizes feature-map differences between frozen source and target networks.
- `AttentionBehavioralRegularization(channel_attention)` applies channel weights to the feature-map penalty.
- `IntermediateLayerGetter(model, return_layers, keep_output=True)` collects named module outputs using forward hooks.
- Layer names must exist in both source and target models and produce matching feature-map shapes.

### BSS

```python
from tllib.regularization.bss import BatchSpectralShrinkage

bss = BatchSpectralShrinkage(k=1)
penalty = bss(features)  # features: [batch, feature_dim]
```

- Penalizes the smallest singular values of the batch feature matrix.
- Use as `loss = cross_entropy + trade_off * bss(features)`.
- Typical `k` is small; oversized `k` can over-constrain features and worsen negative transfer.

### Co-Tuning

```python
from tllib.regularization.co_tuning import CoTuningLoss, Relationship, Classifier

loss_fn = CoTuningLoss()
loss = loss_fn(source_logits, relationship_targets)
```

- `CoTuningLoss(input, target)` expects source-head logits and a conditional distribution `p(source_class | target_class)` for each sample.
- `Relationship(data_loader, classifier, device, cache=None)` estimates that conditional relationship from target data and a source classifier, optionally caching a NumPy matrix.
- `Classifier(backbone, num_classes, head_source, ...)` returns `(y_source, y_target)` in training mode and only target logits in eval mode.

### LwF / knowledge distillation

```python
from tllib.regularization.lwf import Classifier, collect_pretrain_labels
from tllib.regularization.knowledge_distillation import KnowledgeDistillationLoss

kd = KnowledgeDistillationLoss(T=3)
loss = target_ce + trade_off * kd(source_logits_now, source_logits_saved)
```

- The LwF classifier shares a backbone and has source and target heads.
- `collect_pretrain_labels(data_loader, classifier, device)` collects source-model outputs for later distillation.
- Maintain deterministic dataset ordering when storing and reusing pretrained logits.

### Bi-Tuning

```python
from tllib.regularization.bi_tuning import Classifier, BiTuning

encoder_q = Classifier(backbone_q, num_classes, projection_dim=128)
encoder_k = Classifier(backbone_k, num_classes, projection_dim=128)
bituning = BiTuning(encoder_q, encoder_k, num_classes=num_classes, K=40, m=0.999, T=0.07)
y_q, logits_z, logits_y, labels_c = bituning(images_q, images_k, labels)
```

- Uses query/key encoders, projector outputs, normalized features, and class-wise queues.
- Training loss combines target classification CE with contrastive losses on `logits_z` and `logits_y` against `labels_c`.
- Needs paired augmentations of each input image. See [task-adaptation workflows](task-adaptation-workflows.md) and [checkpoint conversion](checkpoint-conversion.md) for MoCo-pretrained setups.

## Component smoke script

Run:

```bash
python path/to/tllib_task_generalization_smoke.py
```

Expected result: a JSON summary with finite scalar checks and no dataset/checkpoint downloads. A passing smoke verifies API availability, not benchmark accuracy.
