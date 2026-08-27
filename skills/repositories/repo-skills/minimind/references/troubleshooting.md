# MiniMind Cross-cutting Troubleshooting

## First triage

1. Classify the artifact and task: data, raw `.pth`, Transformers directory, API server, core training, or post-training.
2. Run the nearest bundled validator or smoke helper before starting a long job.
3. Check the backend explicitly with the root environment checker; do not infer CUDA support from package installation alone.
4. Confirm all user-provided paths, weight prefixes, hidden size/layer/MoE flags, and tokenizer assets.
5. Keep optional network services, telemetry, reward models, and third-party engines disabled until the local path works.

## Cross-cutting failure matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `torch`, `transformers`, or `datasets` | The runtime environment is incomplete or uses a different Python than the one that installed dependencies. | Run `scripts/check_minimind_environment.py`; install a backend-appropriate PyTorch build and the public requirements in the same environment. |
| `ModuleNotFoundError: fastapi` or `uvicorn` | The OpenAI-compatible server dependencies are not listed in the core requirement file. | Install `fastapi` and `uvicorn` only for the API surface; do not add them to a training-only environment unnecessarily. |
| `torch.cuda.is_available()` is false | CPU PyTorch wheel, incompatible driver/runtime, or a host without CUDA. | Use CPU only for tiny plumbing checks, or install a compatible CUDA build on a supported host before real training/generation. |
| A raw `.pth` is passed to a Transformers/third-party engine | Raw MiniMind state dicts need matching MiniMind modules and config; external engines usually need a model directory. | Run `inference-serving/scripts/check_model_artifacts.py`, then merge/export to a Transformers or Qwen3-compatible directory. |
| `config.json` or tokenizer files are missing | The artifact directory is incomplete or points at an output/checkpoint directory rather than a portable model directory. | Validate the directory; provide `config.json`, tokenizer files, chat template, and weight files together. |
| Weight shape mismatch | Hidden size, layer count, vocab/tokenizer, or dense/MoE setting differs from the checkpoint. | Match all architecture flags, including `use_moe` and `_moe` filename suffix; do not rely on `strict=False` to make incompatible weights valid. |
| Chat template errors or literal tags in output | The tokenizer does not carry the MiniMind template, or a wrapper does not parse `<think>`, `<tool_call>`, and `<tool_response>`. | Validate tokenizer features, use the matching tokenizer, and run the tool-call smoke helper before changing model sampling. |
| Invalid JSONL or silent empty training labels | Wrong schema, multi-line JSON objects, malformed nested JSON, or no assistant target. | Run the relevant JSONL validator with the intended schema and inspect assistant/tool fields before training. |
| Resume cannot find or load state | Stage prefix, hidden size, MoE flag, output directory, or optimizer parameter set changed. | Keep the original stage flags and checkpoint directory; use a fresh model-weight start when optimizer/scaler state is intentionally incompatible. |
| CUDA OOM or very slow training | Sequence length, batch size, generations, reward model, Critic, workers, or MoE routing exceeds the memory budget. | Reduce sequence/generation limits and batch size first; use accumulation; for PPO consider GRPO/CISPO; for Agentic RL cap packed context length. |
| DDP hangs | A rank crashed, backend/device mismatch, uneven path, or rank-local early exit. | Reproduce one process first, disable telemetry/compile, then use `torchrun` with matching CUDA visibility and synchronized failure handling. |
| Online logging blocks or requests credentials | `--use_wandb` enables SwanLab-compatible logging and may require network/account state. | Disable logging for local/debug runs; re-enable only after training behavior is stable. |
| Reward model or SGLang prerequisite is missing | Advanced RL relies on external checkpoints/services not in the repository. | Use `rlhf-agentic` validation and explicit prerequisite checks; fall back to torch rollout or stop if the requested backend is mandatory. |
| Post-training score improves but ordinary Q&A degrades | Narrow reward optimization or tool-call overfitting. | Keep the SFT baseline, evaluate held-out general and tool-use tasks, and choose the checkpoint for the intended capability rather than one scalar reward. |

## Escalation rules

- If the failure is a schema or path problem, fix it with the nearest bundled validator/checker before inspecting model code.
- If the failure is a backend mismatch, do not silently substitute CPU for a required GPU capability; report the limitation.
- If a required external reward model, model weight, dataset, or service is unavailable, keep the route explicitly blocked rather than fabricating a successful run.
- If the repository changed after the provenance snapshot, refresh the repo skill before relying on version-sensitive details.
