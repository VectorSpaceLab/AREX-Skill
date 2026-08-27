# Repository provenance

- Schema: `disco.repo-provenance.v1`.
- Public project name: DALLE-pytorch / DALL-E in PyTorch.
- Distribution name: `dalle-pytorch`.
- Import root: `dalle_pytorch`.
- Package version in source: `1.6.6`.
- Git commit: `58c1e1a4fef10725a79bd45cdb5581c03e3e59e7`.
- Branch at analysis time: `main`.
- Exact tag: none found.
- Working tree state at initial source analysis: clean before generated skill artifacts were written.
- Remote URL: public project URL from package metadata: `https://github.com/lucidrains/dalle-pytorch`.

## Evidence paths

- `setup.py`
- `MANIFEST.in`
- `README.md`
- `dalle_pytorch/__init__.py`
- `dalle_pytorch/version.py`
- `dalle_pytorch/dalle_pytorch.py`
- `dalle_pytorch/vae.py`
- `dalle_pytorch/tokenizer.py`
- `dalle_pytorch/loader.py`
- `dalle_pytorch/attention.py`
- `dalle_pytorch/transformer.py`
- `dalle_pytorch/reversible.py`
- `dalle_pytorch/distributed_utils.py`
- `dalle_pytorch/distributed_backends/*.py`
- `train_vae.py`
- `train_dalle.py`
- `generate.py`
- `docker/Dockerfile`
- `install_deepspeed.sh`
- `install_apex.sh`
- `examples/rainbow_dalle.ipynb`

## Refresh triggers

Refresh this skill when any of these change:

- public constructor signatures for `DiscreteVAE`, `DALLE`, `CLIP`, `OpenAIDiscreteVAE`, `VQGanVAE`, tokenizers, or `TextImageDataset`;
- training/generation helper arguments or checkpoint payload keys;
- torch/OpenAI VAE compatibility constraints;
- DeepSpeed/Horovod/Apex wrapper behavior;
- package metadata dependencies, version, or script packaging decisions.
