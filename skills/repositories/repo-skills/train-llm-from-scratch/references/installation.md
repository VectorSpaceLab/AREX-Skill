# Installation and Backend Reference

## Purpose

Read this when setting up a user environment, deciding which optional extras are
needed, or proving that the package imports and the selected backend is usable.
This reference is public runtime guidance; it intentionally omits private
inspection-prefix details.

## Package shape

The distribution name is `train-llm-from-scratch` and version evidence for this
skill is `0.1.0`. The installable import roots are:

- `config` — legacy and modern config objects/loaders.
- `data_loader` — HDF5, packed SFT, preference, and prompt iterators.
- `src` — model and post-training implementation.
- `ui` — Streamlit control panel.

The project requires Python `>=3.9`. For ML dependencies and CUDA wheels, prefer
Python 3.10 or 3.11 unless the user's torch stack explicitly supports another
version.

## Optional extras

| Extra | Installs | Use when |
|---|---|---|
| base editable install | `torch`, `numpy`, `h5py`, `tqdm`, `tiktoken`, `zstandard`, `requests` | Model imports, HDF5/tokenization helpers, core scripts, smoke tests. |
| `[train]` | `datasets`, `wandb` | Hugging Face dataset preparation, SFT/RM/DPO/PPO/GRPO data flows, optional W&B logging. |
| `[ui]` | `streamlit`, `pandas`, `altair` | Control panel, forms, charts, UI job management. |
| `[docs]` | MkDocs Material stack | Building the documentation site only. |
| `[all]` | all extras | Development convenience; avoid for minimal inspection unless all surfaces are selected. |

Avoid installing broad requirements files blindly. The repo has requirements
examples for particular CUDA/PyTorch eras, but a user should install the torch
wheel that matches their GPU/driver first and then install the package/extras
needed for the selected workflow.

## Backend expectations

- Full training workflows are CUDA-oriented in the default configs (`device:
  "cuda"`, `amp_dtype: "bf16"`) and public docs. A modern NVIDIA GPU with a
  compatible PyTorch CUDA build is the normal target.
- CPU smoke configs under `configs/smoke/` are valid for quick parser/config and
  algorithm checks. They are not proof of full CUDA/bf16/DDP training.
- The implementation is pure PyTorch: no custom CUDA extensions are required for
  import. This reduces ABI risk, but large model runs still depend on torch,
  driver, memory, and process-launch compatibility.

## Safe setup sequence

1. Create or choose an isolated Python environment. Do not modify a shared/base
   environment unless the user explicitly accepts that risk.
2. Install a PyTorch build matching the target backend.
3. Install the repo in editable mode with only selected extras, for example:

```bash
pip install -e .
pip install -e ".[train,ui]"
```

4. Run the root environment checker:

```bash
python scripts/check_environment.py --backend auto
```

5. For CUDA claims, ensure the checker reports CUDA available, a device name,
   and a successful tiny tensor/model operation.
6. For stage-specific data, validate files with the data-preparation sub-skill
   before launching training.

## Minimal import/API smoke

```bash
python - <<'PY'
import torch
from src.models.transformer import Transformer
from src.post_training.chat_template import encode_chat, EOT_ID
m = Transformer(n_head=2, n_embed=16, context_length=8, vocab_size=64, N_BLOCKS=1)
ids, mask = encode_chat([
    {"role": "user", "content": "What is 2+2?"},
    {"role": "assistant", "content": "<answer>4</answer>"},
])
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("chat", len(ids), len(mask), sum(mask), ids[-1] == EOT_ID)
print("params", sum(p.numel() for p in m.parameters()))
PY
```

## Selected native verification candidates

After the skill graph is integrated and the user's environment is ready, the
safe native checks are:

```bash
PYTHONPATH=. python tests/test_post_training_smoke.py
PYTHONPATH=. python tests/test_rl_math.py
PYTHONPATH=. python tests/test_checkpoint_resume.py
```

CUDA-specific native checks, when the user has suitable hardware and runtime
budget, include a tiny GRPO live optimization proof. Real-data GPU scripts and
data/eval verification require prepared external datasets and should be treated
as optional or data-dependent, not as basic import checks.
