#!/usr/bin/env node
import process from "node:process";

function parseArgs(argv) {
  const args = {
    baseUrl: process.env.R2R_API_BASE || "http://localhost:7272",
    apiKey: process.env.R2R_API_KEY || "",
    live: false,
    health: false,
    json: false,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--base-url") {
      args.baseUrl = argv[++i];
    } else if (arg === "--api-key") {
      args.apiKey = argv[++i];
    } else if (arg === "--live") {
      args.live = true;
    } else if (arg === "--health") {
      args.health = true;
    } else if (arg === "--json") {
      args.json = true;
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return args;
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help) {
    console.log(
      "Usage: js_sdk_quickstart.mjs [--base-url URL] [--api-key KEY] [--live] [--health] [--json]\n",
    );
    console.log(
      "Print a safe JavaScript SDK quickstart or optionally probe the live R2R health endpoint.",
    );
    return 0;
  }

  const payload = {
    baseUrl: args.baseUrl,
    apiKeySet: Boolean(args.apiKey),
    live: args.live,
    health: args.health,
  };

  if (!args.live) {
    const snippet = [
      'const { r2rClient } = require("r2r-js");',
      `const client = new r2rClient("${args.baseUrl}");`,
      args.apiKey
        ? "client.setApiKey(process.env.R2R_API_KEY);"
        : "// set an API key or use login() when needed",
      "const health = await client.system.health();",
      "console.log(health.results);",
    ].join("\n");

    if (args.json) {
      console.log(JSON.stringify({ ...payload, snippet }, null, 2));
    } else {
      console.log(snippet);
    }
    return 0;
  }

  const { r2rClient } = await import("r2r-js");
  const client = new r2rClient(args.baseUrl);
  if (args.apiKey) {
    client.setApiKey(args.apiKey);
  }

  const report = { ...payload };
  if (args.health) {
    const response = await client.system.health();
    report.health = response.results;
  }

  console.log(JSON.stringify(report, null, 2));
  return 0;
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
