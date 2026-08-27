# Profiling and Debugging Workflows

## Artifact Roles

| Artifact | Created when | Use |
| --- | --- | --- |
| ETRecord | Export time | Maps runtime events back to exported graphs, source/module hierarchy, and delegate segments. |
| ETDump | Runtime execution | Stores performance/debug data captured during model loading/execution. |
| Debug buffer | Runtime execution with debug enabled | Extra data used by Inspector for richer output. |
| BundledProgram | Export/test packaging | Carries representative inputs and expected outputs for runtime validation. |

## Typical Flow

1. Export model with debug metadata enabled when available.
2. Run the model with ETDump collection enabled in the runtime or runner.
3. Load ETRecord + ETDump into Inspector.
4. Print tabular data and identify slow ops, delegate regions, or source/module hotspots.
5. If accuracy diverges, compare eager, AOT, and runtime intermediate outputs with tiny deterministic inputs.

## Runtime ETDump Pattern

When Python runtime pybindings support ETDump:

```python
program = runtime.load_program("model.pte", enable_etdump=True, debug_buffer_size=int(1e7))
method = program.load_method("forward")
outputs = method.execute(inputs)
program.write_etdump_result_to_file("run.etdp", "debug.bin")
```

## Triage Questions

- Is the performance problem in export-time partitioning, runtime backend execution, data loading, or app preprocessing?
- Are debug artifacts from the same `.pte` build and input shape as the failing run?
- Are backend delegate metadata parsers required for vendor-specific timing?

