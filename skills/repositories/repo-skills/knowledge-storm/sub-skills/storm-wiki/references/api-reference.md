# STORM Wiki API Reference

Use these APIs from the installed `knowledge-storm` package.

## Core imports

```python
from knowledge_storm import (
    STORMWikiLMConfigs,
    STORMWikiRunnerArguments,
    STORMWikiRunner,
)
from knowledge_storm.lm import LitellmModel
from knowledge_storm.rm import BingSearch, YouRM
from knowledge_storm.storm_wiki.modules.callback import BaseCallbackHandler
```

Prefer `LitellmModel` for new code. Older `OpenAIModel` and `AzureOpenAIModel` wrappers still exist for compatibility, but they are marked deprecated after v1.1.0 and are not the recommended setup.

## `STORMWikiRunnerArguments`

`STORMWikiRunnerArguments` controls the pipeline and output directory.

| Field | Default | Meaning | Practical guidance |
| --- | ---: | --- | --- |
| `output_dir` | required | Parent directory for generated topic folders. | Use a stable directory. The runner creates a sanitized topic subdirectory. |
| `max_conv_turn` | `3` | Maximum questions in each simulated information-seeking conversation. | Lower to reduce cost/rate pressure. Increase for deeper research. |
| `max_perspective` | `3` | Number of perspectives/personas for perspective-guided question asking. | More perspectives increase coverage and LLM/retriever calls. |
| `max_search_queries_per_turn` | `3` | Maximum search queries generated per conversation turn. | Lower when retriever quotas are tight. |
| `disable_perspective` | `False` | Dataclass field intended to disable perspective-guided question asking. | In the current high-level `STORMWikiRunner.run` path, research is wired with perspective discovery enabled; use `max_perspective=1` for a lighter run or customize the module directly if you need true disablement. |
| `search_top_k` | `3` | Top search results per query. | Affects `rm` construction and research breadth. |
| `retrieve_top_k` | `3` | Top collected references retrieved for each section title during article generation. | Increase for citation diversity; decrease for speed. |
| `max_thread_num` | `10` | Maximum worker threads for research conversations and article-section generation. | Reduce to `1-3` when model or search APIs rate-limit. |

## `STORMWikiLMConfigs`

Create one config object and assign an LM to each component:

```python
lm_configs = STORMWikiLMConfigs()

cheap_lm = LitellmModel(
    model="openai/gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    max_tokens=500,
    temperature=1.0,
    top_p=0.9,
)
strong_outline_lm = LitellmModel(
    model="openai/gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    max_tokens=400,
    temperature=1.0,
    top_p=0.9,
)
strong_article_lm = LitellmModel(
    model="openai/gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    max_tokens=700,
    temperature=1.0,
    top_p=0.9,
)
strong_polish_lm = LitellmModel(
    model="openai/gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    max_tokens=4000,
    temperature=1.0,
    top_p=0.9,
)

lm_configs.set_conv_simulator_lm(cheap_lm)
lm_configs.set_question_asker_lm(cheap_lm)
lm_configs.set_outline_gen_lm(strong_outline_lm)
lm_configs.set_article_gen_lm(strong_article_lm)
lm_configs.set_article_polish_lm(strong_polish_lm)
```

Component setters:

| Setter | Component role | Typical model class |
| --- | --- | --- |
| `set_conv_simulator_lm(model)` | Query splitting and expert-answer synthesis during simulated research conversations. | Cheap/fast `LitellmModel`, `max_tokens≈500`. |
| `set_question_asker_lm(model)` | Generates Wikipedia-writer questions and personas. | Cheap/fast `LitellmModel`, `max_tokens≈500`. |
| `set_outline_gen_lm(model)` | Drafts and refines the article outline. | Stronger `LitellmModel`, `max_tokens≈400`. |
| `set_article_gen_lm(model)` | Writes article sections with inline citations. | Stronger `LitellmModel`, `max_tokens≈700` per section. |
| `set_article_polish_lm(model)` | Adds summary/lead section and optionally removes duplicated content. | Stronger `LitellmModel`, `max_tokens≈4000`. |

## Retriever construction

Internet retrievers are classes in `knowledge_storm.rm`. Examples:

```python
engine_args = STORMWikiRunnerArguments(
    output_dir="./storm-results",
    max_conv_turn=3,
    max_perspective=3,
    max_search_queries_per_turn=3,
    search_top_k=3,
    retrieve_top_k=3,
    max_thread_num=2,
)

rm = BingSearch(
    bing_search_api_key=os.getenv("BING_SEARCH_API_KEY"),
    k=engine_args.search_top_k,
)
# or:
rm = YouRM(ydc_api_key=os.getenv("YDC_API_KEY"), k=engine_args.search_top_k)
```

See [model and retriever options](model-and-retriever-options.md) for the credential matrix and optional-package caveats.

## Runner lifecycle

```python
runner = STORMWikiRunner(engine_args, lm_configs, rm)

runner.run(
    topic="The history of retrieval-augmented generation",
    ground_truth_url="",
    do_research=True,
    do_generate_outline=True,
    do_generate_article=True,
    do_polish_article=True,
    remove_duplicate=False,
    callback_handler=BaseCallbackHandler(),
)
runner.post_run()
runner.summary()
```

### `STORMWikiRunner.run` signature

```python
run(
    topic: str,
    ground_truth_url: str = "",
    do_research: bool = True,
    do_generate_outline: bool = True,
    do_generate_article: bool = True,
    do_polish_article: bool = True,
    remove_duplicate: bool = False,
    callback_handler: BaseCallbackHandler = BaseCallbackHandler(),
)
```

Stage flags and file dependencies:

| Flag | If `True` | If `False` / resume requirement |
| --- | --- | --- |
| `do_research` | Runs perspective-guided simulated conversations and internet retrieval. Writes `conversation_log.json` and `raw_search_results.json`. | Later stages load `conversation_log.json` from the topic output directory. |
| `do_generate_outline` | Generates `direct_gen_outline.txt` and `storm_gen_outline.txt`. | Article generation loads `storm_gen_outline.txt`. |
| `do_generate_article` | Generates `storm_gen_article.txt` and `url_to_info.json`. | Polishing loads `storm_gen_article.txt` and `url_to_info.json`. |
| `do_polish_article` | Generates `storm_gen_article_polished.txt`. | No polished file is produced. |
| `remove_duplicate` | Adds a whole-page duplicate-removal LM pass during polishing. | Polishing only adds the summary/lead and preserves the draft body. |
| `ground_truth_url` | Excludes a known reference URL from search results during research. | Empty string means no explicit exclusion. |

At least one stage flag must be true.

### `post_run()`

`post_run()` writes:

- `run_config.json`: ordered mapping of LM component names to their model kwargs.
- `llm_call_history.jsonl`: one JSON object per collected LM call, with per-call kwargs removed because they are centralized in `run_config.json`.

Call `post_run()` after `run()` if you need provenance, debugging, token-history inspection, or reproducibility metadata.

### `summary()`

`summary()` prints:

- execution time per `run_*` module;
- token usage grouped by module and model when the LM exposes `get_usage_and_reset()`;
- retriever query counts when the retriever exposes `get_usage_and_reset()`.

## Output file contracts

| File | Shape | Notes |
| --- | --- | --- |
| `conversation_log.json` | List of `{ "perspective": str, "dlg_turns": [...] }`. Each turn includes `agent_utterance`, `user_utterance`, `search_queries`, and `search_results`. | Used to reconstruct `StormInformationTable` when research is skipped. |
| `raw_search_results.json` | URL-keyed dictionary of `Information` records with `url`, `title`, `description`, `snippets`, `meta`, and `citation_uuid`. | Good first check for retriever quality. |
| `direct_gen_outline.txt` | Markdown-heading outline generated without the collected conversation. | Compare with refined outline to diagnose retrieval influence. |
| `storm_gen_outline.txt` | Markdown-heading outline refined using collected information. | Required when `do_generate_outline=False` but article generation is enabled. |
| `storm_gen_article.txt` | Markdown article sections with inline numeric citations. | Required with `url_to_info.json` for polish-only resume. |
| `url_to_info.json` | Citation reference mapping: `url_to_unified_index` and `url_to_info`. | Use to resolve `[1]`, `[2]`, etc. to source URLs and snippets. |
| `storm_gen_article_polished.txt` | Final polished markdown article. | Includes a generated `# summary` lead section. |
| `run_config.json` | Component-to-kwargs mapping for configured LMs. | Does not replace provider-side logs. |
| `llm_call_history.jsonl` | JSONL call history after `post_run()`. | Useful for debugging model behavior; may be empty if no LLM calls were made. |

## `BaseCallbackHandler` hooks

Subclass only the hooks you need:

```python
class PrintCallback(BaseCallbackHandler):
    def on_identify_perspective_start(self, **kwargs):
        print("Identifying perspectives...")

    def on_identify_perspective_end(self, perspectives: list[str], **kwargs):
        print(f"Perspectives: {len(perspectives)}")

    def on_dialogue_turn_end(self, dlg_turn, **kwargs):
        urls = sorted({r.url for r in dlg_turn.search_results})
        print(f"Dialogue turn complete; retrieved {len(urls)} unique URLs")
```

Available hooks:

| Hook | Called when |
| --- | --- |
| `on_identify_perspective_start` | Perspective/persona discovery begins. |
| `on_identify_perspective_end(perspectives)` | Perspective/persona discovery ends. |
| `on_information_gathering_start` | Simulated conversations and retrieval begin. |
| `on_dialogue_turn_end(dlg_turn)` | One question/answer dialogue turn completes. |
| `on_information_gathering_end` | Research conversations finish. |
| `on_information_organization_start` | Outline organization begins. |
| `on_direct_outline_generation_end(outline)` | Direct parametric outline is generated. |
| `on_outline_refinement_end(outline)` | Refined outline is generated. |
