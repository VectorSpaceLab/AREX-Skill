# ONNX export

## Export purpose

The BeyondMimic tracker export creates a unified deployment graph for whole-body tracker policies. The output directory contains:

- `unified_pipeline.onnx`: model graph;
- `unified_pipeline.yaml`: metadata and deployment contract.

The export should not require running a simulator; it loads resolved configs and checkpoint weights, creates mock observation context tensors, traces observation/action modules, and optionally validates ONNX runtime output.

## Required inputs

- A checkpoint such as `last.ckpt`.
- `resolved_configs_inference.pt` in the checkpoint directory, or fallback `resolved_configs.pt` if acceptable.
- A CPU-capable Python environment with ProtoMotions, PyTorch, and ONNX Runtime.

## Key export behavior

- Actor observation keys are auto-detected from the agent config.
- Robot dimensions, body names, joint names, anchor body, and future-step indices are extracted from resolved configs.
- The YAML sidecar records input names, semantic keys, shapes, timing, robot/MJCF metadata, PD gains, and post-processing requirements.
- Domain randomization should already be removed/adjusted through inference configs and experiment inference overrides.

## Validation checklist

After export:

1. Inspect `unified_pipeline.yaml` with `scripts/inspect_tracker_yaml.py`.
2. Confirm ONNX inputs match the deployment framework's available sensors/reference data.
3. Confirm root/anchor body indices and quaternion conventions.
4. Confirm motion FPS/control rate and caching expectations.
5. Run standalone MuJoCo validation before integrating with another framework.
6. For hardware, compare the external framework against the standalone MuJoCo contract.

## Common failures

- Missing `resolved_configs*.pt`: export cannot reconstruct model/input contract.
- Wrong checkpoint role: inference-only artifact may lack training state expected by an export path.
- Missing `mimic` control component: tracker export requires mimic future-reference config.
- ONNX Runtime mismatch: install a compatible CPU or GPU ONNX runtime for the target validation mode.
- Unsourced semantic input: update deployment input assembly rather than feeding dummy zeros silently.
