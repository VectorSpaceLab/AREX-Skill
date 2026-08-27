# Cross-cutting troubleshooting

Use the nearest sub-skill reference first. This page handles failures that span
multiple routes.

## Diagnose in layers

1. **Path and version layer:** run the environment checker and confirm the
   user-supplied checkout/config/data paths. Do not repair a missing dependency
   by silently changing the documented version family.
2. **CUDA/MMCV layer:** confirm `torch.cuda.is_available()`, device visibility,
   and MMCV's deformable-attention import. A CPU-only result is insufficient for
   VoxFormer execution.
3. **Native-operator layer:** import `mmdet3d.ops`; for a deform3D request,
   import the separately built `deform3dattn_custom_cn` extension and verify its
   forward/backward symbols. Build failures are usually CUDA_HOME, host
   compiler, ABI, header, or linker mismatches.
4. **Project-registration layer:** import the plugin after the custom wrapper's
   extension path has been intentionally resolved. The stock wrapper's
   placeholder guard is a known `deform3D` limitation, not a generic Python
   package failure.
5. **Data/config layer:** run the read-only dataset and config checkers before
   considering a train/test command.
6. **Launch layer:** use the non-launching train/test preflight; only then run a
   user-approved command with explicit GPU, port, checkpoint, and output paths.

## Common symptoms

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError` for `mmcv`, `mmdet`, or `mmdet3d` | wrong environment or incomplete legacy install | compare the pinned matrix; reinstall in a new environment rather than mutating a working user environment |
| `CUDA_HOME`/`nvcc` not found | native extension build has no CUDA compiler | provide a compatible toolkit and host compiler; do not claim CPU fallback |
| undefined symbol or `GLIBCXX` error when importing an extension | extension was built against a different torch/CUDA/compiler ABI | remove only the stale build artifact after approval, rebuild against the active pinned stack, and re-run the import smoke |
| standard plugin imports but `deform3D` fails at a placeholder | custom extension path was never replaced | build the extension, supply a valid runtime search path, and keep standard S/T as the alternative |
| missing `.pseudo`, query, or `_1_1.npy`/`_1_2.npy` files | preprocessing or stage dependency incomplete | run the data checker and repair the stage-specific artifact set; do not substitute a checkpoint for query files |
| config registry/key error | plugin not imported or config inheritance is broken | validate the config, import the project plugin, and compare the selected preset with the model-configuration catalog |
| CUDA out-of-memory | temporal/S/T geometry, batch size, or stale distributed processes | stop the run, inspect GPU ownership, reduce only documented config/resource knobs, and preserve the checkpoint/work-dir plan |
| distributed hang or address-in-use | port collision, inconsistent rank environment, or mixed package stacks | choose a free port, use the same environment and visible GPUs on every rank, and retry one controlled launch |
| test command rejects its arguments | train-only/test-only flags were mixed or no result operation was selected | rerun `preflight_train_test.py --help`; for test choose `--eval`, `--format-only`, `--show`, or `--show-dir` |
| metrics are absent or implausible | no real predictions/labels, wrong stage, or frame mismatch | verify data and checkpoint/config pairing; the bundled checks do not compute SemanticKITTI metrics |

## Optional preprocessing

The repository documents MobileStereoNet as a separate legacy image-to-depth
path. Keep it isolated from the core environment and mark it unverified unless
a user explicitly supplies the required model, data, and compatible runtime.
A missing optional depth environment does not justify weakening the core CUDA
requirements.

## Safety boundary

No troubleshooting step on this page downloads data or weights, launches
training, regenerates labels, or overwrites a work directory. Treat every
filesystem path and command produced by a checker as a proposal for review.
