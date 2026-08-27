# Workflows: Tools, Handoffs, Approvals, and Guardrails

Use these patterns as safe, self-contained adaptations of the repository examples and tests. They are intentionally small and should be expanded inside the target application with real models, context objects, storage, and user approval UI.

## Basic Function Tool

Use `@function_tool` when a Python function should become a model-callable capability.

```python
from typing import Annotated

from pydantic import Field

from agents import Agent, function_tool


@function_tool
async def lookup_order(
    order_id: Annotated[str, Field(min_length=3, description="Customer order ID.")],
) -> str:
    """Look up order status for a customer support workflow."""
    return f"Order {order_id} is processing."


agent = Agent(
    name="Support agent",
    instructions="Use lookup_order for order-status questions.",
    tools=[lookup_order],
)
```

Checklist:

- Add type hints for every tool argument.
- Use docstrings or `description_override` for model-visible guidance.
- Use Pydantic `Field(...)` or `Annotated[...]` for constraints that should appear in schema and runtime validation.
- Keep side effects explicit in tool names and descriptions.
- Run `../scripts/validate_function_tool_schema.py` from this sub-skill to inspect local schema behavior without API calls.

## Strict Schema and Manual FunctionTool

Prefer strict decorator-generated schemas. Reach for manual `FunctionTool` only when the tool must accept a pre-existing raw JSON contract.

```python
import json
from typing import Any

from pydantic import BaseModel

from agents import FunctionTool
from agents.tool_context import ToolContext


class RefundDraftArgs(BaseModel):
    order_id: str
    amount_cents: int
    reason: str


async def create_refund_draft(ctx: ToolContext[Any], raw_args: str) -> str:
    args = RefundDraftArgs.model_validate_json(raw_args)
    return json.dumps(
        {"draft_id": f"refund-{args.order_id}", "amount_cents": args.amount_cents}
    )


refund_tool = FunctionTool(
    name="create_refund_draft",
    description="Create a refund draft for human review; does not issue payment.",
    params_json_schema=RefundDraftArgs.model_json_schema(),
    on_invoke_tool=create_refund_draft,
    strict_json_schema=True,
)
```

Manual tools must parse invalid JSON and validation failures in their own `on_invoke_tool` unless they intentionally let exceptions fail the run.

## Approval-Gated Function Tool

Use HITL approvals for irreversible or sensitive actions.

```python
from agents import Agent, Runner, function_tool


@function_tool(needs_approval=True)
async def cancel_order(order_id: str, reason: str) -> str:
    """Cancel an order after human approval."""
    return f"Cancelled {order_id}: {reason}"


agent = Agent(name="Support agent", tools=[cancel_order])
result = await Runner.run(agent, "Cancel order A123 because the user requested it.")

while result.interruptions:
    state = result.to_state()
    for interruption in result.interruptions:
        if interruption.tool_name == "cancel_order":
            state.approve(interruption)
        else:
            state.reject(interruption)
    result = await Runner.run(agent, state)
```

Rules:

- Resume the original top-level `agent`, not a handoff target or nested agent-as-tool agent.
- Store `state.to_json()` or `state.to_string()` if approval may be asynchronous or long-running.
- Use `RunConfig.tool_error_formatter` when rejected approvals need a custom model-visible message.
- For repeated safe calls within one run, use `always_approve=True`; for repeated denials, use `always_reject=True`.

## Secret-Redacting Tool Guardrails Around Approval

Use tool input/output guardrails for every function-tool call. Set `pre_approval_tool_input_guardrails=True` when you want obvious bad inputs rejected before a human sees a pending approval.

```python
import json

from agents import (
    Agent,
    RunConfig,
    ToolExecutionConfig,
    ToolGuardrailFunctionOutput,
    function_tool,
    tool_input_guardrail,
    tool_output_guardrail,
)


SECRET_MARKERS = ("sk-", "BEGIN PRIVATE KEY", "password=")


@tool_input_guardrail
def block_secret_input(data):
    raw = data.context.tool_arguments or "{}"
    if any(marker in raw for marker in SECRET_MARKERS):
        return ToolGuardrailFunctionOutput.reject_content(
            "Remove secrets before requesting this action."
        )
    return ToolGuardrailFunctionOutput.allow()


@tool_output_guardrail
def redact_secret_output(data):
    text = str(data.output or "")
    if any(marker in text for marker in SECRET_MARKERS):
        return ToolGuardrailFunctionOutput.reject_content(
            "The tool returned sensitive data and it was withheld."
        )
    return ToolGuardrailFunctionOutput.allow()


@function_tool(
    needs_approval=True,
    tool_input_guardrails=[block_secret_input],
    tool_output_guardrails=[redact_secret_output],
)
def publish_ticket_update(ticket_id: str, body: str) -> str:
    """Publish a customer-visible ticket update after approval."""
    return json.dumps({"ticket_id": ticket_id, "status": "queued"})


agent = Agent(name="Ticket agent", tools=[publish_ticket_update])
run_config = RunConfig(
    tool_execution=ToolExecutionConfig(pre_approval_tool_input_guardrails=True)
)
```

Use `reject_content(...)` when the model can recover. Use `raise_exception(...)` when the workflow must halt and surface an application error.

## Agents as Tools Versus Handoffs

Choose by control flow, not by code reuse.

| Requirement | Prefer |
| --- | --- |
| Manager owns final answer and combines specialists | `Agent.as_tool()` |
| Specialist should directly handle the next user-facing turn | `handoff(...)` |
| Specialist needs structured input but not full conversation history | `Agent.as_tool(parameters=...)` |
| Specialist should see the conversation history, possibly filtered | `handoff(..., input_filter=...)` |
| Shared manager-level guardrails should stay central | `Agent.as_tool()` |
| Specialist-specific output guardrails should decide final response | `handoff(...)` |

Agent-as-tool pattern:

```python
from pydantic import BaseModel, Field

from agents import Agent


class TranslationRequest(BaseModel):
    text: str = Field(description="Text to translate.")
    target_language: str = Field(description="Requested target language.")


translator = Agent(name="Translator", instructions="Translate exactly and concisely.")
manager = Agent(
    name="Manager",
    instructions="Call specialists, then produce the final answer.",
    tools=[
        translator.as_tool(
            tool_name="translate_text",
            tool_description="Translate text into a requested language.",
            parameters=TranslationRequest,
            include_input_schema=True,
        )
    ],
)
```

Handoff pattern:

```python
from pydantic import BaseModel

from agents import Agent, RunContextWrapper, handoff


class EscalationMeta(BaseModel):
    reason: str
    priority: str


async def record_escalation(ctx: RunContextWrapper[dict], meta: EscalationMeta) -> None:
    ctx.context.setdefault("handoffs", []).append(meta.model_dump())


refund_agent = Agent(name="Refund agent", handoff_description="Handles refund policy and status.")
triage_agent = Agent(
    name="Triage agent",
    handoffs=[
        handoff(
            refund_agent,
            input_type=EscalationMeta,
            on_handoff=record_escalation,
            tool_description_override="Transfer refund requests with reason and priority.",
        )
    ],
)
```

Important: `input_type` is metadata for the handoff tool call. It does not change the destination and does not replace the next agent's conversation input. Register one handoff per possible destination, or use a custom code-level orchestration step before running an agent.

## Refactor Misused Handoff `input_type` Dynamic Routing

Anti-pattern:

```python
# Bad idea: one handoff tries to route via input_type.destination.
class RoutePayload(BaseModel):
    destination: str
    summary: str

triage = Agent(name="Triage", handoffs=[handoff(generic_agent, input_type=RoutePayload, ...)])
```

Refactor options:

1. Register explicit fixed-destination handoffs:

```python
triage = Agent(
    name="Triage",
    handoffs=[
        handoff(billing_agent, tool_description_override="Transfer billing issues."),
        handoff(refund_agent, tool_description_override="Transfer refund issues."),
        handoff(technical_agent, tool_description_override="Transfer technical issues."),
    ],
)
```

2. Use code-level classification before agent execution when the destination must be deterministic:

```python
route = classify_ticket(ticket)
selected_agent = {"billing": billing_agent, "refund": refund_agent}[route]
result = await Runner.run(selected_agent, ticket)
```

3. Use `Agent.as_tool(parameters=...)` when the manager should call a specialist with structured input but keep control.

## Handoff Input Filtering

Use `input_filter` to trim or transform what the receiving agent sees. The filter receives `HandoffInputData` and returns a clone.

```python
from agents import Agent, handoff
from agents.extensions import handoff_filters


faq_agent = Agent(name="FAQ agent")
triage_agent = Agent(
    name="Triage agent",
    handoffs=[
        handoff(
            faq_agent,
            input_filter=handoff_filters.remove_all_tools,
            tool_description_override="Transfer FAQ-only requests without prior tool chatter.",
        )
    ],
)
```

Use `input_items` when filtering model input but preserving full `new_items` for session history. Use `RunConfig.nest_handoff_history=True` or `handoff(..., nest_handoff_history=True)` for collapsed-history behavior when no explicit filter is set.

## Deferred Tool Search

For large Responses-model tool surfaces, defer schemas until needed.

```python
from typing import Annotated

from agents import Agent, ToolSearchTool, function_tool, tool_namespace


@function_tool(defer_loading=True)
def get_customer_profile(customer_id: Annotated[str, "Customer ID."]) -> str:
    """Fetch a CRM customer profile."""
    return f"profile:{customer_id}"


@function_tool(defer_loading=True)
def list_open_orders(customer_id: Annotated[str, "Customer ID."]) -> str:
    """List open orders."""
    return f"orders:{customer_id}"


crm_tools = tool_namespace(
    name="crm",
    description="CRM tools for customer profiles and order lookups.",
    tools=[get_customer_profile, list_open_orders],
)

agent = Agent(
    name="Operations assistant",
    model="gpt-5.5",
    instructions="Load the crm namespace before CRM lookups.",
    tools=[*crm_tools, ToolSearchTool()],
)
```

Constraints:

- Responses API only.
- Add exactly one `ToolSearchTool()` for deferred function-tool surfaces.
- Prefer namespaces over many individually deferred functions.
- Keep namespaces small and semantically focused.
- Do not set `tool_choice` to a namespace name or a deferred-only function name.

## Local and Hosted ShellTool

Local shell requires an executor. Hosted shell uses an OpenAI container environment and must not include local executor or approval callbacks.

```python
from agents import Agent, ShellResult, ShellCommandOutput, ShellTool


async def run_local_shell(request):
    command_text = "\n".join(request.data.action.commands)
    return ShellResult(
        output=[ShellCommandOutput(stdout=f"Would run:\n{command_text}\n")],
        max_output_length=request.data.action.max_output_length,
    )


local_agent = Agent(
    name="Local shell agent",
    tools=[ShellTool(executor=run_local_shell, needs_approval=True)],
)

hosted_agent = Agent(
    name="Hosted shell agent",
    model="gpt-5.5",
    tools=[
        ShellTool(
            environment={
                "type": "container_auto",
                "network_policy": {"type": "disabled"},
            }
        )
    ],
)
```

Route sandbox-agent workspace isolation, manifests, Docker clients, and sandbox capabilities to the sandbox sub-skill.

## ComputerTool and ApplyPatchTool Patterns

`ComputerTool` requires a local `Computer` or `AsyncComputer` harness. `ApplyPatchTool` requires an `ApplyPatchEditor` implementation. The SDK maps these local harnesses into model-visible tool calls.

```python
from agents import Agent, ApplyPatchTool, ComputerTool
from agents.computer import AsyncComputer
from agents.editor import ApplyPatchEditor, ApplyPatchOperation, ApplyPatchResult


class BrowserHarness(AsyncComputer):
    environment = "browser"
    dimensions = (1024, 768)
    async def screenshot(self): return ""
    async def click(self, x, y, button): ...
    async def double_click(self, x, y): ...
    async def scroll(self, x, y, scroll_x, scroll_y): ...
    async def type(self, text): ...
    async def wait(self): ...
    async def move(self, x, y): ...
    async def keypress(self, keys): ...
    async def drag(self, path): ...


class ReviewEditor(ApplyPatchEditor):
    async def create_file(self, op: ApplyPatchOperation):
        return ApplyPatchResult(status="completed")
    async def update_file(self, op: ApplyPatchOperation):
        return ApplyPatchResult(status="completed")
    async def delete_file(self, op: ApplyPatchOperation):
        return ApplyPatchResult(status="completed")


agent = Agent(
    name="Workspace agent",
    model="gpt-5.5",
    tools=[
        ComputerTool(computer=BrowserHarness()),
        ApplyPatchTool(editor=ReviewEditor(), needs_approval=True),
    ],
)
```

For `ComputerTool`, set a model and `ModelSettings.tool_choice` deliberately when migrating from preview `computer_use_preview` to GA `computer` selectors.

## Agent-Level Guardrails

Input guardrails can be parallel or blocking; output guardrails run after the final output.

```python
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    input_guardrail,
)


@input_guardrail(run_in_parallel=False)
def block_math_homework(ctx: RunContextWrapper[None], agent: Agent, user_input):
    text = user_input if isinstance(user_input, str) else str(user_input)
    return GuardrailFunctionOutput(
        output_info={"checked": "math_homework"},
        tripwire_triggered="solve for x" in text.lower(),
    )


agent = Agent(name="Support agent", input_guardrails=[block_math_homework])

try:
    result = await Runner.run(agent, "Please solve for x: 2x+3=11")
except InputGuardrailTripwireTriggered:
    result = None
```

Use blocking input guardrails for checks that must prevent tool side effects. Use parallel guardrails when latency matters and side effects are not possible before the guardrail result arrives.

## Tool-Not-Found Recovery

When model output may mention stale or conditionally hidden tools, opt into model-visible recovery.

```python
from agents import Agent, RunConfig, Runner


agent = Agent(name="Assistant", tools=[])
result = await Runner.run(
    agent,
    "Use the available tools if needed.",
    run_config=RunConfig(tool_not_found_behavior="return_error_to_model"),
)
```

Use this as a recovery tactic, not as a substitute for clear tool names and accurate `is_enabled` rules.

## Source Patterns Adapted

The patterns above are distilled from the repository's tools, handoffs, guardrails, HITL, multi-agent orchestration, running-agents docs, examples under `examples/tools` and `examples/agent_patterns`, and tests covering function tools, guardrails, handoffs, tool choice reset, and tool guardrails. Credentialed, networked, or UI-dependent originals are intentionally not referenced as runtime dependencies.
