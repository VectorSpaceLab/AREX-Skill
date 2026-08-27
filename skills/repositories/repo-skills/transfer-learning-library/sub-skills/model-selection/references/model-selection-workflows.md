# Model-Selection Workflows

TLLib ranking metrics estimate how transferable a pretrained representation or source classifier is to a labeled target task. They are a fast pre-fine-tuning screen, not a replacement for validation after training.

## 1. Decide what arrays are available

| Available evidence | Metrics to run | What is missing |
| --- | --- | --- |
| Feature matrix + target labels | H-score, regularized H-score, LogME, TransRate | Source-head predictions are needed for LEEP/NCE. |
| Source-class probabilities + target labels | LEEP; NCE after `argmax` | Features are needed for H-score/LogME/TransRate. |
| Source predicted class ids + target labels | NCE | Probabilities are needed for LEEP; features are needed for feature metrics. |
| Features + continuous targets | LogME with `regression=True` | Classification metrics do not apply directly. |
| Unlabeled target data only | none of these TLLib ranking metrics | Obtain a labeled ranking subset or use a different method outside this sub-skill. |

## 2. Extract reusable features and predictions

For each candidate pretrained model:

1. Use the same target ranking split, preprocessing, batch order, and random seed.
2. Put the model in evaluation mode and disable gradients.
3. Capture a 2-D feature matrix from the same logical layer for all candidates, commonly the input to the final classifier head.
4. Capture source-head logits or outputs for the same samples, then convert logits to probabilities for LEEP.
5. Save arrays and metadata before ranking so the expensive extraction step can be reused.

For dataset construction, model factories, transforms, and local image-list validation, use [vision-data-models](../../vision-data-models/SKILL.md). This sub-skill intentionally does not bundle full dataset feature extraction because that depends on user data, pretrained weights, optional model packages, and often GPU runtime.

### Safe extraction skeleton

```python
import numpy as np
import torch
import torch.nn.functional as F

features, probabilities, targets = [], [], []
model.eval()
with torch.no_grad():
    for images, labels in loader:
        images = images.to(device)
        # Replace this with the selected model's feature/head split.
        feats = backbone(images)
        logits = classifier(feats)
        features.append(feats.detach().cpu().reshape(feats.shape[0], -1))
        probabilities.append(F.softmax(logits, dim=1).detach().cpu())
        targets.append(labels.detach().cpu())

features = torch.cat(features).numpy()
predictions = torch.cat(probabilities).numpy()
targets = torch.cat(targets).numpy().astype(np.int64)
```

The exact feature/head split is model-specific; verify it with the model documentation or a small forward pass before ranking.

## 3. Cache arrays safely

Use a cache directory per target dataset/split and candidate model. At minimum save:

- `features.npy`: `(N, F)` float array.
- `predictions.npy`: `(N, C_s)` probability array, if LEEP/NCE will be used.
- `targets.npy`: `(N,)` integer target labels after any remapping.
- `metadata.json`: model name, checkpoint identifier, target dataset name, split, preprocessing, feature layer, package versions, `N`, `F`, `C_s`, `C_t`, and timestamp.

Before reusing a cache, check that metadata still matches the intended model, checkpoint, split, preprocessing, and feature layer. A stale cache can silently rank the wrong model.

## 4. Compute scores for one candidate

```python
from tllib.ranking import h_score, log_expected_empirical_prediction, negative_conditional_entropy, log_maximum_evidence
from tllib.ranking.hscore import regularized_h_score
from tllib.ranking.transrate import transrate

scores = {
    "h_score": h_score(features, targets),
    "regularized_h_score": regularized_h_score(features, targets),
    "logme": log_maximum_evidence(features, targets),
    "transrate": transrate(features, targets),
}

if predictions is not None:
    scores["leep"] = log_expected_empirical_prediction(predictions, targets)
    scores["nce"] = negative_conditional_entropy(predictions.argmax(axis=1), targets)
```

## 5. Rank multiple candidates

1. Compute each metric for every candidate on the exact same target split.
2. Sort each metric in descending order. LEEP and NCE can be negative; less negative is still higher.
3. Look for agreement across several metrics rather than trusting a single score.
4. Treat very close scores as ties unless repeated extraction on another subset confirms the order.
5. Prefer regularized H-score over vanilla H-score when feature covariance is unstable.
6. Record the final chosen candidate and then fine-tune/evaluate it through [task-generalization](../../task-generalization/SKILL.md).

Example ranking table format:

| candidate | H-score | Reg-H | LogME | TransRate | LEEP | NCE | decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| model A | 12.3 | 11.8 | 0.41 | 2.6 | -1.05 | -0.72 | shortlist |
| model B | 9.4 | 9.1 | 0.37 | 2.2 | -1.12 | -0.80 | backup |

## 6. When to run which metric

- Use **LogME** as a robust default when you have features and target labels; it supports both classification and regression.
- Use **regularized H-score** when high-dimensional features make vanilla H-score noisy.
- Use **TransRate** as an additional feature-only ranking signal; keep `eps` fixed across candidates.
- Use **LEEP/NCE** when the pretrained model still has a meaningful source classifier head and you can obtain source-class probabilities or predicted labels.
- Skip LEEP/NCE when the source head was removed, replaced, or does not correspond to a fixed source label space.

## 7. Interpretation limits

Transferability scores estimate expected fine-tuning usefulness; they do not guarantee final accuracy. Differences can be dominated by target subset bias, label noise, preprocessing mismatch, source-head mismatch, or feature-layer choice. Always validate the selected model with an actual fine-tuning run and target validation metric.
