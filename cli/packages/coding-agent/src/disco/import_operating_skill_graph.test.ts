import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, readdir, readFile, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";

const scriptPath = path.join(
	process.cwd(),
	"packages/coding-agent/src/disco/skills/distill-ml-knowledge/scripts/import_operating_skill_graph.mjs",
);
const cleanupPaths: string[] = [];

type RunOptions = {
	scope: "project" | "managed";
	agentDir: string;
	projectDir?: string;
	cwd?: string;
	draftDirs: string[];
	extraArgs?: string[];
	env?: Record<string, string>;
};

function runImporter(options: RunOptions) {
	const args = [scriptPath, "--scope", options.scope, "--agent-dir", options.agentDir];
	if (options.projectDir) args.push("--project-dir", options.projectDir);
	args.push(...(options.extraArgs ?? []), ...options.draftDirs);
	return spawnSync(process.execPath, args, {
		encoding: "utf8",
		cwd: options.cwd,
		env: {
			...process.env,
			NODE_ENV: "test",
			DISCO_IMPORT_LOCK_PATH: "",
			...options.env,
		},
	});
}

async function writeOperatingSkill(
	draftRoot: string,
	skillId: string,
	revision: string,
	options: { role?: string; linkTo?: string; repoRouting?: boolean } = {},
): Promise<string> {
	const candidate = path.join(draftRoot, skillId);
	await mkdir(candidate, { recursive: true });
	const lines = [
		"---",
		`name: ${skillId}`,
		`description: "Use ${skillId} to execute a verified ML research workflow (${revision})."`,
		"metadata:",
		`  disco-role: ${options.role ?? "operating"}`,
		"---",
		"",
		`# ${skillId} ${revision}`,
		"",
		"Execute the operating workflow and verify its observable result.",
	];
	if (options.linkTo) lines.push("", `[Peer skill](${options.linkTo})`);
	await writeFile(path.join(candidate, "SKILL.md"), lines.join("\n"), "utf8");
	if (options.repoRouting) {
		await mkdir(path.join(candidate, "references"), { recursive: true });
		await writeFile(path.join(candidate, "references", "repo-routing-metadata.json"), "{}\n", "utf8");
	}
	return candidate;
}

async function listTransactionArtifacts(skillsRoot: string): Promise<string[]> {
	if (!existsSync(skillsRoot)) return [];
	return (await readdir(skillsRoot)).filter(
		(entry) => entry.startsWith(".operating-skill-import.") || entry.startsWith(".operating-skill-backup."),
	);
}

describe("import_operating_skill_graph.mjs", () => {
	afterEach(async () => {
		for (const cleanupPath of cleanupPaths.splice(0)) {
			await rm(cleanupPath, { recursive: true, force: true });
		}
	});

	it("imports task-bound output into the current project's .agents/skills directory", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
		cleanupPaths.push(root);
		const projectDir = path.join(root, "project");
		const agentDir = path.join(root, "agent");
		await mkdir(projectDir);
		const candidate = await writeOperatingSkill(path.join(root, "draft"), "task-evaluator", "v1");
		await writeFile(path.join(root, "review.md"), "review-only\n", "utf8");

		const result = runImporter({ scope: "project", agentDir, projectDir, draftDirs: [candidate] });

		expect(result.status, result.stderr).toBe(0);
		expect(result.stdout).toContain("operating-skill graph (scope: project)");
		const target = path.join(projectDir, ".agents", "skills", "task-evaluator");
		expect(await readFile(path.join(target, "SKILL.md"), "utf8")).toContain("# task-evaluator v1");
		expect(existsSync(path.join(target, "review.md"))).toBe(false);
		expect(existsSync(path.join(agentDir, "skills", "task-evaluator"))).toBe(false);
		expect(await listTransactionArtifacts(path.dirname(target))).toEqual([]);
		expect(existsSync(path.join(agentDir, "locks", "repo-skills-import.lockdir"))).toBe(false);
	});

	it("defaults project scope to the invocation working directory", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
		cleanupPaths.push(root);
		const projectDir = path.join(root, "working-project");
		const agentDir = path.join(root, "agent");
		await mkdir(projectDir);
		const candidate = await writeOperatingSkill(path.join(root, "draft"), "local-method", "v1");

		const result = runImporter({
			scope: "project",
			agentDir,
			cwd: projectDir,
			draftDirs: [candidate],
		});

		expect(result.status, result.stderr).toBe(0);
		expect(result.stdout).toContain(`project: ${projectDir}`);
		expect(existsSync(path.join(projectDir, ".agents", "skills", "local-method", "SKILL.md"))).toBe(true);
	});

	it("imports a reusable multi-root graph into the managed library in one transaction", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const draftRoot = path.join(root, "draft");
		const first = await writeOperatingSkill(draftRoot, "shared-router", "v1", {
			linkTo: "../shared-worker/SKILL.md",
		});
		const second = await writeOperatingSkill(draftRoot, "shared-worker", "v1");

		const result = runImporter({ scope: "managed", agentDir, draftDirs: [first, second] });

		expect(result.status, result.stderr).toBe(0);
		expect(result.stdout).toContain("operating-skill graph (scope: managed)");
		expect(await readFile(path.join(agentDir, "skills", "shared-router", "SKILL.md"), "utf8")).toContain(
			"../shared-worker/SKILL.md",
		);
		expect(await readFile(path.join(agentDir, "skills", "shared-worker", "SKILL.md"), "utf8")).toContain(
			"# shared-worker v1",
		);
		expect(await listTransactionArtifacts(path.join(agentDir, "skills"))).toEqual([]);
	});

	it("rejects meta or unclassified skills before changing the live target", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const candidate = await writeOperatingSkill(path.join(root, "draft"), "wrong-role", "v1", { role: "meta" });

		const result = runImporter({ scope: "managed", agentDir, draftDirs: [candidate] });

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("metadata.disco-role must be operating");
		expect(existsSync(path.join(agentDir, "skills", "wrong-role"))).toBe(false);
	});

	it("rejects shared as an operating graph role", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const candidate = await writeOperatingSkill(path.join(root, "draft"), "shared-role", "v1", { role: "shared" });

		const result = runImporter({ scope: "managed", agentDir, draftDirs: [candidate] });

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("metadata.disco-role must be operating");
		expect(existsSync(path.join(agentDir, "skills", "shared-role"))).toBe(false);
	});

	it("requires separate overwrite authorization for a same-name target", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const draftRoot = path.join(root, "draft");
		const candidate = await writeOperatingSkill(draftRoot, "shared-method", "v1");
		expect(runImporter({ scope: "managed", agentDir, draftDirs: [candidate] }).status).toBe(0);
		await writeOperatingSkill(draftRoot, "shared-method", "v2");

		const conflict = runImporter({ scope: "managed", agentDir, draftDirs: [candidate] });
		expect(conflict.status).toBe(2);
		expect(conflict.stderr).toContain("Obtain separate overwrite approval");
		const targetFile = path.join(agentDir, "skills", "shared-method", "SKILL.md");
		expect(await readFile(targetFile, "utf8")).toContain("# shared-method v1");

		const overwrite = runImporter({
			scope: "managed",
			agentDir,
			draftDirs: [candidate],
			extraArgs: ["--overwrite"],
		});
		expect(overwrite.status, overwrite.stderr).toBe(0);
		expect(await readFile(targetFile, "utf8")).toContain("# shared-method v2");
	});

	it.each(["project", "managed"] as const)(
		"never replaces a %s-scope meta skill with an operating graph",
		async (scope) => {
			const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
			cleanupPaths.push(root);
			const agentDir = path.join(root, "agent");
			const projectDir = path.join(root, "project");
			await mkdir(projectDir);
			const liveRoot =
				scope === "managed" ? path.join(agentDir, "skills") : path.join(projectDir, ".agents", "skills");
			const liveMeta = await writeOperatingSkill(liveRoot, "scope-designer", "meta-v1", {
				role: "meta",
			});
			const candidate = await writeOperatingSkill(path.join(root, "draft"), "scope-designer", "operating-v1");

			const result = runImporter({
				scope,
				agentDir,
				projectDir: scope === "project" ? projectDir : undefined,
				draftDirs: [candidate],
				extraArgs: ["--overwrite"],
			});

			expect(result.status).toBe(2);
			expect(result.stderr).toContain("refusing to replace meta skill");
			expect(await readFile(path.join(liveMeta, "SKILL.md"), "utf8")).toContain("# scope-designer meta-v1");
			expect(await listTransactionArtifacts(liveRoot)).toEqual([]);
		},
	);

	it("rolls back every root when a multi-root replacement fails", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const draftRoot = path.join(root, "draft");
		const first = await writeOperatingSkill(draftRoot, "graph-root", "v1");
		const second = await writeOperatingSkill(draftRoot, "graph-worker", "v1");
		expect(runImporter({ scope: "managed", agentDir, draftDirs: [first, second] }).status).toBe(0);
		await writeOperatingSkill(draftRoot, "graph-root", "v2");
		await writeOperatingSkill(draftRoot, "graph-worker", "v2");

		const failed = runImporter({
			scope: "managed",
			agentDir,
			draftDirs: [first, second],
			extraArgs: ["--overwrite"],
			env: { DISCO_TEST_FAIL_OPERATING_IMPORT_AFTER: "1" },
		});

		expect(failed.status).toBe(2);
		expect(failed.stderr).toContain("injected operating-skill import failure");
		expect(await readFile(path.join(agentDir, "skills", "graph-root", "SKILL.md"), "utf8")).toContain(
			"# graph-root v1",
		);
		expect(await readFile(path.join(agentDir, "skills", "graph-worker", "SKILL.md"), "utf8")).toContain(
			"# graph-worker v1",
		);
		expect(await listTransactionArtifacts(path.join(agentDir, "skills"))).toEqual([]);
	});

	it("rejects repo-routed output so the specialized router transaction remains authoritative", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const candidate = await writeOperatingSkill(path.join(root, "draft"), "repo-package", "v1", {
			repoRouting: true,
		});

		const result = runImporter({ scope: "managed", agentDir, draftDirs: [candidate] });

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("use verify-repo-skill's locked repo import and router rebuild");
		expect(existsSync(path.join(agentDir, "skills", "repo-package"))).toBe(false);
	});

	it("rejects symbolic links instead of copying non-portable graph content", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-operating-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const draftRoot = path.join(root, "draft");
		const candidate = await writeOperatingSkill(draftRoot, "linked-method", "v1");
		await writeFile(path.join(draftRoot, "outside.md"), "outside\n", "utf8");
		await symlink(path.join(draftRoot, "outside.md"), path.join(candidate, "outside.md"));

		const result = runImporter({ scope: "managed", agentDir, draftDirs: [candidate] });

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("contains a symbolic link");
		expect(existsSync(path.join(agentDir, "skills", "linked-method"))).toBe(false);
	});
});
