---
name: colorization
description: "Use richzhang/colorization PyTorch colorizers for automatic image
  colorization, Python API calls, preprocessing/postprocessing, and runtime
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# colorization

Use this repo skill when a task involves the `richzhang/colorization` PyTorch release for automatic image colorization, ECCV16/SIGGRAPH17 pretrained colorizers, image-to-PNG demo workflows, or the `colorizers` Python API.

## Read first

- Check [references/installation.md](references/installation.md) when setting up the repo, correcting dependency names, or making `colorizers` importable.
- Check [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting dependency, import, model-cache, device, and unsupported-scope issues.
- Check [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a newer checkout.
- Use [scripts/check_env.py](scripts/check_env.py) for a no-download environment/import/backend diagnostic.

## Route by task

| User intent | Route |
| --- | --- |
| Colorize one image and save output PNG files. | [sub-skills/automatic-colorization/](sub-skills/automatic-colorization/) |
| Recreate the release demo without opening a GUI window. | [sub-skills/automatic-colorization/](sub-skills/automatic-colorization/) |
| Choose ECCV16 vs SIGGRAPH17, CPU vs CUDA, or debug pretrained model downloads. | [sub-skills/automatic-colorization/](sub-skills/automatic-colorization/) |
| Import `colorizers` in Python, inspect constructors, or run no-download API checks. | [sub-skills/python-api/](sub-skills/python-api/) |
| Use `preprocess_img`, `postprocess_tens`, Lab tensors, or SIGGRAPH hint/mask inputs. | [sub-skills/python-api/](sub-skills/python-api/) |
| Train models, reproduce the historical Caffe branch, or run representation-learning experiments. | Out of scope for this PyTorch test-time checkout. |

## Setup snapshot

This checkout is an unpackaged Python repo: it exposes a top-level `colorizers/` package but does not include `pyproject.toml`, `setup.py`, or console entry points. In normal use, clone the repo, install the runtime dependencies, and either run Python from the repo root or put the clone root on `PYTHONPATH`.

Correct dependency names:

```bash
python -m pip install torch numpy matplotlib pillow scikit-image ipython
```

`argparse` is part of the Python standard library. Use `pillow` for the `PIL` import and `scikit-image` for the `skimage` import.

Minimal import check:

```bash
python - <<'PY'
import colorizers
print(colorizers.eccv16(pretrained=False).__class__.__name__)
print(colorizers.siggraph17(pretrained=False).__class__.__name__)
PY
```

Use `pretrained=False` for checks that must not download model weights. Quality colorization with the wrapper defaults uses pretrained weights and may download public files through PyTorch's model cache.

## Shared diagnostic

From this skill directory, run:

```bash
python scripts/check_env.py --repo-root path/to/colorization --check-forward
```

The script constructs both models with `pretrained=False`, checks imports and dependency versions, reports whether CUDA is visible to PyTorch, and optionally runs a tiny forward pass. It does not make network calls.

## Operating boundaries

- Supported: test-time automatic image colorization, CPU execution, optional CUDA execution when the user's PyTorch install supports it, programmatic model/API use, preprocessing/postprocessing, and output-file validation.
- Supported with caution: pretrained weight loading, because first use depends on network access or a populated PyTorch cache.
- Not supported: training workflows, Caffe branch behavior, representation-learning evaluations, service deployment, batch dataset pipelines, or bit-for-bit output guarantees across dependency versions.

## Verification stance

Prefer assertion-backed checks over visual-only judgment:

1. Verify imports and no-download model construction.
2. Verify preprocessing returns `[1, 1, H, W]` original L and `[1, 1, 256, 256]` resized L tensors for normal inference.
3. Verify model output is `[1, 2, H, W]` Lab `ab` and `postprocess_tens` returns an RGB array matching the original image size.
4. For quality pretrained runs, verify output PNG files are readable and match the input dimensions, then perform visual plausibility review.

Do not ask future agents to run original repo scripts as runtime instructions. Use the bundled helpers in this skill; they adapt the repo workflow without depending on construction-time paths.
