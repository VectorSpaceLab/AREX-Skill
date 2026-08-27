# LaVague QA CLI reference

`lavague-qa` generates pytest-bdd code from a Gherkin `.feature` file by first running a LaVague web agent against the target URL and then building a pytest file from the observed actions and final assertion.

## Safe preflight

Before a live generation run, validate the feature file and print the exact command without launching a browser:

```bash
python scripts/lavague_qa_feature_probe.py --url https://example.test --feature checkout.feature
```

The probe is intentionally file-only. It does not import LaVague, call an LLM, launch a browser, download data, or create `generated_tests/`.

## CLI syntax

```bash
lavague-qa --url <site-url> --feature <path/to/file.feature> [options]
```

Options verified from the installed CLI help:

| Option | Alias | Meaning | Use carefully when |
|---|---:|---|---|
| `--url TEXT` | `-u` | URL of the site to test. Required in normal use. | The URL is public, requires login, or is not stable. |
| `--feature TEXT` | `-f` | Path to the `.feature` file containing Gherkin. Required in normal use. | The file has several scenarios or non-standard Gherkin. |
| `--full-llm` | `-l` | Generate the whole pytest file with the multimodal LLM. | Deterministic generation mismatches the Gherkin, but expect higher token/cost and more variable output. |
| `--context TEXT` | `-c` | Python file that defines initialized `context` and `token_counter` variables. | The default OpenAI context is not desired or default credentials are unavailable. |
| `--headless` | `-h` | Run the browser in headless mode. | The target behaves differently headless/headed, has CAPTCHA, or needs a visible login flow. |
| `--log-to-db` | `-db` | Log the live agent run to the default SQLite logger. | Persistent local log files are not allowed. |
| `--help` | | Show help. | Always safe. |

The package has a demo fallback only in environments where bundled example features are discoverable. Do not rely on that in a standalone Researcher workflow; pass both `--url` and `--feature`.

## Generation modes

### Default mode

Default mode executes each Gherkin action step with a LaVague agent, converts observed navigation actions into pytest-bdd step functions, and uses an LLM only for the final assertion code. This is cheaper than full generation, but it assumes the number of agent action logs aligns with the number of Gherkin `When`/`And` action steps.

```bash
lavague-qa --url https://example.test --feature checkout.feature --headless
```

Expected generated paths:

```text
generated_tests/checkout.feature
generated_tests/checkout.py
```

### Full LLM mode

Use full LLM mode when default mode produces missing/misaligned steps, when action logs do not map cleanly to pytest, or when a human explicitly accepts higher token use.

```bash
lavague-qa --url https://example.test --feature checkout.feature --full-llm --headless
```

Expected generated paths:

```text
generated_tests/checkout.feature
generated_tests/checkout_llm.py
```

## Custom context file

A `--context` Python file is executed by the CLI and must define two variables:

```python
from lavague.core.context import Context
from lavague.core.token_counter import TokenCounter

# initialize llm, mm_llm, and embedding with the provider package you intend to use
context = Context(llm=llm, mm_llm=mm_llm, embedding=embedding)
token_counter = TokenCounter()
```

Keep credentials in environment variables or provider configuration, never in the generated skill. If a custom context fails to import optional provider packages or keys are missing, route to the context sub-skill.

## Generated pytest expectations

- The generated pytest imports `pytest_bdd` scenario decorators and Selenium helpers.
- The generated file references the copied feature by basename, so keep the generated `.py` and `.feature` together under `generated_tests/` unless you edit the scenario path.
- Method names are made by lowercasing Gherkin text and replacing punctuation/spaces with underscores. Similar steps can collide after normalization; rename the Gherkin steps before generation if needed.
- Only live execution can prove selectors and assertions are correct. The static probe only validates shape and command construction.

## Run the generated tests

After generation and with browser/provider requirements satisfied:

```bash
pytest generated_tests/checkout.py
```

If full LLM mode was used:

```bash
pytest generated_tests/checkout_llm.py
```
