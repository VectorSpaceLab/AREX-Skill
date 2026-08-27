# Perception troubleshooting

- **Mapper construction error:** `extent_meters_xyz` is required; verify positive
  extents, voxel resolutions, device, block/grid dimensions, and sensor counts.
- **Integration shape error:** match camera/lidar height, width, sensor count,
  feature channels, intrinsics, rays, and batch dimensions to `MapperCfg`.
- **Empty/incorrect map:** filter depth, confirm units are meters, check pose
  frame and grid center, and inspect stats after each integration.
- **ESDF failure or OOM:** use a smaller extent/coarser resolution, reduce visible
  blocks, select a free GPU, and compute ESDF after TSDF data exists.
- **Lidar artifacts:** validate ray calibration and interpolation thresholds on
  a synthetic scan before a full sequence.
- **Feature/Viser import error:** install the selected optional dependency and
  keep feature dimensions/model output aligned; headless core mapping remains a
  valid fallback.
- **Dataset workflow stalls:** stop network/download stages and verify the
  mapper with a tiny local fixture first.
