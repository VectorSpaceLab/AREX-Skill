# Data formats for QA and test-runner workflows

## Gherkin feature files for `lavague-qa`

Use a plain `.feature` file with one clear scenario when possible:

```gherkin
Feature: Checkout

  Scenario: Remove one product from the cart
    Given the user is on the homepage
    When the user searches for "Zero to One"
    And the user opens the first product result
    And the user adds the product to the cart
    And the user removes the product from the cart
    Then the cart should be empty
```

Shape rules distilled from the generator:

- `Feature:` and at least one `Scenario:` are required.
- `Given` steps become setup/context steps. The first generated `Given` usually opens the base URL.
- `When` steps become action steps. `And` inherits the previous keyword, so an `And` after a `When` is also an action step.
- `Then` steps become expected outcomes. Current generation uses the first outcome for assertion generation; multiple `Then` steps should be combined or split into separate generation runs.
- The generator parses scenarios but selects the first scenario for generation. Keep one scenario per feature file for predictable output.
- Malformed Gherkin stops generation before any useful pytest is written; run the bundled feature probe first.

Naming rules:

| Input feature | Default generated pytest | Full-LLM generated pytest |
|---|---|---|
| `checkout.feature` | `generated_tests/checkout.py` | `generated_tests/checkout_llm.py` |
| `demo_amazon.feature` | `generated_tests/demo_amazon.py` | `generated_tests/demo_amazon_llm.py` |

Generated function names are derived from step text. Avoid two steps that normalize to the same lowercase underscore name.

## `lavague-test` site config YAML

Each site folder contains a `config.yml`. Use this portable shape:

```yaml
type: web
max_steps: 5
n_attempts: 1
user_data:
  role: anonymous
tasks:
  - name: Search docs
    url: https://example.test
    prompt: Go to the documentation quickstart
    max_steps: 5
    n_attempts: 1
    expect:
      - URL contains /docs
      - Status is success
      - HTML contains Quickstart
    user_data:
      task_note: prefer visible navigation links
```

Required and optional fields:

| Location | Field | Required | Notes |
|---|---|---:|---|
| top level | `type` | Recommended | Use `web` for external/already-running sites and `static` for built-in static serving. Some releases document an implicit web default, but adding `type: web` avoids parser ambiguity. |
| top level | `tasks` | Yes | Non-empty list of task objects. |
| top level | `max_steps` | No | Default is 5; task value overrides it. |
| top level | `n_attempts` | No | Default is 1; task value overrides it. |
| top level | `user_data` | No | Mapping merged with task-level `user_data`. |
| static only | `directory` | No | Directory served from the site folder; default is `www`. Set it explicitly. |
| static only | `port` | No | Port for the local static server. Use an integer, commonly `8000`. |
| task | `name` | No | Display name. Defaults to a prompt/from-URL string. |
| task | `url` | Usually | Required for `web`; optional only when a static setup default URL is acceptable. |
| task | `prompt` | Yes | Agent objective. |
| task | `expect` | No | String or list of expectation expressions. Without it, there is nothing to assert. |
| task | `max_steps` | No | Overrides top-level `max_steps`. |
| task | `n_attempts` | No | Overrides top-level `n_attempts`. |
| task | `user_data` | No | Mapping merged over top-level `user_data`. |

## Expectation vocabulary

Expectation strings are parsed as:

```text
<Property> <operator> <value>
```

Available operators:

| Operator | Meaning |
|---|---|
| `is` | equality |
| `is not` | inequality |
| `is lower than` | less-than comparison |
| `is greater than` | greater-than comparison |
| `contains` | left value contains right value |
| `does not contain` | left value does not contain right value |

Available result properties are case-sensitive:

| Property | Observed value |
|---|---|
| `URL` | Final browser URL. |
| `Status` | `success` or `failure` from the LaVague result. |
| `Output` | Agent final output text. |
| `Steps` | Number of logged agent steps. |
| `HTML` | Final page HTML. |
| `Tabs` | Browser tab summary. |

Examples:

```yaml
expect:
  - URL is https://example.test/docs/quickstart
  - Status is success
  - HTML contains <h1>Quickstart</h1>
  - Output does not contain Traceback
```

Cautions:

- Property names are exact. `url is ...` does not match `URL`.
- Numeric comparisons depend on the installed parser's type handling. Probe configs that use `Steps is lower than 5` before a live run.
- Keep expected substrings stable and specific. Very long HTML snippets are brittle.

## Static-site config

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

The static server is started only during a live `lavague-test` run. The bundled config probe only verifies the YAML shape and file/directory references.
