# Repository provenance

Schema: `disco.repo-provenance.v1`

This operating skill was distilled from the `nunchaku` repository and package evidence listed below.

## Source identity

- Repository name: `nunchaku`
- Source commit: `8f41840596bd516d434a1f88ac16c86fdb64e74f`
- Branch observed during construction: `main`
- Tag/describe observed during construction: `v1.3.0dev20260306`
- Source version file: `nunchaku/__version__.py` contains `1.3.0dev`
- Built distribution version observed in the private inspection environment: `1.3.0.dev20260817+cu12.8torch2.7`
- Working tree state during final drafting: dirty because the generated `skills/` outputs and private construction artifacts were untracked.

## Runtime/backend evidence

A private inspection environment successfully built and imported the package with:

- Python 3.11
- PyTorch `2.7.1+cu128`
- Torch CUDA runtime `12.8`
- NVIDIA A100-SXM4-40GB visible as SM 80
- `nunchaku` editable distribution `1.3.0.dev20260817+cu12.8torch2.7`
- Successful CUDA scalar allocation smoke
- Successful imports for root transformer exports, caching adapters, IP-Adapter adapters, LoRA compose/converter helpers, and safetensor merge utility

The private environment path, checkout path, and build logs are construction evidence only and are intentionally not embedded in this public skill.

## Evidence paths used

### Package/source

- `pyproject.toml`
- `setup.py`
- `nunchaku/__init__.py`
- `nunchaku/__version__.py`
- `nunchaku/models/transformers/transformer_flux.py`
- `nunchaku/models/transformers/transformer_flux_v2.py`
- `nunchaku/models/transformers/transformer_qwenimage.py`
- `nunchaku/models/transformers/transformer_sana.py`
- `nunchaku/models/transformers/transformer_zimage.py`
- `nunchaku/models/unets/unet_sdxl.py`
- `nunchaku/models/text_encoders/t5_encoder.py`
- `nunchaku/models/attention_processors/`
- `nunchaku/models/ip_adapter/`
- `nunchaku/pipeline/pipeline_flux_pulid.py`
- `nunchaku/caching/`
- `nunchaku/lora/flux/compose.py`
- `nunchaku/lora/flux/convert.py`
- `nunchaku/lora/flux/nunchaku_converter.py`
- `nunchaku/merge_safetensors.py`
- `nunchaku/utils.py`
- `nunchaku/test.py`

### Documentation

- `README.md`
- `docs/source/installation/installation.rst`
- `docs/source/installation/setup_windows.rst`
- `docs/source/usage/basic_usage.rst`
- `docs/source/usage/attention.rst`
- `docs/source/usage/cache.rst`
- `docs/source/usage/controlnet.rst`
- `docs/source/usage/ip_adapter.rst`
- `docs/source/usage/kontext.rst`
- `docs/source/usage/lora.rst`
- `docs/source/usage/offload.rst`
- `docs/source/usage/pulid.rst`
- `docs/source/usage/qencoder.rst`
- `docs/source/usage/qwen-image.rst`
- `docs/source/usage/qwen-image-edit.rst`
- `docs/source/usage/sdxl.rst`
- `docs/source/usage/zimage.rst`
- `docs/source/python_api/nunchaku.rst`
- `docs/source/faq/`

### Examples/tests used as evidence or verification candidates

- `examples/flux*.py`
- `examples/sana*.py`
- `examples/v1/flux*.py`
- `examples/v1/qwen-image*.py`
- `examples/v1/sdxl*.py`
- `examples/v1/z-image*.py`
- `tests/flux/`
- `tests/v1/`
- `tests/sana/test_examples.py`
- `tests/README.md`

## Exclusions

- `third_party/` was used only as build/submodule evidence and is not operating guidance.
- `.git/` metadata is not part of runtime knowledge.
- Private construction/verification artifacts under `skills/tests/` are not part of the public runtime skill.

## Staleness checks for future users

Reload or refresh this skill when any of the following change:

- `setup.py`, `pyproject.toml`, or CUDA extension build logic.
- Public transformer classes or root exports in `nunchaku/__init__.py`.
- Diffusers pipeline compatibility for Qwen 2509, Z-Image, SDXL, Sana PAG, or FLUX v2.
- LoRA/IP-Adapter/PuLID helpers and their documented support status.
- CUDA/PyTorch wheel compatibility, especially Blackwell FP4 and supported SM targets.
- The package version moves beyond the observed `1.3.0dev` source line.
