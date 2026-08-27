# TIRx Troubleshooting

## Parser and script errors

**Symptom:** TVMScript cannot parse a TIRx function.

- Confirm the dialect import is `from tvm.script import tirx as T`.
- Reduce to one `PrimFunc` and one scope before adding tile primitives.
- Compare the printed IR after a successful parse; parser/printer round trips
  are a strong first signal.

## Layout errors

**Symptom:** `verify_well_formed()` returns false or raises.

- Canonicalize the layout.
- Check axis categories: thread axes and memory axes carry different semantics.
- Remove offsets and replica terms until the smallest bad term remains.
- Use `tirx_layout_probe.py --json` to confirm baseline layout APIs work.

## Well-formedness verifier errors

**Symptom:** `verify_tirx_well_formed` fails on a function or module.

- Run it with `assert_mode=True` to keep the detailed diagnostic.
- Check device-function context and scope nesting.
- Confirm buffers, layout annotations, and primitive calls are consistent.
- Do not proceed to codegen until the verifier issue is understood.

## Primitive dispatch errors

**Symptom:** A primitive has no matching implementation or rejects arguments.

- Confirm target architecture and backend support.
- Check dtype, shape, scope, and input/output layouts.
- Reduce to a single primitive invocation with explicit layout facts.
- For Blackwell-only primitives, verify compute capability 10.0+ hardware.

## Codegen/runtime errors

**Symptom:** Codegen fails for CUDA.

- Confirm TVM was built with CUDA and the toolkit/headers are available.
- Check whether the test is architecture-gated.
- If only CPU/LLVM was prepared, record CUDA as unverified rather than trying
  to reinterpret the failure as a layout issue.

**Symptom:** Codegen succeeds but runtime execution fails.

- Check `tvm.cuda().exist`, module target, device id, and driver compatibility.
- Keep GPU contention separate from compiler correctness; use the monitor script
  only around approved GPU test commands.
