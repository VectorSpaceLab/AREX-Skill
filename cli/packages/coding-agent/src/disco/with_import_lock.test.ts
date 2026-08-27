import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";

const scriptPath = path.join(
	process.cwd(),
	"packages/coding-agent/src/disco/skills/verify-repo-skill/scripts/with_import_lock.mjs",
);

function runLocked(agentDir: string, logPath: string, label: string): Promise<void> {
	return new Promise((resolve, reject) => {
		const child = spawn(
			process.execPath,
			[
				scriptPath,
				"--agent-dir",
				agentDir,
				"--timeout",
				"10",
				"--",
				process.execPath,
				"-e",
				[
					"const fs = require('node:fs');",
					"const [logPath] = process.argv.slice(1);",
					`fs.appendFileSync(logPath, ${JSON.stringify(`${label} start\n`)});`,
					"setTimeout(() => {",
					`  fs.appendFileSync(logPath, ${JSON.stringify(`${label} end\n`)});`,
					"}, 350);",
				].join("\n"),
				logPath,
				label,
			],
			{ stdio: ["ignore", "pipe", "pipe"] },
		);

		let stderr = "";
		child.stderr.on("data", (chunk) => {
			stderr += String(chunk);
		});
		child.on("error", reject);
		child.on("close", (code) => {
			if (code === 0) {
				resolve();
			} else {
				reject(new Error(`locked command failed with ${code}: ${stderr}`));
			}
		});
	});
}

describe("with_import_lock.mjs", () => {
	it("serializes concurrent import transactions", async () => {
		const tempRoot = await mkdtemp(path.join(tmpdir(), "disco-import-lock-"));
		try {
			const agentDir = path.join(tempRoot, "agent");
			const logPath = path.join(tempRoot, "critical-section.log");
			await writeFile(logPath, "", "utf-8");

			await Promise.all([runLocked(agentDir, logPath, "a"), runLocked(agentDir, logPath, "b")]);

			const lines = (await readFile(logPath, "utf-8")).trim().split(/\r?\n/);
			expect(lines).toHaveLength(4);
			expect(new Set(lines)).toEqual(new Set(["a start", "a end", "b start", "b end"]));

			const aStart = lines.indexOf("a start");
			const aEnd = lines.indexOf("a end");
			const bStart = lines.indexOf("b start");
			const bEnd = lines.indexOf("b end");
			expect(aStart).toBeGreaterThanOrEqual(0);
			expect(aEnd).toBeGreaterThan(aStart);
			expect(bStart).toBeGreaterThanOrEqual(0);
			expect(bEnd).toBeGreaterThan(bStart);
			expect(aEnd < bStart || bEnd < aStart).toBe(true);
		} finally {
			await rm(tempRoot, { recursive: true, force: true });
		}
	});
});
