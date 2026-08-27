# Developer Notes for Agents

sd-scripts exposes most public behavior through root Python scripts plus shared modules in `library/`, network modules in `networks/`, utility scripts in `tools/`, and preprocessing helpers in `finetune/`.

## Codebase Shape

- `setup.py` installs the distribution as `library`; the import root verified during skill generation was `library`.
- Root scripts such as `train_network.py`, `sdxl_train_network.py`, `flux_train_network.py`, `gen_img.py`, and `sdxl_gen_img.py` are user-facing CLIs rather than package console entry points.
- `docs/` is the main source of user workflow truth; use source code and parser definitions to confirm flags when docs are ambiguous.
- Tests under `tests/` are behavior evidence but many require the ML dependency stack. Select focused safe tests only after the runtime skill has been integrated.

## Agent Behavior

- Treat command construction separately from command execution. Build templates first, then ask/confirm before long GPU jobs or large writes.
- Prefer English docs where present; Japanese/Chinese docs may contain additional historical details but should not be the only source for new public guidance unless they are unique.
- For model-family workflows, route users by architecture first: SD1/2, SDXL, SD3, FLUX/Chroma, Lumina, HunyuanImage, or Anima.
- Keep dataset/config diagnosis in `data-preparation` and execution command choices in `training`.
- Use `model-utilities` for checkpoint and adapter transformations, and apply stricter overwrite/disk/backups checks than for read-only metadata inspection.

## Safe Verification Bias

- Safe: parser/help checks, read-only metadata inspection, TOML/JSON validation on tiny fixtures, command-builder output assertions.
- Usually skip: full training, full generation, cache creation, model conversion, LoRA extraction, checkpoint merge, caption/tag model downloads, and GPU-only manual tests.
