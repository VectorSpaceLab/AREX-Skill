# Pose estimation and segmentation

Public perception exports include robot segmentation, mesh/SDF pose detectors,
and detector configs. These workflows need calibrated depth/point clouds,
robot geometry, and often an interactive visualizer. Start by validating depth,
point-cloud frame, robot mesh, and detector tolerances on a static synthetic or
small captured fixture.

Do not confuse pose-estimation output with a collision-free robot pose. Feed
estimated geometry through the collision/scene route and validate uncertainty,
frame transforms, and collision margins before planning.

Optional external model, USD, and Viser dependencies should be installed only
for a selected application; the core Mapper and observation contracts do not
require them.
