# Evaluation and Benchmark Troubleshooting

## Missing data or images

**Symptoms**
- File-not-found errors for benchmark JSON, TSV, or image files.
- The benchmark script starts but cannot open referenced images.

**Recovery**
- Confirm the benchmark data directory layout before inference.
- Validate the question file and image folder with `scripts/validate_vqa_jsonl.py` or the relevant benchmark helper.
- Do not start the full inference job until the image folder is populated.

## Wrong `conv_mode`

**Symptoms**
- Answers look reasonable but are scored poorly.
- The benchmark output does not match the checkpoint family.

**Recovery**
- Use the model-family table from the chat sub-skill and the benchmark format reference.
- Re-run with the correct conversation mode before changing other settings.

## Merged chunks out of order or missing

**Symptoms**
- The merged JSONL is missing rows or has duplicate rows.
- Submission converters report missing questions.

**Recovery**
- Merge chunk files in numeric order.
- Confirm every chunk was produced.
- Validate the final merged JSONL before conversion.

## CUDA OOM during benchmark inference

**Symptoms**
- The benchmark worker crashes on large checkpoints.

**Recovery**
- Use fewer visible GPUs per job or a smaller checkpoint.
- Reduce concurrency or chunk size.
- Consider quantized loading only on supported Linux/CUDA hosts.

## Converter dependency issues

**Symptoms**
- Excel upload conversion fails.
- `pandas` or `openpyxl` is missing.

**Recovery**
- Install the missing optional dependency in the inspection environment or use a CPU-only validation step before conversion.

## Judge / OpenAI failures

**Symptoms**
- GPT-review scripts fail with authentication or rate-limit errors.

**Recovery**
- Confirm credentials and network access.
- Treat judge flows as optional external-service workflows.
- If no credentials are provided, stop at the answer-file stage and report the judge step as blocked.
