# Custom Training Strategy Escape Hatch

Most user requests should be expressed with `training_strategy.name: "flexible"`. A custom strategy is a code-change path, not a routine config edit.

## Config Is Enough When

Use the flexible strategy when the task can be expressed by combining these pieces:

- Generated vs frozen video/audio modalities with `is_generated`.
- Text conditioning through precomputed `conditions/`.
- Video `first_frame` conditioning.
- Video or audio temporal `prefix`/`suffix` extension.
- Video `spatial_crop` outpainting.
- Video or audio `mask` inpainting.
- Video or audio `reference` IC-LoRA conditioning.
- Frozen cross-modal conditioning: A2V (`audio.is_generated: false`) or V2A (`video.is_generated: false`).
- LoRA vs full fine-tune via `model.training_mode`.

If the user asks for a combination of existing conditions, validate that the modality restrictions still hold. Audio cannot use `first_frame` or `spatial_crop`.

## Custom Code May Be Needed When

Consider a new strategy or condition only when the request requires something the flexible config cannot represent, such as:

- A custom loss term, weighted loss, perceptual loss, or auxiliary target.
- A different noising or timestep policy beyond supported flow-matching sampler settings.
- A new conditioning token layout that is not first-frame, prefix/suffix, spatial crop, mask, or reference concatenation.
- Additional model outputs or a training objective that changes `compute_loss` semantics.
- Additional precomputed data directories that cannot be modeled as a current condition's `latents_dir` or `mask_dir`.

Do not silently edit trainer code. Explain the gap, propose the smallest code change, and ask for explicit consent.

## Safe Change Plan After Consent

1. **Name the strategy or condition.** Use a stable lowercase identifier for the YAML discriminator, for example `"my_condition"` or `"weighted_inpainting"`.
2. **Define the config model.** Create a Pydantic config subclass under the trainer package, inheriting from the base training-strategy config class or condition base. Use `extra="forbid"`, typed fields, validation bounds, and a `Literal[...]` discriminator.
3. **Implement data-source discovery.** `get_data_sources()` must return a mapping from preprocessed data directory names under `data.preprocessed_data_root` to batch keys. This is the single source of truth for dataset wiring and config validation.
4. **Implement training inputs.** A strategy class should prepare patchified latents, text context, per-token timesteps, modality positions, targets, and loss masks. Conditioning tokens should be clean/timestep 0/no loss when that is the intended semantics.
5. **Implement loss.** `compute_loss()` returns a per-element loss tensor of shape `[B]` so the trainer can reduce and track it.
6. **Register the config.** Update the training-strategy package exports/factory and the main config union/discriminator so YAML parsing can instantiate the new strategy. If type checkers reject the base `name` literal, extend that annotation deliberately.
7. **Add a config template.** Provide a small example YAML for the new strategy in a run workspace first. Only add shipped templates and docs tables when this is a maintained repository change.
8. **Update preprocessing only if required.** If the new strategy needs new precomputed artifacts, add an explicit preprocessing step or route the dataset work to `data-preparation`. Do not overload unrelated columns silently.
9. **Validate with safe tests.** Use config parser checks, `get_data_sources()` assertions, and tiny synthetic tensors when practical. Do not run full training as the first test.

## Strategy Implementation Checklist

- The YAML discriminator name matches the Python `Literal` and config union `Tag`.
- Unknown fields are rejected.
- `get_data_sources()` covers `conditions/` and every modality, reference, mask, or custom directory.
- At least one generated target exists.
- Frozen modalities have sigma/timestep 0 and no loss.
- Reference/conditioning tokens are excluded from loss unless the new objective explicitly says otherwise.
- Positions use the same latent coordinate conventions as existing strategies.
- Checkpoint metadata records any downstream inference facts, such as reference scale factors.
- Resume compatibility is considered if the change affects optimizer, scheduler, rank, target modules, or model outputs.
- User-facing docs say that this is an experimental code path and do not predict output quality.

## User-Facing Escape Hatch Response

When a request is unsupported, say:

1. What the user wants in concrete input/output terms.
2. Which flexible conditions exist and why they do not cover the request.
3. The smallest likely code change.
4. The safety and maintenance cost.
5. Ask whether to proceed with the code change, keep to a supported mode, or stop.

Example:

> You want a training objective that adds a perceptual loss on generated video tokens. The flexible strategy can mask, freeze, prefix/suffix, crop, and prepend references, but it cannot add a second loss term from an auxiliary network. This needs a custom strategy with a new config class, `get_data_sources()`, and `compute_loss()` change. Should I implement that code path, adapt the task to a supported flexible mode, or stop here?
