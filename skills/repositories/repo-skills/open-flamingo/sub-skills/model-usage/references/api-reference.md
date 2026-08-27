# OpenFlamingo model API reference

This reference distills the OpenFlamingo 2.0.1 public construction and inference API. It is written for runtime use without reopening source files.

## Public imports

```python
from open_flamingo import create_model_and_transforms, Flamingo
```

`create_model_and_transforms()` returns a `Flamingo` model, an OpenCLIP image processor, and a Hugging Face tokenizer augmented with Flamingo special tokens.

## Construction signature

```python
def create_model_and_transforms(
    clip_vision_encoder_path,
    clip_vision_encoder_pretrained,
    lang_encoder_path,
    tokenizer_path,
    cross_attn_every_n_layers=1,
    use_local_files=False,
    decoder_layers_attr_name=None,
    freeze_lm_embeddings=False,
    cache_dir=None,
    **flamingo_kwargs,
):
    ...
```

Key behavior:

- Calls `open_clip.create_model_and_transforms(clip_vision_encoder_path, pretrained=clip_vision_encoder_pretrained, cache_dir=cache_dir)` and sets `vision_encoder.visual.output_tokens = True`.
- Loads the tokenizer with `AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=use_local_files, trust_remote_code=True, cache_dir=cache_dir)`.
- Adds `"<|endofchunk|>"` and `"<image>"` as `additional_special_tokens`; if no pad token exists, adds `"<PAD>"`.
- Loads the language model with `AutoModelForCausalLM.from_pretrained(lang_encoder_path, local_files_only=use_local_files, trust_remote_code=True, cache_dir=cache_dir)`.
- Extends the language model instance with `FlamingoLMMixin`, then replaces its decoder blocks with Flamingo-wrapped layers containing gated cross-attention at the requested interval.
- Infers the decoder block attribute when possible. If inference fails, pass `decoder_layers_attr_name` manually.
- Resizes LM token embeddings after adding Flamingo tokens.
- Freezes all parameters, then unfreezes the Perceiver resampler, gated cross-attention layers, and LM input embeddings unless `freeze_lm_embeddings=True`.
- Passes `**flamingo_kwargs` to `Flamingo.__init__`; unexpected kwargs raise the normal Python `TypeError`. The commonly relevant kwarg is `gradient_checkpointing`.

## `Flamingo.forward()` signature

```python
def forward(
    vision_x,
    lang_x,
    attention_mask=None,
    labels=None,
    clear_conditioned_layers=True,
    past_key_values=None,
    use_cache=False,
):
    ...
```

Inputs:

- `vision_x`: media tensor shaped `B x T_img x F x C x H x W`; **`F` must equal `1`**.
- `lang_x`: token ids shaped `B x T_txt`.
- `attention_mask`: optional mask shaped `B x T_txt`.
- `labels`: optional LM labels for loss computation.
- `clear_conditioned_layers`: leave `True` for normal calls. Set `False` only when deliberately reusing conditioned/cached state for a sequence of related `forward()` calls.
- `past_key_values` and `use_cache`: forwarded to the underlying Hugging Face causal LM.

Runtime behavior:

- A standard call requires `vision_x` and conditions all Flamingo layers by encoding media plus locating `<image>` tokens in `lang_x`.
- If `cache_media()` has been called, pass `vision_x=None`; passing `vision_x` while cached media is active raises an assertion.
- The return object is the underlying Hugging Face causal LM output, commonly `CausalLMOutputWithPast` with `.logits` and optionally `.past_key_values`.
- When `clear_conditioned_layers=True`, media/text conditioning is cleared before return.

## `Flamingo.generate()` signature

```python
def generate(
    vision_x,
    lang_x,
    attention_mask=None,
    **kwargs,
):
    ...
```

Inputs are the same media and token tensors as `forward()`. `**kwargs` are passed to the language model's `generate()` after OpenFlamingo handles media conditioning. Common kwargs include `max_new_tokens`, `max_length`, `min_new_tokens`, `num_beams`, `temperature`, `top_k`, `top_p`, `do_sample`, `length_penalty`, `num_return_sequences`, `no_repeat_ngram_size`, and `early_stopping`.

Generation-specific behavior:

- `num_beams` defaults to `1`. If `num_beams > 1`, OpenFlamingo internally calls `vision_x.repeat_interleave(num_beams, dim=0)` before generation. Keep your `lang_x` batch at the original batch size.
- If no `eos_token_id` is supplied, `generate()` uses the `<|endofchunk|>` token id as the generation EOS.
- The returned tensor contains the prompt tokens followed by generated tokens. Slice off the prompt length if only the completion is needed.
- `generate()` sets cached vision state internally and clears it before return. Do not call `cache_media()` as a prerequisite for generation.

## Media caching API

```python
model.cache_media(input_ids, vision_x)
model.uncache_media()
```

Use media caching for repeated `forward()` calls such as class-name scoring or log-likelihood ranking. Caching encodes `vision_x`, stores media locations from `input_ids`, and sets the language model into cached-media mode.

Safe pattern:

1. Call `model.cache_media(input_ids=context_ids, vision_x=context_media)`.
2. Call `model(vision_x=None, lang_x=..., clear_conditioned_layers=False, use_cache=True or False, ...)` for the cached scoring steps.
3. Always call `model.uncache_media()` in a `finally` block or immediately after the scoring loop.

Important constraints:

- While cached media is active, standard `forward()` calls must pass `vision_x=None`.
- Cached media makes later tokens attend to the last cached media location when generation-style one-token calls contain no new `<image>` tokens.
- The method comment says this cache is not meant for `generate()`.

## Prompt and tensor contract

### Special tokens

- `<image>` marks where a media item occurs in the text stream.
- `<|endofchunk|>` marks the end of text associated with a media item or completed in-context example.
- Use the exact strings. Changing whitespace inside either token prevents tokenization as the intended special token.

### Text prompts

A three-image captioning prompt has three `<image>` tokens and two completed chunks before the query:

```text
<image>An image of two cats.<|endofchunk|><image>An image of a sink.<|endofchunk|><image>An image of
```

For VQA-style prompts, a common pattern is:

```text
<image>Question:What color is the bus? Short answer:
```

For classification/ranking prompts, include the `<|endofchunk|>` marker when the answer is already supplied as an in-context example.

### Media tensor

OpenFlamingo expects:

```text
vision_x.shape == (B, T_img, F, C, H, W)
F == 1
```

Typical image preprocessing for one example:

```python
processed = [image_processor(img).unsqueeze(0) for img in images]  # each: 1 x C x H x W
vision_x = torch.cat(processed, dim=0)                             # T_img x C x H x W
vision_x = vision_x.unsqueeze(1).unsqueeze(0)                      # 1 x T_img x 1 x C x H x W
```

For batched evaluation, prepare `B x max_images x 1 x C x H x W`; prompts should contain the same number of `<image>` markers as the real media used by each example. Extra padded image slots should not be referenced by prompt tokens.

## Decoder layer attribute names

`create_model_and_transforms()` can infer common model families. If a new or custom language model fails inference, pass the matching decoder block path manually.

| Model family/class marker | Decoder block attribute |
| --- | --- |
| OPT | `model.decoder.layers` |
| GPT-J or `gpt-j` | `transformer.h` |
| Pythia / GPT-NeoX | `gpt_neox.layers` |
| LLaMA | `model.layers` |
| MPT / MosaicGPT | `transformer.blocks` |

If the language model class name is not recognized, inspect the model object for the `nn.ModuleList` that stores transformer blocks and pass its dotted path as `decoder_layers_attr_name`.

## Released checkpoint families

The released model families combine OpenAI CLIP ViT-L/14 with these language models and cross-attention intervals:

| Checkpoint family | Language model | Vision encoder | `cross_attn_every_n_layers` |
| --- | --- | --- | --- |
| `openflamingo/OpenFlamingo-3B-vitl-mpt1b` | `anas-awadalla/mpt-1b-redpajama-200b` | `ViT-L-14` / `openai` | `1` |
| `openflamingo/OpenFlamingo-3B-vitl-mpt1b-langinstruct` | `anas-awadalla/mpt-1b-redpajama-200b-dolly` | `ViT-L-14` / `openai` | `1` |
| `openflamingo/OpenFlamingo-4B-vitl-rpj3b` | `togethercomputer/RedPajama-INCITE-Base-3B-v1` | `ViT-L-14` / `openai` | `2` |
| `openflamingo/OpenFlamingo-4B-vitl-rpj3b-langinstruct` | `togethercomputer/RedPajama-INCITE-Instruct-3B-v1` | `ViT-L-14` / `openai` | `2` |
| `openflamingo/OpenFlamingo-9B-vitl-mpt7b` | `anas-awadalla/mpt-7b` | `ViT-L-14` / `openai` | `4` |

Use the same language model, tokenizer, vision encoder, and cross-attention interval that correspond to the checkpoint. Mismatches usually produce missing/unexpected keys or size mismatches during `load_state_dict()`.
