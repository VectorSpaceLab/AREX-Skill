# Installation and Configuration

## Purpose

Read this reference when choosing between HanLP install variants, configuring model caches, using mirrors, selecting CPU/GPU devices, or proving that an environment can import the expected packages.

## Package Surfaces

| Surface | Install | Import | When to choose |
| --- | --- | --- | --- |
| RESTful Python client | `python -m pip install hanlp-restful` | `from hanlp_restful import HanLPClient` | Lightweight applications that can call a HanLP-compatible service. |
| Native Python package | `python -m pip install hanlp` | `import hanlp` | Local pretrained models, pipeline composition, training/fine-tuning, or offline/model-cache workflows. |
| Common structures | Installed with HanLP packages | `from hanlp_common.document import Document` | Output parsing, JSON conversion, pretty printing, CoNLL conversion. |
| Trie utilities | Installed with native HanLP | `from hanlp_trie import Trie, TrieDict` | Custom dictionaries, deterministic longest-prefix matching, gazetteers. |

HanLP metadata for the inspected version declared base native dependencies including `termcolor`, `pynvml`, `toposort==1.5`, `transformers>=4.1.1`, `sentencepiece>=0.1.91`, `torch>=1.6.0`, `hanlp-common>=0.0.22`, `hanlp-trie>=0.0.4`, and `hanlp-downloader`.

## Optional Extras

Install optional extras only when the user's workflow requires them:

```bash
python -m pip install 'hanlp[amr]'   # AMR dependencies such as penman/perin-parser/networkx
python -m pip install 'hanlp[tf]'    # TensorFlow and fastText paths
python -m pip install 'hanlp[full]'  # all optional groups
```

Do not install `full` just to inspect ordinary RESTful, `Document`, trie, pipeline, or CPU native guidance.

## Minimal Import Checks

```bash
python -c "import hanlp; from hanlp_common.document import Document; from hanlp_trie import Trie; print(hanlp.__version__, Document, Trie)"
```

For RESTful-only work:

```bash
python -c "from hanlp_restful import HanLPClient; print(HanLPClient('https://hanlp.hankcs.com/api', auth=None, language='zh'))"
```

The RESTful check above only constructs the client; it does not prove network access or service quota.

## Model Cache and Downloads

Native `hanlp.load(identifier_or_url, verbose=None, **kwargs)` resolves predefined identifiers through `hanlp.pretrained.ALL`, then loads a model archive or local model directory. If a resource is remote, HanLP can download it into `HANLP_HOME`.

- Set `HANLP_HOME` to redirect model archives and extracted resources.
- Set `HANLP_URL` to use a compatible mirror for HanLP-hosted model URLs.
- Set `TRANSFORMERS_OFFLINE=1` only when the needed Hugging Face files are already cached.
- Set `HANLP_VERBOSE=0` to reduce progress output.

## CPU, GPU, and Device Selection

- Use CPU-only mode when the task is a no-download smoke check, output handling, trie/rules, RESTful payload construction, or small CPU inference.
- Use a GPU-enabled PyTorch/TensorFlow stack when the task explicitly needs GPU performance, large local models, or training.
- `CUDA_VISIBLE_DEVICES` limits visible NVIDIA devices.
- `hanlp.load(..., devices=...)` passes device control to component loading. Common patterns include `devices=-1` for CPU and `devices=0` or a list for GPU placement when supported by the component.
- Do not claim GPU verification from a CPU-only framework import.

## Editable Checkout Install for Maintainers

When maintaining a checkout, install plugins before the main package so local imports resolve consistently:

```bash
python -m pip install -e plugins/hanlp_trie
python -m pip install -e plugins/hanlp_common
python -m pip install -e plugins/hanlp_restful
python -m pip install -e .
```

Then run focused tests for the edited area instead of starting model-download or training workflows immediately.

## Safe Diagnostic Helper

Run the bundled root helper from this skill directory:

```bash
python scripts/check_hanlp_environment.py --json
```

It checks installed distributions, imports, registered pretrained identifiers, environment variables, and CPU/CUDA visibility without downloading models or contacting a RESTful service.
