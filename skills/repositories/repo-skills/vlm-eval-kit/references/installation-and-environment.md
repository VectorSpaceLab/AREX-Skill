# Installation and environment guide

## Package identity

- Public repo/project: VLMEvalKit
- Python distribution/import: `vlmeval`
- Console utility entry point: `vlmutil`
- Main evaluation runner in source checkouts: `run.py`

The package metadata declares Python `>=3.7`, but modern VLMEvalKit dependencies are easier to satisfy on Python 3.10 or 3.11. Avoid assuming Python 3.13 support for all compiled ML/media dependencies unless the current environment verifies it.

## Install modes

### Editable source install

Use this when contributing, adding benchmarks/models, or running the repository `run.py` entry point:

```bash
git clone https://github.com/open-compass/VLMEvalKit.git
cd VLMEvalKit
python -m pip install -e .
```

For a minimal inspection environment, installing the full `requirements.txt` may be heavy but matches the package metadata. If a task only needs a narrow API or helper, install missing dependencies incrementally and keep skipped optional capabilities explicit.

### Runtime dependencies

`requirements.txt` is broad because VLMEvalKit spans local VLMs, API providers, video decoding, OCR/document/math metrics, Gradio tools, dataset conversions, Torch/TorchVision, Transformers, and judge helpers. Expect compiled packages and large wheels such as `torch`, `torchvision`, `opencv-python`, `decord`, `scikit-image`, and model libraries.

Known dependency notes from the verified baseline:

- `rouge_score` is imported by the MMLongBench metrics path although the dependency file lists `rouge`; install `rouge-score` if `from rouge_score import rouge_scorer` fails.
- Some `decord` wheels may import but still make `pip check` report platform issues. A conda-forge `decord` package can resolve this in conda environments.
- Recent `opencv-python` releases may require NumPy 2, while some test/import patterns are steadier with NumPy 1.26 + pandas 2.2. Pin only when a concrete failure requires it.

## Credentials and services

API models and judge models need credentials or running services. Common variables and flags include:

| Surface | Configuration |
| --- | --- |
| OpenAI/GPT judge or API models | `OPENAI_API_KEY`, `OPENAI_API_BASE`, `--judge`, `--judge-base-url`, `--judge-key` |
| LiteLLM provider | `LITELLM_API_KEY`, `LITELLM_API_BASE`, model strings like `anthropic/...` or `vertex_ai/...` |
| Local/OpenAI-compatible service | `run.py --base-url http://host:port/v1 --key ...` |
| LMDeploy judge/service | Deploy an OpenAI-compatible server and point `OPENAI_API_BASE`, `LOCAL_LLM`, or `--base-url` appropriately |
| Evaluation proxy | `EVAL_PROXY` is applied during evaluation judge calls |
| Repository `.env` file | Optional key file loaded by `vlmeval.load_env`; a missing `.env` log is non-fatal |

Never bake secrets into configs, logs, or generated scripts.

## Data and cache roots

VLMEvalKit uses cache roots for benchmark TSVs, images, videos, and auxiliary models.

| Variable | Meaning |
| --- | --- |
| `LMUData` | Root for TSVs, images, videos, downloaded files, and local unsupported datasets. Defaults to `~/LMUData` when unset. |
| `FORCE_LOCAL` | Forces localization/regeneration of large TSV image-path forms in several dataset loaders. |
| `VLMEVALKIT_USE_MODELSCOPE` | Allows supported video/data downloads from ModelScope when set to `1` or `True`. |
| `LONGDOCURL_TSV_ROOT`, `LONGDOCURL_IMAGE_ROOT` | Override LongDocURL TSV/image locations. |
| `MMLB_TSV_ROOT` | Override MMLongBench TSV root. |
| `MEMLENS_TSV_ROOT` | Override MemLens TSV root. |

Dataset construction can download large TSVs, image archives, videos, or metric models. Check disk/network expectations before running a new dataset.

## Output-format variables

| Variable | Values | Effect |
| --- | --- | --- |
| `PRED_FORMAT` | `xlsx` default, `tsv`, `json` | Prediction file suffix. Use `PRED_FORMAT=tsv` for long responses that may exceed spreadsheet cell limits. |
| `EVAL_FORMAT` | `csv` default, `json` | Evaluation metric output suffix. |
| `SPLIT_THINK` | truthy string | Splits `<think>...</think>` content into a `thinking` column when supported by inference output handling. |
| `SKIP_ERR` | `1` | Converts runtime model errors into failure strings rather than stopping local inference loops. |
| `MMEVAL_ROOT` | directory | Overrides `--work-dir` in `run.py`. |
| `FWD_API` | `1` | Forces configured API model entries through `GPT4V` wrapper behavior. |

## Hardware/backends

CPU checks can verify imports, CLI help, converters, config parsing, and API wrapper construction. They do **not** verify local VLM generation, video throughput, CUDA memory behavior, or vLLM/LMDeploy performance.

For local VLM inference:

- Select model-specific `transformers`, `torchvision`, and optional `flash-attn` versions from VLMEvalKit compatibility notes.
- Use `CUDA_VISIBLE_DEVICES` to control visible GPUs.
- With plain `python run.py`, one model instance may use all visible GPUs depending on the wrapper.
- With `torchrun`, VLMEvalKit splits visible GPUs among processes for supported non-vLLM paths.
- vLLM-backed models are documented as incompatible with the torchrun splitting pattern; use a plain Python launch for those paths.

## Safe environment check

Run the bundled checker:

```bash
python scripts/check_vlmeval_install.py
```

Run it from this generated skill directory or pass the script path directly. It performs import/signature checks and optional `vlmutil` discovery without downloading datasets or calling providers.
