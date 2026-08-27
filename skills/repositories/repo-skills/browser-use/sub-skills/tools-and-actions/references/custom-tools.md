# Custom Tools and Controller Actions

This reference covers Browser Use `Tools`/`Controller` action authoring. `Controller` is a backwards-compatible alias for `Tools`; prefer `Tools` in new code.

## Imports

```python
from pydantic import BaseModel, Field
from browser_use import ActionResult, Agent, BrowserSession, ChatBrowserUse, Tools
```

Use `ChatBrowserUse` as the default model recommendation for browser automation unless the user explicitly requests another provider.

## Registering Actions

```python
tools = Tools()

@tools.action('Look up an internal order by ID')
async def lookup_order(order_id: str) -> ActionResult:
    data = {'order_id': order_id, 'status': 'ready'}
    return ActionResult(extracted_content=str(data), long_term_memory=f'Order {order_id} is ready')
```

Attach the registry to an agent:

```python
agent = Agent(task='Use lookup_order for any order status checks', llm=ChatBrowserUse(), tools=tools)
```

## Signature Rules

The registry normalizes actions into keyword-only functions and validates schemas with Pydantic.

| Rule | Correct pattern | Failure symptom |
| --- | --- | --- |
| Use explicit parameters | `async def action(name: str, count: int = 1)` | Missing schema fields or wrong defaults |
| Do not use `**kwargs` | Use a Pydantic model or named params | `kwargs ... not allowed` |
| Special injected names must use compatible types | `browser_session: BrowserSession` | `conflicts with special argument` |
| Direct decorated calls use keyword args | `await action(params=Model(...), browser_session=session)` | `does not accept positional arguments` |
| Browser-dependent actions need a session | Let `Agent` inject it or pass one in tests | `requires browser_session but none provided` |

Special injectable parameter names include:

- `browser_session: BrowserSession`
- `page_url: str | None`
- `cdp_client`
- `page_extraction_llm`
- `file_system`
- `available_file_paths: list[str]`
- `has_sensitive_data: bool`
- `extraction_schema`
- `context`

Do not use these names for ordinary action inputs.

## Loose-Parameter Pattern

Browser Use auto-generates the action parameter model from non-special parameters.

```python
@tools.action('Fill a field after validating text')
async def safe_fill(index: int, text: str, browser_session: BrowserSession) -> ActionResult:
    if not text.strip():
        return ActionResult(error='Text cannot be empty')
    node = await browser_session.get_element_by_index(index)
    if node is None:
        return ActionResult(error=f'Element index {index} is not available')
    return ActionResult(extracted_content=f'Validated input for element {index}')
```

Use this for simple scalar parameters. Defaults are preserved in the generated schema.

## Pydantic Model Pattern

Use a model when the action has nested data, constraints, descriptions, or validation.

```python
class TicketParams(BaseModel):
    title: str = Field(min_length=3, description='Short ticket title')
    priority: str = Field(pattern='^(low|medium|high)$')

@tools.action('Create a support ticket', param_model=TicketParams)
async def create_ticket(params: TicketParams) -> ActionResult:
    return ActionResult(extracted_content=f'Created {params.priority} ticket: {params.title}')
```

The first non-special parameter is treated as the Pydantic input object when `param_model` is provided.

## Browser-Aware Actions

Use `browser_session` for deterministic page inspection or CDP-backed operations. For general browser/session construction, route to `../../browser-control/SKILL.md`.

```python
@tools.action('Get the current page title and URL')
async def page_identity(browser_session: BrowserSession) -> ActionResult:
    url = await browser_session.get_current_page_url()
    title = await browser_session.get_current_page_title()
    return ActionResult(
        extracted_content=f'{title}\n{url}',
        long_term_memory=f'Observed page title {title!r} at {url}',
    )
```

Avoid bypassing built-in actions for routine clicks, typing, uploads, dropdowns, and navigation unless the task needs deterministic custom logic.

## Domain-Filtered Actions

Restrict credentialed or destructive actions to matching URL patterns.

```python
@tools.action(
    'Submit invoice only on the billing app',
    allowed_domains=['https://billing.example.com', 'https://*.billing.example.com'],
)
async def submit_invoice(invoice_id: str, page_url: str | None = None) -> ActionResult:
    return ActionResult(extracted_content=f'Submitted invoice {invoice_id} from {page_url}')
```

`domains=` and `allowed_domains=` are aliases; do not pass both.

## Sequence-Terminating Actions

Use `terminates_sequence=True` for actions that can invalidate queued follow-up actions, such as navigation-like custom actions.

```python
@tools.action('Open the account dashboard', terminates_sequence=True)
async def open_dashboard(browser_session: BrowserSession) -> ActionResult:
    # Prefer built-in navigate for normal navigation; this is for deterministic app-specific transitions.
    return ActionResult(extracted_content='Dashboard transition requested')
```

## Excluding or Replacing Defaults

```python
tools = Tools(exclude_actions=['search', 'evaluate'])
# or after construction
tools.exclude_action('screenshot')
```

Use exclusions for safety policies, application-specific workflows, or models that should not have broad JavaScript/file access.

## ActionResult Semantics

Return `ActionResult` when the agent needs structured feedback:

```python
return ActionResult(
    extracted_content='Visible to the current reasoning step',
    long_term_memory='Compact fact retained for future steps',
    error=None,
    is_done=False,
    success=None,
)
```

Guidance:

- `extracted_content`: concise observed data or action result.
- `long_term_memory`: durable summary, not raw large output.
- `error`: recoverable failure text; prefer this over raising for expected workflow issues.
- `is_done` and `success`: use only for actions that intentionally complete the user task.
- `include_extracted_content_only_once`: useful for large reads/extractions that should not bloat memory.
- `attachments`/`images`: use for files or visual outputs when relevant.

`Tools.act()` also normalizes `str` returns into `ActionResult(extracted_content=...)` and `None` into an empty `ActionResult`.

## Direct Execution and Validation

For unit tests or debugging, call through the registry or direct action wrapper.

```python
result = await tools.registry.execute_action(
    'lookup_order',
    {'order_id': 'A-123'},
    browser_session=None,
    file_system=None,
    available_file_paths=[],
)
```

Or for registered default/custom actions:

```python
result = await tools.read_file(
    file_name='report.md',
    browser_session=session,
    file_system=file_system,
    available_file_paths=[],
)
```

Use `../tools-and-actions/scripts/validate_custom_tool.py` to smoke-test schema generation and expected failures without a browser.

## Common Anti-Patterns

- `async def action(browser: Browser)`: wrong injection name and type; use `browser_session: BrowserSession`.
- `async def action(**kwargs)`: registry rejects this; define explicit inputs.
- Returning huge raw API responses in `long_term_memory`: put concise summaries in memory and detailed content in files.
- Embedding secrets in descriptions or task strings: use `sensitive_data` placeholders.
- Creating a custom click/upload/navigation when a built-in action already covers the need.
- Registering destructive custom actions with no domain filter or confirmation.
