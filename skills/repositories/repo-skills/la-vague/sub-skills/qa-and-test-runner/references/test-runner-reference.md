# LaVague test-runner reference

`lavague-test` runs LaVague agents against one or more site configuration folders and checks the final agent context against declarative expectations.

## Safe preflight

Validate one site config and print the command before launching Selenium or a model provider:

```bash
python scripts/lavague_tests_config_probe.py --config sites/example-site/config.yml
```

The probe reads YAML only. It does not start a static server, open a browser, call an LLM, contact the target site, or write a database.

## CLI syntax

```bash
lavague-test [options]
```

Options verified from the installed CLI help:

| Option | Alias | Meaning | Notes |
|---|---:|---|---|
| `--context TEXT` | `-c` | Python file containing initialized `context` and `token_counter`. | Prefer an explicit context file outside the original checkout; it is executed as Python. |
| `--directory TEXT` | `-d` | Directory containing site subdirectories. | Each selected subdirectory must contain `config.yml`. |
| `--site TEXT` | `-s` | Site name to run. May be repeated. | The value must match a subdirectory name under `--directory`. |
| `--display` | | Show the browser. Without it, tests run headless. | Use only when the user accepts an interactive browser. |
| `--log-to-db` | `-db` | Enable default SQLite logging. | Opt in only when persistent local logs are acceptable. |
| `--help` | | Show help. | Always safe. |

The documented default directory is relative to the current working directory. For self-contained operation, pass `--directory` and `--site` explicitly instead of depending on the working directory.

## Site folder layout

```text
sites/
  example-site/
    config.yml
    www/              # only when type: static uses the default directory
```

Run one site:

```bash
lavague-test --directory sites --site example-site
```

Run multiple sites:

```bash
lavague-test --directory sites --site example-site --site another-site
```

Run all site folders under a directory:

```bash
lavague-test --directory sites
```

## What a live run does

For each configured task, the runner:

1. Loads `context` and `token_counter`.
2. Creates a Selenium-backed LaVague agent with `headless=not --display`.
3. Applies global or task-specific `max_steps` and `n_attempts`.
4. Calls `agent.get(task.url)` and then `agent.run(task.prompt, user_data=..., log_to_db=...)`.
5. Builds a result context with `URL`, `Status`, `Output`, `Steps`, `HTML`, and `Tabs`.
6. Evaluates every `expect` expression against that context.

## Output and exit status

The output is a human-readable report. Successful expectations are listed under `[o]`; failures are listed under `[x]` with the observed value. A final summary includes success percentage, elapsed time, and token/cost tables when token logs are available.

The process exits successfully only if every selected task expectation passes. Treat any non-zero exit as a failed benchmark, even if some tasks passed.

## Local static sites

A config with `type: static` starts a simple local static file server for the duration of the run:

```yaml
type: static
port: 8000
directory: www
tasks:
  - name: Navigate using link
    url: http://localhost:8000
    prompt: Go to the menu
    max_steps: 1
    expect:
      - URL is http://localhost:8000/menu.html
      - HTML contains <h1>Menu</h1>
```

Use an integer `port` and keep the static `directory` under the site folder. If the task `url` is omitted, the static setup can provide `http://localhost:8000` as a default in supported versions; passing `url` explicitly is clearer.

## Dynamic or already-running local sites

The package documentation notes that dynamic local-site initialization is not implemented. For dynamic apps, start and stop the server outside `lavague-test`, then use a normal `type: web` config with an explicit `url`. Do not leave persistent servers running unless the user explicitly asked for them.
