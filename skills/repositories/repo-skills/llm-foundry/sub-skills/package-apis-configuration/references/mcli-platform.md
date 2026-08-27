# MCLI and MosaicML Platform Adaptation

This reference covers how LLM Foundry package/configuration surfaces appear inside MosaicML platform job YAMLs. It is not a complete training, eval, data-prep, or inference workflow guide.

## MCLI job shape

Observed LLM Foundry platform examples use this general shape:

```yaml
name: mpt-api-oriented-job
image: mosaicml/llm-foundry:<torch-cuda-compatible-tag>

integrations:
- integration_type: git_repo
  git_repo: mosaicml/llm-foundry
  git_branch: v0.21.0
  pip_install: .[gpu]
  ssh_clone: false

compute:
  gpus: 8
  # cluster: optional-cluster-name
  # gpu_type: a100_80gb

command: |
  cd llm-foundry/scripts
  composer train/train.py <platform-parameters-yaml>

parameters:
  # Written by the platform as the parameters YAML consumed by the command
  model:
    name: mpt_causal_lm
    init_device: meta
    d_model: 2048
    n_heads: 16
    n_layers: 24
    max_seq_len: 2048
    attn_config:
      attn_impl: flash
```

Important platform conventions:

- `parameters` is injected into the job as a YAML file; the command should consume the parameters path provided by the platform.
- `integrations` can install the repo via `git_repo` with `pip_install: .`, `.[gpu]`, or extras such as `.[gpu,openai]` depending on optional backends.
- `image` must match the PyTorch/CUDA expectations of the installed package and flash-attn wheel. A mismatched image is a common cause of flash-attn undefined symbols.
- Private repos require `ssh_clone: true` and platform-side SSH credentials.
- Some examples use `compute.gpus`; others use older top-level keys like `gpu_num`, `gpu_type`, `cluster`, or `run_name`. Preserve the schema expected by the target platform/account.

## Mapping package API configs into platform parameters

LLM Foundry package configs inside `parameters` still use the same registry keys described in the API reference.

```yaml
parameters:
  variables:
    tokenizer_name: meta-llama/Meta-Llama-3-8B
    max_seq_len: 4096
    global_seed: 17

  max_seq_len: ${variables.max_seq_len}
  seed: ${variables.global_seed}

  model:
    name: hf_causal_lm
    pretrained_model_name_or_path: meta-llama/Meta-Llama-3-8B
    pretrained: true
    init_device: mixed
    use_auth_token: true
    use_flash_attention_2: true

  tokenizer:
    name: ${variables.tokenizer_name}
    kwargs:
      model_max_length: ${variables.max_seq_len}

  optimizer:
    name: decoupled_lionw
    lr: 5.0e-7
    betas: [0.9, 0.95]
    weight_decay: 0.0

  scheduler:
    name: cosine_with_warmup
    t_warmup: 100ba
    alpha_f: 0.1

  callbacks:
    speed_monitor:
      window_size: 10
    lr_monitor: {}
```

Adaptation rules:

1. Keep registry keys exact: `model.name`, `optimizer.name`, `scheduler.name`, callback names, logger names, and tokenizer names must match installed registry entries.
2. If the config uses `hf_causal_lm` with `use_auth_token: true`, ensure the platform job has the required Hugging Face token environment variable or secret.
3. If the config uses OpenAI wrappers, install the OpenAI extra and provide `OPENAI_API_KEY` unless a custom `base_url` intentionally does not need it.
4. If the config uses `tiktoken`, install the OpenAI/tiktoken dependency set or otherwise ensure `tiktoken` is present.
5. If the config uses `te` FC/FFN layers, install Transformer Engine and use compatible GPU hardware.
6. If the config uses MegaBlocks FFNs or callbacks, install the MegaBlocks dependency set and use a compatible CUDA environment.
7. When adapting from a local YAML to MCLI, move the original LLM Foundry train/eval config under `parameters` and update the `command` to consume the platform-provided parameters YAML path.

## Commands and console scripts

The installed package exposes `llmfoundry` as a Typer console script.

Equivalent command patterns:

```bash
llmfoundry train <platform-parameters-yaml>
llmfoundry eval <platform-parameters-yaml>
llmfoundry registry get models
```

Examples may also call Composer scripts directly:

```bash
composer train/train.py <platform-parameters-yaml>
composer eval/eval.py <platform-parameters-yaml>
```

Use direct script paths only when the platform job clones the repo and `cd`s into the expected scripts directory. Use `llmfoundry train`/`llmfoundry eval` when the installed package CLI is the intended entry point.

## Platform credentials and environment

Common credentials/env needed by API/config tasks:

| Feature | Needed environment/config |
| --- | --- |
| Hugging Face gated models | HF token plus `use_auth_token: true` or equivalent cached credentials |
| OpenAI API wrappers | `OPENAI_API_KEY`, unless using a custom compatible endpoint with `base_url` |
| FMAPI local endpoint | `MOSAICML_MODEL_ENDPOINT` or default local endpoint when `local: true` |
| Weights & Biases logger | WandB credentials/project settings |
| MLflow logger/model registry | MLflow tracking/model registry configuration |
| Object storage datasets/checkpoints | Cloud provider credentials mounted into the platform job |
| Private git integration | Platform SSH key/secret and `ssh_clone: true` |

## Image and optional-backend alignment

The most fragile adaptation is GPU backend compatibility:

- `.[gpu]` installs flash-attn. The flash-attn wheel must match the PyTorch and CUDA version in the image.
- `use_flash_attention_2: true`, MPT default `attn_impl: flash`, fused cross entropy, DAIL RoPE, and some RMSNorm/Triton paths all depend on flash-attn.
- `fc_type: te` and `ffn_type: te_ln_mlp` depend on Transformer Engine.
- MegaBlocks FFNs depend on MegaBlocks/grouped-GEMM.
- CPU-only smoke tests should use `attn_impl: torch`, avoid `use_flash_attention_2`, and use `loss_fn: torch_crossentropy`.

## MCLI adaptation checklist

Before launching a platform job for package/config work:

1. Confirm the exact registry key exists in the active image using `llmfoundry registry get <group>` or the API probe.
2. Confirm extras match the config: `gpu`, `openai`, `peft`, `te`, `megablocks`, or CPU-only base package.
3. Confirm secrets are mounted: HF, OpenAI, WandB, MLflow, cloud storage, private git as needed.
4. Confirm `parameters` contains only keys accepted by the target train/eval dataclass or nested under `variables`.
5. Confirm `command` uses the correct working directory and config path.
6. For import/registry-only checks, prefer a short command that runs `python scripts/llmfoundry_api_probe.py` or `llmfoundry registry get` rather than a full train/eval command.
