# MiniMind-V Architecture Notes

## Visual-token flow

MiniMind-V extends the MiniMind causal language model with a frozen SigLIP2 vision encoder and a small MLP projector.

1. A user prompt contains `<image>` placeholders.
2. The data/inference path expands one image placeholder to 64 `<|image_pad|>` tokens.
3. SigLIP2 P32 at 256x256 produces an 8x8 grid, or 64 visual tokens.
4. `MMVisionProjector` maps SigLIP hidden width into MiniMind hidden width with `LayerNorm -> Linear -> GELU -> Linear`.
5. `count_vision_proj` replaces contiguous image-token embedding runs with projected visual features.
6. The remaining forward/generation path is the MiniMind autoregressive LM.

## Dense and MoE variants

`VLMConfig(use_moe=False)` uses ordinary feed-forward blocks. `use_moe=True` replaces feed-forward blocks with `MOEFeedForward` experts and gate parameters. Match this flag to checkpoint filename and export config; `_moe` filenames imply `use_moe=True`.

## Frozen components

The SigLIP2 vision encoder is frozen during normal training and excluded from saved MiniMind-V checkpoint weights. The trainable VLM side is the projector plus selected LLM layers depending on `freeze_llm`.

## Generation behavior

The base MiniMind generation loop repeats `input_ids` for `num_return_sequences`. `MiniMindVLM.generate` also repeats `pixel_values` so image batches remain aligned. Visual insertion happens only at the first cached step (`start_pos == 0`). If the image changes, restart generation instead of reusing old cache.

## Position buffers

The model includes a guard to recompute RoPE/YaRN buffers when buffers are zero after lazy/meta-device initialization. If position errors occur, check config compatibility before assuming prompt/image issues.
