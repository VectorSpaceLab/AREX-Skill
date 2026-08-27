# Inference workflows

## Real-world image inference

1. Install the documented CUDA stack and confirm a compatible GPU. Download
   the Motus checkpoint, WAN model/VAE, and Qwen VLM assets into stable local
   directories; do not put private machine paths in shared config.
2. Prepare one RGB image in the expected three-view T layout. Use the sibling
   camera helper if separate head and wrist images are available.
3. Encode the instruction once with the T5 encoder, saving a tensor file, when
   using a roughly 24–25 GB GPU. On-the-fly `--use_t5` is simpler but the guide
   estimates roughly 41 GB VRAM.
4. Run the real-world CLI with the embodiment YAML, checkpoint directory, WAN
   asset root, image, instruction, and optional embedding/output paths.
5. Check the output image grid and action chunk shape. Preserve the exact
   config/checkpoint pairing when comparing results.

A parser/help invocation is safe; loading the actual model is not a smoke test
because it allocates multi-billion-parameter weights.

## RoboTwin evaluation

Install and configure RoboTwin separately. Set the external `robotwin_root`,
policy/checkpoint, WAN/VLM paths, task name, and evaluation count in a copied
configuration. Use single-task evaluation first, then batch/auto evaluation.
The simulator can mutate output/log directories and may run for a long time;
obtain explicit approval and reserve the required GPU/process count.

## Output interpretation

The denoising loop keeps the condition latent by teacher forcing, decodes future
frames, maps pixels back to `[0,1]`, and integrates the action velocity into an
action chunk. A visually valid grid does not prove task success; RoboTwin
success must come from the simulator evaluator and the same task/checkpoint
configuration.
