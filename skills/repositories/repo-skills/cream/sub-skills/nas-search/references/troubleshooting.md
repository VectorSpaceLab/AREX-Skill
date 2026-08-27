# NAS Search Troubleshooting

## Purpose

Read this when a NAS-family command or import fails.

## Legacy torch import failures

**Symptom:** `ModuleNotFoundError: torch._six` or a stack trace inside `model/utils.py`.

**Likely cause:** The code was written for older torch releases.

**Recovery:**

1. Use `../../../scripts/check_legacy_imports.py --repo-root <cream-checkout>` to confirm the compatibility shim path.
2. If you only need command construction, prefer `../scripts/build_nas_command.py` and the workflow reference.
3. If you need the original legacy runtime, switch to a historical torch environment rather than forcing a modern-torch execution path.

## Apex or NAS-Bench-201 errors

**Symptom:** `ModuleNotFoundError: apex` or missing NAS-Bench-201 API files in `benchmark201/search.py`.

**Likely cause:** The optional benchmark201 path depends on extra historical packages.

**Recovery:**

- Treat benchmark201 as optional unless the user explicitly asks for it.
- Install Apex only in a compatible CUDA environment if the benchmark201 path is truly required.
- Otherwise route to the standard CDARTS search/retrain/test scripts.

## Dataset layout errors

**Symptom:** `FileNotFoundError` for `imagenet/train`, `imagenet/val`, `subImageNet`, or COCO paths.

**Likely cause:** The expected data tree is missing or named differently.

**Recovery:**

1. Run `../../../scripts/check_dataset_layout.py --kind imagenet1k --root <imagenet-root>`.
2. For sampled data, run `../../../scripts/check_dataset_layout.py --kind subimagenet --root <repo-data-root>`.
3. For COCO-based branches, run `../../../scripts/check_dataset_layout.py --kind coco2017 --root <coco-root>`.

## Argument parser / launcher confusion

**Symptom:** The script exits with `--name` or `mode` missing, or a distributed command fails immediately.

**Likely cause:** The user skipped the config or mode argument that the project expects at import time.

**Recovery:**

- Check the launcher shape in `references/workflows.md`.
- Use the bundled command builder to print the exact command string before running it.
- Verify the chosen config file and dataset root before increasing GPU count.

## Mutating sampled-data helpers

**Symptom:** A command copies images into `subImageNet` or rewrites a sampled dataset unexpectedly.

**Likely cause:** The original helper script is a mutating maintainer workflow.

**Recovery:**

- Do not use the original copy-heavy helper as a runtime dependency.
- Validate the layout with the bundled checker and keep the generated skill self-contained.
