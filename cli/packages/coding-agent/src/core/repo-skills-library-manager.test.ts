import { execFileSync } from "node:child_process";
import { cpSync, existsSync, readFileSync } from "node:fs";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import {
	RepoSkillsLibraryConflictError,
	RepoSkillsLibraryManager,
	type RepoSkillsLibraryManagerOptions,
	type RepoSkillsTransactionPoint,
} from "./repo-skills-library-manager.ts";

const roots: string[] = [];
const bundledSkillsDir = path.join(process.cwd(), "packages", "coding-agent", "src", "disco", "skills");
const updaterScript = path.join(bundledSkillsDir, "verify-repo-skill", "scripts", "update_repo_skills_router.mjs");
const taxonomyHash = "f8c306386015711634ddbb43a5eb95d1f58909c3513ce2063ba42efdd583a431";

function git(repository: string, ...args: string[]): string {
	return execFileSync("git", ["-C", repository, ...args], { encoding: "utf8" }).trim();
}

async function makeRoot(): Promise<string> {
	const root = await mkdtemp(path.join(tmpdir(), "disco-repo-skills-manager-"));
	roots.push(root);
	return root;
}

async function writeSkill(libraryRoot: string, id: string, marker: string): Promise<void> {
	const skillDir = path.join(libraryRoot, "repo-skills", id);
	await mkdir(path.join(skillDir, "references"), { recursive: true });
	await writeFile(path.join(skillDir, "SKILL.md"), [
		"---",
		`name: ${id}`,
		`description: "Use ${id} for focused repository workflows."`,
		"disable-model-invocation: true",
		"metadata:",
		"  disco-role: operating",
		"---",
		"",
		`# ${id}`,
		"",
		marker,
	].join("\n"), "utf8");
	await writeFile(path.join(skillDir, "references", "repo-routing-metadata.json"), `${JSON.stringify({
		schema_version: "2.0",
		repo_id: "owner/alpha",
		skill_id: id,
		taxonomy_sha256: taxonomyHash,
		routing_status: "classified",
		assignments: [{ area: "Computer Vision", family: "Image Classification" }],
	}, null, 2)}\n`, "utf8");
}

async function createSourceRepository(root: string, marker = "source-v1"): Promise<string> {
	const repository = path.join(root, "source");
	const libraryRoot = path.join(repository, "skills", "repositories");
	await mkdir(repository, { recursive: true });
	execFileSync("git", ["init", "--initial-branch=main", repository]);
	git(repository, "config", "user.email", "test@example.com");
	git(repository, "config", "user.name", "DisCo Test");
	await writeSkill(libraryRoot, "alpha", marker);
	cpSync(path.join(bundledSkillsDir, "repo-skills-router"), path.join(libraryRoot, "repo-skills-router"), { recursive: true });
	await writeFile(path.join(libraryRoot, "repo-skills", "repository-index.jsonl"), `${JSON.stringify({
		schema_version: 1,
		repo_id: "owner/alpha",
		legacy_repo_id: "batch_0/alpha",
		repo_name: "alpha",
		skill_id: "alpha",
		source_url: "https://github.com/owner/alpha",
		source_commit: null,
		source_skill_root: "repo-skills/alpha",
		target_skill_root: "repo-skills/alpha",
		aliases: [],
		content_sha256: null,
		description: "Use alpha for focused repository workflows.",
	})}\n`, "utf8");
	await writeFile(path.join(libraryRoot, "repo-skills-router", "references", "index", "assignments.jsonl"), `${JSON.stringify({
		repo_id: "owner/alpha",
		legacy_repo_id: "batch_0/alpha",
		skill_id: "alpha",
		area: "Computer Vision",
		family: "Image Classification",
		confidence: "high",
	})}\n`, "utf8");
	execFileSync(process.execPath, [updaterScript, "--library-root", libraryRoot, "--template-dir", path.join(bundledSkillsDir, "repo-skills-router"), "--router-visibility", "enabled"]);
	git(repository, "add", "skills");
	git(repository, "commit", "-m", "source v1");
	return repository;
}

function manager(agentDir: string, sourceRepository: string, overrides: Omit<RepoSkillsLibraryManagerOptions, "agentDir" | "sourceRepository"> = {}) {
	return new RepoSkillsLibraryManager({
		...overrides,
		agentDir,
		sourceRepository,
		bundledSkillsDir,
		env: { ...(overrides.env ?? process.env), DISCO_OFFLINE: "" },
	});
}

afterEach(async () => {
	for (const root of roots.splice(0)) await rm(root, { recursive: true, force: true });
});

describe("RepoSkillsLibraryManager", () => {
	it("installs the repositories collection and reports router counts", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root);
		const agentDir = path.join(root, "agent");
		const result = await manager(agentDir, source).install();
		expect(result.noop).toBe(false);
		expect(result.managedSkills).toBe(1);
		expect(result.repositoryCount).toBe(1);
		expect(result.assignmentCount).toBe(1);
		expect(result.areaCount).toBe(20);
		expect(result.familyCount).toBe(178);
		expect(existsSync(path.join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md"))).toBe(true);
		expect(existsSync(path.join(agentDir, "skills", "repositories", "repo-skills-router", "references", "index", "assignments.jsonl"))).toBe(true);
		const status = manager(agentDir, source).status();
		expect(status.issues).toEqual([]);
		expect(status.repositoryCount).toBe(1);
		expect(status.assignmentCount).toBe(1);
	});

	it("preserves local repository skills while updating official collection data", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root, "source-v1");
		const agentDir = path.join(root, "agent");
		await manager(agentDir, source).install();
		const localDir = path.join(agentDir, "skills", "repositories", "repo-skills", "local-helper");
		await mkdir(localDir, { recursive: true });
		await writeFile(path.join(localDir, "SKILL.md"), [
			"---", "name: local-helper", 'description: "Local helper."',
			"disable-model-invocation: true", "metadata:", "  disco-role: operating", "---", "", "# Local",
		].join("\n"), "utf8");
		const updated = await manager(agentDir, source).update();
		expect(updated.localSkills).toBe(1);
		expect(existsSync(path.join(localDir, "SKILL.md"))).toBe(true);
	});

	it("preserves routed local repository skills and their central index rows during an official update", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root, "source-v1");
		const agentDir = path.join(root, "agent");
		await manager(agentDir, source).install();
		const liveRoot = path.join(agentDir, "skills", "repositories");
		const localDir = path.join(liveRoot, "repo-skills", "local-routed");
		await mkdir(path.join(localDir, "references"), { recursive: true });
		await writeFile(path.join(localDir, "SKILL.md"), [
			"---", "name: local-routed", 'description: "Local routed helper."',
			"disable-model-invocation: true", "metadata:", "  disco-role: operating", "---", "", "# Local routed",
		].join("\n"), "utf8");
		await writeFile(path.join(localDir, "references", "repo-routing-metadata.json"), `${JSON.stringify({
			schema_version: "2.0",
			repo_id: "local/local-routed",
			skill_id: "local-routed",
			taxonomy_sha256: taxonomyHash,
			routing_status: "classified",
			assignments: [{ area: "Computer Vision", family: "Image Classification" }],
		}, null, 2)}\n`, "utf8");
		const repositoryIndexPath = path.join(liveRoot, "repo-skills", "repository-index.jsonl");
		await writeFile(repositoryIndexPath, `${readFileSync(repositoryIndexPath, "utf8")}${JSON.stringify({
			schema_version: 1,
			repo_id: "local/local-routed",
			legacy_repo_id: null,
			repo_name: "local-routed",
			skill_id: "local-routed",
			source_url: "https://github.com/local/local-routed",
			source_commit: null,
			source_skill_root: null,
			target_skill_root: "repo-skills/local-routed",
			aliases: [],
			content_sha256: null,
			description: "Local routed helper.",
		})}\n`, "utf8");
		const assignmentIndexPath = path.join(liveRoot, "repo-skills-router", "references", "index", "assignments.jsonl");
		await writeFile(assignmentIndexPath, `${readFileSync(assignmentIndexPath, "utf8")}${JSON.stringify({
			repo_id: "local/local-routed",
			legacy_repo_id: null,
			skill_id: "local-routed",
			area: "Computer Vision",
			family: "Image Classification",
			confidence: "high",
		})}\n`, "utf8");
		execFileSync(process.execPath, [updaterScript, "--library-root", liveRoot, "--template-dir", path.join(bundledSkillsDir, "repo-skills-router"), "--router-visibility", "enabled"]);

		const updated = await manager(agentDir, source).update();
		expect(updated.localSkills).toBe(1);
		expect(existsSync(path.join(localDir, "SKILL.md"))).toBe(true);
		expect(readFileSync(repositoryIndexPath, "utf8")).toContain('"repo_id":"local/local-routed"');
		expect(readFileSync(assignmentIndexPath, "utf8")).toContain('"skill_id":"local-routed"');
		expect(manager(agentDir, source).status().issues).toEqual([]);
	});

	it("fails closed when a direct repository skill directory is not covered by the source index", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root);
		await writeSkill(path.join(source, "skills", "repositories"), "orphan", "unindexed source skill");
		git(source, "add", "skills");
		git(source, "commit", "-m", "add unindexed repository skill");

		await expect(manager(path.join(root, "agent"), source).install()).rejects.toThrow(
			"repository-index.jsonl does not cover direct repository skill directory",
		);
	});

	it("rejects a repository index whose source URL does not identify the declared repository", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root);
		const indexPath = path.join(source, "skills", "repositories", "repo-skills", "repository-index.jsonl");
		const index = JSON.parse(readFileSync(indexPath, "utf8"));
		index.source_url = "https://github.com/other/alpha";
		await writeFile(indexPath, `${JSON.stringify(index)}\n`, "utf8");
		git(source, "add", "skills");
		git(source, "commit", "-m", "mismatch repository source URL");

		await expect(manager(path.join(root, "agent"), source).install()).rejects.toThrow(
			"Invalid repository-index.jsonl identity at line 1",
		);
	});

	it("detects stale router index digests, taxonomy counts, and live skill content", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root);
		const agentDir = path.join(root, "agent");
		await manager(agentDir, source).install();
		const liveRoot = path.join(agentDir, "skills", "repositories");
		const repositoryIndexPath = path.join(liveRoot, "repo-skills-router", "references", "index", "repositories.jsonl");
		const repositoryIndex = JSON.parse(readFileSync(repositoryIndexPath, "utf8"));
		repositoryIndex.content_sha256 = `sha256:${"0".repeat(64)}`;
		await writeFile(repositoryIndexPath, `${JSON.stringify(repositoryIndex)}\n`, "utf8");
		await writeFile(path.join(liveRoot, "repo-skills", "alpha", "SKILL.md"), `${readFileSync(path.join(liveRoot, "repo-skills", "alpha", "SKILL.md"), "utf8")}\nlocally changed\n`, "utf8");
		const buildMetadataPath = path.join(liveRoot, "repo-skills-router", "references", "index", "build-metadata.json");
		const buildMetadata = JSON.parse(readFileSync(buildMetadataPath, "utf8"));
		buildMetadata.area_count = 999;
		await writeFile(buildMetadataPath, `${JSON.stringify(buildMetadata)}\n`, "utf8");

		const issues = manager(agentDir, source).status().issues;
		expect(issues).toEqual(expect.arrayContaining([
			expect.stringContaining("content_sha256 does not match live skill alpha"),
			expect.stringContaining("build metadata area_count is stale"),
			expect.stringContaining("repository index digest is stale"),
		]));
	});

	it("rejects routing metadata fields and assignments outside the v2 minimal schema", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root);
		const agentDir = path.join(root, "agent");
		await manager(agentDir, source).install();
		const metadataPath = path.join(
			agentDir,
			"skills",
			"repositories",
			"repo-skills",
			"alpha",
			"references",
			"repo-routing-metadata.json",
		);
		const validMetadata = JSON.parse(readFileSync(metadataPath, "utf8"));

		await writeFile(metadataPath, `${JSON.stringify({ ...validMetadata, confidence: "high" }, null, 2)}\n`, "utf8");
		expect(manager(agentDir, source).status().issues).toEqual(expect.arrayContaining([
			expect.stringContaining("metadata contains unknown field confidence"),
		]));

		await writeFile(metadataPath, `${JSON.stringify({
			...validMetadata,
			assignments: [{ ...validMetadata.assignments[0], rationale: "not runtime metadata" }],
		}, null, 2)}\n`, "utf8");
		expect(manager(agentDir, source).status().issues).toEqual(expect.arrayContaining([
			expect.stringContaining("metadata assignment 0 contains unknown field rationale"),
		]));

		await writeFile(metadataPath, `${JSON.stringify({
			...validMetadata,
			assignments: [validMetadata.assignments[0], validMetadata.assignments[0]],
		}, null, 2)}\n`, "utf8");
		expect(manager(agentDir, source).status().issues).toEqual(expect.arrayContaining([
			expect.stringContaining("metadata contains duplicate assignment Computer Vision -> Image Classification"),
		]));
	});

	it("rolls back all managed artifacts when the transaction fails", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root, "source-v1");
		const agentDir = path.join(root, "agent");
		const points: RepoSkillsTransactionPoint[] = [];
		const first = await manager(agentDir, source).install();
		const before = readFileSync(path.join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md"), "utf8");
		await writeSkill(path.join(source, "skills", "repositories"), "alpha", "source-v2");
		execFileSync(process.execPath, [updaterScript, "--library-root", path.join(source, "skills", "repositories"), "--template-dir", path.join(bundledSkillsDir, "repo-skills-router"), "--router-visibility", "enabled"]);
		git(source, "add", "skills");
		git(source, "commit", "-m", "source v2");
		const failing = manager(agentDir, source, { transactionFaultInjector: (point) => { points.push(point); if (point === "before-install-router") throw new Error("injected manager failure"); } });
		await expect(failing.update({ force: true })).rejects.toThrow("injected manager failure");
		expect(points).toContain("before-install-router");
		expect(readFileSync(path.join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md"), "utf8")).toBe(before);
		expect(first.managedSkills).toBe(1);
	});

	it("uses the new source layout and rejects an old managed state schema", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root);
		const agentDir = path.join(root, "agent");
		await manager(agentDir, source).install();
		const statePath = path.join(agentDir, "repo-skills-library.json");
		const state = JSON.parse(readFileSync(statePath, "utf8"));
		state.schemaVersion = 1;
		await writeFile(statePath, `${JSON.stringify(state)}\n`, "utf8");
		expect(manager(agentDir, source).status().issues).toEqual(expect.arrayContaining([
			expect.stringContaining("Unsupported repository skill state schema"),
		]));
	});

	it("exposes the conflict error type for local official-id drift", async () => {
		const root = await makeRoot();
		const source = await createSourceRepository(root);
		const agentDir = path.join(root, "agent");
		await manager(agentDir, source).install();
		await writeFile(
			path.join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md"),
			[
				"---",
				"name: alpha",
				'description: "Locally modified alpha skill."',
				"disable-model-invocation: true",
				"metadata:",
				"  disco-role: operating",
				"---",
				"",
				"# Locally modified alpha",
			].join("\n"),
			"utf8",
		);
		await expect(manager(agentDir, source).update()).rejects.toBeInstanceOf(RepoSkillsLibraryConflictError);
	});
});
