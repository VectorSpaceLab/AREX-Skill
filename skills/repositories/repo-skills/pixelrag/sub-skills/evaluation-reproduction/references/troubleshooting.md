# Evaluation Troubleshooting

## Preflight says reader is wrong

`reproduce.sh` expects `Qwen/Qwen3.5-4B` at the reader endpoint for paper Table 1. Check:

```bash
curl -s ${READER_URL%/v1}/v1/models
```

If using a different reader intentionally, record it and do not compare to paper numbers directly.

## Search serve is down or wrong index

Call `/status` on the expected port and compare `total_vectors`. A wrong index can run successfully but produce non-paper scores. Use the preflight helper with expected minimum vector counts.

## Score is near zero

Common causes:

- Retrieval request timed out and cached an empty result.
- Reader endpoint returned errors or a different model.
- OpenAI judge key/base URL is missing or region-incompatible.
- Strict exact match was used for NQ/NQ-Tables instead of LLM judge.
- Query instruction or retrieval mode does not match the target condition.
- `TILES_DIR` points at missing tiles and the serve did not return base64 images.

## On-demand rendering is slow

Set a larger retrieval timeout, for example:

```bash
export PIXELRAG_RETRIEVAL_TIMEOUT=7200
```

Expect first queries to be slow when the serve must render retrieved Kiwix pages on demand.

## Public API smoke does not match published results

The public API endpoint may serve a different index from the paper's normed base/LoRA indexes. Use it to validate request plumbing and grader wiring only.

## Grader silently returns zero

Some grader paths swallow provider errors and record zero. Verify the key before launching a long run:

- Check `OPENAI_API_KEY` is set.
- If the provider asks for a regional base URL, set `OPENAI_BASE_URL` accordingly.
- Run a tiny `NUM=1` or `--num-examples 1` job before full evaluation.

## Query image files escape or fail path checks

Use the eval library's safe-stem behavior; do not interpolate raw example IDs into filenames. If adapting the harness, preserve the sanitized filename pattern and output-directory containment checks.

## LiveVQA mode confusion

LiveVQA uses `run_livevqa.py`, the news pixel serve, and MCQ exact-match. It does not support every retrieval mode that the other benchmark cells support.
