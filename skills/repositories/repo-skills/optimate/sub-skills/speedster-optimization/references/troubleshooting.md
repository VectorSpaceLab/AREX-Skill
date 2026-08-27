# Speedster Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` for `speedster` or `nebullvm` | The package family is not installed in the active Python. | Install the matching package family and re-run the bundled probe script. |
| `torch.cuda.is_available() == False` on a GPU host | CPU-only torch, incompatible wheel, or driver mismatch. | Fix the torch/CUDA pairing before debugging Speedster itself. |
| A compiler backend is missing | The backend is optional and platform-specific. | Read the NebullVM backend sub-skill before trying the backend installer scripts. |
| Optimized output is `None` | The chosen `metric_drop_ths`, backend filter, or data sample size is too strict. | Relax the parameters and check whether the compiler set was too narrow. |
| `store_latencies=True` creates a file but you do not see a speedup | The best path may still be near parity with the original model. | Treat the latency file as evidence, not as a promise of improvement. |
| Dynamic-shape validation fails | `dynamic_info` does not match the model's real axes. | Recheck the axis tags and input/output dictionaries before rerunning. |

## Next step

If the problem is really about `DataManager`, `check_device`, compiler selection, or optional backend availability, read the NebullVM backend troubleshooting page next.
