---
name: postprocess-backends
description: "Guide SAHI NMS/NMM backend selection, match metrics, class-aware
  behavior, and direct postprocess APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# postprocess-backends

Use this sub-skill when the task is to choose or debug SAHI postprocessing backends and duplicate-removal behavior: `set_postprocess_backend`, `get_postprocess_backend`, `resolve_backend`, direct array calls such as `nms`, `batched_nms`, `greedy_nmm`, `nmm`, and object-list postprocessors such as `NMSPostprocess`, `NMMPostprocess`, and `GreedyNMMPostprocess`.

Do not use this sub-skill as the owner for detector loading, weights, or framework wrappers; route those to `../model-integrations/SKILL.md`. For where to pass `postprocess_type`, `postprocess_match_metric`, `postprocess_match_threshold`, or class-agnostic options in prediction pipelines, route to `../sliced-inference/SKILL.md`. For result object export, serialization, COCO JSON, or visualization payloads, route to `../annotations-and-results/SKILL.md`.

## Start here

1. Distinguish backend state before changing code:
   - `get_postprocess_backend()` returns the configured value, which can remain `"auto"`.
   - `resolve_backend()` returns the concrete backend used by dispatch: `"numpy"`, `"numba"`, or `"torchvision"`.
   - See [Backend selection and acceleration limits](references/backend-reference.md).
2. Pick the postprocess operation:
   - Use NMS when duplicates should be discarded.
   - Use GreedyNMM when overlapping detections should be merged by direct highest-score neighbors.
   - Use NMM when transitive overlaps should also merge into the same keeper.
   - See [Direct API and class reference](references/api-reference.md).
3. Decide class behavior:
   - Class-agnostic mode lets all categories compete or merge together.
   - Class-aware mode runs independently per category; use `batched_*` direct functions or `class_agnostic=False` on postprocess classes.
4. Decide the match metric:
   - `"IOU"` is the default for similarly sized boxes.
   - `"IOS"` is often the correct choice for nested small objects, where a small box inside a larger duplicate has low IoU but high intersection-over-smaller.
5. If optional acceleration behaves inconsistently, force `"numpy"` first and run the bundled [safe smoke script](scripts/postprocess_backend_smoke.py).
6. If the number of boxes is surprising, check [Troubleshooting](references/troubleshooting.md) before changing model thresholds.

## Safe local smoke

From this sub-skill directory, run:

```bash
python scripts/postprocess_backend_smoke.py --print-backend
```

The smoke script builds tiny in-memory arrays with columns `[x1, y1, x2, y2, score, category_id]`, forces the `numpy` backend by default, exercises `nms`, `batched_nms`, `greedy_nmm`, and `nmm`, and asserts deterministic outputs. It does not download data, train models, use credentials, contact the network, or write files.

## Boundaries and assumptions

- Backend selection is process-global and should be set at startup, before threaded inference or batched prediction loops.
- Optional acceleration is opportunistic: `numba` requires the optional package and has first-call JIT cost; `torchvision` requires compatible `torch`/`torchvision` and only auto-selects when CUDA or Apple MPS is available.
- Low-level direct APIs operate on numpy-compatible arrays and return indices or merge mappings, not serialized result objects.
- Prediction-pipeline parameter placement is intentionally excluded here; use `../sliced-inference/SKILL.md` for `get_sliced_prediction` and CLI placement details.
