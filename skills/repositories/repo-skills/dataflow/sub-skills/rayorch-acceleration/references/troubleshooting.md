# Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| CPU smoke says the optional dependency is missing | `ray` or `rayorch` is not installed in the current environment | Install the Ray/RayOrch backend in that environment and rerun the smoke script. |
| The first Ray stage works but the next one hangs | Earlier actors are still alive and holding GPU reservations | Call `shutdown()` after the stage, or rely on `PipelineABC.compile()`'s compiled runner. For CPU-only smoke, keep `num_gpus_per_replica=0.0`. |
| Output row order differs from the serial version | The wrapped operator is not row-independent or mutates shared state | Only wrap map-style deterministic operators. Keep each chunk's local ordering stable. |
| Fractional GPU allocation never starts | The scheduler cannot satisfy the requested fraction | Lower the replica count, fall back to `0.0` for CPU, or use `1.0` for a full GPU. |
| `env`-related launch errors appear | The RayOrch runtime environment key is unknown or mismatched | Use a registered `env` value or omit it until the runtime env is configured. |
| `compile()` fails before Ray actors start | The operator's input or output keys do not match the storage schema | This is a pipeline-foundations issue. Fix the key mapping first, then retry the Ray wrapper. |
| Memory stays high after the run finishes | Actors are still alive and holding model weights | Call `shutdown()` explicitly when you manage the wrapper yourself. |

## Quick checks
- Use `num_gpus_per_replica=0.0` when you want a CPU proof.
- Check that the wrapped operator is row-independent before increasing `replicas`.
- Prefer the compiled pipeline path when you want automatic actor cleanup.
- Run `scripts/smoke_rayorch_cpu.py` before a longer benchmark or integration pass.
