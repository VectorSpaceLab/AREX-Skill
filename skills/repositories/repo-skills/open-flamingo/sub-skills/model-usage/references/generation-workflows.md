# Generation and checkpoint-loading workflows

These workflows are safe templates for local-cache or caller-supplied checkpoint use. They do not require benchmark datasets. Full model downloads and released checkpoint acquisition are network-, disk-, memory-, and time-dependent; only do them when the caller explicitly permits the budget.

## 1. Preflight prompt and media shape without downloads

Run the bundled validator before attempting model execution:

```bash
python scripts/validate_generation_inputs.py \
  --batch-size 1 \
  --num-media 1 \
  --num-frames 1 \
  --channels 3 \
  --height 224 \
  --width 224 \
  --prompt '<image>An image of'
```

For few-shot captioning, `--num-media` should equal the number of `<image>` tokens in the prompt. Current OpenFlamingo requires `--num-frames 1`.

## 2. Choose matching model identifiers

A released checkpoint must be loaded with its matching language model, tokenizer, vision encoder, and cross-attention interval.

```python
MODEL_SPECS = {
    "3b_mpt1b": {
        "checkpoint_repo": "openflamingo/OpenFlamingo-3B-vitl-mpt1b",
        "clip_vision_encoder_path": "ViT-L-14",
        "clip_vision_encoder_pretrained": "openai",
        "lang_encoder_path": "anas-awadalla/mpt-1b-redpajama-200b",
        "tokenizer_path": "anas-awadalla/mpt-1b-redpajama-200b",
        "cross_attn_every_n_layers": 1,
    },
    "3b_mpt1b_langinstruct": {
        "checkpoint_repo": "openflamingo/OpenFlamingo-3B-vitl-mpt1b-langinstruct",
        "clip_vision_encoder_path": "ViT-L-14",
        "clip_vision_encoder_pretrained": "openai",
        "lang_encoder_path": "anas-awadalla/mpt-1b-redpajama-200b-dolly",
        "tokenizer_path": "anas-awadalla/mpt-1b-redpajama-200b-dolly",
        "cross_attn_every_n_layers": 1,
    },
    "4b_redpajama_base": {
        "checkpoint_repo": "openflamingo/OpenFlamingo-4B-vitl-rpj3b",
        "clip_vision_encoder_path": "ViT-L-14",
        "clip_vision_encoder_pretrained": "openai",
        "lang_encoder_path": "togethercomputer/RedPajama-INCITE-Base-3B-v1",
        "tokenizer_path": "togethercomputer/RedPajama-INCITE-Base-3B-v1",
        "cross_attn_every_n_layers": 2,
    },
    "4b_redpajama_instruct": {
        "checkpoint_repo": "openflamingo/OpenFlamingo-4B-vitl-rpj3b-langinstruct",
        "clip_vision_encoder_path": "ViT-L-14",
        "clip_vision_encoder_pretrained": "openai",
        "lang_encoder_path": "togethercomputer/RedPajama-INCITE-Instruct-3B-v1",
        "tokenizer_path": "togethercomputer/RedPajama-INCITE-Instruct-3B-v1",
        "cross_attn_every_n_layers": 2,
    },
    "9b_mpt7b": {
        "checkpoint_repo": "openflamingo/OpenFlamingo-9B-vitl-mpt7b",
        "clip_vision_encoder_path": "ViT-L-14",
        "clip_vision_encoder_pretrained": "openai",
        "lang_encoder_path": "anas-awadalla/mpt-7b",
        "tokenizer_path": "anas-awadalla/mpt-7b",
        "cross_attn_every_n_layers": 4,
    },
}
```

If using a custom language model and automatic decoder-layer inference fails, supply `decoder_layers_attr_name`; see [api-reference.md](api-reference.md#decoder-layer-attribute-names).

## 3. Instantiate from an existing local cache

This pattern avoids network by setting `use_local_files=True`. The caller must have already populated the model/tokenizer/OpenCLIP cache.

```python
from open_flamingo import create_model_and_transforms

spec = MODEL_SPECS["3b_mpt1b"]
cache_dir = "<CACHE_DIR>"  # caller-supplied cache containing HF/OpenCLIP files

model, image_processor, tokenizer = create_model_and_transforms(
    clip_vision_encoder_path=spec["clip_vision_encoder_path"],
    clip_vision_encoder_pretrained=spec["clip_vision_encoder_pretrained"],
    lang_encoder_path=spec["lang_encoder_path"],
    tokenizer_path=spec["tokenizer_path"],
    cross_attn_every_n_layers=spec["cross_attn_every_n_layers"],
    use_local_files=True,
    cache_dir=cache_dir,
)
model.eval()
tokenizer.padding_side = "left"
```

Optional process-level offline guards, when all files are already cached:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
```

## 4. Resolve or load a checkpoint

### Use an already available checkpoint file

```python
import torch

checkpoint_path = "<CHECKPOINT_PT>"
checkpoint = torch.load(checkpoint_path, map_location="cpu")

if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    checkpoint = checkpoint["model_state_dict"]

if isinstance(checkpoint, dict):
    checkpoint = {key.replace("module.", "", 1): value for key, value in checkpoint.items()}

load_result = model.load_state_dict(checkpoint, strict=False)
print("missing keys:", len(load_result.missing_keys))
print("unexpected keys:", len(load_result.unexpected_keys))
```

`strict=False` is the released-checkpoint pattern. A small number of missing/unexpected keys can be normal when wrappers or prefixes differ; size mismatches usually mean the checkpoint does not match the selected language model, tokenizer, vision encoder, or `cross_attn_every_n_layers`.

### Use a cache-only Hugging Face lookup

This still requires `huggingface_hub`, but `local_files_only=True` prevents downloads:

```python
from huggingface_hub import hf_hub_download

checkpoint_path = hf_hub_download(
    repo_id=spec["checkpoint_repo"],
    filename="checkpoint.pt",
    cache_dir=cache_dir,
    local_files_only=True,
)
```

If network access is explicitly allowed, remove `local_files_only=True` only after confirming disk, memory, and time budget.

## 5. Build `vision_x` from images

For one example with `N` images:

```python
from PIL import Image
import torch

image_paths = ["<IMAGE_1>", "<IMAGE_2>", "<QUERY_IMAGE>"]
images = [Image.open(path).convert("RGB") for path in image_paths]

vision_x = torch.stack([image_processor(image) for image in images], dim=0)
# T_img x C x H x W
vision_x = vision_x.unsqueeze(1).unsqueeze(0)
# B x T_img x F x C x H x W, with B=1 and F=1
```

For a batch, each example should use a prompt whose `<image>` count matches that example's real media count. If examples have different media counts, zero-padding to the maximum media count is possible, but the prompt must not reference padded slots.

## 6. Tokenize an interleaved prompt

Few-shot captioning prompt:

```python
prompt = (
    "<image>An image of two cats.<|endofchunk|>"
    "<image>An image of a sink.<|endofchunk|>"
    "<image>An image of"
)

tokenizer.padding_side = "left"
lang = tokenizer([prompt], return_tensors="pt")
lang_x = lang["input_ids"]
attention_mask = lang["attention_mask"]
```

VQA query prompt:

```python
prompt = "<image>Question:What color is the bus? Short answer:"
```

Completed in-context examples should include `<|endofchunk|>` after the answer. The final query usually remains open so generation can complete it.

## 7. Generate text

```python
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
vision_x = vision_x.to(device)
lang_x = lang_x.to(device)
attention_mask = attention_mask.to(device)

with torch.inference_mode():
    generated = model.generate(
        vision_x=vision_x,
        lang_x=lang_x,
        attention_mask=attention_mask,
        max_new_tokens=20,
        num_beams=3,
    )

prompt_len = lang_x.shape[1]
full_text = tokenizer.decode(generated[0], skip_special_tokens=False)
completion = tokenizer.decode(generated[0, prompt_len:], skip_special_tokens=True)
print(completion)
```

Notes:

- Do not pre-repeat `vision_x` for beam search. `generate()` repeats it internally when `num_beams > 1`.
- The default generation EOS is `<|endofchunk|>`. If a different stop condition is required, pass `eos_token_id` explicitly.
- The generated tensor includes the original prompt tokens.

## 8. Use `forward()` for scoring or log-likelihood

Standard one-pass call:

```python
with torch.inference_mode():
    outputs = model(
        vision_x=vision_x,
        lang_x=lang_x,
        attention_mask=attention_mask,
        clear_conditioned_layers=True,
        use_cache=False,
    )
logits = outputs.logits
```

Cached media pattern for repeated class-name scoring:

```python
try:
    model.cache_media(input_ids=context_ids, vision_x=context_vision_x)
    context_outputs = model(
        vision_x=None,
        lang_x=context_ids,
        attention_mask=context_attention_mask,
        clear_conditioned_layers=False,
        use_cache=True,
    )
    past_key_values = context_outputs.past_key_values

    # Then score candidate tokens with vision_x=None and the cached state.
    candidate_outputs = model(
        vision_x=None,
        lang_x=candidate_ids,
        attention_mask=None,
        clear_conditioned_layers=False,
        past_key_values=past_key_values,
        use_cache=True,
    )
finally:
    model.uncache_media()
```

Do not use `cache_media()` as a generation setup step. `generate()` handles its own temporary cached media state and clears it before returning.

## 9. Practical support cases

- **Local checkpoint generation:** caller supplies populated model/tokenizer/OpenCLIP cache plus `checkpoint.pt`; use sections 2-7.
- **Shape/token correction:** run the validator, fix `F`, `<image>` count, and prompt chunk markers, then retry preprocessing.
- **Offline smoke preparation:** instantiate with `use_local_files=True`, load the checkpoint from a provided file, run only short generation (`max_new_tokens` small) on one or two images.
