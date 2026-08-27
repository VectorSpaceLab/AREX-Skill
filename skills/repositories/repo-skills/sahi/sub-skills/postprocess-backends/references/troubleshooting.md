# Troubleshooting postprocess backends and duplicate handling

Start by separating three questions:

1. Which backend was configured?
2. Which concrete backend was resolved?
3. Is the surprising output caused by backend execution, match metric, threshold, or class-aware behavior?

Use the safe smoke script first when optional acceleration is suspected:

```bash
python ../scripts/postprocess_backend_smoke.py --backend numpy --print-backend
```

## Failure matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: Unknown backend ...` | `set_postprocess_backend` was called with a name outside `"auto"`, `"numpy"`, `"numba"`, or `"torchvision"`. | Use one of the valid names exactly. If the goal is the default behavior, use `"auto"`. |
| `get_postprocess_backend()` prints `auto`, but a concrete backend appears during execution. | `get_postprocess_backend()` reports configuration, not dispatch resolution. | Call `resolve_backend()` to see the concrete backend. Record both values in diagnostics. |
| `auto` chooses different backends on two machines. | Optional packages or CUDA/MPS visibility differ. | Force `"numpy"` for a baseline, or explicitly install and force the desired optional backend. |
| Forcing `"numba"` fails on the first NMS/NMM call. | `numba` is not installed or cannot import in the runtime. | Install a compatible `numba` stack or use `set_postprocess_backend("numpy")`. |
| First `numba` call is slow, then later calls are faster. | JIT compilation and cache warmup. | Ignore first-call timing when benchmarking, or warm up once before measuring. |
| Forcing `"torchvision"` fails with an import error. | `torch` or `torchvision` is missing or incompatible. | Install a matching torch/torchvision pair, or force `"numpy"`. |
| `auto` does not choose `"torchvision"` even though torch is installed. | Auto-selection requires `torchvision` and visible CUDA or Apple MPS. CPU-only torch is not enough. | Verify CUDA/MPS availability in the runtime, or force and test `"torchvision"` only if CPU fallback is acceptable. |
| `"torchvision"` is selected but is not faster. | Workload is small; IOS/NMM paths include metric-matrix and CPU merge work; device may have fallen back to CPU. | Compare with `"numpy"` on realistic box counts. Keep `"numpy"` if postprocessing is not the bottleneck. |
| GPU is not detected. | Runtime hides CUDA/MPS, torch is CPU-only, or package versions do not expose the backend. | Check torch CUDA/MPS availability outside SAHI. Do not treat this as a SAHI postprocess API bug until torch itself sees the device. |
| Too many boxes remain after NMS. | Threshold is too high, `"IOU"` is too strict for nested boxes, or class-aware mode prevents cross-class suppression. | Lower `match_threshold`; try `match_metric="IOS"` for nested small objects; use class-agnostic mode only if cross-class suppression is intended. |
| Too few boxes remain after NMS. | Threshold is too low, `"IOS"` is overmatching containment-like boxes, or class-agnostic mode lets categories compete. | Raise `match_threshold`; switch back to `"IOU"`; use `batched_nms` or `class_agnostic=False` when categories must stay independent. |
| NMM output is a dictionary instead of a list of boxes. | Direct `greedy_nmm` and `nmm` return merge mappings, not object predictions. | Use the mapping to merge manually, or use `GreedyNMMPostprocess` / `NMMPostprocess` on `ObjectPrediction` lists. |
| NMM returns fewer final objects than expected. | NMM merges instead of suppressing and can propagate transitive matches. | Use GreedyNMM to avoid transitive expansion, raise the threshold, or use NMS if duplicates should be discarded. |
| NMS discarded data that should have contributed to the final object. | NMS suppresses lower-scored boxes rather than merging geometry. | Use GreedyNMM or NMM classes if merged boxes/masks are desired. |
| Direct functions allow different categories to affect each other. | `nms`, `greedy_nmm`, and `nmm` are class-agnostic by design. | Use `batched_nms`, `batched_greedy_nmm`, `batched_nmm`, or `class_agnostic=False` on the class API. |
| Changing backend does not seem to take effect. | Backend was changed after a long-lived inference worker started, or diagnostics are reading only the configured value. | Set the backend once at startup and print both `get_postprocess_backend()` and `resolve_backend()` before the first postprocess call. |
| Exact-threshold cases behave differently than expected. | Low-level match maps use `>= match_threshold`; class-level merge confirmation has its own object-prediction overlap check. Floating-point equality can be brittle. | Avoid relying on exact equality at the threshold. Use a small margin in tests and production thresholds. |
| Invalid or lowercase match metric gives confusing output. | Public documentation supports uppercase `"IOU"` and `"IOS"`; backend internals are optimized for those values. | Validate metric strings before calling direct functions. Prefer constants or controlled CLI choices. |

## Decision checklist for box-count surprises

1. **Is category separation intended?**
   - Yes: use `batched_*` functions or `class_agnostic=False`.
   - No: use global functions or `class_agnostic=True`.
2. **Are boxes similarly sized?**
   - Yes: start with `match_metric="IOU"`.
   - No, one box can be inside another: test `match_metric="IOS"`.
3. **Should overlaps be discarded or merged?**
   - Discard: NMS.
   - Merge only direct neighbors: GreedyNMM.
   - Merge transitive chains: NMM.
4. **Is optional acceleration involved?**
   - If yes, force `"numpy"` and reproduce the issue before debugging `numba` or `torchvision`.
5. **Is the threshold extreme?**
   - `match_threshold <= 0` collapses every pair.
   - Very high thresholds preserve nearly all boxes.

## Difficult diagnostic examples

### Nested small object duplicate

A small box fully inside a large box can have low IoU and high IoS. If the goal is to treat the larger and smaller boxes as duplicates, choose `"IOS"`; if the small object may be real and distinct, keep `"IOU"` or raise the threshold.

### Cross-class overlap

Two classes can predict the same geometry. Class-agnostic NMS keeps only the higher score. Class-aware NMS keeps one per category. Choose based on downstream semantics, not on backend speed.

### NMM versus GreedyNMM chain

Boxes A-B and B-C can merge into one result under NMM even if A-C do not overlap enough. GreedyNMM is safer when slice-boundary duplicates should merge locally but neighboring objects must stay separate.
