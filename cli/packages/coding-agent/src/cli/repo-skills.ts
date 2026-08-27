import chalk from "chalk";
import { APP_NAME } from "../config.ts";
import {
	RepoSkillsLibraryError,
	RepoSkillsLibraryManager,
	type RepoSkillsInstallResult,
	type RepoSkillsLibraryStatus,
	type RepoSkillsRouterToggleResult,
} from "../core/repo-skills-library-manager.ts";

export type RepoSkillsCommand =
	| { type: "help" }
	| { type: "install" | "update"; force: boolean }
	| { type: "status" }
	| { type: "router"; enabled: boolean };

interface RepoSkillsCommandManager {
	install(options?: { force?: boolean }): Promise<RepoSkillsInstallResult>;
	update(options?: { force?: boolean }): Promise<RepoSkillsInstallResult>;
	status(): RepoSkillsLibraryStatus;
	setRouterEnabled(enabled: boolean): Promise<RepoSkillsRouterToggleResult>;
}

export interface RepoSkillsCommandHandlerOptions {
	manager?: RepoSkillsCommandManager;
}

function usage(): string {
	return `${APP_NAME} repo-skills <install|update|status|router enable|router disable>`;
}

export function printRepoSkillsHelp(): void {
	console.log(`${chalk.bold("Usage:")}
  ${APP_NAME} repo-skills install [--force]
  ${APP_NAME} repo-skills update [--force]
  ${APP_NAME} repo-skills status
  ${APP_NAME} repo-skills router disable
  ${APP_NAME} repo-skills router enable

Install and update DisCo's published repository skill collection.

Commands:
  install          Install or adopt the official repo skills and build the router
  update           Update managed official skills while preserving local Creator skills
  status           Show source commit, local drift, skill counts, and router state
  router disable   Stop automatic router selection; explicit /skill: invocation remains available
  router enable    Restore automatic router selection

Options:
  --force          Back up and replace conflicting or locally modified official skills
  -h, --help       Show this help
`);
}

export function parseRepoSkillsCommand(args: string[]): RepoSkillsCommand | undefined {
	const normalizedArgs = args.filter((arg) => arg !== "--offline");
	if (normalizedArgs[0] !== "repo-skills") return undefined;
	const rest = normalizedArgs.slice(1);
	if (rest.length === 0 || rest[0] === "-h" || rest[0] === "--help") return { type: "help" };
	const command = rest[0];
	if (command === "install" || command === "update") {
		let force = false;
		for (const arg of rest.slice(1)) {
			if (arg === "-h" || arg === "--help") return { type: "help" };
			if (arg === "--force") {
				force = true;
				continue;
			}
			throw new RepoSkillsLibraryError(`Unknown option for ${command}: ${arg}\nUsage: ${usage()}`, 2);
		}
		return { type: command, force };
	}
	if (command === "status") {
		if (rest.length > 1) {
			if (rest[1] === "-h" || rest[1] === "--help") return { type: "help" };
			throw new RepoSkillsLibraryError(`Unexpected argument for status: ${rest[1]}\nUsage: ${usage()}`, 2);
		}
		return { type: "status" };
	}
	if (command === "router") {
		if (rest[1] === "-h" || rest[1] === "--help") return { type: "help" };
		if (rest.length !== 2 || (rest[1] !== "enable" && rest[1] !== "disable")) {
			throw new RepoSkillsLibraryError(`Router command must be "enable" or "disable".\nUsage: ${usage()}`, 2);
		}
		return { type: "router", enabled: rest[1] === "enable" };
	}
	throw new RepoSkillsLibraryError(`Unknown repo-skills command: ${command}\nUsage: ${usage()}`, 2);
}

function printInstallResult(result: RepoSkillsInstallResult): void {
	if (result.noop) {
		console.log(
			result.operation === "install"
				? "Repository skills are already managed. Run `disco repo-skills update` to check for updates."
				: "Repository skills are already up to date.",
		);
	} else {
		console.log(
			`${result.operation === "install" ? "Installed" : "Updated"} repository skills${result.commit ? ` from commit ${result.commit}` : ""}.`,
		);
	}
	console.log(`Official skills: ${result.managedSkills}`);
	console.log(`Local skills preserved: ${result.localSkills}`);
	console.log(`Total repo skills: ${result.totalSkills}`);
	if (result.repositoryCount !== undefined) console.log(`Routed repositories: ${result.repositoryCount}`);
	if (result.assignmentCount !== undefined) console.log(`Area-family assignments: ${result.assignmentCount}`);
	if (result.areaCount !== undefined && result.familyCount !== undefined) {
		console.log(`Router taxonomy: ${result.areaCount} areas, ${result.familyCount} families`);
	}
	if (result.routerEnabled !== undefined) {
		console.log(`Router: ${result.routerEnabled ? "enabled" : "disabled"}`);
	}
	if (result.backupPath) console.log(`Backup: ${result.backupPath}`);
	for (const issue of result.issues) console.error(chalk.yellow(`Warning: ${issue}`));
	console.log("Start a new Researcher session to load the updated repository skill index.");
}

function printStatus(status: RepoSkillsLibraryStatus): void {
	console.log(`Installed: ${status.installed ? "yes" : "no"}`);
	console.log(`Managed by DisCo: ${status.managed ? "yes" : "no"}`);
	if (status.sourceRepository) console.log(`Source: ${status.sourceRepository}`);
	if (status.commit) console.log(`Commit: ${status.commit} (${status.commit.slice(0, 12)})`);
	if (status.installedAt) console.log(`Installed at: ${status.installedAt}`);
	if (status.updatedAt) console.log(`Updated at: ${status.updatedAt}`);
	console.log(`Official skills: ${status.managedSkills}`);
	console.log(`Local skills: ${status.localSkills}`);
	console.log(`Total repo skills: ${status.totalSkills}`);
	if (status.repositoryCount !== undefined) console.log(`Routed repositories: ${status.repositoryCount}`);
	if (status.assignmentCount !== undefined) console.log(`Area-family assignments: ${status.assignmentCount}`);
	if (status.areaCount !== undefined && status.familyCount !== undefined) {
		console.log(`Router taxonomy: ${status.areaCount} areas, ${status.familyCount} families`);
	}
	console.log(`Files: ${status.totalFiles}`);
	console.log(
		`Router: ${status.routerPresent ? (status.routerEnabled ? "enabled" : "disabled") : "not installed"}`,
	);
	if (status.issues.length === 0) console.log("Drift: none");
	else {
		console.log("Drift/issues:");
		for (const issue of status.issues) console.log(`- ${issue}`);
	}
}

function printRouterResult(result: RepoSkillsRouterToggleResult): void {
	if (result.enabled) {
		console.log(result.changed ? "Enabled repo-skills-router automatic selection." : "Repo-skills-router is already enabled.");
	} else {
		console.log(
			result.changed
				? "Disabled repo-skills-router automatic selection. Explicit /skill:repo-skills-router invocation remains available."
				: "Repo-skills-router automatic selection is already disabled. Explicit /skill:repo-skills-router invocation remains available.",
		);
	}
	console.log("Start a new Researcher session for the change to take effect.");
}

export async function handleRepoSkillsCommand(
	args: string[],
	options: RepoSkillsCommandHandlerOptions = {},
): Promise<boolean> {
	let command: RepoSkillsCommand | undefined;
	try {
		command = parseRepoSkillsCommand(args);
	} catch (error) {
		if (args.filter((arg) => arg !== "--offline")[0] !== "repo-skills") return false;
		const message = error instanceof Error ? error.message : String(error);
		console.error(chalk.red(`Error: ${message}`));
		process.exitCode = error instanceof RepoSkillsLibraryError ? error.exitCode : 1;
		return true;
	}
	if (!command) return false;
	if (command.type === "help") {
		printRepoSkillsHelp();
		return true;
	}

	const manager = options.manager ?? new RepoSkillsLibraryManager();
	try {
		if (command.type === "install") printInstallResult(await manager.install({ force: command.force }));
		else if (command.type === "update") printInstallResult(await manager.update({ force: command.force }));
		else if (command.type === "status") {
			const status = manager.status();
			printStatus(status);
			if (status.issues.length > 0) process.exitCode = 1;
		} else if (command.type === "router") {
			printRouterResult(await manager.setRouterEnabled(command.enabled));
		}
	} catch (error) {
		const message = error instanceof Error ? error.message : String(error);
		console.error(chalk.red(`Error: ${message}`));
		process.exitCode = error instanceof RepoSkillsLibraryError ? error.exitCode : 1;
	}
	return true;
}
