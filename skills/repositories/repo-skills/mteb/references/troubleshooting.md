# Cross-Cutting Troubleshooting

Use this reference before moving into a sub-skill-specific troubleshooting file. MTEB problems usually fall into environment setup, optional dependencies, task/data access, model protocol, CLI arguments, or result-cache layout.

## Import Or Install Fails

Symptoms:

- `ModuleNotFoundError` for `mteb`, `numpy`, `datasets`, `torch`, `sentence_transformers`, `transformers`, or `pytrec_eval_terrier`.
- `python -m pip check` reports dependency conflicts.
- The CLI command `mteb` is missing even though Python import works.

Actions:

- Install the base package with `pip install mteb` in the environment that will run evaluations.
- Re-run `python -m pip check` after installation.
- Use `python -m pip show mteb` to confirm the distribution exists, then use `python -c "import mteb; print(mteb.__version__)"` to confirm importability.
- If the CLI is missing, verify the same environment owns both `python` and `mteb`; use `python -m pip install --force-reinstall mteb` only in a disposable or explicitly approved environment.

## Optional Extra Missing

Symptoms:

- `ImportError` when enabling `co2_tracker=True`, launching `mteb leaderboard`, using image/audio tasks, or loading provider-specific models.
- A model wrapper imports an external SDK such as OpenAI, Voyage, Jina, vLLM, BM25, image, or audio dependencies.

Actions:

- Install only the needed extra, such as `mteb[codecarbon]`, `mteb[leaderboard]`, `mteb[image]`, `mteb[audio]`, `mteb[openai]`, `mteb[vllm]`, or a documented model-specific extra.
- Do not install all extras by default; optional groups can pull large GPU, UI, provider, or modality dependencies.
- For custom models, route to `../sub-skills/models-and-encoders/SKILL.md` and validate protocol shape separately from dependency importability.

## Dataset Download Or Private Access Fails

Symptoms:

- Hugging Face dataset not found, private dataset warnings, authentication errors, or long downloads.
- Evaluation skips or fails on private, beta, superseded, or modality-specific tasks.

Actions:

- Use `mteb.get_tasks(...)` with explicit task names and inspect task metadata before running large evaluations.
- Keep `exclude_private=True` and `exclude_beta=True` unless the user intentionally opts into those tasks.
- For private datasets, set up Hugging Face authentication outside the skill and use `public_only=False` only when access is expected.
- Route task visibility and filtering questions to `../sub-skills/tasks-and-benchmarks/SKILL.md`.

## Evaluation Fails Mid-Run

Symptoms:

- A model works on one task type but fails on retrieval, reranking, multimodal, or pair-classification tasks.
- `encode_kwargs` is ignored or causes unexpected keyword errors.
- Some tasks fail while others complete.

Actions:

- Run one small named task first and keep `raise_error=True` while debugging.
- Set `raise_error=False` only when the user wants partial results across many tasks.
- Validate the model object with `../sub-skills/models-and-encoders/scripts/validate_encoder_protocol.py`.
- Route evaluation settings to `../sub-skills/evaluation-workflows/SKILL.md`.

## CLI Command Or Flag Fails

Symptoms:

- `mteb create-meta` is not found.
- A benchmark run warns that task, language, category, or split filters are ignored.
- `--device`, `--prediction-folder`, `--overwrite`, or `--overwrite-strategy` behaves differently than expected.

Actions:

- Run `mteb --help` and subcommand `--help` in the target environment before scripting.
- Use `mteb create-model-results` for model-card result metadata in current releases; if older examples say `create-meta`, verify the installed subcommand first.
- Do not combine `--benchmarks` with task/language/category filters unless the user understands those filters are ignored.
- Route shell automation to `../sub-skills/cli-and-automation/SKILL.md`.

## Cache Or Results Look Wrong

Symptoms:

- `only-cache` cannot find results that appear to exist.
- Model-card metadata generation reports missing task JSON or `model_meta.json`.
- Leaderboard rows are missing after adding local results.

Actions:

- Confirm whether the path is a cache root, a `results/` root, or a specific model/revision folder.
- Inspect local and remote cache separation: local results usually live under `results/`, while downloaded public results live under `remote/results/`.
- Use `../sub-skills/results-and-leaderboard/scripts/inspect_mteb_results.py` before publishing or comparing scores.
- Route result-object/dataframe/leaderboard workflows to `../sub-skills/results-and-leaderboard/SKILL.md`.

## Contribution Validation Fails

Symptoms:

- New task metadata is incomplete, missing dataset revision, or uses ambiguous language/script codes.
- A model implementation imports optional provider packages at module import time.
- Citation, descriptive statistics, or task quality tests fail.

Actions:

- Route contribution workflows to `../sub-skills/contributing-to-mteb/SKILL.md`.
- Keep optional dependency imports inside wrapper constructors or methods, not at top level.
- Validate task metadata structurally before downloading datasets.
- Use small smoke evaluations only after metadata and import checks pass.
