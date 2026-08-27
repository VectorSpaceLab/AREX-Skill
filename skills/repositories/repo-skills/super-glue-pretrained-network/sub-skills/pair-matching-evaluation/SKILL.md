---
name: pair-matching-evaluation
description: "Batch image-pair matching, optional pose evaluation,
  visualization, caching, and pair-list validation for SuperGlue-style runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Pair Matching Evaluation

Use this sub-skill for `match_pairs.py`-style batch runs: validate pair manifests, run bounded matching jobs, interpret `.npz` outputs, choose indoor/outdoor settings, and troubleshoot evaluation or visualization issues.

## Route here when the user asks for
- Batch image-pair matching on a manifest
- Optional pose evaluation with ground truth intrinsics and pose
- Match or evaluation `.npz` contents
- Visualization flags, output names, or file extensions
- Cache reuse, shuffle behavior, or smoke-test commands
- Indoor vs outdoor settings for ScanNet, YFCC, or Phototourism

## Route elsewhere when the user asks for
- Python API or tensor-level SuperPoint/SuperGlue usage: `../programmatic-api/`
- Webcam, video, or image-directory live demo flows: `../live-demo-and-visualization/`

## Bundled helpers
- `references/cli-reference.md`
- `references/data-formats.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/validate_pair_file.py`
- `scripts/run_pair_matching_smoke.py`

## Quick rules
- Match-only manifests usually contain two image paths per row.
- Evaluation manifests must contain 38 tokens per row.
- `--eval` only makes sense when every row has ground truth.
- Use the indoor profile for ScanNet-like indoor pairs; use the outdoor profile for large-view outdoor pairs.
- Keep smoke runs small and cache-aware before scaling up.
- Use `--force_cpu` only when you explicitly want to override CUDA.

## Suggested flow
1. Validate the manifest with the bundled validator.
2. Run the bounded smoke wrapper on one pair.
3. Escalate to the full CLI only after the output keys and metrics look right.
