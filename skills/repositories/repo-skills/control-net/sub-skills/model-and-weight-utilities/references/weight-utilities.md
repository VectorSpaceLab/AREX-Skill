# Weight Utilities

This reference distills the original ControlNet 1.0 checkpoint scripts into safe, parameterized behavior. The original scripts are useful evidence, but future agents should avoid blindly copying their destructive output behavior or hard-coded transfer paths.

## Supported Checkpoint Types

| Extension | Loader behavior | Requirements |
| --- | --- | --- |
| `.ckpt` / `.pth` / other PyTorch formats | `torch.load(path, map_location=torch.device(location))`, then unwrap `state_dict` when present. | PyTorch must be installed; use `location="cpu"` for safe diagnostics. |
| `.safetensors` | `safetensors.torch.load_file(path, device=location)`, then unwrap `state_dict` if present. | `safetensors` must be installed. No pickle execution, but tensor keys must still match expectations. |

The bundled inspector reads key names only and does not save checkpoints.

## Add-Control Initialization

The SD1.5 and SD2.1 add-control scripts share the same state-dict mapping rule. They differ by scratch config family:

| Original utility | Config family | Expected input | Output meaning |
| --- | --- | --- | --- |
| `tool_add_control.py input_path output_path` | `cldm_v15` | SD1.x / SD1.5 checkpoint such as `v1-5-pruned.ckpt` | A ControlNet initialization checkpoint whose compatible keys are copied from SD and whose new control-only keys come from the freshly created ControlNet model. |
| `tool_add_control_sd21.py input_path output_path` | `cldm_v21` | SD2.1 base checkpoint such as `v2-1_512-ema-pruned.ckpt` | Same initialization idea, but with SD2.1/OpenCLIP architecture. |

Original command contract:

- exactly two arguments: input checkpoint and output checkpoint
- input checkpoint must exist
- output checkpoint must not already exist
- output directory must already exist
- script creates a scratch ControlNet model from the selected YAML config
- script writes a checkpoint only after `model.load_state_dict(target_dict, strict=True)` succeeds

Mapping algorithm:

1. Build a scratch ControlNet model from the selected config.
2. Load the pretrained Stable Diffusion state dict and unwrap a top-level `state_dict` if present.
3. Iterate every key in the scratch ControlNet state dict.
4. If the scratch key starts with `control_`, strip that prefix and look for `model.diffusion_` plus the stripped suffix in the pretrained SD checkpoint.
5. Otherwise, look for the same key in the pretrained SD checkpoint.
6. If the source key exists, clone that tensor into the target key.
7. If the source key is missing, keep the scratch model tensor and report the key as newly added.
8. Load the resulting target dict with `strict=True` before saving.

Pseudocode:

```text
for target_key in scratch_controlnet_keys:
    if target_key starts with "control_":
        source_key = "model.diffusion_" + target_key after "control_"
    else:
        source_key = target_key

    if source_key in pretrained_sd:
        target[target_key] = pretrained_sd[source_key]
    else:
        target[target_key] = scratch[target_key]
        newly_initialized.append(target_key)
```

Use [`../scripts/inspect_weight_mapping.py`](../scripts/inspect_weight_mapping.py) to dry-run this rule before adapting a writer.

## Transfer-Control Offset Algorithm

The transfer utility transfers a trained ControlNet from one SD1.5-compatible base to another community SD1.x checkpoint by preserving the ControlNet-specific offset from the original base.

Inputs required by the original algorithm:

| Input | Meaning |
| --- | --- |
| `sd15_state_dict` | Original base SD1.5 checkpoint used as the reference baseline. |
| `sd15_with_control_state_dict` | A trained ControlNet checkpoint on top of the reference SD1.5 base. |
| `input_state_dict` | Target community model checkpoint, compatible with the same SD1.x architecture. |
| `path_output` | Destination checkpoint path. |

The original source hard-coded all four paths and wrote output unconditionally after path checks. A safer adaptation should accept all paths as explicit arguments, require the output directory to exist, refuse to overwrite unless the user asks, load on CPU by default, and report missing keys before saving.

Algorithm:

1. Iterate all keys in the trained ControlNet checkpoint.
2. If a key starts with `first_stage_model` or `cond_stage_model`, copy the tensor directly from the target community checkpoint. This preserves the target model's VAE/text-conditioning components.
3. For other keys, decide the corresponding baseline key:
   - if the key starts with `control_`, map it to `model.diffusion_` plus the suffix after `control_`
   - otherwise use the same key
4. If that baseline key exists in the target community checkpoint, compute:
   - `new_tensor = control_tensor + target_tensor - original_sd15_tensor`
5. If the baseline key does not exist in the target checkpoint, keep the trained ControlNet tensor unchanged.
6. Save the final state dict only after all required source tensors have been checked.

Pseudocode:

```text
for key in sd15_with_control:
    if key starts with "first_stage_model" or "cond_stage_model":
        final[key] = target_community[key]
        continue

    if key starts with "control_":
        baseline_key = "model.diffusion_" + key after "control_"
    else:
        baseline_key = key

    if baseline_key in target_community:
        final[key] = sd15_with_control[key] + target_community[baseline_key] - sd15_base[baseline_key]
    else:
        final[key] = sd15_with_control[key]
```

This algorithm assumes the reference, trained-control, and target-community checkpoints are compatible SD1.x-style checkpoints. It is not a general SD2.1 transfer recipe unless the user has verified equivalent architecture/key compatibility.

## Overwrite and Output Guards

Keep these guards in any output-producing adaptation:

- fail when the input checkpoint is missing
- fail when the output path already exists, unless an explicit overwrite option is implemented and selected
- fail when the output directory is missing
- fail when config family and checkpoint family do not match
- report missing baseline keys before saving
- prefer CPU loads for validation
- never download checkpoints implicitly
- never write output in dry-run mode

## When to Route Elsewhere

- Route app loading, prompts, and generated-image controls to [gradio-inference-apps](../../gradio-inference-apps/SKILL.md).
- Route Fill50K, `tutorial_train.py`, training checkpoints, and optimizer settings to [training-and-datasets](../../training-and-datasets/SKILL.md).
- Route Canny/HED/MLSD/OpenPose/MiDaS/segmentation/normal-map preprocessing to [annotators-and-preprocessing](../../annotators-and-preprocessing/SKILL.md).
