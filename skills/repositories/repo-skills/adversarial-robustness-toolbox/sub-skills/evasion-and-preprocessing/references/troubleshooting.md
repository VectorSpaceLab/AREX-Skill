# Evasion and preprocessing troubleshooting

## Attack fails because gradients are missing

Symptoms:

- Error mentions estimator requirements, `LossGradientsMixin`, `ClassGradientsMixin`, or missing `loss_gradient`/`class_gradient`.
- PGD/FGM/Carlini/DeepFool fails on a black-box classifier.

Actions:

1. Check the attack requirement family:
   - FGM, PGD, BIM, MIM, AutoPGD: loss gradients.
   - Carlini, DeepFool, ElasticNet, JSMA/saliency map: class gradients.
   - HopSkipJump, BoundaryAttack, SignOPT, ZOO: prediction/query access.
2. If the estimator is truly black-box, switch to HopSkipJump, BoundaryAttack, SignOPT, ZOO, SquareAttack, or SimBA if its estimator mixins are satisfied.
3. If the user owns the model, route to estimator construction and wrap it with a gradient-capable estimator.
4. For preprocessing pipelines, remember that non-differentiable defences can hide gradients; use adaptive or black-box checks before claiming robustness.

## Adversarial samples exceed the expected range

Symptoms:

- `x_adv.min()` or `x_adv.max()` is outside the data range.
- Images look saturated or invalid.
- Budgets such as `eps=8` are used on `[0, 1]` data.

Actions:

1. Set estimator `clip_values` to the raw input range, e.g. `(0.0, 1.0)` for normalized images.
2. Match attack budgets to that same range: `eps=8/255`, `eps_step=2/255` for common normalized-image PGD.
3. Assert `np.max(np.abs(x_adv - x)) <= eps + tolerance` for `L_inf` attacks.
4. If the estimator uses `preprocessing=(mean, std)`, keep `clip_values` in the original input scale, not the standardized scale.

## Channel order or input shape is wrong

Symptoms:

- PyTorch attack receives `NHWC` data for a classifier built with `channels_first=True`.
- Preprocessor output shape differs unexpectedly.
- Patch shape is rejected.

Actions:

1. Confirm estimator `input_shape` excludes the batch dimension.
2. For PyTorch image workflows, prefer `NCHW` and `input_shape=(C, H, W)` with `channels_first=True`.
3. For NumPy image preprocessors used directly, default `channels_first=False` means `NHWC`.
4. Align `patch_shape` and masks with the estimator channel convention.
5. Do not silently transpose only the attack input; transpose training, prediction, labels, masks, and patch geometry consistently.

## Targeted attack does not move toward the target

Symptoms:

- A targeted attack runs but predictions do not change toward target classes.
- The target label equals the original label.
- Labels are class indices for one component and one-hot for another.

Actions:

1. For `targeted=True`, pass target labels as `y` to `generate`; do not pass the original labels.
2. Use one-hot labels unless the estimator workflow is known to use class indices.
3. Verify every target differs from the current/source label.
4. Increase `max_iter` or `eps` only after shape, clipping, and label semantics are correct.
5. Start with a tiny batch and inspect `np.argmax(classifier.predict(x_adv), axis=1)`.

## Query attack is too slow

Symptoms:

- HopSkipJump, BoundaryAttack, SignOPT, ZOO, SimBA, SquareAttack, or GRAPHITE runs for too long.
- Runtime scales unexpectedly with image size or class count.

Actions:

1. Start with one or two samples.
2. Lower `max_iter`, `max_eval`, `init_eval`, `init_size`, `query_limit`, `sample_size`, `num_trial`, or `nb_parallel` depending on the attack.
3. Use `batch_size=1` if prediction memory spikes.
4. Verify success/failure criteria on tiny data before expanding budgets.
5. For physical attacks, reduce transform samples and patch search settings before increasing image size.

## Memory spikes during PGD/AutoAttack/Carlini/patch optimization

Symptoms:

- Process is killed or raises out-of-memory errors.
- Runtime grows with `max_iter`, `num_random_init`, `binary_search_steps`, or patch transform counts.

Actions:

1. Reduce `batch_size` first.
2. Reduce `max_iter`, `num_random_init`, `binary_search_steps`, or transform counts.
3. Use CPU smoke settings before running GPU-size workloads.
4. Avoid AutoAttack until a single PGD/FGM smoke succeeds.
5. Disable summary logging during smoke checks.

## Physical patch geometry fails

Symptoms:

- `AdversarialPatch` rejects `patch_shape`, `scale_min`, `scale_max`, or `patch_type`.
- `apply_patch` with `mask` changes the wrong region or fails to broadcast.
- Patch appears in an impossible location or covers the full image unintentionally.

Actions:

1. Keep `0 <= scale_min < scale_max <= 1`.
2. Ensure `patch_shape` follows channel convention: often `(C, H, W)` for PyTorch and `(H, W, C)` for channel-last workflows.
3. Ensure masks are boolean or numeric arrays broadcastable to the input or per-sample image shape.
4. Use `patch_location` only when supported by the concrete patch class.
5. Validate one call to `apply_patch` before running `generate` for many iterations.
6. Treat object-detector and specialized physical attacks as outside the selected runnable scope unless the user explicitly expands backend coverage.

## Standardisation or preprocessing dtype errors

Symptoms:

- Standardisation rejects unsigned integer input.
- Output contains unexpected large values.
- Labels disappear after direct preprocessor calls.

Actions:

1. Convert inputs to `np.float32` before `StandardisationMeanStd` or attack generation.
2. Use mean and std values broadcastable to the input shape.
3. Remember direct preprocessors return `(x_processed, y_processed_or_same)`.
4. For sample-only preprocessors, verify `y_processed is y` or values are unchanged.
5. Use the correct import for standardisation: `art.preprocessing.standardisation_mean_std.numpy.StandardisationMeanStd`.

## Gaussian augmentation parameter conflicts

Symptoms:

- `GaussianAugmentation` raises an error about `augmentation`, `apply_fit`, or `apply_predict`.

Actions:

1. If `augmentation=True`, keep `apply_fit=True`.
2. Do not set both `apply_fit=False` and `apply_predict=False` for an active augmentation.
3. Use non-negative `ratio` and valid two-element increasing `clip_values`.
4. For prediction-time noise without dataset growth, set `augmentation=False` deliberately.

## Feature squeezing, thermometer encoding, or clipping errors

Symptoms:

- Errors mention invalid `clip_values`, negative bit depth, or invalid `num_space`.
- Downstream estimator gets unexpected feature dimensions after thermometer encoding.

Actions:

1. `clip_values` must be a two-element tuple/array with min strictly less than max.
2. `FeatureSqueezing.bit_depth` must be a positive integer no greater than 64.
3. `ThermometerEncoding.num_space` must be positive and changes the encoded feature representation.
4. After dimension-changing preprocessing, re-check estimator `input_shape` and training data shape.

## Summary writer/logging confusion

Symptoms:

- Attack creates unexpected run logs.
- User expects SummaryWriter output to be a robustness metric.

Actions:

1. Keep `summary_writer=False` in smoke checks and scripts.
2. If enabled, pass an explicit user-controlled directory or SummaryWriter object.
3. Treat logs as diagnostics only; route metric interpretation, security curves, and certification to the evaluation/certification sub-skill.
