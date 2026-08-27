# Habitat-Lab Data And Asset Reference

## When To Read

Read this when a user mentions scenes, task datasets, `data/`, missing files, downloaded assets, PointNav/ObjectNav/Rearrange/VLN/EQA episodes, or simulator scene paths.

## Expected Top-Level Layout

Habitat-Lab expects a `data/` directory, or paths in config overrides that point to equivalent content:

```text
data/
  scene_datasets/
    habitat-test-scenes/
    replica_cad/
    hm3d/
    gibson/
    mp3d/
    hssd-hab/
  datasets/
    pointnav/
    objectnav/
    instance_imagenav/
    imagenav/
    eqa/
    vln/
    rearrange_pick/
```

Scene datasets provide 3D assets. Task datasets provide episodes and task-specific annotations. Many config files reference both.

## Common Data Families

| Task family | Typical scene data | Typical task data |
| --- | --- | --- |
| PointNav | Gibson, MatterPort3D, HM3D, habitat test scenes | `data/datasets/pointnav/...` |
| ObjectNav | MatterPort3D, HM3D, HSSD, ProcTHOR-hab | `data/datasets/objectnav/...` |
| Instance ImageNav | HM3D semantic datasets | `data/datasets/instance_imagenav/...` |
| ImageNav | Gibson or MatterPort3D scenes | image-goal task dataset paths |
| VLN R2R | MatterPort3D scenes | `data/datasets/vln/mp3d/r2r/...` |
| EQA | MatterPort3D scenes | `data/datasets/eqa/mp3d/...` |
| Rearrangement | ReplicaCAD or HSSD assets | rearrange task datasets and robot/articulated assets |

## Safe Checks Before Runtime

- Compose the config first and inspect `habitat.dataset.data_path`, `habitat.dataset.scenes_dir`, `habitat.simulator.scene`, and robot asset paths.
- Use the setup/config probes to validate paths without launching simulation.
- Confirm downloads explicitly before running dataset-download commands; some datasets are hundreds of MB to hundreds of GB and may need credentials or licenses.
- Treat benchmark-scale or training-scale data as user-approved work, not an automatic agent action.

## Common Failure Signals

- `FileNotFoundError`, `AssertionError`, or empty episode lists usually mean scene/task data paths do not match the config.
- Simulator errors around `.glb`, `.scene_instance.json`, navmesh, or object templates usually mean scene assets are missing or incompatible.
- Rearrangement errors often involve missing ReplicaCAD/HSSD assets, robot URDF/object templates, or Bullet-enabled Habitat-Sim.
- VLN/EQA/ObjectNav failures can involve task annotations missing even when scenes exist.
