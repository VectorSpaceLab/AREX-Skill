# AIMET GenAILab workflows

GenAILab is AIMET's LLM/VLM scorecard harness. It reads YAML experiment documents, instantiates Hugging Face models, applies AIMET Torch or ONNX quantization recipes, evaluates metrics, writes profiling summaries, and optionally exports ONNX/encoding artifacts.

## Local command patterns

```bash
python -m GenAILab --framework torch --config config.yaml
python -m GenAILab --framework onnx --config config.yaml
python -m GenAILab --framework both --config config.yaml
```

Useful local flags:

```bash
python -m GenAILab --framework torch --config config.yaml \
  --export-dir GenAILab/artifacts/exports \
  --results-dir GenAILab/artifacts/results \
  --fp-cache-dir GenAILab/artifacts/cache/fp \
  --model-cache-dir GenAILab/artifacts/cache/model \
  --recipe-cache-dir GenAILab/artifacts/cache/recipe \
  --force-export -v
```

Run `scripts/genai_config_preflight.py config.yaml --framework torch --print-command` before long local or online runs. GenAILab's launcher forwards unknown local options to pytest, so pytest options from `GenAILab/conftest.py` such as `--recipe-cache-dir`, `--no-recipe-cache`, `--clear-recipe-cache`, and `--truncation-aware` are valid for local runs even when they are not first-class launcher arguments.

## Online command patterns

Online mode dispatches the `genai-scorecard.yaml` GitHub Actions workflow. It requires `gh` authentication and uses a branch/ref, not uncommitted local files.

```bash
python -m GenAILab --framework torch --config config.yaml --online
python -m GenAILab --framework onnx --config config.yaml --online --wait
python -m GenAILab --framework both --config config.yaml --download <run_id>
```

When `--wait` is used, the launcher watches the Actions run, downloads `test-data-<variant>-<run_id>` artifacts, stamps entries as online, merges JSON/CSV results, and prints a summary.

## YAML config essentials

A minimal document contains `model` and `metrics`:

```yaml
model:
  model_id: meta-llama/Llama-3.2-1B-Instruct
  sequence_length: 2048
  context_length: 4096
metrics:
  - name: TinyMMLU
```

Common quantized LLM document:

```yaml
model:
  model_id: meta-llama/Llama-3.2-1B-Instruct
  sequence_length: 2048
  context_length: 4096
precision:
  activations: int16
  kv_cache: int8
  embedding: int16
  lm_head: {qtype: int8, granularity: PCQ}
  blocks:
    default: {qtype: int4, granularity: PCQ}
recipe:
  backbone:
    - name: SeqMSE
      dataset: {name: Wikitext, split: train}
      num_iterations: 20
    - name: Calibration
      dataset: {name: Wikitext, split: train}
      num_iterations: 20
metrics:
  - name: PPL
  - name: TinyMMLU
export: true
run_group: lpbq-or-pcq-sweep
```

VLM documents may include `image_size`, `visual` precision, visual recipes, and multimodal metrics/datasets.

## Registered values snapshot

Recipes on both Torch and ONNX: `Calibration`, `SeqMSE`, `AdaScale`, `SpinQuant`, `RemoveQuantization`, `Skip`.

Datasets: `Wikitext`, `TinyMMLU`, `MMLU`, `MMMLU`, `MMLUPro`, `MMMU`, `C4`, `AOKVQA`, `Interleaved`.

Metrics: `PPL`, `TinyMMLU`, `MMLU`, `MMLU1000`, `MMMLU`, `MMLUKLDivergence`, `MMLUReverseKLDivergence`, `MMLUFlips`, `MMLUJSDivergence`, `MMMU`, `MMMUKLDivergence`, `MMMUReverseKLDivergence`, `MMMUFlips`, `MMMUJSDivergence`, `Interactive`, `Prompts`, `MultimodalPrompts`, `TrickyPrompts`, `AutogradedPrompts`, `AutogradedMultimodalPrompts`.

Adaptations: `SHA`, `SHA_Conv`, `FastExportable`, `AttentionMaskScale`, `AIHM`.

Special model types include `qwen2_5_vl`, `qwen3_vl`, `gemma3`, `gemma4`, `internvl_chat`, and `qwen3_5`; plain LLMs use the backend's default LLM class.

## Result summary entry point

Use the bundled dependency-light summary script when you only need to inspect profiling output or check metric-version comparability:

```bash
python scripts/genai_results_summary.py GenAILab/artifacts/results/profiling_data.json
```

It does not rerun metrics or import GenAILab. It reports model/config groupings, metric values, scoring versions, CUDA peak, elapsed time, and warnings for mixed metric versions.

## Output layout

Default output root:

```text
GenAILab/artifacts/
  results/
    profiling_data.json
    profiling_data.csv
  exports/
    <model-slug>_<timestamp>/
      config.yaml
      backbone/model_*.onnx
      backbone/model_*.encodings
      visual/model.onnx              # VLM only
      visual/model.encodings         # VLM only
      embedding.pth                  # VLM or model-specific export
  cache/
    fp/
    recipe/
    model/
```

Results include model configuration, precision, recipe steps, metric scores, GPU memory, elapsed time, environment metadata, and run metadata for online runs.

## Practical run planning

- Use `TinyMMLU`, a small `PPL.num_iterations`, and short config documents for smoke checks.
- Use explicit cache directories for expensive baselines or recipe chains.
- Use `--clear-fp-cache`, `--clear-model-cache`, or `--clear-recipe-cache` only when stale data is suspected; otherwise preserve caches.
- If a Torch run exports ONNX eval configs, a secondary ONNX evaluation may be run in CI-style workflows.
- Treat metric `scoring_version` as part of the result identity; do not compare mixed versions.
