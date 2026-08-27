# Custom Graph Troubleshooting

## Workflow file does not import

Likely causes:

- File is not JSON or not a ComfyUI workflow/API graph object.
- Required graph fields were exported in an unsupported format.
- Node IDs/links are malformed.

Recovery:

```bash
python sub-skills/custom-graphs/scripts/inspect_custom_workflow.py workflow.json
```

Check whether the script detects `api` or `ui` format and reports node/link
warnings.

## No UI controls appear

Likely causes:

- The graph has no `ETN_Parameter`, `ETN_KritaStyle`, `ETN_KritaImageLayer`, or
  `ETN_KritaMaskLayer` placeholders.
- `ETN_Parameter` nodes use `auto` or unsupported `type` values.
- Choice parameters are not connected to a node/input with known options.

Recovery:

- Inspect placeholder list and parameter list.
- Rename/group parameters using `N. Group/M. Name` style if ordering matters.
- Use recognized parameter types from `custom-graph-reference.md`.

## Validation warning: multiple Style & Prompt nodes

The Graph workspace allows one `ETN_KritaStyleAndPrompt` node. Remove or merge
extra nodes. If multiple prompts are needed, expose additional text/prompt
parameters and combine them in normal ComfyUI nodes.

## Output not returned to Krita

Likely causes:

- Missing `ETN_KritaOutput` node.
- Output node is not connected to the image path the user expects.
- Graph returns text instead of images.
- Live/animation mode changes how results are handled.

Recovery:

- Inspect `Outputs` in the bundled script.
- Ensure the final image path connects to `ETN_KritaOutput.images`.
- For text outputs, inspect client text output handling rather than image
  history.

## Runtime says ETN node class missing

Static graph inspection can pass even when ComfyUI lacks required node packages.
For live execution, route to `server-resources` and install/update the External
Tooling Nodes package and other required custom nodes in the ComfyUI runtime.

## Image or mask placeholder gives wrong data

Route to `document-image-state` and inspect layer selection, mask bounds,
selection context, and image conversion. The Graph workspace only requests the
placeholder data; document/layer APIs provide the actual image/mask.
