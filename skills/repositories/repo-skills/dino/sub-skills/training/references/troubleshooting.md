# DINO training troubleshooting

Diagnose in the order shown: inputs and config, CUDA/model setup,
single-process construction, data loading, distributed initialization,
checkpoint loading, then scheduler/loop behavior. Preserve the exact command,
config, environment facts, and output directory. Do not respond to a failure
by silently changing scale, classes, batch size, or checkpoint semantics.

## First checks

From the DINO checkout root:

```bash
python skills/disco/dino/sub-skills/training/scripts/build_dino_command.py --help
python -m py_compile skills/disco/dino/sub-skills/training/scripts/build_dino_command.py
```

Then run the planner with the exact config, data root, output directory, mode,
and checkpoint arguments. It is deliberately print-only. For a real run,
remove `--allow-missing-data`; use that flag only to inspect a plan before a
data mount is available.

A setup failure belongs to [data-model-setup](../../data-model-setup/SKILL.md),
which has the read-only data validator, backend checker, config smoke, and
CUDA operator test. Do not use a training command to prove the operator or
data layout.

## CUDA operator, compiler, and GPU failures

**Symptoms:** `MultiScaleDeformableAttention` cannot be imported, an undefined
symbol appears at import, compilation cannot find CUDA/CCCL headers, `nvcc`
rejects the host compiler, or the operator reports that CPU is not
implemented.

**Diagnosis and recovery:**

1. Stop before launching distributed training. Run the environment and custom
   operator gates in [data-model-setup](../../data-model-setup/SKILL.md).
2. Confirm the Python interpreter, PyTorch CUDA build, visible GPU, CUDA
   toolkit, host compiler, and extension all belong to the same environment.
   The verified host used Python 3.11, PyTorch 2.5.1+cu121, CUDA toolkit 12.1,
   and an A100; it needed a compatible GCC <=12 toolchain and explicit CUDA
   header discovery during the build.
3. Rebuild only after selecting the actual toolkit/compiler/header paths for
   the target host, then run the extension's CUDA test. Do not copy guessed
   headers into the repository or hide a failed build by falling back to CPU.
4. DINO's distributed initializer selects NCCL and the denoising path contains
   CUDA tensor operations, so a CPU-only training substitute is not supported.

If import succeeds but the first forward fails, treat that as an operator
ABI/shape/backend failure, not as a dataset or checkpoint failure.

## Out-of-memory or host-memory pressure

**Symptoms:** CUDA OOM during model construction, the first forward, backward,
or a validation step; workers are killed; or the process is terminated by the
scheduler for memory.

**Recovery order:**

1. Confirm the effective batch: `config batch_size * world_size`. Lower the
   config's per-process `batch_size` with `--options batch_size=1` and record
   the changed global batch; do not claim the original recipe was reproduced.
2. Add `--amp` if the hardware and loss behavior permit it. This uses the
   repository's CUDA autocast and gradient scaler.
3. Prefer the 4-scale config over 5-scale when the additional feature level is
   the trigger. The five-scale reference uses one image per GPU for this
   reason. Swin's shipped config already enables `use_checkpoint=True`.
4. Reduce `num_workers` if host RAM or worker startup is the issue. It does
   not reduce GPU activation memory.
5. Only after recording an experiment change, consider `num_queries`, input
   augmentation sizes, or other architecture/data changes. Gradient
   accumulation is not implemented in `main.py`.

Do not respond to an OOM by changing `num_classes` or checkpoint semantics;
those do not generally reduce the activation that caused the failure.

## Data layout and loader failures

**Symptoms:** missing `train2017`, `val2017`, annotations, image references,
COCO API errors, invalid boxes, or a worker traceback while reading a sample.

The ordinary `dataset_file=coco` loader constructs:

```text
<data root>/train2017
<data root>/val2017
<data root>/annotations/instances_train2017.json
<data root>/annotations/instances_val2017.json
```

Use [data-model-setup](../../data-model-setup/SKILL.md) to validate that root,
splits, image references, target fields, category IDs, transforms, and any
panoptic choice. This training route does not repair annotations or invent a
custom dataset implementation. If a custom loader is needed, route its schema
and extension work to data-model-setup before returning here.

A loader error after a successful setup check can still be a corrupted image,
worker-specific filesystem access, or an annotation edge case. Re-run a
bounded single-process sample check with the same config before multiplying
processes; do not diagnose a rank-7 traceback in isolation.

## Invalid config overrides

**Symptoms:** `ValueError: Key ... can used by args only`, a missing attribute
later in model construction, a scale/feature assertion, or a scheduler branch
that does not match the intended run.

- Use `--options KEY=VALUE` with no spaces and put it last. The parser accepts
  numeric values, `True`/`False`, `None`, and comma-separated lists.
- Use direct flags for parser-owned values such as `--coco_path`,
  `--output_dir`, `--resume`, `--pretrain_model_path`, `--num_workers`, and
  `--amp`. Do not pass them through `--options`.
- Keep `num_feature_levels=4` with `[1,2,3]`, or 5 with `[0,1,2,3]` for the
  shipped choices. The backbone builder asserts the allowed index lists.
- Do not copy the shell launcher's unused `dn_scalar`, `dn_label_coef`, or
  `dn_bbox_coef` and assume they affect current DINO. Use `dn_number`,
  `dn_box_noise_scale`, `dn_label_noise_ratio`, and the actual loss names.
- A Python config is executed while being loaded. Use a trusted config, run
  the planner's static syntax/assignment checks, and do not add side effects
  just to compute a value.
- If a custom category mapping is changed, update `num_classes` as max label
  plus one and set `dn_labelbook_size` to at least `num_classes + 1` under the
  repository's custom-data rule.

## Distributed launch and hangs

**Symptoms:** all ranks hang at process-group initialization/barrier, NCCL
cannot find a device, duplicate rank errors, an address/port collision, or
one rank exits while others wait.

1. Prove the single-process command can parse the config, import the model,
   see the GPU, and open the data before adding ranks.
2. Use `python -m torch.distributed.run --nproc_per_node=N` (or the checked-in
   legacy `torch.distributed.launch`) and keep `N` equal to visible GPUs per
   node. `util/misc.py` consumes `WORLD_SIZE` and `LOCAL_RANK` and sets NCCL.
3. For multiple nodes, give every node the same master address/port and
   `--nnodes`, with a unique `--node_rank` from 0 through `nodes-1`. The
   planner refuses to print a multi-node plan without an explicit master
   address.
4. Check `CUDA_VISIBLE_DEVICES`, firewall/routing, free port, and that every
   rank sees the same checkout/config/data paths. Do not use a CPU node as a
   rank in a CUDA/NCCL job.
5. Kill all ranks before retrying and use a fresh port/output directory if the
   old process group or checkpoint state is ambiguous. A partial distributed
   run may leave a rolling checkpoint from the previous completed epoch.

Never add `--world_size` manually to a normal `torchrun` command unless the
launch topology specifically requires it; the environment is multiplied by
`init_distributed_mode` according to its launcher contract.

## Checkpoint mismatch and unexpected keys

**Symptoms:** strict `load_state_dict` errors, missing/unexpected class or
backbone keys, size mismatch in `label_enc`, `class_embed`, feature levels,
queries, or decoder tensors, or a fine-tune run that appears to start from
random weights.

- Full `--resume` expects a matching complete checkpoint and loads
  `checkpoint['model']` strictly. Match scale, backbone, feature indices,
  query count, hidden dimensions, class count, and denoising labelbook.
- `--pretrain_model_path` reads `checkpoint['model']` and uses a non-strict
  filtered load. It is the intended route for a new class head or compatible
  architecture, and `--finetune_ignore label_enc.weight class_embed` avoids
  common class-dependent parameters. Inspect the load result in `info.txt`.
- Never pass both. If `output_dir/checkpoint.pth` exists, `main.py` forces
  resume and the pretrain branch is skipped; use a fresh output directory for
  fine-tuning.
- A checkpoint with only a model state can initialize via pretrain but cannot
  restore optimizer/scheduler progress. A full training checkpoint restores
  those states only when all expected fields are present.
- For an HTTPS `--resume`, the repository may download through PyTorch's hub;
  this sub-skill does not perform or approve downloads. Prefer a trusted local
  checkpoint and record its provenance.

## Non-finite loss or early exit

`engine.train_one_epoch` stops the process when the reduced loss is not
finite. First record the epoch, loss components, scale, AMP setting, data
split, and checkpoint used. Then check target boxes, labels, image sizes, and
class-ID bounds through data-model-setup; verify that the selected config and
labelbook match those labels; and retry only after the cause is understood.
Do not mask NaNs by deleting the checkpoint or disabling all diagnostics.

The `--debug` flag breaks the training loop after a small bounded number of
iterations, but it still builds data/model components and runs validation.
Use it only as a deliberate smoke aid, not as a completed training result.

## Submitit and Slurm assumptions

**Symptoms:** Submitit imports locally but submission fails, `job_dir` errors,
no shared initialization URI, invalid resource request, or a requeued job
starts from the wrong state.

- `run_with_submitit.py` requires a non-empty `--job_dir`; the planner refuses
  to print Submitit commands without one.
- A working Slurm service, scheduler partitions/QOS, node GPU count, shared
  filesystem, and site-specific initialization directory are external
  requirements. They were not available for verification here. Do not claim
  cluster support from the import smoke alone.
- `--ngpus` is GPUs and tasks per node; `--nodes` changes world size. Keep the
  effective global batch calculation visible. The wrapper requests memory as
  50 GB per GPU and applies a hard-coded 16 CPUs per task even though it
  parses `--cpus_per_task`.
- `%j` in `--job_dir` is replaced with the scheduler job ID by the wrapper.
  Confirm the resulting path is shared and writable by every node.
- On preemption, the wrapper's `checkpoint()` callback requeues with
  `checkpoint.pth` as `args.resume` when it exists. If the job dies before an
  epoch checkpoint, the previous completed state is the safe recovery point.
- Do not retry a failed submission repeatedly without checking partition,
  account, QOS, path, and resource errors. No Slurm command is launched by the
  bundled planner.

## What was not verified

The prepared environment proved imports, config parsing, a CUDA tensor, and
custom-op import/build facts. It did not run COCO training, long validation,
checkpoint restoration, downloaded Swin/ConvNeXt weights, a network fetch, or
an active Submitit/Slurm job. Keep those as explicit unresolved checks in any
handoff.
