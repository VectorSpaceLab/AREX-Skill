# Conversion, Transfer, Foundation, and Interpretation Routing

This reference covers advanced Chemprop workflow decisions that often sit next to uncertainty work but are not themselves basic training or prediction mechanics.

## Model Conversion

Chemprop provides `chemprop convert` for older model artifacts:

```bash
chemprop convert \
  --conversion v1_to_v2 \
  --input-path old_v1_model.pt \
  --output-path converted_v2.pt
```

```bash
chemprop convert \
  --conversion v2_0_to_v2_1 \
  --input-path old_v2_0_model.pt \
  --output-path converted_v2_1.pt
```

Rules:

- `--conversion` choices are `v1_to_v2` and `v2_0_to_v2_1`; default is `v1_to_v2`.
- `--input-path` is required and should be a model `.pt` checkpoint file in the older format.
- `--output-path` must end in `.pt`.
- If `--output-path` is omitted, Chemprop writes a default name in the current working directory using the input stem plus `_v2.pt` or `_v2_1.pt`.
- Converted v1 models must be used with v1-style atom featurization during later prediction or fingerprinting: add `--multi-hot-atom-featurizer-mode v1`.

Prediction after v1 conversion:

```bash
chemprop predict \
  --test-path test.csv \
  --model-path converted_v2.pt \
  --output converted_preds.csv \
  --multi-hot-atom-featurizer-mode v1
```

Chemprop prediction can sometimes detect a v1 default featurizer mismatch and warn that it is switching to the v1 default featurizer. Prefer passing the featurizer flag explicitly so production commands are reproducible.

## Conversion and Uncertainty

Conversion does not invent uncertainty semantics. After converting a model, choose uncertainty flags based on the converted model's original task/predictor family:

- Plain v1 regression converted to v2: use ordinary prediction or ensemble/dropout if appropriate; do not assume MVE/evidential outputs exist.
- MVE/evidential/quantile-style artifacts: only use matching uncertainty estimators if the converted predictor output has the expected shape.
- Classification artifacts: use classification or Dirichlet uncertainty only if the model was trained for the compatible task family.

When in doubt, first run `chemprop predict --uncertainty-method none` on a tiny CSV with the correct featurizer and schema, then layer uncertainty flags after the base artifact loads cleanly.

## Transfer Learning Routing

Transfer learning belongs to training command construction, but route here when the transfer choice affects advanced workflows such as hpopt or uncertainty model families.

Key flags:

- `--checkpoint`: load weights from a `.ckpt`, `.pt`, directory of `.pt` files, or list of model paths/directories.
- `--freeze-encoder`: freeze the message-passing layer from `--checkpoint`.
- `--frzn-ffn-layers <n>`: freeze the first `n` FFN layers from `--checkpoint`; Chemprop expects `--freeze-encoder` when used with `--checkpoint`.
- `--from-foundation <name-or-path>`: initialize message passing from a foundation model name or a local model file.

Validation rules to remember:

- `--checkpoint` and `--from-foundation` are mutually exclusive.
- `--freeze-encoder` requires `--checkpoint`.
- `--frzn-ffn-layers` requires `--checkpoint` or the deprecated `--model-frzn`; with `--checkpoint`, pair it with `--freeze-encoder`.
- The deprecated `--model-frzn` should be replaced with `--checkpoint --freeze-encoder` patterns.

Transfer example for an uncertainty-capable target task:

```bash
chemprop train \
  --data-path small_regression.csv \
  --task-type regression-mve \
  --checkpoint pretrained.pt \
  --freeze-encoder \
  --frzn-ffn-layers 1 \
  --output-dir runs/transfer_mve
```

Then use prediction-time uncertainty flags compatible with `regression-mve`.

## Foundation Model Routing

Foundation model initialization uses `--from-foundation`. It can accept a known foundation model name or a local model file. Known foundation names may require network access or a populated local cache. Local foundation paths avoid downloads but must be readable model files compatible with Chemprop loading.

Important routing notes:

- Foundation initialization affects training, not prediction-time uncertainty directly.
- Hpopt prunes message-passing search parameters when `--from-foundation` is set.
- Foundation starts can impose featurizer constraints. For CheMeleon, use V2 atom featurization; do not combine it with a different multi-hot atom featurizer mode.
- Some message-passing architecture flags can be ignored because the message-passing layer comes from the foundation model.

Foundation example:

```bash
chemprop train \
  --data-path small_regression.csv \
  --task-type regression \
  --from-foundation CheMeleon \
  --output-dir runs/foundation_regression
```

Foundation plus hpopt example:

```bash
chemprop hpopt \
  --data-path small_regression.csv \
  --task-type regression \
  --from-foundation CheMeleon \
  --search-parameter-keywords basic learning_rate \
  --raytune-num-samples 12 \
  --hpopt-save-dir hpopt/foundation
```

Expect the effective hpopt search space to exclude foundation-owned message-passing parameters.

## Interpretation Workflow Triage

Interpretation examples in Chemprop demonstrate advanced analysis workflows such as Monte Carlo tree search over molecular changes. Route interpretation requests by the user's actual goal:

- If the user asks for attribution/interpretation strategy, data preparation, or how to connect trained Chemprop models to an interpretation loop, stay in this sub-skill for triage and then route to the most relevant command/API sub-skill.
- If the user needs to run existing model predictions inside an interpretation loop, use `prediction-fingerprints` for `chemprop predict` mechanics and model artifact loading.
- If the user needs custom Python loops, model calls, or internal representations, use `python-api-modeling`.
- If the user needs uncertainty-aware interpretation, first ensure the prediction path can emit calibrated uncertainty, then decide how the interpretation loop consumes point predictions versus uncertainty columns.

Practical sequence for uncertainty-aware interpretation:

1. Validate the model on a small CSV with `--uncertainty-method none`.
2. Add the compatible uncertainty estimator and confirm `_unc` columns appear.
3. Add calibration only after matching calibration inputs and labels are available.
4. Feed the resulting prediction and uncertainty columns to the interpretation or ranking logic.
5. Keep interpretation-specific scripts separate from the generated skill unless the user explicitly asks to build reusable runtime tooling.

## Advanced Routing Summary

- Convert first when the artifact format is old; then predict with the correct featurizer.
- Transfer/foundation choices happen at training time; uncertainty flags happen at prediction time.
- Hpopt can tune the training run that creates an uncertainty-capable model, but hpopt does not calibrate or evaluate uncertainty.
- Interpretation generally consumes model outputs; choose the appropriate prediction or Python API path before discussing interpretation metrics.
