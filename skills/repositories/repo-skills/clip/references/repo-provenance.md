# Repo Provenance

## Source Snapshot

- Source project: OpenAI CLIP.
- Public remote: `https://github.com/openai/CLIP.git`.
- Branch at generation: `main`.
- Commit at generation: `d05afc436d78f1c48dc0dbf8e5980a9d471f35f6`.
- Exact tag at generation: none detected.
- Package distribution/import: `clip`.
- Package version observed through installed metadata: `1.0`.
- Working tree state: dirty after skill generation because this workflow created untracked `skills/` outputs; no pre-existing tracked source-code changes were observed before generated artifacts were written.

## Evidence Paths

The skill was generated from these relative repository paths:

- `setup.py`
- `requirements.txt`
- `MANIFEST.in`
- `README.md`
- `model-card.md`
- `hubconf.py`
- `clip/__init__.py`
- `clip/clip.py`
- `clip/model.py`
- `clip/simple_tokenizer.py`
- `clip/bpe_simple_vocab_16e6.txt.gz`
- `data/prompts.md`
- `data/country211.md`
- `data/rendered-sst2.md`
- `data/yfcc100m.md`
- `notebooks/Interacting_with_CLIP.ipynb`
- `notebooks/Prompt_Engineering_for_ImageNet.ipynb`
- `tests/test_consistency.py`

## Verified Runtime Facts

- `clip.available_models()` returns nine released model names: `RN50`, `RN101`, `RN50x4`, `RN50x16`, `RN50x64`, `ViT-B/32`, `ViT-B/16`, `ViT-L/14`, and `ViT-L/14@336px`.
- `clip.load(name, device=..., jit=False, download_root=None)` accepts a released model name or local checkpoint path and returns `(model, preprocess)`.
- `clip.tokenize(texts, context_length=77, truncate=False)` returns a two-dimensional token tensor and raises on overlong text unless truncation is enabled.
- No console scripts are exposed by package metadata; Torch Hub entrypoints are available through the package's hub interface.

## Refresh Signals

Refresh this skill if any of these change:

- New model names, checkpoint URLs, or cache/checksum behavior in `clip/clip.py`.
- Public signatures or behavior for `available_models`, `load`, `tokenize`, `encode_image`, `encode_text`, or `model(image, text)`.
- Prompt template resources, notebooks, README examples, model-card safety guidance, or dataset download notes.
- Package metadata, dependency requirements, or Torch Hub entrypoint behavior.
