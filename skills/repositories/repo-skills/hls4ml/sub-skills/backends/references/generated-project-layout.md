# Generated Project Layout

The exact output tree depends on the backend, but the same idea repeats:
configuration at the top, generated firmware or source code in a dedicated
subtree, testbench data in `tb_data/`, and reports in backend-specific build
folders.

## Common pieces

Most generated projects contain some combination of:

- `hls4ml_config.yml`
- a top-level project file for the build system
- generated C++ or source files for the model top function
- generated headers for layer configuration and precision types
- a `firmware/` or `src/firmware/` subtree
- `firmware/weights/` or `src/firmware/weights/`
- `tb_data/` for optional input/output samples
- a build helper script or build system entry point
- optional `.tar.gz` archive when tar output is enabled

`write()` stops after the project tree is generated.
`compile()` adds a local shared library build.
`build()` adds vendor artifacts and report output.

## Backend-specific sketch

| Backend | Main generated shape | Report or build output to expect |
| --- | --- | --- |
| Vivado | `project.tcl`, `build_prj.tcl`, `vivado_synth.tcl`, `build_lib.sh`, `firmware/`, `firmware/weights/`, `tb_data/`, bridge and testbench files | `project_name_prj/solution1/...`, `vivado_synth.rpt`, `tb_data/csim_results.log`, `tb_data/rtl_cosim_results.log` |
| Vitis | Vivado-style tree plus `build_opt.tcl` and Vitis build helpers | Same Vivado-style report shape, with Vitis build logs when the backend logs to files |
| VivadoAccelerator | Vivado-style tree plus accelerator wrapper assets and board-specific packaging files | Bitfile or xclbin artifacts, board handoff files, and Vivado-style reports |
| Quartus | `Makefile`, `build_lib.sh`, `firmware/`, `firmware/weights/`, `tb_data/`, project source, and testbench files | `*-fpga.prj/reports/`, `report.html`, and the summary report used by the parser |
| oneAPI | `CMakeLists.txt`, `src/`, `src/firmware/`, `src/firmware/weights/`, `src/exception_handler.hpp`, bridge/testbench files, `build/` | `build/<project>.fpga.prj/reports/resources/json/*.ndjson` and local library output under `build/` |
| Catapult | `build_prj.tcl`, `build_lib.sh`, `firmware/`, `firmware/weights/`, `tb_data/`, bridge/testbench files | Catapult solution folders plus timing, utilization, and co-simulation reports |
| SymbolicExpression | Vivado/Vitis-like firmware tree plus copied HLS math headers and build scripts | Vivado/Vitis-style reports only when the compiler toolchain is actually available |
| Libero | `config.tcl`, `Makefile`, `Makefile.compile`, `build_lib.sh`, `firmware/`, `firmware/weights/`, `tb_data/`, bridge/testbench files | `hls_output/reports/summary.results.rpt` and other SmartHLS/Libero report files |

## Layout details worth remembering

- `firmware/weights/` usually holds one header per weight array and, when
  enabled, matching text dumps for fast local compilation.
- `tb_data/` is where generated or user-supplied test vectors are copied.
- Backend report paths are not interchangeable; always use the parser that
  matches the generated backend.
- One backend can emit multiple build subfolders; inspect the project tree
  before assuming there is only one report location.
- `write_tar=True` creates a sibling archive beside the generated output
  directory.
