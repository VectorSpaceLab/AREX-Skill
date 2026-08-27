# Workflow overview

## Purpose

Use this overview to compose ART workflows across sub-skills without reopening source examples. ART workflows usually follow this order:

1. Install/import and backend readiness.
2. Wrap a model as an ART estimator.
3. Generate attacks or apply defences.
4. Evaluate, diagnose, or certify the result.

## End-to-end routes

### Wrap, attack, evaluate

1. Use `setup-and-backends` if imports or optional dependencies are uncertain.
2. Use `estimators-and-models` to create a wrapper with explicit:
   - `input_shape`
   - `nb_classes`
   - `clip_values`
   - `preprocessing`
   - `channels_first`
   - label format
   - device/backend choice
3. Use `evasion-and-preprocessing` to choose an attack that matches estimator capabilities.
4. Use `evaluation-and-certification` to compute adversarial accuracy, security curves, gradient checks, or certification outputs.

### Defend or adversarially train

1. Confirm the base estimator works on benign data.
2. Add preprocessors such as standardisation, spatial smoothing, feature squeezing, JPEG compression, Mixup/CutMix/Cutout, or thermometer encoding.
3. For adversarial training, start from a bounded FGM/PGD attack and a small batch before scaling.
4. Re-evaluate with a stronger or different attack family; do not accept training loss alone as robustness evidence.

### Poisoning, privacy, extraction

1. Identify whether the user is modifying training data, inferring private attributes/membership, reconstructing inputs, or stealing model behavior.
2. Use `poisoning-inference-extraction` to determine the required data splits, labels, query budgets, and estimator capabilities.
3. Use `estimators-and-models` only for wrapper construction details.
4. Use `evaluation-and-certification` for downstream privacy/robustness metrics.

## Data and label conventions

- Match `x` scale to `clip_values`. If images are normalized to `[0, 1]`, budgets such as `8/255` are more appropriate than raw pixel budgets such as `8`.
- Check channel order. PyTorch image estimators commonly use `channels_first=True` and `NCHW`; NumPy image preprocessors often default to `channels_first=False` and `NHWC`.
- Many classifiers and attacks expect one-hot labels for `y`; some sklearn wrappers and metrics can work with class-index labels. Confirm in the owning sub-skill before mixing formats.
- Use tiny benign `predict` checks before `fit`, gradients, attacks, or metrics.
- White-box attacks require gradient-enabled estimators. Black-box wrappers are useful, but they do not make PGD/FGM/Carlini gradient calls available.

## Estimator capability quick map

| Need | Estimator capability |
|---|---|
| Benign predictions and black-box attacks | `predict` with probabilities/logits and stable output shape |
| FGM/PGD/BIM/MIM/AutoPGD/security curves | `loss_gradient` through a compatible classifier |
| Carlini/DeepFool/JSMA-like attacks | class gradients or loss gradients depending on attack |
| Adversarial training | `fit`, gradients, labels, and a compatible attack object |
| Privacy membership inference | train/test or member/non-member data for the attack model plus classifier/regressor predictions or losses |
| Tree verification | tree classifier wrapper exposing tree structure; normalized numeric inputs |
| Randomized smoothing/certification | neural-network classifier wrapper plus sampling budget and noise scale |

## Scaling from smoke to real work

The bundled scripts are intentionally tiny. When moving to real data:

- Increase batch sizes, attack iterations, and Monte Carlo sample counts gradually.
- Log metrics, random seeds, `clip_values`, and preprocessing choices.
- Use `SummaryWriter` only after the core workflow works without logging.
- Keep expensive downloads, notebook execution, and long training outside this skill's diagnostic scripts.
