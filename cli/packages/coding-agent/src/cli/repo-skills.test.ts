import { afterEach, describe, expect, it, vi } from "vitest";
import type {
	RepoSkillsInstallResult,
	RepoSkillsLibraryStatus,
	RepoSkillsRouterToggleResult,
} from "../core/repo-skills-library-manager.ts";
import { RepoSkillsLibraryConflictError } from "../core/repo-skills-library-manager.ts";
import { handleRepoSkillsCommand, parseRepoSkillsCommand } from "./repo-skills.ts";

function installResult(overrides: Partial<RepoSkillsInstallResult> = {}): RepoSkillsInstallResult {
	return {
		operation: "install",
		commit: "a".repeat(40),
		managedSkills: 170,
		localSkills: 2,
		totalSkills: 172,
		routerEnabled: true,
		noop: false,
		issues: [],
		...overrides,
	};
}

function statusResult(overrides: Partial<RepoSkillsLibraryStatus> = {}): RepoSkillsLibraryStatus {
	return {
		installed: true,
		managed: true,
		sourceRepository: "https://github.com/VectorSpaceLab/AREX-Skill.git",
		commit: "a".repeat(40),
		managedSkills: 170,
		localSkills: 2,
		totalSkills: 172,
		totalFiles: 1000,
		routerPresent: true,
		routerEnabled: true,
		issues: [],
		...overrides,
	};
}

function fakeManager() {
	return {
		install: vi.fn(async (): Promise<RepoSkillsInstallResult> => installResult()),
		update: vi.fn(async (): Promise<RepoSkillsInstallResult> => installResult({ operation: "update" })),
		status: vi.fn((): RepoSkillsLibraryStatus => statusResult()),
		setRouterEnabled: vi.fn(
			async (enabled: boolean): Promise<RepoSkillsRouterToggleResult> => ({ enabled, changed: true }),
		),
	};
}

afterEach(() => {
	vi.restoreAllMocks();
	process.exitCode = undefined;
});

describe("repo-skills CLI", () => {
	it("parses the command namespace without claiming unrelated commands", () => {
		expect(parseRepoSkillsCommand(["repo-skills", "install", "--force"])).toEqual({
			type: "install",
			force: true,
		});
		expect(parseRepoSkillsCommand(["repo-skills", "router", "disable"])).toEqual({
			type: "router",
			enabled: false,
		});
		expect(parseRepoSkillsCommand(["--offline", "repo-skills", "status"])).toEqual({ type: "status" });
		expect(parseRepoSkillsCommand(["update"])).toBeUndefined();
	});

	it("handles nested help and restricts --force to install and update", () => {
		expect(parseRepoSkillsCommand(["repo-skills"])).toEqual({ type: "help" });
		expect(parseRepoSkillsCommand(["repo-skills", "install", "--help"])).toEqual({ type: "help" });
		expect(parseRepoSkillsCommand(["repo-skills", "router", "--help"])).toEqual({ type: "help" });
		expect(parseRepoSkillsCommand(["repo-skills", "update", "--force"])).toEqual({
			type: "update",
			force: true,
		});
		expect(() => parseRepoSkillsCommand(["repo-skills", "status", "--force"])).toThrow(
			"Unexpected argument for status",
		);
		expect(() => parseRepoSkillsCommand(["repo-skills", "router", "disable", "--force"])).toThrow(
			'Router command must be "enable" or "disable"',
		);
	});

	it("runs install with force and reports preserved local skills", async () => {
		const manager = fakeManager();
		const output = vi.spyOn(console, "log").mockImplementation(() => undefined);

		expect(await handleRepoSkillsCommand(["repo-skills", "install", "--force"], { manager })).toBe(true);

		expect(manager.install).toHaveBeenCalledWith({ force: true });
		expect(output.mock.calls.flat().join("\n")).toContain("Local skills preserved: 2");
	});

	it("reports drift through status and returns a failing exit code", async () => {
		const manager = fakeManager();
		manager.status.mockReturnValue(statusResult({ issues: ["alpha-skill: managed skill is modified"] }));
		vi.spyOn(console, "log").mockImplementation(() => undefined);

		await handleRepoSkillsCommand(["repo-skills", "status"], { manager });

		expect(process.exitCode).toBe(1);
	});

	it("disables automatic router selection while retaining explicit invocation guidance", async () => {
		const manager = fakeManager();
		const output = vi.spyOn(console, "log").mockImplementation(() => undefined);

		await handleRepoSkillsCommand(["repo-skills", "router", "disable"], { manager });

		expect(manager.setRouterEnabled).toHaveBeenCalledWith(false);
		expect(output.mock.calls.flat().join("\n")).toContain("Explicit /skill:repo-skills-router invocation remains available");
	});

	it("rejects unknown nested commands with usage exit code 2", async () => {
		const error = vi.spyOn(console, "error").mockImplementation(() => undefined);

		expect(await handleRepoSkillsCommand(["repo-skills", "remove"])).toBe(true);

		expect(process.exitCode).toBe(2);
		expect(error.mock.calls.flat().join("\n")).toContain("Unknown repo-skills command");
	});

	it("maps conflicts to exit code 2 and operational failures to exit code 1", async () => {
		const manager = fakeManager();
		vi.spyOn(console, "error").mockImplementation(() => undefined);
		manager.install.mockRejectedValueOnce(new RepoSkillsLibraryConflictError(["alpha-skill: local drift"]));

		await handleRepoSkillsCommand(["repo-skills", "install"], { manager });
		expect(process.exitCode).toBe(2);

		process.exitCode = undefined;
		manager.update.mockRejectedValueOnce(new Error("Git fetch failed"));
		await handleRepoSkillsCommand(["repo-skills", "update"], { manager });
		expect(process.exitCode).toBe(1);
	});
});
