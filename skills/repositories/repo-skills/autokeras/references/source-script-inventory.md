# Source Script and Example Inventory

## Purpose

This records how repository-owned examples and scripts were handled. Runtime instructions should use bundled skill files, not the original repository checkout.

| Source repo artifact | Workflow | Decision | Bundled replacement | Reason |
| --- | --- | --- | --- | --- |
| `docs/py/image_classification.py`, `docs/py/image_regression.py`, `examples/mnist.py`, `examples/cifar10.py` | Image task APIs | Adapt | `sub-skills/task-apis/scripts/run_tiny_image_task.py` | Original examples use public datasets or larger searches; bundled helper uses synthetic arrays. |
| `docs/py/text_classification.py`, `docs/py/text_regression.py`, `examples/imdb.py`, `examples/reuters.py`, `examples/new_pop.py` | Text task APIs | Adapt | `sub-skills/task-apis/scripts/run_tiny_text_task.py` | Avoid dataset downloads and Colab-era assumptions. |
| `docs/py/structured_data_classification.py`, `docs/py/structured_data_regression.py`, benchmark Titanic fixture tests | Structured-data APIs | Adapt | `sub-skills/task-apis/scripts/run_tiny_structured_task.py` | Preserve column metadata and tabular workflow with tiny in-memory data. |
| `docs/py/customized.py`, `examples/automodel_with_cnn.py` | Custom AutoModel graph | Adapt | `sub-skills/automodel-customization/scripts/build_tiny_custom_image_automodel.py` | Preserve topology pattern while avoiding downloads/plotting. |
| `docs/py/multi.py` | Multimodal/multitask AutoModel | Adapt | `sub-skills/automodel-customization/scripts/build_tiny_multimodal_automodel.py` | Preserve multi-input/multi-output ordering with synthetic data. |
| `docs/py/export.py` | Export/reload | Adapt | `sub-skills/search-and-export/scripts/export_tiny_model.py` | Preserve `export_model()` and `ak.CUSTOM_OBJECTS` path without external data. |
| `benchmark/run.py`, `benchmark/performance.py` | Benchmark timing | Exclude | None | Repeated experiments and possible downloads are outside selected operating scope. |
| `docs/run_py_files.sh` | Docs example runner | Reference-only/exclude | None | Runs many examples with network/long training assumptions. |
| `shell/*.sh`, `docker/*`, `.github/workflows/*` | Maintainer automation | Reference-only/exclude | Root setup reference only distills CI backend/install evidence | Docker, formatting, release, and credential side effects are not AutoKeras user operation. |
