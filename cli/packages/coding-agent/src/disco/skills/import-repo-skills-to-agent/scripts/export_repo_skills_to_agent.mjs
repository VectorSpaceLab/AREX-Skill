#!/usr/bin/env node

/**
 * Export DisCo-managed repository skills to another agent's repository-skill
 * collection. The source is read-only; the target is staged, validated, and
 * swapped transactionally.
 */

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";
import { inspectRepoSkillLicenses } from "../../verify-repo-skill/scripts/license-validation.mjs";

const ROUTER_ID = "repo-skills-router";
const ROUTING_METADATA = path.join("references", "repo-routing-metadata.json");
const TAXONOMY_PATH = path.join("references", "index", "taxonomy.json");
const REPOSITORIES_PATH = path.join("references", "index", "repositories.jsonl");
const ASSIGNMENTS_PATH = path.join("references", "index", "assignments.jsonl");
const REPOSITORY_INDEX_PATH = "repository-index.jsonl";
const TRANSACTION_PREFIX = ".repo-skills-export-";
const CANONICAL_SKILL_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const REPO_ID = /^[^/\s]+\/[^/\s]+$/;
const DIGEST = /^sha256:[0-9a-f]{64}$/i;
const RAW_SHA256 = /^[0-9a-f]{64}$/i;
const SCRIPT_PATH = fileURLToPath(import.meta.url);
const SCRIPT_DIR = path.dirname(SCRIPT_PATH);
const BUNDLED_SKILLS_DIR = path.resolve(SCRIPT_DIR, "../..");
const ROUTER_TEMPLATE_DIR = path.join(BUNDLED_SKILLS_DIR, "repo-skills-router");
const ROUTER_UPDATER = path.join(
	BUNDLED_SKILLS_DIR,
	"verify-repo-skill",
	"scripts",
	"update_repo_skills_router.mjs",
);
const CODEX_POLICY = path.join(SCRIPT_DIR, "apply_codex_openai_policy.py");

const REPOSITORY_INDEX_FIELDS = new Set([
	"schema_version",
	"repo_id",
	"legacy_repo_id",
	"repo_name",
	"skill_id",
	"source_url",
	"source_commit",
	"source_skill_root",
	"target_skill_root",
	"aliases",
	"description",
]);
const ASSIGNMENT_INDEX_FIELDS = new Set([
	"repo_id",
	"legacy_repo_id",
	"skill_id",
	"area",
	"family",
	"confidence",
]);
const TRANSACTION_PHASES = new Set([
	"staging",
	"validated",
	"repo_backup_pending",
	"repo_backed_up",
	"repo_install_pending",
	"repo_installed",
	"router_backup_pending",
	"router_backed_up",
	"router_install_pending",
	"router_installed",
	"live_validated",
	"committed",
	"rolled_back",
]);
const MUTATION_PHASES = new Set([
	"repo_backup_pending",
	"repo_backed_up",
	"repo_install_pending",
	"repo_installed",
	"router_backup_pending",
	"router_backed_up",
	"router_install_pending",
	"router_installed",
	"live_validated",
]);

class ExportError extends Error {
	constructor(message) {
		super(message);
		this.name = "ExportError";
	}
}

function defaultAgentDir() {
	return process.env.DISCO_CODING_AGENT_DIR || path.join(os.homedir(), ".disco", "agent");
}

function expandHome(value) {
	return value.replace(/^~(?=$|[\\/])/, os.homedir());
}

function optionValue(argv, index, option) {
	const value = argv[index + 1];
	if (!value || value.startsWith("--")) throw new ExportError(`${option} requires a value`);
	return value;
}

function addIds(target, value) {
	for (const id of String(value).split(",")) {
		const trimmed = id.trim();
		if (trimmed) target.push(trimmed);
	}
}

function parseArgs(argv) {
	const args = {
		sourceLibraryRoot: undefined,
		sourceAgentDir: undefined,
		target: undefined,
		targetKind: undefined,
		targetSkillsRoot: undefined,
		targetAgentDir: undefined,
		targetAgent: undefined,
		includeSkillIds: [],
		overwriteSkillIds: [],
		routerVisibility: undefined,
		resumeTransaction: undefined,
		explicit: new Set(),
	};
	for (let index = 0; index < argv.length; index += 1) {
		const item = argv[index];
		if (item === "--source-library-root") {
			args.sourceLibraryRoot = optionValue(argv, index, item);
			args.explicit.add("source");
			index += 1;
		} else if (item === "--source-agent-dir") {
			args.sourceAgentDir = optionValue(argv, index, item);
			args.explicit.add("source");
			index += 1;
		} else if (item === "--target") {
			args.target = optionValue(argv, index, item);
			args.explicit.add("target");
			index += 1;
		} else if (item === "--target-kind") {
			args.targetKind = optionValue(argv, index, item);
			args.explicit.add("targetKind");
			index += 1;
		} else if (item === "--target-skills-root") {
			args.targetSkillsRoot = optionValue(argv, index, item);
			args.explicit.add("target");
			index += 1;
		} else if (item === "--target-agent-dir") {
			args.targetAgentDir = optionValue(argv, index, item);
			args.explicit.add("target");
			index += 1;
		} else if (item === "--target-agent") {
			args.targetAgent = optionValue(argv, index, item);
			args.explicit.add("targetAgent");
			index += 1;
		} else if (item === "--include-skill") {
			addIds(args.includeSkillIds, optionValue(argv, index, item));
			args.explicit.add("includeSkillIds");
			index += 1;
		} else if (item === "--overwrite-skill") {
			addIds(args.overwriteSkillIds, optionValue(argv, index, item));
			args.explicit.add("overwriteSkillIds");
			index += 1;
		} else if (item === "--router-visibility") {
			args.routerVisibility = optionValue(argv, index, item);
			args.explicit.add("routerVisibility");
			index += 1;
		} else if (item === "--resume") {
			args.resumeTransaction = optionValue(argv, index, item);
			index += 1;
		} else if (item === "-h" || item === "--help") {
			printHelp();
			process.exit(0);
		} else {
			throw new ExportError(`unknown argument: ${item}`);
		}
	}
	if (args.sourceLibraryRoot && args.sourceAgentDir) {
		throw new ExportError("use either --source-library-root or --source-agent-dir, not both");
	}
	const targetSelectors = [args.target, args.targetSkillsRoot, args.targetAgentDir].filter(Boolean);
	if (targetSelectors.length > 1 || (!args.resumeTransaction && targetSelectors.length !== 1)) {
		throw new ExportError(args.resumeTransaction
			? "provide at most one of --target, --target-skills-root, or --target-agent-dir with --resume"
			: "provide exactly one of --target, --target-skills-root, or --target-agent-dir");
	}
	if (args.targetKind !== undefined && !["auto", "skills-root", "agent-root"].includes(args.targetKind)) {
		throw new ExportError("--target-kind must be auto, skills-root, or agent-root");
	}
	if (args.targetKind !== undefined && !args.target) {
		throw new ExportError("--target-kind is valid only with --target");
	}
	if (args.targetAgent !== undefined && !["codex", "agent-neutral"].includes(args.targetAgent)) {
		throw new ExportError("--target-agent must be codex or agent-neutral");
	}
	if (args.routerVisibility !== undefined && !["preserve", "enabled", "disabled"].includes(args.routerVisibility)) {
		throw new ExportError("--router-visibility must be preserve, enabled, or disabled");
	}
	args.includeSkillIds = [...new Set(args.includeSkillIds)].sort();
	args.overwriteSkillIds = [...new Set(args.overwriteSkillIds)].sort();
	if (!args.resumeTransaction) {
		args.targetKind ??= "auto";
		args.targetAgent ??= "agent-neutral";
		args.routerVisibility ??= "preserve";
	}
	return args;
}

function printHelp() {
	console.log(`Usage: node export_repo_skills_to_agent.mjs [options]

Options:
  --source-library-root DIR  Source root containing repo-skills/ and the router
  --source-agent-dir DIR     Source DisCo agent directory
  --target DIR               Target skills root or agent root; use --target-kind when ambiguous
  --target-kind KIND         auto, skills-root, or agent-root (default: auto)
  --target-skills-root DIR   Target skills root, e.g. ~/.agents/skills
  --target-agent-dir DIR     Target agent root, e.g. ~/.agents
  --target-agent KIND        codex or agent-neutral (default: agent-neutral)
  --include-skill ID         Export only this skill; repeat or comma-separate
  --overwrite-skill ID       Explicitly approved target skill replacement
  --router-visibility MODE   preserve, enabled, or disabled (default: preserve)
  --resume DIR               Resume/retry the persisted transaction at DIR`);
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

function isRegularFile(filePath) {
	if (!pathExists(filePath)) return false;
	const stat = fs.lstatSync(filePath);
	return stat.isFile() && !stat.isSymbolicLink();
}

function isRealDirectory(directory) {
	if (!pathExists(directory)) return false;
	const stat = fs.lstatSync(directory);
	return stat.isDirectory() && !stat.isSymbolicLink();
}

function assertRealDirectory(directory, label) {
	if (!isRealDirectory(directory)) throw new ExportError(`${label} is not a real directory: ${directory}`);
}

function assertNoSymlinks(root, label) {
	if (!pathExists(root)) return;
	const stat = fs.lstatSync(root);
	if (stat.isSymbolicLink()) throw new ExportError(`${label} contains a symbolic link: ${root}`);
	if (stat.isDirectory()) {
		for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
			assertNoSymlinks(path.join(root, entry.name), label);
		}
	}
}

function assertPathHasNoSymlinkComponents(targetPath, label) {
	let existing = path.resolve(targetPath);
	while (!pathExists(existing)) {
		const parent = path.dirname(existing);
		if (parent === existing) break;
		existing = parent;
	}
	if (!pathExists(existing)) throw new ExportError(`${label} has no inspectable filesystem ancestor: ${targetPath}`);
	const resolved = fs.realpathSync.native(existing);
	if (resolved !== path.resolve(existing)) {
		throw new ExportError(`${label} traverses a symbolic link: ${targetPath}`);
	}
}

function readText(filePath) {
	return fs.readFileSync(filePath, "utf8");
}

function writeText(filePath, value) {
	fs.mkdirSync(path.dirname(filePath), { recursive: true });
	fs.writeFileSync(filePath, value, "utf8");
}

function writeJson(filePath, value) {
	const temporary = `${filePath}.tmp-${process.pid}-${Math.random().toString(36).slice(2)}`;
	fs.mkdirSync(path.dirname(filePath), { recursive: true });
	fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, "utf8");
	fs.renameSync(temporary, filePath);
}

function readJson(filePath) {
	try {
		return JSON.parse(readText(filePath));
	} catch (error) {
		throw new ExportError(`${filePath} is invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
	}
}

function readJsonLines(filePath) {
	if (!isRegularFile(filePath)) return [];
	return readText(filePath).split(/\r?\n/).filter(Boolean).map((line, index) => {
		try {
			const value = JSON.parse(line);
			if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("record must be an object");
			return value;
		} catch (error) {
			throw new ExportError(`${filePath}:${index + 1} is invalid JSON: ${error instanceof Error ? error.message : String(error)}`);
		}
	});
}

function writeJsonLines(filePath, records) {
	writeText(filePath, records.map((record) => JSON.stringify(record)).join("\n") + (records.length ? "\n" : ""));
}

function hashFile(filePath) {
	if (!isRegularFile(filePath)) throw new ExportError(`required file is missing: ${filePath}`);
	return createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function digestTreeState(root) {
	if (!pathExists(root)) return "absent";
	assertRealDirectory(root, "tree snapshot root");
	const hash = createHash("sha256");
	hash.update("present\0");
	const visit = (directory) => {
		for (const entry of fs.readdirSync(directory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
			const entryPath = path.join(directory, entry.name);
			const relativePath = path.relative(root, entryPath).split(path.sep).join("/");
			if (entry.isSymbolicLink()) throw new ExportError(`tree snapshot contains a symbolic link: ${entryPath}`);
			if (entry.isDirectory()) {
				hash.update(`dir\0${relativePath}\0`);
				visit(entryPath);
			} else if (entry.isFile()) {
				const content = fs.readFileSync(entryPath);
				hash.update(`file\0${relativePath}\0${content.byteLength}\0`);
				hash.update(content);
				hash.update("\0");
			} else {
				throw new ExportError(`tree snapshot contains a non-regular file: ${entryPath}`);
			}
		}
	};
	visit(root);
	return `sha256:${hash.digest("hex")}`;
}

function digestSelection(repositories, assignments, taxonomyHash) {
	const hash = createHash("sha256");
	hash.update(`${taxonomyHash}\0`);
	for (const record of repositories) hash.update(`${JSON.stringify(record)}\n`);
	hash.update("\0");
	for (const record of assignments) hash.update(`${JSON.stringify(record)}\n`);
	return `sha256:${hash.digest("hex")}`;
}

function digestSelectedSourceSkills(sourceLibraryRoot, selectedIds, skillDirs) {
	const hash = createHash("sha256");
	hash.update("selected-source-skills\0");
	for (const skillId of [...selectedIds].sort()) {
		const skillDir = skillDirs?.get(skillId) || path.join(sourceLibraryRoot, "repo-skills", skillId);
		if (!isRealDirectory(skillDir)) throw new ExportError(`selected source skill is missing: ${skillId}`);
		hash.update(`skill\0${skillId}\0${digestTreeState(skillDir)}\0`);
	}
	return `sha256:${hash.digest("hex")}`;
}

function pathsOverlap(left, right) {
	const resolvedLeft = path.resolve(left);
	const resolvedRight = path.resolve(right);
	return resolvedLeft === resolvedRight ||
		resolvedLeft.startsWith(`${resolvedRight}${path.sep}`) ||
		resolvedRight.startsWith(`${resolvedLeft}${path.sep}`);
}

function parseFrontmatter(filePath) {
	const match = readText(filePath).match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match) throw new ExportError(`${filePath} is missing YAML frontmatter`);
	let value;
	try {
		value = parse(match[1]);
	} catch (error) {
		throw new ExportError(`${filePath} has invalid YAML frontmatter: ${error instanceof Error ? error.message : String(error)}`);
	}
	if (!value || typeof value !== "object" || Array.isArray(value)) throw new ExportError(`${filePath} frontmatter must be a mapping`);
	return value;
}

function validateSkillIdentity(skillDir) {
	const skillFile = path.join(skillDir, "SKILL.md");
	if (!isRegularFile(skillFile)) throw new ExportError(`repository skill is missing ${skillFile}`);
	const frontmatter = parseFrontmatter(skillFile);
	if (typeof frontmatter.name !== "string" || !CANONICAL_SKILL_ID.test(frontmatter.name) || frontmatter.name.length > 64) {
		throw new ExportError(`${skillFile} must declare a canonical lowercase-hyphen name`);
	}
	if (frontmatter.name !== path.basename(skillDir)) throw new ExportError(`${skillFile} name must match directory basename`);
	if (typeof frontmatter.description !== "string" || !frontmatter.description.trim()) {
		throw new ExportError(`${skillFile} must declare a non-empty description`);
	}
	const license = inspectRepoSkillLicenses(skillDir);
	if (!license.valid) {
		throw new ExportError(`repository skill license gate failed for ${skillDir}:\n${license.errors.map((error) => `- ${error}`).join("\n")}`);
	}
	return frontmatter.name;
}

function listSkillDirs(repoSkillsRoot) {
	if (!isRealDirectory(repoSkillsRoot)) return new Map();
	const result = new Map();
	for (const entry of fs.readdirSync(repoSkillsRoot, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
		if (!entry.isDirectory() || entry.isSymbolicLink()) continue;
		const skillDir = path.join(repoSkillsRoot, entry.name);
		if (!isRegularFile(path.join(skillDir, "SKILL.md"))) continue;
		const skillId = validateSkillIdentity(skillDir);
		if (skillId === ROUTER_ID || skillId === "repo-skills") continue;
		result.set(skillId, skillDir);
	}
	return result;
}

function collectFiles(root, result = []) {
	if (!pathExists(root)) return result;
	const stat = fs.lstatSync(root);
	if (stat.isSymbolicLink()) throw new ExportError(`repository skill contains a symbolic link: ${root}`);
	if (stat.isDirectory()) {
		for (const entry of fs.readdirSync(root, { withFileTypes: true })) collectFiles(path.join(root, entry.name), result);
	} else if (stat.isFile()) {
		result.push(root);
	} else {
		throw new ExportError(`repository skill contains a non-regular file: ${root}`);
	}
	return result;
}

function hasCodexPolicy(root) {
	return collectFiles(root).some((filePath) => {
		const relative = path.relative(root, filePath).split(path.sep).join("/");
		return relative === "agents/openai.yaml" || relative.endsWith("/agents/openai.yaml");
	});
}

function copyDirectory(source, destination) {
	assertRealDirectory(source, "source directory");
	assertNoSymlinks(source, source);
	fs.mkdirSync(path.dirname(destination), { recursive: true });
	fs.cpSync(source, destination, { recursive: true, force: true, errorOnExist: false });
	assertNoSymlinks(destination, destination);
}

function removePath(target) {
	if (pathExists(target)) fs.rmSync(target, { recursive: true, force: true });
}

function shortOutput(value) {
	const text = String(value || "").trim();
	return text.length > 4_000 ? `${text.slice(0, 4_000)}\n...` : text;
}

function runRouterUpdater(libraryRoot, outputRouterDir, includeSkillIds, visibility) {
	const args = [
		ROUTER_UPDATER,
		"--library-root",
		libraryRoot,
		"--template-dir",
		ROUTER_TEMPLATE_DIR,
		"--output-router-dir",
		outputRouterDir,
		"--router-visibility",
		visibility,
	];
	for (const skillId of includeSkillIds) args.push("--include-skill", skillId);
	const result = spawnSync(process.execPath, args, { encoding: "utf8", env: process.env });
	if (result.error) throw new ExportError(`router updater could not start: ${result.error.message}`);
	if (result.status !== 0) {
		throw new ExportError(`router updater failed with exit code ${result.status ?? 1}: ${shortOutput(result.stderr || result.stdout)}`);
	}
}

function resolveSourceLibraryRoot(args) {
	const source = args.sourceLibraryRoot
		? path.resolve(expandHome(args.sourceLibraryRoot))
		: path.join(path.resolve(expandHome(args.sourceAgentDir || defaultAgentDir())), "skills", "repositories");
	assertPathHasNoSymlinkComponents(source, "source library root");
	assertRealDirectory(source, "source library root");
	assertRealDirectory(path.join(source, "repo-skills"), "source repo-skills collection");
	assertRealDirectory(path.join(source, ROUTER_ID), "source repo-skills-router");
	assertNoSymlinks(source, "source library");
	return source;
}

function resolveTargetSkillsRoot(args) {
	let targetSkillsRoot;
	if (args.targetSkillsRoot) {
		targetSkillsRoot = path.resolve(expandHome(args.targetSkillsRoot));
	} else if (args.targetAgentDir) {
		targetSkillsRoot = path.join(path.resolve(expandHome(args.targetAgentDir)), "skills");
	} else {
		const target = path.resolve(expandHome(args.target));
		if (args.targetKind === "skills-root" || path.basename(target) === "skills") {
			targetSkillsRoot = target;
		} else if (args.targetKind === "agent-root" || [".agents", ".claude", ".codex"].includes(path.basename(target)) || pathExists(path.join(target, "skills"))) {
			targetSkillsRoot = path.join(target, "skills");
		} else {
			throw new ExportError(`cannot infer target kind for ${target}; pass --target-kind skills-root or agent-root`);
		}
	}
	if (targetSkillsRoot === path.parse(targetSkillsRoot).root) {
		throw new ExportError("target skills root cannot be the filesystem root");
	}
	return targetSkillsRoot;
}

function resolveVisibility(requested, targetRouterDir) {
	if (requested === "enabled" || requested === "disabled") return requested;
	if (!isRegularFile(path.join(targetRouterDir, "SKILL.md"))) return "enabled";
	const frontmatter = parseFrontmatter(path.join(targetRouterDir, "SKILL.md"));
	return frontmatter["disable-model-invocation"] === true ? "disabled" : "enabled";
}

function readRouterRecords(routerDir) {
	return {
		repositories: readJsonLines(path.join(routerDir, REPOSITORIES_PATH)),
		assignments: readJsonLines(path.join(routerDir, ASSIGNMENTS_PATH)),
	};
}

function validateRepositoryRecords(records, label) {
	const skillIds = new Set();
	const repoIds = new Set();
	for (const [index, record] of records.entries()) {
		const unknown = Object.keys(record).find((key) => !REPOSITORY_INDEX_FIELDS.has(key));
		if (unknown || record.schema_version !== 1 || typeof record.skill_id !== "string" || !CANONICAL_SKILL_ID.test(record.skill_id) ||
			typeof record.repo_id !== "string" || !REPO_ID.test(record.repo_id) || record.repo_name !== record.repo_id.split("/").at(-1) ||
			(record.source_commit !== null && (typeof record.source_commit !== "string" || !/^[0-9a-f]{40}$/i.test(record.source_commit))) ||
			(record.source_skill_root !== null && (typeof record.source_skill_root !== "string" || path.isAbsolute(record.source_skill_root))) ||
			record.target_skill_root !== `repo-skills/${record.skill_id}` || !Array.isArray(record.aliases) ||
			record.aliases.some((alias) => typeof alias !== "string") || typeof record.description !== "string" || !record.description.trim() ||
			(record.legacy_repo_id !== null && (typeof record.legacy_repo_id !== "string" || !record.legacy_repo_id.trim()))) {
			throw new ExportError(`${label} repository record ${index + 1} is invalid${unknown ? ` (unknown field ${unknown})` : ""}`);
		}
		if (skillIds.has(record.skill_id)) throw new ExportError(`${label} contains duplicate skill_id ${record.skill_id}`);
		if (repoIds.has(record.repo_id.toLowerCase())) throw new ExportError(`${label} contains duplicate repo_id ${record.repo_id}`);
		skillIds.add(record.skill_id);
		repoIds.add(record.repo_id.toLowerCase());
	}
}

function validateAssignmentRecords(records, repositoryRecords, label) {
	const repositories = new Map(repositoryRecords.map((record) => [record.skill_id, record]));
	const seen = new Set();
	for (const [index, record] of records.entries()) {
		const unknown = Object.keys(record).find((key) => !ASSIGNMENT_INDEX_FIELDS.has(key));
		const key = `${record.repo_id}\0${record.area}\0${record.family}`;
		if (unknown || typeof record.skill_id !== "string" || !repositories.has(record.skill_id) ||
			record.repo_id !== repositories.get(record.skill_id).repo_id || typeof record.area !== "string" ||
			typeof record.family !== "string" || !["high", "medium", "low"].includes(record.confidence)) {
			throw new ExportError(`${label} assignment record ${index + 1} is invalid${unknown ? ` (unknown field ${unknown})` : ""}`);
		}
		if (seen.has(key)) throw new ExportError(`${label} contains duplicate assignment ${key.replaceAll("\0", " -> ")}`);
		seen.add(key);
	}
}

function compareJsonLines(left, right) {
	return left.length === right.length && left.every((record, index) => JSON.stringify(record) === JSON.stringify(right[index]));
}

function validateRouterTaxonomy(routerDir, taxonomyHash, label) {
	const taxonomyFile = path.join(routerDir, TAXONOMY_PATH);
	if (!isRegularFile(taxonomyFile)) throw new ExportError(`${label} is missing ${TAXONOMY_PATH}`);
	if (hashFile(taxonomyFile) !== taxonomyHash) throw new ExportError(`${label} uses a different taxonomy hash`);
}

function validateTargetCollection(targetLibraryRoot, sourceTaxonomyHash, transactionDir, { requireRootIndex = false } = {}) {
	assertPathHasNoSymlinkComponents(targetLibraryRoot, "target repository collection");
	if (pathExists(targetLibraryRoot)) assertNoSymlinks(targetLibraryRoot, "target repository collection");
	const targetRepoSkills = path.join(targetLibraryRoot, "repo-skills");
	const targetRouter = path.join(targetLibraryRoot, ROUTER_ID);
	const targetSkillDirs = listSkillDirs(targetRepoSkills);
	if (targetSkillDirs.size === 0 && !pathExists(targetRouter)) {
		return { skillDirs: targetSkillDirs, repositories: [], assignments: [], visibility: "enabled" };
	}
	if (targetSkillDirs.size > 0 && !isRealDirectory(targetRouter)) {
		throw new ExportError(`existing target repository skills have no usable ${ROUTER_ID}; refusing an unsafe merge`);
	}
	if (!isRealDirectory(targetRouter)) {
		return { skillDirs: targetSkillDirs, repositories: [], assignments: [], visibility: "enabled" };
	}
	assertNoSymlinks(targetRouter, "target router");
	validateRouterTaxonomy(targetRouter, sourceTaxonomyHash, "target router");
	const targetIndexes = readRouterRecords(targetRouter);
	validateRepositoryRecords(targetIndexes.repositories, "target router");
	validateAssignmentRecords(targetIndexes.assignments, targetIndexes.repositories, "target router");
	for (const skillId of targetSkillDirs.keys()) {
		if (!targetIndexes.repositories.some((record) => record.skill_id === skillId)) {
			throw new ExportError(`target router does not index existing repository skill ${skillId}`);
		}
	}
	for (const record of targetIndexes.repositories) {
		if (!targetSkillDirs.has(record.skill_id)) throw new ExportError(`target router indexes missing skill ${record.skill_id}`);
	}
	const rootIndexPath = path.join(targetRepoSkills, REPOSITORY_INDEX_PATH);
	if (isRegularFile(rootIndexPath)) {
		const rootRecords = readJsonLines(rootIndexPath);
		validateRepositoryRecords(rootRecords, "target root repository index");
		if (!compareJsonLines(rootRecords, targetIndexes.repositories)) {
			throw new ExportError("target root repository-index.jsonl differs from the target router repository index");
		}
	} else if (requireRootIndex) {
		throw new ExportError("target repo-skills collection is missing repository-index.jsonl");
	}
	const outputRouter = path.join(transactionDir, "target-router-validation");
	removePath(outputRouter);
	runRouterUpdater(targetLibraryRoot, outputRouter, [], "enabled");
	const regenerated = readRouterRecords(outputRouter);
	validateRepositoryRecords(regenerated.repositories, "validated target router");
	validateAssignmentRecords(regenerated.assignments, regenerated.repositories, "validated target router");
	if (regenerated.repositories.length !== targetSkillDirs.size) {
		throw new ExportError("target router validation did not cover every existing repository skill");
	}
	if (!compareJsonLines(targetIndexes.repositories, regenerated.repositories) ||
		!compareJsonLines(targetIndexes.assignments, regenerated.assignments)) {
		throw new ExportError("target router indexes differ from a deterministic regeneration");
	}
	return {
		skillDirs: targetSkillDirs,
		repositories: regenerated.repositories,
		assignments: regenerated.assignments,
		visibility: resolveVisibility("preserve", targetRouter),
	};
}

function validateSourceSelection(sourceLibraryRoot, includeSkillIds, transactionDir, taxonomyHash) {
	assertRealDirectory(sourceLibraryRoot, "source library root");
	assertRealDirectory(path.join(sourceLibraryRoot, "repo-skills"), "source repo-skills collection");
	assertRealDirectory(path.join(sourceLibraryRoot, ROUTER_ID), "source repo-skills-router");
	assertNoSymlinks(sourceLibraryRoot, "source library");
	const sourceRepoSkills = path.join(sourceLibraryRoot, "repo-skills");
	const available = listSkillDirs(sourceRepoSkills);
	const selectedIds = includeSkillIds.length ? includeSkillIds : [...available.keys()].sort();
	const missing = selectedIds.filter((skillId) => !available.has(skillId));
	if (missing.length) throw new ExportError(`source selection contains missing skill ids: ${missing.join(", ")}`);
	for (const skillId of selectedIds) {
		const skillDir = available.get(skillId);
		if (hasCodexPolicy(skillDir)) throw new ExportError(`source skill ${skillId} contains target-only agents/openai.yaml`);
		if (!isRegularFile(path.join(skillDir, ROUTING_METADATA))) {
			throw new ExportError(`source skill ${skillId} is missing ${ROUTING_METADATA}`);
		}
	}
	const outputRouter = path.join(transactionDir, "source-router");
	removePath(outputRouter);
	runRouterUpdater(sourceLibraryRoot, outputRouter, selectedIds, "enabled");
	validateRouterTaxonomy(outputRouter, taxonomyHash, "validated source router");
	const records = readRouterRecords(outputRouter);
	validateRepositoryRecords(records.repositories, "validated source router");
	validateAssignmentRecords(records.assignments, records.repositories, "validated source router");
	const actualIds = new Set(records.repositories.map((record) => record.skill_id));
	if (actualIds.size !== selectedIds.length || selectedIds.some((skillId) => !actualIds.has(skillId))) {
		throw new ExportError("validated source router does not exactly cover the selected skills");
	}
	return {
		selectedIds,
		skillDirs: available,
		repositories: records.repositories,
		assignments: records.assignments,
		sourceSkillSnapshotSha256: digestSelectedSourceSkills(sourceLibraryRoot, selectedIds, available),
	};
}

function mergeRecords(target, source, selectedIds) {
	const selected = new Set(selectedIds);
	const targetRepositories = target.repositories.filter((record) => !selected.has(record.skill_id));
	const targetAssignments = target.assignments.filter((record) => !selected.has(record.skill_id));
	const targetByRepoId = new Map(target.repositories.map((record) => [record.repo_id.toLowerCase(), record]));
	for (const record of source.repositories) {
		const collision = targetByRepoId.get(record.repo_id.toLowerCase());
		if (collision && collision.skill_id !== record.skill_id && !selected.has(collision.skill_id)) {
			throw new ExportError(`repository identity collision: ${record.repo_id} is already provided by target skill ${collision.skill_id}`);
		}
	}
	return {
		repositories: [...targetRepositories, ...source.repositories].sort((left, right) => left.repo_id.localeCompare(right.repo_id) || left.skill_id.localeCompare(right.skill_id)),
		assignments: [...targetAssignments, ...source.assignments],
	};
}

function resolveTransactionParent(targetSkillsRoot) {
	const parent = path.dirname(targetSkillsRoot);
	fs.mkdirSync(parent, { recursive: true });
	return parent;
}

function transactionPaths(transactionDir) {
	return {
		manifest: path.join(transactionDir, "manifest.json"),
		stageRoot: path.join(transactionDir, "stage", "repositories"),
		stageRepoSkills: path.join(transactionDir, "stage", "repositories", "repo-skills"),
		stageRouter: path.join(transactionDir, "stage", "repositories", ROUTER_ID),
		backupRepoSkills: path.join(transactionDir, "backup", "repo-skills"),
		backupRouter: path.join(transactionDir, "backup", ROUTER_ID),
	};
}

function makeTransaction(parent, config) {
	const transactionDir = path.join(parent, `${TRANSACTION_PREFIX}${Date.now()}-${process.pid}-${Math.random().toString(36).slice(2, 8)}`);
	fs.mkdirSync(transactionDir, { recursive: true });
	const manifest = {
		schema_version: 1,
		phase: "staging",
		created_at: new Date().toISOString(),
		updated_at: new Date().toISOString(),
		source_library_root: config.sourceLibraryRoot,
		target_skills_root: config.targetSkillsRoot,
		target_library_root: config.targetLibraryRoot,
		target_agent: config.targetAgent,
		include_skill_ids: config.includeSkillIds,
		selected_skill_ids: config.selectedIds,
		overwrite_skill_ids: config.overwriteSkillIds,
		router_visibility: config.routerVisibility,
		target_visibility: config.targetVisibility,
		effective_router_visibility: config.effectiveRouterVisibility,
		taxonomy_sha256: config.taxonomyHash,
		source_selection_sha256: config.sourceSelectionSha256,
		source_skill_snapshot_sha256: config.sourceSkillSnapshotSha256,
		target_snapshot_sha256: config.targetSnapshotSha256,
		final_skill_ids: config.merged.repositories.map((record) => record.skill_id).sort(),
		final_repository_count: config.merged.repositories.length,
		final_assignment_count: config.merged.assignments.length,
		target_skills_root_existed: pathExists(config.targetSkillsRoot),
		target_library_root_existed: pathExists(config.targetLibraryRoot),
		repo_existed: pathExists(path.join(config.targetLibraryRoot, "repo-skills")),
		router_existed: pathExists(path.join(config.targetLibraryRoot, ROUTER_ID)),
	};
	writeJson(transactionPaths(transactionDir).manifest, manifest);
	return { directory: transactionDir, manifest };
}

function updateManifest(transactionDir, manifest, phase) {
	manifest.phase = phase;
	manifest.updated_at = new Date().toISOString();
	writeJson(transactionPaths(transactionDir).manifest, manifest);
}

function findTransactions(parent, targetLibraryRoot) {
	if (!isRealDirectory(parent)) return [];
	return fs.readdirSync(parent, { withFileTypes: true })
		.filter((entry) => entry.isDirectory() && entry.name.startsWith(TRANSACTION_PREFIX))
		.map((entry) => path.join(parent, entry.name))
		.filter((directory) => isRegularFile(transactionPaths(directory).manifest))
		.map((directory) => ({ directory, manifest: readJson(transactionPaths(directory).manifest) }))
		.filter(({ manifest }) => manifest.target_library_root === targetLibraryRoot)
		.sort((left, right) => left.manifest.updated_at.localeCompare(right.manifest.updated_at));
}

function loadTransaction(transactionDirectory) {
	const directory = path.resolve(expandHome(transactionDirectory));
	assertRealDirectory(directory, "export transaction");
	if (!path.basename(directory).startsWith(TRANSACTION_PREFIX)) {
		throw new ExportError(`not a repository-skills export transaction: ${directory}`);
	}
	assertNoSymlinks(directory, "export transaction");
	const manifestFile = transactionPaths(directory).manifest;
	if (!isRegularFile(manifestFile)) throw new ExportError(`export transaction is missing ${manifestFile}`);
	const manifest = readJson(manifestFile);
	if (!manifest || typeof manifest !== "object" || Array.isArray(manifest) ||
		manifest.schema_version !== 1 || !TRANSACTION_PHASES.has(manifest.phase)) {
		throw new ExportError(`export transaction manifest is invalid: ${manifestFile}`);
	}
	for (const field of ["source_library_root", "target_skills_root", "target_library_root"]) {
		if (typeof manifest[field] !== "string" || !manifest[field]) {
			throw new ExportError(`export transaction manifest is missing ${field}`);
		}
		if (!path.isAbsolute(manifest[field]) || path.resolve(manifest[field]) !== manifest[field]) {
			throw new ExportError(`export transaction manifest has an invalid ${field}`);
		}
	}
	if (manifest.target_library_root !== path.join(manifest.target_skills_root, "repositories")) {
		throw new ExportError("export transaction target collection does not match its target skills root");
	}
	if (manifest.target_skills_root === path.parse(manifest.target_skills_root).root) {
		throw new ExportError("export transaction target skills root cannot be the filesystem root");
	}
	if (!new Set(["codex", "agent-neutral"]).has(manifest.target_agent) ||
		!new Set(["preserve", "enabled", "disabled"]).has(manifest.router_visibility) ||
		!new Set(["enabled", "disabled"]).has(manifest.target_visibility) ||
		!new Set(["enabled", "disabled"]).has(manifest.effective_router_visibility)) {
		throw new ExportError("export transaction manifest has invalid target policy fields");
	}
	for (const field of ["include_skill_ids", "selected_skill_ids", "overwrite_skill_ids", "final_skill_ids"]) {
		const value = manifest[field];
		if (!Array.isArray(value) || value.some((skillId) => typeof skillId !== "string" || !CANONICAL_SKILL_ID.test(skillId)) ||
			JSON.stringify(value) !== JSON.stringify([...new Set(value)].sort())) {
			throw new ExportError(`export transaction manifest has an invalid ${field}`);
		}
	}
	if (manifest.overwrite_skill_ids.some((skillId) => !manifest.selected_skill_ids.includes(skillId)) ||
		manifest.selected_skill_ids.some((skillId) => !manifest.final_skill_ids.includes(skillId))) {
		throw new ExportError("export transaction manifest has inconsistent skill selections");
	}
	if (!RAW_SHA256.test(manifest.taxonomy_sha256) || !DIGEST.test(manifest.source_selection_sha256) ||
		(manifest.source_skill_snapshot_sha256 !== undefined && !DIGEST.test(manifest.source_skill_snapshot_sha256)) ||
		!(manifest.target_snapshot_sha256 === "absent" || DIGEST.test(manifest.target_snapshot_sha256))) {
		throw new ExportError("export transaction manifest has invalid fingerprints");
	}
	if (!Number.isInteger(manifest.final_repository_count) || manifest.final_repository_count !== manifest.final_skill_ids.length ||
		!Number.isInteger(manifest.final_assignment_count) || manifest.final_assignment_count < 0) {
		throw new ExportError("export transaction manifest has invalid final counts");
	}
	for (const field of ["target_skills_root_existed", "target_library_root_existed", "repo_existed", "router_existed"]) {
		if (typeof manifest[field] !== "boolean") {
			throw new ExportError(`export transaction manifest has an invalid ${field}`);
		}
	}
	if (path.dirname(directory) !== path.dirname(manifest.target_skills_root)) {
		throw new ExportError("export transaction is not stored beside its recorded target skills root");
	}
	return { directory, manifest };
}

function maybeFailAfter(phase) {
	if (process.env.NODE_ENV === "test" && process.env.DISCO_EXPORT_TEST_FAIL_AFTER === phase) {
		throw new ExportError(`injected export failure after ${phase}`);
	}
}

function maybeFailAt(point) {
	if (process.env.NODE_ENV === "test" && process.env.DISCO_EXPORT_TEST_FAIL_AT === point) {
		throw new ExportError(`injected export failure at ${point}`);
	}
}

function assertResumeMatches(args, manifest) {
	if (args.explicit.has("source")) {
		const sourceLibraryRoot = resolveSourceLibraryRoot(args);
		if (sourceLibraryRoot !== manifest.source_library_root) throw new ExportError("resume source does not match the persisted transaction");
	}
	if (args.explicit.has("target")) {
		const targetSkillsRoot = resolveTargetSkillsRoot(args);
		if (targetSkillsRoot !== manifest.target_skills_root) throw new ExportError("resume target does not match the persisted transaction");
	}
	if (args.explicit.has("targetAgent") && args.targetAgent !== manifest.target_agent) {
		throw new ExportError("resume target agent does not match the persisted transaction");
	}
	if (args.explicit.has("routerVisibility") && args.routerVisibility !== manifest.router_visibility) {
		throw new ExportError("resume router visibility does not match the persisted transaction");
	}
	if (args.explicit.has("includeSkillIds") && JSON.stringify(args.includeSkillIds) !== JSON.stringify(manifest.include_skill_ids || [])) {
		throw new ExportError("resume selection does not match the persisted transaction");
	}
	if (args.explicit.has("overwriteSkillIds") && JSON.stringify(args.overwriteSkillIds) !== JSON.stringify(manifest.overwrite_skill_ids || [])) {
		throw new ExportError("resume overwrite approvals do not match the persisted transaction");
	}
}

function configFromManifest(manifest) {
	return {
		sourceLibraryRoot: manifest.source_library_root,
		targetSkillsRoot: manifest.target_skills_root,
		targetLibraryRoot: manifest.target_library_root,
		targetAgent: manifest.target_agent,
		includeSkillIds: manifest.include_skill_ids || [],
		overwriteSkillIds: manifest.overwrite_skill_ids || [],
		selectedIds: manifest.selected_skill_ids || [],
		targetVisibility: manifest.target_visibility,
		routerVisibility: manifest.router_visibility,
		effectiveRouterVisibility: manifest.effective_router_visibility,
		taxonomyHash: manifest.taxonomy_sha256,
		sourceSelectionSha256: manifest.source_selection_sha256,
		sourceSkillSnapshotSha256: manifest.source_skill_snapshot_sha256 || null,
		targetSnapshotSha256: manifest.target_snapshot_sha256,
	};
}

function assertPersistedSourceUnchanged(config, transactionDir) {
	const source = validateSourceSelection(
		config.sourceLibraryRoot,
		config.includeSkillIds,
		transactionDir,
		config.taxonomyHash,
	);
	if (JSON.stringify(source.selectedIds) !== JSON.stringify(config.selectedIds) ||
		digestSelection(source.repositories, source.assignments, config.taxonomyHash) !== config.sourceSelectionSha256 ||
		(config.sourceSkillSnapshotSha256 && source.sourceSkillSnapshotSha256 !== config.sourceSkillSnapshotSha256)) {
		throw new ExportError("source selection changed after staging; cannot resume this transaction");
	}
}

function validateCodexPolicies(repoSkillsRoot, routerDir, skillIds) {
	for (const skillId of skillIds) {
		const skillDir = path.join(repoSkillsRoot, skillId);
		for (const skillFile of collectFiles(skillDir).filter((filePath) => path.basename(filePath) === "SKILL.md")) {
			const policy = path.join(path.dirname(skillFile), "agents", "openai.yaml");
			if (!isRegularFile(policy) || !readText(policy).includes("allow_implicit_invocation: false")) {
				throw new ExportError(`Codex policy is missing for ${skillFile}`);
			}
		}
	}
	if (hasCodexPolicy(routerDir)) throw new ExportError("router must not receive a Codex implicit-invocation policy");
}

function validatePreparedCollection(collectionRoot, config, transactionDir) {
	const validated = validateTargetCollection(collectionRoot, config.taxonomyHash, transactionDir, { requireRootIndex: true });
	const actualIds = [...validated.skillDirs.keys()].sort();
	const expectedIds = [...(config.finalSkillIds || config.merged?.repositories.map((record) => record.skill_id) || [])].sort();
	if (JSON.stringify(actualIds) !== JSON.stringify(expectedIds)) {
		throw new ExportError("validated target skill inventory differs from the persisted final selection");
	}
	if (config.finalRepositoryCount !== undefined && validated.repositories.length !== config.finalRepositoryCount) {
		throw new ExportError("validated target repository count differs from the persisted transaction");
	}
	if (config.finalAssignmentCount !== undefined && validated.assignments.length !== config.finalAssignmentCount) {
		throw new ExportError("validated target assignment count differs from the persisted transaction");
	}
	if (validated.visibility !== config.effectiveRouterVisibility) {
		throw new ExportError(`target router visibility is ${validated.visibility}; expected ${config.effectiveRouterVisibility}`);
	}
	if (config.targetAgent === "codex") {
		validateCodexPolicies(path.join(collectionRoot, "repo-skills"), path.join(collectionRoot, ROUTER_ID), actualIds);
	} else if (hasCodexPolicy(path.join(collectionRoot, ROUTER_ID))) {
		throw new ExportError("router must remain model-visible and agent-neutral");
	}
	return validated;
}

function prepareStage(transactionDir, manifest, config) {
	const paths = transactionPaths(transactionDir);
	removePath(path.join(transactionDir, "stage"));
	fs.mkdirSync(paths.stageRepoSkills, { recursive: true });
	fs.mkdirSync(paths.stageRouter, { recursive: true });

	const targetRepoSkills = path.join(config.targetLibraryRoot, "repo-skills");
	if (isRealDirectory(targetRepoSkills)) copyDirectory(targetRepoSkills, paths.stageRepoSkills);
	for (const skillId of config.selectedIds) {
		const sourceSkill = path.join(config.sourceLibraryRoot, "repo-skills", skillId);
		const stagedSkill = path.join(paths.stageRepoSkills, skillId);
		removePath(stagedSkill);
		copyDirectory(sourceSkill, stagedSkill);
	}

	writeJsonLines(path.join(paths.stageRepoSkills, REPOSITORY_INDEX_PATH), config.merged.repositories);
	writeJsonLines(path.join(paths.stageRouter, REPOSITORIES_PATH), config.merged.repositories);
	writeJsonLines(path.join(paths.stageRouter, ASSIGNMENTS_PATH), config.merged.assignments);

	if (config.targetAgent === "codex") {
		const finalSkillDirs = [...listSkillDirs(paths.stageRepoSkills).values()];
		const result = spawnSync("python3", [CODEX_POLICY, ...finalSkillDirs], { encoding: "utf8", env: process.env });
		if (result.error) throw new ExportError(`Codex policy helper could not start: ${result.error.message}`);
		if (result.status !== 0) throw new ExportError(`Codex policy helper failed: ${shortOutput(result.stderr || result.stdout)}`);
	}

	const visibility = config.routerVisibility === "preserve" ? config.targetVisibility : config.routerVisibility;
	runRouterUpdater(paths.stageRoot, paths.stageRouter, [], visibility);
	validatePreparedCollection(paths.stageRoot, {
		...config,
		finalSkillIds: config.merged.repositories.map((record) => record.skill_id),
		finalRepositoryCount: config.merged.repositories.length,
		finalAssignmentCount: config.merged.assignments.length,
	}, transactionDir);
	updateManifest(transactionDir, manifest, "validated");
	maybeFailAfter("validated");
}

function ensureBackupDirectory(directory) {
	fs.mkdirSync(path.dirname(directory), { recursive: true });
}

function commitTransaction(transactionDir, manifest, config) {
	const paths = transactionPaths(transactionDir);
	const liveRepoSkills = path.join(config.targetLibraryRoot, "repo-skills");
	const liveRouter = path.join(config.targetLibraryRoot, ROUTER_ID);
	if (manifest.phase !== "validated") throw new ExportError(`cannot commit transaction from phase ${manifest.phase}`);
	if (digestTreeState(config.targetLibraryRoot) !== config.targetSnapshotSha256) {
		throw new ExportError("target repository collection changed after staging; refusing to commit stale output");
	}
	if (pathExists(paths.backupRepoSkills) || pathExists(paths.backupRouter)) throw new ExportError("transaction backup already exists before commit");
	ensureBackupDirectory(paths.backupRepoSkills);

	updateManifest(transactionDir, manifest, "repo_backup_pending");
	maybeFailAt("before_repo_backup_rename");
	fs.mkdirSync(config.targetLibraryRoot, { recursive: true });
	if (pathExists(liveRepoSkills)) fs.renameSync(liveRepoSkills, paths.backupRepoSkills);
	maybeFailAt("after_repo_backup_rename");
	updateManifest(transactionDir, manifest, "repo_backed_up");
	maybeFailAfter("repo_backed_up");

	updateManifest(transactionDir, manifest, "repo_install_pending");
	maybeFailAt("before_repo_install_rename");
	if (!pathExists(paths.stageRepoSkills) || pathExists(liveRepoSkills)) throw new ExportError("repository-skill staging/install state is invalid");
	fs.renameSync(paths.stageRepoSkills, liveRepoSkills);
	maybeFailAt("after_repo_install_rename");
	updateManifest(transactionDir, manifest, "repo_installed");
	maybeFailAfter("repo_installed");

	updateManifest(transactionDir, manifest, "router_backup_pending");
	maybeFailAt("before_router_backup_rename");
	if (pathExists(liveRouter)) fs.renameSync(liveRouter, paths.backupRouter);
	maybeFailAt("after_router_backup_rename");
	updateManifest(transactionDir, manifest, "router_backed_up");
	maybeFailAfter("router_backed_up");

	updateManifest(transactionDir, manifest, "router_install_pending");
	maybeFailAt("before_router_install_rename");
	if (!pathExists(paths.stageRouter) || pathExists(liveRouter)) throw new ExportError("router staging/install state is invalid");
	fs.renameSync(paths.stageRouter, liveRouter);
	maybeFailAt("after_router_install_rename");
	updateManifest(transactionDir, manifest, "router_installed");
	maybeFailAfter("router_installed");

	maybeFailAt("before_live_validation");
	validatePreparedCollection(config.targetLibraryRoot, config, transactionDir);
	updateManifest(transactionDir, manifest, "live_validated");
	maybeFailAfter("live_validated");
	updateManifest(transactionDir, manifest, "committed");
	maybeFailAfter("committed");
}

function phaseAtOrAfter(phase, threshold) {
	const ordered = [
		"repo_backup_pending",
		"repo_backed_up",
		"repo_install_pending",
		"repo_installed",
		"router_backup_pending",
		"router_backed_up",
		"router_install_pending",
		"router_installed",
		"live_validated",
	];
	return ordered.indexOf(phase) >= ordered.indexOf(threshold) && ordered.indexOf(threshold) >= 0;
}

function restoreManagedPath(livePath, backupPath, stagePath, existedBefore, installMayHaveStarted) {
	if (pathExists(backupPath)) {
		removePath(livePath);
		fs.renameSync(backupPath, livePath);
		return;
	}
	if (existedBefore) {
		if (!pathExists(livePath)) throw new ExportError(`original target is missing and no backup exists for ${livePath}`);
		return;
	}
	if (installMayHaveStarted && pathExists(livePath) && !pathExists(stagePath)) removePath(livePath);
}

function rollbackTransaction(transactionDir, manifest, config) {
	const paths = transactionPaths(transactionDir);
	const errors = [];
	try {
		restoreManagedPath(
			path.join(config.targetLibraryRoot, "repo-skills"),
			paths.backupRepoSkills,
			paths.stageRepoSkills,
			manifest.repo_existed === true,
			phaseAtOrAfter(manifest.phase, "repo_install_pending"),
		);
	} catch (error) {
		errors.push(`repo-skills rollback failed: ${error instanceof Error ? error.message : String(error)}`);
	}
	try {
		restoreManagedPath(
			path.join(config.targetLibraryRoot, ROUTER_ID),
			paths.backupRouter,
			paths.stageRouter,
			manifest.router_existed === true,
			phaseAtOrAfter(manifest.phase, "router_install_pending"),
		);
	} catch (error) {
		errors.push(`router rollback failed: ${error instanceof Error ? error.message : String(error)}`);
	}
	removePath(path.join(transactionDir, "stage"));
	if (!manifest.target_library_root_existed && isRealDirectory(config.targetLibraryRoot) && fs.readdirSync(config.targetLibraryRoot).length === 0) {
		removePath(config.targetLibraryRoot);
	}
	if (!manifest.target_skills_root_existed && isRealDirectory(config.targetSkillsRoot) && fs.readdirSync(config.targetSkillsRoot).length === 0) {
		removePath(config.targetSkillsRoot);
	}
	if (errors.length) throw new ExportError(`${errors.join("; ")} Recovery artifacts remain at ${transactionDir}`);
	if (digestTreeState(config.targetLibraryRoot) !== config.targetSnapshotSha256) {
		throw new ExportError(`rollback did not restore the recorded target snapshot. Recovery artifacts remain at ${transactionDir}`);
	}
	updateManifest(transactionDir, manifest, "rolled_back");
}

function cleanupTransaction(transactionDir) {
	removePath(transactionDir);
}

function buildConfig(options, sourceLibraryRoot, targetSkillsRoot, targetLibraryRoot, source, target, taxonomyHash) {
	const selectedIds = source.selectedIds;
	const targetIds = new Set(target.repositories.map((record) => record.skill_id));
	const overwrite = new Set(options.overwriteSkillIds);
	for (const skillId of selectedIds) {
		if (targetIds.has(skillId) && !overwrite.has(skillId)) {
			throw new ExportError(`target skill ${skillId} already exists; obtain approval and pass --overwrite-skill ${skillId}`);
		}
	}
	for (const skillId of overwrite) {
		if (!targetIds.has(skillId)) throw new ExportError(`--overwrite-skill ${skillId} is not an existing target skill`);
		if (!selectedIds.includes(skillId)) throw new ExportError(`--overwrite-skill ${skillId} is not in the selected source set`);
	}
	const merged = mergeRecords(target, source, selectedIds);
	const effectiveRouterVisibility = options.routerVisibility === "preserve" ? target.visibility : options.routerVisibility;
	return {
		sourceLibraryRoot,
		targetSkillsRoot,
		targetLibraryRoot,
		targetAgent: options.targetAgent,
		includeSkillIds: options.includeSkillIds,
		overwriteSkillIds: options.overwriteSkillIds,
		selectedIds,
		merged,
		targetVisibility: target.visibility,
		routerVisibility: options.routerVisibility,
		effectiveRouterVisibility,
		taxonomyHash,
		sourceSelectionSha256: digestSelection(source.repositories, source.assignments, taxonomyHash),
		sourceSkillSnapshotSha256: source.sourceSkillSnapshotSha256,
		targetSnapshotSha256: digestTreeState(targetLibraryRoot),
		finalSkillIds: merged.repositories.map((record) => record.skill_id).sort(),
		finalRepositoryCount: merged.repositories.length,
		finalAssignmentCount: merged.assignments.length,
	};
}

function assertConfigMatchesManifest(config, manifest) {
	const comparisons = [
		["selected_skill_ids", config.selectedIds],
		["final_skill_ids", config.finalSkillIds],
	];
	for (const [field, value] of comparisons) {
		if (JSON.stringify(manifest[field] || []) !== JSON.stringify(value)) throw new ExportError(`resume ${field} differs from the persisted transaction`);
	}
	for (const [field, value] of [
		["source_selection_sha256", config.sourceSelectionSha256],
		["target_snapshot_sha256", config.targetSnapshotSha256],
		["effective_router_visibility", config.effectiveRouterVisibility],
		["final_repository_count", config.finalRepositoryCount],
		["final_assignment_count", config.finalAssignmentCount],
	]) {
		if (manifest[field] !== value) throw new ExportError(`resume ${field} differs from the persisted transaction`);
	}
	if (manifest.source_skill_snapshot_sha256 !== undefined && manifest.source_skill_snapshot_sha256 !== config.sourceSkillSnapshotSha256) {
		throw new ExportError("resume source_skill_snapshot_sha256 differs from the persisted transaction");
	}
}

function prepareOrReprepareTransaction(transaction, config, taxonomyHash) {
	const source = validateSourceSelection(config.sourceLibraryRoot, config.includeSkillIds, transaction.directory, taxonomyHash);
	const target = validateTargetCollection(config.targetLibraryRoot, taxonomyHash, transaction.directory);
	const rebuilt = buildConfig(config, config.sourceLibraryRoot, config.targetSkillsRoot, config.targetLibraryRoot, source, target, taxonomyHash);
	assertConfigMatchesManifest(rebuilt, transaction.manifest);
	if (transaction.manifest.source_skill_snapshot_sha256 === undefined) {
		transaction.manifest.source_skill_snapshot_sha256 = rebuilt.sourceSkillSnapshotSha256;
	}
	prepareStage(transaction.directory, transaction.manifest, rebuilt);
	return rebuilt;
}

function main(argv) {
	let transaction;
	let config;
	try {
		const args = parseArgs(argv);
		const templateTaxonomy = path.join(ROUTER_TEMPLATE_DIR, TAXONOMY_PATH);
		const taxonomyHash = hashFile(templateTaxonomy);

		if (args.resumeTransaction) {
			transaction = loadTransaction(args.resumeTransaction);
			assertResumeMatches(args, transaction.manifest);
			config = {
				...configFromManifest(transaction.manifest),
				finalSkillIds: transaction.manifest.final_skill_ids || [],
				finalRepositoryCount: transaction.manifest.final_repository_count,
				finalAssignmentCount: transaction.manifest.final_assignment_count,
			};
			if (config.taxonomyHash !== taxonomyHash) throw new ExportError("transaction taxonomy no longer matches the bundled canonical taxonomy");
			assertPathHasNoSymlinkComponents(config.sourceLibraryRoot, "persisted source library root");
			assertPathHasNoSymlinkComponents(config.targetLibraryRoot, "persisted target repository collection");
			if (pathsOverlap(config.sourceLibraryRoot, config.targetLibraryRoot)) throw new ExportError("source and target repository collections overlap");
			if (MUTATION_PHASES.has(transaction.manifest.phase)) rollbackTransaction(transaction.directory, transaction.manifest, config);
			if (transaction.manifest.phase === "committed") {
				validatePreparedCollection(config.targetLibraryRoot, config, transaction.directory);
			} else if (transaction.manifest.phase === "validated") {
				assertPersistedSourceUnchanged(config, transaction.directory);
				if (digestTreeState(config.targetLibraryRoot) !== config.targetSnapshotSha256) throw new ExportError("target changed after staging; cannot resume this transaction");
				validatePreparedCollection(transactionPaths(transaction.directory).stageRoot, config, transaction.directory);
				commitTransaction(transaction.directory, transaction.manifest, config);
			} else if (transaction.manifest.phase === "staging" || transaction.manifest.phase === "rolled_back") {
				assertRealDirectory(config.sourceLibraryRoot, "persisted source library root");
				config = prepareOrReprepareTransaction(transaction, config, taxonomyHash);
				commitTransaction(transaction.directory, transaction.manifest, config);
			} else {
				throw new ExportError(`cannot resume transaction from unknown phase ${transaction.manifest.phase}`);
			}
		} else {
			const sourceLibraryRoot = resolveSourceLibraryRoot(args);
			const targetSkillsRoot = resolveTargetSkillsRoot(args);
			const targetLibraryRoot = path.join(targetSkillsRoot, "repositories");
			assertPathHasNoSymlinkComponents(targetSkillsRoot, "target skills root");
			if (pathsOverlap(sourceLibraryRoot, targetLibraryRoot)) throw new ExportError("source and target repository collections overlap");
			const parent = resolveTransactionParent(targetSkillsRoot);
			const pending = findTransactions(parent, targetLibraryRoot);
			if (pending.length) throw new ExportError(`a pending export transaction already exists at ${pending[0].directory}; rerun with --resume ${pending[0].directory}`);
			const validationDir = fs.mkdtempSync(path.join(parent, ".repo-skills-export-validation-"));
			try {
				const source = validateSourceSelection(sourceLibraryRoot, args.includeSkillIds, validationDir, taxonomyHash);
				const target = validateTargetCollection(targetLibraryRoot, taxonomyHash, validationDir);
				config = buildConfig(args, sourceLibraryRoot, targetSkillsRoot, targetLibraryRoot, source, target, taxonomyHash);
			} finally {
				removePath(validationDir);
			}
			transaction = makeTransaction(parent, config);
			prepareStage(transaction.directory, transaction.manifest, config);
			commitTransaction(transaction.directory, transaction.manifest, config);
		}
		console.log(`exported repository skills to ${config.targetLibraryRoot}`);
		console.log(`transaction: ${transaction.directory}`);
		console.log(`selected skills: ${transaction.manifest.selected_skill_ids.length}`);
		console.log(`approved replacements: ${transaction.manifest.overwrite_skill_ids.length}`);
		console.log(`final repositories: ${transaction.manifest.final_repository_count}`);
		console.log(`final assignments: ${transaction.manifest.final_assignment_count}`);
		console.log(`router: ${path.join(config.targetLibraryRoot, ROUTER_ID)}`);
		cleanupTransaction(transaction.directory);
		return 0;
	} catch (error) {
		let message = error instanceof Error ? error.message : String(error);
		if (transaction && config && MUTATION_PHASES.has(transaction.manifest.phase)) {
			try {
				rollbackTransaction(transaction.directory, transaction.manifest, config);
				message = `${message}; target restored. Retry with --resume ${transaction.directory}`;
			} catch (rollbackError) {
				message = `${message}; ${rollbackError instanceof Error ? rollbackError.message : String(rollbackError)}`;
			}
		} else if (transaction && transaction.manifest.phase !== "committed") {
			message = `${message}; transaction preserved for --resume ${transaction.directory}`;
		}
		console.error(`export_repo_skills_to_agent.mjs: ${message}`);
		return 2;
	}
}

process.exitCode = main(process.argv.slice(2));
