# Document, PDF, RAG, speech, and chemistry workflows

This note maps the document-heavy workflows covered by this sub-skill. The same document can move through more than one path, but the handoff point matters:

- **Raw documents and PDFs** belong in knowledge cleaning or PDF VQA paths.
- **Already-cleaned local text** belongs in LightRAG retrieval.
- **Audio** belongs in speech transcription.
- **Chemical OCR text** belongs in chemistry extraction/evaluation.

## Route map

| Task family | Typical operators or serving classes | Input shape | Output shape | Keep out of scope |
| --- | --- | --- | --- | --- |
| Knowledge cleaning | `FileOrURLToMarkdownConverterAPI`, `FileOrURLToMarkdownConverterLocal`, `FileOrURLToMarkdownConverterFlash`, `KBCChunkGenerator`, `KBCTextCleaner`, `Text2MultiHopQAGenerator`, `QAExtractor` | `source` rows pointing at local files or URLs | markdown paths, cleaned chunks, QA pairs, Alpaca rows | generic serving-only routing and pure key validation |
| Agentic RAG and retrieval | `LightRAGServing`, `RetrievalGenerator`, `AgenticRAGAtomicTaskGenerator`, `AgenticRAGWidthQAGenerator`, `AgenticRAGDepthQAGenerator`, `AgenticRAGQAF1SampleEvaluator` | local text files, or QA-style records for generation/eval stages | retrieved documents, refined answers, quality metrics | raw PDF OCR and document conversion |
| PDF VQA | `PDF_Merger`, `MinerU2LLMInputOperator`, `ChunkedPromptedGenerator`, `LLMOutputParser`, `QA_Merger`, `VQAFormatter` | `input_pdf_paths` plus `name` | merged PDFs, converted layout JSON, extracted QA, `messages` and `images` | pure text QA or text-only filtering |
| Speech | `Speech2TextGenerator` | `raw_content` path or URL to audio | transcription text | PDF or OCR planning |
| Chemistry | `ExtractSmilesFromTextGenerator`, `SmilesEquivalenceDatasetEvaluator` | `text` plus optional abbreviation metadata | SMILES JSON and per-block scores | generic text QA and retrieval |

## Choose the path

- Use **knowledge cleaning** when the source is messy: PDF, HTML, crawled pages, or mixed document sources that need OCR or markdown normalization before QA or retrieval.
- Use **LightRAG retrieval** when the source is already local text and you want query-time retrieval, not OCR.
- Use **PDF VQA** when the target is multimodal question answering over PDF pages, figures, or merged document bundles.
- Use **speech** only for audio transcription; do not route it through document cleaning.
- Use **chemistry** for SMILES extraction or SMILES equivalence evaluation from OCR/text.

## Data-shape checkpoints

### Knowledge cleaning

- `source` should be one local path or URL per row.
- The converter writes a markdown path field such as `text_path`.
- Chunking usually follows with `raw_chunk`, then cleaning to `cleaned_chunk`, then QA generation to `QA_pairs`.
- `QAExtractor` can reshape QA pairs to Alpaca-style `instruction`, `input`, `output` rows.

### LightRAG retrieval

- `LightRAGServing.create(...)` expects a `document_list` of local text files.
- `load_documents` reads the file contents directly, so raw PDFs are not the right input.
- Retrieval operators typically read a question column and write a retrieved-docs column.

### PDF VQA

- `input_pdf_paths` may be a string or a list of strings, but the local paths should be PDFs.
- `name` is used to build per-sample output folders.
- The VQA path ends with ShareGPT-style `messages` and `images` columns.

### Speech

- `raw_content` is the source path or URL for the audio clip.
- The transcription operator writes one text column per row.

### Chemistry

- `text` is the main input used by the SMILES extractor.
- `abbreviations` and `golden_label` are common dataset fields, but only `text` is mandatory for extraction.
- The evaluator compares `golden_label` against `synth_smiles` and writes block scores.

## Minimal examples

### Knowledge cleaning chain

```python
from dataflow.serving import APILLMServing_request
from dataflow.operators.knowledge_cleaning import FileOrURLToMarkdownConverterAPI, KBCChunkGenerator, KBCTextCleaner
from dataflow.operators.core_text import Text2MultiHopQAGenerator

llm = APILLMServing_request(model_name="gpt-4o")
mineru = FileOrURLToMarkdownConverterAPI(intermediate_dir="./intermediate")
chunker = KBCChunkGenerator(chunk_size=512, tokenizer_name="Qwen/Qwen2.5-7B-Instruct")
cleaner = KBCTextCleaner(llm_serving=llm, lang="en")
qa = Text2MultiHopQAGenerator(llm_serving=llm, lang="en", num_q=5)
```

### LightRAG retrieval

```python
import asyncio
from dataflow.serving import LightRAGServing
from dataflow.operators.core_text import RetrievalGenerator

async def build_rag():
    rag = await LightRAGServing.create(
        api_url="https://api.openai.com/v1",
        document_list=["docs/a.txt", "docs/b.md"],
    )
    retriever = RetrievalGenerator(llm_serving=rag, system_prompt="Answer using the text only.")
    return rag, retriever
```

### Chemistry extraction and evaluation

```python
from dataflow.operators.chemistry import ExtractSmilesFromTextGenerator, SmilesEquivalenceDatasetEvaluator
```

## Safe stop conditions

- Stop if you only have raw PDFs but the target is LightRAG retrieval; clean the documents first.
- Stop if the task needs OCR or VLM behavior but only CPU-safe validation is available.
- Stop if the selected backend requires an API key, model path, or GPU and those are missing.
- Stop if the user wants pure text QA or filtering; route that to the text workflow family instead.
