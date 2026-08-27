#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const DEFAULT_TIMEOUT_SECONDS = 900;
const SCRIPT_PATH = fileURLToPath(import.meta.url);
const SCRIPT_DIR = path.dirname(SCRIPT_PATH);
const CANONICAL_NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

class ImportError extends Error {
	constructor(message) {
		super(message);
		this.name = "ImportError";
	}
}

function defaultAgentDir() {
	return process.env.DISCO_CODING_AGENT_DIR || path.join(os.homedir(), ".disco", "agent");
}

function withImportLockScript() {
	return path.resolve(SCRIPT_DIR, "..", "..", "verify-repo-skill", "scripts", "with_import_lock.mjs");
}

function expandHome(value) {
	return value.replace(/^~(?=$|[\\/])/, os.homedir());
}

function pathExists(filePath) {
	try {
		fs.lstatSync(filePath);
		return true;
	} catch (error) {
		if (error?.code === "ENOENT") return false;
		throw error;
	}
}

function isWithin(parent, candidate) {
	const relative = path.relative(parent, candidate);
	return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function optionValue(argv, index, option) {
	const value = argv[index + 1];
	if (!value || value.startsWith("--")) throw new ImportError(`${option} requires a value`);
	return value;
}

function parseArgs(argv) {
	const args = {
		scope: undefined,
		projectDir: undefined,
		agentDir: defaultAgentDir(),
		draftDirs: [],
		overwrite: false,
		alreadyLocked: false,
		timeout: DEFAULT_TIMEOUT_SECONDS,
	};

	for (let index = 0; index < argv.length; index += 1) {
		const item = argv[index];
		if (item === "--scope") {
			args.scope = optionValue(argv, index, item);
			index += 1;
		} else if (item === "--project-dir") {
			args.projectDir = optionValue(argv, index, item);
			index += 1;
		} else if (item === "--agent-dir") {
			args.agentDir = optionValue(argv, index, item);
			index += 1;
		} else if (item === "--timeout") {
			args.timeout = Number(optionValue(argv, index, item));
			index += 1;
		} else if (item === "--overwrite") {
			args.overwrite = true;
		} else if (item === "--already-locked") {
			args.alreadyLocked = true;
		} else if (item === "-h" || item === "--help") {
			printHelp();
			process.exit(0);
		} else if (item.startsWith("-")) {
			throw new ImportError(`unknown argument: ${item}`);
		} else {
			args.draftDirs.push(item);
		}
	}

	if (args.scope !== "project" && args.scope !== "managed") {
		throw new ImportError("--scope must be project or managed");
	}
	if (args.scope === "managed" && args.projectDir) {
		throw new ImportError("--project-dir is valid only with --scope project");
	}
	if (args.draftDirs.length === 0) {
		throw new ImportError("provide at least one draft operating skill directory");
	}
	if (!Number.isFinite(args.timeout) || args.timeout <= 0) {
		throw new ImportError("--timeout must be a positive number");
	}
	return args;
}

function printHelp() {
	console.log(`Usage: node import_operating_skill_graph.mjs --scope project|managed [options] DRAFT_SKILL_DIR...

Options:
  --scope SCOPE        Required deployment scope: project or managed
  --project-dir DIR    Project root for .agents/skills (defaults to cwd)
  --agent-dir DIR      DisCo agent directory and shared-lock owner
  --overwrite          Replace same-name targets after explicit approval
  --already-locked     Assert the shared skill import lock is already held
  --timeout SECONDS    Seconds to wait for the shared import lock`);
}

function parseFrontmatter(skillFile) {
	const content = fs.readFileSync(skillFile, "utf8");
	const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match?.[1]) throw new ImportError(`${skillFile} is missing YAML frontmatter`);
	let frontmatter;
	try {
		frontmatter = parse(match[1]);
	} catch (error) {
		throw new ImportError(
			`${skillFile} has invalid YAML frontmatter: ${error instanceof Error ? error.message : String(error)}`,
		);
	}
	if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter)) {
		throw new ImportError(`${skillFile} frontmatter must be a mapping`);
	}
	return { content, frontmatter };
}

function collectPortableFiles(root, files = []) {
	const stat = fs.lstatSync(root);
	if (!stat.isDirectory() || stat.isSymbolicLink()) {
		throw new ImportError(`draft operating skill must be a real directory: ${root}`);
	}
	for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
		const entryPath = path.join(root, entry.name);
		if (entry.isSymbolicLink()) {
			throw new ImportError(`draft operating skill contains a symbolic link: ${entryPath}`);
		}
		if (entry.isDirectory()) {
			collectPortableFiles(entryPath, files);
		} else if (entry.isFile()) {
			files.push(entryPath);
		} else {
			throw new ImportError(`draft operating skill contains a non-regular file: ${entryPath}`);
		}
	}
	return files;
}

function validateSkillFile(skillFile, seenNames) {
	const { frontmatter } = parseFrontmatter(skillFile);
	const name = frontmatter.name;
	if (typeof name !== "string" || !CANONICAL_NAME.test(name) || name.length > 64) {
		throw new ImportError(`${skillFile} must declare a canonical lowercase-hyphen name`);
	}
	if (name !== path.basename(path.dirname(skillFile))) {
		throw new ImportError(`${skillFile} name must match its directory basename`);
	}
	if (seenNames.has(name)) {
		throw new ImportError(`operating-skill graph contains duplicate skill name: ${name}`);
	}
	seenNames.add(name);

	const metadata = frontmatter.metadata;
	const role =
		typeof metadata === "object" && metadata !== null && !Array.isArray(metadata)
			? metadata["disco-role"]
			: undefined;
	if (role !== "operating") {
		throw new ImportError(`${skillFile} metadata.disco-role must be operating`);
	}
	if (name === "repo-skills-router" || name === "repo-skills") {
		throw new ImportError(`${name} is reserved for the repo-skill import workflow`);
	}
	return name;
}

function validateMarkdownLinks(skillRoots, markdownFiles) {
	for (const filePath of markdownFiles) {
		const content = fs.readFileSync(filePath, "utf8");
		for (const match of content.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
			const target = match[1]?.split("#", 1)[0];
			if (!target || /^(?:https?:|mailto:)/.test(target)) continue;
			let decodedTarget;
			try {
				decodedTarget = decodeURIComponent(target);
			} catch {
				throw new ImportError(`${filePath} contains an invalid encoded Markdown link: ${target}`);
			}
			const resolvedTarget = path.resolve(path.dirname(filePath), decodedTarget);
			if (!skillRoots.some((skillRoot) => isWithin(skillRoot, resolvedTarget))) {
				throw new ImportError(`${filePath} contains a relative link outside the operating-skill graph: ${target}`);
			}
			if (!pathExists(resolvedTarget)) {
				throw new ImportError(`${filePath} contains a broken relative link: ${target}`);
			}
		}
	}
}

function validateGraph(skillRoots) {
	const seenNames = new Set();
	const rootIds = [];
	const markdownFiles = [];

	for (const skillRoot of skillRoots) {
		const files = collectPortableFiles(skillRoot);
		const rootSkillFile = path.join(skillRoot, "SKILL.md");
		if (!files.includes(rootSkillFile)) {
			throw new ImportError(`draft operating skill is missing a regular root SKILL.md: ${rootSkillFile}`);
		}
		if (files.some((file) => path.basename(file) === "repo-routing-metadata.json")) {
			throw new ImportError(
				`${skillRoot} contains repo-routing-metadata.json; use verify-repo-skill's locked repo import and router rebuild`,
			);
		}
		for (const file of files) {
			if (path.basename(file) === "SKILL.md") validateSkillFile(file, seenNames);
			if (path.extname(file).toLowerCase() === ".md") markdownFiles.push(file);
		}
		rootIds.push(parseFrontmatter(rootSkillFile).frontmatter.name);
	}

	validateMarkdownLinks(skillRoots, markdownFiles);
	return rootIds;
}

function resolveDraftDirs(rawDirs) {
	const draftDirs = rawDirs.map((rawDir) => path.resolve(expandHome(rawDir)));
	for (const draftDir of draftDirs) {
		if (!pathExists(draftDir)) throw new ImportError(`draft operating skill directory does not exist: ${draftDir}`);
	}
	for (let left = 0; left < draftDirs.length; left += 1) {
		for (let right = left + 1; right < draftDirs.length; right += 1) {
			if (isWithin(draftDirs[left], draftDirs[right]) || isWithin(draftDirs[right], draftDirs[left])) {
				throw new ImportError(`draft operating skill roots must not overlap: ${draftDirs[left]} and ${draftDirs[right]}`);
			}
		}
	}
	return draftDirs;
}

function resolveTarget(args) {
	const agentDir = path.resolve(expandHome(args.agentDir));
	if (args.scope === "managed") {
		return { agentDir, skillsRoot: path.join(agentDir, "skills"), projectDir: undefined };
	}

	const projectDir = path.resolve(expandHome(args.projectDir || process.cwd()));
	if (!pathExists(projectDir) || !fs.lstatSync(projectDir).isDirectory()) {
		throw new ImportError(`project directory does not exist or is not a directory: ${projectDir}`);
	}
	return { agentDir, skillsRoot: path.join(projectDir, ".agents", "skills"), projectDir };
}

function readLiveRootRole(target) {
	const skillFile = path.join(target, "SKILL.md");
	if (!pathExists(skillFile) || !fs.lstatSync(skillFile).isFile()) return undefined;
	const metadata = parseFrontmatter(skillFile).frontmatter.metadata;
	return typeof metadata === "object" && metadata !== null && !Array.isArray(metadata)
		? metadata["disco-role"]
		: undefined;
}

function assertRoleCollisionSafety(targets) {
	for (const target of targets) {
		if (pathExists(target) && readLiveRootRole(target) === "meta") {
			throw new ImportError(`refusing to replace meta skill ${target} with an operating skill`);
		}
	}
}

function assertManagedNamespaceSafety(skillsRoot, rootIds) {
	for (let index = 0; index < rootIds.length; index += 1) {
		const rootId = rootIds[index];
		const repoSkillTarget = path.join(skillsRoot, "repo-skills", rootId);
		if (pathExists(repoSkillTarget)) {
			throw new ImportError(
				`managed repo skill with the same id already exists at ${repoSkillTarget}; use the repo workflow or choose a distinct id`,
			);
		}
	}
}

function runUnderLock(argv, agentDir, timeout) {
	const lockScript = withImportLockScript();
	if (!pathExists(lockScript)) throw new ImportError(`shared skill import lock helper not found: ${lockScript}`);
	const command = [
		process.execPath,
		lockScript,
		"--agent-dir",
		agentDir,
		"--timeout",
		String(timeout),
		"--",
		process.execPath,
		SCRIPT_PATH,
		...argv.filter((item) => item !== "--already-locked"),
		"--already-locked",
	];
	const completed = spawnSync(command[0], command.slice(1), { stdio: "inherit" });
	if (completed.error) throw completed.error;
	return completed.status ?? 1;
}

function rollback(targets, backups, installed) {
	const errors = [];
	for (const target of [...installed].reverse()) {
		try {
			fs.rmSync(target, { recursive: true, force: true });
		} catch (error) {
			errors.push(`could not remove partial target ${target}: ${error instanceof Error ? error.message : String(error)}`);
		}
	}
	for (const target of [...targets].reverse()) {
		const backup = backups.get(target);
		if (!backup || !pathExists(backup)) continue;
		try {
			fs.rmSync(target, { recursive: true, force: true });
			fs.renameSync(backup, target);
		} catch (error) {
			errors.push(`could not restore ${target} from ${backup}: ${error instanceof Error ? error.message : String(error)}`);
		}
	}
	return errors;
}

function maybeInjectTestFailure(installedCount) {
	if (process.env.NODE_ENV !== "test") return;
	const failAfter = Number(process.env.DISCO_TEST_FAIL_OPERATING_IMPORT_AFTER);
	if (Number.isInteger(failAfter) && failAfter > 0 && installedCount === failAfter) {
		throw new ImportError(`injected operating-skill import failure after ${installedCount} install(s)`);
	}
}

function importOperatingGraph(args) {
	const { agentDir, skillsRoot, projectDir } = resolveTarget(args);
	const draftDirs = resolveDraftDirs(args.draftDirs);
	for (const draftDir of draftDirs) {
		if (isWithin(skillsRoot, draftDir)) {
			throw new ImportError(`draft operating skills must be staged outside the live skills root: ${skillsRoot}`);
		}
	}

	const rootIds = validateGraph(draftDirs);
	if (!rootIds.every((rootId) => typeof rootId === "string")) {
		throw new ImportError("every draft operating skill root must declare a name");
	}
	if (new Set(rootIds).size !== rootIds.length) {
		throw new ImportError("operating-skill graph contains duplicate root names");
	}

	const targets = rootIds.map((rootId) => path.join(skillsRoot, rootId));
	assertRoleCollisionSafety(targets);
	if (args.scope === "managed") assertManagedNamespaceSafety(skillsRoot, rootIds);
	const conflicts = targets.filter(pathExists);
	if (conflicts.length > 0 && !args.overwrite) {
		throw new ImportError(
			`live target(s) already exist: ${conflicts.join(", ")}. Obtain separate overwrite approval, then rerun with --overwrite`,
		);
	}
	fs.mkdirSync(skillsRoot, { recursive: true });

	const transactionId = `${process.pid}.${Date.now()}.${Math.random().toString(36).slice(2)}`;
	const transactionDir = path.join(skillsRoot, `.operating-skill-import.${transactionId}`);
	const backups = new Map();
	const installed = [];
	let committed = false;

	try {
		fs.mkdirSync(transactionDir);
		const stagedRoots = draftDirs.map((draftDir, index) => {
			const stagedDir = path.join(transactionDir, rootIds[index]);
			fs.cpSync(draftDir, stagedDir, { recursive: true, errorOnExist: true, force: false });
			return stagedDir;
		});
		validateGraph(stagedRoots);

		const lateConflicts = targets.filter(pathExists);
		if (lateConflicts.length > 0 && !args.overwrite) {
			throw new ImportError(
				`live target(s) appeared during import: ${lateConflicts.join(", ")}. Obtain separate overwrite approval, then rerun with --overwrite`,
			);
		}
		assertRoleCollisionSafety(targets);
		if (args.scope === "managed") assertManagedNamespaceSafety(skillsRoot, rootIds);

		for (let index = 0; index < targets.length; index += 1) {
			const target = targets[index];
			if (!pathExists(target)) continue;
			const backup = path.join(skillsRoot, `.operating-skill-backup.${rootIds[index]}.${transactionId}`);
			fs.renameSync(target, backup);
			backups.set(target, backup);
		}

		for (let index = 0; index < targets.length; index += 1) {
			fs.renameSync(stagedRoots[index], targets[index]);
			installed.push(targets[index]);
			maybeInjectTestFailure(installed.length);
		}
		validateGraph(targets);
		committed = true;

		for (const backup of backups.values()) {
			try {
				fs.rmSync(backup, { recursive: true, force: true });
			} catch (error) {
				console.warn(
					`warning: imported graph is valid, but old backup cleanup failed at ${backup}: ${
						error instanceof Error ? error.message : String(error)
					}`,
				);
			}
		}
		console.log(`imported and validated operating-skill graph (scope: ${args.scope})`);
		if (projectDir) console.log(`project: ${projectDir}`);
		for (let index = 0; index < rootIds.length; index += 1) {
			console.log(`- ${rootIds[index]} -> ${targets[index]}`);
		}
		console.log(
			args.scope === "project"
				? "Ensure the project is trusted, then run /researcher to start a new session and use the imported operating skills."
				: "Run /researcher to start a new session and use the imported operating skills.",
		);
		return 0;
	} catch (error) {
		if (committed) throw error;
		const rollbackErrors = rollback(targets, backups, installed);
		if (rollbackErrors.length > 0) {
			throw new ImportError(
				`${error instanceof Error ? error.message : String(error)}; rollback failed:\n${rollbackErrors.join("\n")}`,
			);
		}
		throw error;
	} finally {
		try {
			fs.rmSync(transactionDir, { recursive: true, force: true });
		} catch (error) {
			console.warn(
				`warning: could not remove operating-skill transaction directory ${transactionDir}: ${
					error instanceof Error ? error.message : String(error)
				}`,
			);
		}
	}
}

function main(argv) {
	let args;
	try {
		args = parseArgs(argv);
	} catch (error) {
		console.error(`import_operating_skill_graph.mjs: ${error instanceof Error ? error.message : String(error)}`);
		return 2;
	}

	let target;
	try {
		target = resolveTarget(args);
	} catch (error) {
		console.error(`import_operating_skill_graph.mjs: ${error instanceof Error ? error.message : String(error)}`);
		return error instanceof ImportError ? 2 : 1;
	}
	if (args.alreadyLocked && !process.env.DISCO_IMPORT_LOCK_PATH) {
		console.error(
			"import_operating_skill_graph.mjs: --already-locked requires DISCO_IMPORT_LOCK_PATH; run through with_import_lock.mjs or omit --already-locked",
		);
		return 2;
	}
	if (!args.alreadyLocked && !process.env.DISCO_IMPORT_LOCK_PATH) {
		try {
			return runUnderLock(argv, target.agentDir, args.timeout);
		} catch (error) {
			console.error(`import_operating_skill_graph.mjs: ${error instanceof Error ? error.message : String(error)}`);
			return 1;
		}
	}

	try {
		return importOperatingGraph(args);
	} catch (error) {
		console.error(`import_operating_skill_graph.mjs: ${error instanceof Error ? error.message : String(error)}`);
		return error instanceof ImportError ? 2 : 1;
	}
}

process.exitCode = main(process.argv.slice(2));
