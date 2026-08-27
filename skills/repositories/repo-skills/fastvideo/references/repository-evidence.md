# FastVideo Repository Evidence Map

Use this map to decide where to inspect before editing. It is intentionally
repo-relative and should be refreshed when the repository layout changes.

## Top-level orientation

- `README.md`: project overview, install commands, inference/training/Dreamverse
  pointers.
- `pyproject.toml`: Python version, package dependencies, extras, console
  scripts, lint/test tooling.
- `AGENTS.md`: global repository rules for agents.
- `docs/`: user-facing install, inference, training, attention, server contract,
  and contributor docs.
- `examples/`: runnable inference/training examples.
- `scripts/`: checkpoint conversion, dataset preparation, training/distillation,
  inference, Hugging Face utilities, and LoRA extraction.
- `fastvideo-kernel/`: separate custom-kernel package/build flow.
- `apps/dreamverse/`: Dreamverse app, server, UI/deployment docs, and tests.

## Public API and inference

- `fastvideo/__init__.py`: exported public names.
- `fastvideo/entrypoints/video_generator.py`: `VideoGenerator` implementation.
- `fastvideo/api/`: schemas, parser, compatibility, presets, results.
- `fastvideo/fastvideo_args.py`: unified generation/config argument model.
- `fastvideo/entrypoints/cli/`: CLI subcommands and config translation.
- `fastvideo/entrypoints/openai/`: OpenAI-compatible API server.
- `fastvideo/entrypoints/streaming/`: streaming server/router/session/protocol.
- `fastvideo/attention/` and `fastvideo/platforms/`: backend selection and
  platform-specific availability.

Docs/tests:

- `docs/inference/`
- `docs/design/server_contracts/`
- `docs/attention/`
- `fastvideo/tests/api/`
- `fastvideo/tests/entrypoints/`
- `fastvideo/tests/attention/`
- `fastvideo/tests/inference/`
- `fastvideo/tests/ssim/`

## Model-porting

- `fastvideo/models/`: model implementations.
- `fastvideo/configs/models/`: model config dataclasses.
- `fastvideo/configs/pipelines/`: pipeline config dataclasses.
- `fastvideo/pipelines/basic/`: model-family pipeline implementations.
- `fastvideo/registry.py`: registration and detection.
- `scripts/checkpoint_conversion/`: official/HF checkpoint converters.
- `tests/local_tests/`: model-family local smoke/parity instructions.
- `fastvideo/tests/golden_gate/`: model compatibility checks.
- `fastvideo/tests/train/models/`: modular trainer model tests.

Read these AGENTS when in scope:

- `fastvideo/models/AGENTS.md`
- `fastvideo/configs/AGENTS.md`
- `fastvideo/pipelines/AGENTS.md`
- `scripts/checkpoint_conversion/AGENTS.md`

## Training

- `fastvideo/training/`: legacy monolithic per-model training/distillation
  pipelines.
- `fastvideo/train/`: new modular YAML-driven trainer.
- `examples/train/` and `examples/training/`: launch examples.
- `scripts/train/`, `scripts/preprocess/`, `scripts/distill/`,
  `scripts/lora_extraction/`, `scripts/dataset_preparation/`: supporting flows.
- Training tests appear under `fastvideo/tests/train/`,
  `fastvideo/tests/training/`, `fastvideo/tests/distributed/`,
  `fastvideo/tests/dataset/`, `fastvideo/tests/encoders/`,
  `fastvideo/tests/vaes/`, and `fastvideo/tests/workflow/`.

Read:

- `fastvideo/training/AGENTS.md` for legacy work.
- `fastvideo/train/AGENTS.md` for modular trainer work.
- `docs/training/` docs and `fastvideo/train/README.md`.

## Dreamverse

- `apps/dreamverse/AGENTS.md`: Dreamverse-specific rules.
- `apps/dreamverse/README.md`: app overview and runtime usage.
- `apps/dreamverse/dreamverse/`: server package.
- `apps/dreamverse/dreamverse/_deps.py`: runtime dependency gate.
- `apps/dreamverse/dreamverse/main.py`: FastAPI app and WebSocket endpoint.
- `apps/dreamverse/dreamverse/mock_server.py`: protocol-compatible mock server.
- `apps/dreamverse/dreamverse/tests/`: Dreamverse tests.
- `apps/dreamverse/docker/README.md`, `apps/dreamverse/scripts/launch/README.md`,
  and `apps/dreamverse/scripts/modal/README.md`: deployment docs.

## Generated skill artifacts

- Skill graph: `skills/disco/fastvideo/`.
- Construction/test artifacts: `skills/tests/fastvideo-repo-skill/`.
- Do not import into a live router unless explicitly requested later.
