---
name: profiling-debugging
description: "Profile and debug ExecuTorch execution with ETRecord, ETDump,
  Inspector, visualization, delegate debug data, intermediate outputs, and
  runtime/export triage."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# profiling-debugging

Use this sub-skill when the user asks about ExecuTorch profiling, ETDump, ETRecord, Inspector, delegate debugging, model visualization, memory-planning inspection, intermediate outputs, or runtime/export accuracy/performance triage.

## Route Here For

- Enabling and collecting ETDump at runtime.
- Generating ETRecord during export and using it to map runtime events to graph/source/module hierarchy.
- Loading artifacts with `executorch.devtools.Inspector`.
- Comparing delegate and CPU outputs, inspecting numerical divergence, and deciding when to route QNN-specific per-layer debugging to `../qualcomm/SKILL.md`.
- Understanding memory planning and visualization artifacts.

## Fast Path

1. Ask which artifacts the user already has: `.pte`, ETRecord, ETDump, debug buffer, eager reference outputs, backend logs.
2. If no ETRecord exists and source model/export is available, regenerate export with ETRecord enabled before collecting runtime data.
3. If only ETDump exists, perform raw timing inspection but explain that source/module attribution may be limited.
4. Use [profiling workflows](references/profiling-workflows.md) and [API reference](references/api-reference.md).
5. For artifact sanity checks, run:

```bash
python scripts/inspect_etdump_summary.py --etdump path/to/run.etdp --etrecord path/to/model.etrecord
```

The helper checks file presence and Inspector import availability; it does not parse private model data unless the installed package supports it.

## Cross-Links

- Export and ETRecord generation details: `../export-runtime/SKILL.md`.
- QNN-specific intermediate output debugger: `../qualcomm/SKILL.md`.
- Backend choice and fallback behavior: `../backend-selection/SKILL.md`.

