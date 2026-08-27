# Troubleshooting and intentional limits

## Missing optional policy dependency

Start with the exact error and run the environment probe for the policy. A
missing `transformers`, `diffusers`, `peft`, `scipy`, `torchdiffeq`,
`qwen_vl_utils`, `datasets`, or tokenizer package is an install gate, not a
model bug. Install the scoped extra from the catalog, for example:

```bash
uv pip install 'lerobot[diffusion]'
uv pip install 'lerobot[pi]'
uv pip install 'lerobot[smolvla]'
uv pip install 'lerobot[groot]'
uv pip install 'lerobot[wallx]'
uv pip install 'lerobot[peft]'
```

Use the package manager/environment that owns the running `lerobot` executable;
do not mix a global pip with a different virtual environment. If the error is
for a tokenizer/model asset rather than a Python import, verify the checkpoint
revision, local cache, network consent, Hub credential, and any
`trust_remote_code` requirement separately. Do not claim that an installed
Python package proves the remote tokenizer is accessible.

## Policy not registered or class import fails

`Unknown policy name` means the built-in registry did not contain the choice;
run plugin discovery in the real CLI if it is a third-party package. If the
choice is registered but `get_policy_class` fails, inspect the full import
exception: it usually identifies the missing scoped extra. A class is expected
in a lazy sibling modeling module following the registered config naming
convention. Do not manually alias a nearby policy.

## Checkpoint feature/stat/processor mismatch

Check all of the following before changing model code:

1. `config.json` has the expected `type`, action chunk/timing, image/state
   dimensions, tokenizer/model IDs, device/dtype, and normalization mapping.
2. `model.safetensors` loads with no unexplained missing/unexpected keys.
3. `policy_preprocessor.json` and `policy_postprocessor.json` exist and their
   serialized step order matches the checkpoint.
4. Processor state safetensors exist for every stateful step.
5. Dataset/environment feature keys and shapes match; use a documented
   `rename_map` for camera/state key renames only.
6. Dataset stats have the required per-feature fields: mean/std for
   `MEAN_STD`, min/max for `MIN_MAX`, q01/q99 for `QUANTILES`, q10/q90 for
   `QUANTILE10`. Check finite values and dimension lengths.
7. Relative-action pre/post steps are present and connected; after loading,
   factory reconnection is expected.

A `ProcessorMigrationError` means the source looks like an older policy format
without a valid processor config. Follow the migration command included in the
exception only after making a backup and confirming the model's version; do not
silently recreate normalization by hand. If a new dataset needs different
statistics, pass an explicit stats override through the supported pipeline
loading path and test the normalization round trip. Stats overrides are
preserved over serialized normalizer state by design.

## CUDA/device failure

`Requested device 'cuda' but CUDA is not available` is an execution block.
Select CPU only for import/config/shape inspection or a deliberately CPU-sized
smoke; do not promise useful VLA training or real-time behavior. If CUDA is
available but a specific index is invalid, inspect `torch.cuda.device_count()`
and `CUDA_VISIBLE_DEVICES`. If a CUDA policy import works but its actual model
or kernel fails, report partial readiness and keep the command blocked.

For AMP, `PreTrainedConfig` may disable AMP on unsupported devices. Recheck the
effective config; MPS AMP is disabled by design in the device utility. VQBeT
with MPS is explicitly rejected by `make_policy`; use CPU or CUDA. A CPU import
is not evidence for a GPU-only optional kernel, tokenizer, or memory budget.

## Training validation failures

- Existing output directory: choose a new directory or explicitly resume; do
  not rely on overwrite behavior.
- `eval_steps > 0`: set a nonzero map-style dataset `eval_split`.
- No policy: provide `--policy.path`/`--policy.type` (or a reward model for its
  separate route).
- `use_policy_training_preset=false`: provide both optimizer and scheduler.
- Hub push enabled without repo ID: disable it for smoke or provide an approved
  repository and credentials.
- `use_peft=true` without a pretrained checkpoint: unsupported; start from a
  base checkpoint and configure the adapter.
- DCP/non-default checkpoint format on a non-sharded run: use safetensors or
  configure a supported sharded run.
- Sharded + PEFT, fp16, env eval, reward model, multiple optimizer, compile,
  activation checkpointing, or context parallel >1: unsupported in this
  release; narrow the request or use a non-sharded plan.

If loss becomes NaN, stop the run. Inspect normalization stats, image scaling
(uint8 versus float), action pad masks, AMP dtype, learning rate, batch size,
and policy-specific processor order before increasing steps.

## Evaluation/rollout failures

- `policy.path` folder lacks `config.json` or weights: it is not a loadable
  policy checkpoint; locate the `pretrained_model` child of a training
  checkpoint or export a policy correctly.
- Environment action shape differs: compare policy output after postprocessing
  with the environment action space; route environment/schema work to the
  owning skill.
- The model returns queued/chunked actions after a task change: call the
  policy's supported queue reset/drop path and reset the episode as appropriate.
- RTC queue under-runs or latency spikes: start with sync, measure inference
  latency, then tune only policy-supported RTC horizon/queue settings. RTC is
  not a hardware safety guarantee.
- Async eval hangs or is hard to diagnose: set `--eval.batch_size=1` and
  `--eval.use_async_envs=false` for isolation.
- Recording/upload appears unexpectedly: inspect strategy and recording flags;
  base strategy must have no dataset, and Hub pushes need explicit consent.
- Hub environment code is rejected: only set `--trust_remote_code=true` after
  reviewing and approving the source.

## Intentional omissions and uncertainty

This sub-skill does not define LeRobot dataset storage/schema, simulator
installation/tasks, RL algorithm configuration, calibration, robot SDKs,
teleoperator setup, or emergency-stop procedures; those are explicit handoffs.
It does not provide universal VRAM thresholds or claim success rates because
those depend on checkpoint, resolution, optimizer, batch, and backend. It does
not promise every registered policy can run from scratch: several VLA policies
expect pretrained remote assets and policy-specific tokenizer/model files.
It does not execute native tests, training, evaluation, downloads, Hub pushes,
or hardware rollouts. The verifier should treat those as separate, approved
operations.
