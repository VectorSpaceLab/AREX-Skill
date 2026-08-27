---
name: keras-tuner
description: "Routes KerasTuner workflows for defining hyperparameter spaces,
  running search algorithms, tuning image and scikit-learn models, and
  coordinating distributed chief/worker search state."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# KerasTuner

Use this skill when the task mentions `keras_tuner`, `KerasTuner`, `HyperParameters`, `HyperModel`, `Oracle`, `Tuner`, `RandomSearch`, `GridSearch`, `Hyperband`, `BayesianOptimization`, `SklearnTuner`, `HyperResNet`, `HyperXception`, `HyperEfficientNet`, `HyperImageAugment`, or distributed `KERASTUNER_*` search state.

## What this skill covers

- Defining search spaces with `HyperParameters` and `HyperModel`.
- Running the built-in search algorithms and reading back best trials.
- Tuning scikit-learn estimators with `SklearnTuner`.
- Using the built-in image hypermodels and augmentation search helpers.
- Debugging distributed chief/worker oracle coordination.

## Install and quick check

For a normal CPU-backed KerasTuner install:

```bash
python -m pip install "keras-tuner[tensorflow-cpu]" tensorboard
```

For Bayesian optimization or scikit-learn tuning, add the optional backend package set:

```bash
python -m pip install "keras-tuner[tensorflow-cpu,bayesian]" tensorboard
```

If you are using a GPU TensorFlow environment, swap `tensorflow-cpu` for `tensorflow`.

For editable development from a source checkout, run this from the checkout
root that contains `setup.py`; the generated skill directory is documentation
and is not itself an installable checkout:

```bash
python -m pip install -e ".[tensorflow-cpu,bayesian]" tensorboard
```

Minimal check:

```bash
python -c "import keras_tuner; from keras_tuner.backend import config; print(keras_tuner.__version__, config.backend())"
```

Run `scripts/check_env.py` when you want a slightly richer import and backend sanity check.

## Route map

- Read `sub-skills/tuning/SKILL.md` for generic hyperparameter search, custom `HyperModel` classes, `Oracle`/`Tuner` subclassing, trial inspection, and reload/resume workflows.
- Read `sub-skills/image-hypermodels/SKILL.md` for `HyperResNet`, `HyperXception`, `HyperEfficientNet`, and `HyperImageAugment`.
- Read `sub-skills/sklearn-tuning/SKILL.md` for `SklearnTuner`, estimator factories, cross-validation, sample weights, and pickle-backed model saving.
- Read `sub-skills/distributed-tuning/SKILL.md` for `KERASTUNER_ORACLE_IP`, `KERASTUNER_ORACLE_PORT`, `KERASTUNER_TUNER_ID`, and local chief/worker coordination.

## What to read next

- `references/api-reference.md` for verified signatures and class responsibilities.
- `references/workflows.md` for end-to-end tuning patterns.
- `references/troubleshooting.md` for install/import, optional dependency, and search failures.
- `references/repo-provenance.md` before deciding whether this skill matches the current checkout.

## Operational notes

- This package is Python-first; there is no separate CLI to route here.
- Use `keras_tuner.backend.config.backend()` to check the active backend, not `keras_tuner.backend.backend`.
- Bayesian optimization and scikit-learn tuning need the optional `bayesian` dependency set.
- In this 1.4.8 TensorFlow path, Keras model trials also import TensorBoard's HParams API; install `tensorboard` even when you do not pass a TensorBoard callback.
- The built-in image models may be slow to build; `HyperEfficientNet` can also trigger a first-run Keras Applications weight download.
- Distributed tuning needs the chief/worker environment variables to be set together.
Unless a command says otherwise, run the shell snippets from this skill's root directory (the directory containing this `SKILL.md`); from another cwd, use the corresponding absolute path.

## Fast path

If you only need to confirm the install, backend, and public exports, run:

```bash
python scripts/check_env.py
```

If you need a workflow-specific smoke check, run the helper from the skill
root, using its full bundle-relative path, such as
`python sub-skills/tuning/scripts/smoke_search.py`.
