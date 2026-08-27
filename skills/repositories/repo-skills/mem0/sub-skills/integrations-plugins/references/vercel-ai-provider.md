# Vercel AI SDK Provider

Use this reference when wiring Mem0 into Vercel AI SDK, Next.js/React chat routes, or AI SDK model calls.

## Current Package Facts

- Package: `@mem0/vercel-ai-provider` version `3.0.0`.
- Runtime: Node.js `>=18`; package manager examples should use the host app’s package manager.
- AI SDK compatibility: Vercel AI SDK v6 (`ai` `^6.0.199`) and `@ai-sdk/provider` v3 (`ProviderV3` / `LanguageModelV3`).
- Supported upstream provider packages in the integration: OpenAI, Anthropic, Google, Groq, and Cohere at AI SDK provider v3 versions.
- Public exports: `createMem0`, `mem0`, `addMemories`, `retrieveMemories`, `searchMemories`, `getMemories`, and provider/config TypeScript types.
- Mem0 API endpoints used by utilities: `POST /v3/memories/search/` and `POST /v3/memories/add/` against `https://api.mem0.ai` unless `host` is supplied.

## Install Pattern

```bash
npm install @mem0/vercel-ai-provider ai@^6 @ai-sdk/openai@^3
```

Use the corresponding provider package for the selected upstream model, for example `@ai-sdk/anthropic`, `@ai-sdk/google`, `@ai-sdk/groq`, or `@ai-sdk/cohere`.

Required environment variables normally include:

- `MEM0_API_KEY` for Mem0 Platform memory calls.
- The upstream model key such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`, `GROQ_API_KEY`, or `COHERE_API_KEY`.

## Wrapped Provider Pattern

`createMem0` returns an AI SDK provider. The returned provider can be called as `mem0(modelId, settings)`, `mem0.chat(modelId, settings)`, `mem0.completion(modelId, settings)`, or `mem0.languageModel(modelId, settings)`.

```ts
import { generateText } from "ai";
import { createMem0 } from "@mem0/vercel-ai-provider";

const mem0 = createMem0({
  provider: "openai",
  mem0ApiKey: process.env.MEM0_API_KEY,
  apiKey: process.env.OPENAI_API_KEY,
  mem0Config: { user_id: "alice", app_id: "support-app" },
});

const result = await generateText({
  model: mem0("gpt-5-mini", { user_id: "alice" }),
  prompt: "Recommend a good car for me",
});
```

Key behavior:

1. The wrapped model searches Mem0 for relevant memories before generation.
2. If memories are found, it prepends a system message containing memory context.
3. It calls the selected upstream AI SDK provider.
4. It writes the prompt messages back to Mem0; in current v3 source this add path is awaited internally but errors are caught and logged so generation can still continue.
5. For non-streaming generation, memory results may be attached as a source titled `Mem0 Memories` with `providerMetadata.mem0.memories`.

## Standalone Utility Pattern

Use standalone utilities when the app already has its model provider and needs explicit control over retrieve/store timing.

```ts
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";
import { addMemories, retrieveMemories } from "@mem0/vercel-ai-provider";

const userId = "alice";
const prompt = "What should I cook tonight?";
const memorySystem = await retrieveMemories(prompt, { user_id: userId });

const result = await generateText({
  model: openai("gpt-5-mini"),
  prompt,
  system: memorySystem,
});

await addMemories(
  [
    { role: "user", content: prompt },
    { role: "assistant", content: result.text },
  ],
  { user_id: userId }
);
```

Utility differences:

- `retrieveMemories(prompt, config)` returns a formatted system prompt string, or an empty string when no memories match.
- `getMemories(prompt, config)` returns a normalized array of memory objects.
- `searchMemories(prompt, config)` returns the raw search response or an empty array on caught error.
- `addMemories(messages, config)` stores string, structured text, image URL, Markdown URL, PDF URL, or AI SDK file-style prompt parts after conversion to Mem0 message format.

## Scope and Filters

Use a stable entity scope on every workflow:

- `user_id`: primary user identity and most common scope.
- `app_id`: application/project boundary.
- `agent_id`: specific agent identity.
- `run_id`: conversation/session boundary.

For search, the provider converts top-level `user_id`, `app_id`, `agent_id`, and `run_id` into the `filters` object sent to `/v3/memories/search/`. If `config.filters` is also present, those filters are merged first and entity fields override matching keys. For add, entity fields remain top-level in the body sent to `/v3/memories/add/`.

When refactoring a route, preserve the old tenant/user value exactly. Do not replace a per-user `user_id` with a constant demo ID.

## Route Refactor Checklist

Use this checklist when moving a route from standalone utilities to `createMem0`:

- Keep the route’s existing auth-derived user identifier and pass it as `user_id` in per-call settings or `mem0Config`.
- Keep upstream provider configuration separate from Mem0 configuration: `apiKey`/`config` for the model provider, `mem0ApiKey`/`mem0Config` for Mem0.
- Use `streamText` or `generateText` exactly as the app already does; only replace the `model` expression with `mem0(modelId, settings)`.
- If the route previously called `addMemories` after the response, remove duplicate writes or keep only intentionally different metadata writes.
- Preserve tool definitions, structured output settings, and message arrays. The provider forwards V3 call options to the upstream model after memory processing.
- Avoid client-side exposure of `MEM0_API_KEY` and provider API keys. Keep provider calls in server routes or trusted server actions.

## Static Check

Run the bundled read-only checker on files or directories before editing:

```bash
node scripts/check_vercel_mem0_usage.mjs app/api/chat/route.ts src/server/chat.ts
```

Useful signals:

- Missing `@mem0/vercel-ai-provider` import.
- `createMem0` imported but not called.
- Wrapped model used without a nearby `user_id`, `agent_id`, `app_id`, or `run_id`.
- Standalone utility calls without scope.
- Literal `m0-` API keys in source.
- AI SDK v5/v4 hints that may conflict with provider v3.0.0.

## Common Pitfalls

- AI SDK v5 examples from older apps may not match provider v3.0.0. Upgrade the `ai` package and provider packages together.
- `retrieveMemories` is a formatted string for `system`; use `getMemories` for raw arrays.
- Missing `MEM0_API_KEY` causes standalone utilities and wrapped memory operations to fail even when the upstream model key is valid.
- Empty retrieval usually means missing/incorrect `user_id` scope, too-strict `threshold`, no prior memories, or a different `app_id`/`agent_id` than the write path.
- Browser bundles must not include Mem0 Platform API keys. Keep memory calls server-side.
