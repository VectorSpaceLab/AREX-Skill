# PocketFlow core workflows

Use these recipes when the user wants a concrete PocketFlow graph shape rather than only API semantics.

## 1. Linear flow

Use when each step should run after the previous one with default transitions.

```python
class StepA(Node):
    def prep(self, shared):
        return shared["input"]

    def exec(self, value):
        return value.strip()

    def post(self, shared, prep_res, exec_res):
        shared["clean"] = exec_res

class StepB(Node):
    def prep(self, shared):
        return shared["clean"]

    def exec(self, text):
        return text.upper()

    def post(self, shared, prep_res, exec_res):
        shared["final"] = exec_res

step_a = StepA()
step_b = StepB()
step_a >> step_b
Flow(start=step_a).run({"input": " hello "})
```

### When to use

- Simple task decomposition.
- Cleaning, parsing, summarizing, and post-processing pipelines.
- One LLM call per stage.

## 2. Branching flow

Use when a node returns an action string.

```python
class Decide(Node):
    def exec(self, prep_res):
        return {"action": "search"}

    def post(self, shared, prep_res, exec_res):
        return exec_res["action"]

class Search(Node):
    def post(self, shared, prep_res, exec_res):
        shared["path"] = "search"

class Answer(Node):
    def post(self, shared, prep_res, exec_res):
        shared["path"] = "answer"

decide = Decide()
search = Search()
answer = Answer()
decide - "search" >> search
decide - "answer" >> answer
```

### Notes

- Keep action names explicit and mutually exclusive.
- If `post()` returns `None`, the action is treated as `default`.

## 3. Looping flow

Use when the graph should re-enter a previous node until a condition is met.

```python
class Check(Node):
    def post(self, shared, prep_res, exec_res):
        return "again" if shared["count"] < 3 else "done"

class Inc(Node):
    def prep(self, shared):
        shared["count"] += 1

check = Check()
inc = Inc()
check - "again" >> inc
inc >> check
```

### Notes

- Make sure a loop has a real exit action.
- Store progress in `shared` so the exit condition is visible.

## 4. Nested flow

Use when a reusable sub-workflow should behave like a node.

```python
inner = Flow(start=StepA())
inner >> StepB()
outer = Flow(start=inner)
```

### Notes

- The outer flow sees the inner flow's `post()` action.
- This pattern is useful for reusable subroutines such as parsing, extraction, validation, or post-processing.

## 5. BatchNode map-reduce

Use when one node should process many items and then summarize the results.

```python
class SummarizeChunks(BatchNode):
    def prep(self, shared):
        return shared["chunks"]

    def exec(self, chunk):
        return chunk[:10]

    def post(self, shared, prep_res, exec_res):
        shared["summaries"] = exec_res
        return "default"
```

### Notes

- `prep()` returns the items to map over.
- `exec()` runs once per item.
- `post()` receives the list of all results.

## 6. BatchFlow parameter fan-out

Use when the same flow should run repeatedly with different task parameters.

```python
class ForFiles(BatchFlow):
    def prep(self, shared):
        return [{"filename": name} for name in shared["files"]]

class ReadFile(Node):
    def prep(self, shared):
        return self.params["filename"]
```

### Notes

- BatchFlow is about task identifiers, not about splitting data.
- Put identifiers in `self.params` and long-lived outputs in `shared`.
- Do not treat `self.params` as mutable state.

## 7. Async flow

Use when one or more steps need awaiting.

```python
class Fetch(Node):
    def prep(self, shared):
        return shared["url"]

class AsyncFetch(AsyncNode):
    async def exec_async(self, prep_res):
        return prep_res

flow = AsyncFlow(start=AsyncFetch())
await flow.run_async({"url": "https://example.com"})
```

### Notes

- You can mix sync and async nodes in the same async flow.
- Keep async code at the graph edge; keep the shared-store contract the same.

## 8. Parallel async batch

Use when each item is independent and I/O-bound.

```python
class ParallelFetch(AsyncParallelBatchNode):
    async def prep_async(self, shared):
        return shared["urls"]
```

### Notes

- Good for many API calls, file reads, or network requests.
- Do not use for CPU-heavy work; Python parallelism here is about overlapping async waits.
- Watch upstream service rate limits.

## 9. Safe local smoke case

A useful smoke case for future agents is:

1. A branching flow that writes one shared key.
2. A retry node that falls back after failure.
3. A BatchNode that doubles values and sums them.
4. A tiny async node that returns a transformed string.

That combination proves the most common PocketFlow assumptions without requiring any external API or file system setup.
