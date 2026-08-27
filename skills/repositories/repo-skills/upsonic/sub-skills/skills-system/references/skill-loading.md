# Skill Loading Reference

## Loader families

| Loader | Purpose |
| --- | --- |
| `LocalSkills(path, validate=True, version_constraint=None)` | Load skill directories from a local path. |
| `InlineSkills(skills, validate=False)` | Load skill objects already in memory. |
| `BuiltinSkills(skills=None, validate=False)` | Load the packaged built-in skill library. |
| `GitHubSkills(repo, branch='main', path='skills/', token=None, skills=None, **kwargs)` | Load skills from a GitHub repo. |
| `URLSkills(url, headers=None, max_size=..., **kwargs)` | Load skills from a remote URL. |

## Skills container behavior

- `Skills(loaders, strict_deps=False, cache_ttl=None, on_load=None, on_script_execute=None, on_reference_access=None, auto_select=False, max_skills=5, embedding_provider=None, policy=None)`.
- Later loaders override earlier loaders when names collide.
- The container exposes load, lookup, reload, and selection helpers plus hooks for reference/script use.

## What to remember

- A future agent should be able to load a skill tree without knowing the repo that produced it.
- Keep skill names canonical, lowercase, and hyphenated.
