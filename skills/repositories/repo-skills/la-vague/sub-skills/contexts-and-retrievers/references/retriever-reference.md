# Retriever reference

LaVague uses retrievers inside the NavigationEngine/ActionEngine to select relevant HTML nodes before asking an LLM to generate browser automation code. Retriever choice affects both cost and success: too little context loses target elements; too much context confuses the code generator.

## Default behavior

If `ActionEngine(..., retriever=None)` is used, LaVague builds the default retriever with the engine's embedding model:

```python
RetrieversPipeline(
    InteractiveXPathRetriever(driver),
    FromXPathNodesExpansionRetriever(),
    SemanticRetriever(embedding=embedding),
)
```

`ActionEngine.from_context(context, driver=driver)` passes `context.embedding` into this default pipeline. Therefore, provider-context embedding defaults matter even when you did not pass `retriever=` explicitly.

## Core retrievers

| Retriever | Constructor | What it does | When to use |
| --- | --- | --- | --- |
| `InteractiveXPathRetriever` | `InteractiveXPathRetriever(driver)` | Reads driver possible interactions and annotates matching HTML with `xpath` attributes, including iframe traversal when possible. | Useful first stage for action generation because LaVague-generated Selenium needs authorized XPaths. |
| `FromXPathNodesExpansionRetriever` | `FromXPathNodesExpansionRetriever(chunk_size=750)` | Expands xpathed interactive elements to surrounding HTML context, merging overlapping chunks. | Good middle stage after XPath annotation when raw element labels are too narrow. |
| `SemanticRetriever` | `SemanticRetriever(embedding, top_k=10, xpathed_only=True)` | Splits HTML, filters for xpathed chunks when possible, embeds chunks, and returns top semantic matches. | Default final stage. Requires a working embedding object and therefore often a provider key. |
| `SyntaxicRetriever` | `SyntaxicRetriever(top_k=5, xpathed_only=True)` | Uses BM25/syntaxic retrieval over split HTML and can operate without provider embeddings. | Safer low-cost fallback when embeddings are missing or a deterministic import/probe is needed. |
| `XPathedChunkRetriever` | `XPathedChunkRetriever()` | Filters chunks to those containing an `xpath="..."` attribute. | Useful after syntaxic or custom stages to keep only actionable nodes. |
| `OpsmSplitRetriever` | `OpsmSplitRetriever(driver, top_k=5, group_by=10, rank_fields=[...])` | Builds dictionaries of element attributes, retrieves relevant elements, validates visibility through the driver, and returns node text. | Advanced custom retrieval and benchmarks; needs a live driver for visibility checks. |
| `BM25HtmlRetriever` | `BM25HtmlRetriever(top_k=10, xpathed_only=True)` | Legacy/benchmark BM25 over split HTML. | Reference or experiments; not recommended as the main production retriever. |
| `CleanHTMLRetriever` | `CleanHTMLRetriever(drop_base_64=True, drop_svg=True)` | Removes base64 image data and/or SVG from HTML chunks. | Preprocessing stage for noisy HTML before another retriever. |
| `UniqueXPathRetriever` | `UniqueXPathRetriever(driver)` | Removes redundant elements with identical bounding boxes using driver JavaScript. | Advanced browser-backed cleanup when duplicate nodes confuse action generation. |

## Pipeline examples

Default-like pipeline with explicit embedding:

```python
from lavague.core.retrievers import (
    InteractiveXPathRetriever,
    FromXPathNodesExpansionRetriever,
    SemanticRetriever,
    RetrieversPipeline,
)

retriever = RetrieversPipeline(
    InteractiveXPathRetriever(driver),
    FromXPathNodesExpansionRetriever(chunk_size=750),
    SemanticRetriever(embedding=context.embedding, top_k=10),
)
action_engine = ActionEngine.from_context(context=context, driver=driver, retriever=retriever)
```

No-provider syntaxic pipeline:

```python
from lavague.core.retrievers import (
    InteractiveXPathRetriever,
    SyntaxicRetriever,
    XPathedChunkRetriever,
    RetrieversPipeline,
)

retriever = RetrieversPipeline(
    InteractiveXPathRetriever(driver),
    SyntaxicRetriever(top_k=5),
    XPathedChunkRetriever(),
)
action_engine = ActionEngine(driver=driver, retriever=retriever)
```

The second pattern was distilled from the provider/retriever examples but made safe for local probing. Full agent execution still needs a browser and model context.

## Cohere rerank retriever

The optional Cohere package exposes:

```python
from lavague.retrievers.cohere import CohereRetriever

retriever = CohereRetriever(
    cohere_model="rerank-english-v3.0",
    cohere_api_key=os.environ.get("COHERE_API_KEY"),
    top_k=5,
)
```

Use it only when all of these are true:

- `lavague-retriever-cohere` and `cohere` import successfully.
- `COHERE_API_KEY` is present or a key is passed securely.
- Network/provider calls are explicitly allowed for reranking.
- You understand that this retriever uses Cohere rerank rather than LaVague's embedding model.

For safe checks, inspect the class signature instead of instantiating it. Construction may create a Cohere client, and actual retrieval performs Cohere API calls.

## Selection rules

1. Start with the default pipeline when provider embeddings are available and page markup is ordinary.
2. Use `SyntaxicRetriever` plus `XPathedChunkRetriever` when you need a no-embedding probe, lower cost, or deterministic retrieval scaffolding.
3. Increase `top_k` when the correct element is visible but absent from retrieved nodes; decrease it when generated code targets unrelated repeated elements.
4. Adjust `rank_fields` for `OpsmSplitRetriever` when target attributes are in fields beyond `element`, `placeholder`, `text`, and `name`, such as `type`, `id`, `aria-label`, or `title`.
5. Add `CleanHTMLRetriever` before other stages if embedded images/SVG bloat the prompt.
6. Keep driver-backed retrievers out of pure import tests; they need a real driver object and can execute browser methods.

## Retriever failure clues

- WorldModel instruction is correct but generated action targets the wrong element: inspect retrieved nodes, then tune `top_k`, `rank_fields`, or pipeline stages.
- Missing `OPENAI_API_KEY` appears during a non-OpenAI run: the default or selected pipeline may still use an OpenAI embedding. Pass a context with another embedding, or use a no-provider syntaxic pipeline.
- Iframe content is absent: verify the selected driver can switch frames and that `InteractiveXPathRetriever` can obtain frame HTML; route browser/iframe setup to `../browser-drivers/SKILL.md`.
- Cohere retrieval fails before LLM work: verify the optional package and `COHERE_API_KEY`, then confirm provider calls are allowed.
