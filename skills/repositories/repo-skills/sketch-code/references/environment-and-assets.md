# Environment and assets

## Purpose

Read this when setting up SketchCode, checking whether a runtime can import the legacy code, or deciding whether to download the public dataset/pretrained model assets. The generated skill keeps downloads opt-in and uses bundled checkers instead of running network scripts by default.

## Runtime shape

SketchCode is a historical script-style repository rather than an installable package with console entry points. Its Python code expects a source layout with a `classes` package under a runtime `src` directory. The bundled wrappers in this skill accept `--sketchcode-root` so future agents can operate on any user-provided SketchCode checkout/runtime without relying on the checkout that produced this skill.

Useful check:

```sh
python scripts/check_sketch_code_environment.py --sketchcode-root "$SKETCHCODE_ROOT"
```

Add optional files when diagnosing a real conversion setup:

```sh
python scripts/check_sketch_code_environment.py \
  --sketchcode-root "$SKETCHCODE_ROOT" \
  --model-json-file "$MODEL_JSON" \
  --model-weights-file "$MODEL_WEIGHTS" \
  --image "$PNG_PATH"
```

## Dependency expectations

The repository documents these vintage runtime pins:

| Package | Historical pin | Notes |
| --- | --- | --- |
| Keras | `2.1.2` | Uses APIs such as `fit_generator`, `RMSprop(lr=...)`, and `ModelCheckpoint(period=...)`. |
| TensorFlow | `1.4.0` | Old TensorFlow 1.x runtime; modern Python versions usually will not work. |
| OpenCV | `opencv-python==3.3.0.10` | That exact wheel may be unavailable on modern indexes; use the closest compatible legacy wheel only after verifying image preprocessing. |
| NumPy | `1.13.1` | Old ABI expectations; keep isolated from modern projects. |
| NLTK | `3.2.5` | Used for sentence/corpus BLEU; no corpus download is needed for the distilled BLEU path. |
| Pillow, h5py, matplotlib, tqdm, SciPy | historical pins in requirements | Needed by preprocessing/model/runtime imports. |

Prefer an isolated legacy Python environment. Do not install these pins into a modern project environment unless the user explicitly accepts the risk.

## External asset manifest

Use the bundled manifest checker first:

```sh
python scripts/sketch_code_assets.py --root "$SKETCHCODE_ROOT"
```

Expected assets:

| Asset | Default location under a runtime root | Purpose |
| --- | --- | --- |
| Dataset archive | `data/all_data.zip` | Synthetic paired PNG/GUI dataset archive used for training examples. |
| Model JSON | `bin/model_json.json` | Keras model architecture required for conversion and fine-tuning. |
| Model weights | `bin/weights.h5` | Keras HDF5 weights matching the model JSON. |

To print human-reviewed download commands without executing them:

```sh
python scripts/sketch_code_assets.py --print-download-commands
```

Do not download automatically in an agent workflow unless the user approves network access, storage use, and the large dataset/model side effects.

## What each workflow needs

| Workflow | Required runtime | Required assets |
| --- | --- | --- |
| GUI DSL compiler debugging | Only the bundled `compile_tiny_dsl.py` helper for fallback checks; optional SketchCode runtime for original compiler comparison. | None. |
| Single/batch PNG conversion | Legacy SketchCode runtime plus Keras/TensorFlow/OpenCV imports. | Both model JSON and weights; PNG input(s). |
| Training/fine-tuning | Legacy SketchCode runtime plus TensorFlow/Keras/OpenCV/NumPy/Pillow stack. | Paired `.png`/`.gui` dataset; optional model JSON and weights for fine-tuning. |
| BLEU evaluation | NLTK-compatible Python for the historical evaluator; bundled helper has a fallback exact-match smoke path. | Original and predicted `.gui` files. |

## Verification sequence

1. Check assets with `scripts/sketch_code_assets.py`.
2. Check dependency and runtime imports with `scripts/check_sketch_code_environment.py`.
3. For conversion readiness, run `sub-skills/conversion-inference/scripts/compile_tiny_dsl.py` before model inference.
4. For training readiness, run `sub-skills/training-data/scripts/validate_training_dataset.py` before any training command.
5. For evaluation readiness, run `sub-skills/evaluation/scripts/evaluate_tiny_gui_bleu.py` before comparing real folders.
