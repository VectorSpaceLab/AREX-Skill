# LangChain Integrations

The bundled LangChain scripts are optional demos for retrieval QA and summarization with Chinese-LLaMA-Alpaca-compatible local models. They require additional packages and user-provided model/embedding paths; they do not download assets safely by default.

## Retrieval QA

Script: [`scripts/langchain_qa.py`](../scripts/langchain_qa.py)

```bash
python scripts/langchain_qa.py \
  --file_path scripts/doc.txt \
  --embedding_path /path/or/model-id/for/embedding-model \
  --model_path /path/to/local_text_generation_model \
  --gpus 0 \
  --chain_type refine
```

Behavior:

- Loads one text file with `TextLoader`.
- Splits it with `RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)`.
- Builds FAISS vector search from `HuggingFaceEmbeddings`.
- Loads a Hugging Face text-generation pipeline through `HuggingFacePipeline.from_model_id`.
- Runs `RetrievalQA` with either `stuff` or `refine` prompts in Chinese Alpaca instruction format.

## Summarization

Script: [`scripts/langchain_sum.py`](../scripts/langchain_sum.py)

```bash
python scripts/langchain_sum.py \
  --file_path /path/to/input.txt \
  --model_path /path/to/local_text_generation_model \
  --gpus 0 \
  --chain_type refine
```

Behavior:

- Reads one text file.
- Splits into chunks of 600 characters with 100 overlap.
- Loads a HF text-generation pipeline.
- Runs LangChain summarization with `stuff` or `refine` prompts.

## Optional Dependencies

The minimum core repository requirements do not include all LangChain pieces. Depending on LangChain version, the examples may require packages such as:

- `langchain`
- `faiss-cpu` or another vectorstore backend
- `sentence-transformers` or another embedding backend
- `transformers`, `torch`, and model-specific tokenizer dependencies

Run `python scripts/langchain_qa.py --help` or `python scripts/langchain_sum.py --help` first. If the parser works but runtime imports fail, install the missing optional package only after confirming the user wants the LangChain workflow.

## Prompt Templates

Both scripts use Chinese Alpaca-style prompts beginning with:

```text
Below is an instruction that describes a task. Write a response that appropriately completes the request.
```

For base Chinese LLaMA continuation models, results may be weaker than with instruction-tuned Chinese Alpaca models.

## Safety and Scope

- Do not run these scripts against private documents without confirming data handling.
- Do not download embedding/model assets without user approval.
- Treat these demos as examples for app integration, not production RAG systems with robust chunking, citation, or evaluation.
- If the user asks only for local generation, use `hf-inference.md` instead of LangChain.
