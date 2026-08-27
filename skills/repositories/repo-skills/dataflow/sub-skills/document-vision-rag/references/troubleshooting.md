# Troubleshooting

This note focuses on failure modes that matter for document, PDF, VQA, retrieval, speech, and chemistry workflows.

## Symptom table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| No documents are found | wrong directory, empty directory, or unsupported suffixes | point the validator at the actual files; for PDF-only flows, add `--expect-pdf` |
| Raw PDFs fail in a retrieval flow | LightRAG reads local text files directly | clean the PDF first and feed the extracted markdown or text into retrieval |
| `source` is missing | KBC manifest shape is wrong | add a `source` column with one document source per row |
| `input_pdf_paths` or `name` is missing | PDF VQA manifest shape is wrong | use the PDF VQA schema and keep local PDFs only |
| `messages` or `images` is missing | VQA training data is not ShareGPT-shaped | make sure the data is converted to `messages` and `images` before training |
| `raw_content` is missing | speech transcription manifest shape is wrong | add the audio path or URL column |
| `text` is missing | chemistry manifest shape is wrong | provide OCR or extracted text for SMILES extraction |
| `DF_API_KEY` is missing | API-backed retrieval or chat path is selected | set the key or switch to a local-only path |
| `MINERU_API_KEY` is missing | MinerU API conversion is selected | set the key or switch to a local MinerU backend |
| `flash_mineru` import fails or GPU setup is missing | FlashMinerU backend is selected without the required stack | install the extra, provide a model path, and stop if the hardware is not available |
| `vqa only supports base` | incompatible `pdf2model` backend choice | rerun with `--train-backend base` |
| `dataflex-*` is rejected for VQA | DataFlex is only valid for KBC | switch to `qa=kbc` or use the base backend |
| no adapter files are found | training did not finish or the wrong save folder was chosen | rerun training and point chat at the adapter directory that contains adapter files |
| JSON/JSONL columns fail validation | manifest schema mismatch | fix the record keys and rerun the validator before launching the backend |

## Stop conditions

- Stop immediately when a required credential, model path, or GPU is missing.
- Stop when a local path does not exist instead of trying to continue with a guessed fallback.
- Stop when a PDF is used where a local text retrieval flow expects markdown or plain text.
- Stop when the requested `pdf2model` backend does not match the chosen `qa` mode.
- Stop when the input validator reports column or suffix errors; do not launch a heavy backend until that is clean.

## Fast recovery order

1. Run `scripts/check_document_workflow_inputs.py` with the right profile.
2. Fix missing paths, suffixes, or JSON/JSONL columns.
3. Add the required env vars for the chosen backend.
4. Re-check whether the selected backend is API, local OCR, GPU, or training heavy.
5. Only then launch the document or training command.
