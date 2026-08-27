# Inference workflows

## 1. Choose the checkpoint

| Checkpoint | Best for | Trade-off |
| --- | --- | --- |
| Helios-Base | Best overall quality | Heavier and slower |
| Helios-Mid | Intermediate staging and experimentation | Not the best final quality |
| Helios-Distilled | Fastest practical generation | Most aggressive compression |

## 2. Choose the mode

| Mode | Input | Typical use |
| --- | --- | --- |
| Text-to-video | Prompt only | Start from a text prompt |
| Image-to-video | Prompt + image | Animate a reference image |
| Video-to-video | Prompt + source video | Re-style or continue an existing clip |

## 3. Choose the runtime shape

- **Single GPU** is the simplest path and is the right default for most
  generation tasks.
- **Low-VRAM offload** is useful when the card is memory-constrained and is
  treated as a single-GPU path in the bundled helper.
- **Context parallelism** is for multi-GPU runs and requires a launcher such as
  `torchrun`.
- **Demo-style startup** is a deployment-style workflow; it is not a cheap
  import smoke test because the local app preloads and compiles model code.

## 4. Run order

1. Check the environment with `scripts/check_helios_env.py`.
2. Decide the checkpoint and mode.
3. Validate that the prompt, image, or video input matches the mode.
4. Run the bundled inference helper.
5. Save the output mp4 and, if needed, rerun with a different checkpoint or
   offload setting.

## 5. Common output expectations

- Default output shape is an mp4 video file.
- The canonical working resolution is 384×640 unless a task says otherwise.
- Frame counts are usually chosen as a multiple of 33 in the source repo's
  workflows; keep that pattern when you want the same chunked behavior.
