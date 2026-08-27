# Python SDK testing and maintenance

This reference collects the Python-idiomatic rules that matter most when a future agent edits or verifies the SDK.

## Coding conventions to preserve

- Python floor is 3.10.
- Use `X | None` and `X | Y`; do not reintroduce `Optional[...]` or `Union[...]` in new code.
- Choose the data shape by role: `TypedDict` for wire/config payloads, `dataclass` for runtime objects, and Pydantic only when the model reads or writes the schema.
- Keep public package surfaces explicit with `__all__`.
- Keep heavy provider modules lazy-loaded.
- Use Protocols for extensible call shapes instead of `Callable` when the contract may grow new keyword arguments.
- Use Google-style docstrings, and include a `Raises:` section when a public function raises as part of its contract.
- Keep logging structured: `field=<%s>, field=<%s> | lowercase message`.
- Use `%s` interpolation in logs, not f-strings.
- Name every variable for its content, including short-lived loop and exception bindings.
- Follow the evergreen-comment rule: state only what cannot be inferred from the code, and keep comments brief.
- Translate vendor exceptions at provider boundaries instead of letting raw SDK errors escape.

## Testing conventions to preserve

- Unit tests mirror `src/strands/` under `tests/strands/`.
- Integration tests live in `tests_integ/` and usually need credentials or external services.
- Async tests must carry `@pytest.mark.asyncio` in strict asyncio mode.
- Prefer shared fixtures from `tests/fixtures/` over hand-rolled doubles.
- Use `tru_...` / `exp_...` naming for assertion pairs when you control the shape.
- Assert the whole object when the SDK controls the shape; assert only the relevant fields when the type is externally evolving.
- Prefer extending an existing test over creating a duplicate scenario.
- Keep test names focused on the behavior under test, not on the module name.

## High-value test modules

| Area | Best starting test module |
| --- | --- |
| Agent loop, context, checkpointing, hooks, concurrency, sessions, memory wiring | `tests/strands/agent/test_agent.py` |
| `@tool`, schema generation, context injection, async generators, result formatting | `tests/strands/tools/test_decorator.py` |
| Memory manager, search/add tools, extraction, injection, store scoping | `tests/strands/memory/test_memory_manager.py` |
| MCP client lifecycle, transport handling, progress/cancellation, task support | `tests/strands/tools/mcp/test_mcp_client.py` and `tests/strands/tools/mcp/test_mcp_client_tasks.py` |
| Base model token counting and utilization | `tests/strands/models/test_model.py` |
| Provider-specific contracts | the matching `tests/strands/models/test_<provider>.py` file |
| Session persistence | `tests/strands/session/*` |
| Sandbox backends | `tests/strands/sandbox/*` |
| Telemetry and tracing | `tests/strands/telemetry/*` |
| Multi-agent orchestration | `tests/strands/multiagent/*` |

## Common verification commands

Run the following from the repository root unless a command says otherwise:

- `scripts/python-core-check.sh`
- `scripts/python-core-check.sh --pytest`
- `cd strands-py && pytest tests/strands/tools/test_decorator.py -q`
- `cd strands-py && pytest tests/strands/agent/test_agent.py -q`
- `cd strands-py && pytest tests/strands/memory/test_memory_manager.py -q`
- `cd strands-py && pytest tests/strands/tools/mcp/test_mcp_client_tasks.py -q`
- `cd strands-py && hatch fmt --formatter`
- `cd strands-py && hatch fmt --linter`
- `cd strands-py && hatch test`

## Maintenance checklist

- Update `pyproject.toml` extras when a public provider or backend dependency changes.
- Update `__all__` when a public symbol moves or is newly exported.
- Keep `strands.models.__getattr__` aligned with any new provider module.
- Keep `docs/HOOKS.md` in mind before adding or renaming hook events.
- Treat provider-backed integrations, live network checks, and AWS-backed tests as optional unless the task explicitly asks for them.
- Keep docs-site authoring and TypeScript SDK work in their own sub-skills.
- When changing serialization or config contracts, add a focused regression test before widening the refactor.
