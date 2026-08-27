---
name: evasion-and-preprocessing
description: "Use ART evasion attacks, preprocessing defences, and adversarial
  training recipes for image/tabular robustness workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Evasion and preprocessing

Use this sub-skill when the task is to generate evasion adversarial examples, select a white-box/black-box/physical image attack, add preprocessing defences, or plan adversarial training with ART estimators.

## Route here

- Craft FGSM/FGM, PGD/BIM/MIM/AutoPGD/AutoAttack, Carlini, DeepFool, ElasticNet, JSMA, universal perturbation, virtual adversarial, HopSkipJump, Boundary, ZOO, SimBA, Square, Pixel/Threshold, SignOPT, DecisionTree, spatial, feature-adversary, or image-patch attacks.
- Add image/tabular preprocessing defences such as standardisation, spatial smoothing, feature squeezing, JPEG compression, Gaussian augmentation, label smoothing, Mixup, CutMix, Cutout, thermometer encoding, total variation minimization, or PixelDefend.
- Plan adversarial training with `AdversarialTrainer`, `AdversarialTrainerMadryPGD`, or TRADES-style trainers.

## Route away

- Model wrapping, `clip_values`, `input_shape`, backend device setup, and estimator construction details belong to `../estimators-and-models/` or `../setup-and-backends/`.
- Poisoning, backdoors, membership/attribute inference, model inversion, or model extraction belong to `../poisoning-inference-extraction/`.
- Robustness metrics, certification, tree verification, security curves, and gradient checks after attack generation belong to `../evaluation-and-certification/`.
- Speech, object-detection-heavy, malware, and audio-heavy evasion workflows are outside this selected runtime scope unless a future refresh adds their required backends. Recognize their ART class names, but do not promise runnable coverage here.

## Operating sequence

1. Confirm the estimator capability: loss gradients for PGD/FGM/BIM/MIM/AutoPGD, class gradients for Carlini/DeepFool/JSMA-style attacks, prediction-only classifiers for hard-label black-box attacks, or neural-network/image-specific support for patch/spatial attacks.
2. Match all perturbation budgets to the estimator input scale and `clip_values`; for normalized `[0, 1]` images use budgets such as `8/255`, not `8`.
3. Check shape conventions before running an attack: PyTorch image estimators usually use `channels_first=True` and `NCHW`; many NumPy image preprocessors default to `channels_first=False` and `NHWC`.
4. For targeted attacks, pass target labels as `y` to `generate`; use one-hot labels unless the wrapped estimator workflow explicitly uses class-index labels.
5. Add preprocessing defences either directly as callable preprocessors or through estimator `preprocessing_defences`; do not treat preprocessing alone as proof of robustness.
6. For adversarial training, start from a bounded PGD/FGM attack, verify labels and clipping, then choose generic, Madry PGD, or TRADES training according to the estimator backend.

## References

- Attack family/API chooser: [references/attack-api-reference.md](references/attack-api-reference.md)
- Preprocessing and adversarial training recipes: [references/preprocessing-and-training.md](references/preprocessing-and-training.md)
- Evasion/preprocessing troubleshooting: [references/troubleshooting.md](references/troubleshooting.md)

## Bundled checks

- Tiny CPU PyTorch PGD/FGM smoke: [scripts/smoke_evasion_pytorch.py](scripts/smoke_evasion_pytorch.py)
- Tiny NumPy standardisation/spatial smoothing smoke: [scripts/smoke_preprocessor_numpy.py](scripts/smoke_preprocessor_numpy.py)

Run bundled scripts with `--help` first; they use synthetic data and do not download datasets.
