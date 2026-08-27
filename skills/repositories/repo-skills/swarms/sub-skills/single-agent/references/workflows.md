# Single-agent workflows

## 1. Minimal agent

Use this when the user only needs one model call with a clear instruction.

```python
from swarms import Agent

agent = Agent(
    agent_name="Analyst",
    model_name="gpt-5.4",
    max_loops=1,
    print_on=False,
)
result = agent.run("Summarize the repository in one paragraph.")
```

## 2. Skills-enabled agent

Use a `skills_dir` when the user has local `SKILL.md` folders that should be loaded into the system prompt.

```python
from swarms import Agent

agent = Agent(
    agent_name="SkillAgent",
    model_name="gpt-5.4",
    skills_dir="./skills",
    max_loops=1,
)
```

If the task is specific, let the skill manager pick only the relevant skills. If the task is broad, load the full skill set.

## 3. Memory-backed agent

If the user wants long-lived memory, keep the agent name stable and set a workspace directory before running.

- `WORKSPACE_DIR` determines where the memory tree is stored.
- `persistent_memory` controls whether `MEMORY.md` is read and written.
- Use `Conversation` only when you need direct transcript control.

## 4. Prompt-caching or provider-sensitive agent

Use prompt caching only when the provider accepts the chosen cache parameters.

- Start with `prompt_caching=False`.
- Add `cache_config` only if the target provider supports it.
- If you see provider parameter errors, strip unsupported options before retrying.

## 5. Marketplace prompt agent

When the user names a marketplace prompt id or wants a curated prompt, set `marketplace_prompt_id` rather than copying text by hand.

- Requires `SWARMS_API_KEY`.
- The handler can back-fill the agent name and description.
- Treat marketplace fetch failures as auth or prompt-id problems first.

## 6. Live multimodal agent

Use `img=` or `imgs=` only when the selected model actually supports vision input.

- A successful constructor does not guarantee multimodal support.
- If the provider rejects the request, check the model family and vision support before changing the prompt.

## 7. Offline smoke workflow

Before asking a user to pay for or rely on a model call, prefer a local check:

1. Import `Agent`.
2. Build a minimal instance.
3. Confirm skills, memory, or artifact helpers work against a temp fixture.
4. Escalate to a live provider only if the task really needs it.

## Common gotchas

- `persistent_memory=False` by default in the installed package, so no on-disk memory appears unless the caller opts in.
- `max_loops="auto"` changes execution style and may expose tool or prompt constraints that a fixed loop count hides.
- `skills_dir` must point at a directory of subdirectories, not at a single `SKILL.md` file.
- `WORKSPACE_DIR` missing or unstable is a common source of surprise file locations.
