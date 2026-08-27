# Serving and dependencies

This note classifies the optional document-heavy dependencies and the main serving classes that show up in this sub-skill.

## Dependency matrix

| Extra or package | What it unlocks | Heavy? | Notes |
| --- | --- | --- | --- |
| `rag` | LightRAG retrieval paths | medium | retrieval loads local text documents and needs the document list to be clean |
| `mineru` | MinerU document conversion | heavy | local MinerU can require extra setup and model files |
| `pdf2vqa` | PDF VQA document extraction path | heavy | used for VQA-oriented PDF extraction flows |
| `flash-mineru` | FlashMinerU acceleration | very heavy | GPU-backed MinerU acceleration path |
| `audio` | speech transcription helpers | medium | adds audio I/O support for speech workflows |
| `pdf2model` | PDF-to-model setup and training | very heavy | pulls in LlamaFactory, MinerU, vLLM, and related training pieces |
| `pdf2model-dataflex` | pdf2model with DataFlex support | very heavy | adds the extra training stack for the DataFlex backend |

## Serving class matrix

| Class | Role | Typical environment or credential | Important limits |
| --- | --- | --- | --- |
| `APILLMServing_request` | OpenAI-compatible chat/completion client | `DF_API_KEY` | no local service is started; missing key should stop the flow |
| `LightRAGServing` | document ingestion and retrieval over local text | `DF_API_KEY` plus `lightrag-hku` and a local embedding backend | it reads document files directly, so raw PDFs are the wrong input |
| `FileOrURLToMarkdownConverterAPI` | MinerU API conversion | `MINERU_API_KEY` | API-backed OCR only; do not claim offline behavior |
| `FileOrURLToMarkdownConverterLocal` | local MinerU conversion | local MinerU install and model configuration | usually heavy and not CPU-only |
| `FileOrURLToMarkdownConverterFlash` | FlashMinerU conversion | FlashMinerU plus GPU and model path | the fastest OCR path, but the most hardware-sensitive |
| `LocalVLMServing_vllm` | local vision-language inference | vLLM, a model path, and GPU capacity | suitable for VQA-style prompts, not for CPU-safe claims |
| `LocalModelLALMServing_vllm` | local audio-language inference | vLLM, audio extras, and GPU capacity | useful for speech transcription paths |
| `LocalModelLLMServing_vllm` / `LocalModelLLMServing_sglang` | local text-model serving | vLLM or SGLang plus model files | often used inside local document pipelines and training loops |

## Common environment variables

| Env var | Meaning |
| --- | --- |
| `DF_API_KEY` | default API key name used by API-backed serving classes and LightRAG |
| `MINERU_API_KEY` | MinerU API credential |
| `MINERU_MODEL_PATH` | local MinerU or FlashMinerU model location when you use a local backend |
| `MINERU_MODEL_SOURCE` | local MinerU source selector used by the local backend |
| `NPROC_PER_NODE` | optional pdf2model/DataFlex distributed launch tuning |
| `FORCE_TORCHRUN` | controls whether the DataFlex launcher uses `torchrun` |
| `MASTER_ADDR`, `MASTER_PORT`, `NNODES`, `NODE_RANK` | distributed launch controls for DataFlex-style training |

## Safe classification rules

- **CPU-safe**: input validation, manifest checking, CLI help inspection, and environment presence checks.
- **Network/API-backed**: `APILLMServing_request`, `LightRAGServing`, and the MinerU API converter.
- **GPU-backed**: FlashMinerU, local VLM serving, local audio-language serving, and pdf2model training.
- **Do not claim verification** of GPU, VLM, OCR, or distributed training behavior on a CPU-only run.

## Practical guidance

- Use API-backed OCR or retrieval only when the credential is present and the user accepts external calls.
- Use local OCR or VLM paths only when the model files and hardware are ready.
- Use the validator script before launching any heavy backend so missing env vars fail fast.
- If the task is plain text QA or filtering, hand it to the text workflow family instead of choosing a document backend.
