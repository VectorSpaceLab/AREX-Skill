# Install and Inspect

Use this page when you need to verify that BoxMOT is installed correctly, the CLI is available, and the public API imports cleanly.

## Public install

```bash
pip install boxmot
boxmot --help
python -c "import boxmot; print(boxmot.__version__)"
```

## Source-checkout install

If you are working from a source checkout and want the broader development stack:

```bash
uv sync --all-extras --all-groups
uv run python -m boxmot.engine.cli --help
uv run python -c "import boxmot; print(boxmot.__version__)"
```

Keep runtime guidance public and reproducible. Do not mention temporary env names, private prefixes, or local activation commands in the generated skill files.

## What to verify

- `import boxmot` succeeds
- `boxmot --help` prints the top-level mode list
- `boxmot.track`, `boxmot.generate`, `boxmot.eval`, `boxmot.tune`, `boxmot.research`, `boxmot.train`, `boxmot eval-reid`, `boxmot compare-reid`, and `boxmot export` appear in CLI help
- the installed package version is readable through `boxmot.__version__`
- optional extras are only installed when the workflow needs them

## Relevant extras

- `yolo` for detector-backed tracking and replay
- `evolve` for tuning
- `research` for the GEPA workflow
- `onnx`, `openvino`, and `tflite` for ReID export targets

## Minimal safety check

If a future agent needs one quick sanity test, `boxmot --help` plus `python -c "import boxmot; print(boxmot.__version__)"` is the shortest useful check.
