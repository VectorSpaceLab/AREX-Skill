# Demo-Light Reference Notes

The demo-light UI is a minimal Streamlit application around `STORMWikiRunner`. This sub-skill does not bundle or reproduce the full UI code, assets, or page modules. Use these notes to recreate the relevant operating pattern in your own app.

## What the demo does

The lightweight UI pattern provides:

1. a "Create New Article" page where the user enters a topic;
2. real-time progress updates while `STORMWikiRunner` researches and outlines;
3. a final article view with article text and references side by side;
4. a "My Articles" page that lists previously generated topic directories.

Outputs are ordinary STORM output files in an application working directory, so they can also be inspected with the CLI workflows in this sub-skill.

## Setup pattern

A local Streamlit app needs three layers:

1. **Package/runtime dependencies**
   - Required: `knowledge-storm` and its runtime dependencies.
   - UI extras: `streamlit`, `streamlit-card`, `markdown`, `streamlit-float`, `streamlit-option-menu`, and related Streamlit helper packages used by the app.
2. **Secrets**
   - Place keys in Streamlit secrets, usually `.streamlit/secrets.toml`, or load them into environment variables before app startup.
   - Minimum examples: model provider key such as `OPENAI_API_KEY`, plus retriever key such as `YDC_API_KEY` or `BING_SEARCH_API_KEY`.
3. **Runner initialization**
   - Create `STORMWikiRunnerArguments(output_dir=<demo-working-dir>, ...)`.
   - Create `STORMWikiLMConfigs` using `LitellmModel` for each component.
   - Create a retriever such as `YouRM` or `BingSearch`.
   - Store the resulting `STORMWikiRunner` in Streamlit session state.

## Modernized runner initialization sketch

```python
import os
import streamlit as st
from knowledge_storm import STORMWikiRunnerArguments, STORMWikiRunner, STORMWikiLMConfigs
from knowledge_storm.lm import LitellmModel
from knowledge_storm.rm import YouRM

for key, value in st.secrets.items():
    if isinstance(value, str):
        os.environ[key] = value

output_dir = "./DEMO_WORKING_DIR"
engine_args = STORMWikiRunnerArguments(
    output_dir=output_dir,
    max_conv_turn=3,
    max_perspective=3,
    search_top_k=3,
    retrieve_top_k=5,
    max_thread_num=2,
)

lm_kwargs = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "temperature": 1.0,
    "top_p": 0.9,
}
lm_configs = STORMWikiLMConfigs()
lm_configs.set_conv_simulator_lm(LitellmModel(model="openai/gpt-4o-mini", max_tokens=500, **lm_kwargs))
lm_configs.set_question_asker_lm(LitellmModel(model="openai/gpt-4o-mini", max_tokens=500, **lm_kwargs))
lm_configs.set_outline_gen_lm(LitellmModel(model="openai/gpt-4o", max_tokens=400, **lm_kwargs))
lm_configs.set_article_gen_lm(LitellmModel(model="openai/gpt-4o", max_tokens=700, **lm_kwargs))
lm_configs.set_article_polish_lm(LitellmModel(model="openai/gpt-4o", max_tokens=4000, **lm_kwargs))

rm = YouRM(ydc_api_key=os.getenv("YDC_API_KEY"), k=engine_args.search_top_k)
st.session_state["runner"] = STORMWikiRunner(engine_args, lm_configs, rm)
```

This sketch intentionally uses `LitellmModel`. If older UI code uses `OpenAIModel`, replace it for new implementations.

## Two-phase UI run pattern

The UI can split a full article into a fast visible research phase and a longer final writing phase.

### Phase 1: pre-writing

```python
runner.run(
    topic=topic,
    do_research=True,
    do_generate_outline=True,
    do_generate_article=False,
    do_polish_article=False,
    callback_handler=streamlit_callback_handler,
)
```

Display `conversation_log.json` immediately after this phase so users can see perspectives, questions, and source discovery.

### Phase 2: final writing

```python
runner.run(
    topic=topic,
    do_research=False,
    do_generate_outline=False,
    do_generate_article=True,
    do_polish_article=True,
    remove_duplicate=False,
)
runner.post_run()
```

This resumes from `conversation_log.json` and `storm_gen_outline.txt`, then writes `storm_gen_article.txt`, `url_to_info.json`, `storm_gen_article_polished.txt`, `run_config.json`, and `llm_call_history.jsonl`.

## Streamlit callback pattern

Subclass `BaseCallbackHandler` and update a Streamlit status container in selected hooks:

- `on_identify_perspective_start`: show that perspective discovery started.
- `on_identify_perspective_end`: list perspectives/personas.
- `on_information_gathering_start`: show that browsing/retrieval started.
- `on_dialogue_turn_end`: display URLs retrieved for that dialogue turn.
- `on_information_gathering_end`: mark research complete.
- `on_information_organization_start`: show outline organization started.
- `on_direct_outline_generation_end`: mark direct outline finished.
- `on_outline_refinement_end`: mark refined outline finished.

Keep callback bodies lightweight. Avoid long blocking work inside callbacks because the runner already uses concurrency internally.

## Display pattern

A minimal article viewer can read the topic directory and prefer files in this order:

1. `storm_gen_article_polished.txt` if present;
2. otherwise `storm_gen_article.txt`;
3. `url_to_info.json` for citation titles, URLs, and snippets;
4. `conversation_log.json` for expandable research-dialogue history.

Useful display transformations:

- convert inline `[1]` citation markers into links using `url_to_info.json`;
- render markdown headings as a table of contents;
- show a reference sidebar with title, URL, and snippets;
- show persona conversations as chat turns after stripping citation markers from dialogue text.

## Boundaries

- Do not copy the full demo UI tree just to run STORM; the core article-generation API is `STORMWikiRunner`.
- Do not use demo UI code as the source of truth for model wrappers. New code should use `LitellmModel`.
- Do not store long-lived production secrets in a checked-in `secrets.toml`; use Streamlit secrets, environment variables, or your deployment secret manager.
- The UI working directory can be any stable app-controlled directory. Preserve the same topic string and working directory when resuming stages.
