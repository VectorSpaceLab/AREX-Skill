# Installation and Environment

Graphormer is consumed as a fairseq user-dir package. The validated historical
stack for this repository is the older Graphormer / fairseq / PyTorch family,
not a modern from-scratch rebuild.

## Recommended starting point

- Python 3.9 is the safest default for this checkout.
- Use an isolated environment manager such as conda, micromamba, uv, or venv.
- Install a Graphormer-compatible PyTorch build, the fairseq user-dir stack,
  and the graph backends used by the selected workflow.
- Make sure the `fairseq` submodule or equivalent fairseq package is available
  before trying to import Graphormer registries.

## Validated historical stack

The repository documentation and installed-package inspection both point to the
following compatibility family:

- `torch==1.9.1+cu111`
- `torchaudio==0.9.1`
- `lmdb`
- `torch-scatter==2.0.9`
- `torch-sparse==0.6.12`
- `torch-geometric==1.7.2`
- `tensorboardX==2.4.1`
- `ogb==1.3.2`
- `rdkit-pypi==2021.9.3`
- `dgl==0.7.2`
- `cffi`
- `Cython==0.29.37`
- `protobuf==3.20.3`
- `googledrivedownloader==0.4`
- `hydra-core==1.0.7`
- `omegaconf==2.0.6`
- `sacrebleu` and `bitarray` in the older fairseq-compatible range

If your environment manager or package mirror prefers newer tooling, keep the
older Graphormer stack isolated from other projects so you can preserve the
exact compatibility family for inspection.

## Example setup flow

```bash
conda create --prefix <graphormer-env> python=3.9 pip
conda run --prefix <graphormer-env> python -m pip install 'pip<24.1'
conda run --prefix <graphormer-env> python -m pip install 'torch==1.9.1+cu111' torchaudio -f https://download.pytorch.org/whl/cu111/torch_stable.html
conda run --prefix <graphormer-env> python -m pip install lmdb 'torch-scatter==2.0.9' 'torch-sparse==0.6.12' 'torch-geometric==1.7.2' 'tensorboardX==2.4.1' 'ogb==1.3.2' 'rdkit-pypi==2021.9.3' 'dgl==0.7.2' -f https://data.dgl.ai/wheels/repo.html
conda run --prefix <graphormer-env> python -m pip install cffi 'Cython==0.29.37' 'protobuf==3.20.3' 'googledrivedownloader==0.4' 'hydra-core==1.0.7' 'omegaconf==2.0.6'
```

If you are starting from a source checkout that includes a fairseq submodule,
initialize it before editable installation. If the fairseq build tries to
compile extensions and you only need import and registry inspection, use the
READTHEDOCS-style editable path documented in troubleshooting.

## Minimal smoke check

After installation, run the bundled checker and confirm the expected registries:

```bash
python scripts/check_graphormer_environment.py --user-dir <graphormer-package-dir> --format text
```

Add these flags when needed:

- `--require-complete` to confirm the expected Graphormer registries are present
- `--require-cuda` to add a tiny CUDA allocation smoke check on GPU hardware

## What this environment should prove

- Graphormer can be imported as a fairseq user-dir plugin.
- The expected models, tasks, criterions, and architectures are visible in the
  fairseq registries.
- CUDA is available when the selected workflow needs it.
- The environment is isolated from unrelated projects so old dependency pins do
  not leak into other work.

## What this environment does not prove

- It does not execute training, evaluation, or DiG runs.
- It does not download datasets or checkpoints.
- It does not guarantee that long-running distributed jobs or optional research
  workflows will finish; those are handled later by workflow-specific review and
  verification.
