---
name: m2cgen
description: "Use m2cgen to transpile fitted Python machine-learning models into
  standalone C, C#, Dart, Elixir, F#, Go, Haskell, Java, JavaScript, PHP,
  PowerShell, Python, R, Ruby, Rust, or Visual Basic code through its API or
  CLI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# m2cgen

Use this repo skill when a task involves converting an already fitted Python estimator or booster into native source code, selecting a supported target language, or diagnosing m2cgen API/CLI export failures.

## Install and verify

Install the public package in the environment that contains the fitted model:

```bash
python -m pip install m2cgen
python -c "import m2cgen; print(m2cgen.__version__)"
```

The package has a base NumPy dependency. The library that created a serialized model (for example scikit-learn, statsmodels, lightning, XGBoost, or LightGBM) must also be installed when the model is fitted or unpickled.

## Route by task

- **Export an in-memory fitted model**: read [`sub-skills/model-export/SKILL.md`](sub-skills/model-export/SKILL.md), then [`sub-skills/model-export/references/api-reference.md`](sub-skills/model-export/references/api-reference.md).
- **Export a pickle/joblib file or pipe stdin**: read [`sub-skills/model-export/references/cli-reference.md`](sub-skills/model-export/references/cli-reference.md).
- **Choose a model family, understand output semantics, or check target support**: read [`sub-skills/model-export/references/model-overview.md`](sub-skills/model-export/references/model-overview.md).
- **Follow an end-to-end recipe or use the bundled smoke check**: read [`sub-skills/model-export/references/workflows.md`](sub-skills/model-export/references/workflows.md).
- **Investigate unsupported models, dependencies, recursion, serialization, or numerical differences**: read [`references/troubleshooting.md`](references/troubleshooting.md) and the sub-skill troubleshooting reference.

## Minimal decision process

1. Confirm that the object is fitted and identify its runtime estimator class.
2. Select one of the 16 supported target-language exporters; do not infer support from a similar language name.
3. Use the Python API for an in-memory object or the CLI for pickle/joblib and shell pipelines.
4. Pass only target-appropriate naming options, then validate the generated source before integrating it into a build.
5. Compare generated predictions with the original model using the correct output semantics and a floating-point tolerance.

## Boundaries

This skill covers public m2cgen usage and export troubleshooting. It does not train models, execute generated programs in foreign runtimes, or reproduce the repository's maintainer-only bulk example generation.

Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is stale for a changed checkout. The generated skill is self-contained; the original repository's tests, examples, and tools are evidence rather than runtime dependencies.
