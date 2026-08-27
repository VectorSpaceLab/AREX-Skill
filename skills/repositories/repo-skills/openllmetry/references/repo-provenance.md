# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an OpenLLMetry checkout. If the current commit, tag, package versions, entry points, source roots, or checkout testing workflow differ materially from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-10T06:27:23Z",
  "repository": {
    "name": "openllmetry",
    "remote_url": "https://github.com/traceloop/openllmetry.git",
    "vcs": "git",
    "branch": "main",
    "tag": "0.62.2",
    "commit": "c2f3f45e26ebee23d97ff30fb0fa84a8cb030a1b",
    "working_tree": "clean-at-evidence-capture",
    "dirty_paths": [],
    "notes": "Generated skill files were created after the evidence snapshot and are not part of the source baseline."
  },
  "packages": [
    {
      "name": "opentelemetry-instrumentation-agno",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.agno"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-alephalpha",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.alephalpha"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-anthropic",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.anthropic"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-bedrock",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.bedrock"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-chromadb",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.chromadb"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-cohere",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.cohere"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-crewai",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.crewai"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-google-generativeai",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.google_generativeai"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-groq",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.groq"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-haystack",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.haystack"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-lancedb",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.lancedb"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-langchain",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.langchain"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-litellm",
      "version": "0.1.0",
      "import_names": [
        "opentelemetry.instrumentation.litellm"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-llamaindex",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.llamaindex"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-marqo",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.marqo"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-mcp",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.mcp"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-milvus",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.milvus"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-mistralai",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.mistralai"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-ollama",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.ollama"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-openai",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.openai"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-openai-agents",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.openai_agents"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-pinecone",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.pinecone"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-qdrant",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.qdrant"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-replicate",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.replicate"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-sagemaker",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.sagemaker"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-together",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.together"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-transformers",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.transformers"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-vertexai",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.vertexai"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-voyageai",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.voyageai"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-watsonx",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.watsonx"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-weaviate",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.weaviate"
      ]
    },
    {
      "name": "opentelemetry-instrumentation-writer",
      "version": "0.62.2",
      "import_names": [
        "opentelemetry.instrumentation.writer"
      ]
    },
    {
      "name": "opentelemetry-semantic-conventions-ai",
      "version": "0.5.2",
      "import_names": [
        "opentelemetry.semconv_ai"
      ]
    },
    {
      "name": "sample-app",
      "version": "0.0.1",
      "import_names": [
        "sample_app"
      ]
    },
    {
      "name": "traceloop-sdk",
      "version": "0.62.2",
      "import_names": [
        "traceloop.sdk"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "packages/opentelemetry-instrumentation-agno/opentelemetry/instrumentation/agno",
      "packages/opentelemetry-instrumentation-alephalpha/opentelemetry/instrumentation/alephalpha",
      "packages/opentelemetry-instrumentation-anthropic/opentelemetry_instrumentation_anthropic",
      "packages/opentelemetry-instrumentation-bedrock/opentelemetry_instrumentation_bedrock",
      "packages/opentelemetry-instrumentation-chromadb/opentelemetry/instrumentation/chromadb",
      "packages/opentelemetry-instrumentation-cohere/opentelemetry/instrumentation/cohere",
      "packages/opentelemetry-instrumentation-crewai/opentelemetry_instrumentation_crewai",
      "packages/opentelemetry-instrumentation-google-generativeai/opentelemetry/instrumentation/google_generativeai",
      "packages/opentelemetry-instrumentation-groq/opentelemetry_instrumentation_groq",
      "packages/opentelemetry-instrumentation-haystack/opentelemetry/instrumentation/haystack",
      "packages/opentelemetry-instrumentation-lancedb/opentelemetry/instrumentation/lancedb",
      "packages/opentelemetry-instrumentation-langchain/opentelemetry/instrumentation/langchain",
      "packages/opentelemetry-instrumentation-litellm/opentelemetry/instrumentation/litellm",
      "packages/opentelemetry-instrumentation-llamaindex/opentelemetry/instrumentation/llamaindex",
      "packages/opentelemetry-instrumentation-marqo/opentelemetry/instrumentation/marqo",
      "packages/opentelemetry-instrumentation-mcp/opentelemetry/instrumentation/mcp",
      "packages/opentelemetry-instrumentation-milvus/opentelemetry/instrumentation/milvus",
      "packages/opentelemetry-instrumentation-mistralai/opentelemetry/instrumentation/mistralai",
      "packages/opentelemetry-instrumentation-ollama/opentelemetry/instrumentation/ollama",
      "packages/opentelemetry-instrumentation-openai/opentelemetry/instrumentation/openai",
      "packages/opentelemetry-instrumentation-openai-agents/opentelemetry/instrumentation/openai_agents",
      "packages/opentelemetry-instrumentation-pinecone/opentelemetry/instrumentation/pinecone",
      "packages/opentelemetry-instrumentation-qdrant/opentelemetry/instrumentation/qdrant",
      "packages/opentelemetry-instrumentation-replicate/opentelemetry/instrumentation/replicate",
      "packages/opentelemetry-instrumentation-sagemaker/opentelemetry_instrumentation_sagemaker",
      "packages/opentelemetry-instrumentation-together/opentelemetry/instrumentation/together",
      "packages/opentelemetry-instrumentation-transformers/opentelemetry/instrumentation/transformers",
      "packages/opentelemetry-instrumentation-vertexai/opentelemetry/instrumentation/vertexai",
      "packages/opentelemetry-instrumentation-voyageai/opentelemetry/instrumentation/voyageai",
      "packages/opentelemetry-instrumentation-watsonx/opentelemetry/instrumentation/watsonx",
      "packages/opentelemetry-instrumentation-weaviate/opentelemetry/instrumentation/weaviate",
      "packages/opentelemetry-instrumentation-writer/opentelemetry/instrumentation/writer",
      "packages/opentelemetry-semantic-conventions-ai/opentelemetry/semconv/ai",
      "packages/sample-app/sample_app",
      "packages/traceloop-sdk/traceloop_sdk"
    ],
    "docs": [
      "README.md",
      "CONTRIBUTING.md",
      "CLAUDE.md",
      "packages/*/README.md"
    ],
    "examples": [
      "packages/sample-app/sample_app"
    ],
    "tests": [
      "packages/*/tests"
    ],
    "configs": [
      "package.json",
      "nx.json",
      "packages/*/pyproject.toml",
      "packages/*/project.json",
      ".github/workflows/ci.yml"
    ],
    "scripts": [
      "scripts/build-release.sh",
      "scripts/generate-models.sh",
      "scripts/codegen/generate_evaluator_models.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If a current checkout is dirty in source files that affect packages, tests, examples, or scripts, refresh before relying on detailed API or test guidance.
- If any package `pyproject.toml` changes entry points, optional dependencies, source roots, or version constraints, refresh.
- If upstream OpenTelemetry GenAI semantic conventions change and tests begin failing around `opentelemetry.semconv_ai`, refresh the semantic-conventions sub-skill.
- If new instrumentation packages or sample-app examples are added, refresh the instrumentation catalog and repo-development package inventory.
