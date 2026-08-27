# Troubleshooting conversion and compilation

## Quick decision table

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Conversion cannot start because a model file is missing | SketchCode requires both model JSON and HDF5 weights | Stop and ask for the missing file. Use the parent asset helper when available. Do not try to run with only one artifact. |
| `ValueError: Image is not a png!` | Single-image sampler checks whether the filename contains `.png` | Rename/provide a real PNG file. Do not pass JPG/PDF/SVG unless the user first converts it to PNG. |
| OpenCV read/convert error during preprocessing | File is corrupt, not a readable image, or has an unexpected format despite its name | Validate with an image tool, re-export as PNG, then rerun. |
| Unsupported style fails with a path/`None`-like error | `get_stylesheet` only handles `default`, `facebook`, `airbnb` and otherwise returns no path | Validate style before calling conversion. Ask the user to choose one of the supported styles. |
| `.gui` is written but `.html` is missing | Compiler returned `HTML Parsing Error` | Use `scripts/compile_tiny_dsl.py` to check tokens/braces/style. Keep the `.gui` for debugging. |
| `HTML Parsing Error` | Unknown DSL token or a render failure; often unbalanced braces or a token absent from the style mapping | Compare tokens against [DSL and styles](dsl-and-styles.md). Fix unknown tokens or braces, then compile again. |
| TensorFlow/Keras import error before `--help` | Conversion scripts import legacy ML packages at module import time | Use a compatible legacy environment or limit work to the bundled compiler helper until the runtime is prepared. |
| OpenCV/Keras/Pillow version conflict | Requirements pin vintage packages | Do not mutate a modern application environment; prepare an isolated runtime for SketchCode. |
| Batch conversion stops for some images but continues | Batch mode catches per-image exceptions and continues | Review printed per-image errors and generated count; rerun failed PNGs after fixing inputs/assets. |
| Output folder contains stale files | The CLI creates folders but does not clean existing outputs | Use a fresh output folder or remove stale `.gui`/`.html` files before rerunning. |
| BLEU flag prints nothing | `--print_bleu_score` was not `1`, or original GUI path/folder was not supplied | Provide the original `.gui` path/folder or run standalone evaluation. Route details to `evaluation`. |

## Missing model JSON or weights

Conversion requires both files:

- Model architecture JSON, commonly `model_json.json`.
- Matching HDF5 weights, commonly `weights.h5`.

Common user case: they have `weights.h5` but not `model_json.json`. This is not enough; Keras needs the JSON architecture before it can load weights. Ask the user to supply the matching JSON or route to the parent asset helper if pretrained assets are allowed.

Do not silently start training as a workaround. Training requires a paired dataset and belongs to `training-data`.

## Invalid or non-PNG input

The sampler validates the filename by checking for `.png`. It does not accept a generic image path. If the user has a sketch as JPG, PDF, SVG, clipboard image, or screenshot without a `.png` suffix:

1. Convert/export it to PNG first.
2. Confirm OpenCV can read it.
3. Use the PNG path in `--png_path` or place it in the batch PNG directory.

## Unsupported style

Supported values are exactly:

- `default`
- `facebook`
- `airbnb`

The historical compiler does not raise a friendly `unsupported style` exception. Unsupported values can cause a bad path/`None` error while opening the style mapping. Validate before running conversion or compilation.

## Debugging `HTML Parsing Error`

Use the helper from this sub-skill directory:

```sh
python scripts/compile_tiny_dsl.py --style default --tokens '<START> row { single { big-title , text , btn-orange } } <END>'
```

Then test the user's token string:

```sh
python scripts/compile_tiny_dsl.py --style default --tokens "$GUI_TOKENS"
```

Likely fixes:

- Add missing `}` braces.
- Remove extra `}` braces.
- Replace unsupported tokens with known mapping keys.
- Add commas between adjacent leaf tokens, such as `big-title , text , btn-orange`, when checking behavior against the original compiler.
- Preserve `<START>` and `<END>` when calling the original compiler directly.
- Use a supported style.

If a model-generated `.gui` contains unknown tokens repeatedly, the issue may be model/data quality rather than compilation. Route training or dataset questions to `training-data`.

## TensorFlow/Keras/OpenCV import problems

The conversion path depends on legacy packages pinned by the repository, including TensorFlow 1.x, Keras 2.1.x, OpenCV 3.3.x, old NumPy, and old Pillow. Symptoms may include:

- `ModuleNotFoundError: keras` or `tensorflow`.
- TensorFlow 1.x incompatibility with a modern Python interpreter.
- OpenCV import ABI errors.
- Keras/TensorFlow API mismatch.

Safe response:

1. Do not install these pins into an unrelated modern environment.
2. Use a dedicated SketchCode runtime environment.
3. Verify imports before attempting model conversion.
4. If runtime preparation is blocked, still use the bundled compiler helper for `.gui` debugging because it does not need TensorFlow/Keras.

## Output folder behavior

- Conversion CLIs create the output folder if it is missing.
- They do not clean existing output files.
- The `.gui` file is written immediately after GUI generation.
- The `.html` file is only written when compilation succeeds.
- Batch mode may leave a mixture of successful `.gui`/`.html` pairs and failed/skipped inputs.

For reproducible runs, create a new output folder per run.

## Optional BLEU routing

Conversion exposes `--print_bleu_score`, but BLEU is not a conversion prerequisite.

- Single conversion needs `--original_gui_filepath` for sentence BLEU.
- Batch conversion needs `--original_guis_filepath` for corpus BLEU.
- File pairing, token normalization, button-color normalization, and BLEU warnings belong to `evaluation`.

If the user only wants HTML output, leave BLEU disabled.
