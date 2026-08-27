# SUN RGB-D troubleshooting

| Symptom | Cause | Recovery |
|---|---|---|
| raw-data preparation instructions seem incomplete | the included code is a beta supplement and relies on the external dataset/toolbox | obtain the official assets, record the extraction/toolbox version, and validate the reorganized training tree before Python preprocessing |
| expected pickle or box-dimension file is absent | generated/precomputed asset was not produced or copied | run the bounded preparation step only after validating raw inputs; do not substitute a KITTI pickle |
| test result cannot be evaluated | data/result pickle modes or class ordering differ | match `--from_rgb_detection`, split, class list, point count, and checkpoint metadata |
| `cPickle` fails under Python 3 | Python-2-era import | apply an explicit compatibility import and validate the sequential pickle stream |
| TensorFlow graph or checkpoint fails | wrong TensorFlow/model/runtime | use the legacy runtime route and match `frustum_pointnets_v1_sunrgbd` checkpoint variables |
| Mayavi/display error | no local GUI/OpenGL backend | omit visualization or run it in a compatible local GUI; it is not required for AP |
| MATLAB MEX/toolbox binary fails | platform-specific external dependency | rebuild/use the official toolbox for the host; do not treat bundled binaries as portable |

Keep SUN RGB-D and KITTI class maps, dimensions, and coordinate conventions
separate. A valid-looking pickle from one dataset is not a compatible input to
the other pipeline.
