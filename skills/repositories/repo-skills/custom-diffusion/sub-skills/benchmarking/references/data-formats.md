# Data formats

## Evaluation-time layout

A benchmark run is valid only when `sample_root/` has the following structure:

- `samples/` — exactly `numgen` PNG files.
  - The source evaluator counts `samples/*.png` when it checks the run.
  - Keep this directory PNG-only so the counted sample set and the loaded sample set stay aligned.
- `prompts.json` — a JSON object mapping each sample filename stem to the exact prompt string used for that image.
  - The evaluator does not auto-prefix prompts.
  - Every PNG stem must appear exactly once as a key.

`target_paths` is a `+`-separated list of external benchmark image directories or files.

- The first path produces `CLIP Image alignment` and `DINO Image alignment`.
- The second path produces `CLIP Image alignment1` and `DINO Image alignment1`.
- Later paths continue with `2`, `3`, and so on.

`outpkl` is a pandas pickle. If it already exists, the benchmark updates the row keyed by `sample_root`.

## Dataset JSONs

The benchmark ships two authoring catalogs:

- `dataset.json` — single-concept benchmark entries.
- `dataset_multiconcept.json` — two-concept composition entries.

### `dataset.json`

Each object contains:

- `instance_prompt`
- `class_prompt`
- `instance_data_dir`
- `class_data_dir`
- `prompt_filename`

The `instance_prompt` values use `<new1>` as the learned concept token. The `prompt_filename` field points to a prompt catalog under `prompts/` for that concept family.

### `dataset_multiconcept.json`

Each group contains two concept objects plus a compose-prompt object.

- The first concept uses `<new1>`.
- The second concept uses `<new2>`.
- The third entry contains `prompt_filename_compose`.

The concept order in the JSON is the order that fills `{0}` and `{1}` inside the compose prompt file.

## Prompt-file semantics

Prompt catalogs are line-delimited template lists.

- Single-concept prompt files usually use one unnamed placeholder: `{}`.
- Multi-concept prompt files use positional placeholders: `{0}` and `{1}`.
- The order in the dataset JSON decides which concept fills which slot.
- Blank lines should not become prompts.

These catalogs are generation inputs. Benchmark scoring reads the concrete prompt strings stored in `prompts.json`, not the template files themselves.
