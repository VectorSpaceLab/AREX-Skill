# Cross-cutting troubleshooting

## Start with safe diagnostics

```sh
python scripts/sketch_code_assets.py --root "$SKETCHCODE_ROOT"
python scripts/check_sketch_code_environment.py --sketchcode-root "$SKETCHCODE_ROOT"
```

Then route to the focused sub-skill:

- Conversion/model inference: `sub-skills/conversion-inference/SKILL.md`
- Training/data/model architecture: `sub-skills/training-data/SKILL.md`
- BLEU evaluation: `sub-skills/evaluation/SKILL.md`

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'classes'` | SketchCode is script-style and the runtime `src` directory is not on `PYTHONPATH`. | Use bundled wrappers with `--sketchcode-root` pointing at the runtime checkout, or add the runtime `src` directory to the active Python path. |
| TensorFlow/Keras import fails before argument parsing | The active Python is too new or has incompatible modern Keras/TensorFlow. | Use an isolated legacy Python environment. Do not install the historical pins into a modern project environment. |
| Exact `opencv-python==3.3.0.10` cannot be installed | The old wheel may be unavailable on the configured package index. | Try a nearby legacy OpenCV 3.x wheel in an isolated environment, then run `check_sketch_code_environment.py --image PNG` to prove preprocessing still works. |
| `model_json.json` exists but `weights.h5` is missing, or vice versa | Conversion and fine-tuning require a matched architecture JSON and HDF5 weights file. | Stop before model loading. Use `scripts/sketch_code_assets.py --root ROOT` to check expected locations or ask the user for both files. |
| User asks to download assets but storage/network policy is unclear | Dataset and model files come from external S3 URLs and the dataset archive is large. | Print commands with `scripts/sketch_code_assets.py --print-download-commands`; execute only after user approval. |
| GUI compiler returns `HTML Parsing Error` | Unknown DSL token, unsupported style, unbalanced braces, or generated sequence outside the vocabulary. | Run `sub-skills/conversion-inference/scripts/compile_tiny_dsl.py --style STYLE --tokens '...'` to isolate grammar/style errors. |
| Training deletes unexpected folders | Legacy dataset split deletes/recreates `training_set` and `validation_set` siblings under the parent of `--data_input_path`. | Validate and dry-run with `sub-skills/training-data/scripts/run_training.py` before passing `--run --allow-destructive-split`. |
| BLEU score is unexpectedly low or high | Tokenization, predicted `<START>/<END>` trimming, color/button normalization, or skipped unmatched batch files. | Read `sub-skills/evaluation/references/evaluation-workflow.md` and run the bundled tiny BLEU helper. |

## Legacy dependency isolation

Keep SketchCode's runtime isolated. Its historical pins predate current Python packaging expectations and may conflict with modern ML projects. A working inspection environment has been proven possible with a legacy Python and close OpenCV 3.x substitute, but exact dependency availability depends on the user's package indexes and platform.

## Network and asset policy

The generated skill never downloads data or model files by default. The asset helper only prints/checks:

```sh
python scripts/sketch_code_assets.py --root "$SKETCHCODE_ROOT"
python scripts/sketch_code_assets.py --print-download-commands
```

If downloads are approved, keep downloaded archives, expanded data, and model files outside the generated skill directory. They are runtime assets, not part of the reusable operating graph.

## Source-layout notes

The wrappers accept `--sketchcode-root` because SketchCode did not define package metadata or console entry points. A root is valid when it contains `src/classes/`, or when the provided path itself contains `classes/`. The generated skill's bundled scripts are the stable entry points; avoid relying on paths from the checkout that produced this skill.
