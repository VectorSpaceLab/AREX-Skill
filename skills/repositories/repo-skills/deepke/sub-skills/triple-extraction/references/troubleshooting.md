# Triple-extraction troubleshooting

Start with a safe diagnostic:

```bash
python scripts/check_triple_env.py --task <prgc|pure|asp|mt5|cnschema>
```

Add `--json` for machine-readable output and `--strict` only when you want missing required imports/paths or absent CUDA to return nonzero.

## Dependency/version failures

| Symptom | Likely cause | Fix direction |
| --- | --- | --- |
| `ModuleNotFoundError: deepke.triple_extraction...` | DeepKE package is not installed or the selected module is unavailable in the installed version | Install the target DeepKE version in the active environment and re-run the diagnostic. |
| AllenNLP or `overrides` import/version errors in PURE | PURE depends on an older AllenNLP/Transformers/PyTorch compatibility stack | Use an isolated PURE environment matching the source README or adapt the code deliberately; do not mix with unrelated LLM dependencies. |
| `ImportError` from `huggingface_hub` or `transformers` | Mismatched Transformers/Hugging Face Hub versions | Pin a compatible pair for the selected workflow and verify imports before training. |
| ASP `apex` import/build failure | NVIDIA Apex was not built for the active CUDA/PyTorch combination | Treat ASP as blocked until a CUDA-capable environment can build/import Apex; CPU import checks do not prove ASP readiness. |
| DeepSpeed launch errors for MT5 | Missing DeepSpeed, wrong CUDA visibility, incompatible GPU count, or bad config JSON | Validate DeepSpeed install and GPU count separately; reduce batch size or adjust ZeRO/bf16 settings only after confirming hardware. |

## CUDA and hardware failures

- PRGC and PURE can sometimes be inspected on CPU, but meaningful training/prediction with PLMs usually needs GPU memory.
- ASP's documented stack is CUDA/Apex-oriented. Mark ASP runtime as a required-backend block if the user specifically requests a real ASP run and no compatible GPU stack is available.
- MT5/DeepSpeed training was documented on multiple 24GB GPUs. A CPU-only environment can validate file conversion but not training readiness.
- If `torch.cuda.is_available()` is false, do not silently convert a GPU-native request into a CPU run. Ask to narrow scope, provide hardware, or accept a planning-only result.

## Dataset and label failures

| Symptom | Checks |
| --- | --- |
| Training crashes with missing file | Confirm exact filenames: PRGC commonly uses `val_triples.json`, PURE/ASP commonly use `dev.json`, and MT5 source docs use `valid.json` as prediction input. |
| Unknown relation id or label mismatch | Compare every relation label in data/predictions against `rel2id.json` or the workflow's relation constants. |
| Staged PURE relation accuracy is unexpectedly poor | Evaluate entity-stage predictions first; relation errors may be caused by wrong/missing entity spans. |
| cnSchema output misses expected facts | Verify the facts are actually in the cnSchema inventory; custom relations usually need custom training. |
| MT5 converter writes empty `kg` arrays | Inspect raw `output`: it may lack parenthesized triples, use unsupported delimiters, include commas inside entity names, or emit explanatory text. |

## MT5 conversion pitfalls

Use the bundled converter instead of copying the source helper directly:

```bash
python scripts/convert_mt5_predictions.py --src-path input.jsonl --pred-path test_preds.json --tgt-path result.jsonl --strict-length
```

If the converter fails:

- `missing prediction field`: use `--prediction-field <name>` if predictions do not store text under `output`.
- `row count mismatch`: remove `--strict-length` for intentional partial conversion, or regenerate predictions for the full input file.
- Empty `kg` with apparently valid triples: check whether the model emitted full-width Chinese commas or nested parentheses; choose `--allow-chinese-comma` only if entity/relation names do not themselves contain that punctuation.
- Bad JSON: verify the file is JSONL (one JSON object per line), not a JSON array. Convert arrays to JSONL before using line-oriented DeepKE helpers.

## Config mutation and reproducibility

- Native DeepKE examples often rely on relative working directories and mutable configs. Run them from a deliberate experiment directory and preserve the resolved config.
- Do not edit a shared config in place without recording the diff; create a copy for experiments when possible.
- Do not assume a downloaded checkpoint matches the data/schema; record both the checkpoint source and relation inventory.
- For MT5/DeepSpeed, keep `output_dir`, `logging_dir`, and prediction result paths unique to avoid overwriting earlier runs.

## When to stop and report a block

Report a block rather than retrying indefinitely when:

- A requested ASP/Apex or MT5/DeepSpeed run needs CUDA but no compatible GPU stack is available.
- Required datasets or checkpoints are absent and cannot be downloaded under the current network/budget constraints.
- The user's prediction format cannot be parsed without a task-specific schema decision.
- A dependency stack conflict would break an existing environment and the user has not approved a new isolated environment.
