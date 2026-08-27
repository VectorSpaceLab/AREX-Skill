#!/usr/bin/env node
/** DisCo CLI process entry point. */
import { isolateDisCoProcessFromPiEnvironment } from "./cli/pi-environment-isolation.ts";

process.env.DISCO_CODING_AGENT = "true";
process.emitWarning = (() => {}) as typeof process.emitWarning;
isolateDisCoProcessFromPiEnvironment();

const [{ APP_NAME }, { configureHttpDispatcher }, { main }] = await Promise.all([
	import("./config.ts"),
	import("./core/http-dispatcher.ts"),
	import("./main.ts"),
]);

process.title = APP_NAME;

// Configure undici's global dispatcher before provider SDKs issue requests.
// Runtime settings are applied once SettingsManager has loaded global/project settings.
configureHttpDispatcher();

await main(process.argv.slice(2));
