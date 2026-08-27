# PyOD Installation and Optional Extras

Read this for package-level setup guidance before selecting a sub-skill. The
exact environment used to build this skill is private and intentionally omitted;
use public PyOD install commands for new work.

## Core install

```bash
pip install pyod
# or, from conda-forge:
conda install -c conda-forge pyod
```

Core PyOD requires Python 3.9 or newer and installs the base runtime stack:
`joblib`, `matplotlib`, `numpy`, `numba`, `scipy`, and `scikit-learn`.

Verify the install:

```bash
python - <<'PY'
import pyod
from pyod.models.iforest import IForest
from pyod.utils.ad_engine import ADEngine
print(pyod.__version__)
print(IForest)
print(ADEngine().list_detectors(data_type="tabular")[:2])
PY
pyod info
```

## Optional extras

Install only the extras required by the selected workflow. Quote extras in
shells that expand brackets.

| Extra | Enables | Notes |
|---|---|---|
| `torch` | PyTorch-backed detectors such as AutoEncoder, VAE, DeepSVDD, LUNAR, some time-series/audio paths | Install a custom CUDA/ROCm/MPS torch build first if accelerator support matters. |
| `graph` | PyTorch Geometric graph anomaly detectors | Pulls torch and `torch_geometric`; verify PyG imports before graph tasks. |
| `embedding` | SentenceTransformer text embeddings | May download model weights unless a local model is used. |
| `openai` | OpenAI embedding encoders | Requires API credentials for real calls. |
| `huggingface` | HuggingFace/transformers text-image encoders | May download models and needs torch/Pillow. |
| `audio` | librosa/soundfile audio feature extraction | `AudioAE` also needs torch. |
| `mcp` | `pyod mcp serve` server runtime | `pyod info` is safe without this extra and reports it missing. |
| `suod` | SUOD acceleration | Use for large heterogeneous detector ensembles. |
| `xgboost` | XGBOD supervised detector | Use when labels are available and supervised OD is desired. |
| `combo` | score-combination functions and related ensemble helpers | Needed by `pyod.models.combination`. |
| `pythresh` | data-driven thresholding objects | Needed by `pyod.models.thresholds` factories. |
| `all` | all optional extras | Large; avoid as a default setup path. |

A common mistake is `pyod[pytorch]`; the valid torch extra is `pyod[torch]`.

## Sub-skill routing after install

- Direct `fit`/`predict` detector workflows -> `classic-detectors`.
- Automated selection, `ADEngine`, CLI, od-expert install, MCP ->
  `automated-lifecycle`.
- Time series, graph, embedding/text/image/audio, neural and backend probes ->
  `specialized-modalities`.
- Persistence, thresholding, score combination, SUOD/XGBOD operations ->
  `model-operations`.
- Editing the PyOD checkout, tests, docs, packaged skills -> `repo-maintenance`.
