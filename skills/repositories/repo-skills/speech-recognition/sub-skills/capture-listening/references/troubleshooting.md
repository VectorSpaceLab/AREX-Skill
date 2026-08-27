# Capture and Listening Troubleshooting

## Purpose

Use this when a SpeechRecognition microphone workflow cannot open a device, blocks while listening, starts on noise, misses speech, or misbehaves in background callbacks. Recognition-engine setup, network failures, language settings, and model downloads belong in `recognition-engines` or `cli-model-setup`.

## Quick triage

1. Confirm the task actually needs microphone input. File input and conversion do not require PyAudio and belong in `audio-data`.
2. Run the bundled helper help path, which is safe without PyAudio:

   From the generated skill root:

   ```bash
   python sub-skills/capture-listening/scripts/microphone_capture_template.py --help
   ```

3. If microphone input is required, list devices:

   From the generated skill root:

   ```bash
   python sub-skills/capture-listening/scripts/microphone_capture_template.py --list-devices
   ```

4. Capture with finite bounds so silence cannot block forever:

   From the generated skill root:

   ```bash
   python sub-skills/capture-listening/scripts/microphone_capture_template.py --timeout 5 --phrase-limit 10
   ```

## PyAudio is missing or too old

**Symptoms**

- `AttributeError: Could not find PyAudio; check installation`
- `ModuleNotFoundError: No module named 'pyaudio'`
- `Microphone()` fails while non-microphone APIs still import.

**Likely cause**

`Microphone` is the only SpeechRecognition surface in this sub-skill that requires the PyAudio extra. The project metadata declares the `audio` extra as `PyAudio >= 0.2.11`.

**Recovery**

- Install the package with its audio extra in an environment where PortAudio/PyAudio can build or be provided by the OS.
- On systems that need PortAudio headers, install PortAudio development packages first, then install `SpeechRecognition[audio]`.
- If the user only needs audio file transcription, do not install PyAudio; route to `audio-data` instead.
- Keep host package-manager commands under user control because they may require admin privileges.

## No default input device

**Symptoms**

- `OSError` or `IOError` mentioning `No Default Input Device Available`.
- `Microphone()` fails, but `Microphone.list_microphone_names()` shows devices.

**Likely cause**

PyAudio cannot determine an OS default input device.

**Recovery**

1. List microphones with the bundled helper.
2. Select the desired index explicitly with `Microphone(device_index=INDEX)` or `--device-index INDEX`.
3. Alternatively configure the OS default input device.
4. If no devices are listed, check hardware connection, OS privacy microphone permissions, container audio passthrough, and PyAudio/PortAudio installation.

## Raspberry Pi or embedded board blocks in `listen`

**Symptoms**

- The process hangs inside `recognizer.listen` or `MicrophoneStream.read`.
- The default microphone appears to exist but no audio is ever read.

**Likely cause**

The README documents this for Raspberry Pi boards that do not have built-in audio input. PyAudio may block when reading the default device.

**Recovery**

- Use a USB sound card or USB microphone.
- List devices and pass an explicit USB input `device_index`.
- Lower `sample_rate` if the device or CPU cannot keep up with high rates.
- Always use finite `timeout` and `phrase_time_limit` while diagnosing.

## ALSA, JACK, and Bluetooth terminal noise

**Symptoms**

- Terminal prints messages like `bt_audio_service_open: ... Connection refused`.
- `ALSA lib ... Unknown PCM ...`.
- `jack server is not running or cannot be started`, `connect(2) call to /dev/shm/jack... failed`, or `attempt to connect to server failed`.

**Likely cause**

These messages come from the platform audio stack while PyAudio enumerates or opens devices. The README notes that Bluetooth messages may be harmless when the Bluetooth device is not connected, ALSA `Unknown PCM` messages usually come from ALSA configuration entries, and JACK messages may be safely ignored if JACK is not used.

**Recovery**

- If capture works, treat the messages as noisy diagnostics rather than SpeechRecognition exceptions.
- If using Bluetooth input, verify the physical device is connected and selected.
- If ALSA device names are wrong, fix the ALSA configuration outside the skill before retrying.
- If the messages must be hidden in an end-user app, suppress stderr only around microphone startup, not around the whole program where real errors would be lost.

## False positives: recognizer starts when nobody speaks

**Symptoms**

- `listen` returns audio for room noise.
- Recognition starts after the user is done speaking.
- The callback keeps firing in a noisy room.

**Likely causes**

- `energy_threshold` is too low for the microphone or room.
- Microphone gain is too high.
- `dynamic_energy_ratio` is too small or dynamic adjustment has not settled.
- `pause_threshold` is too long for the desired end-of-phrase behavior.

**Recovery**

1. Calibrate during silence:

   ```python
   with sr.Microphone(device_index=INDEX) as source:
       recognizer.adjust_for_ambient_noise(source, duration=1)
       print(recognizer.energy_threshold)
   ```

2. Increase `energy_threshold` manually if calibration still triggers on noise. The docs mention good values vary widely and can range from about `50` to `4000`.
3. Reduce microphone input gain in the OS if it is picking up excessive ambient sound.
4. For callback loops, set a `phrase_time_limit` and keep callback work short.

## False negatives: recognizer misses speech at startup

**Symptoms**

- The first utterance is ignored.
- `listen` waits until timeout even though the user spoke.
- Speech is considered ambient noise immediately after startup.

**Likely causes**

- Initial `energy_threshold` is too high.
- Dynamic threshold adjustment has not yet settled.
- The user spoke during `adjust_for_ambient_noise`, causing an unrepresentative threshold.
- Microphone gain is too low or the wrong device is selected.

**Recovery**

1. Ask for a quiet second and call `adjust_for_ambient_noise(source, duration=1)` before listening.
2. If the first phrase still fails, lower `energy_threshold` or set it to a known working value for that microphone.
3. Confirm the correct `device_index` and OS input gain.
4. Use `timeout` while debugging so failures are visible as `WaitTimeoutError` instead of indefinite waits.

## Slow speakers are cut off, or capture never ends

**Symptoms**

- Phrases are truncated before the user finishes.
- Long pauses cause multiple small captures.
- Capture keeps running in background after the phrase is over.

**Likely causes**

- `pause_threshold` is too low for slow speakers.
- `phrase_time_limit` is too short for the target utterance.
- Ambient noise remains above `energy_threshold`, so silence is not detected.

**Recovery**

- Raise `pause_threshold` for slow speakers, ensuring `pause_threshold >= non_speaking_duration >= 0`.
- Raise or remove `phrase_time_limit` when longer phrases are expected.
- If capture never ends, recalibrate or raise `energy_threshold`, and check input gain/noise.

## Callback threading and stopping problems

**Symptoms**

- Background listener does not stop immediately.
- Deadlock or hang when stopping.
- GUI or main-thread-only code fails inside the callback.
- Recognition/network calls pile up in callbacks.

**Likely causes**

- `listen_in_background` uses a daemon thread and calls `callback(recognizer, audio)` from a non-main thread.
- The stopper joins the listener when `wait_for_stop=True`; the source code says this must be called from the same thread that originally called `listen_in_background`.
- The internal loop listens with a one-second timeout before checking the stop flag, so non-blocking stops can take a short time to settle.

**Recovery**

- Store the stopper returned by `listen_in_background` and call it in a `finally` block.
- Call `stopper(wait_for_stop=True)` from the starter thread for clean shutdown.
- Use `stopper(wait_for_stop=False)` when stopping from another thread or when immediate return is required, then allow cleanup time.
- Keep callbacks short. Put `AudioData` onto a `queue.Queue` and process transcription in a worker thread if recognition is slow or network-bound.
- Do not update GUI frameworks directly from the callback thread; marshal events to the main thread.

## Keep capture examples separate from transcription setup

The original microphone examples demonstrate many recognition engines after capture. Do not copy their transcription setup placeholders into capture templates. This sub-skill's bundled template captures audio only; engine-specific recognition setup belongs in `recognition-engines`.
