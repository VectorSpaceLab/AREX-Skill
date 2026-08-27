# Configuration and Registry Troubleshooting

Use this table to turn MMEngine config or registry symptoms into concrete checks and fixes.

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `KeyError: cfg or default_args must contain the key "type"` | A registry build config lacks `type`, and `default_args` also lacks `type`. | Add `type='RegisteredName'` to the config dict or provide `default_args=dict(type='RegisteredName')`. |
| `KeyError: X is not in the scope::registry registry` | The class/function was not registered, was registered under another name, or the wrong registry/scope is used. | Import the module, add `custom_imports`, verify the registry owner, and check aliases from `register_module(name=...)`. |
| `type must be a str or valid type` | `type` is an integer, dict, list, or other non-callable object. | Use a registered string key or a callable class/function in Python-created configs. |
| `registry must be a mmengine.Registry object` | `build_from_cfg` received a string, module, or wrong object for `registry`. | Pass the actual `Registry` instance, such as `MODELS`, not its name. |
| Constructor `TypeError` for unexpected keyword | Config contains keys the target constructor does not accept. | Compare config keys with the class/function signature; remove or route nested dicts to the correct child builder. |
| Duplicate registration error like `Name is already registered` | Same name registered twice in one registry, often from repeated imports or copied class names. | Rename with `register_module(name='Alias')`, reset the interactive process, or use `force=True` only for deliberate replacement. |
| Custom class not found even though code exists | The file defining `@REGISTRY.register_module()` was never imported. | Add `custom_imports = dict(imports=['package.module'], allow_failed_imports=False)` or import the module before building. |
| `Failed to import custom modules` | `custom_imports` module path is wrong or imports missing optional dependencies. | Fix the import path, install the dependency, or isolate optional imports; keep `allow_failed_imports=False` while debugging. |
| Scope-qualified `mmdet.X` not found | Target package registry was not imported or is not installed. | Confirm package import, add `custom_imports`, and check whether `mmdet.registry` or module locations register the target. |
| Sibling package item not found from root registry | Default scope still points at `mmengine` or another package. | Use `type='sibling.Item'`, put `_scope_='sibling'` in the config dict being built, or call `init_default_scope('sibling')` before root-registry builds. |
| `_scope_` seems ignored | `_scope_` is placed outside the dict passed to `Registry.build`/`build_from_cfg`. | Move `_scope_` into the same dict that contains `type`, or the subtree whose builder will receive it. |
| Config inheritance keeps old optimizer keys | Dict overrides merge recursively by default. | Add `_delete_=True` to the replacement dict when inherited keys should be removed. |
| List override fails or updates the wrong field | Dotted override key does not target a valid list index, or `allow_list_keys=False`. | Use numeric path parts such as `pipeline.0.type`; ensure the list index exists and `allow_list_keys=True`. |
| CLI list override parses as a string | Missing shell quoting around brackets or spaces in the override. | Quote list/tuple values, for example `model.in_channels="[1,1,1]"`; avoid spaces inside list strings for `DictAction`. |
| YAML/JSON config fails to parse | File format syntax error or Python-only syntax used in YAML/JSON. | Validate the file as YAML/JSON; keep Python expressions only in `.py` configs. |
| Python config parse imports optional packages unexpectedly | Pure Python config imports are executed or lazy import was disabled. | Use text-style configs for portable parsing, or set/inspect `lazy_import` behavior and avoid building imported objects during inspection. |
| `{{_base_.x}}` reference cannot be modified in Python syntax | Text-style base variable references are substituted, not general mutable Python expressions. | For Python configs, use `_base_.x` mutation patterns; otherwise assign a full replacement. |
| Environment variable override affects derived fields unexpectedly | `{{$ENV:default}}` substitution happens before parsing and before derived assignments. | Use environment variables when derived values should change together; use `merge_from_dict` when only the target key should change. |
| Predefined variable creates absolute local path in output | `{{fileDirname}}` expands to the config file directory. | Prefer relative or project-configurable paths in public configs; do not bake private checkout paths into shared config text. |
| Dumped config loses `_base_` | `Config.dump` emits a standalone resolved config. | This is expected; keep original source config if inheritance structure matters. |

## Debugging Playbooks

### Parse Before Building

1. Load the file with `Config.fromfile` or use `scripts/inspect_config.py`.
2. Print top-level keys and the specific subtree to be built.
3. Apply CLI-style overrides with `merge_from_dict` and inspect the result.
4. Only then call the relevant registry builder.

### Missing Registry Type

1. Confirm the config dict has `type` at the level being built.
2. Confirm the expected registry owner: model, hook, dataset, transform, metric, optimizer, runner, visualizer, or function.
3. Confirm the module file was imported by `locations`, manual import, or `custom_imports`.
4. Check whether the registered name is the class name or an alias.
5. If cross-library, add a scope prefix or `_scope_`, and confirm default scope when a root builder is used.

### `_base_` plus Environment Variables plus List Override

1. Load the config with environment variables set exactly as intended.
2. Inspect derived fields that depend on the environment variable.
3. Apply list overrides with numeric dotted keys, for example `train_pipeline.0.type`.
4. If a list item is a dict inherited from a base, override only the nested keys you need; if replacing a dict completely, use `_delete_=True` in a config file rather than a CLI scalar.
5. Dump to a string and verify there are no private absolute paths before sharing.

### Custom Registry Item under a Sibling Scope

1. Import the sibling package's registry and module definitions, or add `custom_imports`.
2. Build with a scope-qualified type such as `sibling.CustomItem` to prove registration is visible.
3. If many nested items belong to that sibling, put `_scope_='sibling'` in the dict passed to the registry build.
4. If a root or parent builder constructs the item, call `init_default_scope('sibling')` before the build or ensure the runner/default runtime sets the correct default scope.
5. If errors mention the current scope rather than the sibling, the scope switch did not reach the builder.

## Safe Script Check

Use the bundled parser when the question is about syntax, inheritance, variables, or dotted overrides and not about constructing live objects:

```bash
python scripts/inspect_config.py config.py --cfg-options optimizer.lr=0.001 pipeline.0.type=LoadImageFromFile --dump
```

The helper exits nonzero on parse or merge errors so it can be used as a quick validation gate before touching training, datasets, or model code.
