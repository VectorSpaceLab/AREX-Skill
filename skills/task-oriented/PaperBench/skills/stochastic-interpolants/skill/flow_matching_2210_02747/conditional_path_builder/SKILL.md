---
name: conditional_path_builder
description: Build Gaussian and optimal-transport conditional Flow Matching path samples and target vector fields from noise/data pairs.
---
# Conditional Path Builder
Use this skill to construct Flow Matching per-example Gaussian/OT conditional paths. Inputs are `x0`, `x1`, `t`, and `sigma_min`; outputs are `x_t`, `u_t`, and metadata. Workflow: validate shapes/times, compute `sigma_t=1-(1-sigma_min)t`, `x_t=sigma_t*x0+t*x1`, and `u_t=x1-(1-sigma_min)x0`. Run `python tests/test_flow_paths.py`. This skill is not a complete generative model or FID evaluator.
