# Training and inference workflows

This reference distills the public training/evaluation intent and the source
control flow. Commands use placeholders so they do not depend on a particular
checkout or environment. They are historical routes and must pass the backend
gate in `compatibility.md` first.

## Preflight

1. Choose an isolated Python environment only when a separately supplied
   compatible checkout is intentionally in scope; this package has no setup
   metadata and this skill does not bundle the historical runner.
2. Run the safe probe without importing `second`:

   ```bash
   python <training-skill-root>/scripts/check_legacy_backend.py
   python <training-skill-root>/scripts/check_legacy_backend.py --require-detector
   ```

   The first command is a report. The second is a gate: it must report all
   required legacy spconv symbols before detector construction is attempted.
3. Confirm the config is a text protobuf, the train/eval dataset paths and info
   files exist, and model/checkpoint output is on writable storage. Data
   creation and info regeneration belong to `data-preparation`.
4. If `train.py --help` fails, preserve the first traceback. Do not work around
   an import failure by deleting imports or replacing NMS with an untested
   modern operator.

## Fire command surface

The historical Fire runner ends with `fire.Fire()`. Its source-authoritative
public top-level callable surface is:

| Command | Signature and purpose |
|---|---|
| `train` | `train(config_path, model_dir, result_path=None, create_folder=False, display_step=50, summary_step=5, pretrained_path=None, pretrained_include=None, pretrained_exclude=None, freeze_include=None, freeze_exclude=None, multi_gpu=False, measure_time=False, resume=False)`; build, optionally initialize, train, periodically evaluate, and save. |
| `evaluate` | `evaluate(config_path, model_dir=None, result_path=None, ckpt_path=None, measure_time=False, batch_size=None, **kwargs)`; restore a model, generate detections, pickle them, and call the dataset evaluator. |
| `helper_tune_target_assigner` | `helper_tune_target_assigner(config_path, target_rate=None, update_freq=200, update_delta=0.01, num_tune_epoch=5)`; inspect or adjust anchor assignment rates. Use only for config tuning, not as a detector smoke test. |
| `mcnms_parameters_search` | `mcnms_parameters_search(config_path, model_dir, preds_path)`; the current source body is a placeholder (`pass`), so do not promise a search workflow. |
| `build_network` | `build_network(model_cfg, measure_time=False)`; source API used by `train` and the viewer. It constructs voxel/box/target builders and the registered model; it is backend guarded. |
| `example_convert_to_torch` | `example_convert_to_torch(example, dtype=torch.float32, device=None)`; converts batch arrays to tensors, defaulting to `cuda:0` when no device is supplied. Do not call it on CPU accidentally. |

Fire accepts booleans in command-line form, but verify the rendered help for
the installed Fire version. Quote paths and values containing shell metacharacters.

## Single-GPU training

Historical argument shape (documentation only; this skill does not bundle
or execute the source runner):

```text
train --config_path=<kitti-or-nuscenes-config> \
  --model_dir=<new-model-dir> --resume=False \
  --multi_gpu=False --measure_time=False
```

Expected source-level behavior, if all dependencies work:

- the text protobuf is copied to `<model-dir>/pipeline.config`;
- the model and optimizer are restored from the latest entries in
  `checkpoints.json` only when `resume=True` is permitted by the directory
  checks (the implementation also tries latest checkpoints after construction);
- periodic saves use model and optimizer `.tckpt` files, evaluations use
  `results/step_<step>/`, and the final step is saved;
- TensorBoard-style logs and metrics are written under the model directory.

A fresh run requires a nonexistent model directory unless `create_folder=True`
or `resume=True` is deliberately selected. Never point a fresh run at an
important directory to discover this behavior.

## Multi-GPU arithmetic

The implementation wraps the network in `torch.nn.DataParallel` and selects
`merge_second_batch_multigpu`. Visible devices are controlled by
`CUDA_VISIBLE_DEVICES`; `torch.cuda.device_count()` is the count used by the
training code. Config input `batch_size` and `preprocess.num_workers` are per
GPU and are multiplied at loader construction.

For a schedule authored for one GPU and `N` visible GPUs, the README's
historical guidance is:

```text
new_steps = old_steps // N
new_steps_per_eval = old_steps_per_eval // N
```

Check divisibility and record the intended effective samples/optimizer updates.
Do not both edit the config and add an external multiplier. A request such as
"use four GPUs" is incomplete until the user confirms whether the config was
already scaled; the synthetic verification case specifically catches an
undivided `steps`/`steps_per_eval` pair.

Multi-GPU support was announced as needing testing in the release notes. It is
not verified by a CPU import or by seeing `DataParallel` in source.

## Mixed precision and timing

Set `train_config.enable_mixed_precision: true` only for a compatible historical
Apex installation and backend. The source imports `apex.amp`, initializes at
`opt_level="O2"`, keeps batch norm in fp32, and uses `amp.scale_loss`. The
source's voxel-count assertion is a hard precondition. It is not safe to swap in
`torch.amp.autocast` without revalidating sparse operations, loss scaling, and
checkpoint behavior.

`measure_time=True` causes model timers to synchronize CUDA around stages and
prints average component timings. `evaluate --measure_time=True` additionally
reports preprocessing and tensor conversion timing. Compare runs only with the
same batch size, data loader settings, GPU visibility, and timing flag.

## Evaluation outputs

Historical argument shape (documentation only; do not execute from this
skill):

```text
evaluate --config_path=<config> --model_dir=<model-dir> \
  --ckpt_path=<optional-model-name-step.tckpt> \
  --result_path=<optional-output-dir> \
  --batch_size=<positive-integer> --measure_time=False
```

Although the signature defaults `model_dir=None`, the current implementation
resolves `Path(model_dir)` before it uses `ckpt_path`; provide a valid
`--model_dir` even when restoring an explicit checkpoint. `model_dir` is used
for latest restore when `ckpt_path` is omitted. The current implementation
creates `<result-path>/step_<net-global-step>/result.pkl`, then calls
`eval_dataset.dataset.evaluation(detections, step-directory)`. It prints
throughput, timing (when requested), and evaluator result strings when a result
is returned.

The README's older text mentions `--pickle_result=False` for KITTI label files,
but current `evaluate` explicitly says that option is unsupported and rejects
unknown Fire kwargs. Treat `result.pkl` as the current source behavior and use
the dataset-specific conversion/evaluation API only after checking its contract.
Do not infer a good metric from file creation alone.

## Direct inference context

`second/pytorch/inference.py` defines `TorchInferenceContext`, an
`InferenceContext` adapter used by the historical viewer. A normal lifecycle is:

1. assign a parsed pipeline config to the context;
2. `_build()` constructs the voxel generator, box coder, target assigner,
   registered network, anchor cache, and calls `.cuda().eval()`;
3. `_restore(<model-name-step.tckpt>)` requires a `.tckpt` suffix and restores
   the network;
4. `_inference(example)` converts a prepared example and calls the model's
   KITTI-label prediction path.

This path is not currently an accepted execution route: the module imports a
`predict_to_kitti_label` symbol from `second.pytorch.train`, while the inspected
train source does not define that symbol, and `_build()` hard-codes CUDA. Treat
that mismatch and any missing legacy NMS/backend symbols as a compatibility
block, not as an invitation to patch the public skill.

## Pretrained initialization

The historical docs associate the `car_fhd` weights with the car-FHD config;
no download is bundled here. After placing a user-owned state dictionary at
`<pretrained-state>`, the argument shape is documentation only:

```text
train --config_path=<car-fhd-config> --model_dir=<new-model-dir> \
  --pretrained_path=<pretrained-state> --resume=False
```

The download, provenance, and checksum must be managed by the user. The README
warns that its historical pretrained model predates a sparse-convolution bug
fix, so do not treat its reported metric as a current baseline.

## Freeze, initialize, and restore

`train` can selectively load a pretrained state dict:

- `pretrained_path` points to a PyTorch state dictionary;
- `pretrained_include` retains matching parameter names;
- `pretrained_exclude` removes matching names;
- only keys present in the new model with equal shapes are loaded;
- `freeze_include` sets matching new parameters to `requires_grad=False`;
- `freeze_exclude` freezes parameters that do not match the expression;
- loading pretrained parameters clears global step and metrics.

Use regexes anchored to printed `state_dict` keys, save the original config, and
verify which keys were actually loaded. `resume=True` is different: it keeps
model/global-step state and asks the checkpoint index for the latest compatible
model and optimizer state.

## Historical tuning notes

For NuScenes, the guide recommends ten sweeps, using the mini train split during
development when hardware is limited, tuning lower score thresholds / larger
NMS limits on hard examples, cautious augmentation, and possible KITTI or
PointPillars pretraining. It warns that multi-class NMS requires a parameter
grid search and says not to enable it during early development. These are
historical intent notes, not current benchmark guarantees. The multi-head
NuScenes model additionally requires output order to match config class order;
see `configuration.md`.
