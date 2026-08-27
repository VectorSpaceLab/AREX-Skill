# CLI reference

SketchCode's historical source tree had separate conversion scripts for one PNG and a directory of PNGs. This generated skill bundles `scripts/run_conversion.py` as the validated replacement: it imports the same `Sampler` runtime from a user-supplied SketchCode root or active Python path, validates assets first, and keeps help/error handling self-contained. Both modes require a Keras model architecture JSON and matching HDF5 weights.

## Single-image conversion flags

Command shape:

```sh
python sub-skills/conversion-inference/scripts/run_conversion.py single \
  --sketchcode-root SKETCHCODE_ROOT \
  --png-path INPUT.png \
  --output-folder OUT_DIR \
  --model-json-file MODEL.json \
  --model-weights-file WEIGHTS.h5 \
  [--style default|facebook|airbnb] \
  [--print-generated-output 0|1] \
  [--print-bleu-score 0|1 --original-gui-filepath ORIGINAL.gui]
```

| Flag | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--sketchcode-root` | no | import from current Python path | Checkout/runtime root containing `src/classes/`, or a `src` directory containing `classes/`. |
| `--png-path` | yes | none | PNG filepath to convert into GUI DSL and HTML. Filename must end with `.png`; otherwise the wrapper stops before model loading. |
| `--output-folder` | yes | none | Directory where generated `.gui` and compiled `.html` outputs are saved. Created when missing. |
| `--model-json-file` | yes | none | Trained model architecture JSON loaded through Keras `model_from_json`. |
| `--model-weights-file` | yes | none | Trained model weights loaded through Keras `load_weights`. |
| `--style` | no | `default` | Style mapping used by the compiler. Supported values are `default`, `facebook`, and `airbnb`. |
| `--print-generated-output` | no | `1` | Prints generated GUI tokens and compiled HTML when set to `1`. |
| `--print-bleu-score` | no | `0` | Prints sentence BLEU when set to `1` and `--original-gui-filepath` is supplied. Route BLEU interpretation to `evaluation`. |
| `--original-gui-filepath` | no | `None` | Original `.gui` reference for optional sentence BLEU. |

## Batch conversion flags

Command shape:

```sh
python sub-skills/conversion-inference/scripts/run_conversion.py batch \
  --sketchcode-root SKETCHCODE_ROOT \
  --pngs-path PNG_FOLDER \
  --output-folder OUT_DIR \
  --model-json-file MODEL.json \
  --model-weights-file WEIGHTS.h5 \
  [--style default|facebook|airbnb] \
  [--print-bleu-score 0|1 --original-guis-filepath ORIGINAL_GUI_FOLDER]
```

| Flag | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--sketchcode-root` | no | import from current Python path | Checkout/runtime root containing `src/classes/`, or a `src` directory containing `classes/`. |
| `--pngs-path` | yes | none | Folder containing PNG inputs. Batch mode processes sorted filenames where the name contains `.png`. |
| `--output-folder` | yes | none | Directory where generated `.gui` and compiled `.html` files are saved. Created when missing. |
| `--model-json-file` | yes | none | Trained model architecture JSON. Required even if weights exist. |
| `--model-weights-file` | yes | none | Trained model weights. Required even if JSON exists. |
| `--print-bleu-score` | no | `0` | Prints corpus BLEU when set to `1` and `--original-guis-filepath` is supplied. Route details to `evaluation`. |
| `--original-guis-filepath` | no | `None` | Folder of original `.gui` references for optional corpus BLEU. Filenames should match generated `.gui` names. |
| `--style` | no | `default` | Style mapping used by the compiler. Supported values are `default`, `facebook`, and `airbnb`. |

## Output naming and folder behavior

- `sample_id` is derived from the input PNG basename before `.png`.
- The generated GUI is written to `<output_folder>/<sample_id>.gui` after model prediction.
- The compiler writes `<output_folder>/<sample_id>.html` only when compilation succeeds.
- If compilation returns `HTML Parsing Error`, the `.gui` remains useful for debugging but `.html` is not written.
- Existing files with the same names may be replaced; choose a fresh output folder when preserving old results matters.
- Batch conversion catches per-image exceptions, prints an error, and continues.

## Model and asset prerequisites

Conversion cannot run without both model artifacts:

1. Model JSON, commonly `model_json.json`.
2. Matching Keras weights, commonly `weights.h5`.

If either artifact is missing, stop before running conversion. Use the parent `sketch-code` asset checker/helper when available, or ask the user to provide the missing file. Do not silently switch to training; training is a separate workflow.

## PNG preprocessing fact

Before prediction, the sampler uses SketchCode's image preprocessor:

1. Read PNG with OpenCV.
2. Convert BGR to grayscale.
3. Apply adaptive thresholding.
4. Repeat the thresholded image into three channels.
5. Resize content to `200 x 200` and place it on a `256 x 256 x 3` white background.
6. Normalize values by dividing by `255`.
7. Assert the final feature shape is `(256, 256, 3)`.

This means input files should be readable by OpenCV and named as PNGs. It also means model predictions are tied to the historical wireframe preprocessing distribution.

## Runtime dependency expectations

The bundled wrapper can print `--help` without TensorFlow/Keras, but actual conversion imports the legacy Keras/TensorFlow/OpenCV stack through SketchCode's `Sampler`. The repository requirements pin vintage versions including Keras `2.1.2`, TensorFlow `1.4.0`, OpenCV `3.3.0.10`, NumPy `1.13.1`, NLTK `3.2.5`, Pillow `4.3.0`, and related packages. Modern Python environments may fail during conversion import or model loading; run the root environment checker before diagnosing model quality.
