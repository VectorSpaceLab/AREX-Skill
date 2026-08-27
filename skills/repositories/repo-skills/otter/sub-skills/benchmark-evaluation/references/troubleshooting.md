# Benchmark troubleshooting

## `unrecognized arguments: --confg`

The documented example contains a typo. Use:

```bash
python -m pipeline.benchmarks.evaluate --config benchmark.yaml
```

or:

```bash
python -m pipeline.benchmarks.evaluate -c benchmark.yaml
```

## Registry name failure

Symptoms:

- `<name> is not an available model.`
- `<name> is not an available eval dataset.`
- Import failure for `pipeline.benchmarks.models.<name>` or `pipeline.benchmarks.datasets.<name>`.

Fixes:

1. Check exact keys in [model-and-dataset-registry](model-and-dataset-registry.md).
2. Correct documentation spelling traps: use `scienceqa`, not `SicenceQA`; use `otterhd`, not `OtterHD` as a registry key.
3. For third-party model wrappers such as LLaVA, LLaMA-Adapter, mPLUG-Owl, VideoChat, and Video-ChatGPT, confirm the dependency is intentionally installed. If not, skip that model and use an available wrapper.

## Missing GPT/API credentials

GPT-assisted judging/extraction is required for full runs of:

- `magnifierbench` free-form scoring.
- `mmvet` grading; `api_key` is a required constructor argument.
- `mathvista` answer extraction/scoring when quick local extraction is insufficient.
- `gpt4v` model wrapper.

Safe responses:

- If credentials are not available, remove those datasets/models from the config and record the skip reason as `missing GPT API key`.
- If credentials are available through an environment variable, expand it into the runtime config or use a launcher that substitutes it before evaluation.
- Validate placeholders before launch; strings such as `${OPENAI_API_KEY}`, `[You GPT-4 API]`, `changeme`, or empty values should not be treated as real keys.

## Dataset download or cache failure

Most benchmark datasets are loaded through Hugging Face `datasets`. A first run may need network access and writable cache space.

Checklist:

1. Decide whether downloads are allowed. If not, skip uncached datasets with reason `dataset download not approved or unavailable`.
2. In YAML config mode, set `cache_dir` inside each dataset entry that should use a specific cache.
3. In non-config CLI mode, `--cache_dir` is copied into every synthesized dataset entry.
4. Verify filesystem permissions and free space for both the cache and `default_output_path`.
5. If an HF dataset revision or split is unavailable, try the documented default split first (`test` for most; `dev` or `test` for MMBench/MathVista).

## Model path, model download, or dependency failure

Common causes:

- `model_path` omitted for wrappers that require it (`llama_adapter`, `mplug_owl`, `video_chat`, `video_chatgpt`).
- Local `model_path` or `checkpoint_path` does not exist.
- Remote Hugging Face model download is blocked by network, license, authentication, or cache space.
- Optional third-party package imports are missing.
- GPU memory or dtype support is insufficient for the selected model.

Safe responses:

- Prefer one model and one small/debug dataset subset for the first run.
- Use local model paths when downloads are not approved.
- Use the validator with `--check-paths` for local path checks.
- Record skip reasons such as `missing local model path`, `model download not approved`, `third-party wrapper dependency missing`, or `insufficient GPU memory`.

## Output logging surprises

`pipeline.benchmarks.evaluate` redirects stdout into the top-level `output` text file while also echoing to the terminal. Individual dataset classes write their own result files, typically JSON, XLSX, or CSV, under `default_output_path`.

Avoid these traps:

- Do not set `output` to a bare filename such as `evaluation.txt`; the evaluator tries to create `os.path.dirname(output)`, so use `./logs/evaluation.txt` or another path with a directory.
- Do not reuse the same output directory for unrelated benchmark attempts unless overwriting/resuming is intentional.
- For MME, expect a timestamped model subdirectory under the MME output path.
- For MM-VET, expect model answer JSON, GPT grade JSON, and capability score CSV files.

## Config-constructor mismatch

Because config mappings are passed directly to constructors, unknown keys cause runtime `TypeError`.

Examples:

- Top-level `cache_dir` is ignored in YAML mode; put it inside each dataset entry.
- `model_paths` is a CLI flag name, not a model YAML key; YAML entries use `model_path`.
- `default_output_path` is dataset-specific; top-level `output` is only the text report.
- `decimail_places` is misspelled in the MM-VET constructor; avoid setting it unless necessary.

Run:

```bash
python ../scripts/validate_benchmark_config.py benchmark.yaml --strict
```

before launching.

## Public suite caveats

For `pipeline.benchmarks.public_datasets_suite.evaluate`:

- Rebuild commands from [public-suite](public-suite.md); do not copy machine-specific example paths.
- Use the current module path, not stale `pipeline.eval.evaluate` examples.
- Classification evaluation with caching is noted as unreliable for MPT-style models; disable caching when investigating classification anomalies.
- Multi-process runs need distributed environment variables or a distributed launcher.
- Skip public-suite runs when required local annotation/image paths are missing, converted TextVQA/VizWiz annotations are unavailable, or large GPU/runtime budget has not been approved.
