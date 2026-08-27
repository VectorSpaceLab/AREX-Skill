# Attack API reference

This reference helps choose an ART evasion attack that matches the estimator, perturbation budget, input shape, and label convention. Use it after the model has already been wrapped as an ART estimator.

## Quick chooser

| User intent | Prefer | Estimator capability | Notes |
|---|---|---|---|
| Fast first-pass white-box image/tabular attack | `FastGradientMethod` | `BaseEstimator` + `LossGradientsMixin` | Single-step; good smoke check before stronger PGD. |
| Strong bounded first-order attack | `ProjectedGradientDescent`, `BasicIterativeMethod`, `MomentumIterativeMethod`, `AutoProjectedGradientDescent` | `LossGradientsMixin`; AutoPGD also expects classifier behavior | Use `eps`, `eps_step`, `max_iter`, `norm`, `num_random_init`; PGD can also accept `mask=` in `generate`. |
| Evaluation suite with multiple attacks | `AutoAttack` | classifier estimator; component attacks may need gradients | Provide custom `attacks=[...]` if the default suite does not match estimator capabilities. |
| Optimization-heavy white-box attack | `CarliniL0Method`, `CarliniL2Method`, `CarliniLInfMethod`, `ElasticNet` | class-gradient classifier | Often slow; start with tiny batches and explicit `max_iter`/`binary_search_steps`. |
| Decision boundary / geometric white-box attack | `DeepFool`, `SaliencyMapMethod`, `NewtonFool`, `Wasserstein` | typically class gradients or loss gradients | Check class count, `clip_values`, and batch size; these can be expensive. |
| Universal perturbation | `UniversalPerturbation`, `TargetedUniversalPerturbation`, `VirtualAdversarialMethod` | classifier; inner attacker may require gradients | Budget applies to a fixed perturbation reused across samples. |
| Prediction-only hard-label black-box | `HopSkipJump`, `BoundaryAttack`, `SignOPTAttack` | classifier predictions; no gradients required | Query budgets are controlled by `max_iter`, `max_eval`, `init_eval`, `query_limit`, or trial counts. |
| Score/query black-box | `ZooAttack`, `SquareAttack`, `SimBA` | classifier predictions; some classes require neural-network estimator mixins | Use low `max_iter`/small batches first; query count can dominate runtime. |
| Pixel/sparse image perturbations | `PixelAttack`, `ThresholdAttack` | neural-network classifier | CPU-safe only for very small images and iterations. |
| Decision tree evasion | `DecisionTreeAttack` | `ScikitlearnDecisionTreeClassifier` | Tree-specific; not a generic sklearn wrapper attack. |
| Spatial/image transform | `SpatialTransformation`, `FeatureAdversariesNumpy`, `FeatureAdversariesPyTorch`, `FeatureAdversariesTensorFlowV2` | neural-network/image estimator; PyTorch variant needs PyTorch estimator | Validate `channels_first`, layer selection, and image dimensions. |
| Physical image patch/sticker | `AdversarialPatch`, `AdversarialPatchNumpy`, `AdversarialPatchPyTorch`, `AdversarialPatchTensorFlowV2`, `GRAPHITEBlackbox`, `GRAPHITEWhiteboxPyTorch` | neural-network/image classifier; GRAPHITE black-box uses hard-label style queries | Treat as image-classification physical scope; validate patch shape, mask, rotation, scale, and clipping before long runs. |
| Object-detector/special physical attacks | `DPatch`, `RobustDPatch`, `SNAL`, `AdversarialTexturePyTorch` | object detector or specialized PyTorch estimator | Recognize these names but do not treat them as covered by the selected runnable scope. Ask for backend/scope expansion. |

## Common imports and constructor signatures

| Class | Import | Key constructor parameters |
|---|---|---|
| `FastGradientMethod` | `from art.attacks.evasion import FastGradientMethod` | `estimator`, `norm=np.inf`, `eps=0.3`, `eps_step=0.1`, `targeted=False`, `num_random_init=0`, `batch_size=32`, `minimal=False`, `summary_writer=False` |
| `ProjectedGradientDescent` | `from art.attacks.evasion import ProjectedGradientDescent` | `estimator`, `norm=np.inf`, `eps=0.3`, `eps_step=0.1`, `decay=None`, `max_iter=100`, `targeted=False`, `num_random_init=0`, `batch_size=32`, `random_eps=False`, `summary_writer=False`, `verbose=True` |
| `AutoProjectedGradientDescent` | `from art.attacks.evasion import AutoProjectedGradientDescent` | `estimator`, `norm=np.inf`, `eps=0.3`, `eps_step=0.1`, `max_iter=100`, `targeted=False`, `nb_random_init=5`, `batch_size=32`, `loss_type=None`, `verbose=True` |
| `AutoAttack` | `from art.attacks.evasion import AutoAttack` | `estimator`, `norm=np.inf`, `eps=0.3`, `eps_step=0.1`, `attacks=None`, `batch_size=32`, `estimator_orig=None`, `targeted=False`, `parallel_pool_size=0` |
| `CarliniL2Method` | `from art.attacks.evasion import CarliniL2Method` | `classifier`, `confidence=0.0`, `targeted=False`, `learning_rate=0.01`, `binary_search_steps=10`, `max_iter=10`, `initial_const=0.01`, `batch_size=1`, `verbose=True` |
| `DeepFool` | `from art.attacks.evasion import DeepFool` | `classifier`, `max_iter=100`, `epsilon=1e-6`, `nb_grads=10`, `batch_size=1`, `verbose=True` |
| `HopSkipJump` | `from art.attacks.evasion import HopSkipJump` | `classifier`, `batch_size=64`, `targeted=False`, `norm=2`, `max_iter=50`, `max_eval=10000`, `init_eval=100`, `init_size=100`, `verbose=True` |
| `BoundaryAttack` | `from art.attacks.evasion import BoundaryAttack` | `estimator`, `batch_size=64`, `targeted=True`, `delta=0.01`, `epsilon=0.01`, `step_adapt=0.667`, `max_iter=5000`, `num_trial=25`, `sample_size=20`, `init_size=100`, `min_epsilon=0.0`, `verbose=True` |
| `SimBA` | `from art.attacks.evasion import SimBA` | `classifier`, `attack='dct'`, `max_iter=3000`, `order='random'`, `epsilon=0.1`, `freq_dim=4`, `stride=1`, `targeted=False`, `batch_size=1`, `verbose=True` |
| `SquareAttack` | `from art.attacks.evasion import SquareAttack` | `estimator`, `norm=np.inf`, `adv_criterion=None`, `loss=None`, `max_iter=100`, `eps=0.3`, `p_init=0.8`, `nb_restarts=1`, `batch_size=128`, `verbose=True` |
| `PixelAttack` / `ThresholdAttack` | `from art.attacks.evasion import PixelAttack, ThresholdAttack` | `classifier`, `th=None`, `es`, `max_iter=100`, `targeted=False`, `verbose=False` |
| `SignOPTAttack` | `from art.attacks.evasion import SignOPTAttack` | `estimator`, `targeted=True`, `epsilon=0.001`, `num_trial=100`, `max_iter=1000`, `query_limit=20000`, `k=200`, `alpha=0.2`, `beta=0.001`, `batch_size=64`, `verbose=False` |
| `DecisionTreeAttack` | `from art.attacks.evasion import DecisionTreeAttack` | `classifier`, `offset=0.001`, `verbose=True` |
| `AdversarialPatch` | `from art.attacks.evasion import AdversarialPatch` | `classifier`, `rotation_max=22.5`, `scale_min=0.1`, `scale_max=1.0`, `learning_rate=5.0`, `max_iter=500`, `batch_size=16`, `patch_shape=None`, `targeted=True`, `verbose=True` |
| `AdversarialPatchPyTorch` | `from art.attacks.evasion import AdversarialPatchPyTorch` | `estimator`, `rotation_max=22.5`, `scale_min=0.1`, `scale_max=1.0`, `distortion_scale_max=0.0`, `learning_rate=5.0`, `max_iter=500`, `batch_size=16`, `patch_shape=(3, 224, 224)`, `patch_location=None`, `patch_type='circle'`, `optimizer='Adam'`, `targeted=True` |
| `GRAPHITEBlackbox` | `from art.attacks.evasion import GRAPHITEBlackbox` | `classifier`, `noise_size`, `net_size`, physical transform ranges, `num_xforms_*`, `num_boost_queries`, `batch_size=64` |
| `GRAPHITEWhiteboxPyTorch` | `from art.attacks.evasion import GRAPHITEWhiteboxPyTorch` | `classifier`, `net_size`, `min_tr=0.8`, `num_xforms=100`, `step_size=0.0157`, `steps=50`, transform ranges, `batch_size=64` |
| `SNAL` | `from art.attacks.evasion import SNAL` | `estimator`, `candidates`, `collector`, `eps`, `max_iter`, `num_grid`; specialized object-detection scope |

## Estimator compatibility rules

- `LossGradientsMixin` is required for FGM/FGSM, PGD, BIM, MIM, and many adversarial-training attacks. A plain black-box estimator is not enough.
- `ClassGradientsMixin` is required for Carlini, DeepFool, ElasticNet, JSMA/saliency-map workflows, and similar class-gradient attacks.
- Prediction-only classifiers can use hard-label/query attacks such as HopSkipJump, BoundaryAttack, SignOPT, ZOO, and often SquareAttack; check whether the concrete attack also requires `NeuralNetworkMixin`.
- `NeuralNetworkMixin` is required by many image attacks (`SimBA`, `SquareAttack`, `PixelAttack`, `AdversarialPatch`, `SpatialTransformation`, feature adversaries).
- `DecisionTreeAttack` is only for `ScikitlearnDecisionTreeClassifier`.
- Object detector, speech, malware, and audio-specific evasion classes are not selected for runnable coverage here.

## `generate` labels, masks, and outputs

- Most attacks expose `x_adv = attack.generate(x, y=None, **kwargs)` and return an array with the same shape as `x`.
- For untargeted attacks, `y` can often be omitted; ART may use model predictions as labels. Pass true labels when you need repeatable evaluation.
- For targeted attacks, `y` is the target label, not the original label. One-hot target labels are the safest cross-estimator convention.
- PGD and HopSkipJump support `mask=` in `generate`; use a mask broadcastable to `x`. Positions with mask value `0` should remain unchanged.
- For patch attacks, `generate` generally learns a patch and patch mask/metadata; `apply_patch` inserts the learned patch into images. Validate patch shape and scale before long optimization.

## Budgets and scale conventions

- `eps`, `eps_step`, `epsilon`, and patch learning rates use the estimator input scale. If inputs are `[0, 1]`, `8/255` is a common image budget; if inputs are `[0, 255]`, use pixel-scale values and matching `clip_values`.
- For iterative attacks, keep `eps_step <= eps` for `L_inf` workflows unless deliberately testing unusual behavior.
- `norm` is commonly `np.inf`, `2`, or `1`; not all attacks support all norms.
- `clip_values` on the estimator determines clipping after perturbation. Missing or wrong clipping is a common cause of invalid adversarial samples.
- Query attacks should start with very small `max_iter`, `max_eval`, `init_eval`, `query_limit`, `sample_size`, and `batch_size`, then scale up only after a tiny smoke succeeds.

## Shape and channel conventions

- ART estimators expect the same shape at attack time that they were constructed with. For PyTorch image classifiers this is commonly `NCHW` with `channels_first=True`; for many NumPy image preprocessors the default is `NHWC` with `channels_first=False`.
- `input_shape` excludes the batch dimension. Examples: `(1, 28, 28)` for grayscale NCHW PyTorch, `(28, 28, 1)` for NHWC.
- Patch `patch_shape` follows the estimator channel convention; a PyTorch patch is commonly `(C, H, W)`.
- Masks should either match the full input shape or the per-sample feature/image shape so ART can broadcast them consistently.

## Summary writer convention

`summary_writer` can be `False`, `True`, a directory string, or a SummaryWriter object for supported attacks. Keep it disabled in smoke checks. If enabled, direct logs to a user-controlled run directory and route robustness interpretation to the evaluation/certification sub-skill.
