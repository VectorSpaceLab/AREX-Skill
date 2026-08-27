#!/usr/bin/env node
/**
 * Run a DisCo import/update command under the shared skill import lock.
 *
 * The lock serializes writes to DisCo's managed user skill library and its
 * live repo-skills-router across concurrent agent sessions. It intentionally
 * uses a directory lock so the helper works from the npm package without a
 * Python runtime or native fcntl bindings.
 *
 * Example:
 *   node with_import_lock.mjs -- node scripts/import_skill.mjs
 */

import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_TIMEOUT_SECONDS = 900;
const STALE_AFTER_SECONDS = 3600;
const POLL_SECONDS = 0.25;

function defaultAgentDir() {
	return process.env.DISCO_CODING_AGENT_DIR || path.join(os.homedir(), ".disco", "agent");
}

function sleep(ms) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseArgs(argv) {
	const args = {
		agentDir: defaultAgentDir(),
		timeout: DEFAULT_TIMEOUT_SECONDS,
		staleAfter: STALE_AFTER_SECONDS,
		command: [],
	};

	for (let index = 0; index < argv.length; index += 1) {
		const value = argv[index];
		if (value === "--") {
			args.command = argv.slice(index + 1);
			return args;
		}
		if (value === "--agent-dir") {
			args.agentDir = argv[++index];
		} else if (value === "--timeout") {
			args.timeout = Number(argv[++index]);
		} else if (value === "--stale-after") {
			args.staleAfter = Number(argv[++index]);
		} else if (value === "-h" || value === "--help") {
			printHelp();
			process.exit(0);
		} else {
			args.command = argv.slice(index);
			return args;
		}
	}

	return args;
}

function printHelp() {
	console.log(`Usage: node with_import_lock.mjs [--agent-dir DIR] [--timeout SECONDS] [--stale-after SECONDS] -- COMMAND [ARGS...]

Run COMMAND while holding the DisCo skill import lock.`);
}

function ownerPayload() {
	return {
		pid: process.pid,
		host: os.hostname(),
		started_at: new Date().toISOString(),
		argv: process.argv,
	};
}

function writeOwner(lockDir) {
	fs.writeFileSync(path.join(lockDir, "owner.json"), `${JSON.stringify(ownerPayload(), null, 2)}\n`, "utf8");
}

function isStale(lockDir, staleAfterSeconds) {
	try {
		const stat = fs.statSync(path.join(lockDir, "owner.json"));
		return Date.now() - stat.mtimeMs > staleAfterSeconds * 1000;
	} catch (error) {
		if (error && error.code === "ENOENT") {
			return false;
		}
		return false;
	}
}

function startHeartbeat(lockDir, intervalSeconds) {
	const ownerFile = path.join(lockDir, "owner.json");
	const timer = setInterval(() => {
		const now = new Date();
		try {
			fs.utimesSync(ownerFile, now, now);
			fs.utimesSync(lockDir, now, now);
		} catch (error) {
			if (!error || error.code !== "ENOENT") {
				// Keep the lock holder alive even if timestamp refresh fails.
			}
		}
	}, Math.max(1000, intervalSeconds * 1000));
	timer.unref();
	return () => clearInterval(timer);
}

async function acquireDirectoryLock(lockDir, timeoutSeconds, staleAfterSeconds) {
	const deadline = Date.now() + timeoutSeconds * 1000;

	for (;;) {
		try {
			fs.mkdirSync(path.dirname(lockDir), { recursive: true });
			fs.mkdirSync(lockDir);
			writeOwner(lockDir);
			const stopHeartbeat = startHeartbeat(lockDir, Math.min(Math.max(POLL_SECONDS, 1), staleAfterSeconds / 4));
			return {
				lockPath: lockDir,
				release() {
					stopHeartbeat();
					fs.rmSync(lockDir, { recursive: true, force: true });
				},
			};
		} catch (error) {
			if (!error || error.code !== "EEXIST") {
				throw error;
			}
			if (isStale(lockDir, staleAfterSeconds)) {
				fs.rmSync(lockDir, { recursive: true, force: true });
				continue;
			}
			if (Date.now() >= deadline) {
				throw new Error(`timed out waiting for import lock at ${lockDir}`);
			}
			await sleep(POLL_SECONDS * 1000);
		}
	}
}

function runCommand(command, env) {
	return new Promise((resolve, reject) => {
		const child = spawn(command[0], command.slice(1), {
			env,
			stdio: "inherit",
			shell: false,
		});
		child.on("error", reject);
		child.on("close", (code, signal) => {
			if (signal) {
				resolve(128);
			} else {
				resolve(code ?? 0);
			}
		});
	});
}

async function main(argv) {
	const args = parseArgs(argv);
	if (!args.command.length) {
		console.error("with_import_lock.mjs: provide a command after '--'");
		return 2;
	}
	if (!Number.isFinite(args.timeout) || args.timeout <= 0) {
		console.error("with_import_lock.mjs: --timeout must be a positive number");
		return 2;
	}
	if (!Number.isFinite(args.staleAfter) || args.staleAfter <= 0) {
		console.error("with_import_lock.mjs: --stale-after must be a positive number");
		return 2;
	}

	const agentDir = path.resolve(args.agentDir.replace(/^~(?=$|[\\/])/, os.homedir()));
	const lockDir = path.join(agentDir, "locks", "repo-skills-import.lockdir");

	let lock;
	try {
		lock = await acquireDirectoryLock(lockDir, args.timeout, args.staleAfter);
		const env = {
			...process.env,
			DISCO_IMPORT_LOCK_PATH: lock.lockPath,
			DISCO_CODING_AGENT_DIR: agentDir,
		};
		return await runCommand(args.command, env);
	} catch (error) {
		console.error(error instanceof Error ? error.message : String(error));
		return /timed out waiting/.test(String(error)) ? 75 : 1;
	} finally {
		if (lock) {
			lock.release();
		}
	}
}

process.exitCode = await main(process.argv.slice(2));
