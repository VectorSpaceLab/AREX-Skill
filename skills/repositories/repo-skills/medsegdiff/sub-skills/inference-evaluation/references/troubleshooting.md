# Troubleshooting and bounded recovery

Use this table to classify failures before changing model or data settings.
Do not solve a sampling failure by silently switching to a different checkpoint
or by reading the original source checkout from a recovery script.

| Symptom | Likely cause | Action |
|---|---|---|
| `Missing key(s)`, `Unexpected key(s)`, or tensor-size mismatch at `load_state_dict` | Architecture flags, `version`, or effective `in_ch` differ from training; checkpoint may be wrapped under `state_dict`. | Inspect the checkpoint key set and tensor shapes without mutating it. Confirm exact `version`, image size, channels, attention, and branch. Unwrap only in an explicit adapter. The source loader does not unwrap wrappers and uses strict loading. |
| Keys begin with `module.` | DataParallel checkpoint prefix. | Strip exactly one leading `module.` from every key in a preflight adapter, then verify no duplicate/colliding keys. The source's substring test and in-loop reassignment are brittle for mixed or non-prefix keys; do not assume it safely handles every state dict. |
| Checkpoint loads but output is nonsensical | `version` selects a different UNet/post-processing path, or a legacy checkpoint is sampled with `new` (or vice versa). | Treat `version` as part of checkpoint identity. In `new`, ensemble the final sample channel; otherwise ensemble `cal_out`. Record the selected path in metrics. |
| `TypeError` about unexpected `step` while `--use_ddim True` | Caller passes `step=args.diffusion_steps` to a DDIM-known function that does not accept it. | Mark DDIM unavailable in the unpatched source. Patch the caller/function signature consistently and test a tiny synthetic call in a compatible runtime before real data. Do not report the parser check as DDIM success. |
| `RuntimeError`/dummy CUDA Event failure on CPU, or failure at `cuda.synchronize()` | Source unconditionally creates CUDA timing events and synchronizes during sampling. | Require a CUDA device for source sampling or patch timing behind `torch.cuda.is_available()`. The bundled inspector and evaluators are the intended CPU-safe checks. |
| DPM-Solver flag appears ignored | `--use_ddim True` takes precedence, or `dpm_solver` was not passed into diffusion construction. | Use non-DDIM sampling for the DPM-Solver branch and inspect the effective plan. The branch uses order-2 multistep `dpmsolver++`; it is not a generic replacement for DDIM. |
| DPM-Solver is unstable or too slow | Steps, schedule, checkpoint, or GPU precision are incompatible with the trained setup. | Start with the trained diffusion schedule; only then compare bounded step counts. Keep `diffusion_steps` explicit and record solver mode. Do not claim quality from a synthetic parser check. |
| `FileNotFoundError` for ISIC CSV or masks | Loader expects `ISBI2016_ISIC_Part3B_<mode>_GroundTruth.csv` and paths from its second/third CSV columns. README examples mention Part1 names/tree, which may not match the loader revision. | Inspect the actual CSV header and path values; provide the loader's expected filenames or use a deliberate loader adapter. This sub-skill does not prepare or download datasets. |
| BRATS loader asserts missing keys or samples unexpected slices | `BRATSDataset3D` expects its sequence naming convention and, in the source sampler, is called without `test_flag=True`, so a segmentation file is expected. | Check exact `t1`, `t1ce`, `t2`, `flair`, and `seg` token extraction and virtual `_sliceN.nii` names. Decide explicitly whether to patch the sampler to use test mode. |
| Custom branch raises `UnboundLocalError: slice_ID` | The source assigns `slice_ID` only for ISIC and BRATS. | Add a deterministic custom ID derived from the image path in an adapter and test collision handling. Do not treat the fallback branch as supported merely because its loader exists. |
| Several samples overwrite one output or IDs do not match | `batch_size>1` combined with `path[0]`, shuffle, or brittle underscore/slice parsing. | Keep `batch_size=1` for the unpatched source. Use stable, unique input names; inspect output names before evaluation. For custom/BRATS, patch ID derivation and write an explicit mapping manifest. |
| ISIC evaluator reports no pairs | Aggregate files do not contain `ens`, use unexpected prefixes, or ground truth is not named `ISIC_<first-token>_Segmentation.png`. | List sorted prediction names and expected ground-truth paths. Use the bundled evaluator's actionable error. Do not rename files blindly without recording the mapping. |
| ISIC evaluator crashes on missing ground truth or zero files | Original divides by `num` without a guard and opens the derived file unconditionally. | The bundled evaluator fails with a nonzero status and reports missing/zero pairs. Use `--allow-missing` only for an explicitly exploratory partial audit; zero usable pairs remains an error. |
| All-zero prediction gives NaN or implausible score | Original uses `pred / pred.max()` with no zero guard; JPEG may contain a blank image. | The bundled evaluator treats zero max as all-zero and reports a warning/count. Investigate checkpoint, output write, and version path before interpreting metrics. |
| Shape mismatch in evaluation | Source resizes ground truth to 256x256 but leaves prediction at its current size. | Set the evaluator's explicit `--image-size` for a controlled fixture, or regenerate/resize predictions in a documented preprocessing step. Do not silently compare different grids. |
| Per-class output contains NaN or PrettyTable import fails | Source divides by zero for absent classes and imports optional `prettytable`. | Use the bundled evaluator, which emits `NA` for undefined class denominators and has no PrettyTable dependency. Treat absent-class metrics as coverage information, not as zero. |
| A per-class run silently includes unrelated images | Source walks every file and does not require an ensemble suffix. | Put only the intended prediction images in the input tree, use sorted pairing, and apply `--limit` for a bounded audit. Verify derived same-stem `.tif` names before accepting results. |
| Evaluator has no original-repo import but sampling script cannot import | This is expected separation: bundled scripts are deterministic image/CLI tools; real sampling needs the project's installed dependencies and model code. | Diagnose the prepared sampling environment separately. Do not add source imports to the bundled evaluators or claim they prove diffusion execution. |

## Minimal diagnostic order

1. Run `inspect_sample_cli.py --help`, then inspect the exact branch, version,
   effective `in_ch`, solver, and output contract.
2. Validate checkpoint key prefixes, wrapper shape, and architecture metadata
   without starting sampling.
3. Validate data naming and one sample's expected path/shape in the prepared
   application runtime.
4. Run a tiny image-only evaluator fixture and confirm pair counts/metrics.
5. Only then attempt real CUDA sampling with `batch_size=1` and a bounded
   ensemble, preserving logs and output mapping outside the runtime skill tree.

A parser success, a checkpoint deserialization success, or a metric fixture
success is not evidence that the full diffusion run is valid.
