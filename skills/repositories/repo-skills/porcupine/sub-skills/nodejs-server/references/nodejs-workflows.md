# Node.js Workflows

Use these workflows for server-side JavaScript/TypeScript with `@picovoice/porcupine-node`. For API details, see `nodejs-api-reference.md`; for failure triage, see `troubleshooting.md`.

## Workflow 1: file-based WAV detection

Use file detection when the input is already a local WAV file and the goal is to scan for wake-word occurrences with timestamps.

### Requirements

- Node.js 18+.
- Installed packages:

```console
npm install @picovoice/porcupine-node wavefile
```

- A Picovoice AccessKey for actual detection.
- Input WAV: 16 kHz, 16-bit linear PCM, mono.
- Either built-in keyword names or custom `.ppn` keyword paths.

### Safe bundled helper

This sub-skill includes a self-contained helper template at `../scripts/porcupine_node_file_template.js`.

Examples:

```console
node ../scripts/porcupine_node_file_template.js --help
node ../scripts/porcupine_node_file_template.js --list-keywords
node ../scripts/porcupine_node_file_template.js --show-inference-devices
```

Detection with built-in keywords:

```console
PICOVOICE_ACCESS_KEY="${ACCESS_KEY}" \
node ../scripts/porcupine_node_file_template.js \
  --input-wav path/to/input.wav \
  --keywords grasshopper,bumblebee \
  --sensitivity 0.5
```

Detection with custom keyword files:

```console
node ../scripts/porcupine_node_file_template.js \
  --access-key "${ACCESS_KEY}" \
  --input-wav path/to/input.wav \
  --keyword-paths path/to/keyword_linux.ppn \
  --model-path path/to/porcupine_params.pv \
  --device cpu
```

The helper intentionally has no repository checkout paths. It requires the installed npm packages only when listing inference devices or running detection; help and built-in keyword listing work without credentials.

### Implementation pattern

1. Parse arguments and require exactly one keyword source:
   - built-ins such as `porcupine`, `grasshopper`, or `hey google`; or
   - custom `.ppn` file paths.
2. Expand one sensitivity value to all keywords, or validate a per-keyword sensitivity list.
3. Construct `Porcupine` with an AccessKey and optional `{ modelPath, device, libraryPath }`.
4. Read the WAV file with a parser such as `wavefile`.
5. Call `checkWaveFile(wave, handle.sampleRate)` and stop if it is not 16-bit, mono, and the expected sample rate.
6. Split frames with `getInt16Frames(wave, handle.frameLength)`.
7. For every full frame, call `handle.process(frame)`.
8. Convert a detection frame index to seconds with:

```javascript
const seconds = (frameIndex * handle.frameLength) / handle.sampleRate;
```

9. Call `handle.release()` in `finally`.

### Minimal code skeleton

```javascript
const fs = require("fs");
const { WaveFile } = require("wavefile");
const {
  Porcupine,
  BuiltinKeyword,
  checkWaveFile,
  getInt16Frames,
} = require("@picovoice/porcupine-node");

const keywords = [BuiltinKeyword.GRASSHOPPER, BuiltinKeyword.BUMBLEBEE];
const sensitivities = [0.5, 0.65];
let handle;

try {
  handle = new Porcupine(process.env.PICOVOICE_ACCESS_KEY, keywords, sensitivities, {
    device: "best",
  });

  const wave = new WaveFile(fs.readFileSync("path/to/input.wav"));
  if (!checkWaveFile(wave, handle.sampleRate)) {
    throw new Error("WAV must be 16-bit, mono, and match Porcupine sampleRate");
  }

  const frames = getInt16Frames(wave, handle.frameLength);
  for (let i = 0; i < frames.length; i++) {
    const keywordIndex = handle.process(frames[i]);
    if (keywordIndex !== -1) {
      const timestampSeconds = (i * handle.frameLength) / handle.sampleRate;
      console.log(`Detected keyword ${keywordIndex} at ${timestampSeconds.toFixed(3)}s`);
    }
  }
} finally {
  if (handle) {
    handle.release();
  }
}
```

## Workflow 2: microphone hardware detection

Use microphone detection when a Node process should listen continuously on local audio hardware. The repository demo pattern uses `@picovoice/pvrecorder-node`; this sub-skill documents it as reference-only because it depends on microphone hardware, OS permissions, and a long-running loop.

### Requirements

```console
npm install @picovoice/porcupine-node @picovoice/pvrecorder-node
```

Also ensure:

- The host has a microphone device visible to the Node process.
- OS privacy settings allow terminal/Node microphone access.
- The process handles `SIGINT`/shutdown so native resources are released.
- A valid AccessKey is available when constructing Porcupine.

### Device discovery

List Porcupine inference devices:

```javascript
const { Porcupine } = require("@picovoice/porcupine-node");
console.log(Porcupine.listAvailableDevices().join("\n"));
```

List microphone input devices:

```javascript
const { PvRecorder } = require("@picovoice/pvrecorder-node");
PvRecorder.getAvailableDevices().forEach((device, index) => {
  console.log(`index: ${index}, device name: ${device}`);
});
```

### Loop pattern

```javascript
const { Porcupine, BuiltinKeyword } = require("@picovoice/porcupine-node");
const { PvRecorder } = require("@picovoice/pvrecorder-node");

let interrupted = false;
process.on("SIGINT", () => {
  interrupted = true;
});

async function main() {
  const handle = new Porcupine(
    process.env.PICOVOICE_ACCESS_KEY,
    [BuiltinKeyword.GRAPEFRUIT],
    [0.5],
    { device: "best" }
  );

  const recorder = new PvRecorder(handle.frameLength, -1);
  try {
    recorder.start();
    console.log(`Using device: ${recorder.getSelectedDevice()}`);

    while (!interrupted) {
      const pcm = await recorder.read();
      const keywordIndex = handle.process(pcm);
      if (keywordIndex !== -1) {
        console.log("Detected grapefruit");
      }
    }
  } finally {
    recorder.release();
    handle.release();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
```

### Microphone decisions

- `audioDeviceIndex = -1` lets the recorder select a default device; use an explicit index after listing devices when debugging production deployments.
- Use `handle.frameLength` as the recorder frame length so `recorder.read()` returns frames Porcupine can process directly.
- Keep keyword display names in the same order as the constructor keyword array; detection returns only an index.
- Release both the recorder and Porcupine engine. Releasing one does not release the other.

## Built-in versus custom keyword decision

Use this decision table before writing code:

| Situation | Use |
| --- | --- |
| English built-in keyword such as `porcupine`, `grasshopper`, or `hey google` | `BuiltinKeyword.<NAME>` or CLI `--keywords`. |
| A `.ppn` file trained or downloaded for the deployment platform | Custom keyword path array or CLI `--keyword-paths`. |
| Non-English or custom model `.pv` is required | Route asset/model selection to `../../custom-keywords-and-assets/SKILL.md`, then pass the chosen `modelPath`. |
| A file path string happens to look like a built-in word | Prefer explicit built-in enum for built-ins; use actual filesystem paths for custom `.ppn` files. |

## Native verification candidates

- `Porcupine.listAvailableDevices()` can be checked without credentials if Node and the installed native package are available.
- File detection and Jest/API tests require a valid AccessKey and compatible local WAV/PPN/PV assets.
- Microphone detection additionally requires audio hardware and permissions; treat it as optional hardware verification unless explicitly requested.
