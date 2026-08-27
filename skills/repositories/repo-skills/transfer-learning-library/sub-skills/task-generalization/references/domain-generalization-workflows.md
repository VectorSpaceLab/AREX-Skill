# Domain-Generalization Workflows

Use this when the user has labeled data from multiple source domains and wants a model that generalizes to unseen target domains. If target-domain training data is unlabeled or used during training, route to [domain-adaptation](../../domain-adaptation/SKILL.md). For dataset and model factory details, route to [vision-data-models](../../vision-data-models/SKILL.md).

## Common setup

A DG training loop in TLLib-style code has these parts:

1. Build one dataloader per labeled source domain; sample several source domains per iteration.
2. Build a classifier/backbone. IBN and MixStyle replace or augment the backbone; CORAL/GroupDRO/IRM/VREx/MLDG change the objective.
3. For each iteration, concatenate the sampled per-domain batches only after retaining domain boundaries.
4. Compute per-domain classification losses and any method-specific penalty.
5. Tune `trade_off`, penalty annealing, and domain sampling on source-domain validation data. Do not use held-out target-domain labels for method selection unless the user explicitly describes a supervised target validation protocol.

Distilled training-command shape for benchmark-like runs:

```text
python train_dg.py <data-root> -d <dataset-name> -s <source-domains...> -t <held-out-target> -a <arch> \
  --batch-size <per-iteration-total> --n-domains-per-batch <k> --epochs <n> --iters-per-epoch <n> \
  --lr <value> --wd <value> --seed <seed> --log <output-dir> --phase train
```

This shape is a recipe, not a bundled executable. Real DG training usually requires image datasets, pretrained weights, optional model packages, and CUDA.

## Method selection quick guide

| User symptom or goal | Start with | Why | Main cautions |
| --- | --- | --- | --- |
| Baseline across multiple source domains | ERM | Establishes source-only reference before penalties | Needs balanced domain sampling and source validation |
| Style/appearance shift, same labels | MixStyle | Mixes feature statistics between instances/domains | Active only in `train()`; batch composition matters |
| Appearance shift with architecture-level robustness | IBN | Adds instance-normalization channels in ResNet-style backbones | `pretrained=True` may download external weights |
| Need covariance alignment among source domains | CORAL/DG | Pairwise feature covariance penalty | Penalty can dominate CE if trade-off too high |
| Worst-domain robustness | GroupDRO | Upweights high-loss domains | Domain index ordering and per-domain losses must be correct |
| Invariant classifier objective | IRM | Penalizes environment-specific classifier gradients | Needs annealing and stable per-domain batch sizes |
| Equalize risks across domains | VREx | Penalizes variance of per-domain CE losses | Penalize after warmup; high trade-off can underfit |
| Meta-generalization to held-out source domains | MLDG | Support/query source-domain meta-learning | Usually needs optional differentiable inner-loop tooling |

## MixStyle workflow

Use MixStyle when domains mainly differ in texture, color, or style statistics.

```python
from tllib.normalization.mixstyle import MixStyle

features = backbone_stem(images)
features = MixStyle(p=0.5, alpha=0.1).train()(features)
logits = classifier_head(rest_of_backbone(features))
loss = cross_entropy(logits, labels)
```

Operational notes:

- MixStyle is a module-level operation and returns unchanged input in eval mode.
- Insert it into intermediate convolutional feature maps, not into raw labels or logits.
- Prefer mixed-domain mini-batches; a batch from one domain only weakens the domain-generalization effect.
- If using a TLLib MixStyle ResNet factory, choose the layers with a `mix_layers`-style setting and document `p`/`alpha`.

## IBN workflow

Use IBN when you want a backbone-level normalization change.

```python
from tllib.normalization.ibn import resnet50_ibn_a

backbone = resnet50_ibn_a(pretrained=False)
```

Operational notes:

- `_ibn_a` places IBN in early residual blocks; `_ibn_b` uses an instance-normalization pattern in residual outputs.
- Use `pretrained=False` for offline setup or smoke checks. `pretrained=True` reaches external checkpoint URLs.
- IBN backbones output convolutional features and still need a classifier head/pooling strategy. Route head/model assembly questions to [vision-data-models](../../vision-data-models/SKILL.md).

## CORAL as a DG penalty

Use CORAL to align pairwise source-domain feature covariances.

```python
from tllib.alignment.coral import CorrelationAlignmentLoss

coral = CorrelationAlignmentLoss()
loss_ce = sum(cross_entropy(logits[d], labels[d]) for d in domains) / len(domains)
loss_penalty = 0.0
pairs = 0
for i in range(len(domains)):
    for j in range(i + 1, len(domains)):
        loss_penalty = loss_penalty + coral(features[i], features[j])
        pairs += 1
loss = loss_ce + trade_off * loss_penalty / max(pairs, 1)
```

Cautions:

- Feature tensors should be two-dimensional `[batch, feature_dim]` and comparable across domains.
- Normalize by the number of domain pairs to keep `trade_off` stable when changing `n_domains_per_batch`.
- CORAL can also be used in domain adaptation; if unlabeled target features are part of training, route to [domain-adaptation](../../domain-adaptation/SKILL.md).

## GroupDRO workflow

Use GroupDRO when the user asks for worst-case source-domain performance or robustness to group shifts.

```python
from tllib.reweight.groupdro import AutomaticUpdateDomainWeightModule

weight_module = AutomaticUpdateDomainWeightModule(num_domains=num_sources, eta=1e-2, device=device)
loss_per_domain = torch.stack(per_domain_ce_losses)
idxes = sampled_domain_idxes
weight_module.update(loss_per_domain, idxes)
weights = weight_module.get_domain_weight(idxes)
loss = (loss_per_domain * weights).sum()
```

Cautions:

- `sampled_domain_idxes` must map to the same domain order for the whole run.
- Log both raw per-domain losses and the selected normalized weights.
- High `eta` can make weights collapse to one domain; lower it when training becomes unstable.

## IRM pattern

TLLib's IRM logic is a workflow pattern rather than a reusable package loss. Implement it as:

1. Maintain a scalar `scale` parameter initialized to `1.0` with `requires_grad=True`.
2. For each domain's logits and labels, split the domain mini-batch into two interleaved halves.
3. Compute CE on both halves after multiplying logits by `scale`.
4. Compute gradients of both CEs with respect to `scale` and penalize their product.
5. Use an annealed trade-off: small or zero penalty during warmup, full penalty after `anneal_iters`.

Cautions:

- Each domain needs enough samples per batch for two halves.
- If IRM loss explodes, reduce trade-off, increase warmup, and confirm class labels are valid.

## VREx pattern

VREx minimizes mean risk plus cross-domain risk variance.

```python
losses = torch.stack(per_domain_ce_losses)
loss_ce = losses.mean()
loss_penalty = ((losses - loss_ce) ** 2).mean()
loss = loss_ce + trade_off * loss_penalty
```

Cautions:

- Use source-domain validation to choose `trade_off` and warmup.
- If all domains underfit, the penalty may be too large or annealed too early.

## MLDG pattern

MLDG uses meta-train/meta-test splits of source domains:

1. Split sampled source domains into support and query groups.
2. Clone the classifier for an inner update on support-domain CE.
3. Evaluate query-domain CE with the inner-updated classifier.
4. Optimize the original classifier using support loss plus `trade_off * query_loss` through the inner step.

Cautions:

- This is expensive and often needs an optional differentiable-optimization helper.
- Keep support/query domain counts explicit in logs.
- If optional inner-loop tooling is unavailable, present MLDG as a design recipe rather than a verified runnable component.

## Re-identification DG

TLLib also has DG patterns for re-identification tasks using IBN/MixStyle-style backbones. Treat those as dataset/model-heavy workflows:

- Route dataset layout, re-id metrics, and model details to [vision-data-models](../../vision-data-models/SKILL.md).
- Do not claim CPU smoke coverage for re-id benchmark training.
- Expect GPU, large datasets, and task-specific evaluation protocols.
