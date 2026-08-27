# Credentialed generation utilities

RoboTwin includes several optional generation helpers for task-language, object-language, and robot-task code. Treat them as maintainer utilities, not the default workflow. They can call hosted LLM APIs, mutate files, run simulation, and write generated scratch code.

## Default policy

- Prefer deterministic/manual authoring: edit task JSON, object-description JSON, task classes, and task configs directly.
- Use this sub-skill's bundled scripts for safe config scaffolding and local episode-instruction expansion.
- Do not call any hosted model API unless the user explicitly requests it, understands the cost/privacy implications, and provides their own credentials.
- Do not paste private keys into source files. Use environment variables or a user-approved secret manager.
- Review and test all generated outputs before promoting them into canonical task files.

## Task instruction generator

The task instruction generator uses an Azure-backed helper module.

What it does:

1. Reads a task instruction JSON file containing `full_description`, `schema`, and `preference`.
2. Prompts a hosted model for alternative natural-language instructions.
3. Appends generated instructions to the same task JSON file.
4. Splits each batch by appending the first two generated instructions to `unseen` and the remaining generated instructions to `seen`.

Operational constraints:

- The Azure helper requires an `AZURE_API_KEY` environment variable and raises immediately when it is not set.
- The generator expects the requested instruction count to be divisible by 12, because it loops in batches of 12.
- It mutates `description/task_instruction/<task_name>.json` in place.
- It relies on prompt files and Pydantic schemas; validate JSON output before accepting it.

Safer alternative: manually author `seen` and `unseen` arrays, then use the bundled deterministic episode expander to test placeholder replacement.

## Object description generator

The object description generator also uses the Azure-backed helper. It renders or loads object images from GLB assets, asks a hosted vision/text model for object phrases, and writes object-description JSON.

Operational constraints:

- It requires object assets and rendering/image dependencies.
- It may cache PNG previews while generating descriptions.
- It writes JSON under `description/objects_description/<object_folder>/`.
- It uses generated phrases for `seen` and `unseen` splits; review for concrete, manipulation-relevant wording and remove hallucinated properties.

Safer alternative: write object-description JSON manually from the known asset identity and visible properties.

## Generated task code utilities

The `code_gen` utilities are intended to draft `play_once()` logic for an existing or planned task. They are not a substitute for understanding RoboTwin task mechanics.

Observed components:

- API prompt material describes world coordinates, poses, `ArmTag`, functional points, and high-level motion helpers.
- Task metadata dictionaries describe known tasks, actor lists, and expected behavior.
- A generator writes `envs_gen/gpt_<task_name>.py` and may iterate after simulation failures.
- A tester imports generated task classes, creates or loads task configs, runs multiple simulation episodes, and records success/error signals.
- A multimodal branch can add observation points, save camera images, and call a hosted vision model for feedback.

Risk profile:

- `gpt_agent.py` contains placeholder API-key variables for OpenAI-compatible providers. They must be configured by the user; they are not safe defaults.
- `observation_agent.py` calls a hosted vision API and reads generated camera images.
- Task generation can run SAPIEN simulation, create logs, write `envs_gen/`, and consume GPU/render resources.
- Prompts explicitly warn that common failures include wrong `pre_dis_axis`, functional point, `pre_dis`/`dis`, and `constrain` values.
- Generated code may slice text out of Markdown fences; malformed model output can create syntactically invalid files.

Safe handling procedure:

1. Ask whether the user wants manual authoring or LLM-assisted drafting.
2. If LLM-assisted, confirm provider, credential source, budget, privacy constraints, simulation backend availability, and output directory before running anything.
3. Keep generated code in `envs_gen/` until reviewed.
4. Inspect imports, class name, `play_once()` body, arm choices, object/pose references, gripper states, functional point IDs, and success logic.
5. Run cheap syntax and placeholder checks before simulator episodes.
6. Only after review and simulator success should a maintainer copy or adapt logic into `envs/<task_name>.py`.
7. Re-run deterministic language expansion because generated task code may change `self.info["info"]` keys.

## When to route elsewhere

- For motion helper semantics, functional points, SAPIEN actors, planner behavior, render smoke tests, and backend troubleshooting, use `simulation-core`.
- For data collection after a task exists, instruction embedding inside trajectories, HDF5 layout, downloads, and format conversion, use `data-pipeline`.
- For policy evaluation with XPolicyLab, use the policy-evaluation sub-skill if available.
