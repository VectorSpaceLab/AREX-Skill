# PEFT Test Selection

Use focused tests during development, then broaden based on the changed surface. Always ensure at least one selected test actually runs.

## Baseline Commands

```bash
make test
make quality
make style
```

`make test` runs pytest over `tests/` with xdist. `make quality` checks ruff format/check and doc-builder style. `make style` applies ruff fixes/formatting and doc-builder style.

## Focused Selectors by Method

For a method-specific change, run a focused selector first:

```bash
pytest tests/ -k ia3 -v
pytest tests/ -k "lora and not adalora and not randlora" -v
pytest tests/test_custom_models.py -k ia3 -v
```

LoRA needs exclusions because names such as AdaLoRA and RandLoRA also contain `lora`. Consider excluding known overlapping method names when selecting by substring.

Common overlap exclusions:

- For `lora`: exclude `adalora`, `randlora`, `loha`, `lokr`, `lorafa`, `loraplus`, `monteclora`, `bdlora`, `velora`, `tinylora`, and `delora` unless those variants are intentionally affected.
- For `ia3`: `pytest tests/ -k ia3 -v` is usually specific enough.
- For method packages with their own test files, prefer both the dedicated file and a cross-cutting matrix file.

## Changed Path Heuristics

- `src/peft/tuners/<method>/`: run that method's dedicated tests if present, `tests/test_custom_models.py -k <method>`, and relevant save/load/config/mapping tests.
- `src/peft/utils/peft_types.py`, `src/peft/tuners/__init__.py`, or `src/peft/__init__.py`: run mapping/import tests and at least one method smoke test.
- `src/peft/utils/save_and_load.py`: run save/load-focused tests and regression tests when behavior can affect checkpoint compatibility.
- `src/peft/mapping*.py`: run mapping, auto, and representative tuner tests.
- `docs/`: run quality/style checks; run docs build only when the docs surface is substantial and the environment supports it.
- `examples/`: run or smoke-check the touched example when dependencies and hardware are available.
- `tests/training/`: run the relevant `accelerate launch` target only when the needed hardware and dependencies are available.
- GPU-only behavior: use `tests/test_common_gpu.py` or `tests/test_gpu_examples.py` with `single_gpu_tests`, `multi_gpu_tests`, and `bitsandbytes` markers as applicable.

## Save/Load and Regression

If the change affects adapter checkpoints, `PeftConfig`, state dict keys, merge/unmerge, adapter names, or Hub loading, include targeted save/load tests and consider:

```bash
pytest -s --regression tests/regression/
```

Use `--regression` only when regression tests are relevant and the environment has the needed fixtures.

## Native Test Script

The bundled helper suggests selectors and repeats PEFT's contribution warnings:

```bash
python sub-skills/repo-development/scripts/select_tests.py --method lora --changed-path src/peft/tuners/lora/model.py
python sub-skills/repo-development/scripts/select_tests.py --method ia3 --changed-path tests/test_custom_models.py
```

It is a planning aid, not a substitute for judgment. If it recommends a selector that deselects all tests, adjust the selector or add the missing test coverage.

## Reporting Results

Record exact commands and outcomes in the PR description. For skipped tests, state why they were skipped, such as missing GPU, optional backend, or unavailable external dependency. Do not claim unrun tests passed.
