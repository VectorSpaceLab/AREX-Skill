import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterAll, describe, expect, it } from "vitest";

const scriptPath = path.join(
	process.cwd(),
	"packages/coding-agent/src/disco/skills/verify-repo-skill/scripts/update_repo_skills_router.mjs",
);
const cleanup: string[] = [];
const fixtureTaxonomy = {
	title: "Test taxonomy",
	areas: [
		{ name: "Vision", scope: "Vision tasks.", families: [{ name: "Classification", scope: "Image classification." }, { name: "Detection", scope: "Object detection." }] },
		{ name: "Language", scope: "Language tasks.", families: [{ name: "Embeddings", scope: "Text embeddings." }] },
	],
};
const fixtureTaxonomyHash = createHash("sha256").update(`${JSON.stringify(fixtureTaxonomy, null, 2)}\n`).digest("hex");

async function writeSkill(root: string, id: string, repoId: string, assignments: Array<{ area: string; family: string }>): Promise<void> {
	const skill = path.join(root, "repo-skills", id);
	await mkdir(path.join(skill, "references"), { recursive: true });
	await writeFile(
		path.join(skill, "SKILL.md"),
		[
			"---",
			`name: ${id}`,
			`description: "Use ${id} for focused repository workflows."`,
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
		path.join(skill, "references", "repo-routing-metadata.json"),
		`${JSON.stringify({ schema_version: "2.0", repo_id: repoId, skill_id: id, taxonomy_sha256: fixtureTaxonomyHash, routing_status: "classified", assignments }, null, 2)}\n`,
		"utf8",
	);
	const assignmentIndex = path.join(root, "repo-skills-router", "references", "index", "assignments.jsonl");
	await mkdir(path.dirname(assignmentIndex), { recursive: true });
	const existing = existsSync(assignmentIndex) ? await readFile(assignmentIndex, "utf8") : "";
	const records = assignments.map((assignment) => JSON.stringify({
		repo_id: repoId,
		legacy_repo_id: `legacy/${id}`,
		skill_id: id,
		area: assignment.area,
		family: assignment.family,
		confidence: "high",
	})).join("\n");
	await writeFile(assignmentIndex, `${existing}${records}\n`, "utf8");
}

async function writeTemplate(root: string): Promise<string> {
	const template = path.join(root, "template");
	await mkdir(path.join(template, "references", "index"), { recursive: true });
	await writeFile(
		path.join(template, "SKILL.md"),
		[
			"---",
			"name: repo-skills-router",
			'description: "Repository skills router template."',
			"metadata:",
			"  disco-role: operating",
			"---",
			"",
			"# Router template",
		].join("\n"),
		"utf8",
	);
	await writeFile(path.join(template, "references", "index", "taxonomy.json"), `${JSON.stringify(fixtureTaxonomy, null, 2)}\n`, "utf8");
	return template;
}

function run(libraryRoot: string, templateDir: string, extra: string[] = []) {
	return spawnSync(process.execPath, [scriptPath, "--library-root", libraryRoot, "--template-dir", templateDir, ...extra], {
		encoding: "utf8",
		env: { ...process.env, DISCO_ROUTER_ALLOW_NONCANONICAL_TAXONOMY_FOR_TESTS: "1" },
	});
}

describe("area/family repository skills router updater", () => {
	it("builds deterministic root, area, family, and machine indexes", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "router-area-family-"));
		cleanup.push(root);
		const library = path.join(root, "library");
		await mkdir(path.join(library, "repo-skills"), { recursive: true });
		const template = await writeTemplate(root);
		await writeSkill(library, "alpha", "owner/alpha", [{ area: "Vision", family: "Classification" }]);
		await writeSkill(library, "beta", "owner/beta", [{ area: "Vision", family: "Detection" }, { area: "Language", family: "Embeddings" }]);
		const result = run(library, template);
		expect(result.status, result.stderr).toBe(0);
		expect(result.stdout).toContain("2 skills, 3 assignments, 2 areas, 3 families");
		const router = path.join(library, "repo-skills-router");
		expect(await readFile(path.join(router, "SKILL.md"), "utf8")).toContain("[Vision](references/areas/vision.md)");
		expect(await readFile(path.join(router, "references", "areas", "vision.md"), "utf8")).toContain("Classification");
		expect(await readFile(path.join(router, "references", "families", "vision", "classification.md"), "utf8")).toContain("../../../../repo-skills/alpha/SKILL.md");
		expect((await readFile(path.join(library, "repo-skills", "repository-index.jsonl"), "utf8")).trim().split("\n")).toHaveLength(2);
		expect((await readFile(path.join(router, "references", "index", "assignments.jsonl"), "utf8")).trim().split("\n")).toHaveLength(3);
		expect(await readFile(path.join(router, "references", "index", "assignments.jsonl"), "utf8")).toContain('"confidence":"high"');
	});

	it("builds a filtered router without mutating the source collection index", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "router-subset-"));
		cleanup.push(root);
		const library = path.join(root, "library");
		await mkdir(path.join(library, "repo-skills"), { recursive: true });
		const template = await writeTemplate(root);
		await writeSkill(library, "alpha", "owner/alpha", [{ area: "Vision", family: "Classification" }]);
		await writeSkill(library, "beta", "owner/beta", [{ area: "Vision", family: "Detection" }]);
		expect(run(library, template).status).toBe(0);
		const before = await readFile(path.join(library, "repo-skills", "repository-index.jsonl"), "utf8");
		const output = path.join(root, "filtered-router");
		const result = run(library, template, ["--include-skill", "alpha", "--output-router-dir", output]);
		expect(result.status, result.stderr).toBe(0);
		expect(await readFile(path.join(output, "references", "index", "repositories.jsonl"), "utf8")).toContain("owner/alpha");
		expect(await readFile(path.join(output, "references", "index", "repositories.jsonl"), "utf8")).not.toContain("owner/beta");
		expect(await readFile(path.join(library, "repo-skills", "repository-index.jsonl"), "utf8")).toBe(before);
		expect(existsSync(path.join(output, "references", "families", "vision", "detection.md"))).toBe(false);
		expect(existsSync(path.join(output, "references", "areas", "language.md"))).toBe(false);
		expect(await readFile(path.join(output, "SKILL.md"), "utf8")).not.toContain("[Language](references/areas/language.md)");
		expect(await readFile(path.join(output, "references", "index", "build-metadata.json"), "utf8")).not.toContain("generated_at");

		const secondOutput = path.join(root, "filtered-router-second");
		const secondResult = run(library, template, ["--include-skill", "alpha", "--output-router-dir", secondOutput]);
		expect(secondResult.status, secondResult.stderr).toBe(0);
		expect(await readFile(path.join(output, "SKILL.md"), "utf8")).toBe(await readFile(path.join(secondOutput, "SKILL.md"), "utf8"));
		expect(await readFile(path.join(output, "references", "index", "build-metadata.json"), "utf8")).toBe(await readFile(path.join(secondOutput, "references", "index", "build-metadata.json"), "utf8"));
	});

	it("fails closed on a non-exact taxonomy assignment", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "router-invalid-"));
		cleanup.push(root);
		const library = path.join(root, "library");
		await mkdir(path.join(library, "repo-skills"), { recursive: true });
		const template = await writeTemplate(root);
		await writeSkill(library, "bad", "owner/bad", [{ area: "Vision", family: "Not In Taxonomy" }]);
		const result = run(library, template);
		expect(result.status).toBe(2);
		expect(result.stderr).toContain("unknown taxonomy path");
	});

	it("recomputes repository content digests after a skill refresh", async () => {
		const root = await mkdtemp(path.join(tmpdir(), "router-digest-refresh-"));
		cleanup.push(root);
		const library = path.join(root, "library");
		await mkdir(path.join(library, "repo-skills"), { recursive: true });
		const template = await writeTemplate(root);
		await writeSkill(library, "alpha", "owner/alpha", [{ area: "Vision", family: "Classification" }]);
		const first = run(library, template);
		expect(first.status, first.stderr).toBe(0);
		const indexPath = path.join(library, "repo-skills-router", "references", "index", "repositories.jsonl");
		const firstRecord = JSON.parse((await readFile(indexPath, "utf8")).trim());
		await writeFile(path.join(library, "repo-skills", "alpha", "SKILL.md"), `${await readFile(path.join(library, "repo-skills", "alpha", "SKILL.md"), "utf8")}\nrefreshed\n`, "utf8");
		const second = run(library, template);
		expect(second.status, second.stderr).toBe(0);
		const secondRecord = JSON.parse((await readFile(indexPath, "utf8")).trim());
		expect(secondRecord.content_sha256).not.toBe(firstRecord.content_sha256);
	});
});

afterAll(async () => {
		for (const root of cleanup.splice(0)) await rm(root, { recursive: true, force: true });
});
