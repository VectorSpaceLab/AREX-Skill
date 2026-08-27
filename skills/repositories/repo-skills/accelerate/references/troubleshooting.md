# Cross-Cutting Troubleshooting

Use this reference for Accelerate problems that affect multiple sub-skills. For workflow-specific errors, route to the nearest sub-skill troubleshooting file.

## Import Or Install Fails

Symptoms:

- `ModuleNotFoundError: No module named 'accelerate'`
- `ImportError` for `torch`, `safetensors`, `huggingface_hub`, or optional backend packages
- `pip check` reports incompatible package versions

Fixes:

1. Install the base package first: `pip install accelerate`.
2. Confirm `python -c "import accelerate; print(accelerate.__version__)"` uses the intended Python environment.
3. Install optional packages only for selected workflows: `deepspeed` for DeepSpeed, `torch_xla` for TPU, tracker packages for external logging, or model libraries for inference examples.
4. If a local checkout shadows an installed distribution, run the import check from a clean working directory or install the checkout editable deliberately.

## CLI Command Is Missing Or Uses The Wrong Environment

Symptoms:

- `accelerate: command not found`
- `accelerate --help` works in one shell but not another
- CLI runs against a different Python than the package import check

Fixes:

1. Prefer `python -m accelerate.commands.env --help` or the absolute environment `bin/accelerate` when diagnosing PATH issues.
2. Reinstall into the active environment if `python -c "import accelerate"` succeeds but `accelerate --help` is unavailable.
3. Use `sub-skills/configuration-and-cli/scripts/print_accelerate_help_summary.py` to check which CLI subcommands are visible.

## Optional Backend Or Hardware Is Unavailable

Symptoms:

- DeepSpeed, FSDP, TPU/XLA, FP8, bitsandbytes, torchao, or tracker imports fail.
- CUDA/TPU/Gaudi hardware is not visible.
- A config validates syntactically but launch fails immediately on backend setup.

Fixes:

1. Route to `sub-skills/distributed-training-backends/` for backend-specific install, config, and hardware requirements.
2. Run static config validation before distributed launch.
3. Treat CPU-only inspection as sufficient for API/config planning, not as proof that GPU/TPU execution will work.
4. Stop and report the missing backend or hardware when the user requested an execution check that the machine cannot support.

## Distributed Job Hangs

Common causes:

- Mismatched tensor shapes in collective operations.
- One rank exits or early-stops while other ranks continue.
- Wrong `num_processes`, `machine_rank`, `main_process_ip`, or `main_process_port`.
- Dataset/dataloader length differs across processes.

Fixes:

1. Enable debug mode with `accelerate launch --debug ...` or `ACCELERATE_DEBUG_MODE=1`.
2. Use `accelerator.set_trigger()` and `accelerator.check_trigger()` for distributed early stopping.
3. Verify launch topology in `sub-skills/configuration-and-cli/`.
4. Check training-loop gather/reduce guidance in `sub-skills/training-loop-integration/references/troubleshooting.md`.

## Safe Verification Ladder

Use the least risky check that proves the claim:

1. `--help` for CLI and bundled helper scripts.
2. Static YAML/JSON validation for config files.
3. Tiny CPU smoke tests for `Accelerator`, checkpointing, and meta-device big-model APIs.
4. Focused native tests only after the generated skill is integrated and the environment supports them.
5. Full distributed, GPU/TPU, model-download, tracker-service, or SLURM runs only with explicit user approval and matching infrastructure.
