# Package API and configuration troubleshooting

Read this when LLM Foundry imports, registry lookup, model construction, optional backend selection, or MosaicML platform adaptation fails. For workflow-specific launch failures, route to the data, training, evaluation, or inference sub-skill first.

## Safe first probe

Run the bundled API probe before making package claims:

```bash
python scripts/llmfoundry_api_probe.py --json
```

The probe imports `llmfoundry`, lists registries, constructs a tiny `MPTConfig` with `attn_impl: torch`, and checks optional modules without downloading models or running training/eval.

## Import fails before any workflow starts

Symptoms:

- `ModuleNotFoundError` while importing `llmfoundry`.
- Warning or failure around `pkg_resources`.
- `flash_attn` import raises an `undefined symbol` error.

Likely causes and recovery:

1. The package is not installed in the active Python. Install the public package or editable checkout, then verify:
   ```bash
   python -c "from importlib.metadata import version; print(version('llm-foundry'))"
   python -c "import llmfoundry; print(llmfoundry.__version__)"
   ```
2. LLM Foundry still imports `pkg_resources` through environment logging. If a newer setuptools removed that module, install a compatible setuptools in the task environment:
   ```bash
   python -m pip install 'setuptools<81'
   ```
3. If the error names `flash_attn` and says `undefined symbol`, the FlashAttention wheel was built for a different torch/CUDA ABI. Either use `attn_impl: torch` for CPU/API work, or reinstall flash-attn against the exact torch/CUDA stack in the target environment.
4. Do not treat an import from a local checkout as a package install. Confirm distribution metadata with `importlib.metadata.version('llm-foundry')`.

## Unknown registry key

Symptoms:

- `KeyError`, `RegistryError`, or a builder says an option such as `model.name`, `optimizer.name`, `callback`, or `logger` is unknown.

Recovery:

1. Check the exact registry group:
   ```bash
   llmfoundry registry get --group models
   llmfoundry registry get --group callbacks
   ```
2. Match YAML keys to installed registry names exactly. Examples from this snapshot include models `mpt_causal_lm`, `hf_causal_lm`, `hf_t5`, `openai_causal_lm`, `openai_chat`, `fmapi_causal_lm`, `fmapi_chat`, `finetune_embedding_model`, and `contrastive_lm`.
3. For custom code, import registration code before builders run. Use one of:
   - `code_paths` in train/eval config for a bounded local file import.
   - Python package entry points for reusable plugins.
4. If a custom entry overrides a built-in key, document that overwrite and test with `llmfoundry registry find <group> <name>` before launching a long run.

## Constructor keyword mismatch

Symptoms:

- `TypeError: got an unexpected keyword argument ...` from model, optimizer, callback, logger, tokenizer, or dataloader construction.
- YAML passes `params` to an optimizer or includes `name` inside constructor kwargs.

Recovery:

1. Inspect current signatures with `python scripts/llmfoundry_api_probe.py`.
2. Keep registry selector names separate from constructor kwargs. For example, YAML uses `model.name: mpt_causal_lm`, but `name` is not normally forwarded to `MPTConfig`.
3. Optimizer builders pass model parameters separately; do not put `params` in YAML.
4. Callback entries in `callbacks_with_config` receive the full train config; ordinary callbacks do not.
5. Hugging Face wrappers can download configs/models/tokenizers when instantiated. For dry API work, inspect signatures rather than constructing `ComposerHFCausalLM`.

## MPT configuration and attention/backend failures

Symptoms:

- Flash attention unavailable, unsupported dtype/device, or sequence length/position config errors.
- `alibi`, `rope`, `sliding_window_size`, or `block_overrides` validation failures.
- TransformerEngine or MegaBlocks import errors.

Recovery:

1. For CPU or quick API checks, set attention to torch:
   ```yaml
   model:
     name: mpt_causal_lm
     attn_config:
       attn_impl: torch
   ```
2. Use `flash` only after the target environment has a flash-attn build matching torch, CUDA, Python, and GPU architecture. CPU import or torch CUDA alone does not verify flash kernels.
3. TransformerEngine (`fc_type: te`, `te_ln_mlp`, FP8) and MegaBlocks MoE (`mb_moe`, `mb_dmoe`) require optional packages and compatible GPUs. If those packages are absent, route to CPU/torch alternatives or explicitly install the optional stack before claiming support.
4. `alibi` or `rope` disables learned positional embeddings in `MPTConfig`; avoid combining incompatible position encodings in default and block override configs.
5. `sliding_window_size` requires flash-attn support in the relevant code path; do not rely on it for CPU-only torch attention.

## Tokenizer and Hugging Face remote-code issues

Symptoms:

- `trust_remote_code` warnings or refusal to load custom model/tokenizer code.
- Tokenizer has no pad/eos token, unexpected `model_max_length`, or remote download failures.

Recovery:

1. Separate pure config inspection from downloading. `MPTConfig` can be constructed locally; `AutoTokenizer.from_pretrained` and HF model wrappers may contact the Hub.
2. If the task permits downloads, set `trust_remote_code` deliberately and record why custom code is trusted.
3. For generation/inference, set `pad_token_id` or allow the script to fall back to EOS only when that behavior is acceptable for the model.
4. For training/eval, route tokenizer/data alignment questions to the training or evaluation sub-skill.

## MCLI/platform YAML adaptation issues

Symptoms:

- Job YAML has image, command, or integration fields that do not match the target MosaicML platform workspace.
- The same YAML works locally but not in a remote platform run.

Recovery:

1. Read `references/mcli-platform.md` in this sub-skill for platform-field adaptation patterns.
2. Keep package-level checks short: `python scripts/llmfoundry_api_probe.py` and `llmfoundry registry get` are safe; full `llmfoundry train`/`eval` commands consume cluster resources.
3. Put credentials, tokens, object-store permissions, and cluster secrets in the platform's secret mechanism, not in YAML content.
4. If the platform image lacks optional GPU packages, either choose a Docker image matching the desired torch/CUDA/flash stack or switch the config to CPU/torch-compatible options.

## When to stop and ask for environment changes

Stop instead of guessing when:

- The user explicitly needs flash-attn, TransformerEngine, MegaBlocks, FasterTransformer, ROCm, Gaudi, or multi-node distributed verification and the current environment has not prepared that backend.
- The task requires private HF, Databricks, MosaicML platform, S3/GCS/OCI/Azure, MLflow, W&B, or OpenAI credentials.
- A config launches long training/eval/generation or downloads large model/data artifacts and the user has not approved budget/runtime.
