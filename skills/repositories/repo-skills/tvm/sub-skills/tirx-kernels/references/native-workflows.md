# TIRx Native Workflow Playbook

## What TIRx is for

TIRx is TVM's native kernel authoring stack for expressing device-level tensor
programs, lowering them through a TIRx-specific pipeline, and compiling them for
target backends. It is lower level than Relax and more specialized than ordinary
S-TIR schedules.

Use it when the task asks for:

- `from tvm.script import tirx as T`,
- explicit cluster/CTA/warpgroup/warp/thread scopes,
- TIRx `PrimFunc` well-formedness,
- `TileLayout` or `ComposeLayout`,
- CUDA tile primitives, TMA, MMA, TMEM, or dispatch selection,
- `tvm.tirx.build` or `tvm.compile(..., tir_pipeline="tirx")`.

## Author-inspect-compile loop

1. **Author a minimal PrimFunc.** Keep one kernel and one operation family while
   debugging parser or lowering behavior.
2. **Print or show the IR.** Parser/printer tests are ground truth for whether
   TVMScript syntax round-trips.
3. **Validate well-formedness.** Use
   `tvm.tirx.analysis.verify_tirx_well_formed(func_or_mod, assert_mode=True)`.
4. **Validate layout objects separately.** Use `TileLayout(...).canonicalize()`
   and `.verify_well_formed()` before attaching layout-heavy code to a kernel.
5. **Select target and pipeline.** Use `tvm.tirx.build(mod, target, pipeline)`
   for TIRx build flows, or `tvm.compile(mod, target, tir_pipeline="tirx")`
   when the unified compile entry point is appropriate.
6. **Run only when the backend is verified.** CUDA codegen and device execution
   require a CUDA-enabled TVM build and compatible runtime device.

## Execution scope concepts

TIRx tracks scopes such as cluster, CTA, warpgroup, warp, and thread. Layout and
primitive legality often depends on whether axes are tied to the expected scope:
thread axes such as `laneid`, `warpid`, `tid_in_wg`, and `wgid` are not
interchangeable with memory axes such as `m`, `P`, `F`, `TCol`, and `TLane`.

When a failure mentions disconnected scope, wrong scope, or invalid binding:

- inspect the layout's scope with `layout.get_scope()` when available,
- canonicalize the layout before comparing it,
- reduce the kernel to the smallest scope combination that still fails,
- verify the PrimFunc before running codegen.

## Lowering pipeline

TIRx lowering prepares script-level TIRx constructs for target code generation.
The exact pass sequence can change by checkout, so treat the public `tvm.tirx`
API and lowering docs as the stable entry points rather than hard-coding private
pass names. When bisecting a pipeline failure, try:

- parser/printer round trip,
- well-formedness verification,
- layout probe,
- `tvm.tirx.build` with default pipeline,
- `tvm.compile(..., tir_pipeline="tirx")` if the task uses the unified entry
  point.

## Minimal backend-safe checks

- Parser/printer and well-formedness tests are CPU-safe and do not prove GPU
  execution.
- Layout tests are CPU-safe and useful for reasoning about dispatch failures.
- CUDA codegen tests require a TVM build configured with CUDA support.
- Runtime kernel execution requires a compatible device and driver.
- Blackwell-specific tests require compute capability 10.0-class hardware.
