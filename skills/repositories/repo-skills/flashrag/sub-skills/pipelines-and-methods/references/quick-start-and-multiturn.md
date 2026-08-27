# Quick-Start Demos and Multi-Turn Workflows

This page covers safe adaptations of FlashRAG quick-start scripts and interactive demos without running large models by default.

## Simple pipeline quick start

A minimal standard RAG run uses:

- `Config` with `data_dir`, `corpus_path`, `index_path`, `model2path`, `retrieval_method`, `generator_model`, metrics, and sampling/output settings.
- `get_dataset(config)` to load a split such as `test`.
- `PromptTemplate` with `{reference}` and `{question}` placeholders.
- `SequentialPipeline(config, prompt_template=...)` followed by `pipeline.run(dataset, do_eval=True/False)`.

Adaptation checklist:

1. Replace placeholder model names in `model2path` with user-provided model identifiers or paths.
2. Ensure `retrieval_method` matches both `model2path` and the index embedding model.
3. Ensure `corpus_path` points to a JSONL corpus and `index_path` points to a compatible index.
4. Start with `test_sample_num` set to a small value and `retrieval_topk` set to 1 for smoke tests.
5. Set `save_intermediate_data=True` when you need to inspect `retrieval_result`, `prompt`, and `pred`.

## Demo app pattern

FlashRAG Streamlit demos follow this pattern:

1. Create a config with `save_note`, `model2path`, `retrieval_method`, `generator_model`, `corpus_path`, and `index_path`.
2. Cache `get_retriever(config)` and `get_generator(config)` resources.
3. Read a user query.
4. Retrieve documents with `retriever.search(query, num=topk)`.
5. Build two prompts: one with retrieved references and one without RAG.
6. Generate both responses and display retrieved document snippets.

Safe adaptation notes:

- Do not instantiate cached retriever/generator until the user has confirmed model/index availability.
- Make `temperature`, `topk`, and max generation tokens UI controls with conservative defaults.
- Keep retrieved document display short enough to avoid leaking large corpora in logs.
- For multilingual demos, align `retrieval_method`, retriever model, corpus language, prompt language, and generator model.

## Multi-turn generator workflow

FlashRAG supports chat-like multi-turn generation through `PromptTemplate.get_string(messages=messages)`.

Skeleton:

```python
from flashrag.config import Config
from flashrag.utils import get_generator
from flashrag.prompt import PromptTemplate

config = Config(config_dict={
    "model2path": {"llama3-8B-instruct": "USER_MODEL"},
    "generator_model": "llama3-8B-instruct",
    "generation_params": {"max_tokens": 128},
})
generator = get_generator(config)
prompt_template = PromptTemplate(config)
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "First question"},
]
first_prompt = prompt_template.get_string(messages=messages)
first_output = generator.generate(first_prompt)[0]
messages.append({"role": "assistant", "content": first_output})
messages.append({"role": "user", "content": "Follow-up question"})
second_prompt = prompt_template.get_string(messages=messages)
second_output = generator.generate(second_prompt)[0]
```

Use `assistant` for prior model answers. If you intentionally inject corrective system-like instructions in later turns, document why; most chat templates expect alternating user/assistant roles after the initial system message.

## Multi-turn with retrieval

For a retrieval-aware conversation, keep the chat state separate from per-turn retrieved evidence:

1. Store persistent `messages` for conversational context.
2. For each new user turn, retrieve with the current user question, optionally augmented by a short conversation summary.
3. Use a prompt template whose system prompt includes `{reference}` and whose user prompt includes the current question.
4. Add only the final answer to `messages`; store `retrieval_result` separately for auditability.

Avoid stuffing all previous retrieved documents into every turn. Instead, summarize prior turns or retrieve again from the current turn to control prompt length.

## Smoke-test strategy

- `zero-shot`: test generator and prompt template without retrieval/index dependencies.
- `SequentialPipeline.naive_run`: test dataset loading plus generation without retrieval.
- `SequentialPipeline.run` on 1-5 samples: test retrieval, prompt formatting, generation, and optional evaluation.
- Streamlit demo dry-run: render UI and config validation first; instantiate models only after explicit approval.
