# Graph Runtime Workflows

Use these recipes to build and validate custom graph workflows without depending on the original repository checkout.

## Build A Linear Graph

```python
from typing_extensions import TypedDict
from langgraph.graph import END, START, StateGraph

class State(TypedDict):
    text: str

def normalize(state: State) -> State:
    return {"text": state["text"].strip().lower()}

def exclaim(state: State) -> State:
    return {"text": state["text"] + "!"}

builder = StateGraph(State)
builder.add_sequence([("normalize", normalize), ("exclaim", exclaim)])
builder.add_edge(START, "normalize")
builder.add_edge("exclaim", END)
graph = builder.compile()
assert graph.invoke({"text": " Hi "}) == {"text": "hi!"}
```

Use `add_sequence` for readability, but still add a `START` edge and finish edge.

## Convert A Linear Graph To Conditional Routing

1. Identify the node whose output determines the branch.
2. Write a route function that returns a small set of symbolic labels or node names.
3. Add `path_map` so validation and visualization know the exact destinations.
4. Ensure every target node exists before `compile()`.
5. Add an `END` route for terminal decisions.

```python
from typing_extensions import Literal, TypedDict
from langgraph.graph import END, START, StateGraph

class State(TypedDict):
    score: int
    decision: str

def score(state: State) -> State:
    return {"score": state["score"] + 1}

def route(state: State) -> Literal["retry", "done"]:
    return "done" if state["score"] >= 3 else "retry"

def mark_done(state: State) -> State:
    return {"decision": "accepted"}

builder = StateGraph(State)
builder.add_node("score", score)
builder.add_node("done", mark_done)
builder.add_edge(START, "score")
builder.add_conditional_edges("score", route, {"retry": "score", "done": "done"})
builder.add_edge("done", END)
graph = builder.compile()
```

If `compile()` reports an unknown branch target, fix the `path_map` or add the missing node. If execution hits a recursion limit, add a reachable stop condition or raise `recursion_limit` only after proving the loop is intentional.

## Add Reducer State For Fan-Out

When multiple nodes can update one key in the same step, use `Annotated` with a reducer.

```python
from typing_extensions import Annotated, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

def extend(left: list[str], right: list[str] | None) -> list[str]:
    return left + (right or [])

class State(TypedDict):
    items: list[str]
    processed: Annotated[list[str], extend]

def route_items(state: State):
    return [Send("worker", {"item": item, "processed": []}) for item in state["items"]]

def worker(state: dict) -> dict:
    return {"processed": [state["item"].upper()]}

builder = StateGraph(State)
builder.add_node("worker", worker)
builder.add_conditional_edges(START, route_items)
builder.add_edge("worker", END)
graph = builder.compile()
```

Validate both a single item and multiple items. Invalid update errors usually mean a shared key needs a reducer or the fan-out input shape is wrong.

## Invoke And Stream

```python
final = graph.invoke({"value": 1})
updates = list(graph.stream({"value": 1}, stream_mode="updates"))
values = list(graph.stream({"value": 1}, stream_mode="values"))
combined = list(graph.stream({"value": 1}, stream_mode=["updates", "values"]))
```

Use `stream_mode="updates"` to inspect which node wrote what. Use `stream_mode="debug"` or `print_mode=["updates", "values"]` when diagnosing execution order, tasks, interrupts, and checkpoints.

For async applications:

```python
result = await graph.ainvoke(input_state)
async for chunk in graph.astream(input_state, stream_mode="updates"):
    print(chunk)
```

Do not call sync `invoke` from an event loop if your graph or app expects async scheduling.

## Add Human Interrupt And Resume

Interrupt/resume requires checkpointing so the graph can continue from the paused state. The concrete saver choice is covered by [persistence](../../persistence/SKILL.md); the runtime usage is:

```python
from typing_extensions import TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

class State(TypedDict):
    question: str
    answer: str

def ask(state: State) -> State:
    answer = interrupt({"question": state["question"]})
    return {"answer": answer}

builder = StateGraph(State)
builder.add_node("ask", ask)
builder.add_edge(START, "ask")
builder.add_edge("ask", END)
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "human-review-1"}}
first = graph.invoke({"question": "Approve?", "answer": ""}, config)
resumed = graph.invoke(Command(resume="yes"), config)
```

If there are multiple interrupts in the same step, inspect interrupt ids and resume with a mapping when needed. Always reuse the exact same `thread_id` for the paused run.

## Pause Before Or After Nodes

Use static interrupts for debugging or human gates around known nodes:

```python
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["review"])
# or per call
graph.invoke(input_state, config, interrupt_after=["draft"])
```

Validation fails if an interrupt node name does not exist. Use `"*"` only for broad debugging; it is noisy in normal applications.

## Use Subgraphs

A compiled graph can be added as a node in a parent graph. Use subgraphs for reusable workflows or nested state machines.

- Decide whether the subgraph should inherit, disable, or use its own checkpointer.
- Stream with `subgraphs=True` when parent-level output hides child activity.
- If a child graph must route to a parent node, return `Command(graph=Command.PARENT, goto="parent_node", update=...)` from the child design.
- Keep state schemas explicit at the parent/child boundary.

## Use Low-Level Pregel Channels

Prefer `StateGraph` unless the task explicitly needs channel-level control. For low-level Pregel wiring, declare channels, subscribe nodes to input channels, write to output channels, and then use the same compiled runtime methods.

```python
from langgraph.channels import EphemeralValue, LastValue
from langgraph.pregel import NodeBuilder, Pregel

node = NodeBuilder().subscribe_only("input").do(lambda value: value + 1).write_to("output")
app = Pregel(
    nodes={"plus_one": node},
    channels={"input": EphemeralValue(int), "output": LastValue(int)},
    input_channels="input",
    output_channels="output",
)
assert app.invoke(1) == 2
```

If two nodes write the same channel in one step, `LastValue` and guarded `EphemeralValue` can fail. Use an aggregating channel such as `BinaryOperatorAggregate` when the graph needs deterministic merges.

## Debug State And History

Checkpointed compiled graphs expose state inspection methods such as `get_state`, `get_state_history`, `update_state`, and `bulk_update_state`. Use them when repairing a paused run, applying human edits, or comparing expected versus actual channel values. Detailed saver setup belongs in [persistence](../../persistence/SKILL.md).

## Validate With The Smoke Script

Run the bundled smoke script after installation or when unsure whether the local environment can execute LangGraph:

```bash
python skills/langgraph/sub-skills/graph-runtime/scripts/smoke_state_graph.py
python skills/langgraph/sub-skills/graph-runtime/scripts/smoke_state_graph.py --start 3 --limit 5 --json
```

The script builds a reducer-backed conditional graph and checks both final output and streamed updates. It performs no network calls, uses no credentials, and writes no files.
