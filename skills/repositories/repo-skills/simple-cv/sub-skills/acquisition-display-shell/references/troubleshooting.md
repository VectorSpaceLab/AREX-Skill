# Acquisition, Display, and Shell Troubleshooting

## Camera cannot open

**Symptoms**

- `Camera(0)` fails, returns no image, or blocks.
- Camera examples never progress.

**Likely causes**

- No camera device is present.
- Permissions or container device passthrough are missing.
- The camera index is wrong.
- The environment only supports static/headless workflows.

**Recovery**

1. Ask whether a physical camera is required.
2. Try a finite `VirtualCamera` workflow using a temporary image file if the task can use static frames.
3. If hardware is required, confirm device visibility and permissions before opening `Camera`.
4. Avoid infinite loops until one frame can be captured and saved.

## Display fails on a server

**Symptoms**

- `pygame.error: No available video device`.
- `Image.show()` or `Display()` fails.

**Recovery**

Use dummy SDL and finite display smoke:

```bash
SDL_VIDEODRIVER=dummy python ../../scripts/check_display_headless.py
```

Use `Image.save(...)` in scripts unless the user explicitly wants an interactive window.

## Shell starts but does not exit

**Symptoms**

- `simplecv --help` prints the banner and waits at `>>>`.

**Recovery**

Bound the command:

```bash
SDL_VIDEODRIVER=dummy timeout 10 simplecv --help
```

Treat banner output as the check signal. Do not wait indefinitely for the shell to exit.

## Calibration gives poor or no result

**Causes**

- Too few good checkerboard views.
- Wrong interior-corner dimensions.
- Blurry or badly lit images.
- The camera matrix was not saved or loaded from the intended file.

**Recovery**

- Confirm `dimensions=(8, 5)` or the user-specified interior-corner count.
- Capture diverse views at multiple positions and tilts.
- Use stored calibration images for automated checks; use the physical camera only when the user is present and approves interaction.

## Optional hardware module missing

| Symptom | Cause | Recovery |
|---|---|---|
| `Kinect()` warns about `freenect` | Kinect bindings absent | Mark Kinect unverified unless user asks to provision hardware. |
| Vimba/AVT camera class fails | `pymba` or vendor SDK missing | Treat as optional industrial-camera stack. |
| Scanner/digital camera calls fail | OS-level device tools absent | Verify host tool/device availability before using these classes. |
| Web display example fails | Flask/browser/static assets or old Flash/webcam assumptions | Distill the concept; do not rely on dated web assets as verification. |

## Display loop consumes the session

**Cause**

Many original examples run `while True` or `while display.isNotDone()` and wait for mouse/window events.

**Recovery**

Convert to a finite loop before running:

```python
for _ in range(5):
    img = cam.getImage()
    if img is None or img.isEmpty():
        break
    img.save('frame.png')
```

Then route downstream processing to the relevant image, feature, or tracking sub-skill.
