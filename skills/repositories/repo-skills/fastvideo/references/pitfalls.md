# FastVideo Operating Pitfalls

## Repository rules

- Read the nearest `AGENTS.md` before editing. Several directories have specific
  rules that override generic assumptions.
- Do not bypass repo-configured `pre-commit` behavior. If a path is excluded,
  that is deliberate.
- Do not maintain duplicate static maps or experiment journals under `.agents/`.
  This generated DisCo skill lives under `skills/disco/fastvideo/` by request.

## Training-stack confusion

- `fastvideo/training/` and `fastvideo/train/` are separate stacks.
- Legacy monolithic pipelines remain authoritative for shipped legacy models.
- The modular trainer is preferred for new training work, but that does not
  authorize migrating an existing legacy pipeline.

## Config-first inference

- `fastvideo generate`, `serve`, and `router-serve` expect `--config` files and
  support dotted overrides.
- Adding a new generation parameter usually requires schema/config/parser tests,
  not just an example change.

## Attention backends

- Set `FASTVIDEO_ATTENTION_BACKEND` before constructing components.
- Recreate the generator/model after changing backend env or config.
- Use selector/platform APIs rather than arbitrary direct env reads.
- A fallback backend passing does not prove that a specialized backend works.

## GPU/runtime evidence

- CPU import success does not prove generation, SSIM, training, CUDA kernels, or
  backend-specific execution.
- `torch.cuda.is_available()` proves only torch device visibility. It does not
  prove a model can fit, a custom kernel works, or a long training job will pass.
- `fastvideo_kernel` wheel import is not the same as rebuilding
  `fastvideo-kernel/` from source.

## Dreamverse

- `dreamverse-server --help` checks import and dependency gates; it does not
  prove full GPU generation or production deployment.
- The full Dreamverse extra/deployment path may require additional packages,
  API credentials, model assets, frontend static files, and ports.
- Keep mock-server protocol tests separate from real server/generation tests.

## Model-porting

- Registry detection and executable pipeline resolution are different concerns.
- `model_index.json` `_class_name` must resolve to an appropriate registered
  pipeline class or wrapper/alias.
- Loader-time changes required for module construction must happen before module
  loading, not in a post-load initializer that runs too late.
- Read each `tests/local_tests/<family>/README.md` before running local parity;
  commands and assets vary by family.

## Expensive commands

Ask or confirm before running commands that may:

- download large model weights or datasets;
- use external credentials/services;
- launch long-lived servers;
- start Slurm/distributed jobs;
- overwrite checkpoints or outputs;
- build CUDA extensions from source;
- run SSIM or full training suites.
