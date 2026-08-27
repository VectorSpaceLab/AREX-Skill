# Donut Troubleshooting

Start here for cross-cutting failures. Then use the nearest workflow-specific troubleshooting file for inference, training, or SynthDoG details.

## Import or install failures

### `ModuleNotFoundError: No module named 'donut'`

- Install the package distribution, not the module name alone:
  ```bash
  pip install donut-python
  ```
- Verify the import with:
  ```bash
  python scripts/runtime_smoke.py --check imports --check signatures
  ```
- If using a local clone for development, install it into the active environment with `pip install -e .`; do not rely on the current working directory being the repo root.

### Dependency conflicts after installing modern packages

The original README lists older tested dependencies, while verified skill construction succeeded with modern compatible packages including PyTorch 2.5.1+CUDA 12.4 and Transformers 4.38.2. If imports fail after upgrades:

- check `pip check`;
- keep `torch` and `torchvision` from the same CUDA/CPU build family;
- avoid mixing very old `pytorch-lightning`, `transformers`, `timm`, and `datasets` pins with a modern Python unless you have tested the combination;
- test only the workflow you need: inference does not require every training/SynthDoG dependency.

### `transformers`, `huggingface_hub`, or checkpoint loading errors

- Donut's `from_pretrained` requests the `official` revision for Donut model repositories. If a checkpoint does not have that revision, use a local checkpoint directory or a Donut-compatible repository that does.
- For offline runs, pre-download checkpoints and pass local paths. The inference helper also supports `--local-files-only`.
- Authentication, corporate proxies, or Hub outages can appear as model-loading errors; retry with a local path before changing code.

## CUDA and device failures

### Training fails on CPU or no GPU is found

The original training workflow is GPU-oriented. It configures CUDA/DDP/16-bit behavior and was validated with CUDA available. If `torch.cuda.is_available()` is false:

- do not present CPU as a supported replacement for full training;
- run dataset/config validation first;
- install a CUDA-compatible PyTorch build for the host driver;
- rerun `python scripts/runtime_smoke.py --check cuda --require-cuda`.

### Inference is slow or fails with half precision

- Use CUDA when available for large checkpoints: `model.half(); model.to("cuda")`.
- On CPU, keep the model in float32. Do not call `half()` for CPU inference.
- If the bundled inference helper is used, choose `--device cpu`, `--device cuda`, or `--device auto` explicitly.

## Data and config failures

### `metadata.jsonl` rows fail to load

Each row must be a JSON object with a local image path and a JSON-encoded `ground_truth` string:

```json
{"file_name": "sample.jpg", "ground_truth": "{\"gt_parse\": {\"class\": \"letter\"}}"}
```

Common fixes:

- ensure `file_name` points to an existing image relative to the split directory;
- encode `ground_truth` as a string containing JSON, not as a nested object;
- use `gt_parse` for classification/extraction/text-reading tasks;
- use non-empty `gt_parses` with `{question, answer}` objects for DocVQA;
- run `sub-skills/training/scripts/check_training_config.py --dataset-root <dataset>`.

### Metrics look inverted

- Training validation metric (`val_metric`) is normalized edit distance; lower is better.
- Test/evaluation outputs include TED-based accuracy and F1; higher is better.
- RVL-CDIP uses exact class equality; DocVQA uses answer matching against candidate answers.

## Prompt and output failures

### Empty or malformed prediction JSON

- Confirm the checkpoint and prompt task match: CORD-like checkpoints expect `<s_cord>`, RVL-CDIP expects `<s_rvlcdip>`, and DocVQA expects a question prompt ending with `<s_answer>`.
- If debugging parse behavior, run inference with raw-token output first, then compare the token string to `references/api-reference.md` token rules.
- Custom task names require matching special tokens and training data; changing only the prompt string is not enough.

## Gradio failures

- Use the inference sub-skill launcher and pass an explicit port if the default is occupied.
- Modern Gradio versions may differ from the original demo's API; this skill bundles a current launcher instead of depending on the old source app.
- When launching remotely, bind `--host 0.0.0.0` only when network exposure is intended.

## SynthDoG failures

- `synthtiger`, OpenCV, NumPy, and `pytweening` must be importable for generation.
- Large resources are not bundled. Provide external background images, paper textures, corpus text, and fonts.
- Render configs with `sub-skills/synthdog/scripts/render_config.py` before running `synthtiger`; it checks resource paths before generation.
- If NumPy/OpenCV/imgaug compatibility errors appear, use the SynthDoG sub-skill troubleshooting reference for dependency notes.

## When to refresh this skill

Refresh the repo skill if Donut changes any of these surfaces:

- public exports or signatures in `donut/model.py` or `donut/util.py`;
- demo, training, or evaluation CLI behavior;
- `config/train_*.yaml` field names or task defaults;
- `synthdog/template.py`, elements/layouts, or resource config schema;
- package version, dependency compatibility, or model-loading behavior.
