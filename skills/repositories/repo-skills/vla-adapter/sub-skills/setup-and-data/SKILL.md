---
name: setup-and-data
description: "Install dependencies, place pretrained VLM/checkpoints, and
  validate LIBERO/CALVIN/ALOHA data layouts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Setup and Data (external-checkout adapter)

This is documentation and a read-only layout validator, not a self-contained
runtime. Work against an absolute `VLA_ADAPTER_REPO_ROOT` containing the native
VLA-Adapter checkout; install its `vla-adapter` distribution with
`python -m pip install -e "$VLA_ADAPTER_REPO_ROOT"` so the import is
`prismatic`. Keep pretrained VLM/config assets and native VLA checkpoints in
that checkout or explicit external storage. LIBERO, CALVIN, and ALOHA data and
their simulator/TFDS/ROS stacks are external prerequisites, not bundled here.
Use this sub-skill when planning or validating installation, external data roots,
pretrained model placement, or checkpoint layout before a native workflow.

## Owns

- Base dependency stack from the project README and `pyproject.toml`
- `our_envs.txt` parity checks and version sanity notes
- `pretrained_models/configs` placement and the companion Prismatic VLM weights
- Local checkpoint directory shape and `dataset_statistics.json`
- LIBERO, CALVIN, and ALOHA dataset-root layout
- Storage planning for datasets, local model mirrors, and checkpoint outputs

## Fast path

1. Read [data and checkpoints](references/data-and-checkpoints.md).
2. Validate local paths with the bundled checker from the skill path (it does
   not install packages or run training/evaluation):

   ```bash
   python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/setup-and-data/scripts/validate_data_layout.py" \
     --benchmark libero --data-root "$VLA_ADAPTER_REPO_ROOT/data/libero" \
     --checkpoint "$VLA_ADAPTER_REPO_ROOT/outputs/LIBERO-Spatial-Pro" \
     --vlm-config-dir "$VLA_ADAPTER_REPO_ROOT/pretrained_models/configs"
   ```

3. If you are using ALOHA offline loading, review the ALOHA notes in the reference before enabling local-model mutation.
4. If any path check fails, follow [troubleshooting](references/troubleshooting.md).

## Route away

- Training command profiles, VRAM sizing, LoRA choices, and run scripts: `training`
- Benchmark rollouts, success-rate execution, and result interpretation: `evaluation`
- MsgPack / ROS server-client payloads and robot execution: `deployment`
- Package APIs, model loading internals, and conversion helpers: `package-apis`

## Safety boundaries

- Do not download datasets, rewrite source files, or start training/evaluation.
- Treat the bundled checker as read-only: it only inspects local paths and prints PASS/WARN/FAIL.
- Keep all internal links within this skill subtree.
