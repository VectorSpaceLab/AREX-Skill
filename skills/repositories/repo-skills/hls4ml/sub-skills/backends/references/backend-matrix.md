# Backend Matrix

The current backend registry contains these built-ins:
`vivado`, `vivadoaccelerator`, `vitis`, `quartus`, `catapult`,
`symbolicexpression`, `oneapi`, and `libero`.

Every `create_config(...)` call starts with the common project defaults:
`OutputDir='my-hls-test'`, `ProjectName='myproject'`, and `Version='1.0.0'`
unless you override them.

## Quick selection guide

| Backend | Typical target | Default config highlights | Required tools / notes | Status |
| --- | --- | --- | --- | --- |
| Vivado | AMD/Xilinx IP for Vivado designs | `Part='xcvu13p-flga2577-2-e'`, `ClockPeriod=5`, `ClockUncertainty='12.5%'`, `IOType='io_parallel'` | `vivado_hls` on `PATH`; local `compile()` is separate from vendor synthesis | Legacy backend; use Vitis for new AMD/Xilinx work |
| VivadoAccelerator | PYNQ and accelerator overlays | `Board='pynq-z2'`, `Part` is derived from the board, `ClockPeriod=5`, `ClockUncertainty='12.5%'`, `Interface='axi_stream'`, `Driver='python'` | Vivado toolchain plus board flow; Alveo boards also use a Vitis platform | Specialized deployment wrapper on top of Vivado |
| Vitis | AMD/Xilinx IP for Vitis HLS | `Part='xcvu13p-flga2577-2-e'`, `ClockPeriod=5`, `ClockUncertainty='27%'`, `IOType='io_parallel'` | `vitis-run` on `PATH`; local `compile()` is still separate from synthesis | Preferred AMD/Xilinx backend for new projects |
| Quartus | Intel FPGA HLS projects | `Part='Arria10'`, `ClockPeriod=5`, `IOType='io_parallel'` | Intel HLS compiler (`i++`) is required; optional Quartus synthesis uses `quartus_sh` | Deprecated; migrate to oneAPI |
| Catapult | Siemens Catapult HLS | `Technology='fpga'`, `Part='xcku115-flvb2104-2-i'`, `ClockPeriod=5`, `IOType='io_parallel'` | `catapult` on `PATH`, or under `MGC_HOME`/`CATAPULT_HOME` | Supported, but docs are sparse and flows are specialized |
| SymbolicExpression | Symbolic-regression expressions | `Part='xcvu9p-flga2577-2-e'`, `ClockPeriod=5`, compiler defaults to `vivado_hls` | Needs Vivado/Vitis HLS include and library paths for math support | Niche backend for LUT-based expressions |
| oneAPI | Intel FPGA SYCL projects | `Part='Agilex7'`, `ClockPeriod=5`, `HyperoptHandshake=False`, `IOType='io_parallel'` | `icpx`, `cmake`, and oneAPI FPGA compiler; current build flow is CMake-based | Experimental; preferred Intel path for new work |
| Libero | Microchip PolarFire / SmartHLS | `FPGAFamily='PolarFire'`, `Part='MPF300'`, `Board='hw_only'`, `ClockPeriod=5`, `IOType='io_parallel'` | `shls` must be available; `SmartHLSPath` is inferred from it if not supplied | Supported, but requires SmartHLS/Libero environment |

## Board and part notes

### VivadoAccelerator boards

Supported board names in the current runtime are:
`pynq-z2`, `zcu102`, `alveo-u50`, `alveo-u250`, `alveo-u200`, and `alveo-u280`.

Board-to-part mapping is board-specific. If you provide a mismatched `Part`,
the accelerator config corrects it to the board's known part and warns.

### Catapult technology mode

`Technology='fpga'` is the default path. The backend also accepts ASIC-mode
settings through `ASICLibs`, but the generated project still depends on the
Catapult toolchain.

## Practical defaults to remember

- `ClockPeriod` defaults to `5` across the backends above.
- `ProjectName` defaults to `myproject`.
- `OutputDir` defaults to `my-hls-test`.
- `io_parallel` is the default I/O mode unless the backend adds extra wrapper
  behavior.
- `Vivado` and `Vitis` differ mainly in clock uncertainty and toolchain entry
  points.
- `Quartus` only implements the resource strategy family.
- `oneAPI` currently supports the resource-style backend flow and does not aim
  to behave like the Vivado/Vitis writer tree.
- `Libero` config creation can fail if `shls` is missing; treat that as a
  prerequisite issue, not a package bug.
- `SymbolicExpression` can fail if Vivado/Vitis HLS headers and libraries are
  not discoverable; treat that as a prerequisite issue, not a package bug.
