# Camera and Segmentation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: deeplab2` | Optional camera segmentation metrics dependency missing | Install Deeplab2 only for that workflow or mark camera-segmentation metric execution unavailable. |
| Camera custom op import fails | Wheel/ABI/TensorFlow mismatch or compiled op absent | Use a WOD wheel matching the TensorFlow line; run the bundled import checker. |
| 2D detections lack camera name | Output did not preserve single camera input context | Carry camera enum/name from image source into the object/submission. |
| Segmentation metric labels mismatch | Mixing camera segmentation with lidar semantic segmentation | Use the task-specific proto and class mapping. |
| WDL-limited code reuse concern | Additional limited patent/license terms apply | Read the WDL-limited license terms before adapting code outside WOD-authorized use. |
