# Data Formats and Layouts

Habitat-Lab configs separate task episode datasets from scene assets. An episode file tells Habitat what to do; scene assets and scene-dataset metadata let Habitat-Sim instantiate the world.

## Config Fields That Point to Data

- `habitat.dataset.type`: registered dataset key, such as `PointNav-v1`, `ObjectNav-v1`, `InstanceImageNav-v1`, `Matterport3dDataset-v1`, `VLN-v0`, or `RearrangeDataset-v0`.
- `habitat.dataset.split`: split name used by `{split}` placeholders in `data_path`.
- `habitat.dataset.data_path`: task episode file or pattern, often ending in `.json.gz`.
- `habitat.dataset.scenes_dir`: root for scene assets, usually `data/scene_datasets`.
- `habitat.dataset.content_scenes`: scene names to load, often `['*']` for all scenes in the split.
- `habitat.simulator.scene`: direct scene asset path used when no dataset episode overrides it.
- `Episode.scene_dataset_config`: scene-dataset metadata path used to set `habitat.simulator.scene_dataset` during `Env` setup.
- `Episode.scene_id`: the scene asset path or scene identifier used to set `habitat.simulator.scene` during `Env` setup.

## Scene Dataset Layouts

Common scene asset layouts from Habitat-Lab dataset guidance:

- Habitat test scenes: `data/scene_datasets/habitat-test-scenes/{scene}.glb`.
- ReplicaCAD: `data/scene_datasets/replica_cad/configs/scenes/{scene}.scene_instance.json`.
- HM3D: `data/scene_datasets/hm3d/{split}/{scene-directory}/{scene}.basis.glb`.
- Gibson: `data/scene_datasets/gibson/{scene}.glb`.
- MatterPort3D: `data/scene_datasets/mp3d/{scene}/{scene}.glb`.
- HSSD-Habitat: `data/scene_datasets/hssd-hab/scenes/{scene}.scene_instance.json`.
- AI2-THOR-Habitat: `data/scene_datasets/ai2thor-hab/ai2thor-hab/configs/scenes/{dataset}/{scene}.scene_instance.json`.

## Task Dataset Layouts

Common episode dataset locations and matching config families:

- PointNav Habitat test: `data/datasets/pointnav/habitat-test-scenes/v1/{split}/{split}.json.gz`, config `habitat/dataset/pointnav/habitat_test`.
- PointNav Gibson: `data/datasets/pointnav/gibson/v1/`, config `habitat/dataset/pointnav/gibson`.
- PointNav MP3D: `data/datasets/pointnav/mp3d/v1/`, config `habitat/dataset/pointnav/mp3d`.
- PointNav HM3D: `data/datasets/pointnav/hm3d/v1/`, config `habitat/dataset/pointnav/hm3d`.
- ObjectNav MP3D: `data/datasets/objectnav/mp3d/v1/`, config `habitat/dataset/objectnav/mp3d`.
- ObjectNav HM3D: `data/datasets/objectnav/hm3d/v1/` or versioned HM3D data, config `habitat/dataset/objectnav/hm3d`.
- ObjectNav HSSD-Habitat: `data/datasets/objectnav/hssd-hab`, config `habitat/dataset/objectnav/hssd-hab`.
- ObjectNav ProcTHOR-Habitat: `data/datasets/objectnav/procthor-hab`, config `habitat/dataset/objectnav/procthor-hab`.
- EQA MP3D: `data/datasets/eqa/mp3d/v1/`, config `habitat/dataset/eqa/mp3d`.
- VLN R2R MP3D: `data/datasets/vln/mp3d/r2r/v1`, config `habitat/dataset/vln/mp3d_r2r`.
- InstanceImageNav HM3D: `data/datasets/instance_imagenav/hm3d/v1/` or newer versioned directories, config `habitat/dataset/instance_imagenav/hm3d_v*`.
- Rearrangement ReplicaCAD: configs commonly point at `data/datasets/replica_cad/rearrange/v2/{split}/...json.gz` and require ReplicaCAD scene/object assets.

## Base Episode Fields

`Episode` is keyword-only and includes:

- `episode_id`: unique string identifier within a dataset.
- `scene_id`: scene path or scene identifier.
- `scene_dataset_config`: scene-dataset metadata config; default is `default`.
- `additional_obj_config_paths`: additional object config search paths; important for rearrangement/object assets.
- `start_position`: `[x, y, z]` agent start position.
- `start_rotation`: quaternion `[x, y, z, w]` start orientation.
- `info`: optional arbitrary metadata.

A minimal in-memory test fixture can use:

```python
from habitat.core.dataset import Dataset, Episode

dataset = Dataset()
dataset.episodes = [
    Episode(
        episode_id="0",
        scene_id="data/scene_datasets/habitat-test-scenes/van-gogh-room.glb",
        start_position=[0.0, 0.0, 0.0],
        start_rotation=[0.0, 0.0, 0.0, 1.0],
    )
]
```

This fixture is useful for `Dataset` methods, but simulator-backed `Env` still needs the referenced scene asset.

## Navigation Episode Fields

`NavigationEpisode` adds:

- `goals`: list of `NavigationGoal` objects; each base goal has `position` and optional `radius`.
- `start_room`: optional room identifier.
- `shortest_paths`: optional path annotations.

PointNav, ImageNav, ObjectNav, EQA, and VLN build on this structure with task-specific goal or instruction data.

## ObjectNav and Instance/Image Navigation Fields

- ObjectNav episodes add `object_category` and rely on semantic scene/category metadata.
- Object goals may include `object_id`, `object_name`, `object_category`, room metadata, and view points.
- ImageNav/InstanceImageNav reuse navigation-style starts/goals but require image goal data and compatible dataset loaders.

## VLN Episode Fields

`VLNEpisode` adds:

- `reference_path`: list of `[x, y, z]` points aligned with the route.
- `instruction`: instruction object with text and token fields.
- `trajectory_id`: ground-truth trajectory identifier.

VLN configs also require `InstructionSensor` to expose instruction observations.

## Rearrangement Episode Fields

`RearrangeEpisode` adds object and articulated-object state:

- `ao_states`: articulated object link states.
- `rigid_objs`: object handles and transforms to place in the scene.
- `targets`: target transforms for objects.
- `markers`: named points of interest such as handles or grasp points.
- `target_receptacles` and `goal_receptacles`: receptacle names/link indices for objects and goals.
- `name_to_receptacle`: object instance handle to receptacle mapping.

Rearrangement episodes often fail earlier than navigation if scene dataset configs, object templates, robot files, or physics configs are absent.

## Tiny Fixture Guidance

- Use in-memory `Dataset`/`Episode` fixtures for pure dataset operations such as `scene_ids`, `get_scene_episodes`, `filter_episodes`, `get_splits`, and `get_episode_iterator`.
- Use the Habitat test PointNav config for small local smoke tests only when `data/scene_datasets/habitat-test-scenes/` and `data/datasets/pointnav/habitat-test-scenes/` are present.
- Do not create fake scene `.glb` files to bypass simulator checks; config/dataset checks can be mocked, but `Env` requires real scene assets.
- Keep fixture episode IDs strings, rotations as length-4 quaternions, and positions as length-3 lists.
- For dataset-loader tests, prefer `.json.gz` fixtures compatible with the target dataset class instead of constructing subclass-specific episode dictionaries by guesswork.
