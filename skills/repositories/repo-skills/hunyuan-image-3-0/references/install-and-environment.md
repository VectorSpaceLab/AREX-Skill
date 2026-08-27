# Install and Environment

This reference gives a public, reproducible setup shape for HunyuanImage-3.0.
It intentionally avoids private environment names or local inspection paths.

## Baseline runtime

- Python: `>=3.12`.
- Distribution name: `hunyuan-image-3`.
- Core package import: `hunyuan_image_3`.
- Real generation backend: CUDA. CPU import checks are not generation proof.

A source-checkout install should use a GPU-capable Python environment when real
generation is selected. A minimal public command shape is:

```bash
python -m pip install torch==2.8.0 torchvision==0.23.0 \
  --index-url https://download.pytorch.org/whl/cu128

python -m pip install \
  einops==0.8.1 numpy==2.2.0 pillow==12.0.0 \
  diffusers==0.35.2 safetensors==0.7.0 tokenizers==0.22.0 \
  'transformers[accelerate,tiktoken]==4.57.1' \
  'huggingface_hub[cli]' 'loguru>=0.7.3' 'gradio>=4.21.0'
```

Optional prompt-enhancement dependency:

```bash
python -m pip install -i https://mirrors.tencent.com/pypi/simple/ \
  --upgrade tencentcloud-sdk-python
```

Optional performance dependencies, only when the GPU stack and compiler/toolkit
are compatible:

```bash
python -m pip install flashinfer-python==0.5.0
# FlashAttention is optional and must match the installed torch/CUDA ABI.
```

## Source-install caveat

This snapshot's package metadata can miss top-level helper modules that the
package imports or optional workflows use, including `utils`, `PE`, and
`vllm_infer`. If a normal wheel-style install cannot import them, use a
source/editable install that keeps the source root importable, or vendor those
modules into the environment explicitly.

A source-checkout install that preserves those top-level modules can use:

```bash
python -m pip install -e . --config-settings editable_mode=compat
```

Do not treat metadata success alone as readiness. Metadata can exist even when
`import hunyuan_image_3` fails due missing top-level helper modules.

## Safe import smoke

From an environment where the package is installed, run:

```bash
python - <<'PY'
from importlib.metadata import version
from hunyuan_image_3 import HunyuanImage3Config, HunyuanImage3ForCausalMM
from hunyuan_image_3.system_prompt import get_system_prompt
print('hunyuan-image-3', version('hunyuan-image-3'))
print(HunyuanImage3Config.model_type)
print(HunyuanImage3ForCausalMM.generate_image)
print(get_system_prompt('None', 'image') is None)
PY
```

Or use the bundled checker:

```bash
python scripts/check_hunyuan_image_environment.py --require-cuda
```

The checker does not load weights or run generation.

## Console entry point caveat

The declared `hunyuan-image` console command is broken in this snapshot because
it calls `main()` without parsed arguments. Do not use the console entry point
as a health check. Use the bundled runner under
`sub-skills/local-inference-cli/scripts/run_hunyuan_image_generation.py`, the
local inference dry-run helper, or a patched source CLI.

## What an environment is ready for

| Check | Ready signal | Not enough |
|---|---|---|
| Package inspection | import/API smoke passes | distribution metadata alone |
| Local CLI planning | bundled dry-run renders command | checkpoint absent but hidden |
| Real generation | CUDA + checkpoint + enough VRAM + package imports | CPU import only |
| DeepSeek rewrite | Tencent credentials + network + PE import | system-prompt files alone |
| vLLM serving | custom vLLM branch + Hunyuan task env vars + checkpoint | `hunyuan-image-3` install alone |
| Gradio UI | app imports fixed + model path + host/port available | wrapper command alone |
