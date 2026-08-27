# Paper Table 1 Reproduction

The `eval/` harness reproduces PixelRAG paper Table 1 one cell at a time. Full reproduction is not a lightweight smoke test.

## Roles and default ports

| Role | Default | Purpose |
| --- | --- | --- |
| Reader | `READER_URL=http://localhost:8010/v1` | vLLM OpenAI-compatible `Qwen/Qwen3.5-4B` reader, preferably H100 for paper match. |
| Base pixel | `BASE_PORT=30088` | `search_index_normed_v2`, multimodal pixel query. |
| LoRA pixel | `LORA_PORT=30096` | LoRA ViT checkpoint index. |
| Text | `TEXT_PORT=30097` | Trafilatura text index; text-only query mode. |
| News pixel | `NEWS_PORT=30095` | News image index for LiveVQA. |

`reproduce.sh <bench> <retrieval>` supports:

- `bench`: `nq`, `nqt`, `sqa`, `mms`, `evqa`, `livevqa`
- `retrieval`: `naive`, `traf`, `base`, `lora` (LiveVQA supports `naive` and `base`)

## Resource expectations

Paper-matching runs can require:

- H100/A100-class GPU for reader and GPU search serves.
- FAISS indexes from `StarTrail-org/pixelrag-faiss-indexes` (hundreds of GB).
- Tile corpus from `StarTrail-org/pixelrag-tiles` or Kiwix on-demand rendering.
- Reader model downloads.
- OpenAI key for LLM judge on NQ/NQ-Tables and VQA-style graders.
- Long wall time for full benchmark splits.

## Preflight contract

Before running, verify:

```bash
curl -s http://localhost:8010/v1/models
curl -s http://localhost:30088/status
curl -s http://localhost:30096/status
curl -s http://localhost:30097/status
curl -s http://localhost:30095/status
```

The shell script checks that the required serve is up and has at least the expected vector count. If this fails, it prints a launch hint and exits rather than silently producing an empty retrieval run.

## Public API quick smoke

A public PixelRAG endpoint can exercise the pipeline without self-hosting an index:

```bash
python run_bench.py --task nq --model Qwen/Qwen3.5-4B \
  --api-base "$READER_URL" --api-key dummy --no-think \
  --retrieval-top-k 5 --reader-top-k 3 --num-examples 20 --max-tokens 200 \
  --local-api --local-api-url http://api.pixelrag.ai:30001/search \
  --query-instruction "Retrieve images or text relevant to the user's query."
```

Caveat: public endpoint index/version may not match the paper's normed base/LoRA cells, so use it for plumbing, not score claims.

## Grading notes

- NQ/NQ-Tables paper numbers use an LLM judge, not strict exact match.
- SimpleQA uses the SimpleQA grader.
- MMSearch/EVQA/WorldVQA use VQA/WorldVQA-style judge logic.
- LiveVQA is MCQ exact-match in `run_livevqa.py`.

## Serve helper boundary

The repo's serve helper can download indexes and launch services. Treat it as a user-approved operational action because it consumes large disk, network, GPU, and long-running process resources.
