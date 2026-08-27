# Generation and ranking workflows

## API image generation

```python
import torch
from dalle_pytorch import DiscreteVAE, DALLE
from dalle_pytorch.tokenizer import tokenizer

vae = DiscreteVAE(image_size=256, num_layers=3, num_tokens=8192, codebook_dim=512, hidden_dim=64)
dalle = DALLE(dim=1024, vae=vae, num_text_tokens=tokenizer.vocab_size, text_seq_len=256, depth=12, heads=16)
# load checkpoint weights before generation
text = tokenizer.tokenize(["fireflies in a field under a full moon"], dalle.text_seq_len)
images = dalle.generate_images(text, filter_thres=0.9, temperature=1.0, cond_scale=1.0)
```

For tiny CPU tests, use `scripts/tiny_generation_api_smoke.py` rather than a full checkpoint.

## Build a generation command template

```bash
python scripts/build_generate_command.py \
  --dalle-path ./dalle.pt \
  --text 'a dog chewing a bone|a cat chasing mice' \
  --num-images 128 \
  --batch-size 4 \
  --top-k 0.9 \
  --outputs-dir ./outputs
```

The historical helper saves images under a prompt-derived output directory and writes `caption.txt`. It calls CUDA and requires a valid checkpoint.

## Prompt splitting

The helper splits `--text` on `|` and processes each prompt separately. Output directory names replace spaces with underscores and are truncated to about 100 characters.

## Image priming

`DALLE.generate_images` accepts an optional image tensor and `num_init_img_tokens`:

```python
primed = dalle.generate_images(
    text_tokens,
    img=starting_crop,
    num_init_img_tokens=14 * 32,
)
```

The image must have shape `(batch, 3, vae.image_size, vae.image_size)`. `num_init_img_tokens` must be less than the image sequence length.

## Classifier-free conditioning strength

If the model was trained with `null_cond_prob > 0`, generation can use `cond_scale > 1`:

```python
images = dalle.generate_images(text_tokens, cond_scale=3.0)
```

This amplifies the conditional logits. Do not promise quality improvements for checkpoints that were not trained with condition dropout.

## Text generation

`DALLE.generate_texts(tokenizer, text=...)` completes text tokens. The source implementation creates CUDA tensors internally, so treat it as GPU-oriented unless you adapt the code.

## CLIP ranking

```python
from dalle_pytorch import CLIP

clip = CLIP(dim_text=512, dim_image=512, dim_latent=512, num_text_tokens=10000)
images, scores = dalle.generate_images(text_tokens, clip=clip)
ranked = scores.argsort(descending=True)
```

`CLIP.forward(..., return_loss=False)` returns same-index similarity scores. With a CLIP scorer supplied to `generate_images`, the method returns `(images, scores)`.
