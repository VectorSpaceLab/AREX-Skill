# Motion data formats

## `.motion`

A `.motion` file represents one motion clip in ProtoMotions format. Conversion scripts build these from SMPL/SOMA/robot trajectories, root transforms, joint angles, velocities, and contacts.

## Packaged MotionLib `.pt`

A packaged MotionLib is the main training/inference data container. Evidence from `MotionLib` and utility scripts shows common fields:

- `gts`: global rigid-body positions.
- `grs`: global rigid-body rotations.
- `gvs`: global rigid-body velocities.
- `gavs`: global rigid-body angular velocities.
- `dps`: DOF positions.
- `dvs`: DOF velocities.
- `contacts`: rigid-body contact labels when available.
- `motion_num_frames`, `motion_lengths`, `motion_dt`, `motion_weights`, `length_starts`.
- optional `motion_files`: source filenames.

`MotionLibConfig` can load `.pt`, `.yaml`, or `.motion` sources. It also supports shard selection through `slurmrank` patterns and modes `fixed`, `live`, and `restart`.

## YAML motion lists

YAML motion lists reference motion files relative to the YAML location. If packaging fails with a missing first motion file, check whether the YAML was moved without its referenced files.

## FPS handling

Conversion scripts downsample by integer factors and preserve or infer FPS metadata. Retargeted `.npz` may store FPS values; otherwise defaults apply. Contact labels must be downsampled with the same effective factor as the motion.

## Contacts

Rigid-body contacts are stored as per-body labels in MotionLib. Retargeting pipelines often extract source foot contacts separately and apply them to the robot motion. This is preferred when retargeted contact geometry is imperfect.

If all contacts are zero at load time, MotionLib warns and may discard contacts, so components that require reference contacts will later fail.

## Body alignment

Motion data body count and order must match the target robot/skeleton kinematic info. A mismatch usually means the source data was packaged for a different skeleton or the wrong `robot_type`/`skeleton_format` was used.
