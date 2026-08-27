---
name: repo-development
description: "Maintain LightFM editable builds, compiled extension variants,
  Cython regeneration, tests, lint, docs, and CI expectations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LightFM Repo Development

Use this sub-skill when the user is maintaining the LightFM repository itself: editable installs, C extension builds, OpenMP/no-OpenMP behavior, Cython template changes, focused tests, linting, documentation builds, or CI compatibility.

## Route map

- For fitting models, choosing losses, calling `LightFM.fit`, `fit_partial`, `predict`, or inspecting learned representations, route to [model-training](../model-training/SKILL.md).
- For `Dataset`, interaction matrices, user/item feature construction, identity features, or data loaders, route to [data-features](../data-features/SKILL.md).
- For `random_train_test_split`, `precision_at_k`, `auc_score`, `predict_rank`, or train/test intersection handling, route to [evaluation-splitting](../evaluation-splitting/SKILL.md).
- Stay here for repository maintenance, package installation, compiled extension diagnosis, Cython regeneration, tests, lint, docs, and CI expectations.

## Safe maintainer workflow

1. Work from an isolated Python environment in a LightFM checkout. Treat the package as CPU-only; there is no GPU implementation to enable or verify.
2. Install the package editable before testing. Add test, lint, or docs requirements only for the scope being changed.
3. If changing the Cython template or generated extension sources, regenerate the OpenMP and no-OpenMP C files, reinstall editable, and run focused extension/API tests before broader tests.
4. Use focused pytest targets first, then the full suite when the change can affect package behavior broadly. Dataset and MovieLens-oriented tests may need cached/downloaded data and can be slower than pure in-memory tests.
5. Run the bundled diagnostic after build or install changes from this sub-skill directory, using the Python environment where the checkout is installed:

   ```bash
   python scripts/check_lightfm_install.py --tiny-run
   ```

6. Keep publication actions explicit. Local docs builds are fine when scoped; commands that switch branches, commit, or push must not run without release-maintainer approval.

## Reference links

- [Maintenance commands and expectations](references/maintenance.md)
- [Build and install troubleshooting](references/troubleshooting.md)
- [Install diagnostic script](scripts/check_lightfm_install.py)

## Expected observations

- `import lightfm` reports version `1.17` for this distilled source version.
- `lightfm._lightfm_fast` imports a compiled backend: OpenMP-enabled on Linux when the compiler/runtime supports it, or no-OpenMP on macOS/Windows and fallback builds.
- OpenMP changes affect CPU threading only; they do not create GPU support.
- CI expectations cover Python 3.7 and 3.11 across the configured OS matrix, with macOS/Windows limited to Python 3.11 in the observed workflow.
