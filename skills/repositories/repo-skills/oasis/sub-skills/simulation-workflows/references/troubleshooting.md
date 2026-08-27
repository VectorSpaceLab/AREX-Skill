# Simulation Workflow Troubleshooting

## Missing `OPENAI_API_KEY` During `SocialAgent` Construction

**Symptom:** constructing `SocialAgent(model=None)` fails before any provider
call, often with an OpenAI credential error.

**Cause:** current CAMEL behavior may create a default OpenAI backend when
`model=None`.

**Recovery:**

- For a no-LLM manual smoke, set a non-secret placeholder key only for that
  process and do not execute `LLMAction()`.
- For real LLM steps, set valid provider credentials or pass an explicit model
  backend such as OpenAI, VLLM/local server, DeepSeek, or another CAMEL backend.
- If credentials or budget are unavailable, run
  [the manual smoke](../scripts/oasis_manual_smoke.py) instead.

## Real `LLMAction` Fails Or Costs Too Much

**Symptoms:** authentication errors, rate limits, quota errors, tool-call
failures, slow local-server responses, or unexpectedly high token usage.

**Recovery:**

- Verify credentials and model selection in [model-backends.md](model-backends.md).
- Confirm the model supports tool/function calling.
- Activate a small subset with `env.agent_graph.get_agents([ids...])`.
- Lower `semaphore`.
- Replace some agents' actions with `ManualAction` or `ActionType.DO_NOTHING`.
- Stop if the user has not approved a token/cost budget.

## `database_path is required for DefaultPlatformType`

**Symptom:** `make(..., platform=DefaultPlatformType.REDDIT)` or `TWITTER`
raises a `ValueError`.

**Cause:** built-in platform presets require `database_path`.

**Recovery:** pass `database_path=str(db_path)` and set `OASIS_DB_PATH` to the
same absolute path, or construct a custom `Platform(db_path=...)` and pass that
platform object to `make(...)`.

## Forgot To Await `reset`, `step`, Or `close`

**Symptoms:** no agents are signed up, empty DB tables, pending task warnings,
`coroutine was never awaited`, or DB connection remains locked.

**Recovery:** wrap the run in `asyncio.run(main())`, call `await env.reset()`
before the first step, `await env.step(actions)` for every step, and
`await env.close()` in `finally`.

## Stale `EnvAction`, `SingleAction`, `action`, Or `args` Examples

**Symptoms:** `ImportError` for `EnvAction`/`SingleAction`, `TypeError` for
unexpected `ManualAction` keywords, or manual actions are not executed.

**Cause:** some docs still show an older environment-action interface. Current
source uses `ManualAction(action_type=..., action_args={...})` and
`LLMAction()` values inside a dict keyed by `SocialAgent` objects.

**Recovery:** use the contract in
[environment-lifecycle.md](environment-lifecycle.md#current-envstep-action-mapping).
For detailed action arguments, route to `platform-actions`.

## Action Mapping Keyed By IDs Instead Of Agents

**Symptoms:** `AttributeError` such as an integer lacking
`perform_action_by_data`, or no expected side effect in the DB.

**Cause:** `env.step` expects keys to be `SocialAgent` instances.

**Recovery:** build keys with `env.agent_graph.get_agent(id)` or unpack
`for _, agent in env.agent_graph.get_agents([...])`.

## Ordered Actions Race Inside One Step

**Symptoms:** a comment cannot find the post it should reference, a like/follow
uses a row that does not exist yet, or results vary between runs.

**Cause:** OASIS schedules all actions in a step concurrently, including list
values for one agent.

**Recovery:** split dependent work into multiple awaited steps. Create the post
in one `await env.step(...)`; comment, like, or follow in the next.

## `OASIS_DB_PATH` And Log Side Effects

**Symptoms:** environment prompts read a different DB than the platform writes,
logs appear in an unexpected `./log` directory, or a cleanup script removes the
wrong DB.

**Recovery:** set `OASIS_DB_PATH` to the absolute simulation DB path before
reset/steps. Run smoke tests from a disposable working directory if you want to
contain OASIS log files.

## Database Locked After Failure

**Symptoms:** SQLite reports `database is locked`, or a later run cannot delete
or overwrite the DB.

**Cause:** `env.close()` did not run, an exception interrupted the platform
loop, or another process still has the DB open.

**Recovery:** close every environment in `finally`, close any SQLite cursors and
connections used for inspection, stop leftover simulation processes, and retry
with a fresh DB path if needed.

## Twitter Default Or Recommendation Path Pulls Optional Dependencies

**Symptoms:** imports or steps fail around sentence-transformers, embedding
models, local model cache, CUDA, or network access.

**Cause:** model-heavy recommendation paths are optional for core manual
lifecycle validation.

**Recovery:** use the Reddit manual smoke or a custom `Platform` with a simpler
recsys setting for no-credential validation. Route recsys internals and DB trace
diagnostics to `platform-actions`.
