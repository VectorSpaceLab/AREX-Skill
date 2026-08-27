# Cortex-M Workflows

## Dialect vs Implementation

- Dialect tests validate graph structure and Python rewrite behavior. They are the first choice when no Arm toolchain/FVP is available.
- Implementation tests validate numerical behavior on the target/simulator and require Arm tooling such as Corstone FVP setup.

## Adding or Debugging an Op

1. Define or inspect the op schema and Python reference implementation in the Cortex-M op namespace.
2. Add or adjust quantizer pattern support.
3. Add a graph pass to rewrite the ATen quantized op into the Cortex-M op.
4. Add C++ CMSIS-NN kernel implementation and registration when implementation support is required.
5. Run dialect tests first; run implementation/FVP only after toolchain prerequisites are confirmed.

## Build/Test Planning

- Do not run setup scripts that install Arm tooling or accept licenses without user approval.
- For CI-like reproduction, record toolchain version, FVP availability, and selected test class/method.
- If a test fails before FVP execution, debug export/quantization/pass ordering first.

