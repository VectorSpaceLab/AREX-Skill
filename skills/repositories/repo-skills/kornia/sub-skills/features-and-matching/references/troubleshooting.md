# Feature and matching troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cdist` or matcher raises a shape error | Descriptor dimensions differ or descriptors are not 2D `(N,D)`. | Print descriptor shapes, select one batch item if needed, and ensure both descriptors share `D`. |
| Matcher returns zero rows | Ratio/mutual/geometric filtering rejected all pairs, or one descriptor set is empty. | Check raw `match_nn` first, lower thresholds only with justification, and handle empty results before geometry handoff. |
| Keypoints are swapped after matching | Match index columns were interpreted incorrectly. | Use `idxs[:,0]` for the first descriptor/keypoint set and `idxs[:,1]` for the second. |
| Learned matcher constructor tries to download weights | A pretrained option was requested without a local cache. | Use a non-pretrained/synthetic smoke for environment checks, or explicitly supply/authorize weight acquisition. |
| `OnnxLightGlue` import fails | ONNX Runtime optional dependencies are not installed. | Install the ONNX runtime stack only when deployment is selected; otherwise use the PyTorch matcher path. |
| CUDA half-precision matching fails | Backend lacks a half-precision distance/kernel path or a model layer has dtype constraints. | Retry float32 on the same device; use isolated half-precision verification before claiming support. |
| LoFTR/LightGlue output format is unexpected | Learned matchers return dictionaries or model-specific structures rather than `(dists, idxs)`. | Inspect keys once, then normalize to explicit point arrays before geometry handoff. |
| Geometry estimation fails after plausible matches | Points are degenerate, coordinates are in different spaces, or the wrong index column was used. | Verify point order and coordinate space, then route to `../geometry-vision/SKILL.md` for robust-estimation checks. |

## Debugging sequence

1. Run `scripts/matching_smoke.py --device cpu` to prove base descriptor matching works.
2. Print descriptor/keypoint/LAF shapes and devices.
3. Compare `match_nn` against stricter matchers to identify whether filtering is the issue.
4. For learned models, verify weights/cache and optional dependencies separately from the matching algorithm.
5. Convert matches to explicit point arrays before calling any geometry solver.
