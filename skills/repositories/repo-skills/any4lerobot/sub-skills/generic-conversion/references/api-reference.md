# Generic adapter API reference

This reference is the self-contained operating contract for adapters. It is
based on the repository's `generic_converter/adapter.py`, `utils.py`, package
README, and the task metadata examples in the AgiBot and LIBERO documentation.
It describes the contract without importing or requiring those source files.

## Required class attributes

A concrete adapter subclasses `BaseAdapter` and supplies these class-level
values:

| Attribute | Expected value | Why it matters |
|---|---|---|
| `dataset_type` | Stable non-empty string | Names the dataset family and contributes to Hub tags. |
| `fps` | Positive integer-like control frequency | Passed to each temporary `LeRobotDataset.create` call. |
| `robot_type` | Stable non-empty string | Written into each temporary dataset and contributes to tags. |
| `features` | Mapping from feature key to feature specification | Defines the shape, dtype, names, and image/video metadata accepted by the writer. |
| `tags` | Optional sequence of strings; defaults to `()` | Adds adapter-specific Hub tags; order is retained and duplicates are removed later. |

The generic implementation does not perform complete schema validation for
these attributes. Treat empty names, non-positive FPS, inconsistent feature
maps, or incompatible video metadata as adapter defects and catch them before
scheduling. All tasks aggregated together must describe one compatible output
schema: the adapter's FPS, robot type, and features are shared across tasks.

## Constructor and output paths

The base constructor accepts `output_path: Path`, expands `~`, resolves it, and
stores the resulting final aggregate path as `adapter.output_path`. The
`temp_output_path` property is the sibling path whose name is the final output
name plus `_temp`:

```text
final_root              = /work/demo
adapter.temp_output_path = /work/demo_temp
```

The pipeline does not enforce that task roots are inside this staging path, so
an adapter should construct unique `ConversionTask.output_path` values beneath
it. Never point a task root at raw data, the final aggregate root, or a path
owned by another run. Existing task roots are recursively removed when their
worker starts; the existing final aggregate root is recursively removed before
aggregation.

## `ConversionTask`

`ConversionTask` is a frozen dataclass with this shape:

| Field | Type | Contract |
|---|---|---|
| `input_path` | `Path` | Raw file or directory owned by this task. The generic layer passes it through; it does not interpret the layout. |
| `output_path` | `Path` | Unique temporary LeRobot root for this task. |
| `local_repo_id` | `str` | Repo id used while constructing the temporary local dataset. It need not be a Hub destination. |
| `metadata` | `Mapping[str, Any]` | Adapter-owned task data, defaulting to an empty mapping. Use it for instructions, task ids, embodiment choices, or other source-specific values. |

A task is passed as a whole object to `load_subset(task)`. Do not change the
API to pass only `input_path`; doing so loses task metadata. Although the
container is frozen, nested metadata is not deeply immutable, so adapters
should treat it as read-only after construction. Keep `local_repo_id` and
output paths deterministic so a resume log refers to the same task plan.

## Required hooks

```text
load_tasks(self) -> list[ConversionTask]
load_subset(self, task: ConversionTask) -> Iterable[Any]
```

`load_tasks()` is called without arguments before executor selection. It should
return a finite, deterministic list. Discover source files, assign task ids,
choose metadata, and allocate unique temporary roots there. An empty list is a
hard error: `No conversion tasks found. Provide a non-empty tasks file or matching source files.`

`load_subset(task)` yields one episode at a time for the supplied task. By
default, each episode must be a sequence of frame dictionaries that the target
LeRobot dataset accepts through `add_frame`. Prefer a concrete list or another
reusable sequence when the default `get_episode_length` is used; a one-shot
generator needs an override that can report its length without consuming it.

## Optional hooks and default semantics

| Hook | Default behavior | Override when |
|---|---|---|
| `create_dataset(task)` | Imports `LeRobotDataset` and calls `create(repo_id=task.local_repo_id, root=task.output_path, fps=self.fps, robot_type=self.robot_type, features=self.features)`. | A custom writer, metadata initializer, or compatible LeRobot version needs a different construction path. |
| `save_episode(dataset, episode_data, task)` | Calls `dataset.add_frame(frame)` for every frame, then `dataset.save_episode()`, and returns `True`. | The source needs custom episode arguments, filtering, padding, or a non-standard writer. Return `False` to skip an episode intentionally. |
| `get_episode_length(episode_data)` | Returns `len(episode_data)` for logging. | Episodes are lazy, filtered, or otherwise do not implement a reliable length. |

When `save_episode` returns `False`, the worker logs the episode as skipped and
does not increment the saved-episode count. It does not call the default
`save_episode` afterward. A task with no saved episodes is finalized and then
its temporary output is removed. A custom hook should preserve that meaning and
make every skip observable.

## Frame and episode contract

Validate each frame against the declared `features` before writing:

- Feature keys must match the dataset schema, including nested observation/state
  and action keys.
- Numeric arrays must have the declared dtype and shape; do not silently reshape
  a source array to fit.
- Image/video frames must have the declared height, width, channel order, and
  depth indicator. A video feature is not interchangeable with an image feature
  merely because both are arrays.
- Include a scalar/string `task` field in every frame when task or language
  conditioning is required. Put the canonical value in `task.metadata` and
  apply it consistently to every frame of the episode.
- Keep episode boundaries explicit. Do not concatenate episodes inside
  `load_subset` unless the output schema intentionally treats them as one.
- State/action alignment and source-specific corruption policy belong in the
  owning dataset route; the generic writer should only receive validated frames.

A useful adapter-level validation record contains the task id, input path,
episode index, frame count, feature keys, shapes, skipped reason, and output
root. Do not put raw-source layout assumptions in this generic route.

## Feature metadata checklist

For each feature, record at least:

```text
key -> {
  dtype: scalar type or "video",
  shape: [dimensions...],
  names: axis names or named motor groups,
  info: video fps/height/width/channels/codec/pixel format/depth flag when video
}
```

The exact accepted representation is controlled by the target LeRobot release.
The source examples use dictionary-style feature specifications, including
separate state/action keys and video metadata. Check the live target API before
assuming an older import path or writer signature. In particular, this
repository's code imports `LeRobotDataset` through `lerobot.datasets` and uses
that package's aggregation module; an environment exposing the class only in a
nested module needs a compatibility decision, not a blind import rewrite.

## Safe adapter skeleton

Use this as a design shape, not as a source-dependent implementation:

```python
class Adapter(BaseAdapter):
    dataset_type = "example"
    fps = 20
    robot_type = "example_robot"
    features = FEATURE_SPEC
    tags = ("example",)

    def __init__(self, output_path, source_root, instruction):
        super().__init__(Path(output_path))
        self.source_root = Path(source_root)
        self.instruction = instruction

    def load_tasks(self):
        return [
            ConversionTask(
                input_path=path,
                output_path=self.temp_output_path / task_id,
                local_repo_id=f"{self.dataset_type}-{task_id}",
                metadata={"task": self.instruction, "task_id": task_id},
            )
            for task_id, path in discover_inputs(self.source_root)
        ]

    def load_subset(self, task):
        for episode in read_one_input(task.input_path):
            yield [dict(frame, task=task.metadata["task"]) for frame in episode]
```

The helpers in the sketch are adapter-owned and intentionally undefined. They
must validate their source layout in the source-specific route. The checker
script can validate a manifest of the resulting contract without importing this
adapter.
