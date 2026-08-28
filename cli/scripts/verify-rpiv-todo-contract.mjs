import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createJiti } from "jiti";

const TODO_VERSION = "2.7.1";
const tempRoot = mkdtempSync(join(tmpdir(), "disco-rpiv-todo-contract-"));

function runNpm(args) {
	const npmExecPath = process.env.npm_execpath;
	const command = npmExecPath ? process.execPath : process.platform === "win32" ? "npm.cmd" : "npm";
	const commandArgs = npmExecPath ? [npmExecPath, ...args] : args;
	const result = spawnSync(command, commandArgs, {
		encoding: "utf8",
		stdio: ["ignore", "pipe", "pipe"],
	});
	if (result.status !== 0) {
		throw new Error(`npm ${args.join(" ")} failed:\n${result.stderr || result.stdout}`);
	}
}

function mutate(store, reducer, sessionId, action, params) {
	const result = reducer.applyTaskMutation(store.getState(sessionId), action, params);
	assert.notEqual(result.op.kind, "error", result.op.message);
	store.commitState(sessionId, result.state);
}

try {
	runNpm([
		"install",
		"--prefix",
		tempRoot,
		"--ignore-scripts",
		"--legacy-peer-deps",
		"--no-save",
		"--no-package-lock",
		"--no-audit",
		"--no-fund",
		`@juicesharp/rpiv-todo@${TODO_VERSION}`,
	]);

	const packageRoot = join(tempRoot, "node_modules", "@juicesharp", "rpiv-todo");
	const packageJson = JSON.parse(readFileSync(join(packageRoot, "package.json"), "utf8"));
	assert.equal(packageJson.version, TODO_VERSION);

	const jiti = createJiti(import.meta.url, { interopDefault: true });
	const store = await jiti.import(join(packageRoot, "state", "store.ts"));
	const reducer = await jiti.import(join(packageRoot, "state", "state-reducer.ts"));
	store.__resetState();

	store.replaceState("main", {
		tasks: [{ id: 1, subject: "Inspect distillation contract and evidence", status: "in_progress" }],
		nextId: 2,
	});
	store.setActiveRenderSession("main");
	store.replaceState("child-inference", { tasks: [], nextId: 1 });
	mutate(store, reducer, "child-inference", "create", { subject: "Draft inference sub-skill" });
	store.replaceState("child-evaluation", { tasks: [], nextId: 1 });
	mutate(store, reducer, "child-evaluation", "create", { subject: "Draft evaluation sub-skill" });

	assert.deepEqual(store.getState("main"), {
		tasks: [{ id: 1, subject: "Inspect distillation contract and evidence", status: "in_progress" }],
		nextId: 2,
	});
	assert.deepEqual(store.getState("child-inference"), {
		tasks: [{ id: 1, subject: "Draft inference sub-skill", status: "pending" }],
		nextId: 2,
	});
	assert.deepEqual(store.getState("child-evaluation"), {
		tasks: [{ id: 1, subject: "Draft evaluation sub-skill", status: "pending" }],
		nextId: 2,
	});

	store.evictSession("child-inference");
	assert.deepEqual(store.getState("child-inference"), { tasks: [], nextId: 1 });
	assert.equal(store.getState("main").tasks.length, 1);
	assert.equal(store.getActiveRenderSession(), "main");

	store.__resetState();
	mutate(store, reducer, "main", "create", { subject: "A" });
	mutate(store, reducer, "main", "create", { subject: "B" });
	mutate(store, reducer, "main", "create", { subject: "C" });
	mutate(store, reducer, "main", "update", { id: 2, status: "completed" });
	mutate(store, reducer, "main", "update", { id: 3, status: "in_progress" });
	assert.deepEqual(store.getState("main"), {
		tasks: [
			{ id: 1, subject: "A", status: "pending" },
			{ id: 2, subject: "B", status: "completed" },
			{ id: 3, subject: "C", status: "in_progress" },
		],
		nextId: 4,
	});

	console.log(`Verified @juicesharp/rpiv-todo@${TODO_VERSION} session isolation and task ordering.`);
} finally {
	rmSync(tempRoot, { recursive: true, force: true });
}
