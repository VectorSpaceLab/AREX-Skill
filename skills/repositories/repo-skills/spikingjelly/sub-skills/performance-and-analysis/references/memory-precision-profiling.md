# Memory, Precision, and Profiling Reference

## Precision policy workflow

Primary public APIs:

- `PrecisionConfig(mode="fp32", strictness="warn", fp8_recipe="auto", device=None)`
- `PrecisionConfig.from_any(config, default_device=None)` accepts `None`, a `PrecisionConfig`, a mode string, or a dictionary.
- `prepare_model_for_precision(model, device, config)` returns `PrecisionArtifacts`.
- `build_capability_report(model, device, mode)` summarizes whether the requested precision mode can convert and execute.
- `validate_capability(report)` raises when a report does not meet the requested mode's runtime contract.
- `save_precision_reports(artifacts, output_dir)` writes policy, capability, conversion, and runtime JSON reports.

Precision modes in the inspected source are `fp32`, `fp16`, `bf16`, `fp8-torchao`, and `fp8-te`. Use `strictness="strict"` when a fallback must fail fast; use `strictness="warn"` when falling back to FP32 is acceptable and should be visible. Call `prepare_model_for_precision` before creating the optimizer because the model may be structurally converted.

FP8 paths are optional. `fp8-torchao` requires `torchao` plus CUDA capability support; `fp8-te` requires Transformer Engine and a compatible FP8/autocast path. In this production run, FP8 stacks were not verified as ready.

## Memory optimization workflow

Primary public API:

```python
memory_optimization(
    net,
    instance,
    dummy_input=None,
    compress_x=None,
    level=None,
    profile=None,
    prefer=None,
    checkpoint_budget=None,
    return_summary=False,
)
```

Use it for training-memory reduction through gradient checkpointing and spike compression. The level/profile contract is:

| Level/profile | Meaning |
| --- | --- |
| `level=0` | no optimization |
| `level=1` / `profile="safe"` | wrap matching modules with gradient checkpoint containers |
| `level=2` / `profile="balanced"` | add spatial split search when `dummy_input` is available |
| `level=3` / `profile="memory"` | add temporal split search when supported |
| `level=4` / `profile="exhaustive"` | try greedy unwraps when they do not increase memory |

If `level > 1` is requested without `dummy_input`, expect fallback to safer behavior. Use `return_summary=True` and inspect `MemOptSummary` fields such as `requested_level`, `applied_level`, `notes`, `gc_wrap_count`, `gc_selected_modules`, and `recommendation`.

## Counting and energy analysis

Use `op_counter.DispatchCounterMode(counters, strict=False)` or `FunctionCounterMode` to collect per-operation statistics. Set `strict=True` only when missing rules should fail fast.

Common counters include FLOP, MAC, AC, SynOp, memory access, neuron state, and analytical energy surfaces. `estimate_compute_energy(model, inputs, config=None)` runs one real forward and returns a `ComputeEnergyReport` with normalized MAC/AC-based energy fields plus auxiliary counts.

`ComputeEnergyCostConfig.fp32()`, `.fp16()`, and `.int8()` select comparison cost tables. These reports are useful for consistent model-to-model comparison; they are not exact hardware power measurements and do not include every memory or runtime-system cost unless the selected counter explicitly models it.

## Safe validation

From this sub-skill directory, run:

```bash
python scripts/memory_precision_smoke.py --case all --json
python scripts/memory_precision_smoke.py --case precision --device cpu --json
```

Use CUDA devices only when the target environment has a working CUDA PyTorch install and the selected optional packages.
