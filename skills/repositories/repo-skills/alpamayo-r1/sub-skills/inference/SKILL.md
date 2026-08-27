---
name: inference
description: "End-to-end Alpamayo R1 multimodal driving inference, sample
  generation, and troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Alpamayo R1 Inference

Use this sub-skill when the user wants to run, inspect, or adapt the Alpamayo R1 inference path on a PhysicalAI-AV clip.

## What this covers

- Load a gated PhysicalAI-AV clip and egomotion history/future.
- Build the multimodal chat prompt from stacked camera frames.
- Load `nvidia/Alpamayo-R1-10B` on CUDA with the Alpamayo tokenizer and processor.
- Sample future trajectories plus Chain-of-Causation text traces.
- Compare predicted trajectories with ground truth and visualize them in notebook style.
- Troubleshoot HF gating, CUDA OOM, flash-attn / SDPA fallback, device placement, prompt rank, and early `t0_us` failures.

## What this does not cover

- Training, SFT, RL post-training, or repo maintenance.
- Import/export plumbing or package provenance.
- Any workflow that depends on the original checkout at runtime.

## Fast route

1. Read `references/api-reference.md` for the public call contract.
2. Read `references/data-formats.md` for shapes, frames, and output semantics.
3. Follow `references/workflows.md` for the end-to-end inference flow and notebook-style visualization.
4. If anything fails, open `references/troubleshooting.md`.
5. Run `scripts/run_inference_smoke.py` as the bundled smoke test.

## Key defaults

- Default model id: `nvidia/Alpamayo-R1-10B`
- Default loader history / future / camera settings: 16 steps, 64 steps, 4 cameras
- Default attention path: `flash_attention_2`
- SDPA is a fallback for flash-attn incompatibility, not a replacement for the CUDA path.

## See also

- `../../SKILL.md` for the root router
- `../../references/repo-provenance.md`
- `../../references/repo-routing-metadata.json`
- `../../references/troubleshooting.md` for shared Alpamayo R1 troubleshooting
- `references/api-reference.md`
- `references/data-formats.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/run_inference_smoke.py`
