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

class ImportError extends Error {
	constructor(message) {
		super(message);
		this.name = "ImportError";
	}
}

function defaultAgentDir() {
	return process.env.DISCO_CODING_AGENT_DIR || path.join(os.homedir(), ".disco", "agent");
}

function validatorScript() {
	return path.join(SCRIPT_DIR, "validate_meta_skill.mjs");
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
		if (error?.code === "ENOENT") {
			return false;
		}
		throw error;
	}
}

function isWithin(parent, candidate) {
	const relative = path.relative(parent, candidate);
	return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

function optionValue(argv, index, option) {
	const value = argv[index + 1];
	if (!value || value.startsWith("--")) {
		throw new ImportError(`${option} requires a value`);
	}
	return value;
}

function parseArgs(argv) {
	const args = {
		agentDir: defaultAgentDir(),
		draftDir: undefined,
		overwrite: false,
		alreadyLocked: false,
		timeout: DEFAULT_TIMEOUT_SECONDS,
	};

	for (let index = 0; index < argv.length; index += 1) {
		const item = argv[index];
		if (item === "--agent-dir") {
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
		} else if (args.draftDir) {
			throw new ImportError("provide exactly one draft meta skill directory");
		} else {
			args.draftDir = item;
		}
	}

	if (!args.draftDir) {
		throw new ImportError("provide a draft meta skill directory");
	}
	if (!Number.isFinite(args.timeout) || args.timeout <= 0) {
		throw new ImportError("--timeout must be a positive number");
	}
	return args;
}

function printHelp() {
	console.log(`Usage: node import_meta_skill.mjs [options] DRAFT_META_SKILL_DIR

Options:
  --agent-dir DIR       DisCo agent directory
  --overwrite           Replace an existing same-name skill after explicit approval
  --already-locked      Assert the shared skill import lock is already held
  --timeout SECONDS     Seconds to wait for the shared import lock`);
}

function parseRootFrontmatter(skillFile) {
	const content = fs.readFileSync(skillFile, "utf8");
	const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match?.[1]) {
		throw new ImportError(`${skillFile} is missing YAML frontmatter`);
	}
	let frontmatter;
	try {
		frontmatter = parse(match[1]);
	} catch (error) {
		throw new ImportError(`${skillFile} has invalid YAML frontmatter: ${error instanceof Error ? error.message : String(error)}`);
	}
	if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter)) {
		throw new ImportError(`${skillFile} frontmatter must be a mapping`);
	}
	return frontmatter;
}

function readCandidateId(draftDir) {
	const skillFile = path.join(draftDir, "SKILL.md");
	if (!pathExists(skillFile) || !fs.lstatSync(skillFile).isFile()) {
		throw new ImportError(`draft meta skill is missing a regular root SKILL.md: ${skillFile}`);
	}
	const name = parseRootFrontmatter(skillFile).name;
	if (typeof name !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(name) || name.length > 64) {
		throw new ImportError(`${skillFile} must declare a canonical lowercase-hyphen name`);
	}
	if (name !== path.basename(draftDir)) {
		throw new ImportError(`${skillFile} name must match draft directory basename ${JSON.stringify(path.basename(draftDir))}`);
	}
	if (name === "repo-skills-router") {
		throw new ImportError("repo-skills-router is reserved for the Researcher operating router");
	}
	return name;
}

/**
 * Meta and operating skills share the same managed directory.  An explicit
 * overwrite may update a previous revision of the same meta skill, but it
 * must never silently change a live operating skill's mode ownership.
 */
function assertExistingTargetIsMeta(targetDir) {
	if (!pathExists(targetDir)) return;

	const targetStat = fs.lstatSync(targetDir);
	if (!targetStat.isDirectory() || targetStat.isSymbolicLink()) {
		throw new ImportError(`refusing to replace non-directory live skill target: ${targetDir}`);
	}

	const skillFile = path.join(targetDir, "SKILL.md");
	if (!pathExists(skillFile) || !fs.lstatSync(skillFile).isFile()) {
		throw new ImportError(`refusing to replace live target without a readable SKILL.md: ${targetDir}`);
	}

	const frontmatter = parseRootFrontmatter(skillFile);
	const metadata = frontmatter.metadata;
	const role =
		typeof metadata === "object" && metadata !== null && !Array.isArray(metadata)
			? metadata["disco-role"]
			: undefined;
	if (role !== "meta") {
		throw new ImportError(`refusing to replace non-meta skill target ${targetDir}; existing metadata.disco-role is ${JSON.stringify(role)}`);
	}
}

function assertPortableTree(root) {
	const stat = fs.lstatSync(root);
	if (!stat.isDirectory() || stat.isSymbolicLink()) {
		throw new ImportError(`draft meta skill must be a real directory: ${root}`);
	}
	for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
		const entryPath = path.join(root, entry.name);
		if (entry.isSymbolicLink()) {
			throw new ImportError(`draft meta skill contains a symbolic link: ${entryPath}`);
		}
		if (entry.isDirectory()) {
			assertPortableTree(entryPath);
		} else if (!entry.isFile()) {
			throw new ImportError(`draft meta skill contains a non-regular file: ${entryPath}`);
		}
	}
}

function validateMetaSkill(skillDir, label) {
	const validator = validatorScript();
	if (!pathExists(validator)) {
		throw new ImportError(`meta skill validator not found: ${validator}`);
	}
	const result = spawnSync(process.execPath, [validator, skillDir], { encoding: "utf8" });
	if (result.error) {
		throw result.error;
	}
	if (result.status !== 0) {
		const output = [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
		throw new ImportError(`${label} validation failed${output ? `:\n${output}` : ""}`);
	}
}

function runUnderLock(argv, agentDir, timeout) {
	const lockScript = withImportLockScript();
	if (!pathExists(lockScript)) {
		throw new ImportError(`shared skill import lock helper not found: ${lockScript}`);
	}
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
	if (completed.error) {
		throw completed.error;
	}
	return completed.status ?? 1;
}

function importMetaSkill(args) {
	const agentDir = path.resolve(expandHome(args.agentDir));
	const skillsRoot = path.join(agentDir, "skills");
	const draftDir = path.resolve(expandHome(args.draftDir));
	if (!pathExists(draftDir)) {
		throw new ImportError(`draft meta skill directory does not exist: ${draftDir}`);
	}
	if (isWithin(skillsRoot, draftDir)) {
		throw new ImportError(`draft meta skill must be staged outside the live skills root: ${skillsRoot}`);
	}

	assertPortableTree(draftDir);
	validateMetaSkill(draftDir, "draft meta skill");
	const skillId = readCandidateId(draftDir);
	const targetDir = path.join(skillsRoot, skillId);
	fs.mkdirSync(skillsRoot, { recursive: true });

	if (pathExists(targetDir) && !args.overwrite) {
		throw new ImportError(
			`live target already exists: ${targetDir}. Obtain separate overwrite approval, then rerun with --overwrite`,
		);
	}
	if (pathExists(targetDir)) {
		assertExistingTargetIsMeta(targetDir);
	}

	const transactionId = `${process.pid}.${Date.now()}.${Math.random().toString(36).slice(2)}`;
	const transactionDir = path.join(skillsRoot, `.meta-skill-import.${transactionId}`);
	const stagedDir = path.join(transactionDir, skillId);
	const backupDir = path.join(skillsRoot, `.meta-skill-backup.${skillId}.${transactionId}`);
	let backupActive = false;

	try {
		fs.mkdirSync(transactionDir);
		fs.cpSync(draftDir, stagedDir, { recursive: true, errorOnExist: true, force: false });
		assertPortableTree(stagedDir);
		validateMetaSkill(stagedDir, "staged meta skill");

		const targetExists = pathExists(targetDir);
		if (targetExists && !args.overwrite) {
			throw new ImportError(
				`live target appeared during import: ${targetDir}. Obtain separate overwrite approval, then rerun with --overwrite`,
			);
		}
		if (targetExists) {
			assertExistingTargetIsMeta(targetDir);
		}
		if (targetExists) {
			fs.renameSync(targetDir, backupDir);
			backupActive = true;
		}

		try {
			fs.renameSync(stagedDir, targetDir);
			validateMetaSkill(targetDir, "installed meta skill");
		} catch (error) {
			fs.rmSync(targetDir, { recursive: true, force: true });
			if (backupActive) {
				fs.renameSync(backupDir, targetDir);
				backupActive = false;
			}
			throw error;
		}

		if (backupActive) {
			fs.rmSync(backupDir, { recursive: true, force: true });
			backupActive = false;
		}
		console.log(`imported and validated meta skill ${skillId} at ${targetDir}`);
		console.log(`Run /reload, then invoke /skill:${skillId}.`);
		return 0;
	} catch (error) {
		if (backupActive && !pathExists(targetDir)) {
			try {
				fs.renameSync(backupDir, targetDir);
				backupActive = false;
			} catch (rollbackError) {
				throw new ImportError(
					`${error instanceof Error ? error.message : String(error)}; rollback failed: ${
						rollbackError instanceof Error ? rollbackError.message : String(rollbackError)
					}. The previous target remains at ${backupDir}`,
				);
			}
		}
		throw error;
	} finally {
		fs.rmSync(transactionDir, { recursive: true, force: true });
	}
}

function main(argv) {
	let args;
	try {
		args = parseArgs(argv);
	} catch (error) {
		console.error(`import_meta_skill.mjs: ${error instanceof Error ? error.message : String(error)}`);
		return 2;
	}

	const agentDir = path.resolve(expandHome(args.agentDir));
	if (args.alreadyLocked && !process.env.DISCO_IMPORT_LOCK_PATH) {
		console.error(
			"import_meta_skill.mjs: --already-locked requires DISCO_IMPORT_LOCK_PATH; run through with_import_lock.mjs or omit --already-locked",
		);
		return 2;
	}
	if (!args.alreadyLocked && !process.env.DISCO_IMPORT_LOCK_PATH) {
		try {
			return runUnderLock(argv, agentDir, args.timeout);
		} catch (error) {
			console.error(`import_meta_skill.mjs: ${error instanceof Error ? error.message : String(error)}`);
			return 1;
		}
	}

	try {
		return importMetaSkill(args);
	} catch (error) {
		console.error(`import_meta_skill.mjs: ${error instanceof Error ? error.message : String(error)}`);
		return error instanceof ImportError ? 2 : 1;
	}
}

process.exitCode = main(process.argv.slice(2));
