# Repo provenance

This file records the source snapshot used to create the self-contained SpeechBrain repo skill.

## Source snapshot

- Repository: SpeechBrain
- Public remote: `https://github.com/speechbrain/speechbrain.git`
- Branch: `develop`
- Commit: `e5cb1f65b940634215650aa1171e0440d0808123`
- Exact tag at commit: none detected
- Package version from source metadata: `1.1.0`
- Working tree baseline: the source checkout was clean before this skill and its review artifacts were generated. Generated files under `skills/` are output artifacts, not source evidence.

## Package metadata

- Distribution name: `speechbrain`
- Import module: `speechbrain`
- Python requirement in package metadata: `>=3.8.1`
- Required package data: `speechbrain/version.txt`, `speechbrain/log-config.yaml`
- Core dependency families: PyTorch/Torchaudio, HyperPyYAML, NumPy/SciPy, SentencePiece, SoundFile, Hugging Face Hub, requests, tqdm, joblib, packaging.

## Evidence paths used

The generated runtime skill distills information from these relative source paths. Future agents should use them only to decide whether a refresh is needed; runtime instructions are self-contained in the skill tree.

- `pyproject.toml`
- `requirements.txt`
- `README.md`
- `docs/installation.md`
- `docs/experiment.md`
- `docs/audioloading.rst`
- `docs/multigpu.md`
- `docs/guidance.md`
- `docs/tutorials/basics.rst`
- `docs/tutorials/advanced.rst`
- `docs/tutorials/preprocessing.rst`
- `docs/tutorials/tasks.rst`
- `docs/tutorials/nn.rst`
- `speechbrain/__init__.py`
- `speechbrain/core.py`
- `speechbrain/inference/*.py`
- `speechbrain/dataio/*.py`
- `speechbrain/augment/*.py`
- `speechbrain/processing/*.py`
- `speechbrain/lobes/*.py`
- `speechbrain/nnet/*.py`
- `speechbrain/decoders/*.py`
- `speechbrain/tokenizers/*.py`
- `speechbrain/utils/*.py`
- `recipes/`
- `templates/`
- `tests/README.md`
- `tests/unittests/`
- `tests/integration/`
- `tests/recipes/*.csv`
- `tests/recipes/README.md`
- `tests/utils/recipe_tests.py`
- `tests/consistency/`
- `.github/workflows/*.yml`
- `tools/compute_wer.py`
- `tools/g2p.py`
- `tools/profiling/`
- `tools/readme_builder.py`

## Refresh triggers

Refresh this skill if any of the following change materially:

- `speechbrain.inference` class names, `from_hparams`, `Pretrained.load_audio`, or method signatures.
- `Brain`, `RunOptions`, HyperPyYAML command-line override behavior, or recipe launch conventions.
- `audio_io` backend assumptions, especially the SoundFile wrapper API.
- Recipe layout, `tests/recipes` CSV fields, template structure, or debug flag conventions.
- Checkpoint/pretrainer APIs, metric-stat APIs, WER/edit-distance utilities, or streaming helpers.
- Repository maintenance commands, CI Python/Torch pins, or docs/performance generation flows.
