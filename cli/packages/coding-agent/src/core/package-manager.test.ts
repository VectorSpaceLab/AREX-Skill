import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { describe, expect, it } from "vitest";
import { getBundledSkillsDir } from "../config.ts";
import { DefaultResourceLoader } from "./resource-loader.ts";
import { DefaultPackageManager } from "./package-manager.ts";
import type { SettingsManager } from "./settings-manager.ts";
import { loadSkills } from "./skills.ts";

function createSettingsManagerStub(
	globalSettings: Record<string, unknown> = {},
	projectSettings: Record<string, unknown> = {},
	projectTrusted = false,
): SettingsManager {
	return {
		getGlobalSettings: () => globalSettings,
		getProjectSettings: () => projectSettings,
		isProjectTrusted: () => projectTrusted,
		reload: async () => {},
		setProjectTrusted: () => {},
	} as unknown as SettingsManager;
}

function writeSkill(filePath: string, name: string, description = `${name} test skill.`): void {
	mkdirSync(dirname(filePath), { recursive: true });
	writeFileSync(
		filePath,
		[
			"---",
			`name: ${name}`,
			`description: ${JSON.stringify(description)}`,
			"metadata:",
			"  disco-role: operating",
			"---",
			"",
			`# ${name}`,
		].join("\n"),
		"utf8",
	);
}

async function withTemporaryHome<T>(callback: (homeDir: string) => Promise<T>): Promise<T> {
	const homeDir = mkdtempSync(join(tmpdir(), "disco-package-manager-home-"));
	const previousHome = process.env.HOME;
	process.env.HOME = homeDir;
	try {
		return await callback(homeDir);
	} finally {
		if (previousHome === undefined) delete process.env.HOME;
		else process.env.HOME = previousHome;
		rmSync(homeDir, { recursive: true, force: true });
	}
}

function createManager(
	cwd: string,
	agentDir: string,
	settingsManager: SettingsManager,
	discoMode: "creator" | "researcher",
	includeDisCoBuiltinSkills = false,
): DefaultPackageManager {
	return new DefaultPackageManager({
		cwd,
		agentDir,
		settingsManager,
		includeDisCoDefaults: false,
		includeDisCoBuiltinSkills,
		discoMode,
	});
}

function enabledSkillPaths(resolved: Awaited<ReturnType<DefaultPackageManager["resolve"]>>): string[] {
	return resolved.skills.filter((entry) => entry.enabled).map((entry) => entry.path);
}

describe("repository skill export discovery", () => {
	it("ignores global exported copies when Researcher has the managed counterparts", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedSglang = join(agentDir, "skills", "repositories", "repo-skills", "sglang", "SKILL.md");
			const managedVllm = join(agentDir, "skills", "repositories", "repo-skills", "vllm", "SKILL.md");
			const managedRouter = join(agentDir, "skills", "repositories", "repo-skills-router", "SKILL.md");
			const externalSglang = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "sglang", "SKILL.md");
			const externalVllm = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "vllm", "SKILL.md");
			const externalRouter = join(homeDir, ".agents", "skills", "repositories", "repo-skills-router", "SKILL.md");

			writeSkill(managedSglang, "sglang", "DisCo managed SGLang skill.");
			writeSkill(managedVllm, "vllm", "DisCo managed vLLM skill.");
			writeSkill(managedRouter, "repo-skills-router", "DisCo managed router.");
			writeSkill(externalSglang, "sglang", "Exported SGLang copy.");
			writeSkill(externalVllm, "vllm", "Exported vLLM copy.");
			writeSkill(externalRouter, "repo-skills-router", "Exported router copy.");

			const manager = createManager(cwd, agentDir, createSettingsManagerStub(), "researcher");
			const resolved = await manager.resolve();
			const paths = enabledSkillPaths(resolved);

			expect(paths).toContain(managedSglang);
			expect(paths).toContain(managedVllm);
			expect(paths).toContain(managedRouter);
			expect(paths).not.toContain(externalSglang);
			expect(paths).not.toContain(externalVllm);
			expect(paths).not.toContain(externalRouter);

			const loaded = loadSkills({ cwd, agentDir, skillPaths: paths, includeDefaults: false, discoMode: "researcher" });
			expect(loaded.diagnostics.filter((diagnostic) => diagnostic.type === "collision")).toEqual([]);
			expect(loaded.skills.map((skill) => skill.filePath)).toEqual(expect.arrayContaining([managedSglang, managedVllm, managedRouter]));
		});
	});

	it("keeps unmanaged exports and ordinary external skills", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedAlpha = join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const externalAlpha = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const externalOrphan = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "orphan", "SKILL.md");
			const ordinaryExternal = join(homeDir, ".agents", "skills", "standalone-user-skill", "SKILL.md");

			writeSkill(managedAlpha, "alpha", "DisCo managed alpha skill.");
			writeSkill(externalAlpha, "alpha", "Exported alpha copy.");
			writeSkill(externalOrphan, "orphan", "Unmanaged repository export.");
			writeSkill(ordinaryExternal, "standalone-user-skill", "Ordinary external skill.");

			const manager = createManager(cwd, agentDir, createSettingsManagerStub(), "researcher");
			const paths = enabledSkillPaths(await manager.resolve());

			expect(paths).toContain(managedAlpha);
			expect(paths).not.toContain(externalAlpha);
			expect(paths).toContain(externalOrphan);
			expect(paths).toContain(ordinaryExternal);
		});
	});

	it("keeps ordinary same-name external skills in normal collision handling", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedAlpha = join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const ordinaryAlpha = join(homeDir, ".agents", "skills", "ordinary-alpha", "SKILL.md");

			writeSkill(managedAlpha, "alpha", "DisCo managed alpha skill.");
			writeSkill(ordinaryAlpha, "alpha", "Ordinary same-name external skill.");

			const manager = createManager(cwd, agentDir, createSettingsManagerStub(), "researcher");
			const paths = enabledSkillPaths(await manager.resolve());
			const loaded = loadSkills({ cwd, agentDir, skillPaths: paths, includeDefaults: false, discoMode: "researcher" });
			const collision = loaded.diagnostics.find(
				(diagnostic) => diagnostic.type === "collision" && diagnostic.collision?.name === "alpha",
			);

			expect(paths).toContain(managedAlpha);
			expect(paths).toContain(ordinaryAlpha);
			expect(collision?.collision?.winnerPath).toBe(managedAlpha);
			expect(collision?.collision?.loserPath).toBe(ordinaryAlpha);
		});
	});

	it("does not apply the Researcher auto-discovery filter in Creator mode", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedAlpha = join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const externalAlpha = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "alpha", "SKILL.md");

			writeSkill(managedAlpha, "alpha", "DisCo managed alpha skill.");
			writeSkill(externalAlpha, "alpha", "Exported alpha copy.");

			const manager = createManager(cwd, agentDir, createSettingsManagerStub(), "creator");
			const paths = enabledSkillPaths(await manager.resolve());

			expect(paths).toContain(managedAlpha);
			expect(paths).toContain(externalAlpha);
		});
	});

	it("keeps an explicitly configured external copy even in Researcher mode", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedAlpha = join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const externalAlpha = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "alpha", "SKILL.md");

			writeSkill(managedAlpha, "alpha", "DisCo managed alpha skill.");
			writeSkill(externalAlpha, "alpha", "Explicitly selected external alpha copy.");

			const manager = createManager(
				cwd,
				agentDir,
				createSettingsManagerStub({ skills: [externalAlpha] }),
				"researcher",
			);
			const resolved = await manager.resolve();
			const paths = enabledSkillPaths(resolved);

			expect(paths).toContain(managedAlpha);
			expect(paths).toContain(externalAlpha);
		});
	});

	it("respects a force-included external repository skill override", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedAlpha = join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const externalAlpha = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "alpha", "SKILL.md");

			writeSkill(managedAlpha, "alpha", "DisCo managed alpha skill.");
			writeSkill(externalAlpha, "alpha", "Force-included external alpha copy.");

			const manager = createManager(
				cwd,
				agentDir,
				createSettingsManagerStub({ skills: ["+skills/repositories/repo-skills/alpha"] }),
				"researcher",
			);
			const paths = enabledSkillPaths(await manager.resolve());

			expect(paths).toContain(managedAlpha);
			expect(paths).toContain(externalAlpha);
		});
	});

	it("keeps the external copy when the managed counterpart is disabled", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedAlpha = join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const externalAlpha = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "alpha", "SKILL.md");

			writeSkill(managedAlpha, "alpha", "Disabled DisCo managed alpha skill.");
			writeSkill(externalAlpha, "alpha", "Enabled external alpha copy.");

			const manager = createManager(
				cwd,
				agentDir,
				createSettingsManagerStub({ skills: [`-${managedAlpha}`] }),
				"researcher",
			);
			const resolved = await manager.resolve();
			const paths = enabledSkillPaths(resolved);

			expect(resolved.skills.find((entry) => entry.path === managedAlpha)?.enabled).toBe(false);
			expect(paths).toContain(externalAlpha);
		});
	});

	it("does not apply the global export filter to trusted project .agents skills", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedAlpha = join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const projectAlpha = join(cwd, ".agents", "skills", "repositories", "repo-skills", "alpha", "SKILL.md");

			writeSkill(managedAlpha, "alpha", "DisCo managed alpha skill.");
			writeSkill(projectAlpha, "alpha", "Trusted project alpha skill.");

			const manager = createManager(
				cwd,
				agentDir,
				createSettingsManagerStub({}, {}, true),
				"researcher",
			);
			const paths = enabledSkillPaths(await manager.resolve());

			expect(paths).toContain(managedAlpha);
			expect(paths).toContain(projectAlpha);
		});
	});

	it("does not let an external router suppress the bundled fallback", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const externalRouter = join(homeDir, ".agents", "skills", "repositories", "repo-skills-router", "SKILL.md");
			writeSkill(externalRouter, "repo-skills-router", "Exported router copy.");

			const manager = createManager(cwd, agentDir, createSettingsManagerStub(), "researcher", true);
			const paths = enabledSkillPaths(await manager.resolve());
			const bundledRouter = join(getBundledSkillsDir(), "repo-skills-router", "SKILL.md");

			expect(existsSync(bundledRouter)).toBe(true);
			expect(paths).toContain(bundledRouter);
			expect(paths).not.toContain(externalRouter);
		});
	});

	it("passes the active mode through the ResourceLoader without reporting duplicate diagnostics", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedAlpha = join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const externalAlpha = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "alpha", "SKILL.md");

			writeSkill(managedAlpha, "alpha", "DisCo managed alpha skill.");
			writeSkill(externalAlpha, "alpha", "Exported alpha copy.");

			const loader = new DefaultResourceLoader({
				cwd,
				agentDir,
				settingsManager: createSettingsManagerStub(),
				includeDisCoDefaults: false,
				includeDisCoBuiltinSkills: false,
				discoMode: "researcher",
			});
			await loader.reload();
			const result = loader.getSkills();

			expect(result.skills.map((skill) => skill.filePath)).toContain(managedAlpha);
			expect(result.skills.map((skill) => skill.filePath)).not.toContain(externalAlpha);
			expect(result.diagnostics.filter((diagnostic) => diagnostic.type === "collision")).toEqual([]);
		});
	});

	it("keeps an additional skill path explicit and reports the ordinary collision", async () => {
		await withTemporaryHome(async (homeDir) => {
			const cwd = join(homeDir, "project");
			const agentDir = join(homeDir, ".disco", "agent");
			const managedAlpha = join(agentDir, "skills", "repositories", "repo-skills", "alpha", "SKILL.md");
			const externalAlpha = join(homeDir, ".agents", "skills", "repositories", "repo-skills", "alpha", "SKILL.md");

			writeSkill(managedAlpha, "alpha", "DisCo managed alpha skill.");
			writeSkill(externalAlpha, "alpha", "Explicit additional alpha copy.");

			const loader = new DefaultResourceLoader({
				cwd,
				agentDir,
				settingsManager: createSettingsManagerStub(),
				includeDisCoDefaults: false,
				includeDisCoBuiltinSkills: false,
				discoMode: "researcher",
				additionalSkillPaths: [externalAlpha],
			});
			await loader.reload();
			const result = loader.getSkills();
			const collision = result.diagnostics.find(
				(diagnostic) => diagnostic.type === "collision" && diagnostic.collision?.name === "alpha",
			);

			expect(result.skills.map((skill) => skill.filePath)).toContain(managedAlpha);
			expect(collision?.collision?.winnerPath).toBe(managedAlpha);
			expect(collision?.collision?.loserPath).toBe(externalAlpha);
		});
	});
});
