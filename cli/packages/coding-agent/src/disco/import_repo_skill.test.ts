import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";

const scriptPath = path.join(
	process.cwd(),
	"packages/coding-agent/src/disco/skills/verify-repo-skill/scripts/import_repo_skill.mjs",
);
const cleanup: string[] = [];

async function digestTree(root: string): Promise<string> {
	const files: string[] = [];
	async function visit(directory: string): Promise<void> {
		for (const entry of (await readdir(directory, { withFileTypes: true })).sort((left, right) => left.name.localeCompare(right.name))) {
			const entryPath = path.join(directory, entry.name);
			if (entry.isDirectory()) await visit(entryPath);
			else files.push(entryPath);
		}
	}
	await visit(root);
	const hash = createHash("sha256");
	for (const filePath of files.sort((left, right) => left.localeCompare(right))) {
		const relativePath = path.relative(root, filePath).split(path.sep).join("/");
		const content = await readFile(filePath);
		hash.update(`file\0${relativePath}\0${content.byteLength}\0`);
		hash.update(content);
		hash.update("\0");
	}
	return `sha256:${hash.digest("hex")}`;
}
const taxonomyHash = "f8c306386015711634ddbb43a5eb95d1f58909c3513ce2063ba42efdd583a431";

async function writeCandidate(root: string, id = "alpha-repo", extraReference?: string): Promise<{ skill: string; handoff: string }> {
	const skill = path.join(root, id);
	await mkdir(root, { recursive: true });
	await writeFile(path.join(root, "README.md"), "# Source repository checkout\n\nThis fixture provides repository evidence for the import handoff.\n", "utf8");
	await mkdir(path.join(skill, "references"), { recursive: true });
	await mkdir(path.join(skill, "sub-skills", "setup"), { recursive: true });
	await writeFile(
		path.join(skill, "SKILL.md"),
		[
			"---",
			`name: ${id}`,
			`description: "Use ${id} for repository import tests."`,
			"disable-model-invocation: true",
			"metadata:",
			"  disco-role: operating",
			"---",
			"",
			`# ${id}`,
		].join("\n"),
		"utf8",
	);
	await writeFile(
		path.join(skill, "sub-skills", "setup", "SKILL.md"),
		[
			"---",
			"name: setup",
			'description: "Set up the repository import test workflow."',
			"disable-model-invocation: true",
			"metadata:",
			"  disco-role: operating",
			"---",
			"",
			"# Setup",
		].join("\n"),
		"utf8",
	);
	await writeFile(
		path.join(skill, "references", "repo-routing-metadata.json"),
		`${JSON.stringify({ schema_version: "2.0", repo_id: "owner/alpha-repo", skill_id: id, taxonomy_sha256: taxonomyHash, routing_status: "classified", assignments: [{ area: "Computer Vision", family: "Image Classification" }] }, null, 2)}\n`,
		"utf8",
	);
	if (extraReference !== undefined) {
		await writeFile(path.join(skill, "references", "markdown-code-syntax.md"), extraReference, "utf8");
	}
	const handoff = path.join(root, `${id}-classification.json`);
	const skillContentSha256 = await digestTree(skill);
	await writeFile(
		handoff,
		`${JSON.stringify({ schema_version: 1, repo_id: "owner/alpha-repo", legacy_repo_id: "batch_0/alpha-repo", repo_name: "alpha-repo", source_url: "https://github.com/owner/alpha-repo", source_commit: "a".repeat(40), source_checkout: root, source_skill_root: id, skill_id: id, skill_root: `repo-skills/${id}`, skill_content_sha256: skillContentSha256, taxonomy_sha256: taxonomyHash, status: "classified", assignments: [{ area: "Computer Vision", family: "Image Classification", confidence: "high", rationale: "The repository provides image classification workflows.", evidence: [{ path: "README.md", line_start: 1, line_end: 3, description: "Repository documentation identifies the capability." }] }] }, null, 2)}\n`,
		"utf8",
	);
	return { skill, handoff };
}

function runImporter(agentDir: string, candidate: { skill: string; handoff: string }, extra: string[] = [], env: Record<string, string> = {}) {
	return spawnSync(process.execPath, [scriptPath, "--agent-dir", agentDir, "--routing-entry", candidate.handoff, ...extra, candidate.skill], {
		encoding: "utf8",
		env: { ...process.env, NODE_ENV: "test", ...env },
	});
}

describe("import_repo_skill.mjs", () => {
	afterEach(async () => {
		for (const root of cleanup.splice(0)) await rm(root, { recursive: true, force: true });
	});

	it("imports a v2 repo skill into skills/repositories and rebuilds the area/family router", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-import-"));
		cleanup.push(root);
		const candidate = await writeCandidate(path.join(root, "draft"));
		const agentDir = path.join(root, "agent");
		const result = runImporter(agentDir, candidate);
		expect(result.status, result.stderr).toBe(0);
		expect(result.stdout).toContain("imported and routed repo skill alpha-repo");
		const liveRoot = path.join(agentDir, "skills", "repositories");
		expect(existsSync(path.join(liveRoot, "repo-skills", "alpha-repo", "SKILL.md"))).toBe(true);
		expect(await readFile(path.join(liveRoot, "repo-skills-router", "references", "families", "computer-vision", "image-classification.md"), "utf8")).toContain("../../../../repo-skills/alpha-repo/SKILL.md");
		expect(await readFile(path.join(liveRoot, "repo-skills", "repository-index.jsonl"), "utf8")).toContain("owner/alpha-repo");
		expect(await readFile(path.join(liveRoot, "repo-skills", "repository-index.jsonl"), "utf8")).toContain('"legacy_repo_id":"batch_0/alpha-repo"');
		expect(await readFile(path.join(liveRoot, "repo-skills-router", "references", "index", "assignments.jsonl"), "utf8")).toContain('"confidence":"high"');
	});

	it("rejects the old scenario-shaped routing metadata before mutating the live tree", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-import-"));
		cleanup.push(root);
		const candidate = await writeCandidate(path.join(root, "draft"), "legacy-repo");
		await writeFile(path.join(candidate.skill, "references", "repo-routing-metadata.json"), JSON.stringify({ skills: { "legacy-repo": { scenarios: [] } } }), "utf8");
		const result = runImporter(path.join(root, "agent"), candidate);
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("unknown field skills");
		expect(existsSync(path.join(root, "agent", "skills"))).toBe(false);
	});

	it("requires an external routing handoff for a normal managed import", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-import-"));
		cleanup.push(root);
		const candidate = await writeCandidate(path.join(root, "draft"));
		const result = spawnSync(process.execPath, [scriptPath, "--agent-dir", path.join(root, "agent"), candidate.skill], {
			encoding: "utf8",
			env: { ...process.env, NODE_ENV: "test" },
		});
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("normal managed imports require --routing-entry");
		expect(existsSync(path.join(root, "agent", "skills"))).toBe(false);
	});

	it("rejects a classified routing handoff without an inspectable source checkout", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-import-"));
		cleanup.push(root);
		const candidate = await writeCandidate(path.join(root, "draft"));
		const handoff = JSON.parse(await readFile(candidate.handoff, "utf8"));
		delete handoff.source_checkout;
		await writeFile(candidate.handoff, `${JSON.stringify(handoff, null, 2)}\n`, "utf8");

		const result = runImporter(path.join(root, "agent"), candidate);
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("routing handoff source_checkout must be an existing absolute directory");
		expect(existsSync(path.join(root, "agent", "skills"))).toBe(false);
	});

	it("rejects evidence line ranges outside the source file", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-import-"));
		cleanup.push(root);
		const candidate = await writeCandidate(path.join(root, "draft"));
		const handoff = JSON.parse(await readFile(candidate.handoff, "utf8"));
		handoff.assignments[0].evidence[0].line_end = 999;
		await writeFile(candidate.handoff, `${JSON.stringify(handoff, null, 2)}\n`, "utf8");

		const result = runImporter(path.join(root, "agent"), candidate);
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("line range exceeds README.md");
		expect(existsSync(path.join(root, "agent", "skills"))).toBe(false);
	});

	it("restores the skill, repository index, and router after a post-update failure", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-import-"));
		cleanup.push(root);
		const candidate = await writeCandidate(path.join(root, "draft"));
		const agentDir = path.join(root, "agent");
		const result = runImporter(agentDir, candidate, [], { DISCO_TEST_FAIL_REPO_IMPORT_AT: "after-router-update" });
		expect(result.status).toBe(2);
		expect(existsSync(path.join(agentDir, "skills", "repositories", "repo-skills", "alpha-repo"))).toBe(false);
		expect(existsSync(path.join(agentDir, "skills", "repositories", "repo-skills", "repository-index.jsonl"))).toBe(false);
		expect(existsSync(path.join(agentDir, "skills", "repositories", "repo-skills-router"))).toBe(false);
	});

	it("does not treat links-shaped syntax inside fenced code as Markdown links", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-import-"));
		cleanup.push(root);
		const candidate = await writeCandidate(
			path.join(root, "draft"),
			"fenced-code-repo",
			"```python\nvalue = mapping[\"key\"](argument[0])\n```\n",
		);
		const result = runImporter(path.join(root, "agent"), candidate);
		expect(result.status, result.stderr).toBe(0);
	});

	it("does not treat links-shaped syntax inside multiline inline code as Markdown links", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "disco-repo-import-"));
		cleanup.push(root);
		const candidate = await writeCandidate(
			path.join(root, "draft"),
			"multiline-code-repo",
			"The tensor stores `[J*4 quaternion values, root xyz,\nroot-facing pivot, 4 contact flags]` as `(T, channels)`.\n",
		);
		const result = runImporter(path.join(root, "agent"), candidate);
		expect(result.status, result.stderr).toBe(0);
	});
});
