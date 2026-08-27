# Training troubleshooting

Use this reference after the static validator and before retrying an
expensive run. Preserve the original error, config path, commit, environment,
device, and checkpoint intent in the run record.

## Dependency and package failures

### `ModuleNotFoundError` for `pytorch_lightning`

The source imports `pytorch_lightning` directly. Install or activate the
verified package set in the intended environment, including
`pytorch-lightning==2.3.0`, then retry a lightweight import or `--help` check.
The repository has no packaging metadata. Use the shared bundled wrapper with
`--repo-root` set to the user's GeoSeg checkout so the entrypoint runs with the
checkout available for imports; do not invoke the checkout file directly.

### `lightning` and `pytorch-lightning` conflict

`requirements.txt` lists both `lightning==2.0.0` and
`pytorch-lightning==2.3.0`, while the source uses only the latter namespace.
The verified inspection environment used `pytorch-lightning==2.3.0` and
omitted the unused `lightning` meta-package after its resolved pydantic stack
caused import trouble. Do not change source imports to `lightning.pytorch` as
an ad hoc fix. Inspect the active environment, remove the conflicting unused
package if necessary, and confirm `import pytorch_lightning` before training.

### `timm`, Albumentations, or other import failures

The config imports model, dataset, loss, and augmentation modules at top level.
Confirm the intended versions before retrying. Evidence for the inspection
set includes Python 3.8, torch 2.0.1+cu118, torchvision 0.15.2+cu118,
pytorch-lightning 2.3.0, timm 0.9.16, albumentations 1.3.1, ttach 0.0.3,
catalyst 21.05, and scikit-image 0.21.0. A package probe or the static
validator cannot prove all transitive imports; keep import failures separate
from data failures.

### PyramidMamba cannot import

`PyramidMamba` imports optional `mamba_ssm`/related accelerator extensions and
was not verified in this checkout. Do not silently substitute a different
model when the requested experiment requires PyramidMamba. Install and verify
the optional backend for the target Torch/CUDA build, or report the model as
blocked. The ordinary UNetFormer/DCSwin/FTUNetFormer configs do not prove
PyramidMamba readiness.

## Config and data failures

### Static validator reports missing fields

Add the exact assignment names from
[cli-reference.md](cli-reference.md). The validator is static: a value built
inside a helper function may be reported as unknown or absent even if a
runtime import would eventually provide it. Prefer explicit top-level config
assignments for trainer contract values. Do not silence a missing `monitor`,
`weights_path`, loader, optimizer, or scheduler; those are consumed directly.

### Config import fails with `FileNotFoundError` or `NotADirectoryError`

A Python config executes dataset constructors and often model weight loading
at import time. Check all roots and subdirectories, not just the config file:

- LoveDA needs both Urban and Rural image/mask trees in Train and Val because
  `loveda_val_dataset` is instantiated at module scope;
- Potsdam and Vaihingen need paired `images_1024`/`masks_1024` directories;
- UAVid needs paired `images`/`masks` directories under the selected processed
  roots;
- factories with `pretrained=True` may open `pretrain_weights/*.pth` during
  import.

Use data-preparation rather than changing a dataset class in this sub-skill.

### Image/mask count assertion or empty dataset

The dataset modules enumerate both directories and assert equal counts. Check
that extensions and stems match the configured suffixes (`.tif` images and
`.png` masks for ISPRS; `.png` pairs for UAVid/LoveDA), that hidden files are
not included unexpectedly, and that the selected root is the processed split.
An empty root can pass some filesystem checks but produces no useful training;
stop and fix the data split.

### Mask/loss class-range errors or implausible metrics

Verify that masks are integer class IDs, `num_classes` equals the network
output channels and `len(classes)`, and the loss receives the same
`ignore_index` used during preparation. LoveDA/Potsdam/Vaihingen configs use
`ignore_index=len(CLASSES)`; UAVid uses `255`. The evaluator filters targets
outside `[0, num_classes)`, but a wrong in-range label is counted as a real
class and corrupts mIoU/F1/OA.

### `use_aux_loss` or tuple/tensor shape error

UNetFormer returns `(main, auxiliary)` in training mode and a main tensor in
evaluation mode. Its `UnetFormerLoss` recognizes a two-item output only while
training. The training metric branch also depends on `use_aux_loss`. Ensure
that the flag, selected network, loss, and any custom model's train/eval
return contract agree. Do not set the flag merely because the config has a
loss with an auxiliary component.

## CLI and Lightning failures

### `unrecognized arguments`

Only `-c`/`--config_path` is supported. Put epochs, batch sizes, monitor,
checkpoint paths, and device settings in the config. Re-run the static
validator after edits.

### Config path rejected by `tools.cfg`

The path must exist, end in `.py`, and have a stem without a dot. Use a
plain filename such as `unetformer.py`, not a generated dotted name. Run from
the project root so imports such as `geoseg`, `tools`, and `config` resolve.

### Monitor key missing or no best checkpoint

The callback monitors the configured string, but the script logs only
`val_mIoU`, `val_F1`, and `val_OA` at validation epoch end. Use one of those
exact names, set `monitor_mode='max'` for the checked-in metrics, and ensure
`check_val_every_n_epoch` allows validation to run. If `log_name` was renamed,
metric averaging may also change because dataset tokens are inspected in the
training script.

### Validation never runs or loader hangs

Check `check_val_every_n_epoch`, validation loader length, and worker count.
For an initial diagnostic, lower `num_workers` in the copied config (even to
zero) and check whether the failure is multiprocessing, filesystem, or model
execution. Do not treat a worker workaround as the final benchmark protocol.

## Checkpoint failures and recovery

### Resume checkpoint cannot be found

`resume_ckpt_path` is passed to `trainer.fit` and must be a readable Lightning
checkpoint. Verify the exact file, not only the containing directory, and
check that the previous run used `save_last=True` or that a top-k file exists.
Keep `pretrained_ckpt_path=None` for a pure resume.

### Resume checkpoint has incompatible keys or state

A resume restores model, optimizer, scheduler, epoch, and callback state. Use
the same architecture, class count, optimizer parameter structure, and
scheduler family. If the experiment intentionally changes those, start fresh
or set only `pretrained_ckpt_path` to use model initialization without the old
training state. Do not edit checkpoint keys blindly.

### Synthetic case: monitor mismatch on resume

**Input:** a valid config with `resume_ckpt_path` pointing to a real prior
checkpoint, but `monitor='val_mIoU'` while the prior run/checkpoint policy was
built around `val_F1` (or a typo such as `val_miou`).

**Expected handling:** stop before full training, validate the exact current
monitor against the script's logged keys, choose the intended ranking metric,
and decide whether callback state should be reused. If the monitor policy is
changed intentionally, use a new output/checkpoint directory or document that
best-checkpoint ranking is being restarted; do not report the resumed run as
comparable without this caveat.

### Synthetic case: valid config but GPU batch-memory failure

**Input:** a statically valid UNetFormer/Potsdam config with real paired data,
correct labels, visible CUDA, and a batch/crop combination that triggers
`CUDA out of memory` during the first training step.

**Expected handling:** preserve config semantics and first reduce
`train_batch_size`; then reduce validation batch size and/or crop/input size
if needed. Lower `num_workers` only for host-memory/worker pressure. Record
that the run is a reduced-batch smoke or changed-protocol run. Do not “fix” it
by changing `num_classes`, ignore labels, monitor, or checkpoint paths. The
`accumulate_n` field does not implement gradient accumulation in this trainer.

## Backend and device failures

### `gpus='auto'` selects CPU or no device is visible

`gpus` is passed to Lightning's `devices` argument and `accelerator='auto'`
lets Lightning select the accelerator. Check `torch.cuda.is_available()`, the
visible-device environment, and the installed Torch CUDA build. A verified
A100 CUDA smoke check exists for the inspection environment, but it is not a
claim that every host supports every model. If CPU is intentional, expect a
much longer run and label it; do not compare it as an equivalent performance
benchmark without recording the change.

### CUDA or custom-kernel incompatibility

Separate ordinary PyTorch CUDA errors from optional extensions. Confirm Torch,
torchvision, CUDA driver, and model/backend compatibility. For Mamba, treat
missing or incompatible `mamba_ssm`/`causal-conv1d` as a required-backend block.
Do not fall back silently when the requested model depends on that backend.

## Workflow and result interpretation

### Run is unexpectedly expensive

Stop rather than waiting if data size, crop size, worker count, epoch count,
or device selection was not approved. Full training is explicitly
skip-expensive. A static validator, parser `--help`, model import, or one-batch
smoke check is not a recovered benchmark result.

### mIoU/F1 differs from an external report

Check the dataset token in `log_name`, last-class exclusion, ignore-index
encoding, validation split, crop/augmentation settings, checkpoint selection,
seed/hardware, and whether the compared number is validation or test output.
The script reports per-class IoU and uses `np.nanmean`; preserve those raw
values before attributing a difference to the model.

### Run was interrupted

If a valid last checkpoint exists, set only `resume_ckpt_path` and rerun with
matching model/config state. If no usable checkpoint exists, report the run as
partial and decide whether a fresh run is scientifically acceptable. Preserve
logs and partial checkpoints; do not overwrite them until the recovery plan
is recorded.
