# Haystack Component Selection

| Goal | Start here | Notes |
| --- | --- | --- |
| Build or debug a graph | `sub-skills/pipelines-and-components` | Owns component sockets, connections, async execution, serialization, snapshots, and super components. |
| Convert files into documents | `sub-skills/data-ingestion` | Owns `Document`, `ByteStream`, converters, cleaning, splitting, preprocessing, and routing. |
| Index and retrieve documents | `sub-skills/retrieval-and-rag` | Owns document stores, writers, retrievers, filters, rankers, joiners, readers, and RAG wiring. |
| Configure prompts or models | `sub-skills/generation-and-model-components` | Owns prompt builders, text/chat generators, embedders, classifiers, samplers, validators, credentials, and optional model backends. |
| Add tools or agents | `sub-skills/agents-tools-and-hitl` | Owns function tools, component/pipeline tools, tool invocation, agent state, HITL, and tool breakpoints. |
| Measure or trace behavior | `sub-skills/evaluation-and-observability` | Owns retrieval/answer metrics, LLM evaluator caveats, tracing, logging, pipeline debug, and telemetry. |
| Change the repository | `sub-skills/repo-development` | Owns Hatch commands, focused tests, formatting, typing, release notes, and docs checks. |

Use in-memory stores and deterministic smoke scripts first. Add provider-backed generators, LLM evaluators, model downloads, or external services only after the local pipeline shape is correct.
