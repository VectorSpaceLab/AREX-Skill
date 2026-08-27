# Optional integration boundaries

The core `MotionRetargeter` route accepts cuRobo-native pose goals. A humanoid
application may additionally use an external retargeter (for example, SOMA),
source motion capture data, camera calibration, and Viser playback. These
components are not implied by the cuRobo package install: validate their
licenses, coordinate frames, checkpoint/data availability, and device tensors
separately before passing goals to cuRobo.
