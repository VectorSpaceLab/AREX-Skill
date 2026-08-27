# Alpamayo R1 inference API reference

## Standard end-to-end call flow

The bundled smoke script follows this order:

1. `load_physical_aiavdataset(clip_id, t0_us=5_100_000)`
2. `helper.create_message(data["image_frames"].flatten(0, 1))`
3. `processor = helper.get_processor(model.tokenizer)`
4. `processor.apply_chat_template(..., tokenize=True, add_generation_prompt=False, continue_final_message=True, return_dict=True, return_tensors="pt")`
5. `helper.to_device({...}, "cuda")`
6. `model.sample_trajectories_from_data_with_vlm_rollout(..., return_extra=True)`

Keep the same order unless you have a specific reason to deviate.

## Public APIs used by this sub-skill

| API | Signature and defaults | What it does | Key failure modes / notes |
| --- | --- | --- | --- |
| `load_physical_aiavdataset` | `load_physical_aiavdataset(clip_id, t0_us=5100000, avdi=None, maybe_stream=True, num_history_steps=16, num_future_steps=64, time_step=0.1, camera_features=None, num_frames=4)` | Loads one PhysicalAI-AV clip and converts it into Alpamayo-ready tensors. | Raises `ValueError` when `t0_us` is earlier than the history window. The returned history/future tensors are already in the local ego frame at `t0`. |
| `helper.create_message` | `create_message(frames: torch.Tensor)` | Builds the system/user/assistant chat template with the trajectory placeholders and assistant `<|cot_start|>` seed. | Requires a 4D tensor `(N, C, H, W)` and raises `ValueError` otherwise. |
| `helper.get_processor` | `get_processor(tokenizer)` | Loads `Qwen/Qwen3-VL-2B-Instruct` with `min_pixels=163840` and `max_pixels=196608`, then attaches the Alpamayo tokenizer. | Do not use the base Qwen tokenizer alone; the Alpamayo tokenizer carries the trajectory tokens. |
| `helper.to_device` | `to_device(data, device=None, dtype=None)` | Recursively moves tensors inside mappings and sequences. | Safe for nested dict/list structures; non-tensor values are returned unchanged. |
| `AlpamayoR1.from_pretrained` | `AlpamayoR1.from_pretrained("nvidia/Alpamayo-R1-10B", dtype=torch.bfloat16)` | Loads the Alpamayo R1 model and default CUDA-capable weights. | The default inference path uses `flash_attention_2`; pass the SDPA fallback only when flash-attn is not viable. |
| `sample_trajectories_from_data_with_vlm_rollout` | `sample_trajectories_from_data_with_vlm_rollout(self, data, top_p=0.98, top_k=None, temperature=0.6, num_traj_samples=6, num_traj_sets=1, diffusion_kwargs=None, *args, **kwargs)` | Runs VLM rollout plus diffusion sampling and optionally returns reasoning text. | `data` must contain `tokenized_data`, `ego_history_xyz`, and `ego_history_rot`. The method consumes `tokenized_data["input_ids"]`, so rebuild or copy the tokenized input for repeated calls. |

## Generation knobs

- `top_p`, `top_k`, and `temperature` control the autoregressive VLM rollout.
- `num_traj_samples` and `num_traj_sets` expand the number of sampled trajectories per input clip.
- `max_generation_length` is accepted through `**kwargs` and defaults to `self.config.tokens_per_future_traj` when omitted.
- `return_extra=True` returns text traces in addition to trajectories.

## Output contract

- `pred_xyz` is a torch tensor with shape `[B, num_traj_sets, num_traj_samples, 64, 3]` under the default 64-waypoint future horizon.
- `pred_rot` is a torch tensor with shape `[B, num_traj_sets, num_traj_samples, 64, 3, 3]`.
- `extra["cot"]`, `extra["meta_action"]`, and `extra["answer"]` are NumPy arrays reshaped to `[B, num_traj_sets, num_traj_samples]` when `return_extra=True`.
- The decoder keeps the `z` coordinate at the current ego height; use `xy` for the standard minADE check and 2D overlay plots.

## Load-time defaults that matter

- The model release is centered on `nvidia/Alpamayo-R1-10B`.
- The default attention implementation is `flash_attention_2`.
- The bundled smoke path uses `torch.bfloat16` and `num_traj_samples=1` to stay within GPU memory limits.
- Future agents can switch to SDPA via the model config when flash-attn is unavailable or incompatible, but CUDA inference remains the primary route.
