# Data-prep troubleshooting

Use this table to map common symptoms to likely causes and safe next actions. Avoid destructive cleanup until the output location and intended command are confirmed.

## Quick triage

```bash
# Read-only import/signature and fixture probe
python scripts/llmfoundry_data_prep_smoke.py --fixture sample.jsonl --schema auto
python scripts/llmfoundry_data_prep_smoke.py --check-cli

# Check MDS output without reading shards
python - <<'PY'
import json
from pathlib import Path
root = Path('mds_output')
for index in root.rglob('index.json'):
    data = json.loads(index.read_text())
    print(index, 'shards=', len(data.get('shards', [])))
PY
```

## Missing package or CLI

Symptoms:

- `llmfoundry: command not found`
- `ModuleNotFoundError: No module named 'llmfoundry'`
- Import errors for `streaming`, `composer`, `datasets`, `torch`, `transformers`, or `typer`.

Likely cause:

- The active Python environment does not have LLM Foundry and its data-prep dependencies installed, or the console-script path is not on `PATH`.

Safe actions:

1. Run `python scripts/llmfoundry_data_prep_smoke.py --dump-json` to see which modules are importable.
2. Confirm `python -c "import sys; print(sys.executable)"` matches the environment where LLM Foundry was installed.
3. If `python -c "import llmfoundry"` works but `llmfoundry` is missing, reinstall the package with console scripts or use the environment's executable path directly.
4. Do not start conversion until `streaming`, `datasets`, `transformers`, and `composer` import successfully for non-Delta workflows.

## Tokenizer missing, downloading, or unsafe

Symptoms:

- `When setting --concat_tokens, you must specify a --tokenizer`.
- Hugging Face tokenizer download prompts, network timeouts, or cache permission errors.
- Error that tokenizer does not insert EOS or BOS and no separator was specified.
- `If tokenizing on-the-fly, tokenizer must have a pad_token_id`.

Likely cause:

- Conversion or dataloader tokenization requires a tokenizer name/path, local cache, pad token, and document-boundary strategy.

Safe actions:

- For JSON/HF pretraining with `--concat-tokens`, always set `--tokenizer`.
- If the tokenizer does not insert separators, add `--eos-text '<|endoftext|>'` or an appropriate `--bos-text`.
- If the tokenizer already adds special tokens, avoid duplicating BOS/EOS unless that is deliberate.
- For GPT-style tokenizers with no pad token, set or choose a tokenizer configuration that uses EOS as pad before dataloader construction.
- Do not set `--trust-remote-code` unless the tokenizer repository is trusted and the user explicitly accepts remote code execution.

## Invalid pretraining JSON/JSONL

Symptoms:

- Hugging Face `DatasetGenerationError`.
- Key errors or runtime failures while iterating local JSON data.
- Conversion finishes but output has zero or unexpectedly few shards.

Likely cause:

- JSONL lines are not valid JSON objects, records do not have `text`, values are not strings, or the dataset is too small for the chosen `--concat-tokens` length.

Safe actions:

```bash
python scripts/llmfoundry_data_prep_smoke.py --fixture train.jsonl --schema pretraining --strict
```

Then verify:

- Each line is valid JSON and an object.
- Each record has `text` as a string.
- There are enough total tokens to produce at least one sequence of `--concat-tokens`.
- The input file is not empty and is not accidentally compressed or binary.

## Invalid fine-tuning prompt/response data

Symptoms:

- `Unknown example type`.
- `Expected prompt to be ...` or `Expected response to be ...`.
- Error checking example for proper formatting.
- Examples are dropped because prompt is too long, prompt/response is empty, or response is all padding.
- Truncation removes all loss-generating tokens.

Likely cause:

- Records are not exactly prompt/response or chat/messages after preprocessing, or target policies/max sequence length do not match the prepared data.

Safe actions:

```bash
python scripts/llmfoundry_data_prep_smoke.py --fixture sft.jsonl --schema sft --strict
python scripts/llmfoundry_data_prep_smoke.py --fixture chat.jsonl --schema chat --strict
```

For prompt/response:

- Keep only `prompt` and `response` in the formatted output unless a preprocessor maps custom columns.
- Both values must be strings and should be non-empty.
- If raw data has extra keys, use `--preprocessor module:function` instead of `--skip-preprocessing`.

For chat/messages:

- `messages` must be a list of role/content objects.
- Last role must be `assistant`.
- Roles must be `user`, `assistant`, `system`, or `tool`.
- Consecutive roles should not repeat in the validated chat path.

For target policy:

- Decoder-only default: `--target-prompts none --target-responses last`.
- Encoder-decoder: must use prompts `none` and responses `last`.
- If all target tokens disappear after truncation, increase `max_seq_len`, shorten prompts, or adjust target policy intentionally.

## Output folder exists or is not empty

Symptoms:

- Error that `out_root` contains requested splits.
- Error that output folder is not empty.
- Delta export refuses an existing non-empty JSON output folder.

Likely cause:

- LLM Foundry protects existing data from accidental overwrite.

Safe actions:

1. Inspect the output folder before deleting anything.
2. If it contains a successful MDS dataset, choose a new output root instead of overwriting.
3. If it is a failed partial output and the user approves cleanup, move it aside or delete it deliberately.
4. For `convert_text_to_mds`, use `--reprocess` only when re-running the same input intentionally; it still will not safely overwrite arbitrary non-empty folders.

## Empty or too-small datasets

Symptoms:

- `No text files found`.
- `No shards were created when converting text to MDS`.
- Dataset too small for physical nodes or `num_canonical_nodes`.
- Not enough samples when `drop_last` is true.

Likely cause:

- Input folder has no matching files, total tokens are below `concat_tokens`, or runtime world size/batch settings require more samples than available.

Safe actions:

- Lower `--concat-tokens` only for a smoke run; keep production sequence length aligned with model config.
- Use a larger fixture or more source files.
- For distributed training, ensure sample count is at least physical nodes/canonical nodes and at least world size times dataloader batch size when `drop_last` is true.
- Reduce `num_canonical_nodes` only if the dataset was intentionally tiny.

## Unsafe MDS shard types

Symptoms:

- Errors or warnings about unsafe types/Pickle during MDS deserialization.

Likely cause:

- A shard contains data types that may use Pickle or unsafe deserialization.

Safe actions:

- Keep `allow_unsafe_types: false` by default.
- Only set `allow_unsafe_types: true` for trusted datasets after the user explicitly accepts arbitrary-code-execution risk.
- Prefer converters that write primitive `str`, `json`, or `ndarray:int32` columns.

## Remote object-store access and cache failures

Symptoms:

- Permission denied listing or downloading shards.
- `index.json` not found under the selected split.
- Cache fills disk or repeatedly evicts shards.
- Timeout downloading shards.

Likely cause:

- Wrong `remote`/`split`, missing credentials, insufficient bucket permissions, or undersized local cache.

Safe actions:

- Confirm remote layout contains `remote/split/index.json` when `split` is set.
- Confirm object-store credentials allow list/read for training and write for conversion outputs.
- Set a stable `local` cache and sufficient `cache_limit`.
- Increase `download_retry` and `download_timeout` for slow object stores.
- Avoid `keep_zip: true` unless compressed shards must be retained; it increases disk use.

## `remote`, `local`, `split`, and `streams` misconfiguration

Symptoms:

- `Local directory ... does not contain split ...`.
- Error that `hf_name` is set with `remote`/`local`.
- Error that `remote` requires `local` for streaming fine-tuning.
- Error that `streams` is set with top-level `remote`/`local`.

Likely cause:

- Mixing HF and streaming dataset paths or putting split/cache fields at the wrong level.

Safe actions:

- HF fine-tuning path: set `hf_name`, `split`, optional `hf_kwargs`, optional `preprocessing_fn`; do not set `remote` or `local`.
- Single streaming path: set `remote`, `local`, `split`, `max_seq_len`, and target fields if SFT.
- Local-only streaming path: set `local` and `split` if local root contains split subdirs.
- Multiple streams: put `remote`, `local`, and `split` inside each stream; do not set top-level `remote`/`local`.

## Packing failures

Symptoms:

- `packing_ratio must be >= 1`.
- `dataset.max_leftover_bins_to_keep has been defined, but dataset.packing_ratio has not been set`.
- `On-the-fly packing is currently only supported for decoder-only formats`.
- Unexpected discarded examples or changed effective sample consumption.

Likely cause:

- Fine-tuning packing is a collator/dataloader feature with strict constraints.

Safe actions:

- Use packing only for `decoder_only_format: true`.
- Set `packing_ratio` to a float `>= 1` or `auto`.
- Only set `max_leftover_bins_to_keep` when packing is enabled.
- Treat `auto` as a profile-based estimate; validate throughput/waste on a representative subset.
- Remember that device batch size remains the packed batch size while raw examples consumed per batch increase.

## Databricks and Delta export failures

Symptoms:

- Missing `lz4`, `databricks-connect`, `databricks-sdk`, `databricks-sql`, or `pyspark` imports.
- Failed to connect to Databricks or SQL warehouse.
- Cluster does not exist, cannot attach, invalid access mode, terminated/unusable cluster.
- Unity Catalog not enabled, table not found, malformed table name, or insufficient permissions.
- Output JSONL is empty or contains invalid JSON.

Likely cause:

- Delta export requires optional dependencies, workspace host/token, compatible cluster/warehouse, Unity Catalog access, and table read permissions.

Safe actions:

1. Do not run Delta commands without explicit user approval and credentials.
2. Use `catalog.schema.table` for `--delta-table-name`.
3. Use a local empty `--json-output-folder`; remote output folders are rejected.
4. For DBSQL, provide `--http-path` and ensure warehouse permissions.
5. For Databricks Connect, provide a compatible `--cluster-id` or use `--use-serverless` only if the workspace supports it.
6. After export, validate JSONL locally before converting to MDS:

```bash
python scripts/llmfoundry_data_prep_smoke.py --fixture delta_json/train-00000-of-00001.jsonl --schema auto
```

## Command option spelling

Symptoms:

- Typer says an option does not exist.

Likely cause:

- The package CLI uses Typer-style kebab-case option names even though Python arguments use snake_case.

Safe actions:

- Prefer `--out-root`, `--data-subset`, `--concat-tokens`, `--eos-text`, `--max-seq-len`, and `--json-output-folder`.
- Run `llmfoundry data_prep COMMAND --help` in the active environment for exact accepted options.
- Old source script examples may use `--out_root` or direct `python convert_*.py`; prefer the public package CLI in this skill.

## When to stop and ask

Ask the user before proceeding if any of these are true:

- The next step downloads a model/tokenizer/dataset from the network.
- The command queries Databricks, object storage, or a protected remote dataset.
- The output folder exists and cleanup is required.
- The dataset schema is ambiguous and no preprocessing function is provided.
- The user asks to launch training, tune optimizer/callbacks, or evaluate ICL tasks; route to the owning sub-skill instead.
