# Build and Reports

## Safe rule

`write()` is safe and only materializes files.
`compile()` is still local and CPU-bound, but it can invoke the generated
project's build helper.
`build()` is the expensive step: it may call vendor HLS or FPGA tools and can
run synthesis, co-simulation, or report generation.

Prefer `write()` and the parser APIs whenever the user already has generated
artifacts or pregenerated reports.

## Recommended workflow

1. Create a backend config with `hls4ml.utils.create_config(...)`.
2. Convert the model with the appropriate frontend converter.
3. Call `model.write()` to inspect the generated project tree.
4. Call `model.compile()` only if you want the Python runtime bridge and the
   local compiler environment is ready.
5. Call `model.build(...)` only when the matching vendor toolchain is actually
   available and the user wants synthesis or report generation.
6. Parse existing reports with the `hls4ml.report` APIs instead of rerunning
   synthesis.

## Backend build entry points

| Backend | Build entry point | Safe notes |
| --- | --- | --- |
| Vivado | `model.build(reset=False, csim=True, synth=True, cosim=False, validation=False, export=False, vsynth=False, fifo_opt=False)` | Uses the generated Vivado HLS project and can return a structured Vivado synthesis report |
| Vitis | same shape as Vivado, but through the Vitis toolchain | Uses `vitis-run` and a Vitis-specific build helper; report parsing still reuses the Vivado report parser |
| VivadoAccelerator | Vivado build plus `bitfile=True` in the backend-specific build path | Adds board packaging and bitfile/xclbin handling; only use when board deployment is intended |
| Quartus | `model.build(synth=True, fpgasynth=False, log_level=1, cont_if_large_area=False)` | Requires Intel HLS; FPGA synthesis is a second step and uses `quartus_sh` |
| oneAPI | `model.compile()` for local library build, `model.build(build_type='fpga_emu', run=False)` for CMake-based builds | `compile()` returns the shared library path; `build_type` controls the generated make target |
| Catapult | `model.build(reset=False, csim=True, synth=True, cosim=False, validation=False, vhdl=False, verilog=True, export=False, vsynth=False, fifo_opt=False, bitfile=False, ran_frame=5, sw_opt=False, power=False, da=False, bup=False)` | Catapult flows are broad; keep them off unless the user has the toolchain ready |
| Libero | `model.compile()` and `model.build(reset=False, skip_preqs=True, sw_compile=True, hw=True, cosim=False, rtl_synth=False, fpga=False, **kwargs)` | Build paths are driven by `shls`; extra flags are forwarded to the SmartHLS command line |
| SymbolicExpression | `model.build(reset=False, csim=True, synth=True, cosim=False, validation=False, export=False, vsynth=False)` | Uses Vivado or Vitis HLS depending on the `Compiler` setting |

## Report parser APIs

Use these when reports already exist on disk.

| Backend | Parser / printer | Notes |
| --- | --- | --- |
| Vivado / Vitis | `hls4ml.report.parse_vivado_report(path)` and `hls4ml.report.read_vivado_report(path, full_report=False)` | Returns a dictionary with C-synthesis, Vivado synthesis, and co-simulation sections when present |
| VivadoAccelerator | same Vivado parser family | The accelerator wrapper still emits Vivado-style report artifacts |
| Quartus | `hls4ml.report.parse_quartus_report(path)` and `hls4ml.report.read_quartus_report(path, open_browser=False)` | `read_quartus_report` is the user-facing printer and may need the optional report extra |
| oneAPI | `hls4ml.report.parse_oneapi_report(path)` and `hls4ml.report.print_oneapi_report(report)` | The parser reads the generated JSON report directories |
| Catapult | `hls4ml.report.parse_catapult_report(path)` and `hls4ml.report.read_catapult_report(path, full_report=False)` | Reads Catapult report directories and can also print per-layer QOFR data with `qofr(report)` |
| Libero | `hls4ml.report.parse_libero_report(path)` | Returns simulation, timing, and resource sections from the SmartHLS/Libero summary report |

## Generated-flow reminders

- FIFO depth optimization flows are backend-specific and only make sense when
  actual RTL co-simulation is available.
- External BRAM exposure is a build-time/backend concern, but tuning the
  threshold belongs in the analysis workflow.
- If the user already has a report directory, do not trigger new synthesis just
  to inspect resource or latency numbers.
