# Detection and Distance Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Detector output is a DataFrame, not a dense mask | sktime uses sparse event/segment outputs | Inspect intervals/ilocs and map to the original index. |
| `mode` changes output rows | Points vs segments semantics differ | Choose `mode="points"` or `mode="segments"` intentionally. |
| DTW class missing package | Optional backend absent | Install the narrow alignment/distance extra or use `ScipyDist` fallback. |
| Distance matrix wrong shape | X/X2 orientation or pairwise transformer misuse | Check input containers and whether X2 was supplied. |
| Kernel diagonal not zero | Kernels are similarities, not distances | Validate symmetry/PSD expectations separately. |
