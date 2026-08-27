# MiniMind-V CLI Inference Workflows

## What the CLI does

The command-line inference entrypoint loads a tokenizer, loads either native PyTorch weights or a Transformers-format checkpoint, attaches the SigLIP2 vision encoder, loops over sorted images, expands the image placeholder, applies the chat template, and calls `model.generate(..., pixel_values=pixel_values)`.

## Important flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `--load_from` | `model` | Native mode when the value contains substring `model`; otherwise Transformers directory mode. |
| `--save_dir` | `out` | Native checkpoint directory. |
| `--weight` | `sft_vlm` | Native weight prefix. |
| `--hidden_size` | `768` | Hidden size encoded in native checkpoint filename. |
| `--num_hidden_layers` | `8` | Layer count for native config. |
| `--use_moe` | `0` | Dense (`0`) or MoE (`1`, `_moe` filename suffix). |
| `--max_new_tokens` | `512` | Generation length; lower for smoke tests. |
| `--temperature` | `0.7` | Sampling temperature. |
| `--top_p` | `0.85` | Nucleus sampling threshold. |
| `--image_dir` | `dataset/eval_images` | Directory of `.png`, `.jpg`, `.jpeg`, or `.bmp` images. |
| `--device` | CUDA if available else CPU | PyTorch device; CUDA path uses half precision. |
| `--open_thinking` | `0` | Passed to tokenizer chat template as boolean. |

## Native `.pth` mode

Native mode constructs the checkpoint path:

```text
save_dir/weight_hidden_size[_moe].pth
```

Examples: `out/sft_vlm_768.pth`, `out/pretrain_vlm_768.pth`, and `out/sft_vlm_768_moe.pth`.

Before generation, run the bundled preflight checker:

```bash
python path/to/minimind_vlm_inference_check.py --repo-root . --load-from model --weight sft_vlm --use-moe 0 --image-dir path/to/images --device cpu
```

Use `--device cuda` only after confirming a compatible GPU and memory budget.

## Transformers mode

Transformers mode is selected when `--load_from` does not contain `model`. The directory should include config, tokenizer files, trusted custom code or `auto_map`, and weights (`.bin`, `.safetensors`, or shard index). Avoid paths such as `transformers-model` because the substring `model` will trigger native mode.

Even in Transformers mode, image-conditioned generation needs the local SigLIP2 vision encoder unless the user's code was adapted.

## Image guidance

- Use one or two small RGB-compatible images for smoke tests.
- Reduce `--max_new_tokens` for quick validation.
- Successful output prints each image name, prompt, generated text, and optional speed.
- Poor output after successful generation usually indicates mismatched checkpoint type, `--use_moe`, hidden size, tokenizer, or SigLIP2 resources.
