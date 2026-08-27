# PocketFlow agentic coding guide

PocketFlow's docs and cookbook favor a simple process: understand the user problem first, design the flow, implement utilities, then wire nodes and iterate.

## 1. Requirements

Start with the user's goal, not the framework.

Ask:
- What should the app do?
- What is the input and output?
- Which steps are deterministic and which require LLM judgment?
- What external systems are allowed?
- What failure modes must the app tolerate?

## 2. Flow design

Write the workflow before implementation.

### Good flow questions
- Is this a fixed sequence or a decision loop?
- Are there independent chunks that should be batched?
- Does the task need offline indexing and online retrieval?
- Do multiple roles need to coordinate?

### Good flow outputs
- A concise node list
- A shared-store schema
- Action names for branches and loops
- A simple diagram

### Example staging
- `Plan`
- `Fetch/Read`
- `Transform`
- `Review/Validate`
- `Finalize`

## 3. Utilities

Utilities are the external functions the nodes call.

Typical utility categories:
- LLM calls
- search APIs
- embedding functions
- vector DB wrappers
- file or DB accessors
- speech synthesis or transcription
- visualization helpers

Rules of thumb:
- Put external I/O in utilities, not in prompt text.
- Keep utilities small and easy to test.
- Document required env vars and credentials.
- Prefer one purpose per utility file.

## 4. Data design

Design the shared store before coding nodes.

### Good shared-store ideas
- Use one top-level dict for the task state.
- Separate inputs, intermediate state, and outputs.
- Avoid redundant copies when a reference or key is enough.
- Store per-run config and task ids in params only when a batch style flow needs them.

### Example
```python
shared = {
    "input": "...",
    "context": {},
    "intermediate": {},
    "results": {},
}
```

## 5. Node design

Describe each node with three questions:
- What does `prep()` read?
- What does `exec()` compute?
- What does `post()` write and which action does it return?

### Example node contract
- `prep`: load current file text
- `exec`: call an LLM or parser
- `post`: store the result and return `next_step`

## 6. Implementation

Implement the graph after the design is stable.

Practical advice:
- Keep nodes small.
- Prefer explicit naming.
- Add logging at boundaries.
- Let node retries handle transient LLM or service failures.
- Add assertions for structured outputs.

## 7. Optimization

After the first version works:
- tighten prompts
- add more specific validation
- split overly large nodes
- reduce prompt bloat
- simplify action spaces

## 8. Reliability

Add reliability in two places:
- validate inputs before `exec()`
- validate outputs before `post()` persists them

### Common reliability levers
- `max_retries`
- `wait`
- fallback results
- explicit review nodes
- deterministic local checks

## 9. Suggested project layout

A compact PocketFlow app often uses:

- `main.py`
- `flow.py`
- `nodes.py`
- `utils/`
- `requirements.txt`
- optional `docs/design.md`

That layout is enough for most small workflows and keeps the app easy to explain.

## 10. Cookbook-derived task families

### Chat
- One node or a short loop
- Conversation history in shared store
- Tooling only if the user asks for it

### Workflow writing
- Outline -> draft -> review -> finalize
- Good for staged synthesis

### Agent research
- Decide -> search -> decide -> answer
- Good for action loops and tool use

### RAG
- Chunk -> embed -> store -> query -> retrieve -> answer
- Good for document-heavy questions

### Text-to-SQL
- schema -> generate SQL -> execute -> debug loop
- Good for schema-aware generation

### Streaming and background jobs
- separate transport from graph logic
- use async or background job updates around the flow, not inside it
