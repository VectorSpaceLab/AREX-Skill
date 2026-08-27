# Design-pattern troubleshooting

## The graph feels too big

### Symptoms
- One node prompt does several unrelated things.
- The flow is hard to name or explain.

### Likely cause
- The task was decomposed too coarsely or too loosely.

### Fix
- Split the work into smaller stages with clear outputs.
- Use a separate validation or review node if needed.
- Keep each node focused on one human-recognizable step.

## The graph feels too fragmented

### Symptoms
- There are many tiny nodes with little useful boundary.
- The prompt context is repeating itself across stages.

### Likely cause
- The task was decomposed too granularly.

### Fix
- Merge adjacent stages that always move together.
- Reuse shared-store fields instead of passing through many trivial nodes.

## Agent decision loops never settle

### Symptoms
- The agent keeps searching or asking for another step forever.

### Likely causes
- Action space is ambiguous.
- The stop condition is not explicit.
- The context keeps growing without a limit.

### Fix
- Use a small action set.
- Add a termination action.
- Cap the number of search or refinement rounds.

## Structured output parsing fails

### Symptoms
- YAML or JSON parsing raises errors.
- A downstream node cannot find expected keys.

### Likely causes
- The prompt did not show the exact structure.
- The model emitted extra prose.
- The parser does not validate before storing the result.

### Fix
- Give the model a concrete schema example.
- Strip code fences carefully.
- Validate required keys and types before continuing.

## RAG answers ignore the source documents

### Symptoms
- Retrieval happens, but the answer is generic or off-topic.

### Likely causes
- Chunking is too coarse.
- The query and document embeddings are mismatched.
- The retrieved text is not passed into the answer node.

### Fix
- Check chunk size and chunk count.
- Confirm the same embedding family is used for indexing and querying.
- Log the retrieved context before the answer step.

## Background job progress stalls

### Symptoms
- The UI is waiting forever.
- The progress stream never reaches completion.

### Likely causes
- Queue state is not updated.
- The worker graph never returns a terminal action.
- The service layer and the graph disagree about job ids.

### Fix
- Keep job id and queue management outside the PocketFlow node logic.
- Add a clear completion signal.
- Validate that the job updates are written to the same state the UI is reading.

## Credential or network assumptions leak into the design

### Symptoms
- The app only works in the original developer environment.
- A recipe silently assumes external connectivity or a paid API.

### Likely causes
- Provider-specific steps were mixed into the graph design.
- Optional services were treated as mandatory.

### Fix
- Separate the graph design from the provider wrapper.
- Mark API keys, browser services, or background services as optional dependencies unless the task truly depends on them.
