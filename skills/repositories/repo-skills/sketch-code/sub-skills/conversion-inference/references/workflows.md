# Conversion workflows

This reference distills SketchCode's conversion behavior so future agents do not need to rediscover the public flags or compiler behavior. Use the user's own SketchCode project/runtime and assets; do not assume example images, downloaded data, or pretrained files are already present.

## Required inputs

| Need | Required value | Notes |
| --- | --- | --- |
| Model architecture | Keras JSON file, commonly named `model_json.json` | Loaded with Keras `model_from_json`; conversion cannot run with weights alone. |
| Model weights | HDF5 file, commonly named `weights.h5` | Loaded with `load_weights`; must match the model JSON architecture. |
| Single image | One filename ending in `.png` | The sampler derives the output sample id from the PNG basename. |
| Batch images | Directory containing one or more filenames with `.png` | Batch mode sorts directory entries and processes names containing `.png`. |
| Output folder | Writable directory path | The CLIs create it if it does not exist. |
| Style | `default`, `facebook`, or `airbnb` | Validate before calling the compiler. Unsupported names can fail as a bad/`None` style path. |

## Single PNG to GUI and HTML

Use the bundled wrapper so validation and troubleshooting stay inside this generated skill. Point `--sketchcode-root` at the SketchCode runtime checkout you are operating on, or omit it only when `classes.inference.Sampler` is already importable in the active Python environment.

```sh
python sub-skills/conversion-inference/scripts/run_conversion.py single \
  --sketchcode-root "$SKETCHCODE_ROOT" \
  --png-path "$PNG_PATH" \
  --output-folder "$OUTPUT_FOLDER" \
  --model-json-file "$MODEL_JSON" \
  --model-weights-file "$MODEL_WEIGHTS" \
  --style default \
  --print-generated-output 1
```

Expected behavior:

1. The script creates `OUTPUT_FOLDER` when missing.
2. `Sampler` loads the vocabulary, model JSON, and weights.
3. The PNG is preprocessed into a normalized `(256, 256, 3)` array before model prediction.
4. The generated GUI token sequence is written as `<sample_id>.gui`, where `sample_id` is the PNG basename without `.png`.
5. The GUI tokens are compiled to HTML using the selected style. `<sample_id>.html` is written only when compilation does not return `HTML Parsing Error`.

## Batch PNG directory to GUI and HTML

```sh
python sub-skills/conversion-inference/scripts/run_conversion.py batch \
  --sketchcode-root "$SKETCHCODE_ROOT" \
  --pngs-path "$PNGS_FOLDER" \
  --output-folder "$OUTPUT_FOLDER" \
  --model-json-file "$MODEL_JSON" \
  --model-weights-file "$MODEL_WEIGHTS" \
  --style default
```

Expected behavior:

- Batch mode creates the output folder if needed.
- It sorts all entries in `PNGS_FOLDER` and attempts conversion for filenames containing `.png`.
- It prints `Generated code for N images` after the loop.
- Per-image generation exceptions are caught and printed, then the loop continues to the next PNG.
- Each successful image follows the same `<sample_id>.gui` and optional `<sample_id>.html` output convention as single-image mode.

## Optional BLEU during conversion

The conversion CLIs can print BLEU if the user provides original `.gui` references, but metric interpretation belongs to the `evaluation` sub-skill.

Single-image route:

```sh
python sub-skills/conversion-inference/scripts/run_conversion.py single \
  --sketchcode-root "$SKETCHCODE_ROOT" \
  --png-path "$PNG_PATH" \
  --output-folder "$OUTPUT_FOLDER" \
  --model-json-file "$MODEL_JSON" \
  --model-weights-file "$MODEL_WEIGHTS" \
  --print-bleu-score 1 \
  --original-gui-filepath "$ORIGINAL_GUI"
```

Batch route:

```sh
python sub-skills/conversion-inference/scripts/run_conversion.py batch \
  --sketchcode-root "$SKETCHCODE_ROOT" \
  --pngs-path "$PNGS_FOLDER" \
  --output-folder "$OUTPUT_FOLDER" \
  --model-json-file "$MODEL_JSON" \
  --model-weights-file "$MODEL_WEIGHTS" \
  --print-bleu-score 1 \
  --original-guis-filepath "$ORIGINAL_GUIS_FOLDER"
```

If the user asks what the BLEU value means, how files are paired, or why button colors are normalized, route to `evaluation`.

## Compile/debug an existing `.gui` token string

Use the bundled helper first for syntax and token sanity checks, especially when the user reports `HTML Parsing Error`.

From this sub-skill directory:

```sh
python scripts/compile_tiny_dsl.py \
  --style default \
  --tokens '<START> header { btn-active , btn-inactive } row { single { big-title , text , btn-orange } } <END>'
```

What the helper can diagnose without model assets:

- Unsupported style names before SketchCode hits the bad style path behavior.
- Unknown DSL tokens that the mapping cannot render.
- Unbalanced braces or a bare `{` without a parent token.
- Whether a tiny known-good DSL can produce HTML.

When the user provides a SketchCode project root and wants to compare with the original compiler, the helper supports an optional `--repo-root` argument. Its fallback mode remains self-contained and does not require TensorFlow/Keras.

## Style selection workflow

1. Ask whether the user wants the historical bootstrap-like `default` output or the alternate color presets `facebook` / `airbnb`.
2. Validate the selected style string exactly.
3. Pass the style with `--style STYLE` to conversion CLIs or `--style STYLE` to the helper.
4. If an unsupported style is requested, do not run conversion; explain the supported set and ask the user to choose one.
