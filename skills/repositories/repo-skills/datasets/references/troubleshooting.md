# Cross-cutting Troubleshooting

Use this for package-wide failures before switching to a focused sub-skill.

## Install and Import

- Symptom: `ModuleNotFoundError: datasets`. Install with `pip install datasets` in the active Python environment and verify `python -c "import datasets; print(datasets.__version__)"`.
- Symptom: optional media/framework import errors. Install only the needed extra or backend package: `datasets[audio]` for audio decoding, `datasets[vision]` for image/video basics, `datasets[pdfs]` for PDF extraction, `datasets[nibabel]` for NIfTI, or the desired ML framework package.
- Symptom: imports work in one shell but not another. Compare `python -m pip show datasets` and `python -c "import sys; print(sys.executable)"` in the shell that will run the workflow.

## Loading and Network

- For ambiguous local files, provide explicit `data_files`, `split`, and `features` instead of relying on inference.
- For private or gated Hub datasets, authenticate outside code and pass `token=True` or a secure token variable; never paste tokens into reusable scripts or dataset cards.
- For offline execution, use cached datasets or local files and avoid commands that require Hub metadata resolution.

## Schemas and Optional Decoders

- If inferred types are wrong, declare `Features` at load time or use `cast`/`cast_column` on a tiny sample first.
- If media decoders are unavailable, use `decode=False` when paths/bytes are enough, or install the relevant optional dependency before decoding.
- If nested examples fail, validate one representative row with a schema smoke helper before loading the full corpus.

## Processing and Cache

- If `map(batched=True)` changes row counts, remove or rewrite old columns and provide output `features` when needed.
- If multiprocessing fails, ensure mapped functions are picklable and avoid capturing non-serializable objects.
- If cached results surprise you, change transform code/fingerprint intentionally or disable cache reuse for the specific operation.

## Routing

- Loading paths, Hub/local builders, and `data_files` belong in `../sub-skills/loading-local-hub/SKILL.md`.
- Transforming, streaming, and framework formatting belong in `../sub-skills/processing-streaming/SKILL.md`.
- `Features`, file formats, and media decoding belong in `../sub-skills/features-formats/SKILL.md`.
- Hub upload, dataset cards, `datasets-cli`, cache directories, offline mode, and filesystems belong in `../sub-skills/sharing-cli-cache/SKILL.md`.
