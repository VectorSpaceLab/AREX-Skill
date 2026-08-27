# Mimic and SkillGen Workflows

## Mimic overview

Mimic generates additional demonstrations from a small set of human demonstrations by splitting each episode into subtasks and replaying or transforming those segments under new spatial configurations.

## SkillGen-specific requirements

SkillGen adds a stricter annotation contract on top of Mimic:

- Subtask start signals are required.
- Subtask termination signals are required.
- Each subtask should define a reference object when the motion is object-relative.
- The dataset must already be annotated before generation starts.

## Common phases

1. Collect a source dataset from teleoperation.
2. Annotate the dataset with subtask signals.
3. Run a synthetic-generation pass to create more demonstrations.
4. Optionally use SkillGen to plan motions between annotated subtask segments.
5. Export the result for policy training or visual augmentation.

## Signal semantics

- `subtask_term_signal` marks the completion of a subtask.
- `subtask_start_signal` marks the beginning of a subtask.
- A subtask is the contiguous segment between those boundary transitions.

## Practical notes

- Manual annotation is expected for SkillGen-style workflows.
- Automatic annotation is not a substitute when the task requires explicit start signals.
- The source environment must implement the success and subtask signal APIs expected by the Mimic pipeline.
- SkillGen planning is a GPU-heavy optional enhancement, not a baseline requirement for the whole repo.

## Optional dependencies

Basic Mimic support depends on the package extras and Python-side data handling libraries. Some paths are Linux-only and some require the optional teleop packages or cuRobo-style motion planning dependencies.

## Future-agent guidance

When a user asks for a data-generation workflow, start by identifying whether they need only teleoperation capture, annotation, synthetic generation, or SkillGen planning. Those are different operator intents even though they share the same HDF5 dataset family.
