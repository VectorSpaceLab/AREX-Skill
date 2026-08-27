# PhysMamba backend contract

PhysMamba is a CUDA-backed model, not a model that happens to run on CPU when
an optional import is absent. The model imports `Mamba` from `mamba_ssm` and
uses `timm` layers. The bundled Mamba README describes a Linux/NVIDIA/CUDA
installation path, and its module test constructs a CUDA tensor and runs a
Mamba block; those artifacts are backend evidence, not a portable runtime
script.

## Public requirements to verify

For the prepared rPPG-Toolbox target, treat these as generic public dependency
facts that must be checked against the user's installation:

- PyTorch **2.1.2+cu121** (a CUDA 12.1 build);
- `causal-conv1d` **1.0.0**;
- `mamba-ssm` **2.2.2**;
- a compatible NVIDIA driver, CUDA toolkit/compiler where a wheel is not
  available, and the matching `timm` dependency.

The repository's older Mamba README also states Linux, NVIDIA GPU, PyTorch
1.12+, and CUDA 11.6+ as broad upstream requirements. Do not merge those broad
minimums with the tested rPPG target facts: a package that satisfies the old
README may still be incompatible with the target PhysMamba environment.

## Verification sequence

1. Check the interpreter and torch build without importing the model:

   ```bash
   python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
   python -c "import importlib.util; print(importlib.util.find_spec('mamba_ssm')); print(importlib.util.find_spec('causal_conv1d')); print(importlib.util.find_spec('timm'))"
   ```

2. Confirm `torch.cuda.is_available()` and select one visible CUDA device. A
   successful import on CPU is not a PhysMamba verification.
3. Run a tiny, user-controlled CUDA Mamba block check only after imports are
   present. Use the public shape contract `(batch, length, dim) -> same shape`
   and do not download a pretrained language model.
4. Run the supervised model smoke probe with `--model PhysMamba --device
   cuda:0` only after the previous checks. The probe itself does not install or
   compile anything.
5. For a real run, use the model's `N,C,T,H,W` input, normally `NCDHW`, three
   channels, and a complete 128-frame clip. Keep `DEVICE`,
   `NUM_OF_GPU_TRAIN`, PyTorch build, and checkpoint provenance together in the
   run record.

## ABI and nvcc failures

Mamba packages contain compiled CUDA extensions. Common errors include
`undefined symbol`, `no kernel image is available`, C++ ABI mismatches, missing
`nvcc`, unsupported compute capability, and a wheel built for a different
PyTorch/CUDA pair. Diagnose them in this order:

- compare Python, PyTorch, CUDA runtime, driver, `causal-conv1d`, and
  `mamba-ssm` versions from the same environment;
- check the extension's wheel tag and the host's C++ ABI/compiler; do not mix a
  `cxx11abi` wheel with an incompatible torch build;
- if compiling, verify `nvcc --version`, host compiler support, and the GPU
  compute capability, then rebuild both extension dependencies against the
  selected torch—not just one of them;
- clear only user-approved build caches and reinstall in an isolated environment
  when necessary; never delete a working environment or checkpoint as a first
  response;
- retry the tiny CUDA block before starting a dataset run.

A missing `mamba_ssm` or `causal_conv1d` is an actionable required-backend
block, not permission to substitute CPU. A missing `timm` is also an import
block because PhysMamba imports its layers at module load time. Report the exact
exception and version tuple when handing off.

## Scope boundary

Do not copy the Mamba repository, CUDA C++ files, wheels, checkpoints, or its
language-model download/evaluation scripts into this skill. This reference
records only the public backend contract needed by PhysMamba. The generated
`model_smoke.py` catches absent optional imports and explains this requirement;
it never installs, downloads, compiles, writes, or launches training.
