# Repo provenance

## Source snapshot
| Field | Value |
| --- | --- |
| Repository | MaxKB |
| Commit | `01b21db88145278d98bf5e9bd55e6abd6b3aad43` |
| Branch | `v2` |
| Tag | `v2.10.5-lts` |
| Package version | `2.0.0` |
| Python requirement | `~=3.11.0` |

## Construction state
- Working tree was already dirty because of generated `skills/` artifacts.
- This skill was generated from repository evidence plus a prepared CPU-only Python inspection environment.
- Live DB / Redis / frontend / model-server startup was not required for construction.
- Final import was explicitly disabled.

## Verified environment facts
- Python 3.11.15 was available in the private inspection prefix.
- `PYTHONPATH=apps MAXKB_CONFIG_TYPE=ENV` allowed Django setup and import-path validation.
- The package metadata resolved as `maxkb==2.0.0`.

## Evidence roots used
- `main.py`
- `apps/`
- `ui/`
- `installer/`
- `pyproject.toml`
- `README.md`
- `README_CN.md`
- `USE-CASES.md`
- `.github/workflows/`

## Notes for future refreshes
- If the source repo changes, compare this snapshot against the current branch/tag/commit before reusing the skill.
- If route prefixes, service commands, or provider catalogs drift, refresh the corresponding sub-skill first.
