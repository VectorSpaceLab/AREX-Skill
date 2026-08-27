# OpenChat cross-cutting troubleshooting

Use this reference for install/import/backend problems that affect more than one OpenChat workflow. Workflow-specific issues live in the nearest sub-skill troubleshooting page.

## `import ochat` or `from ochat.config import MODEL_CONFIG_MAP` fails

Symptoms:

- `ModuleNotFoundError: No module named 'ochat'`
- imports succeed only from a repository checkout, not from another working directory

Likely causes:

- The `ochat` package is not installed in the active Python environment.
- A local checkout is on `PYTHONPATH` in one shell but not another.
- An editable install was made in a different environment.

Recovery:

1. Run `python -m pip show ochat` in the environment the user will actually use.
2. Run `python scripts/check_openchat_import.py` from this skill.
3. Install a released package or user-provided checkout as described in [installation-and-backends](installation-and-backends.md).

## Missing optional or broad dependencies

Symptoms:

- `ModuleNotFoundError` for `vllm`, `ray`, `fastapi`, `flash_attn`, `datasets`, `wandb`, `pylatexenc`, or `openai`.
- `python -m pip check` reports missing dependencies after an editable or `--no-deps` install.

Likely causes:

- OpenChat metadata uses broad base dependencies rather than workflow extras.
- The environment was intentionally installed with a smaller subset.
- The selected workflow actually needs a skipped backend package.

Recovery:

1. Identify the sub-skill needed by the user: [prompting](../sub-skills/prompting/SKILL.md), [serving](../sub-skills/serving/SKILL.md), or [evaluation](../sub-skills/evaluation/SKILL.md).
2. Install only dependencies needed for that workflow unless the user explicitly wants a full package install.
3. If `pip check` must pass for publication or deployment, install all metadata-required dependencies, including FlashAttention-compatible wheels.

## CUDA is visible but local serving/evaluation fails

Symptoms:

- vLLM import succeeds but server startup fails.
- `torch.cuda.is_available()` is false despite an NVIDIA GPU.
- FlashAttention or xFormers reports ABI, CUDA, or symbol errors.

Likely causes:

- CPU-only PyTorch wheel installed.
- PyTorch CUDA wheel requires a newer driver.
- FlashAttention/xFormers wheel does not match PyTorch, Python, CUDA, or C++ ABI.
- The container cannot see GPUs even if the host has them.

Recovery:

1. Run `python scripts/check_openchat_import.py --check-cuda --json`.
2. Compare PyTorch version, CUDA runtime, GPU count, and device name with the user's hardware.
3. Reinstall the PyTorch CUDA wheel and matching extension wheels rather than mixing CPU/GPU packages.
4. For source builds, ensure CUDA toolkit and `nvcc` are available before approving a long build.

## Model type, alias, and model path are confused

Symptoms:

- Server returns 404 for request `model`.
- `MODEL_CONFIG_MAP["openchat_3.5"]` raises a key error.
- Server auto-detection fails to load `openchat.json`.

Likely causes:

- A serving alias was used as a canonical model type.
- The model weights directory/repository lacks OpenChat metadata.
- The client request uses a model name not advertised by `/v1/models`.

Recovery:

1. Read [prompting model overview](../sub-skills/prompting/references/model-overview.md).
2. Use a canonical key such as `openchat_3.6` or `openchat_v3.2_mistral` for `--model-type` and direct Python config.
3. Query `/v1/models` and use one of the returned names in request JSON.

## Tokenizer/model artifacts are missing or unexpectedly downloaded

Symptoms:

- Transformers tries to access Hugging Face during a smoke test.
- Prompt tests stall while downloading tokenizers.
- Special-token strings are split into multiple IDs.

Likely causes:

- Real model/tokenizer artifacts are not cached locally.
- The wrong model family was selected for the configured template.
- Custom model weights do not include required OpenChat special tokens.

Recovery:

1. For no-download prompt logic checks, use [prompting smoke](../sub-skills/prompting/scripts/check_prompting_smoke.py).
2. For real token IDs, ensure the user has supplied a local model directory or permits model hub access.
3. Verify the EOT/header token requirements in [model overview](../sub-skills/prompting/references/model-overview.md).

## Evaluation data is missing after source checkout is gone

Symptoms:

- `run_eval` default `data_path` does not exist.
- Task files are missing expected `question`, `label`, or `options` fields.

Likely causes:

- The user is not running from the original checkout, and evaluation data was not supplied separately.
- Package installation did not include the repo's raw `eval_data` tree.

Recovery:

1. Ask the user for a local benchmark data directory.
2. Validate it against [evaluation data layout](../sub-skills/evaluation/references/eval-data-layout.md).
3. Pass it explicitly with `--data-path` rather than relying on the source-repo default.
