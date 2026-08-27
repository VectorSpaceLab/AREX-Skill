# FlashVSR installation reference

This is the setup runbook for the repository's official DiffSynth-based
FlashVSR implementation. Work in an isolated Python **3.11.13** environment.
The setup is not complete until the extension import gate passes.

## 1. Pin Python and PyTorch first

The source requirements pin the CUDA-enabled torch trio:

```text
torch==2.6.0+cu124
torchvision==0.21.0+cu124
torchaudio==2.6.0+cu124
```

Install those wheels from the cu124 PyTorch index when necessary, then install
the complete requirements file:

```bash
python -m pip install --index-url https://download.pytorch.org/whl/cu124 \
  torch==2.6.0+cu124 torchvision==0.21.0+cu124 torchaudio==2.6.0+cu124
python -m pip install -r <FlashVSR-source-directory>/requirements.txt
```

Confirm the selected interpreter rather than relying on shell activation:

```bash
python --version
python -c "import torch; print(torch.__version__); print(torch.version.cuda)"
```

The target is Python 3.11, torch 2.6.0+cu124, and CUDA 12.4. A different
runtime may be useful for unrelated work but is not evidence for this target.

## 2. Work around the editable-install packaging prerequisite

`setup.py` imports `pkg_resources` at module import time and uses
`pkg_resources.parse_requirements` to read `requirements.txt`. Probe it before
editable installation:

```bash
python -c "import pkg_resources; print('pkg_resources OK')"
```

If it is absent, install a setuptools release that still exposes that legacy
compatibility module, for example:

```bash
python -m pip install 'setuptools<81'
python -c "import pkg_resources; print('pkg_resources OK')"
```

Then install the package. The legacy `setup.py` may require the compatibility
workaround described below:

```bash
python -m pip install -e <FlashVSR-source-directory> --no-build-isolation
```

This caveat is about the repository's packaging code; it is not permission to
remove `pkg_resources` use silently or to claim an editable install from a
failed command.

## 3. Build the required LCSA extension separately

Build Block-Sparse-Attention in a separate build directory. Use the same
active interpreter and inspect both toolkit and torch before compiling:

```bash
git clone https://github.com/mit-han-lab/Block-Sparse-Attention
cd Block-Sparse-Attention
git submodule update --init --recursive
python -m pip install packaging ninja wheel
nvcc -V
python -c "import torch; print(torch.__version__, torch.version.cuda)"
```

For an A100 SM80, compile only SM80 and keep build parallelism conservative:

```bash
export BLOCK_SPARSE_ATTN_FORCE_BUILD=TRUE
export BLOCK_SPARSE_ATTN_CUDA_ARCHS=80
export MAX_JOBS=1
export NVCC_THREADS=1
python setup.py install
```

The upstream extension setup uses C++17, CUDA source compilation, and the
`BLOCK_SPARSE_ATTN_CUDA_ARCHS` variable. `MAX_JOBS=1` and
`NVCC_THREADS=1` are intentionally cautious because the README warns that
parallel compilation can be memory intensive. Ensure `nvcc` comes from the
intended development toolkit and that `gcc`/`g++`, torch, and the compiler ABI
are mutually compatible.

Never treat a successful packaging command as the gate. Run:

```bash
python -c "from block_sparse_attn import block_sparse_attn_func; print('LCSA import OK')"
```

The import gate and a small bf16 streaming-attention kernel smoke test passed
on the prepared A100/SM80 target. A real FlashVSR checkpoint load and inference
run remain separate native verification steps.

## 4. Inspect the environment without changing it

```bash
python <skill-root>/sub-skills/setup-and-weights/scripts/check_environment.py --help
python <skill-root>/sub-skills/setup-and-weights/scripts/check_environment.py
```

The script is diagnostic only. It does not expose module file locations,
private paths, credentials, or cache paths.
