#!/usr/bin/env node
"use strict";

/*
 * Safe Porcupine Node.js file-detection helper.
 *
 * This script intentionally contains no repository checkout paths. It expects
 * @picovoice/porcupine-node and wavefile to be installed in the application
 * that runs detection. Help and built-in keyword listing do not require those
 * packages or an AccessKey.
 */

const fs = require("fs");
const path = require("path");

const BUILTIN_KEYWORD_KEYS = [
  "ALEXA",
  "AMERICANO",
  "BLUEBERRY",
  "BUMBLEBEE",
  "COMPUTER",
  "GRAPEFRUIT",
  "GRASSHOPPER",
  "HEY_GOOGLE",
  "HEY_SIRI",
  "JARVIS",
  "OK_GOOGLE",
  "PICOVOICE",
  "PORCUPINE",
  "TERMINATOR",
];

const VALUE_OPTIONS = new Set([
  "access-key",
  "input-wav",
  "keywords",
  "keyword-paths",
  "sensitivity",
  "sensitivities",
  "model-path",
  "library-path",
  "device",
]);

const FLAG_OPTIONS = new Set([
  "help",
  "list-keywords",
  "show-inference-devices",
]);

const ALIASES = new Map([
  ["h", "help"],
  ["a", "access-key"],
  ["i", "input-wav"],
  ["k", "keyword-paths"],
  ["b", "keywords"],
  ["s", "sensitivity"],
  ["m", "model-path"],
  ["l", "library-path"],
  ["y", "device"],
]);

function usage() {
  return `Usage:
  node porcupine_node_file_template.js --help
  node porcupine_node_file_template.js --list-keywords
  node porcupine_node_file_template.js --show-inference-devices [--library-path path/to/pv_porcupine.node]
  node porcupine_node_file_template.js --input-wav path/to/input.wav --keywords porcupine,grasshopper [options]
  node porcupine_node_file_template.js --input-wav path/to/input.wav --keyword-paths path/to/keyword.ppn [options]

Options:
  -a, --access-key <string>        Picovoice AccessKey. May also use PICOVOICE_ACCESS_KEY.
  -i, --input-wav <path>           WAV file: 16 kHz, 16-bit linear PCM, mono.
  -b, --keywords <list>            Comma-separated built-in keywords, e.g. porcupine,hey google.
  -k, --keyword-paths <list>       Comma-separated custom .ppn keyword file paths.
  -s, --sensitivity <number>       One sensitivity for every keyword. Default: 0.5.
      --sensitivities <list>       Comma-separated per-keyword sensitivities.
  -m, --model-path <path>          Optional .pv model override.
  -l, --library-path <path>        Optional pv_porcupine.node override.
  -y, --device <string>            Inference device, e.g. best, cpu, cpu:4, gpu, gpu:0.
      --show-inference-devices     Print Porcupine inference devices; no AccessKey required.
      --list-keywords              Print built-in keyword names; no package or AccessKey required.
  -h, --help                       Show this help.

Detection requires @picovoice/porcupine-node, wavefile, a valid AccessKey, and
at least one built-in keyword or custom .ppn path. Do not put AccessKeys in
source code; pass them through environment or runtime configuration.`;
}

function canonicalOptionName(rawName) {
  const withoutPrefix = rawName.replace(/^-+/, "");
  const normalized = withoutPrefix.replace(/_/g, "-");
  return ALIASES.get(normalized) || normalized;
}

function parseArgs(argv) {
  const opts = { _: [] };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];

    if (!arg.startsWith("-")) {
      opts._.push(arg);
      continue;
    }

    let name;
    let value;
    const equalsIndex = arg.indexOf("=");
    if (equalsIndex !== -1) {
      name = canonicalOptionName(arg.slice(0, equalsIndex));
      value = arg.slice(equalsIndex + 1);
    } else {
      name = canonicalOptionName(arg);
    }

    if (FLAG_OPTIONS.has(name)) {
      opts[name] = true;
      continue;
    }

    if (!VALUE_OPTIONS.has(name)) {
      throw new Error(`Unknown option: ${arg}`);
    }

    if (value === undefined) {
      i += 1;
      value = argv[i];
    }

    if (value === undefined || value.startsWith("--")) {
      throw new Error(`Missing value for --${name}`);
    }

    opts[name] = value;
  }

  return opts;
}

function splitList(value) {
  if (value === undefined || value === null) {
    return [];
  }
  return String(value)
    .split(",")
    .map(item => item.trim())
    .filter(Boolean);
}

function parseSensitivity(value, optionName) {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue) || numberValue < 0 || numberValue > 1) {
    throw new Error(`${optionName} must be a number in the range [0, 1]: ${value}`);
  }
  return numberValue;
}

function parseSensitivities(opts, keywordCount) {
  if (opts["sensitivities"] !== undefined) {
    const values = splitList(opts["sensitivities"]).map(value =>
      parseSensitivity(value, "--sensitivities")
    );
    if (values.length !== keywordCount) {
      throw new Error(
        `--sensitivities count (${values.length}) must match keyword count (${keywordCount})`
      );
    }
    return values;
  }

  const single = parseSensitivity(opts["sensitivity"] || "0.5", "--sensitivity");
  return Array(keywordCount).fill(single);
}

function normalizeBuiltinKey(token) {
  return token.trim().toUpperCase().replace(/[\s-]+/g, "_");
}

function displayBuiltinKeywords() {
  return BUILTIN_KEYWORD_KEYS
    .map(key => key.toLowerCase().replace(/_/g, " "))
    .join("\n");
}

function requirePackage(packageName, installHint) {
  try {
    return require(packageName);
  } catch (error) {
    if (error && error.code === "MODULE_NOT_FOUND") {
      throw new Error(
        `Cannot load ${packageName}. Install it in this project first: ${installHint}`
      );
    }
    throw error;
  }
}

function resolveExistingFile(inputPath, optionName) {
  const resolved = path.resolve(inputPath);
  if (!fs.existsSync(resolved)) {
    throw new Error(`${optionName} file not found: ${inputPath}`);
  }
  return resolved;
}

function buildKeywordInputs(opts, BuiltinKeyword) {
  const builtinTokens = splitList(opts["keywords"]);
  const customPaths = splitList(opts["keyword-paths"]);

  if ((builtinTokens.length > 0 && customPaths.length > 0) ||
      (builtinTokens.length === 0 && customPaths.length === 0)) {
    throw new Error("Specify exactly one of --keywords or --keyword-paths");
  }

  if (builtinTokens.length > 0) {
    const keywords = [];
    const displayNames = [];
    for (const token of builtinTokens) {
      const key = normalizeBuiltinKey(token);
      if (!BUILTIN_KEYWORD_KEYS.includes(key) || BuiltinKeyword[key] === undefined) {
        throw new Error(
          `Unknown built-in keyword '${token}'. Use --list-keywords to see supported names.`
        );
      }
      keywords.push(BuiltinKeyword[key]);
      displayNames.push(BuiltinKeyword[key]);
    }
    return { keywords, displayNames };
  }

  const keywords = customPaths.map(inputPath => resolveExistingFile(inputPath, "--keyword-paths"));
  const displayNames = keywords.map(keywordPath =>
    path.basename(keywordPath).replace(/\.ppn$/i, "").replace(/_(linux|mac|windows|raspberry-pi)$/i, "")
  );
  return { keywords, displayNames };
}

function frameIndexToSeconds(frameIndex, handle) {
  return (frameIndex * handle.frameLength) / handle.sampleRate;
}

function printInferenceDevices(opts) {
  const { Porcupine } = requirePackage(
    "@picovoice/porcupine-node",
    "npm install @picovoice/porcupine-node"
  );
  const options = {};
  if (opts["library-path"] !== undefined) {
    options.libraryPath = resolveExistingFile(opts["library-path"], "--library-path");
  }
  const devices = Porcupine.listAvailableDevices(options);
  console.log(devices.join("\n"));
}

function runDetection(opts) {
  const accessKey = opts["access-key"] || process.env.PICOVOICE_ACCESS_KEY;
  if (!accessKey) {
    throw new Error("Detection requires --access-key or PICOVOICE_ACCESS_KEY");
  }

  if (!opts["input-wav"]) {
    throw new Error("Detection requires --input-wav path/to/input.wav");
  }

  const inputWav = resolveExistingFile(opts["input-wav"], "--input-wav");

  const porcupinePackage = requirePackage(
    "@picovoice/porcupine-node",
    "npm install @picovoice/porcupine-node"
  );
  const { WaveFile } = requirePackage("wavefile", "npm install wavefile");

  const {
    Porcupine,
    BuiltinKeyword,
    checkWaveFile,
    getInt16Frames,
  } = porcupinePackage;

  const { keywords, displayNames } = buildKeywordInputs(opts, BuiltinKeyword);
  const sensitivities = parseSensitivities(opts, keywords.length);

  const options = {};
  if (opts["model-path"] !== undefined) {
    options.modelPath = resolveExistingFile(opts["model-path"], "--model-path");
  }
  if (opts["library-path"] !== undefined) {
    options.libraryPath = resolveExistingFile(opts["library-path"], "--library-path");
  }
  if (opts["device"] !== undefined) {
    options.device = opts["device"];
  }

  let handle;
  try {
    handle = new Porcupine(accessKey, keywords, sensitivities, options);

    let inputWaveFile;
    try {
      inputWaveFile = new WaveFile(fs.readFileSync(inputWav));
    } catch (error) {
      throw new Error(`Could not read WAV file '${opts["input-wav"]}': ${error.message || error}`);
    }

    if (!checkWaveFile(inputWaveFile, handle.sampleRate)) {
      throw new Error(
        "Input WAV did not meet requirements: expected 16-bit linear PCM, mono, and Porcupine sample rate"
      );
    }

    const frames = getInt16Frames(inputWaveFile, handle.frameLength);
    if (frames.length === 0) {
      throw new Error("No full Porcupine frames found in the WAV file");
    }

    for (let frameIndex = 0; frameIndex < frames.length; frameIndex += 1) {
      const keywordIndex = handle.process(frames[frameIndex]);
      if (keywordIndex !== -1) {
        const timestamp = frameIndexToSeconds(frameIndex, handle).toFixed(3);
        console.log(`Detected '${displayNames[keywordIndex]}' @ ${timestamp}s`);
      }
    }
  } finally {
    if (handle) {
      handle.release();
    }
  }
}

function main(argv) {
  const opts = parseArgs(argv);

  if (opts.help || argv.length === 0) {
    console.log(usage());
    return 0;
  }

  if (opts["list-keywords"]) {
    console.log(displayBuiltinKeywords());
    return 0;
  }

  if (opts["show-inference-devices"]) {
    printInferenceDevices(opts);
    return 0;
  }

  runDetection(opts);
  return 0;
}

try {
  process.exitCode = main(process.argv.slice(2));
} catch (error) {
  console.error(error && error.stack ? error.stack : error);
  process.exitCode = 1;
}
