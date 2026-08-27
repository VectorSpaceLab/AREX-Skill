# TIRx GPU Testing and Backend Limits

## Classification rules

| Capability | Required for selected core? | Evidence needed |
|---|---:|---|
| Parser/printer, layout, verifier | Yes | CPU import and focused Python tests |
| LLVM/CPU compile for non-GPU examples | Yes when selected | CPU/LLVM build and native smoke |
| Generic CUDA codegen | Optional unless user asks | CUDA-enabled TVM build plus toolkit/header evidence |
| CUDA runtime execution | Optional unless user asks | CUDA-enabled TVM build, driver, compatible device, and a passing runtime test |
| Blackwell/TIRx-kernel registry | Optional/excluded by default | Compute capability 10.0+ GPU plus external workload package readiness |

Do not treat an A100 or CPU-only run as evidence for Blackwell-specific
primitive execution. If a test suite skips because compute capability is below
10.0, record the result as optional hardware-blocked unless the user made it a
required backend.

## Safe GPU workflow

1. Run the CPU-safe parser/layout/verifier checks first.
2. Probe TVM runtime support: `tvm.runtime.enabled("cuda")` and
   `tvm.cuda().exist`.
3. Confirm toolkit/header/compiler availability when building or codegen needs
   CUDA libraries.
4. Use a single selected CUDA codegen test before broader GPU tests.
5. Monitor GPU occupancy only for an approved long-running GPU command. Use
   `scripts/monitor_gpu.sh` with an explicit command and timeout.

## When to stop

Stop and report an explicit backend limitation when:

- TVM was built without CUDA but the task requires CUDA execution,
- the host lacks toolkit headers needed by the selected build,
- the detected GPU architecture is older than the test requires,
- the external `tirx-kernels` package or registry data is not available,
- the command would start a long benchmark, require credentials, or download
  large artifacts without approval.

## Suggested native candidates

CPU-safe:

```bash
python -m pytest tests/python/tirx/test_parser_printer.py -xvs
python -m pytest tests/python/tirx/test_layout.py -xvs
python -m pytest tests/python/tirx/test_verifier.py -xvs
```

Optional CUDA/architecture-specific:

```bash
python -m pytest tests/python/tirx/codegen/test_codegen_cuda.py -xvs
python -m pytest tests/python/tirx/codegen/test_codegen_ampere.py -xvs
python -m pytest tests/python/tirx/codegen/test_codegen_blackwell.py -xvs
python -m pytest tests/python/tirx/test_tirx_kernels_registry_correctness.py -xvs
```

Run the optional set only in a backend-prepared environment and classify skipped
architecture gates honestly.
