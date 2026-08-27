# Prompt Formats for Generation

## `gen_img.py`, `sdxl_gen_img.py`, and `gen_img_diffusers.py`

A prompt file is UTF-8 text with one generation request per non-empty line. Prompt-line options use two hyphens and must be separated from prompt text by spaces.

```text
masterpiece, 1girl, detailed background --n low quality, bad anatomy --w 768 --h 1024 --s 28 --d 42 --l 8.0
landscape photo, {sunrise|sunset}, mountain lake --n foggy, blurry --d 1001,1002 --am 0.8,0.5
```

Important rules:

- `--n` starts the negative prompt. It consumes text until the next recognized prompt option.
- Prompt weights use WebUI-like syntax: `(word)`, `[word]`, `(word:1.3)`, and nested parentheses/brackets.
- `--d` is the seed. When `--images_per_prompt` is greater than one, it can be a comma-separated seed list such as `--d 1,2,3,4`.
- `--am` is additional-network multiplier override. For multiple LoRAs, use comma-separated values such as `--am 0.8,0.5`.
- `AND` separates regional prompt parts for Attention Couple and Regional LoRA.
- Dynamic prompts use braces: `{A|B|C}`, `{e$$A|B|C}` for enumeration, `{2$$A|B|C}` for selecting two, `{1-3$$A|B|C}` for a range, and `{2$$ and $$A|B|C}` for a custom separator.

## Prompt-Line Options

| Option | Meaning | Typical value |
| --- | --- | --- |
| `--n` | Negative prompt | `low quality, blurry` |
| `--w` | Width override | `512`, `768`, `1024` |
| `--h` | Height override | `512`, `768`, `1024` |
| `--s` | Sampling steps override | `20` to `50` |
| `--d` | Seed or comma-separated seeds | `42` or `1,2,3` |
| `--l` | Guidance scale override | `7.5` |
| `--t` | img2img strength | `0.55` to `0.85` |
| `--nl` | Negative prompt guidance scale | `4.0` |
| `--am` | LoRA/additional network multipliers | `0.8` or `0.4,0.7` |
| `--ow` / `--oh` | SDXL original width/height | `1024` |
| `--nw` / `--nh` | SDXL negative original width/height | `1024` |
| `--ct` / `--cl` | SDXL crop top/left | `0` |
| `--c` | CLIP prompt override | short text |
| `--f` | Output file name stem | `sample_001` |
| `--glt`, `--glr`, `--gls`, `--gle` | Gradual Latent overrides | timestep/ratios |
| `--dsd1`, `--dst1`, `--dsd2`, `--dst2`, `--dsr` | Deep Shrink overrides | depths/timesteps/ratio |

Use the bundled validator to check the syntax of these options:

```bash
python skills/sd-scripts/sub-skills/generation/scripts/validate_prompt_file.py prompts.txt --family gen-img
```

## Negative Prompts

Inline negative prompt:

```text
cinematic photo of a wooden cabin --n low quality, jpeg artifacts, watermark
```

Command-line negative prompt in minimal scripts:

```bash
python sd3_minimal_inference.py --ckpt_path <model> --prompt "a cat" --negative_prompt "blur, low quality"
```

Interactive minimal scripts commonly use `--n <negative prompt>` after the prompt; some use `--n -` or `-` to clear the negative prompt.

## SDXL Conditioning in Prompt Files

For SDXL generation, command-line defaults can be overridden per prompt:

```text
studio portrait, sharp focus --n distorted face --w 1024 --h 1024 --ow 1024 --oh 1024 --ct 0 --cl 0
wide cinematic scene --n bad crop --w 1344 --h 768 --ow 1344 --oh 768 --nw 1024 --nh 1024
```

Use these when a prompt file mixes aspect ratios or when negative conditioning should differ from positive conditioning.

## LoRA Prompt Files

For LoRA application through `gen_img.py`, global LoRA files are selected on the command line and per-line multipliers can be set with `--am`:

```bash
python gen_img.py --ckpt <base-model> --outdir outputs/lora --fp16 --xformers \
  --network_module networks.lora networks.lora \
  --network_weights <style.safetensors> <character.safetensors> \
  --from_file prompts.txt
```

```text
style trigger, character trigger, smiling --n low quality --am 0.5,0.8 --d 101
style trigger, character trigger, serious expression --n blurry --am 0.6,0.7 --d 102
```

If each prompt uses Regional LoRA, make the number of `AND` regions align with the number of loaded LoRA weights.

## ControlNet and LLLite Prompt Files

The broad `gen_img.py` interface takes ControlNet/LLLite model and guide-image options on the command line. The Anima LLLite minimal script also supports per-prompt control-image and multiplier overrides:

```text
a cat sitting on a chair --w 1024 --h 1024 --d 42 --cn guides/chair_canny.png --am 0.8
an ornate room --w 1024 --h 1024 --cn guides/room_depth.png --mk masks/window.png --am 0.6
```

Validate those files with:

```bash
python skills/sd-scripts/sub-skills/generation/scripts/validate_prompt_file.py prompts.txt --family anima-lllite
```

## Minimal Inference Prompt Patterns

Family minimal scripts use conventional command-line prompt arguments rather than the full `gen_img.py` prompt parser:

- SD3/Flux interactive prompt options: `--w`, `--h`, `--s`, `--d`, `--n`; Flux also supports `--g`, `--m`, and `--c`.
- Hunyuan/Anima file modes parse one prompt per line with size, seed, and negative prompt overrides.
- Lumina interactive mode accepts width, height, steps, seed, guidance, negative prompt, and LoRA multiplier options.

When unsure, keep prompt files simple: one positive prompt, optional `--n`, optional dimensions, optional seed, and no shell quoting. Use command-line arguments for model/component paths.
