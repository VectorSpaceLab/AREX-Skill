# Orchestration workflows

## 1. Preflight a prompt and a tool request

Use a caller-owned prompt path (the bundled `resources/system_prompts.txt` is
a portable starting template) and validate the section and names before
constructing anything:

```python
from pathlib import Path
from medrax.utils.utils import load_prompts_from_file

prompt_file = Path("system_prompts.txt")
prompts = load_prompts_from_file(str(prompt_file))
if "MEDICAL_ASSISTANT" not in prompts:
    raise ValueError("prompt file must define [MEDICAL_ASSISTANT]")

requested = ["ImageVisualizerTool", "DicomProcessorTool"]
known = {
    "ChestXRayClassifierTool", "ChestXRaySegmentationTool", "LlavaMedTool",
    "XRayVQATool", "ChestXRayReportGeneratorTool", "XRayPhraseGroundingTool",
    "ChestXRayGeneratorTool", "ImageVisualizerTool", "DicomProcessorTool",
}
unknown = set(requested) - known
if unknown:
    raise ValueError(f"unknown MedRAX tools: {sorted(unknown)}")
```

This static check is important because the package's initializer silently skips
unknown names. Never use `tools_to_use=[]` as an exclusion list: the current
implementation treats it as falsy and initializes all registered tools.

## 2. Minimal no-weight agent construction

For a graph smoke test, use only the two utility registrations and a local
writable temporary directory. Do not initialize a model-backed tool merely to
see whether the graph compiles. Import the source-independent adapted factory
from the bundled `scripts/medrax_agent_factory.py`; it validates names before
constructing tools:

```python
from medrax_agent_factory import build_agent

agent, tools = build_agent(
    "system_prompts.txt",
    tools_to_use=["ImageVisualizerTool", "DicomProcessorTool"],
    model_dir=None,                  # utility tools do not need a model directory
    temp_dir="tmp/medrax",
    device="cpu",
    model="local-model-name",
    temperature=0.0,
    top_p=1.0,
    openai_kwargs={
        "api_key": os.environ["OPENAI_API_KEY"],
        **({"base_url": os.environ["OPENAI_BASE_URL"]}
           if os.environ.get("OPENAI_BASE_URL") else {}),
    },
)
assert set(tools) == {"ImageVisualizerTool", "DicomProcessorTool"}
```

The endpoint must still implement chat completions and tool binding. `device`
only affects MedRAX tool constructors; it does not make a remote chat endpoint
local. Select only utility tools while diagnosing the endpoint. A successful
model request is not proof that a tool schema is supported: send a small
synthetic request and check that the model can emit a tool call before using
medical tools.

## 3. Local OpenAI-compatible endpoint

Build kwargs without exposing secrets:

```python
import os

openai_kwargs = {}
if os.getenv("OPENAI_API_KEY"):
    openai_kwargs["api_key"] = os.environ["OPENAI_API_KEY"]
if os.getenv("OPENAI_BASE_URL"):
    openai_kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
```

For a service such as an Ollama- or LM Studio-compatible endpoint, the endpoint
usually ends in `/v1` and the API key may be a local placeholder accepted by
that service. Select only utility tools while diagnosing the endpoint. A
successful model request is not proof that a tool schema is supported: send a
small synthetic request and check that the model can emit a tool call before
using medical tools.

Do not add a model name from an environment variable blindly. The initializer's
`model` argument is the value passed to `ChatOpenAI`; provider model naming is
endpoint-specific. Keep `temperature` and `top_p` explicit so a reproducible
smoke test does not inherit undocumented defaults.

## 4. Checkpointed thread invocation

A compiled `Agent.workflow` accepts the append-only `messages` state. A
checkpointer requires a configurable thread ID:

```python
from langchain_core.messages import HumanMessage

config = {"configurable": {"thread_id": "orchestration-smoke-001"}}
result = agent.workflow.invoke(
    {"messages": [HumanMessage(content="Describe the available tools.")]},
    config,
)
messages = result["messages"]
```

Reuse exactly the same ID only when continuation is intended. Use a fresh ID per
independent case. Do not use an empty or omitted `configurable` section with
`MemorySaver`; LangGraph may raise a missing `thread_id`/checkpoint error.
`MemorySaver` is process-local and volatile, so use a durable checkpointer and
its documented configuration for production persistence.

## 5. Fake-model synthetic orchestration validation

This validates state transitions and tool execution without an API, network, or
model weights. `Agent` calls only `bind_tools` and `invoke` on its model, so a
small protocol fake is sufficient:

```python
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from medrax.agent import Agent

class FakeBindableModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.bound_names = []

    def bind_tools(self, tools):
        self.bound_names = [tool.name for tool in tools]
        return self

    def invoke(self, messages):
        if not self.responses:
            raise AssertionError("fake model exhausted")
        return self.responses.pop(0)

echo = StructuredTool.from_function(
    lambda text: f"echo:{text}", name="SyntheticEcho", description="test echo"
)
model = FakeBindableModel([
    AIMessage(content="", tool_calls=[{
        "name": "SyntheticEcho", "args": {"text": "ok"},
        "id": "synthetic-call-1", "type": "tool_call",
    }]),
    AIMessage(content="synthetic complete"),
])
agent = Agent(
    model, [echo], checkpointer=MemorySaver(),
    system_prompt="Use the synthetic tool once.", log_tools=False,
)
result = agent.workflow.invoke(
    {"messages": [HumanMessage(content="run the check")]},
    {"configurable": {"thread_id": "fake-001"}},
)
assert result["messages"][-1].content == "synthetic complete"
assert model.bound_names == ["SyntheticEcho"]
```

The fake's first response exercises `process -> execute -> process`; the second
ends the graph. Add a second synthetic case with an unknown tool call and assert
that the resulting `ToolMessage.content` contains `invalid tool, please retry`.
This intentionally tests the current fail-soft behavior without asking a model
or importing any optional tool module.

## 6. Logging validation

For a synthetic run with `log_tools=True`, pre-create a writable, isolated log
folder and inspect the newest `tool_calls_*.json` file. Assert its JSON is a
list and each entry has `tool_call_id`, `name`, `args`, `content`, and
`timestamp`. Never assert a fixed filename: the name uses local wall-clock
seconds. For a no-log test pass `log_tools=False`; `_save_tool_calls` then
returns before touching the filesystem.
