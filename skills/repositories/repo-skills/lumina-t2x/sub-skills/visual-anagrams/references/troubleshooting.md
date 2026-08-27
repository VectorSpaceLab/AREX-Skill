# Visual Anagrams Troubleshooting

## Purpose

Use this page when illusion generation or animation fails before the image is saved.

## Missing FlashAttention or incompatible CUDA stack

**Symptoms**
- `ModuleNotFoundError: No module named 'flash_attn'`
- The generator fails while importing the model code.

**Likely cause**
- The environment does not have a compatible FlashAttention build.

**Recovery**
- Install a CUDA-compatible FlashAttention build before retrying.
- Re-run the shared environment checker with `--workflow visual-anagrams`.

## Missing animation dependencies

**Symptoms**
- `ModuleNotFoundError: No module named 'imageio'`
- `visual_anagrams.animate` fails while building the video output path.

**Likely cause**
- The animation extras from the visual-anagrams environment file were not installed.

**Recovery**
- Install the `imageio` and `imageio-ffmpeg` dependencies before retrying animation.
- Re-run the visual-anagrams checker after the dependency repair.

## Prompt/view count mismatch

**Symptoms**
- `AssertionError: Number of prompts must match number of views`

**Likely cause**
- The prompt list and the view list do not have the same length.

**Recovery**
- Recheck the command line or the `run.sh` template and make the counts identical.

## Missing metadata for animation

**Symptoms**
- `animate.py` cannot reuse prompts or views.
- The script asks for a view or fails to find metadata.

**Likely cause**
- `metadata.pkl` was not saved with the original generation run.

**Recovery**
- Regenerate with metadata saving enabled, or supply `--view`, `--prompt_1`, and `--prompt_2` manually.

## View-argument issues

**Symptoms**
- A parameterized view behaves unexpectedly.
- The generator errors while building a view.

**Likely cause**
- A view that needs `view_args` was called without the right parameter.

**Recovery**
- Check `references/views.md` for the common defaults.
- Pass explicit `view_args` for the view type you selected.

## Resolution / upsampling confusion

**Symptoms**
- The generated size is different from what you expected.
- The upsample path does not run.

**Likely cause**
- The category-resolution value or `--generate_1024` flag was set incorrectly.

**Recovery**
- Recheck the `category:WxH` format and only enable the upsample path when you need it.
