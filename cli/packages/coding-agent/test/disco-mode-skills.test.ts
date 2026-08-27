import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { getModelVisibleSkills, loadSkills } from "../src/core/skills.ts";

type SkillRoleFixture = "meta" | "operating" | "shared" | "missing" | "invalid";

function writeSkill(root: string, directory: string, name: string, role: SkillRoleFixture, hidden = false): string {
	const skillDir = join(root, directory);
	mkdirSync(skillDir, { recursive: true });
	const frontmatter = ["---", `name: ${name}`, `description: "Use ${name} for a focused test workflow."`];
	if (hidden) frontmatter.push("disable-model-invocation: true");
	if (role !== "missing") {
		frontmatter.push("metadata:", `  disco-role: ${role === "invalid" ? "Meta" : role}`);
	}
	frontmatter.push("---", "", `# ${name}`);
	const skillPath = join(skillDir, "SKILL.md");
	writeFileSync(skillPath, frontmatter.join("\n"), "utf8");
	return skillPath;
}

describe("mode-aware skill loading", () => {
	const cleanupPaths: string[] = [];

	afterEach(() => {
		for (const path of cleanupPaths.splice(0)) rmSync(path, { recursive: true, force: true });
	});

	function createCorpus(): { root: string; agentDir: string; cwd: string } {
		const root = mkdtempSync(join(tmpdir(), "disco-mode-skills-"));
		cleanupPaths.push(root);
		const agentDir = join(root, "agent");
		const cwd = join(root, "project");
		mkdirSync(cwd, { recursive: true });
		const managedSkillsRoot = join(agentDir, "skills");
		const repoSkillsRoot = join(managedSkillsRoot, "repo-skills");

		writeSkill(managedSkillsRoot, "untagged", "untagged", "missing");
		writeSkill(repoSkillsRoot, "operating", "operating", "operating");
		writeSkill(repoSkillsRoot, "hidden-operating", "hidden-operating", "operating", true);
		writeSkill(repoSkillsRoot, "invalid", "invalid", "invalid");
		writeSkill(repoSkillsRoot, "collision-operating", "shared-name", "operating");
		writeSkill(managedSkillsRoot, "repo-skills-router", "repo-skills-router", "operating");
		writeSkill(join(cwd, ".disco", "skills"), "meta", "meta", "meta");
		writeSkill(join(cwd, ".disco", "skills"), "collision-meta", "shared-name", "meta");

		return { root, agentDir, cwd };
	}

	it("loads missing-role and operating skills only in Researcher", () => {
		const { agentDir, cwd } = createCorpus();
		const result = loadSkills({ agentDir, cwd, skillPaths: [], includeDefaults: true, discoMode: "researcher" });
		const names = result.skills.map((skill) => skill.name).sort();

		expect(names).toEqual(["hidden-operating", "operating", "repo-skills-router", "shared-name", "untagged"]);
		expect(result.skills.find((skill) => skill.name === "untagged")?.discoRole).toBe("operating");
		expect(
			result.diagnostics.filter((diagnostic) => diagnostic.message.includes("metadata.disco-role")),
		).toHaveLength(1);
		expect(result.diagnostics.some((diagnostic) => diagnostic.type === "collision")).toBe(false);
		expect(getModelVisibleSkills(result.skills).map((skill) => skill.name)).not.toContain("hidden-operating");
	});

	it("loads only explicit meta skills in Creator and filters before collision resolution", () => {
		const { agentDir, cwd } = createCorpus();
		const result = loadSkills({ agentDir, cwd, skillPaths: [], includeDefaults: true, discoMode: "creator" });

		expect(result.skills.map((skill) => skill.name).sort()).toEqual(["meta", "shared-name"]);
		expect(result.skills.every((skill) => skill.discoRole === "meta")).toBe(true);
		expect(result.diagnostics.some((diagnostic) => diagnostic.type === "collision")).toBe(false);
	});

	it("applies the missing-role fallback to explicit external skill paths", () => {
		const { root, agentDir, cwd } = createCorpus();
		const externalRoot = join(root, ".agents", "skills");
		writeSkill(externalRoot, "external", "external", "missing");

		const researcher = loadSkills({
			agentDir,
			cwd,
			skillPaths: [externalRoot],
			includeDefaults: false,
			discoMode: "researcher",
		});
		const creator = loadSkills({
			agentDir,
			cwd,
			skillPaths: [externalRoot],
			includeDefaults: false,
			discoMode: "creator",
		});

		expect(researcher.skills.map((skill) => skill.name)).toEqual(["external"]);
		expect(researcher.diagnostics).toEqual([]);
		expect(creator.skills).toEqual([]);
		expect(creator.diagnostics).toEqual([]);
	});

	it("loads shared skills in both modes while keeping hidden shared skills out of model inventory", () => {
		const { root, agentDir, cwd } = createCorpus();
		const sharedRoot = join(root, "shared-skills");
		writeSkill(sharedRoot, "visible", "shared-visible", "shared");
		writeSkill(sharedRoot, "hidden", "shared-hidden", "shared", true);

		for (const discoMode of ["creator", "researcher"] as const) {
			const result = loadSkills({
				agentDir,
				cwd,
				skillPaths: [sharedRoot],
				includeDefaults: false,
				discoMode,
			});

			expect(result.skills.map((skill) => skill.name).sort()).toEqual(["shared-hidden", "shared-visible"]);
			expect(result.skills.every((skill) => skill.discoRole === "shared")).toBe(true);
			expect(getModelVisibleSkills(result.skills).map((skill) => skill.name)).toEqual(["shared-visible"]);
		}
	});

	it("keeps a 1,000-repository managed collection registered but out of the Researcher prompt", () => {
		const root = mkdtempSync(join(tmpdir(), "disco-repository-skills-scale-"));
		cleanupPaths.push(root);
		const agentDir = join(root, "agent");
		const cwd = join(root, "project");
		const repositoriesRoot = join(agentDir, "skills", "repositories");
		const repoSkillsRoot = join(repositoriesRoot, "repo-skills");
		mkdirSync(cwd, { recursive: true });

		for (let index = 0; index < 1_000; index += 1) {
			const id = `repository-${String(index).padStart(4, "0")}`;
			writeSkill(repoSkillsRoot, id, id, "operating", true);
		}
		writeSkill(repositoriesRoot, "repo-skills-router", "repo-skills-router", "operating");

		const startedAt = performance.now();
		const result = loadSkills({ agentDir, cwd, skillPaths: [], includeDefaults: true, discoMode: "researcher" });
		const elapsedMs = performance.now() - startedAt;
		const visible = getModelVisibleSkills(result.skills);

		expect(result.skills).toHaveLength(1_001);
		expect(result.diagnostics).toEqual([]);
		expect(visible.map((skill) => skill.name)).toEqual(["repo-skills-router"]);
		expect(result.skills.filter((skill) => skill.disableModelInvocation)).toHaveLength(1_000);
		expect(elapsedMs).toBeLessThan(15_000);
	});

});
