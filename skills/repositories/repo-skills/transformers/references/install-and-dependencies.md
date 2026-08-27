# Install And Dependencies

Use this reference to choose a safe Transformers install for the target workflow without over-installing optional backends.

## Minimal Install Choices

| Workflow | Typical install |
| --- | --- |
| Config/tokenizer inspection | `python -m pip install transformers` |
| PyTorch inference and generation | `python -m pip install "transformers[torch]"` plus a PyTorch wheel suitable for the host |
| Vision pipelines/processors | `python -m pip install "transformers[vision]"` and ensure PyTorch/torchvision compatibility |
| Audio/ASR pipelines | `python -m pip install "transformers[audio]"` and verify audio backend packages |
| Training examples | `python -m pip install "transformers[torch]" datasets evaluate accelerate` plus task-specific requirements |
| CLI serving | `python -m pip install "transformers[serving]"` |
| Quality/contributor checks | Use the repository's documented dev or quality install; do not install broad dev extras for ordinary package use |

For local repository contribution work, follow the repository instructions and prefer focused extras such as `[quality]` when full `[dev]` is too broad or unavailable.

## Backend Selection

- CPU-only inspection is enough for signatures, configs, tokenizer checks, and most dry runs.
- CUDA is needed only when the user asks to validate GPU execution, quantized CUDA backends, tensor parallelism, distributed training, or memory behavior.
- Match PyTorch/CUDA wheels to the driver and GPU generation; do not assume a visible GPU means the installed wheel can use it.
- Apple Silicon/MPS, ROCm, Intel, and vendor accelerators need backend-specific package guidance and may not support every quantization or attention path.

## Dependency Failure Pattern

Transformers intentionally raises targeted optional dependency errors. When an import fails:

1. Read the missing package list from the error message.
2. Confirm the workflow actually needs that capability.
3. Install the smallest extra or package set for that capability.
4. Re-run a tiny import/config check before downloading models or running workloads.

Examples:

- `AutoModel` or `Trainer` complains about PyTorch: install/verify PyTorch first.
- `AutoImageProcessor` complains about Pillow/torchvision: install compatible vision dependencies.
- `transformers serve` complains about serving dependencies: install the serving extra and verify `fastapi`, `uvicorn`, `pydantic`, and `openai` where needed.
- Quantization config imports complain about backend packages: install only the selected quantization backend, not every quantization library.

## Offline And Reproducible Runs

- Use local model directories and `local_files_only=True` for no-network validation.
- Pin Hub models with `revision` when reproducibility matters.
- Pre-download assets with `transformers download` or Hugging Face Hub tooling when network access is allowed.
- Do not rely on pipeline default models for production or tests; name the model explicitly.

## Repository Contribution Installs

Contributor workflows can require more tools than package users:

- `make style` runs formatters/linters.
- `make typing` runs the configured type checker and model-structure rules.
- `make fix-repo` auto-fixes copies, modular conversions, docs, and style.
- `make check-repo` runs typing and consistency checks.
- Slow tests may require `RUN_SLOW=1` and heavyweight models; do not run them by default.

Always coordinate issue ownership and duplicate PR checks before preparing PR-ready repository changes.
