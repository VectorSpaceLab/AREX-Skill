# Repository provenance

## Source identity

- Repository skill id: `align-anything`
- Source repository: Align-Anything
- Branch inspected: `main`
- Commit inspected: `3f9decc221be74b2052e712e3a32e155686ec6ec`
- Short revision: `3f9decc`
- Package import name: `align_anything`
- Package version observed: `0.0.1.dev0`
- Construction decision policy: agent-confirmed extraction scope; no import in this session.

## Source state

The source package was restored to a clean tracked state after temporary environment/debug edits. Generated skill files live under the repository `skills/` output area and are not part of the source package implementation.

## Evidence paths distilled

The skill was distilled from relative repository evidence, including:

- `README.md`, `setup.py`, `pyproject.toml`
- `align_anything/configs/`, including train/evaluation/vLLM/DeepSpeed configs and template code
- `align_anything/trainers/` for supervised, preference, RLHF, remote-RM, diffusion, Janus, and VLA/action trainers
- `align_anything/datasets/` for supervised, preference, prompt-only, diffusion, and multimodal data classes
- `align_anything/models/`, especially model registry, pretrained loading, reward/value wrappers, and multimodal wrappers
- `align_anything/models/remote_rm/` for reward server/client/function contracts
- `align_anything/serve/` for text, multimodal, and omni-modal CLI entry points
- `align_anything/utils/` for device, template, media, and process helpers
- `docs/source/` training, data, evaluation, tutorial, Chameleon, and SPOC materials
- representative source scripts under `scripts/`
- satellite project evidence under `projects/`

## Runtime verification facts at construction

- Python package imports: passed for `align_anything`.
- Core pretrained loader import: passed for `align_anything.models.pretrained_model.load_pretrained_models`.
- Serving module imports: passed for text, multimodal, and omni-modal CLI modules.
- Remote reward model module imports: passed for server, launcher, and client modules.
- Representative trainer imports: passed for text-to-text SFT/DPO/PPO/PPO remote RM, text-image-to-text SFT, text-audio-to-text PPO, and any-to-any SFT.
- Optional Janus trainer import: blocked by missing optional Janus-compatible package; covered as optional/project workflow rather than base verified runtime.
- CUDA PyTorch availability: observed during construction; future users must re-check in their active runtime.
- DeepSpeed custom-op warnings: observed when no CUDA toolkit path was configured; documented as troubleshooting.

## Staleness signals

Refresh this skill if any of these change materially:

- trainer module names, config directory layout, or CLI override parser behavior;
- model registry or pretrained loader signatures;
- serving CLI argument names or Gradio launch behavior;
- remote reward server endpoint/payload/reward-function contract;
- satellite project package boundaries or Eval-Anything integration;
- package dependency pins, supported CUDA/PyTorch/Transformers versions, or optional backend requirements.
