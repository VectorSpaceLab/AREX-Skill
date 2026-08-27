# Motus data formats

## Shared sample contract

`data.dataset.create_dataset(config, val=False)` returns one of the dataset
implementations selected by `config.dataset.type`. A sample is normally
collated into:

```text
first_frame       [B, C, H, W]       values in [0, 1]
video_frames      [B, F, C, H, W]   target frames
initial_state     [B, D]             absent for latent-action pretraining
action_sequence   [B, A, D]
language_embedding [B, S, E]         padded/truncated WAN T5 features
vlm_inputs       dict or None        padded Qwen processor tensors
```

`collate_fn` drops `None` samples. It stacks the image/action tensors, pads
language embeddings to 512 tokens, and pads VLM token sequences. A batch can
therefore become `None` when every episode failed; investigate the underlying
episode errors instead of passing it to the model.

## RoboTwin 2.0

```text
<root>/<clean|randomized>/<task>/
  qpos/<episode>.pt
  videos/<episode>.mp4
  umt5_wan/<episode>.pt
  metas/<episode>.txt       # required when VLM processing is enabled
```

`data_mode` is `clean`, `randomized`, or `both`; `task_mode` is `single` or
`multi`. In multi-task mode, episodes are sampled with equal task weights. Each
qpos/video/embedding triplet must exist. A language embedding file can contain
multiple candidate tensors; the loader chooses one and uses the corresponding
line from the task metadata text.

## AC-One and Aloha-Agilex-2

Both robot families recursively discover task directories containing:

```text
<task>/videos/<episode>.mp4
<task>/qpos/<episode>.pt
<task>/instructions/<episode>.txt
<task>/instructions/<episode>.pt
```

An alternative `umt5_wan/` embedding directory is accepted. A single global
text/embedding pair can be reused for every episode; otherwise resources are
matched by episode id, with a task-name fallback. AC-One and Aloha normalize
state/actions with the corresponding bundled statistics before returning a
sample. Validation disables image augmentation.

## Latent-action pretraining

Each configured root is searched recursively for a leaf containing:

```text
<leaf>/videos/<episode>.mp4
<leaf>/umt5_wan/<episode>.pt
<leaf>/latent_action_dim14/<episode>.pt
<leaf>/metas/<episode>.txt
```

All four basenames must intersect. Latent actions are a tensor, or a dict with
a tensor under `latent_action`; a list is rejected. There is no initial state.
The loader samples adjacent-frame latent actions and leaves quantile
normalization disabled in the current implementation, so do not silently
apply robot action normalization to this dataset.

## LeRobot

A local LeRobot root contains `meta/`, `data/`, and `videos/`. The wrapper can
select one repository (`task_mode: single`) or several repositories
(`task_mode: multi`). Prefer a precomputed
`observation.images.cam_concatenated` feature. Otherwise it stitches
`cam_high`, `cam_left_wrist`, and `cam_right_wrist`, then falls back to a
single image feature. WAN T5 embeddings may be referenced from episode metadata
or generated into a cache; generation is a mutating, model-dependent step.

## Image and action conventions

Video decoding returns RGB tensors in `[T,C,H,W]` with values `[0,1]`. Resizing
preserves aspect ratio and center-pads with black pixels. State/action values
are float tensors; robot datasets use their embodiment statistics. Keep the
same dimension and time settings in the config, dataset, checkpoint, and
inference command.
