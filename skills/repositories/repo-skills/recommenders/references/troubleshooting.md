# Cross-Cutting Troubleshooting

## Purpose

Read this when the issue is not clearly owned by one sub-skill, or when a user asks why a Recommenders workflow cannot run in the current environment.

## Install or import failures

Symptoms:
- `ModuleNotFoundError: recommenders`
- `pip check` fails after installation
- A submodule imports in the repo checkout but not in an installed environment

Likely causes:
- Wrong package installation target.
- Missing optional extra.
- Conflicting dependency versions.
- Framework imports masked by the source checkout.

Recovery:
1. Re-run the generated environment report helper.
2. Check that the package version is `recommenders 1.2.1` or the current release in `repo-provenance.md`.
3. Install only the extra needed by the selected workflow.
4. Use the bundled smoke helpers to separate base package problems from backend problems.

## Optional dependency confusion

Symptoms:
- TensorFlow/PyTorch/Spark/NNI/Surprise/LightFM/Vowpal Wabbit/xLearn imports fail.
- The host has a GPU or Spark service but the workflow still fails.

Likely causes:
- The matching extra was never installed.
- The system runtime is incomplete.
- A CPU import was mistaken for GPU/Spark verification.

Recovery:
- Treat each optional family as a separate backend gate.
- Reconfirm framework wheels, Java/JDK, binaries, and credentials before retrying.
- If the user only needs the CPU path, keep the optional path documented but unverified.

## Data download and cache problems

Symptoms:
- Network timeouts or HTTP errors while fetching public datasets.
- Corrupt ZIP or missing extracted files.

Recovery:
- Use a user-provided local fixture first.
- Confirm dataset size/version and cache path.
- Re-download only when allowed.
- Avoid claiming a dataset-backed workflow is verified just because the package imports.

## Backend mismatches

Symptoms:
- CUDA/TensorFlow/PyTorch/Spark classes import, but runtime execution fails.
- GPU is visible but device allocation fails.
- Spark code imports but Java gateway or session startup fails.

Recovery:
- Verify the actual backend runtime, not just importability.
- Check driver/runtime compatibility and package extra alignment.
- Use the sub-skill-specific backend references before planning a new smoke.

## Cloud and remote-service failures

Symptoms:
- AzureML, Databricks, or AKS workflows fail with missing workspace, cluster, profile, DBFS, or service errors.

Recovery:
- Treat these as credentialed or side-effecting workflows.
- Ask for explicit target resource ids and permission before retrying.
- Do not let a local CPU smoke stand in for a remote service run.

## Safe fallback rule

If the user only needs advice, return the smallest verified local path that matches the data and backend, then list the optional families as unverified rather than trying to widen scope automatically.
