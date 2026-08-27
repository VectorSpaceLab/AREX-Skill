# SimpleVLA-RL and RL troubleshooting

SimpleVLA-RL is a separate post-training surface with its own Docker/dependency variant and distributed rollout costs. A documented launch supplies an SFT checkpoint and dataset name to a SimpleVLA-RL experiment through a distributed launcher. Keep this separate from RLinf's Hydra/registry flow.

| Symptom | Likely cause | Remedy |
|---|---|---|
| RL module cannot import | Optional RL dependencies are absent | Verify the RL-specific environment; do not install the whole external stack into the core inspection environment just to make imports pass. |
| RLinf model type unknown | Registry module was not loaded in driver or workers | Set the extension hook as documented and verify both processes import the same registry. |
| Hydra config fails | Wrong config name, suite, override, or missing composed group | Start with the local config tree, print resolved config if supported, and validate before cluster launch. |
| Worker sees different policy | Extension module or checkpoint path is unavailable in worker environment | Check package visibility, mounted paths, and exact actor/rollout model paths. |
| Environment shape mismatch | RL suite observation/action space differs from adapter | Compare adapter preprocessing, action dimension/masks, and environment contract before rollout. |
| CUDA/Ray startup fails | GPU allocation, visible devices, driver, or cluster placement issue | Run the external runtime's backend probes and a minimal worker placement check; do not substitute CPU for an accelerator requirement. |
| Rollout is extremely slow | Environment workers, video decode, or cluster placement bottleneck | Measure rollout and learner stages separately; avoid changing policy semantics to mask infrastructure latency. |
| Checkpoint resumes incorrectly | SFT norm stats or adapter weights are absent/mismatched | Preserve checkpoint lineage and verify norm/action metadata before RL. |
| Core package works but RL job fails | External backend/runtime issue | Keep the failure classified at the RL boundary and record versions/configuration. |
| Training consumes unexpected resources | RL has long rollout and multi-worker costs | Require explicit budget/timeout approval; use config validation and `--help` for routine checks. |
