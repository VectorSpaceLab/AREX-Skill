---
name: tirx-kernels
description: "Guides TVM TIRx kernel authoring, execution scopes, layouts, tile
  primitives, lowering, GPU testing, and backend limits."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TIRx Kernel Workflows

Use this route for TVM's native TIRx kernel DSL: `from tvm.script import tirx
as T`, `tvm.tirx.build`, execution scopes, tensor layouts, tile primitives,
lowering, CUDA codegen decisions, and TIRx-specific tests.

## Route

1. Confirm the package imports with TIRx enabled. If not, use
   [`../install-build/SKILL.md`](../install-build/SKILL.md).
2. Classify the task: parser/printer, layout math, well-formedness verifier,
   tile primitive dispatch, lowering/codegen, or GPU execution.
3. For layout or verifier questions, start with
   [`scripts/tirx_layout_probe.py`](scripts/tirx_layout_probe.py) and
   [`references/layout-and-primitives.md`](references/layout-and-primitives.md).
4. For author/compile/run loops, read
   [`references/native-workflows.md`](references/native-workflows.md). Use
   `tvm.tirx.build(..., pipeline="default")` or `tvm.compile(...,
   tir_pipeline="tirx")` only after the PrimFunc/IRModule is well formed.
5. For CUDA, Blackwell, or GPU CI tasks, read
   [`references/gpu-testing.md`](references/gpu-testing.md) before running
   anything. Do not claim GPU or Blackwell coverage from CPU parser/layout tests.
6. Use [`references/troubleshooting.md`](references/troubleshooting.md) for
   parser, layout, scope, dispatch, target, or runtime failures.

## API anchors

```python
from tvm.script import tirx as T
import tvm.tirx

tvm.tirx.build(mod, target=None, pipeline="default")
tvm.compile(mod, target=None, tir_pipeline="tirx")
```

The verified layout/verifier anchors are `TileLayout(spec)`,
`ComposeLayout(per_element, swizzle_len, atom_len, tile_layout,
swizzle_inner=True)`, and
`verify_tirx_well_formed(obj, assert_mode=True, device_func=False)`.

## Boundaries

- General install/build issues: install-build.
- Relax model/pipeline compilation: relax-compile.
- S-TIR schedules and meta-schedule: s-tir-tuning.
- RPC deployment of compiled modules: rpc-deployment.
- External `tirx-kernels` workload registry: optional external dependency, not
  required by this generated skill.
