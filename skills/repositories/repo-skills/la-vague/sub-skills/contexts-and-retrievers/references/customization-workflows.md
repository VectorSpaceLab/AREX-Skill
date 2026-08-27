# Customization workflows

Use these workflows to choose model context, retriever, knowledge, and task data while keeping live provider/browser work explicit.

## 1. Build engines from one provider context

Use `from_context` when one provider context should control ActionEngine LLM, WorldModel multimodal LLM, and embeddings.

```python
from lavague.core import ActionEngine, WorldModel
from lavague.core.agents import WebAgent
from lavague.contexts.gemini import GeminiContext

context = GeminiContext()
world_model = WorldModel.from_context(context)
action_engine = ActionEngine.from_context(context=context, driver=driver)
agent = WebAgent(world_model, action_engine)
```

This pattern is the safest default after verifying imports and credential variables with the probe script.

## 2. Mix providers with custom LlamaIndex objects

Use direct constructor arguments when you want, for example, Anthropic multimodal planning, Fireworks action generation, and a non-default embedding model.

```python
from lavague.core.context import Context
from lavague.core import ActionEngine, WorldModel

context = Context(
    llm=my_llama_index_llm,
    mm_llm=my_llama_index_multimodal_llm,
    embedding=my_llama_index_embedding,
)
world_model = WorldModel.from_context(context)
action_engine = ActionEngine.from_context(context=context, driver=driver)
```

Or override only one component:

```python
world_model = WorldModel(mm_llm=my_multimodal_llm)
action_engine = ActionEngine(driver=driver, llm=my_llm, embedding=my_embedding)
```

Rules:

- All custom objects must be LlamaIndex-compatible (`llm`, `multi_modal_llm`, or `embedding` objects).
- If `embedding` is omitted, `ActionEngine` will use the default context embedding, which may trigger `OPENAI_API_KEY` requirements.
- If `llm`, `embedding`, or `extraction_llm` are omitted in `ActionEngine`, defaults are loaded and can require OpenAI.
- If `mm_llm` is omitted in `WorldModel`, the default context is loaded and can require OpenAI.

## 3. Override provider defaults explicitly

Provider defaults are convenient, but explicit model names avoid stale-doc/default mismatches.

```python
from lavague.contexts.openai import OpenaiContext

context = OpenaiContext(
    llm="gpt-4o-mini",
    mm_llm="gpt-4o-mini",
    embedding="text-embedding-3-small",
)
```

For Azure, always supply deployment and embedding deployment:

```python
from lavague.contexts.openai import AzureOpenaiContext

context = AzureOpenaiContext(
    endpoint="<AZURE_OPENAI_ENDPOINT>",
    deployment="my-chat-deployment",
    embedding_deployment="my-embedding-deployment",
    llm="gpt-4o",
    mm_llm="gpt-4o",
    embedding="text-embedding-3-small",
)
```

## 4. Use a retriever pipeline

Pass a custom retriever into `ActionEngine` or `ActionEngine.from_context`.

```python
from lavague.core import ActionEngine
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
action_engine = ActionEngine.from_context(
    context=context,
    driver=driver,
    retriever=retriever,
)
```

Use this when provider embeddings are unavailable, when you need a deterministic retrieval probe, or when retrieval logs show that semantic retrieval misses simple text/attribute matches.

## 5. Add WorldModel knowledge examples

`WorldModel.add_knowledge(file_path=...)` appends examples to the WorldModel prompt template. The file should contain compact examples with objective, previous instructions, state observations, thoughts, next engine, and instruction. Keep examples task-relevant and avoid storing secrets or private page data in reusable runtime files.

```python
from pathlib import Path
from lavague.core import WorldModel

knowledge_file = Path("knowledge_for_this_run.txt")
knowledge_file.write_text(
    """Objective: Find the billing contact
Previous instructions:
- SCAN
Last engine: Navigation Controls
Current state:
external_observations:
  vision: '[SCREENSHOT]'
internal_state:
  agent_outputs: []
  user_inputs: []

Thoughts:
- The scan shows an Account menu and Billing link.
Next engine: Navigation Engine
Instruction: Click the Billing link in the Account menu.
""",
    encoding="utf-8",
)

world_model = WorldModel.from_context(context)
world_model.add_knowledge(file_path=str(knowledge_file))
```

`NavigationEngine.add_knowledge(knowledge: str)` appends text to the navigation prompt; use it only for short, action-generation-specific constraints.

## 6. Pass task user data

`agent.run(..., user_data=...)` injects task-specific user data into short-term memory under `internal_state.user_inputs`. This is appropriate for form-filling details or structured task context that the WorldModel should consider for the current run.

```python
user_data = {
    "applicant": {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.invalid",
    }
}

result = agent.run(
    "Fill the application form with the provided applicant data.",
    user_data=user_data,
)
```

Use `user_data` for run-scoped inputs, not reusable model knowledge. Use `add_knowledge` for prompt examples that teach behavior across steps.

## 7. Print a no-live template

The bundled probe can print templates without contacting providers or launching a browser:

```bash
python sub-skills/contexts-and-retrievers/scripts/lavague_context_retriever_probe.py --context anthropic --retriever pipeline --print-template
```

Review the printed imports, environment variables, and constructor signatures, then move to live execution only after browser setup and provider budget are approved.
