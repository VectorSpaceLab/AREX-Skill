# Installation Reference

Read this when preparing an environment for HunyuanVideo or diagnosing dependency failures.

## Documented environment

The repository documents a Linux Conda setup with Python 3.10.9, PyTorch 2.6.0, CUDA 12.4 or CUDA 11.8, and the packages pinned in `requirements.txt`.

Typical manual shape:

```bash
conda create -n HunyuanVideo python==3.10.9
conda activate HunyuanVideo
# Choose exactly one CUDA family matching the host driver.
conda install pytorch==2.6.0 torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia
python -m pip install -r requirements.txt
python -m pip install ninja
python -m pip install git+https://github.com/Dao-AILab/flash-attention.git@v2.6.3
python -m pip install xfuser==0.4.0  # only needed for xDiT multi-GPU
```

If a future task uses PyPI wheels rather than Conda packages, still keep the key compatibility facts: PyTorch 2.6.0, CUDA 11.8/12.4, and flash-attn built against the active CUDA/PyTorch stack.

## Docker option

The repository also documents prebuilt Docker images:

```bash
docker pull hunyuanvideo/hunyuanvideo:cuda_12
docker pull hunyuanvideo/hunyuanvideo:cuda_11
```

Container runs in the README use `--gpus all`, host networking/IPC, relaxed seccomp, stack/memlock ulimits, and privileged mode. Treat those flags as a deliberate GPU runtime choice, not a safe default for unrelated environments.

## Dependency roles

| Package/tool | Role |
| --- | --- |
| `torch==2.6.0` | Core model execution and CUDA runtime. |
| `torchvision` | Video-grid saving helper depends on `torchvision.utils.make_grid`. |
| `diffusers==0.31.0` | Pipeline/model mixins and scheduler infrastructure. |
| `transformers==4.46.3`, `tokenizers==0.20.3` | LLM and CLIP text encoder/tokenizer loading. |
| `accelerate==1.1.1` | Pipeline offload hooks and large-model helpers. |
| `imageio`, `imageio-ffmpeg` | MP4 writing. |
| `gradio==5.0.0` | Web demo. |
| `flash-attn` | Fast attention path used by model attention code; build must match CUDA/PyTorch. |
| `xfuser==0.4.0` | xDiT sequence-parallel multi-GPU path. |

## GPU memory expectations

The README states that HunyuanVideo requires an NVIDIA CUDA GPU, was tested on a single 80GB GPU, and has approximate minimum single-GPU peaks of 45GB for `544x960x129` and 60GB for `720x1280x129`. A 40GB GPU may still be useful for parser/checkpoint checks or multi-GPU attempts, but do not promise single-GPU full-resolution success.
