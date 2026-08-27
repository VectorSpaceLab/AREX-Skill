# Training Reference

Stable Diffusion WebUI exposes textual inversion and hypernetwork creation/training through API routes and the Train tab. These operations are stateful, require a loaded Stable Diffusion model, and can run for a long time.

## Endpoint Map

| Task | Endpoint | Backend call | Completion signal |
| --- | --- | --- | --- |
| Create textual inversion embedding | `POST /sdapi/v1/create/embedding` | `create_embedding(**args)` | `info: create embedding filename: ...` |
| Train textual inversion embedding | `POST /sdapi/v1/train/embedding` | `train_embedding(**args)` | `info: train embedding complete: filename: ... error: None` |
| Create hypernetwork | `POST /sdapi/v1/create/hypernetwork` | `create_hypernetwork(**args)` | `info: create hypernetwork filename: ...` |
| Train hypernetwork | `POST /sdapi/v1/train/hypernetwork` | `train_hypernetwork(**args)` | `info: train embedding complete: filename: ... error: None` |
| Progress | `GET /sdapi/v1/progress` | shared state snapshot | `progress`, `eta_relative`, `state`, `textinfo` |
| Stop current job | `POST /sdapi/v1/interrupt` | `shared.state.interrupt()` | active job exits its loop at the next interrupt check |

Create/train API handlers accept a JSON object whose keys are passed directly to the backend training functions. Route transport, authentication, and base64 mechanics belong to `../api-automation/SKILL.md`.

## Textual Inversion Create

Backend signature:

```text
create_embedding(name, num_vectors_per_token, overwrite_old, init_text='*')
```

Payload keys:

- `name`: embedding token/file stem; illegal characters are stripped to alphanumeric, space, `.`, `_`, and `-`.
- `num_vectors_per_token`: integer vector count; UI allows `1` through `75`.
- `overwrite_old`: set `true` only when replacement is intentional; otherwise the backend asserts if the `.pt` already exists.
- `init_text`: initialization text; defaults to `*`, and empty text creates zero vectors after the conditional model is warmed.

Expected side effects:

- Creates a `.pt` embedding under the configured embeddings directory.
- Reloads textual inversion embeddings after API creation so the new name is immediately selectable.
- Requires a loaded model because it uses the model condition stage to initialize vectors.

## Hypernetwork Create

Backend signature:

```text
create_hypernetwork(name, enable_sizes, overwrite_old, layer_structure=None, activation_func=None, weight_init=None, add_layer_norm=False, use_dropout=False, dropout_structure=None)
```

Payload keys:

- `name`: hypernetwork token/file stem; illegal characters are stripped and an empty result raises `Name cannot be empty!`.
- `enable_sizes`: module sizes as strings or ints; UI defaults to `768`, `320`, `640`, and `1280`, with `1024` also available.
- `overwrite_old`: set `true` only when replacement is intentional.
- `layer_structure`: comma-separated floats or a float list; UI default is `1, 2, 1`.
- `activation_func`: UI default is `linear`; recommended choices depend on architecture.
- `weight_init`: one of `Normal`, `KaimingUniform`, `KaimingNormal`, `XavierUniform`, `XavierNormal` in the UI.
- `add_layer_norm`, `use_dropout`, `dropout_structure`: optional architecture controls; dropout strings become float lists when `use_dropout` is true.

Expected side effects:

- Creates a `.pt` hypernetwork under the configured hypernetwork directory.
- Reloads hypernetwork discovery after creation.

## Shared Train Payload

Textual inversion train backend:

```text
train_embedding(id_task, embedding_name, learn_rate, batch_size, gradient_step, data_root, log_directory, training_width, training_height, varsize, steps, clip_grad_mode, clip_grad_value, shuffle_tags, tag_drop_out, latent_sampling_method, use_weight, create_image_every, save_embedding_every, template_filename, save_image_with_stored_embedding, preview_from_txt2img, preview_prompt, preview_negative_prompt, preview_steps, preview_sampler_name, preview_cfg_scale, preview_seed, preview_width, preview_height)
```

Hypernetwork train backend:

```text
train_hypernetwork(id_task, hypernetwork_name, learn_rate, batch_size, gradient_step, data_root, log_directory, training_width, training_height, varsize, steps, clip_grad_mode, clip_grad_value, shuffle_tags, tag_drop_out, latent_sampling_method, use_weight, create_image_every, save_hypernetwork_every, template_filename, preview_from_txt2img, preview_prompt, preview_negative_prompt, preview_steps, preview_sampler_name, preview_cfg_scale, preview_seed, preview_width, preview_height)
```

Important defaults from the Train tab:

- Embedding learning rate: `0.005`; hypernetwork learning rate: `0.00001`.
- Batch size: `1`; gradient accumulation steps: `1`.
- Log directory field default: `textual_inversion`.
- Prompt template default: `style_filewords.txt`.
- Training width/height: `512` x `512`; UI accepts `64` through `2048` in multiples of `8`.
- Max steps: `100000`; save preview image every `500`; save embedding/hypernetwork copy every `500`.
- Latent sampling: `once`, `deterministic`, or `random`; default is `once`.
- `clip_grad_mode`: `disabled`, `value`, or `norm`; UI clip value default is `0.1`.
- `use_weight`: uses the PNG alpha channel as a loss weight when present; missing alpha falls back to unit weights.

## Validation Order

Training calls validate before loading the dataset. The backend asserts:

- Selected embedding or hypernetwork name is non-empty.
- Learning rate is non-empty and non-zero.
- `batch_size` and `gradient_step` are positive integers.
- `data_root` is set, exists as a directory, and is not empty.
- `template_filename` is selected, maps to a known template, and exists as a file.
- `steps` is a positive integer.
- Save interval and preview interval values are integers greater than or equal to zero.
- `log_directory` is set when either periodic model saves or preview image generation is enabled.

If the initial saved step is already greater than or equal to `steps`, training returns early with the status text `Model has already been trained beyond specified max steps`.

## Dataset Layout

- The dataset root should contain image files. Non-image or unreadable files are skipped during dataset construction.
- For each image, a same-stem `.txt` file supplies caption text when present.
- Without a caption sidecar, the file stem becomes `filename_text`; leading numbers are stripped, and optional filename-token regex settings may further transform it.
- Templates replace `[name]` with the embedding or hypernetwork placeholder token and `[filewords]` with the caption/filename tags.
- When `varsize` is false, images are resized to `training_width` x `training_height`. When true, images remain variable-sized and are bucketed by size for batching.
- Dataset construction encodes images to latents before training; an apparently small dataset can still consume significant GPU time and memory.
- If every file is unreadable or skipped, dataset construction raises `No images have been found in the dataset.`

## Built-In Templates

Known template filenames include:

- `none.txt`: generic `picture` prompt.
- `style.txt`: style prompts using `[name]`.
- `style_filewords.txt`: style prompts using `[filewords]` and `[name]`; default in the UI.
- `subject.txt`: subject prompts using `[name]`.
- `subject_filewords.txt`: subject prompts using both `[name]` and `[filewords]`.
- `hypernetwork.txt`: photo prompts using `[filewords]` for hypernetwork training.

Choose a filewords template when dataset captions matter. Choose a subject/style template when the placeholder token must appear consistently.

## Long-Run Safeguards

- Confirm the active checkpoint before creation/training; training stores checkpoint identity in logs/settings when configured.
- Start with a small `steps` value and disabled periodic previews/saves to validate paths and payload shape.
- Use `/sdapi/v1/progress` for status and `/sdapi/v1/interrupt` for controlled stop; do not assume a client timeout means the server stopped training.
- Periodic save/preview intervals create output subdirectories under a dated log path and increase I/O pressure.
- Low VRAM modes may move model parts between CPU/GPU; route launch/device tuning to `../launch-and-config/SKILL.md`.
- Hypernetwork training clears loaded hypernetworks before starting and reloads model parts in cleanup; avoid concurrent generation jobs.

## Troubleshooting Fast Checks

1. If create fails, check for sanitized empty names and accidental overwrite protection.
2. If train returns `error:` in the `info` string, inspect the embedded error text first; API status can still be HTTP 200.
3. If the dataset path is valid but training says no images found, verify actual image readability and extension/content, not just directory listing.
4. If template errors appear, list the running server's template choices or refresh the Train tab; do not invent template filenames.
5. If the job appears stuck at dataset preparation, expect latent encoding work and poll progress before interrupting.
