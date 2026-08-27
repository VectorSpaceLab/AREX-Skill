# VLA Data and Actions

## When to read

Read this for Vision-Language-Action tasks: canonical TensorDict layout,
`validate_vla_tensordict`, `RobotDatasetMetadata`, LeRobot/OpenX data, action
chunk targets, action tokenizers, `ActionScaling`, `TinyVLA`, and VLA behavior
cloning or token RL. Run [check_vla_schema.py](../scripts/check_vla_schema.py)
for a deterministic CPU smoke test.

## Canonical TensorDict schema

TorchRL VLA components agree on default nested keys but let callers override
most keys. The default schema is:

```text
TensorDict(
  observation: TensorDict(
    image: tensor or camera-keyed TensorDict,  # [*B, T, C, H, W] when time-structured
    state: tensor,                            # optional proprioception
  ),
  language_instruction: NonTensorData | Text, # per trajectory instruction
  action: float tensor,                       # raw per-step action [*B, T, action_dim]
  vla_action: TensorDict(
    chunk: float tensor,                      # [*B, T, chunk, action_dim]
    tokens: long tensor,                      # [*B, T, chunk, action_dim] or [*B, T, L]
    log_probs: float tensor,                  # optional
    logits: float tensor,                     # optional
    mask: bool tensor,                        # optional
  ),
  action_is_pad: bool tensor,                 # [*B, T, chunk]
  next: TensorDict(...),                      # normal TorchRL transition layout
)
```

Default exported key constants include `OBSERVATION_KEY`, `IMAGE_KEY`,
`STATE_KEY`, `INSTRUCTION_KEY`, `ACTION_KEY`, `VLA_ACTION_KEY`,
`ACTION_CHUNK_KEY`, `ACTION_IS_PAD_KEY`, and `ACTION_TOKENS_KEY`.

`validate_vla_tensordict(tensordict, *, instruction_key="language_instruction",
action_key="action", image_key=("observation", "image"), state_key=("observation",
"state"), require_instruction=True, require_action=True,
require_perception=True, check_finite=True, raise_on_error=True)` is permissive
on shapes but strict about required keys and finite floating actions. With
`raise_on_error=False`, it returns a list of human-readable issues such as
missing language instruction, no perception, missing action, empty instruction,
or non-finite action values.

Use the validator before expensive robot training or conversion jobs. If a
user's data uses custom keys, pass those keys to the validator and to every
transform/policy/loss that consumes the same data.

## Robot datasets and metadata

TorchRL's VLA data surface is designed to mirror OpenX and LeRobot conventions
without hard-importing robot-learning packages during base import. Optional
dataset loaders and image preprocessing may require extras such as `vla` or
`offline-data`.

`RobotDatasetMetadata` carries dataset identity and action metadata such as:

- `dataset_id`, `embodiment_id`, action names, action dimension, action space,
  gripper mode, camera keys, and control frequency;
- optional action statistics/bounds: mean, std, low, high;
- JSON round-trip support for metadata files;
- action-spec construction when `action_dim` is known.

Use metadata to build action normalizers/tokenizers consistently across data
conversion, replay sampling, training, and execution.

## Action scaling

`ActionScaling(in_keys_inv=None, out_keys_inv=None, in_keys=None, out_keys=None,
*, loc=None, scale=None, standard_normal=True)` affine-scales continuous actions.
There are two common VLA uses:

1. **Environment-side denormalization**: attach the transform to a
   `TransformedEnv` so a normalized policy output is mapped to the env action
   range before stepping.
2. **Dataset/replay normalization**: build from metadata or statistics and put
   it on the replay-buffer sample path. When raw env-scale data is written
   through `extend`, pass `in_keys_inv=[]` with explicit stats so `extend` does
   not apply the inverse transform to already-raw actions.

The transform requires either explicit `loc` and `scale`, or a bounded action
spec from its parent env. It raises clear errors for missing initialization,
unbounded or partially bounded action specs, multiple action keys in one
instance, zero scale, or inconsistent bounds.

## Action chunking

`ActionChunkTransform(chunk_size, *, action_key="action", chunk_key=("vla_action",
"chunk"), pad_key="action_is_pad", time_dim=-2, done_key="done")` builds the
standard chunked training target. For each time step `t`, it gathers
`a[t], a[t+1], ..., a[t+H-1]` into `("vla_action", "chunk")` and writes a
boolean padding mask for repeated tail values.

Critical details:

- Input must be time-structured: `[*B, T, action_dim]`. If a sampler returns a
  flat `[B*T, ...]` batch, reshape to `[num_slices, slice_len, ...]` first.
- If `("next", done_key)` is present, chunks stop at trajectory boundaries and
  padded positions are marked in `action_is_pad`.
- The transform is a data transform. It does not decide how many predicted
  actions are executed per environment step.
- For replay buffers, append it as a sample transform so raw per-step actions
  stay stored and chunks are built on sampling.

Use the padding mask in losses. For behavior cloning, set the loss keys so
`action=("vla_action", "chunk")` and `pad_mask="action_is_pad"`.

## Action tokenizers

Action tokenizers map continuous robot actions to discrete IDs and back for
OpenVLA/RT-2-style token heads.

`UniformActionTokenizer(num_bins, *, low, high, action_dim=None)`:

- discretizes each action dimension into uniform bins over `[low, high]`;
- clamps inputs to the bounds before binning;
- returns `torch.long` tokens with the same shape as the action tensor;
- decodes to bin centers with error bounded by half a bin width;
- can be built from `RobotDatasetMetadata` when action bounds are present.

`VocabTailActionTokenizer(num_bins=256, *, full_vocab_size=None, norm_low=None,
norm_high=None, norm_mask=None, gripper_binarize=False,
gripper_binarize_threshold=0.0, gripper_invert=False)` follows the OpenVLA
vocabulary-tail convention. Use it when the policy emits action tokens inside a
language-model vocabulary. Decide up front whether downstream code expects
window IDs `[0, num_bins)` or full vocabulary IDs
`[full_vocab_size - num_bins, full_vocab_size)`.

Common tokenizer failures are invalid bin counts, `high <= low`, missing
metadata bounds, a full vocab smaller than the bin window, or norm statistics
provided for only one side of the affine map.

## Policy/environment contract

Base robot environments do not need to know about VLA TensorClasses. They should
write canonical observations and consume a single env-facing action key:

- reset/step observations: `("observation", "image")`, optional
  `("observation", "state")`, and `"language_instruction"`;
- env action input: `"action"` shaped like `[*B, action_dim]`;
- datasets/replay buffers may also carry `("vla_action", "chunk")`,
  `("vla_action", "tokens")`, and `"action_is_pad"`.

VLA wrappers such as `TinyVLA` and `VLAWrapperBase` can produce chunks, tokens,
or both under structured `vla_action` keys. For execution, bridge a chunk policy
to a one-step env explicitly:

- Prefer `MultiStepActorWrapper` when the env clock should remain one base step
  per collector step. It caches a predicted chunk and emits one action at a
  time, with open-loop, receding-horizon, or closed-loop replanning depending on
  `replan_interval`.
- Use `MultiAction` only when you intentionally retime the MDP so one outer step
  executes a whole chunk inside the env transform.

For token-output policies, request decoded chunks with `output_mode="both"` and
keep token fields for logging or RL losses.

## Training patterns

### Chunked behavior cloning

1. Validate sampled data with `validate_vla_tensordict`.
2. Normalize actions if needed with `ActionScaling.from_metadata(...)` or
   `ActionScaling.from_stats(...)`.
3. Build chunk targets with `ActionChunkTransform(chunk_size=H)`.
4. Configure `BCLoss` or an equivalent objective to consume
   `("vla_action", "chunk")` and mask `"action_is_pad"`.
5. Keep data time-structured through sampling and loss computation.

### Token RL fine-tuning

1. Use a token VLA policy with `output_mode="both"` when the env needs decoded
   continuous chunks but the objective needs tokens/log-probs.
2. Store behavior-policy `("vla_action", "tokens")` and
   `("vla_action", "log_probs")` during rollout.
3. Recompute current log-probs from the same observations during the update.
4. Set `ClipPPOLoss` keys to nested token/log-prob keys and ensure advantages
   have the trailing value dimension expected by PPO losses.

## Safe checks

The bundled `check_vla_schema.py` helper creates valid and invalid tiny
TensorDicts, runs `validate_vla_tensordict`, checks uniform tokenization, verifies
chunk padding at a trajectory boundary, and exercises explicit-stat
`ActionScaling`. It does not import LeRobot/OpenX, download datasets, render,
or require GPU.
