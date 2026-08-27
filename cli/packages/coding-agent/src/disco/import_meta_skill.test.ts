import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, readdir, readFile, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";

const scriptPath = path.join(process.cwd(), "packages/coding-agent/src/disco/skills/design-meta-skill/scripts/import_meta_skill.mjs");
const cleanupPaths: string[] = [];

function runImporter(agentDir: string, draftDir: string, extraArgs: string[] = []) {
	return spawnSync(process.execPath, [scriptPath, "--agent-dir", agentDir, ...extraArgs, draftDir], {
		encoding: "utf8",
		env: { ...process.env, DISCO_IMPORT_LOCK_PATH: "" },
	});
}

async function writeCandidate(draftRoot: string, skillId: string, revision: string, role = "meta"): Promise<string> {
	const candidate = path.join(draftRoot, skillId);
	await mkdir(candidate, { recursive: true });
	await writeFile(
		path.join(candidate, "SKILL.md"),
		[
			"---",
			`name: ${skillId}`,
			`description: "Construct reusable operating skills from a caller-supplied knowledge source anchor (${revision})."`,
			"metadata:",
			`  disco-role: ${role}`,
			"---",
			"",
			`# Candidate ${revision}`,
			"",
			"Resolve the source, generate an operating graph, run verification, handle failure, require approval, and write a handoff.",
			"Generated runtime skills must declare `metadata.disco-role: operating`.",
			"After verification, assess reusability and select one deployment scope for the whole operating graph.",
			"Use project scope under `<project-dir>/.agents/skills/` when reuse is uncertain or task-bound.",
			"Use managed scope under `~/.disco/agent/skills/` only for evidence-backed cross-project reuse.",
			"Present exact targets for approval, require separate overwrite approval, then write the Researcher handoff.",
		].join("\n"),
		"utf8",
	);
	return candidate;
}

describe("import_meta_skill.mjs", () => {
	afterEach(async () => {
		for (const cleanupPath of cleanupPaths.splice(0)) {
			await rm(cleanupPath, { recursive: true, force: true });
		}
	});

	it("imports only the reviewed runtime directory under the shared lock and validates the installed copy", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-meta-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const runDir = path.join(root, "creator-run");
		const candidate = await writeCandidate(path.join(runDir, "draft"), "source-constructor", "v1");
		await writeFile(path.join(runDir, "capability-matrix.md"), "review-only\n", "utf8");

		const result = runImporter(agentDir, candidate);

		expect(result.status, result.stderr).toBe(0);
		expect(result.stdout).toContain("imported and validated meta skill source-constructor");
		expect(result.stdout).toContain("Run /reload, then invoke /skill:source-constructor.");
		const target = path.join(agentDir, "skills", "source-constructor");
		expect(await readFile(path.join(target, "SKILL.md"), "utf8")).toContain("# Candidate v1");
		expect(existsSync(path.join(target, "capability-matrix.md"))).toBe(false);
		expect(existsSync(path.join(agentDir, "locks", "repo-skills-import.lockdir"))).toBe(false);
	});

	it("rejects a same-name target until overwrite is explicit", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-meta-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const draftRoot = path.join(root, "draft");
		const candidate = await writeCandidate(draftRoot, "source-constructor", "v1");
		expect(runImporter(agentDir, candidate).status).toBe(0);
		await writeCandidate(draftRoot, "source-constructor", "v2");

		const conflict = runImporter(agentDir, candidate);
		expect(conflict.status).toBe(2);
		expect(conflict.stderr).toContain("Obtain separate overwrite approval");
		const targetFile = path.join(agentDir, "skills", "source-constructor", "SKILL.md");
		expect(await readFile(targetFile, "utf8")).toContain("# Candidate v1");

		const overwrite = runImporter(agentDir, candidate, ["--overwrite"]);
		expect(overwrite.status, overwrite.stderr).toBe(0);
		expect(await readFile(targetFile, "utf8")).toContain("# Candidate v2");
	});

	it("never changes an operating target into a meta skill", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-meta-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const liveTarget = path.join(agentDir, "skills", "source-constructor");
		await mkdir(liveTarget, { recursive: true });
		const liveFile = path.join(liveTarget, "SKILL.md");
		await writeFile(
			liveFile,
			[
				"---",
				"name: source-constructor",
				'description: "Execute the existing operating workflow."',
				"metadata:",
				"  disco-role: operating",
				"---",
				"",
				"# Existing operating skill",
			].join("\n"),
			"utf8",
		);
		const candidate = await writeCandidate(path.join(root, "draft"), "source-constructor", "meta-v2");

		const result = runImporter(agentDir, candidate, ["--overwrite"]);

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("refusing to replace non-meta skill target");
		expect(await readFile(liveFile, "utf8")).toContain("disco-role: operating");
	});

	it("leaves the live target unchanged when candidate validation fails", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-meta-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const draftRoot = path.join(root, "draft");
		const candidate = await writeCandidate(draftRoot, "source-constructor", "valid");
		expect(runImporter(agentDir, candidate).status).toBe(0);
		await writeCandidate(draftRoot, "source-constructor", "invalid", "operating");

		const failed = runImporter(agentDir, candidate, ["--overwrite"]);

		expect(failed.status).toBe(2);
		expect(failed.stderr).toContain("metadata.disco-role must be meta");
		const targetFile = path.join(agentDir, "skills", "source-constructor", "SKILL.md");
		expect(await readFile(targetFile, "utf8")).toContain("# Candidate valid");
		expect(
			(await readdir(path.join(agentDir, "skills"))).filter((entry) => entry.startsWith(".meta-skill-")),
		).toEqual([]);
	});

	it("rejects shared as a live meta-skill role", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-meta-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const candidate = await writeCandidate(path.join(root, "draft"), "shared-constructor", "shared", "shared");

		const result = runImporter(agentDir, candidate);

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("metadata.disco-role must be meta");
		expect(existsSync(path.join(agentDir, "skills", "shared-constructor"))).toBe(false);
	});

	it("rejects a meta skill that does not define project and managed operating deployment", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-meta-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const candidate = await writeCandidate(path.join(root, "draft"), "source-constructor", "missing-policy");
		const skillFile = path.join(candidate, "SKILL.md");
		const content = await readFile(skillFile, "utf8");
		await writeFile(
			skillFile,
			content.replace(
				"Use project scope under `<project-dir>/.agents/skills/` when reuse is uncertain or task-bound.",
				"Keep task-bound output staged outside the live skills directories.",
			),
			"utf8",
		);

		const result = runImporter(agentDir, candidate);

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("must define the project operating-skill target under .agents/skills");
		expect(existsSync(path.join(agentDir, "skills", "source-constructor"))).toBe(false);
	});

	it("rejects target-specific agents manifests in a DisCo meta skill", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-meta-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const candidate = await writeCandidate(path.join(root, "draft"), "source-constructor", "codex-manifest");
		const agentsDir = path.join(candidate, "agents");
		await mkdir(agentsDir);
		await writeFile(
			path.join(agentsDir, "openai.yaml"),
			'interface:\n  display_name: "Source Constructor"\n',
			"utf8",
		);

		const result = runImporter(agentDir, candidate);

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("agents directories are target-specific manifests");
		expect(existsSync(path.join(agentDir, "skills", "source-constructor"))).toBe(false);
	});

	it("rejects symbolic links before copying a non-portable candidate", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-meta-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const draftRoot = path.join(root, "draft");
		const candidate = await writeCandidate(draftRoot, "source-constructor", "linked");
		await writeFile(path.join(draftRoot, "review-only.md"), "not runtime content\n", "utf8");
		await symlink(path.join(draftRoot, "review-only.md"), path.join(candidate, "review-only.md"));

		const result = runImporter(agentDir, candidate);

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("contains a symbolic link");
		expect(existsSync(path.join(agentDir, "skills", "source-constructor"))).toBe(false);
	});

	it("requires proof of the shared lock for --already-locked", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-meta-import-"));
		cleanupPaths.push(root);
		const agentDir = path.join(root, "agent");
		const candidate = await writeCandidate(path.join(root, "draft"), "source-constructor", "v1");

		const result = runImporter(agentDir, candidate, ["--already-locked"]);

		expect(result.status).toBe(2);
		expect(result.stderr).toContain("--already-locked requires DISCO_IMPORT_LOCK_PATH");
		expect(existsSync(path.join(agentDir, "skills", "source-constructor"))).toBe(false);
	});
});
