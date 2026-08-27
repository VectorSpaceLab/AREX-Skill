# Cross-Cutting Troubleshooting

Use this reference before diving into a sub-skill when a problem spans package installation, CUDA/xFormers, model assets, datasets, or DeepSpeed resources.

## Route failures quickly

| Symptom | Likely cause | Next action |
|---|---|---|
| `ModuleNotFoundError` for `torch`, `transformers`, `xformers`, or `sentencepiece` | Core model dependencies are missing or incompatible. | Install the repo-documented stack when possible, then run `sub-skills/architecture-and-loading/scripts/local_model_smoke.py`. |
| `ModuleNotFoundError: No module named 'xformers'` while only trying to import model code | The local model file imports xFormers at module import time. | Install a Torch-compatible xFormers wheel, or use a runtime where Torch/xFormers/CUDA variants match. Eval-mode tiny forward still needs the import. |
| `ValueError` about custom code or remote model files | `trust_remote_code=True` was omitted or the model source is not trusted/resolvable. | Use `trust_remote_code=True` only for official Baichuan sources or vetted local mirrors; see the architecture sub-skill. |
| Missing `tokenizer.model`, `config.json`, or weight shards | Real model assets are absent; a config-only smoke was confused with full inference readiness. | Locate or pre-cache a Baichuan-compatible model directory before inference/evaluation. |
| `.cuda()` fails in evaluation scripts | CUDA is not available, wrong device runtime is active, or the model/data exceed memory. | Use CPU only for static/tiny checks. Full C-Eval/MMLU and README inference snippets require a suitable CUDA runtime. |
| C-Eval cannot load `ceval/ceval-exam` | Dataset package/cache/network is unavailable or selected split is wrong. | Use the evaluation sub-skill preflight and verify `datasets` cache/access before model loading. |
| MMLU fails with `No module named 'categories'` | The MMLU benchmark layout is missing Hendrycks/test `categories.py` beside the evaluation entrypoint. | Use the evaluation preflight helper to validate benchmark root layout. |
| Training launch hangs or initializes distributed runtime during inspection | The training entrypoint is a process script, not an import-safe API. | Do not import it to inspect arguments. Use the bundled training validators and command renderer. |
| DeepSpeed errors about hostfile, NCCL, bf16, ZeRO, or ranks | Cluster/GPU/runtime resources do not match the training config. | Validate hostfile and JSON first; ask for explicit permission before launching distributed training. |

## Dependency and version boundaries

The repository-documented requirements are:

```text
deepspeed==0.9.2
numpy==1.23.5
sentencepiece==0.1.97
torch==2.0.0
transformers==4.29.1
xformers==0.0.20
```

Operational implications:

- Exact pins are safest for reproducing the original demo behavior, but old Torch/xFormers/DeepSpeed wheels may not match a modern CUDA driver or Python version.
- If using newer packages, rerun the bundled smoke/preflight helpers and document the version drift before claiming success.
- `datasets` and `pandas` are needed by evaluation workflows but are not listed in `requirements.txt`; install them only when preparing C-Eval/MMLU.
- Do not install or mutate a user-owned environment broadly. If dependency repair could break the user's environment, ask first or use a private runtime.

## Model asset boundaries

A tiny architecture smoke proves only the local model classes and toy forward path. It does **not** prove that real Baichuan-7B weights or tokenizer assets are available.

For real inference/evaluation, confirm:

- `model_id_or_path` resolves through Hugging Face/ModelScope cache or a local mirror;
- `trust_remote_code=True` is acceptable for that source;
- tokenizer files are present;
- model shards or safetensors/bin files are present;
- the runtime has enough VRAM/offload capacity.

## Backend boundaries

- Full README generation, C-Eval, MMLU, and DeepSpeed pretraining are CUDA-oriented workflows.
- CPU is sufficient for static checks, command rendering, dataset layout validation, and tiny config-only model smoke.
- A tiny CUDA allocation proves only device visibility. It does not prove full 7B memory sufficiency or distributed-training readiness.
- Training mode uses xFormers memory-efficient attention; eval mode uses a safer explicit attention path.

## Safe validation order

1. Start with the relevant sub-skill route from the root `SKILL.md`.
2. Run the safe helper for that workflow:
   - architecture: `sub-skills/architecture-and-loading/scripts/local_model_smoke.py`;
   - evaluation: `sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py`;
   - training: `sub-skills/pretraining-and-deepspeed/scripts/validate_training_inputs.py` and `render_deepspeed_command.py`.
3. Only after preflight passes, ask whether the user wants to spend network/GPU/cluster resources on real inference, benchmarks, or training.
4. If a required model/dataset/GPU resource is absent, report the exact missing item rather than downgrading the claim to a completed run.

## License and trust reminders

- Source code is Apache-2.0.
- Baichuan-7B weights have a separate model license. Confirm usage rights for commercial use, redistribution, or derived weights.
- `trust_remote_code=True` executes model-supplied Python code. Use it only for trusted official sources or reviewed local mirrors.
