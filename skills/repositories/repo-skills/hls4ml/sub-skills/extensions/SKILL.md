---
name: extensions
description: "Custom hls4ml layer, parser handler, template, optimizer-flow, and
  backend/writer plugin workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Extensions

Use this sub-skill for extension tasks around hls4ml internals:

- custom Keras, PyTorch, or ONNX layer support
- IR layer classes and attribute/weight wiring
- backend templates and custom source registration
- optimizer passes, flows, and pass membership checks
- external backend or writer plugins
- diagnosing missing handlers, plugin discovery, or flow wiring

Do not use this sub-skill for ordinary model conversion, vendor synthesis, or precision/resource tuning. Route those to the sibling frontends, backends, or analysis sub-skills.

## Operating map

1. Identify the extension surface: parser handler, IR layer, template/source, optimizer pass, or backend plugin.
2. Read the matching reference:
   - `references/extension-api.md`
   - `references/plugins.md`
   - `references/custom-layer-checklist.md`
   - `references/troubleshooting.md`
3. Run `scripts/inspect_plugins.py` when you need a safe, non-loading discovery probe.
4. If you add behavior, pair it with a focused test that proves registration, flow reachability, and a small compile/predict smoke when appropriate.

## Fast routing

- Custom layer implementation or parser handler -> `references/extension-api.md`
- Plugin or backend visibility problem -> `references/plugins.md`
- Implementation checklist and test planning -> `references/custom-layer-checklist.md`
- Missing source, pass, or registration failure -> `references/troubleshooting.md`

## Safe inspection

```bash
python scripts/inspect_plugins.py
```

The script only reports discovery metadata. It does not import plugin modules.
