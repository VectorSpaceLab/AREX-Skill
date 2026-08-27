# Troubleshooting

## Common failures and recovery steps

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError: Unknown model: ...` | The model key is not in the registry. | Call `show_avai_models()` and use an exact key such as `osnet_x0_25`, `osnet_x1_0`, or `resnet50`. |
| Checkpoint load warning or no matched layers | The checkpoint does not match the selected architecture, or the file path is wrong. | Verify the local checkpoint exists, confirm the `model_name`, and load only with the matching architecture when possible. |
| Unexpected network/download activity | `FeatureExtractor` fell back to pretrained loading because `model_path` was missing or invalid. | Pass a verified local checkpoint path, or build the lower-level model with `pretrained=False` and load the weights manually. |
| `RuntimeError` on CUDA device selection | The selected device is unavailable or does not match the tensors. | Use `device='cpu'` for smoke tests, or choose a visible CUDA device such as `cuda:0` only when GPU support is available. |
| `TypeError` / `NotImplementedError` from `FeatureExtractor` input | The input type or tensor rank is unsupported. | Use one of the accepted forms: image path string, list of image paths, HWC numpy array, list of HWC arrays, or `C/H/W` or `B/C/H/W` tensor. |
| Metric shape mismatch | Feature tensors have different widths, or a distance matrix is not 2-D. | Ensure both feature matrices are 2-D with the same embedding dimension before calling `compute_distance_matrix()`. |
| `AssertionError: Error: all query identities do not appear in gallery` | Every query identity is missing from the gallery labels. | Include at least one gallery sample per query identity before calling `evaluate_rank()`. |
| Rank results differ between runs | CUHK03 metric sampling is stochastic, or you are using a random smoke fixture. | Use Market1501 metric for deterministic smoke checks, or repeat CUHK03 evaluation multiple times and average. |
| Cython is missing | The compiled rank extension is unavailable. | Keep `use_cython=True` if available, otherwise accept the Python fallback. The metrics stay correct; only speed changes. |
| `forward() got unexpected keyword argument 'return_featuremaps'` | The model does not support activation-map extraction. | Use an OSNet-family model, or add a `return_featuremaps` argument that returns the last convolutional feature maps at eval time. |
| Activation-map output is not 4-D | The model returns pooled embeddings instead of convolutional feature maps. | Ensure `return_featuremaps=True` produces `(B, C, H, W)` output before calling the actmap workflow. |
| GPU-Re-Ranking cannot be imported | The optional external CUDA extension is not installed or not selected. | Use the bundled CPU `re_ranking(...)` helper instead. Only treat the external GPU path as optional. |

## Notes for helper scripts

- `scripts/feature_extraction_smoke.py` should never download weights.
- `scripts/compare_embeddings.py` should reject a missing or nonexistent `--weights` path before it builds the extractor.
- `scripts/visualize_actmap.py` should preview by default and require `--run` for the expensive visualization pass.
