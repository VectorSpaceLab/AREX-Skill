# Cortex-M Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Quantized op remains ATen after passes | Pattern not matched or compile config removed required op | Inspect quantizer support and pass ordering; use dialect test to view graph. |
| Dialect test passes but implementation fails | C++ kernel, CMSIS-NN constraints, or FVP/runtime mismatch | Compare reference op output and implementation output on tiny inputs; verify toolchain/FVP. |
| Toolchain setup requires license/EULA | Arm tooling prerequisite | Stop for user approval before running setup. |
| Unsupported dtype/shape | CMSIS-NN kernel has stricter constraints | Add validation or fallback; do not claim full support from dialect-only tests. |

