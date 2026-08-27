# Sphere approximation and ignore maps

cuRobo represents robot links with many spheres because sphere-sphere tests are
cheap and parallel on the GPU. Increase sphere density for fidelity, but expect
more pair checks and memory. Add conservative per-sphere padding when the
application needs clearance beyond mesh contact.

Some adjacent links are always geometrically touching and can be ignored; other
pairs cannot collide by mechanical design. Generate ignore decisions from the
robot's actual geometry and known collision-free samples. To inspect questionable
pairs, enable pair-distance storage and identify the signed-distance entries;
do not delete all pairs to hide an invalid model.

For high-DoF robots, pair reduction is partitioned across blocks. A slow/OOM
self-collision configuration should first reduce sphere density, padding, or
batch size while preserving safety, then optimize the model.
