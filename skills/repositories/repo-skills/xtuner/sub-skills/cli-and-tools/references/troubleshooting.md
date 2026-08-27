# Legacy XTuner CLI/tool troubleshooting

Use this when old top-level `xtuner MODE ...` commands, config discovery, model conversion, legacy chat/evaluation, or preprocess tools fail.

## `xtuner` command is missing

Symptom:

```text
xtuner: command not found
```

Likely cause: the current package metadata may install the Python package without a console entry point for the old router.

Actions:

1. Check whether the command exists:

   ```bash
   command -v xtuner
   python - <<'PY'
   import importlib.metadata as md
   print(md.version('xtuner'))
   PY
   ```

2. If the task is V1 SFT/RL, do not repair the old router; route to the V1 sub-skill.
3. If the task is truly legacy, ask for an environment exposing the legacy `xtuner` console router. Do not rely on source-tree script paths from this generated skill.
4. For config search/copy only, avoid importing XTuner and use `scripts/find_legacy_configs.py` with an explicit config root.

## Legacy command accidentally launches distributed training

Symptom: a harmless-looking `xtuner train`, `test`, `mmbench`, or conversion command is wrapped by `torchrun`, or extra `--launcher pytorch` appears.

Cause: the legacy router checks `NNODES` and `NPROC_PER_NODE`. Values greater than one trigger `torchrun` unless `--launcher slurm` is present.

Actions:

```bash
NNODES=1 NPROC_PER_NODE=1 xtuner list-cfg -p qlora
```

For actual distributed runs, explicitly document `NNODES`, `NPROC_PER_NODE`, `NODE_RANK`, `ADDR`, `PORT`, launcher choice, and cluster assumptions before execution.

## Config name not found

Symptom: `Cannot find CONFIG`, `KeyError`, or a copy/list command cannot locate an old config name.

Actions:

- Confirm the config belongs to the legacy config zoo, not a V1 example/config file.
- Use the bundled helper against an explicit config root:

  ```bash
  python scripts/find_legacy_configs.py --config-root /path/to/legacy-configs qlora alpaca --limit 20
  ```

- If several names match, add tokens or `--family`; copy only with `--exact` when one candidate remains.
- If no config root is available, ask the user for an exported config directory or a package installation that contains the old config files.

## Model path vs HuggingFace snapshot path

Many legacy tools accept a `MODEL`, `LLM`, `CLIP`, or `--visual-encoder` value. Clarify what kind of path it is:

- **HuggingFace snapshot directory**: contains files such as model config, tokenizer/processor metadata, and weight files. Suitable for chat/evaluation base models and adapter merge base paths.
- **Model id**: may trigger network download. Do not rely on this in offline or credential-sensitive environments.
- **`.pth` checkpoint file**: suitable for `convert pth_to_hf`, not for adapter merge.
- **PEFT adapter directory**: contains adapter metadata and adapter weights. It is not a complete model until merged or loaded with a matching base model.
- **LLaVA adapter bundle**: may contain LLM adapter, visual encoder adapter, projector, and possibly a visual encoder; check which components are present.

If a user supplies a single vague path, ask which role it plays before constructing a command.

## Adapter/base mismatch

Symptoms:

- shape mismatch or missing target modules;
- tokenizer mismatch;
- PEFT cannot find adapter metadata;
- merged model produces unusable outputs;
- CLIP/LLM architecture errors when merging.

Actions:

1. Verify base model family and size match the adapter's training base.
2. Verify the adapter directory is not already a merged model.
3. Use `--is-clip` only for visual-encoder adapters; omit it for LLM adapters.
4. Prefer local snapshot paths over unresolved model ids in offline environments.
5. Save to a new output directory and validate files before deleting any input.

## Benchmark data or model assets are missing

Legacy `chat`, `mmbench`, and `eval_refcoco` load large models and data assets.

Checklist:

- `chat`: base model path or id, optional adapter or LLaVA path, optional visual encoder, optional image path, prompt/system template names, generation settings, and device/offload plan.
- `mmbench`: base model, LLaVA adapter, visual encoder if not bundled, MMBench TSV/data path, work directory, and accelerator resources.
- `eval_refcoco`: base model, LLaVA adapter, visual encoder if not bundled, RefCOCO data path/images, work directory, and accelerator resources.
- `preprocess refcoco`: annotation directory, COCO image directory, save directory.
- `preprocess arxiv`: newline-delimited JSON input with `categories` and `update_date` fields.

If the tool attempts `snapshot_download` or model loading from an id, stop and ask whether network access and credentials are allowed.

## Unsafe network or credential handling

Legacy tools may load remote HuggingFace models or remote-code model implementations. Avoid accidental credential leakage.

- Do not paste tokens into commands unless the user explicitly asks and scopes them.
- Prefer pre-downloaded local snapshots for large/private models.
- Review untrusted model snapshots before allowing remote-code execution.
- For private object storage or remote checkpoint paths, require the user to provide a safe credential mechanism and a non-secret command transcript.
- Avoid running benchmark scripts that auto-download data without explicit approval.

## `check-custom-dataset` fails on a custom dataset

Likely causes in the old stack:

- config points to a non-JSON dataset path when the custom SFT workflow expects JSON loading;
- examples are not in the legacy standard `conversation` list format with `input` and `output` strings;
- a non-standard dataset lacks a `dataset_map_fn`;
- a standard dataset incorrectly sets a `dataset_map_fn`;
- `pack_to_max_length=True` but unused columns are not removed;
- tokenizer or dataset imports required by the config are missing.

For V1 JSONL schema validation, route to `data-preparation` instead of using this legacy checker.

## Bitsandbytes, flash attention, or GPU warnings

Old HuggingFace Trainer QLoRA examples and 4/8-bit chat modes depend on quantization support. If bitsandbytes lacks a compatible CUDA binary, GPU quantization and 8-bit optimizers may be unavailable. If flash-attn is missing, some V1 paths may fall back or fail depending on the feature; do not claim GPU backend support without a local check.

Actions:

- Confirm CUDA, PyTorch, bitsandbytes, and model dtype compatibility.
- Prefer CPU-only config discovery helpers when the task does not require model execution.
- Route V1 backend/performance questions to `model-backends`.
