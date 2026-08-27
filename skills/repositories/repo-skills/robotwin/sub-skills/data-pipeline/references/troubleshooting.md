# Troubleshooting

## `envs` import fails early

**Symptom**
- `import envs` or a collection script crashes before any task runs.

**Likely cause**
- The asset bundle is missing.
- In particular, the object metadata file used by the simulator-side loaders is not present yet.

**Fix**
- Download the assets first, then retry the data workflow.
- If you are only validating data files, use the bundled inspection scripts instead of a simulator-backed import.
- For the full simulator/bootstrap path, switch to `simulation-core`.

## XPolicyLab scripts are unavailable

**Symptom**
- A policy-side workflow cannot find the XPolicyLab scripts or policy adapters.

**Likely cause**
- The XPolicyLab submodule has not been initialized in the working tree.

**Fix**
- Initialize the submodule before any workflow that depends on policy-side code.
- This sub-skill does not vendor the policy stack; it only validates and normalizes RoboTwin data.
- For policy consumption, continue in `policy-eval`.

## Downloaded archives fail extraction

**Symptom**
- The download helper refuses an archive or reports a malformed payload.

**Likely cause**
- Unsafe archive paths, a bad archive name, or a corrupted ZIP.

**Fix**
- Use the published dataset naming pattern.
- Avoid custom archive names that introduce path traversal or ambiguous task names.
- Re-run the download helper with a clean cache if the archive was partially downloaded.

## The layout validator reports missing `data/` or wrong episode names

**Symptom**
- `validate_download_layout.py` complains about missing directories, gaps, or non-normalized names.

**Likely cause**
- The tree is still raw or only partly extracted.
- The episode folders were not normalized to seven digits.

**Fix**
- For public archives, re-run the download-and-normalize workflow.
- For old raw episodes, run the legacy conversion workflow before validation.

## The inspector says `legacy-raw` or `unknown`

**Symptom**
- `inspect_xpolicylab_hdf5.py` reports a non-`xpolicylab` layout.

**Likely cause**
- The file is an old raw episode bundle, a cache artifact, or a partial write.

**Fix**
- Use `scripts/process_data_xpolicylab.py` on raw episode bundles.
- Use `envs/utils/pkl2hdf5.py` only for the per-frame cache path inside collection.
- Re-collect the episode if the file is incomplete or truncated.

## Legacy recovery after an interrupted collection

**Symptom**
- An old `.pkl`-based collection run stopped early and left numbering gaps.

**Likely cause**
- The collector exited before the final seed list and episode rename step completed.

**Fix**
- Use `data/process_stuck.py` only on the older `.pkl` bundle layout.
- It renumbers the final cached episode and rewrites `seed.txt`.
- Do not apply it to normalized XPolicyLab episodes.

## HDF5 horizon mismatches

**Symptom**
- `state`, `action`, or `vision` lengths do not match.

**Likely cause**
- The file was partially written or mixed from incompatible conversions.

**Fix**
- Rebuild the affected episode and run the inspector again.
- If you need a quick diagnosis, inspect the sample file directly before reprocessing the whole tree.
