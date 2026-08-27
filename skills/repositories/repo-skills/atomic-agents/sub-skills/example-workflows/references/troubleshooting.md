# Example Workflow Troubleshooting

## Missing provider key

**Symptom:** a quickstart, multimodal, search, research, or video example fails before the first call.

**Cause:** the example is key-backed and the environment does not contain the required provider credentials.

**Fix:** check the example README or the dependency matrix to identify the provider and required variable names before trying to run it.

## Network / remote service failure

**Symptom:** search, RAG, research, YouTube, or MCP example calls time out or cannot connect.

**Cause:** the example expects network access or a local service that is not running yet.

**Fix:** start the needed local service first, or treat the example as documentation-only until the user authorizes live execution.

## Vector store / retrieval setup problems

**Symptom:** the RAG example cannot index or retrieve documents.

**Cause:** the vector store, embeddings dependency, or dataset path is missing.

**Fix:** verify the example-specific dependencies and follow the example's setup sequence before testing retrieval.

## FastAPI or multi-process memory failures

**Symptom:** the memory API example starts but does not persist state as expected.

**Cause:** the persistence backend or session wiring is incomplete.

**Fix:** keep the example's state store configuration intact and confirm that the session identifier is being propagated.

## MCP example transport confusion

**Symptom:** the MCP demo does not connect.

**Cause:** the server/client transport combination is wrong or the server was not started first.

**Fix:** follow the example's transport ordering exactly; STDIO, SSE, and HTTP Stream each need slightly different launch steps.

## YouTube / transcript issues

**Symptom:** transcript extraction fails for a video example.

**Cause:** the video is unavailable, private, or does not expose transcripts.

**Fix:** use a public video with transcripts or treat the example as a recipe rather than a guaranteed runnable demo.
