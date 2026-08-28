import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { copyFile, mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";

const exportScript = path.join(
	process.cwd(),
	"packages/coding-agent/src/disco/skills/import-repo-skills-to-agent/scripts/export_repo_skills_to_agent.mjs",
);
const updaterScript = path.join(
	process.cwd(),
	"packages/coding-agent/src/disco/skills/verify-repo-skill/scripts/update_repo_skills_router.mjs",
);
const routerTemplate = path.join(
	process.cwd(),
	"packages/coding-agent/src/disco/skills/repo-skills-router",
);
const taxonomyPath = path.join(routerTemplate, "references", "index", "taxonomy.json");
const taxonomySha256 = createHash("sha256").update(readFileSync(taxonomyPath)).digest("hex");
const cleanup: string[] = [];

interface SkillDefinition {
	id: string;
	repoId: string;
	area: string;
	family: string;
}

const alpha: SkillDefinition = {
	id: "alpha-repo",
	repoId: "owner/alpha-repo",
	area: "Computer Vision",
	family: "Image Classification",
};
const beta: SkillDefinition = {
	id: "beta-repo",
	repoId: "owner/beta-repo",
	area: "Natural Language Processing",
	family: "Text Generation",
};

async function writeSkill(libraryRoot: string, definition: SkillDefinition): Promise<void> {
	const skillRoot = path.join(libraryRoot, "repo-skills", definition.id);
	const subSkillRoot = path.join(skillRoot, "sub-skills", "setup");
	await mkdir(path.join(skillRoot, "references"), { recursive: true });
	await mkdir(subSkillRoot, { recursive: true });
	await writeFile(
		path.join(skillRoot, "SKILL.md"),
		[
			"---",
			`name: ${definition.id}`,
			`description: \"Use ${definition.id} for focused repository workflows.\"`,
			"disable-model-invocation: true",
			"license: MIT",
			"metadata:",
			"  disco-role: operating",
			"---",
			"",
			`# ${definition.id}`,
			"",
			"[Setup](sub-skills/setup/SKILL.md)",
			"",
		].join("\n"),
		"utf8",
	);
	await writeFile(
		path.join(subSkillRoot, "SKILL.md"),
		[
			"---",
			"name: setup",
			'description: "Set up the repository workflow."',
			"disable-model-invocation: true",
			"license: MIT",
			"metadata:",
			"  disco-role: operating",
			"---",
			"",
			"# Setup",
			"",
		].join("\n"),
		"utf8",
	);
	await writeFile(
		path.join(skillRoot, "references", "repo-routing-metadata.json"),
		`${JSON.stringify({
			schema_version: "2.0",
			repo_id: definition.repoId,
			skill_id: definition.id,
			taxonomy_sha256: taxonomySha256,
			routing_status: "classified",
			assignments: [{ area: definition.area, family: definition.family }],
		}, null, 2)}\n`,
		"utf8",
	);
}

function runUpdater(libraryRoot: string): ReturnType<typeof spawnSync> {
	return spawnSync(
		process.execPath,
		[updaterScript, "--library-root", libraryRoot, "--template-dir", routerTemplate],
		{ encoding: "utf8", env: { ...process.env, NODE_ENV: "test" } },
	);
}

async function createSource(root: string, definitions: SkillDefinition[] = [alpha, beta]): Promise<string> {
	const libraryRoot = path.join(root, "source", "repositories");
	const indexRoot = path.join(libraryRoot, "repo-skills-router", "references", "index");
	await mkdir(path.join(libraryRoot, "repo-skills"), { recursive: true });
	await mkdir(indexRoot, { recursive: true });
	await copyFile(taxonomyPath, path.join(indexRoot, "taxonomy.json"));
	for (const definition of definitions) await writeSkill(libraryRoot, definition);
	await writeFile(
		path.join(indexRoot, "assignments.jsonl"),
		definitions.map((definition) => JSON.stringify({
			repo_id: definition.repoId,
			legacy_repo_id: `legacy/${definition.id}`,
			skill_id: definition.id,
			area: definition.area,
			family: definition.family,
			confidence: "high",
		})).join("\n") + "\n",
		"utf8",
	);
	const result = runUpdater(libraryRoot);
	if (result.status !== 0) throw new Error(result.stderr || result.stdout);
	return libraryRoot;
}

function runExport(args: string[], env: Record<string, string> = {}): ReturnType<typeof spawnSync> {
	return spawnSync(process.execPath, [exportScript, ...args], {
		encoding: "utf8",
		env: { ...process.env, NODE_ENV: "test", ...env },
	});
}

function exportArgs(source: string, targetSkillsRoot: string, extra: string[] = []): string[] {
	return [
		"--source-library-root",
		source,
		"--target-skills-root",
		targetSkillsRoot,
		...extra,
	];
}

async function readJsonLines(filePath: string): Promise<Array<Record<string, unknown>>> {
	return (await readFile(filePath, "utf8"))
		.split(/\r?\n/)
		.filter(Boolean)
		.map((line) => JSON.parse(line) as Record<string, unknown>);
}

async function snapshotTree(root: string): Promise<string> {
	const hash = createHash("sha256");
	async function visit(directory: string): Promise<void> {
		if (!existsSync(directory)) return;
		for (const entry of (await readdir(directory, { withFileTypes: true })).sort((left, right) => left.name.localeCompare(right.name))) {
			const entryPath = path.join(directory, entry.name);
			const relativePath = path.relative(root, entryPath).split(path.sep).join("/");
			if (entry.isDirectory()) {
				hash.update(`dir\0${relativePath}\0`);
				await visit(entryPath);
			} else {
				const content = await readFile(entryPath);
				hash.update(`file\0${relativePath}\0${content.byteLength}\0`);
				hash.update(content);
				hash.update("\0");
			}
		}
	}
	await visit(root);
	return hash.digest("hex");
}

async function transactionDirectories(targetSkillsRoot: string): Promise<string[]> {
	const parent = path.dirname(targetSkillsRoot);
	if (!existsSync(parent)) return [];
	return (await readdir(parent, { withFileTypes: true }))
		.filter((entry) => entry.isDirectory() && entry.name.startsWith(".repo-skills-export-"))
		.map((entry) => path.join(parent, entry.name))
		.sort();
}

describe("export_repo_skills_to_agent.mjs", () => {
	afterEach(async () => {
		for (const root of cleanup.splice(0)) await rm(root, { recursive: true, force: true });
	});

	it("exports a full collection into a fresh target and regenerates matching indexes", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-full-"));
		cleanup.push(root);
		const source = await createSource(root);
		const targetSkillsRoot = path.join(root, "target", "skills");
		const sourceBefore = await snapshotTree(source);

		const result = runExport(exportArgs(source, targetSkillsRoot));
		expect(result.status, result.stderr).toBe(0);
		const targetCollection = path.join(targetSkillsRoot, "repositories");
		expect(existsSync(path.join(targetCollection, "repo-skills", alpha.id, "SKILL.md"))).toBe(true);
		expect(existsSync(path.join(targetCollection, "repo-skills", beta.id, "SKILL.md"))).toBe(true);
		const rootIndex = await readFile(path.join(targetCollection, "repo-skills", "repository-index.jsonl"), "utf8");
		const routerIndex = await readFile(path.join(targetCollection, "repo-skills-router", "references", "index", "repositories.jsonl"), "utf8");
		expect(rootIndex).toBe(routerIndex);
		expect((await readJsonLines(path.join(targetCollection, "repo-skills-router", "references", "index", "assignments.jsonl")))).toHaveLength(2);
		expect(await snapshotTree(source)).toBe(sourceBefore);
		expect(await transactionDirectories(targetSkillsRoot)).toEqual([]);
	});

	it("exports only the selected subset and does not leak unselected source records", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-subset-"));
		cleanup.push(root);
		const source = await createSource(root);
		const targetSkillsRoot = path.join(root, "target", "skills");

		const result = runExport(exportArgs(source, targetSkillsRoot, ["--include-skill", alpha.id]));
		expect(result.status, result.stderr).toBe(0);
		const targetCollection = path.join(targetSkillsRoot, "repositories");
		expect(existsSync(path.join(targetCollection, "repo-skills", alpha.id))).toBe(true);
		expect(existsSync(path.join(targetCollection, "repo-skills", beta.id))).toBe(false);
		const repositories = await readJsonLines(path.join(targetCollection, "repo-skills", "repository-index.jsonl"));
		expect(repositories.map((record) => record.skill_id)).toEqual([alpha.id]);
		const routerText = await readFile(path.join(targetCollection, "repo-skills-router", "SKILL.md"), "utf8");
		expect(routerText).not.toContain(beta.id);
	});

	it("exports selected skills when the source preserves GitHub NOASSERTION", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-noassertion-"));
		cleanup.push(root);
		const source = await createSource(root, [alpha]);
		const skillRoot = path.join(source, "repo-skills", alpha.id);
		for (const relativePath of ["SKILL.md", path.join("sub-skills", "setup", "SKILL.md")]) {
			const filePath = path.join(skillRoot, relativePath);
			await writeFile(filePath, (await readFile(filePath, "utf8")).replaceAll("license: MIT", "license: NOASSERTION"), "utf8");
		}

		const targetSkillsRoot = path.join(root, "target", "skills");
		const result = runExport(exportArgs(source, targetSkillsRoot, ["--include-skill", alpha.id]));
		expect(result.status, result.stderr).toBe(0);
		expect(existsSync(path.join(targetSkillsRoot, "repositories", "repo-skills", alpha.id, "SKILL.md"))).toBe(true);
	});

	it("merges a later subset into an existing target and preserves unrelated skills", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-merge-"));
		cleanup.push(root);
		const source = await createSource(root);
		const targetSkillsRoot = path.join(root, "target", "skills");
		const unrelated = path.join(targetSkillsRoot, "unrelated-skill", "SKILL.md");
		await mkdir(path.dirname(unrelated), { recursive: true });
		await writeFile(unrelated, "---\nname: unrelated-skill\ndescription: \"Unrelated.\"\n---\n", "utf8");

		expect(runExport(exportArgs(source, targetSkillsRoot, ["--include-skill", alpha.id])).status).toBe(0);
		const unrelatedBefore = await readFile(unrelated, "utf8");
		const result = runExport(exportArgs(source, targetSkillsRoot, ["--include-skill", beta.id]));
		expect(result.status, result.stderr).toBe(0);
		const targetCollection = path.join(targetSkillsRoot, "repositories");
		const repositories = await readJsonLines(path.join(targetCollection, "repo-skills", "repository-index.jsonl"));
		expect(repositories.map((record) => record.skill_id).sort()).toEqual([alpha.id, beta.id]);
		expect(await readFile(unrelated, "utf8")).toBe(unrelatedBefore);
		expect(await readJsonLines(path.join(targetCollection, "repo-skills-router", "references", "index", "assignments.jsonl"))).toHaveLength(2);
	});

	it("requires explicit approval before replacing a conflicting target skill", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-conflict-"));
		cleanup.push(root);
		const source = await createSource(root);
		const targetSkillsRoot = path.join(root, "target", "skills");
		expect(runExport(exportArgs(source, targetSkillsRoot, ["--include-skill", alpha.id])).status).toBe(0);
		const targetCollection = path.join(targetSkillsRoot, "repositories");
		const before = await snapshotTree(targetCollection);

		const result = runExport(exportArgs(source, targetSkillsRoot, ["--include-skill", alpha.id]));
		expect(result.status).toBe(2);
		expect(result.stderr).toContain(`--overwrite-skill ${alpha.id}`);
		expect(await snapshotTree(targetCollection)).toBe(before);
	});

	it("replaces only an explicitly approved skill and preserves other memberships", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-overwrite-"));
		cleanup.push(root);
		const source = await createSource(root);
		const targetSkillsRoot = path.join(root, "target", "skills");
		expect(runExport(exportArgs(source, targetSkillsRoot)).status).toBe(0);
		const betaBefore = await snapshotTree(path.join(targetSkillsRoot, "repositories", "repo-skills", beta.id));
		await writeFile(path.join(source, "repo-skills", alpha.id, "references", "updated.md"), "updated source\n", "utf8");
		const updateResult = runUpdater(source);
		expect(updateResult.status, updateResult.stderr).toBe(0);

		const result = runExport(exportArgs(source, targetSkillsRoot, [
			"--include-skill",
			alpha.id,
			"--overwrite-skill",
			alpha.id,
		]));
		expect(result.status, result.stderr).toBe(0);
		expect(existsSync(path.join(targetSkillsRoot, "repositories", "repo-skills", alpha.id, "references", "updated.md"))).toBe(true);
		expect(await snapshotTree(path.join(targetSkillsRoot, "repositories", "repo-skills", beta.id))).toBe(betaBefore);
	});

	it("adds Codex policy without requiring per-repository content digests", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-codex-"));
		cleanup.push(root);
		const source = await createSource(root, [alpha]);
		const targetAgentRoot = path.join(root, ".agents");
		const sourceRecord = (await readJsonLines(path.join(source, "repo-skills", "repository-index.jsonl")))[0];

		const result = runExport([
			"--source-library-root",
			source,
			"--target-agent-dir",
			targetAgentRoot,
			"--target-agent",
			"codex",
		]);
		expect(result.status, result.stderr).toBe(0);
		const collection = path.join(targetAgentRoot, "skills", "repositories");
		expect(existsSync(path.join(collection, "repo-skills", alpha.id, "agents", "openai.yaml"))).toBe(true);
		expect(existsSync(path.join(collection, "repo-skills", alpha.id, "sub-skills", "setup", "agents", "openai.yaml"))).toBe(true);
		expect(existsSync(path.join(collection, "repo-skills-router", "agents", "openai.yaml"))).toBe(false);
		const targetRecord = (await readJsonLines(path.join(collection, "repo-skills", "repository-index.jsonl")))[0];
		expect(sourceRecord).not.toHaveProperty("content_sha256");
		expect(targetRecord).not.toHaveProperty("content_sha256");
		expect(existsSync(path.join(source, "repo-skills", alpha.id, "agents", "openai.yaml"))).toBe(false);
	});

	it("rejects source and target collection overlap before mutation", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-overlap-"));
		cleanup.push(root);
		const source = await createSource(root);
		const sourceSkillsRoot = path.dirname(source);
		const before = await snapshotTree(source);

		const result = runExport(exportArgs(source, sourceSkillsRoot));
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("overlap");
		expect(await snapshotTree(source)).toBe(before);
	});

	it("rolls back a post-mutation failure and resumes from the persisted transaction", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-resume-"));
		cleanup.push(root);
		const source = await createSource(root);
		const targetSkillsRoot = path.join(root, "target", "skills");
		expect(runExport(exportArgs(source, targetSkillsRoot)).status).toBe(0);
		const targetCollection = path.join(targetSkillsRoot, "repositories");
		const before = await snapshotTree(targetCollection);
		await writeFile(path.join(source, "repo-skills", alpha.id, "references", "resume-update.md"), "resume update\n", "utf8");
		expect(runUpdater(source).status).toBe(0);

		const failed = runExport(
			exportArgs(source, targetSkillsRoot, ["--include-skill", alpha.id, "--overwrite-skill", alpha.id]),
			{ DISCO_EXPORT_TEST_FAIL_AFTER: "repo_installed" },
		);
		expect(failed.status).toBe(2);
		expect(await snapshotTree(targetCollection)).toBe(before);
		const transactions = await transactionDirectories(targetSkillsRoot);
		expect(transactions).toHaveLength(1);
		const manifest = JSON.parse(await readFile(path.join(transactions[0], "manifest.json"), "utf8"));
		expect(manifest.phase).toBe("rolled_back");

		const resumed = runExport(["--resume", transactions[0]]);
		expect(resumed.status, resumed.stderr).toBe(0);
		expect(existsSync(path.join(targetCollection, "repo-skills", alpha.id, "references", "resume-update.md"))).toBe(true);
		expect(await transactionDirectories(targetSkillsRoot)).toEqual([]);
	});

	it("keeps a validated pre-mutation transaction retryable without repeating original options", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-precommit-resume-"));
		cleanup.push(root);
		const source = await createSource(root);
		const targetSkillsRoot = path.join(root, "target", "skills");

		const failed = runExport(
			exportArgs(source, targetSkillsRoot, ["--include-skill", beta.id, "--target-agent", "codex"]),
			{ DISCO_EXPORT_TEST_FAIL_AFTER: "validated" },
		);
		expect(failed.status).toBe(2);
		expect(existsSync(path.join(targetSkillsRoot, "repositories"))).toBe(false);
		const transactions = await transactionDirectories(targetSkillsRoot);
		expect(transactions).toHaveLength(1);

		const resumed = runExport(["--resume", transactions[0]]);
		expect(resumed.status, resumed.stderr).toBe(0);
		const collection = path.join(targetSkillsRoot, "repositories");
		expect(existsSync(path.join(collection, "repo-skills", beta.id, "agents", "openai.yaml"))).toBe(true);
		expect(existsSync(path.join(collection, "repo-skills", alpha.id))).toBe(false);
	});

	it("rejects an explicitly repeated resume option that conflicts with the manifest", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-resume-conflict-"));
		cleanup.push(root);
		const source = await createSource(root);
		const targetSkillsRoot = path.join(root, "target", "skills");
		const failed = runExport(
			exportArgs(source, targetSkillsRoot, ["--include-skill", beta.id, "--target-agent", "codex"]),
			{ DISCO_EXPORT_TEST_FAIL_AFTER: "validated" },
		);
		expect(failed.status).toBe(2);
		const [transaction] = await transactionDirectories(targetSkillsRoot);

		const resumed = runExport(["--resume", transaction, "--target-agent", "agent-neutral"]);
		expect(resumed.status).toBe(2);
		expect(resumed.stderr).toContain("does not match the persisted transaction");
		expect(existsSync(transaction)).toBe(true);
	});

	it("rejects symbolic links in source content and symlinked target roots", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-symlink-"));
		cleanup.push(root);
		const source = await createSource(root);
		await symlink("SKILL.md", path.join(source, "repo-skills", alpha.id, "linked-skill.md"));
		const targetSkillsRoot = path.join(root, "target", "skills");
		const sourceFailure = runExport(exportArgs(source, targetSkillsRoot));
		expect(sourceFailure.status).toBe(2);
		expect(sourceFailure.stderr).toContain("symbolic link");

		await rm(path.join(source, "repo-skills", alpha.id, "linked-skill.md"));
		const realTarget = path.join(root, "real-target");
		await mkdir(realTarget, { recursive: true });
		const linkedTarget = path.join(root, "linked-target");
		await symlink(realTarget, linkedTarget, "dir");
		const targetFailure = runExport(exportArgs(source, path.join(linkedTarget, "skills")));
		expect(targetFailure.status).toBe(2);
		expect(targetFailure.stderr).toContain("traverses a symbolic link");
	});

	it("supports the generic target selector with an explicit agent-root kind", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-generic-target-"));
		cleanup.push(root);
		const source = await createSource(root, [alpha]);
		const targetAgentRoot = path.join(root, "custom-agent");

		const result = runExport([
			"--source-library-root",
			source,
			"--target",
			targetAgentRoot,
			"--target-kind",
			"agent-root",
		]);
		expect(result.status, result.stderr).toBe(0);
		expect(existsSync(path.join(targetAgentRoot, "skills", "repositories", "repo-skills", alpha.id))).toBe(true);
	});

	it("refuses a validated resume when the selected source changed", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-source-drift-"));
		cleanup.push(root);
		const source = await createSource(root, [alpha]);
		const targetSkillsRoot = path.join(root, "target", "skills");
		const failed = runExport(
			exportArgs(source, targetSkillsRoot),
			{ DISCO_EXPORT_TEST_FAIL_AFTER: "validated" },
		);
		expect(failed.status).toBe(2);
		const [transaction] = await transactionDirectories(targetSkillsRoot);
		await writeFile(path.join(source, "repo-skills", alpha.id, "references", "drift.md"), "changed\n", "utf8");
		expect(runUpdater(source).status).toBe(0);

		const resumed = runExport(["--resume", transaction]);
		expect(resumed.status).toBe(2);
		expect(resumed.stderr).toContain("source selection changed after staging");
		expect(existsSync(path.join(targetSkillsRoot, "repositories"))).toBe(false);
	});

	it("refuses a validated resume when the target changed", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-target-drift-"));
		cleanup.push(root);
		const source = await createSource(root, [alpha]);
		const targetSkillsRoot = path.join(root, "target", "skills");
		const failed = runExport(
			exportArgs(source, targetSkillsRoot),
			{ DISCO_EXPORT_TEST_FAIL_AFTER: "validated" },
		);
		expect(failed.status).toBe(2);
		const [transaction] = await transactionDirectories(targetSkillsRoot);
		await mkdir(path.join(targetSkillsRoot, "repositories"), { recursive: true });
		await writeFile(path.join(targetSkillsRoot, "repositories", "external-marker.txt"), "external change\n", "utf8");

		const resumed = runExport(["--resume", transaction]);
		expect(resumed.status).toBe(2);
		expect(resumed.stderr).toContain("target changed after staging");
		expect(existsSync(path.join(targetSkillsRoot, "repositories", "repo-skills"))).toBe(false);
	});

	it("rejects a transaction manifest whose target collection escapes its skills root", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-export-invalid-manifest-"));
		cleanup.push(root);
		const source = await createSource(root, [alpha]);
		const targetSkillsRoot = path.join(root, "target", "skills");
		const failed = runExport(
			exportArgs(source, targetSkillsRoot),
			{ DISCO_EXPORT_TEST_FAIL_AFTER: "validated" },
		);
		expect(failed.status).toBe(2);
		const [transaction] = await transactionDirectories(targetSkillsRoot);
		const manifestPath = path.join(transaction, "manifest.json");
		const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
		manifest.target_library_root = path.join(root, "escaped-target");
		await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");

		const resumed = runExport(["--resume", transaction]);
		expect(resumed.status).toBe(2);
		expect(resumed.stderr).toContain("target collection does not match its target skills root");
		expect(existsSync(path.join(root, "escaped-target"))).toBe(false);
	});

	it.each([
		"before_repo_backup_rename",
		"after_repo_backup_rename",
		"before_repo_install_rename",
		"after_repo_install_rename",
		"before_router_backup_rename",
		"after_router_backup_rename",
		"before_router_install_rename",
		"after_router_install_rename",
	])("restores and retries an interruption at %s", async (failurePoint) => {
		const root = await mkdtemp(path.join(tmpdir(), `disco-repo-export-boundary-${failurePoint}-`));
		cleanup.push(root);
		const source = await createSource(root);
		const targetSkillsRoot = path.join(root, "target", "skills");
		expect(runExport(exportArgs(source, targetSkillsRoot)).status).toBe(0);
		const targetCollection = path.join(targetSkillsRoot, "repositories");
		const before = await snapshotTree(targetCollection);
		await writeFile(path.join(source, "repo-skills", alpha.id, "references", `${failurePoint}.md`), `${failurePoint}\n`, "utf8");
		expect(runUpdater(source).status).toBe(0);

		const failed = runExport(
			exportArgs(source, targetSkillsRoot, ["--include-skill", alpha.id, "--overwrite-skill", alpha.id]),
			{ DISCO_EXPORT_TEST_FAIL_AT: failurePoint },
		);
		expect(failed.status).toBe(2);
		expect(await snapshotTree(targetCollection)).toBe(before);
		const transactions = await transactionDirectories(targetSkillsRoot);
		expect(transactions).toHaveLength(1);
		const manifest = JSON.parse(await readFile(path.join(transactions[0], "manifest.json"), "utf8"));
		expect(manifest.phase).toBe("rolled_back");

		const resumed = runExport(["--resume", transactions[0]]);
		expect(resumed.status, resumed.stderr).toBe(0);
		expect(existsSync(path.join(targetCollection, "repo-skills", alpha.id, "references", `${failurePoint}.md`))).toBe(true);
	});
});
