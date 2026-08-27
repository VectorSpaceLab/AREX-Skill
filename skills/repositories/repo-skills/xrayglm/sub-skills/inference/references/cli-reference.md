# CLI inference reference

This reference describes the checked-in `cli_demo.py` contract without
copying the demo. Run it from the repository root so relative checkpoint and
image paths resolve predictably.

## Environment and installation

Use an isolated Python 3.10 environment. The compatible imports were verified
with torch 2.1.2+cu121, torchvision 0.16.2+cu121, transformers 4.27.4,
SwissArmyTransformer 0.3.7, gradio 3.50.2, cpm_kernels 1.0.11,
bitsandbytes 0.39.0, and deepspeed 0.10.3. Install the normal inference/training
set with:

```bash
python -m pip install -r requirements.txt
```

For inference without deepspeed:

```bash
python -m pip install -r requirements_wo_ds.txt
python -m pip install --no-deps 'SwissArmyTransformer>=0.3.6'
```

The latter is a dependency workaround, not a guarantee that every newer
package is compatible. Confirm the package versions and imports before loading
large weights. A CUDA smoke test and free-memory check are useful; `nvcc` is
not required for the Python CUDA smoke test.

## Arguments and defaults

The CLI parser exposes these options:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--max_length` | `2048` | Total sequence capacity used by generation. |
| `--top_p` | `0.4` | Nucleus sampling probability. |
| `--top_k` | `100` | Top-k sampling count. |
| `--temperature` | `0.8` | Sampling temperature. |
| `--english` | off | Use English prompts/separators and English invalid-token range. |
| `--quant {8,4}` | unset | Quantize the transformer to 8 or 4 bits after load. |
| `--from_pretrained PATH` | `visualglm-6b` | Checkpoint/model identifier passed to SAT `AutoModel`. |
| `--prompt_zh TEXT` | `描述这张图片。` | First image prompt in Chinese mode. |
| `--prompt_en TEXT` | `Describe the image.` | First image prompt in English mode. |

The default `visualglm-6b` can resolve a remote base-model location through the
underlying library. For controlled local runs always pass a checkpoint path
and verify the path before starting. The repository's example checkpoints
include XrayGLM-300 and XrayGLM-3000; checkpoint availability and terms must be
verified separately.

## Launch and interaction

```bash
python cli_demo.py --from_pretrained checkpoints/checkpoints-XrayGLM-3000 \
  --prompt_zh '详细描述这张胸部X光片的诊断结果'
```

At the image prompt, enter a readable local path or an approved image URL. A
blank response enters plain-text mode. With an image, the configured first
prompt is sent immediately; subsequent prompts are requested interactively.
Use `clear` to leave the inner loop, reset history and the cached image, and
ask for a new image. Use `stop` at either loop level to terminate. A URL is
fetched with a 10-second request timeout by the chat helper, but this is not a
complete SSRF, size, or content-type defense; use trusted URLs and an approved
network policy.

For English mode:

```bash
python cli_demo.py --english \
  --from_pretrained checkpoints/checkpoints-XrayGLM-3000 \
  --prompt_en 'Describe this chest radiograph.'
```

Chinese turns are serialized using `问：<question>\n答：<answer>\n`; English
turns use `Q:<question>\nA:<answer>\n`. The generated answer is split on
`答：` or `A:` before the printed `XrayGLM：` prefix. Keep one language and one
image study per session. To change language, clear the session and relaunch
with `--english` as appropriate.

## Sampling and quantization

`max_length` must exceed the encoded prompt and image placeholder budget. Very
long histories can exhaust it before a useful answer is generated. `top_p`,
`top_k`, and `temperature` are passed to SAT's `BaseStrategy`; record them for
reproducibility. The chat signature also supports `repetition_penalty` (default
`1.2`), although the CLI does not expose a flag for it.

`--quant 4` and `--quant 8` call SAT's quantizer on `model.transformer` after
model construction. In the observed environment bitsandbytes 0.39.0 warned
that it was CPU-only or missing libcudart. Therefore the flag's parse success
is not evidence that a quantized CUDA inference will load. Treat quantization
as a separately verified capability; if it fails, repair the compatible
CUDA/bitsandbytes installation or omit the flag. Quantization can change
memory use and output quality.

## Output and provenance

The process prints a decoded response for each turn. Save the raw output only
with the corresponding checkpoint identifier/path (not secret tokens), image
provenance, language, prompt, and generation settings. Outputs are stochastic
research artifacts and are not medical findings. Do not expose patient images
or responses through shell logs, public share links, or unapproved telemetry.
