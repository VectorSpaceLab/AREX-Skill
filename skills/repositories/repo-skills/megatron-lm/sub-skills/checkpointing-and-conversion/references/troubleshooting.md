# Checkpoint and conversion troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `WeightsUnpickler` / unsupported global | PyTorch safe loading rejected a class in a trusted checkpoint. | Allow-list only the exact class needed with `torch.serialization.add_safe_globals`; do not disable safe loading broadly. |
| Optimizer state fails but model weights load | Legacy or non-reshardable optimizer state format. | Resume weights-only with `--no-load-optim`, or resave through a compatible fully-reshardable format. |
| Cannot change TP/PP/EP layout on load | Checkpoint format or optimizer metadata cannot reshard. | Use distributed checkpoint formats and fully-reshardable optimizer state before changing layout. |
| Converter rejects hybrid pattern | Unequal attention/MLP occurrences, unsupported symbol, MTP suffix, or source GPT args incompatible with GPT mapping. | Rewrite pattern to architecture-preserving `*-`/`*E` shape or use load-time translation if it supports the intended case. |
| Missing `latest_checkpointed_iteration.txt` | Tool was pointed at a flat metadata directory or output lacks standard tracker. | Point tools at the checkpoint root or create/choose a root consumable by training. |
| Full conversion OOMs on CPU | Converter gathers logical tensors and needs memory proportional to checkpoint size. | Use a machine with more RAM, convert a smaller fixture, or prefer load-time translation if suitable. |
| Async save strategy missing | `nvidia-resiliency-ext` not installed or incompatible async strategy selected. | Install the required package for NVRx or choose the supported legacy strategy while it remains available. |
| Distributed checkpoint save worker fails with `psutil is not installed` | Torch distributed checkpoint asynchronous filesystem writer needs `psutil` in the runtime environment. | Install the repo test/dev dependency that provides `psutil` or add `psutil` to the selected smoke environment, then rerun the bounded checkpoint save/load smoke. |
| FSDP load fails | Format mismatch (`torch_dist` vs `fsdp_dtensor`) or strategy mismatch. | Match `--ckpt-format` with the save path and FSDP mode. |
| HF conversion writes nothing | Host paths/cache/checkpoint dirs were not mounted inside the container or token unavailable. | Verify mounts and credentials; print resolved input/output directories before conversion. |

## Safety rules

- Treat checkpoints from untrusted sources as untrusted code/data. Prefer safe loading and explicit allow-lists.
- Do not overwrite a source checkpoint during conversion. Write to a new target root.
- Validate with a short weights-load or few-step run before long training.
- Preserve optimizer/RNG/scheduler semantics deliberately; do not mix finetune and full-resume semantics accidentally.
