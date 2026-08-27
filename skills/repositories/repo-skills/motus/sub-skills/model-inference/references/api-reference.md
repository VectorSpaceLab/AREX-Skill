# Inference and model API reference

## Core model contract

`MotusConfig` derives:

```text
action_chunk_size = num_video_frames * video_action_freq_ratio
```

The architecture joins WAN video tokens, an action expert, and a frozen Qwen VLM
under a trimodal mixture-of-tokens stack. `training_mode: pretrain` omits state
register behavior; `finetune` includes a state token and four registers by
default. The VLM is frozen, while Motus experts/backbone behavior depends on the
loaded checkpoint and training mode.

Important public methods are:

```python
Motus(config)
model.load_checkpoint(path, strict=True) -> dict
model.load_pretrain_weights(path) -> None
model.inference_step(first_frame, state=None, num_inference_steps=50,
                     language_embeddings=None, vlm_inputs=None)
```

`load_checkpoint` accepts a file or a directory containing
`mp_rank_00_model_states.pt`; it expects a `module` state-dict key. Pretrain
loading accepts either `pytorch_model/mp_rank_00_model_states.pt` or a direct
rank file and filters action input/decoder weights for fine-tuning.

## Real-world CLI contract

The command requires `--model_config`, `--ckpt_dir`, `--wan_path`, `--image`,
and `--instruction`. Optional `--output` writes a grid of the condition and
predicted frames. Use either `--t5_embeds EMBEDDINGS.pt` or `--use_t5`; the
latter loads the WAN T5 encoder at runtime. A separate encoding command accepts
`--instruction`, `--output`, optional `--wan_path`, `--text_len`, and `--device`.

The input image is expected to be the concatenated head/left-wrist/right-wrist
view, not three independent files. The action dimension and embodiment config
must agree; the usual Motus action chunk is determined by the config rather
than by the output filename.

## RoboTwin policy contract

The policy config identifies the policy directory and model config; paths
configuration identifies the external RoboTwin root, checkpoint, WAN assets,
and task setup. The simulator owns episode execution and success metrics.
Keep policy files copied into the external runtime only after reviewing the
external runtime's version and side effects.
