# Research And Benchmark Notes

RAG-Retrieval includes research and benchmark examples in addition to core package and training workflows. These are valuable evidence for capability planning, but they should usually be reference-only in an agent skill because they are dependency-heavy and can require network, API credentials, model downloads, or long runtimes.

## MyopicTrap Positional-Bias Experiments

The MyopicTrap examples study positional bias across an information-retrieval pipeline with BM25, dense embeddings, ColBERT-style scoring, and rerankers on position-aware benchmarks.

Use this evidence when a user asks about:

- Evaluating positional bias in retrieval or reranking.
- Comparing BM25, embedding, ColBERT, and reranker stages.
- Designing an experiment around `SQuAD-PosQ` or `FineWeb-PosQ`-style data.
- Understanding why benchmark scripts are not safe default smoke tests.

Do not run these scripts as routine verification because they can require external datasets, optional packages such as FAISS/BM25/FlagEmbedding, commercial embedding API credentials, and substantial compute.

## Synthetic Embedding Data Generation

The synthetic data example uses a FlashRAG-style configuration and generator/retriever stack to create training signals. Treat it as optional data-generation evidence for embedding workflows.

Use this evidence when a user asks for:

- Generating synthetic training data before embedding distillation.
- Understanding how LLM probabilities or generated answers can become supervision signals.
- Planning a workflow that depends on FlashRAG, retrieval corpora, and generator model access.

Do not bundle or run the original script as a default helper because it depends on external packages, model/data availability, and likely network access.

## Distillation Example Scripts

The Stella embedding distillation and LLM-to-BERT reranker examples show how teacher models can create supervision for smaller models. The generated sub-skills distill those ideas into safer validation and planning helpers:

- Embedding teacher-array merge and memmap checks live in `sub-skills/embedding-training/`.
- Reranker teacher scoring and pointwise conversion planning lives in `sub-skills/reranker-training/`.

Run the heavy teacher-generation scripts only when the user confirms model checkpoints, data paths, device capacity, and runtime expectations.

## Verification Guidance

When using these examples as verification evidence:

1. Prefer static inspection or tiny fixture validation first.
2. Record network, credential, GPU, and runtime requirements before execution.
3. Skip benchmark-scale runs unless the user explicitly asks for them.
4. If a benchmark is run, compare its needs against the generated skill routes and record the result under review artifacts, not inside runtime skill content.
