# Repo Provenance

- Schema: `disco.repo-provenance.v1`
- Source repository: Tencent-Hunyuan/HunyuanImage-3.0
- Public remote URL: https://github.com/Tencent-Hunyuan/HunyuanImage-3.0.git
- Source commit: `6e9113a692a27a0751d82aba3b2015a876646c03`
- Branch at evidence capture: `main`
- Exact tag: none detected
- Package distribution: `hunyuan-image-3`
- Package version: `3.0.0`
- Python requirement: `>=3.12`
- Evidence-capture dirty state: clean before generated skill artifacts were written
- Generated skill id: `hunyuan-image-3-0`

## Relative evidence paths

- `README.md`
- `README_zh_CN.md`
- `Hunyuan-Image3.md`
- `pyproject.toml`
- `setup.py`
- `requirements.txt`
- `hunyuan_image_3/`
- `utils/import_utils.py`
- `PE/`
- `run_image_gen.py`
- `run_demo_instruct.sh`
- `run_demo_instruct_distil.sh`
- `app/`
- `run_app.sh`
- `vllm_infer/`
- `docker/hyimage3_vllm.Dockerfile`
- `assets/demo_instruct_imgs/`

## Verification baseline

The construction environment verified package imports, public API signatures,
CLI help, vLLM client help, and a CUDA tiny-allocation smoke. It did not
download checkpoints, call Tencent Cloud, build Docker images, start Gradio or
vLLM services, or run full image generation.

## Refresh triggers

Refresh this skill if any of these change:

- package metadata, distribution name, or Python requirement;
- `hunyuan_image_3` API signatures or import layout;
- `run_image_gen.py` flags, console entry point, or rewrite branch;
- Gradio app imports under `app/`;
- vLLM client/server scripts or required vLLM branch;
- model card VRAM guidance, checkpoint names, or recommended sampling steps.
