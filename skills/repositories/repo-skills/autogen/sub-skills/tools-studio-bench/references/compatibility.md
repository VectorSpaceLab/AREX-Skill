# Compatibility and Version Boundaries

Use this reference before installing AutoGen tooling into an existing environment. The safest default is to keep modern AutoGen 0.7.x application libraries separate from older tool packages whose metadata pins lower ranges.

## Verified Installed Facts

The inspected environment for this skill successfully imported:

- `autogen-core==0.7.5`
- `autogen-agentchat==0.7.5`
- `autogen-ext==0.7.5`
- `pyautogen==0.10.0`
- `agbench==0.0.1a1`

`agbench --help` also worked. Magentic-One CLI and AutoGen Studio were not treated as same-environment installs because their metadata conflicts with 0.7.x library versions.

## Package Matrix

| Package | Python range | Key AutoGen dependency boundary | Practical guidance |
| --- | --- | --- | --- |
| `autogen-core` / `autogen-agentchat` / `autogen-ext` 0.7.x | Python 3.10+ from root project guidance | Modern maintenance-line libraries | Use for existing 0.7.x application maintenance. |
| `pyautogen==0.10.0` | `>=3.10` | Depends on `autogen-agentchat>=0.6.4` | Proxy package for current AgentChat; not the old 0.2 API. |
| `pyautogen~=0.2.0` | Legacy package line | Old 0.2-style API | Pin only for legacy 0.2 code that cannot migrate yet. |
| `agbench==0.0.1a1` | `>=3.8,<3.13` | No strict modern AutoGen library pin in package metadata | Help/import checks can coexist; benchmark scenarios may target older AutoGen assumptions. |
| `autogenstudio` metadata in repo | `>=3.9` | `autogen-core>=0.4.9.2,<0.7`, `autogen-agentchat>=0.4.9.2,<0.7`, `autogen-ext[...]>=0.4.2,<0.7` | Prefer a separate Studio environment; do not force into 0.7.x env. |
| `magentic-one-cli==0.2.4` metadata in repo | `>=3.10` | `autogen-agentchat>=0.4.4,<0.5`, `autogen-ext[...]>=0.4.4,<0.5` | Requires a separate older AutoGen environment from 0.7.x. |

## Conflict Diagnosis

Symptoms:

- `pip` reports unsatisfiable constraints involving `autogen-agentchat`, `autogen-core`, or `autogen-ext`.
- Installing Studio or `magentic-one-cli` downgrades libraries and breaks 0.7.x application imports.
- `m1` imports fail because expected `autogen_ext.teams.magentic_one` or executor extras do not match the installed package line.
- `autogenstudio` imports fail after installing modern 0.7.x packages because Studio expects `<0.7` APIs.

Diagnosis commands:

```bash
python -m pip check
python -m pip show autogen-core autogen-agentchat autogen-ext pyautogen agbench autogenstudio magentic-one-cli
python - <<'PY'
import importlib.metadata as m
for name in ['autogen-core','autogen-agentchat','autogen-ext','pyautogen','agbench','autogenstudio','magentic-one-cli']:
    try:
        print(name, m.version(name))
        for req in m.requires(name) or []:
            if 'autogen' in req.lower():
                print('  ', req)
    except m.PackageNotFoundError:
        print(name, 'not installed')
PY
```

## Environment Strategy

- Modern app maintenance: keep `autogen-core`, `autogen-agentchat`, and `autogen-ext` aligned on the same modern version line.
- Studio usage: create a separate environment matching Studio metadata and start with `autogenstudio --help` before launching UI.
- Magentic-One CLI usage: create a separate environment matching `magentic-one-cli` metadata and start with `m1 --help` / `m1 --sample-config` before any task execution.
- AG Bench planning: help/lint/tabulate can be inspected first; real runs need explicit Docker, credential, network, and output-directory decisions.
- Legacy pyautogen code: decide whether to pin `pyautogen~=0.2.0` or migrate to `autogen_agentchat` APIs.

## Maintenance-Mode Decision

When a user is starting a new multi-agent project, recommend Microsoft Agent Framework instead of AutoGen tooling. When the user is maintaining existing AutoGen code, keep changes narrow, version-aware, and reversible.
