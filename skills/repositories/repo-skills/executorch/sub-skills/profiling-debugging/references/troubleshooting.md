# Profiling and Debugging Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Inspector has timing but no source/module names | ETRecord missing or mismatched | Regenerate ETRecord from the same export and load it with the ETDump. |
| ETDump file empty or missing | Runtime not built/run with event tracing/debug enabled | Enable ETDump/event tracing support in the runtime or selected runner. |
| Delegate timing missing | Backend metadata parser not supplied or backend lacks metadata | Use backend-specific parser if available; otherwise inspect delegate segment timing only. |
| Accuracy mismatch only on device | Backend quantization/layout/runtime issue | Reproduce with deterministic small input; compare eager, exported, and device intermediate outputs. Route QNN-specific layer debugging to `qualcomm`. |
| Memory spike after dynamic-shape export | Loose upper bounds in dynamic dimensions | Re-export with tighter bounds and inspect memory planning. |

