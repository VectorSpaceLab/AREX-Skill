import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";

const scriptPath = path.join(
	process.cwd(),
	"packages/coding-agent/src/disco/skills/verify-repo-skill/scripts/build_repo_skills_collection.mjs",
);
const taxonomyPath = path.join(
	process.cwd(),
	"packages/coding-agent/src/disco/skills/repo-skills-router/references/index/taxonomy.json",
);
const cleanup: string[] = [];

async function writeSkill(
	checkout: string,
	relativeRoot: string,
	sourceName: string,
	routing: { repoId: string; skillId: string; assignments: Array<{ area: string; family: string }> },
	withLegacyMetadata = false,
): Promise<void> {
	const root = path.join(checkout, relativeRoot);
	await mkdir(path.join(root, "sub-skills", "setup"), { recursive: true });
	await writeFile(
		path.join(root, "SKILL.md"),
		[
			"---",
			`name: ${sourceName}`,
			"description: Source repository skill used by the collection builder",
			"---",
			"",
			"# Source skill",
			"",
			"[Setup](sub-skills/setup/SKILL.md)",
		].join("\n"),
		"utf8",
	);
	await writeFile(
		path.join(root, "sub-skills", "setup", "SKILL.md"),
		[
			"---",
			"name: setup",
			'description: "Setup guidance."',
			"---",
			"",
			"# Setup",
		].join("\n"),
		"utf8",
	);
	if (withLegacyMetadata) {
		await mkdir(path.join(root, "references"), { recursive: true });
		await writeFile(path.join(root, "references", "repo-routing-metadata.json"), JSON.stringify({ skills: { [sourceName]: { scenarios: [] } } }), "utf8");
	} else {
		await mkdir(path.join(root, "references"), { recursive: true });
		await writeFile(
			path.join(root, "references", "repo-routing-metadata.json"),
			`${JSON.stringify({
				schema_version: "2.0",
				repo_id: routing.repoId,
				skill_id: routing.skillId,
				taxonomy_sha256: "f8c306386015711634ddbb43a5eb95d1f58909c3513ce2063ba42efdd583a431",
				routing_status: "classified",
				assignments: routing.assignments,
			}, null, 2)}\n`,
			"utf8",
		);
	}
}

async function writeInputs(root: string, withLegacyMetadata = false): Promise<{ output: string; args: string[] }> {
	const checkout = path.join(root, "checkout");
	const alphaAssignments = [
		{ area: "Computer Vision", family: "Image Classification" },
		{ area: "Natural Language Processing", family: "Text Generation" },
	];
	const betaAssignments = [{ area: "Computer Vision", family: "Image Classification" }];
	await writeSkill(checkout, "skills/disco/alpha-source", "alpha-source", { repoId: "owner/alpha", skillId: "alpha-repo", assignments: alphaAssignments }, withLegacyMetadata);
	await writeSkill(checkout, "skills/disco/beta-source", "beta-source", { repoId: "owner/beta", skillId: "beta-repo", assignments: betaAssignments });
	const repositoryManifest = path.join(root, "repository-manifest.jsonl");
	const sourceManifest = path.join(root, "source-manifest.jsonl");
	const assignments = path.join(root, "assignments.jsonl");
	await writeFile(
		repositoryManifest,
		[
			JSON.stringify({ repo_id: "owner/alpha", repo_name: "alpha", status: "classified" }),
			JSON.stringify({ repo_id: "owner/beta", repo_name: "beta", status: "classified" }),
		].join("\n") + "\n",
		"utf8",
	);
	await writeFile(
		sourceManifest,
		[
			JSON.stringify({ repo_id: "owner/alpha", legacy_repo_id: "batch_0/alpha", repo_name: "alpha", skill_id: "alpha-repo", source_url: "https://github.com/owner/alpha", source_commit: "a".repeat(40), source_checkout: checkout, source_skill_root: "skills/disco/alpha-source", aliases: ["alpha"] }),
			JSON.stringify({ repo_id: "owner/beta", legacy_repo_id: "batch_1/beta", repo_name: "beta", skill_id: "beta-repo", source_url: "https://github.com/owner/beta", source_commit: "b".repeat(40), source_checkout: checkout, source_skill_root: "skills/disco/beta-source" }),
		].join("\n") + "\n",
		"utf8",
	);
	await writeFile(
		assignments,
		[
			JSON.stringify({ repo_id: "owner/alpha", ...alphaAssignments[0], confidence: "high" }),
			JSON.stringify({ repo_id: "owner/alpha", ...alphaAssignments[1], confidence: "medium" }),
			JSON.stringify({ repo_id: "owner/beta", ...betaAssignments[0], confidence: "high" }),
		].join("\n") + "\n",
		"utf8",
	);
	const output = path.join(root, "staged-library");
	return {
		output,
		args: [
			"--source-manifest", sourceManifest,
			"--repository-manifest", repositoryManifest,
			"--assignments", assignments,
			"--taxonomy", taxonomyPath,
			"--output-dir", output,
			"--template-dir", path.join(process.cwd(), "packages/coding-agent/src/disco/skills/repo-skills-router"),
			"--expected-repositories", "2",
			"--expected-assignments", "3",
			"--source-router-run-id", "test-router-run",
		],
	};
}

describe("build_repo_skills_collection.mjs", () => {
	afterEach(async () => {
		for (const root of cleanup.splice(0)) await rm(root, { recursive: true, force: true });
	});

	it("builds and validates a complete staged collection in one router pass", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-collection-builder-"));
		cleanup.push(root);
		const fixture = await writeInputs(root);
		const result = spawnSync(process.execPath, [scriptPath, ...fixture.args], { encoding: "utf8" });
		expect(result.status, result.stderr).toBe(0);
		expect(result.stdout).toContain("2 repositories, 3 assignments");
		expect(existsSync(path.join(fixture.output, "repo-skills", "alpha-repo", "SKILL.md"))).toBe(true);
		expect(await readFile(path.join(fixture.output, "repo-skills", "alpha-repo", "SKILL.md"), "utf8")).toContain("name: alpha-repo");
		expect(await readFile(path.join(fixture.output, "repo-skills", "alpha-repo", "SKILL.md"), "utf8")).toContain("disable-model-invocation: true");
		const metadata = JSON.parse(await readFile(path.join(fixture.output, "repo-skills", "alpha-repo", "references", "repo-routing-metadata.json"), "utf8"));
		expect(metadata).toMatchObject({ schema_version: "2.0", repo_id: "owner/alpha", skill_id: "alpha-repo", routing_status: "classified" });
		expect(metadata.assignments).toHaveLength(2);
		const buildMetadata = JSON.parse(await readFile(path.join(fixture.output, "repo-skills-router", "references", "index", "build-metadata.json"), "utf8"));
		expect(buildMetadata).toMatchObject({ repository_count: 2, assignment_count: 3, source_router_run_id: "test-router-run" });
		const repositoryIndex = await readFile(path.join(fixture.output, "repo-skills", "repository-index.jsonl"), "utf8");
		expect(repositoryIndex).toContain('"legacy_repo_id":"batch_0/alpha"');
		const assignmentIndex = await readFile(path.join(fixture.output, "repo-skills-router", "references", "index", "assignments.jsonl"), "utf8");
		expect(assignmentIndex).toContain('"legacy_repo_id":"batch_0/alpha"');
		expect(assignmentIndex).toContain('"confidence":"medium"');
		expect(await readFile(path.join(fixture.output, "repo-skills-router", "references", "families", "computer-vision", "image-classification.md"), "utf8")).toContain("repo-skills/alpha-repo/SKILL.md");
	});

	it("validates all inputs before publishing and leaves no partial output", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-collection-builder-"));
		cleanup.push(root);
		const fixture = await writeInputs(root);
		const result = spawnSync(process.execPath, [scriptPath, ...fixture.args.map((value, index) => (value === "3" && fixture.args[index - 1] === "--expected-assignments" ? "4" : value))], { encoding: "utf8" });
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("assignment ledger has 3 records; expected 4");
		expect(existsSync(fixture.output)).toBe(false);
	});

	it("rejects a legacy scenario metadata file instead of silently migrating it", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-collection-builder-"));
		cleanup.push(root);
		const fixture = await writeInputs(root, true);
		const result = spawnSync(process.execPath, [scriptPath, ...fixture.args], { encoding: "utf8" });
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("contains unknown field skills");
		expect(existsSync(fixture.output)).toBe(false);
	});

	it("rejects a source checkout path leaked into the runtime skill", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-collection-builder-"));
		cleanup.push(root);
		const fixture = await writeInputs(root);
		const leakedFile = path.join(root, "checkout", "skills", "disco", "alpha-source", "references", "leaked-path.md");
		await writeFile(leakedFile, `Generation checkout: ${path.join(root, "checkout")}\n`, "utf8");

		const result = spawnSync(process.execPath, [scriptPath, ...fixture.args], { encoding: "utf8" });
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("leaks the production source_checkout path");
		expect(existsSync(fixture.output)).toBe(false);
	});

	it("rejects a private DisCo inspection environment path", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-collection-builder-"));
		cleanup.push(root);
		const fixture = await writeInputs(root);
		const leakedFile = path.join(root, "checkout", "skills", "disco", "alpha-source", "references", "leaked-env.md");
		await writeFile(leakedFile, `Inspection prefix: ${path.join(process.env.HOME ?? "", ".disco", "agent", "envs", "alpha")}\n`, "utf8");

		const result = spawnSync(process.execPath, [scriptPath, ...fixture.args], { encoding: "utf8" });
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("leaks the production private DisCo environment path");
		expect(existsSync(fixture.output)).toBe(false);
	});

	it("rejects generated Python cache files in a runtime skill", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-collection-builder-"));
		cleanup.push(root);
		const fixture = await writeInputs(root);
		const cacheDir = path.join(root, "checkout", "skills", "disco", "alpha-source", "scripts", "__pycache__");
		await mkdir(cacheDir, { recursive: true });
		await writeFile(path.join(cacheDir, "helper.cpython-313.pyc"), "generated cache", "utf8");

		const result = spawnSync(process.execPath, [scriptPath, ...fixture.args], { encoding: "utf8" });
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("contains generated Python cache directory");
		expect(existsSync(fixture.output)).toBe(false);
	});

	it("does not treat links-shaped syntax inside fenced code as Markdown links", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-collection-builder-"));
		cleanup.push(root);
		const fixture = await writeInputs(root);
		const alphaSkill = path.join(fixture.output, "..", "checkout", "skills", "disco", "alpha-source", "references");
		await mkdir(alphaSkill, { recursive: true });
		await writeFile(path.join(alphaSkill, "code-example.md"), "Inline `mapping[\"key\"](argument[0])`\n\n```python\nvalue = mapping[\"key\"](argument[0])\n```\n", "utf8");
		const result = spawnSync(process.execPath, [scriptPath, ...fixture.args], { encoding: "utf8" });
		expect(result.status, result.stderr).toBe(0);
	});

	it("does not treat links-shaped syntax inside multiline inline code as Markdown links", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-collection-builder-"));
		cleanup.push(root);
		const fixture = await writeInputs(root);
		const alphaReferences = path.join(fixture.output, "..", "checkout", "skills", "disco", "alpha-source", "references");
		await mkdir(alphaReferences, { recursive: true });
		await writeFile(
			path.join(alphaReferences, "multiline-inline-code.md"),
			"The tensor stores `[J*4 quaternion values, root xyz,\nroot-facing pivot, 4 contact flags]` as `(T, channels)`.\n",
			"utf8",
		);
		const result = spawnSync(process.execPath, [scriptPath, ...fixture.args], { encoding: "utf8" });
		expect(result.status, result.stderr).toBe(0);
	});
});
