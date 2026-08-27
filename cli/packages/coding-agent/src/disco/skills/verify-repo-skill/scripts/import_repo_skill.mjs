#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const DEFAULT_TIMEOUT_SECONDS = 900;
const CANONICAL_NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const REPO_ID = /^[^/\s]+\/[^/\s]+$/;
const TAXONOMY_SHA256 = "f8c306386015711634ddbb43a5eb95d1f58909c3513ce2063ba42efdd583a431";
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

function expandHome(value) {
	return value.replace(/^~(?=$|[\/])/, os.homedir());
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

function validateEvidenceFile(sourceCheckout, evidencePath, lineStart, lineEnd, label) {
	const sourcePath = path.resolve(sourceCheckout, evidencePath);
	if (!isWithin(sourceCheckout, sourcePath) || !pathExists(sourcePath)) {
		throw new ImportError(`${label} path does not exist in source checkout: ${evidencePath}`);
	}
	const stat = fs.lstatSync(sourcePath);
	if (!stat.isFile() || stat.isSymbolicLink()) {
		throw new ImportError(`${label} path must be a regular file in source checkout: ${evidencePath}`);
	}
	if (lineStart === undefined && lineEnd === undefined) return;
	const content = fs.readFileSync(sourcePath, "utf8");
	const lineCount = content.length === 0 ? 0 : content.split(/\r?\n/).length - (content.endsWith("\n") ? 1 : 0);
	const highestLine = lineEnd ?? lineStart;
	if (highestLine > lineCount) {
		throw new ImportError(`${label} line range exceeds ${evidencePath} (${lineCount} lines)`);
	}
}

function optionValue(argv, index, option) {
	const value = argv[index + 1];
	if (!value || value.startsWith("--")) throw new ImportError(`${option} requires a value`);
	return value;
}

function parseArgs(argv) {
	const args = {
		agentDir: defaultAgentDir(),
		sourceDir: undefined,
		routingEntry: undefined,
		manualUnrouted: false,
		overwrite: false,
		alreadyLocked: false,
		timeout: DEFAULT_TIMEOUT_SECONDS,
	};
	for (let index = 0; index < argv.length; index += 1) {
		const item = argv[index];
		if (item === "--agent-dir") {
			args.agentDir = optionValue(argv, index, item);
			index += 1;
		} else if (item === "--routing-entry") {
			args.routingEntry = optionValue(argv, index, item);
			index += 1;
		} else if (item === "--manual-unrouted") {
			args.manualUnrouted = true;
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
		} else if (args.sourceDir) {
			throw new ImportError("provide exactly one runtime repo skill directory");
		} else {
			args.sourceDir = item;
		}
	}
	if (!args.sourceDir) throw new ImportError("provide one verified runtime repo skill directory");
	if (args.routingEntry && args.manualUnrouted) throw new ImportError("--routing-entry and --manual-unrouted are mutually exclusive");
	if (!Number.isFinite(args.timeout) || args.timeout <= 0) throw new ImportError("--timeout must be a positive number");
	return args;
}

function printHelp() {
	console.log(`Usage: node import_repo_skill.mjs [options] RUNTIME_SKILL_DIR

Options:
  --agent-dir DIR       DisCo agent directory
  --routing-entry FILE  External verified area-family classification handoff
  --manual-unrouted     Explicitly import an unclassified skill without a routing handoff
  --overwrite           Replace the same repo skill after explicit approval
  --already-locked      Assert the global import lock is already held
  --timeout SECONDS     Seconds to wait for the global import lock`);
}

function parseFrontmatter(skillFile) {
	const content = fs.readFileSync(skillFile, "utf8");
	const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match?.[1]) throw new ImportError(`${skillFile} is missing YAML frontmatter`);
	let frontmatter;
	try {
		frontmatter = parse(match[1]);
	} catch (error) {
		throw new ImportError(`${skillFile} has invalid YAML frontmatter: ${error instanceof Error ? error.message : String(error)}`);
	}
	if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter)) throw new ImportError(`${skillFile} frontmatter must be a mapping`);
	return { frontmatter, frontmatterText: match[1] };
}

function collectPortableFiles(root, files = []) {
	const stat = fs.lstatSync(root);
	if (!stat.isDirectory() || stat.isSymbolicLink()) throw new ImportError(`runtime repo skill must be a real directory: ${root}`);
	for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
		const entryPath = path.join(root, entry.name);
		if (entry.isSymbolicLink()) throw new ImportError(`runtime repo skill contains a symbolic link: ${entryPath}`);
		if (entry.isDirectory()) collectPortableFiles(entryPath, files);
		else if (entry.isFile()) files.push(entryPath);
		else throw new ImportError(`runtime repo skill contains a non-portable file: ${entryPath}`);
	}
	return files;
}

function digestPortableTree(root) {
	const hash = createHash("sha256");
	const files = collectPortableFiles(root).sort((left, right) => left.localeCompare(right));
	for (const filePath of files) {
		const relativePath = path.relative(root, filePath).split(path.sep).join("/");
		const content = fs.readFileSync(filePath);
		hash.update(`file\0${relativePath}\0${content.byteLength}\0`);
		hash.update(content);
		hash.update("\0");
	}
	return `sha256:${hash.digest("hex")}`;
}

function isRelativeRepositoryPath(value) {
	if (typeof value !== "string" || !value.trim() || path.isAbsolute(value)) return false;
	const normalized = value.replaceAll("\\", "/");
	return normalized !== "." && !normalized.split("/").includes("..") && !normalized.startsWith("/");
}

function validateSkillFile(skillFile, seenNames) {
	const { frontmatter, frontmatterText } = parseFrontmatter(skillFile);
	const name = frontmatter.name;
	if (typeof name !== "string" || !CANONICAL_NAME.test(name) || name.length > 64) throw new ImportError(`${skillFile} must declare a canonical lowercase-hyphen name`);
	if (name !== path.basename(path.dirname(skillFile))) throw new ImportError(`${skillFile} name must match its directory basename`);
	if (seenNames.has(name)) throw new ImportError(`repo skill contains duplicate skill name: ${name}`);
	seenNames.add(name);
	if (typeof frontmatter.description !== "string" || !frontmatter.description.trim()) throw new ImportError(`${skillFile} frontmatter must contain a non-empty description`);
	if (!/^description:\s*"(?:[^"\\]|\\.)*"\s*$/m.test(frontmatterText)) throw new ImportError(`${skillFile} frontmatter description must be double-quoted`);
	if (frontmatter["disable-model-invocation"] !== true) throw new ImportError(`${skillFile} frontmatter must contain disable-model-invocation: true`);
	const role = frontmatter.metadata && typeof frontmatter.metadata === "object" && !Array.isArray(frontmatter.metadata) ? frontmatter.metadata["disco-role"] : undefined;
	if (role !== "operating") throw new ImportError(`${skillFile} metadata.disco-role must be operating`);
	return name;
}

function validateMarkdownLinks(skillRoot, markdownFiles) {
	for (const filePath of markdownFiles) {
		const content = fs.readFileSync(filePath, "utf8");
		let fenced = false;
		const prose = content.split(/\r?\n/).filter((line) => {
			if (/^\s*```/.test(line)) {
				fenced = !fenced;
				return false;
			}
			return !fenced;
		}).join("\n").replace(/(`+)[\s\S]*?\1/g, "");
		for (const match of prose.matchAll(/\[[^\]]+\]\(([^)]+)\)/g)) {
			let target = match[1]?.trim();
			if (!target || target.startsWith("#") || /^[a-z][a-z0-9+.-]*:/i.test(target)) continue;
			if (target.startsWith("<") && target.endsWith(">")) target = target.slice(1, -1);
			target = target.split("#", 1)[0]?.split("?", 1)[0] ?? "";
			if (!target) continue;
			let decoded;
			try { decoded = decodeURIComponent(target); } catch { throw new ImportError(`${filePath} contains an invalid encoded Markdown link: ${target}`); }
			const resolved = path.resolve(path.dirname(filePath), decoded);
			if (!isWithin(skillRoot, resolved)) throw new ImportError(`${filePath} contains a relative link outside the repo skill: ${target}`);
			if (!pathExists(resolved)) throw new ImportError(`${filePath} contains a broken relative link: ${target}`);
		}
	}
}

function loadTaxonomyPaths() {
	const taxonomyFile = process.env.DISCO_ROUTER_TAXONOMY_FILE || path.join(SCRIPT_DIR, "../../repo-skills-router/references/index/taxonomy.json");
	if (!pathExists(taxonomyFile)) throw new ImportError(`router taxonomy is missing: ${taxonomyFile}`);
	const bytes = fs.readFileSync(taxonomyFile);
	const taxonomySha256 = createHash("sha256").update(bytes).digest("hex");
	if (taxonomySha256 !== TAXONOMY_SHA256) throw new ImportError(`router taxonomy does not match the canonical taxonomy hash ${TAXONOMY_SHA256}`);
	let taxonomy;
	try { taxonomy = JSON.parse(bytes.toString("utf8")); } catch (error) { throw new ImportError(`router taxonomy is invalid JSON: ${error instanceof Error ? error.message : String(error)}`); }
	if (!taxonomy || typeof taxonomy !== "object" || !Array.isArray(taxonomy.areas)) throw new ImportError("router taxonomy must contain an areas array");
	const paths = new Set();
	for (const area of taxonomy.areas) {
		if (!area || typeof area.name !== "string" || !Array.isArray(area.families)) throw new ImportError("router taxonomy contains an invalid area");
		for (const family of area.families) {
			if (!family || typeof family.name !== "string") throw new ImportError("router taxonomy contains an invalid family");
			paths.add(`${area.name}\0${family.name}`);
		}
	}
	return { paths, taxonomySha256 };
}

function validateRoutingHandoff(handoff, metadata, skillRoot, skillId, routingEntryPath, taxonomyPaths, taxonomySha256) {
	if (!handoff || typeof handoff !== "object" || Array.isArray(handoff)) throw new ImportError(`${routingEntryPath} must contain a JSON object`);
	if (handoff.schema_version !== 1) throw new ImportError(`${routingEntryPath}.schema_version must be 1`);
	if (handoff.repo_id !== metadata.repo_id || handoff.skill_id !== skillId || handoff.taxonomy_sha256 !== taxonomySha256) throw new ImportError("routing handoff identity or taxonomy does not match the runtime metadata");
	if (typeof handoff.repo_name !== "string" || handoff.repo_name !== metadata.repo_id.split("/").at(-1)) throw new ImportError("routing handoff repo_name does not match repo_id");
	if (typeof handoff.source_url !== "string" || !/^https:\/\/github\.com\/[^/\s]+\/[^/\s]+(?:\.git)?\/?$/i.test(handoff.source_url.trim())) throw new ImportError("routing handoff source_url must be a GitHub repository URL");
	if (typeof handoff.source_commit !== "string" || !/^[0-9a-f]{40}$/i.test(handoff.source_commit)) throw new ImportError("routing handoff source_commit must be a 40-hex commit");
	if (handoff.legacy_repo_id !== undefined && (typeof handoff.legacy_repo_id !== "string" || !handoff.legacy_repo_id.trim())) throw new ImportError("routing handoff legacy_repo_id must be a non-empty string when provided");
	if (!isRelativeRepositoryPath(handoff.skill_root)) throw new ImportError("routing handoff skill_root must be a relative path");
	if (handoff.source_skill_root !== undefined && !isRelativeRepositoryPath(handoff.source_skill_root)) throw new ImportError("routing handoff source_skill_root must be a relative path");
	if (typeof handoff.skill_content_sha256 !== "string" || !/^sha256:[0-9a-f]{64}$/i.test(handoff.skill_content_sha256)) throw new ImportError("routing handoff skill_content_sha256 must be sha256:<64 hex characters>");
	if (handoff.skill_content_sha256.toLowerCase() !== digestPortableTree(skillRoot).toLowerCase()) throw new ImportError("routing handoff skill_content_sha256 does not match the verified runtime skill");
	if (handoff.status !== metadata.routing_status || !Array.isArray(handoff.assignments)) throw new ImportError("routing handoff status/assignments do not match the runtime metadata");
	if (typeof handoff.source_checkout !== "string" || !path.isAbsolute(handoff.source_checkout) || !pathExists(handoff.source_checkout) || !fs.lstatSync(handoff.source_checkout).isDirectory()) throw new ImportError("routing handoff source_checkout must be an existing absolute directory");
	const handoffKeys = new Set();
	for (const [index, assignment] of handoff.assignments.entries()) {
		if (!assignment || typeof assignment !== "object" || Array.isArray(assignment)) throw new ImportError(`routing handoff assignments[${index}] is invalid`);
		const allowedAssignmentFields = new Set(["area", "family", "confidence", "rationale", "evidence", "repo_skill_paths"]);
		if (Object.keys(assignment).some((key) => !allowedAssignmentFields.has(key))) throw new ImportError(`routing handoff assignments[${index}] contains an unknown field`);
		if (typeof assignment.area !== "string" || typeof assignment.family !== "string" || !taxonomyPaths.has(`${assignment.area}\0${assignment.family}`)) throw new ImportError(`routing handoff assignments[${index}] contains an invalid taxonomy assignment`);
		if (!new Set(["high", "medium", "low"]).has(assignment.confidence)) throw new ImportError(`routing handoff assignments[${index}].confidence must be high, medium, or low`);
		const key = `${assignment.area}\0${assignment.family}`;
		if (handoffKeys.has(key)) throw new ImportError(`routing handoff contains a duplicate assignment: ${assignment.area} -> ${assignment.family}`);
		handoffKeys.add(key);
		if (handoff.status !== "classified") continue;
		if (typeof assignment.rationale !== "string" || !assignment.rationale.trim() || !Array.isArray(assignment.evidence) || assignment.evidence.length === 0) throw new ImportError("classified routing handoff assignments require rationale and evidence");
		let nonGeneratedEvidence = false;
		for (const [evidenceIndex, evidence] of assignment.evidence.entries()) {
			if (!evidence || typeof evidence !== "object" || Array.isArray(evidence) || !isRelativeRepositoryPath(evidence.path) || typeof evidence.description !== "string" || !evidence.description.trim()) throw new ImportError(`routing handoff evidence ${index}:${evidenceIndex} must contain a relative path and description`);
			if (evidence.line_start !== undefined && (!Number.isInteger(evidence.line_start) || evidence.line_start < 1)) throw new ImportError(`routing handoff evidence ${index}:${evidenceIndex} has an invalid line_start`);
			if (evidence.line_end !== undefined && (!Number.isInteger(evidence.line_end) || evidence.line_end < 1)) throw new ImportError(`routing handoff evidence ${index}:${evidenceIndex} has an invalid line_end`);
			if (evidence.line_start !== undefined && evidence.line_end !== undefined && evidence.line_end < evidence.line_start) throw new ImportError(`routing handoff evidence ${index}:${evidenceIndex} has a reversed line range`);
			if (evidence.kind !== "generated_skill") nonGeneratedEvidence = true;
			validateEvidenceFile(
				handoff.source_checkout,
				evidence.path,
				evidence.line_start,
				evidence.line_end,
				`routing handoff evidence ${index}:${evidenceIndex}`,
			);
		}
		if (!nonGeneratedEvidence) throw new ImportError(`routing handoff assignment ${assignment.area} -> ${assignment.family} has no non-generated repository evidence`);
		if (assignment.repo_skill_paths !== undefined && (!Array.isArray(assignment.repo_skill_paths) || assignment.repo_skill_paths.some((value) => !isRelativeRepositoryPath(value)))) throw new ImportError(`routing handoff assignment ${index} has invalid repo_skill_paths`);
	}
	if (metadata.routing_status === "classified" && handoffKeys.size === 0) throw new ImportError("classified routing handoff requires assignments");
	if (metadata.routing_status === "unclassified" && (handoffKeys.size !== 0 || typeof handoff.unclassified_reason !== "string" || !handoff.unclassified_reason.trim())) throw new ImportError("unclassified routing handoff requires a reason and no assignments");
	return handoffKeys;
}

function validateRoutingMetadata(skillRoot, skillId, routingEntryPath, manualUnrouted) {
	const metadataFile = path.join(skillRoot, "references", "repo-routing-metadata.json");
	if (!pathExists(metadataFile) || !fs.lstatSync(metadataFile).isFile()) throw new ImportError(`runtime repo skill is missing ${metadataFile}`);
	let data;
	try { data = JSON.parse(fs.readFileSync(metadataFile, "utf8")); } catch (error) { throw new ImportError(`${metadataFile} is invalid JSON: ${error instanceof Error ? error.message : String(error)}`); }
	if (!data || typeof data !== "object" || Array.isArray(data)) throw new ImportError(`${metadataFile} must contain a JSON object`);
	const allowed = new Set(["schema_version", "repo_id", "skill_id", "taxonomy_sha256", "routing_status", "assignments", "unclassified_reason"]);
	for (const key of Object.keys(data)) if (!allowed.has(key)) throw new ImportError(`${metadataFile} contains unknown field ${key}`);
	if (data.schema_version !== "2.0") throw new ImportError(`${metadataFile}.schema_version must be \"2.0\"`);
	if (typeof data.repo_id !== "string" || !REPO_ID.test(data.repo_id)) throw new ImportError(`${metadataFile}.repo_id must use owner/repository form`);
	if (data.skill_id !== skillId) throw new ImportError(`${metadataFile}.skill_id must equal ${skillId}`);
	const taxonomy = loadTaxonomyPaths();
	if (data.taxonomy_sha256 !== taxonomy.taxonomySha256) throw new ImportError(`${metadataFile}.taxonomy_sha256 does not match the current taxonomy`);
	if (!new Set(["classified", "unclassified"]).has(data.routing_status)) throw new ImportError(`${metadataFile}.routing_status must be classified or unclassified`);
	if (!Array.isArray(data.assignments)) throw new ImportError(`${metadataFile}.assignments must be an array`);
	const assignmentKeys = new Set();
	for (const [index, assignment] of data.assignments.entries()) {
		if (!assignment || typeof assignment !== "object" || Array.isArray(assignment) || Object.keys(assignment).some((key) => !["area", "family"].includes(key)) || typeof assignment.area !== "string" || typeof assignment.family !== "string") throw new ImportError(`${metadataFile}.assignments[${index}] is invalid`);
		const key = `${assignment.area}\0${assignment.family}`;
		if (!taxonomy.paths.has(key) || assignmentKeys.has(key)) throw new ImportError(`${metadataFile}.assignments[${index}] is unknown or duplicated`);
		assignmentKeys.add(key);
	}
	if (data.routing_status === "classified" && assignmentKeys.size === 0) throw new ImportError(`${metadataFile} classified status requires assignments`);
	if (data.routing_status === "unclassified" && (assignmentKeys.size !== 0 || typeof data.unclassified_reason !== "string" || !data.unclassified_reason.trim())) throw new ImportError(`${metadataFile} unclassified status requires a reason and no assignments`);
	if (!routingEntryPath && !manualUnrouted) throw new ImportError("normal managed imports require --routing-entry <classification.json>; use --manual-unrouted only for an explicit unclassified import");
	if (manualUnrouted && data.routing_status !== "unclassified") throw new ImportError("--manual-unrouted requires runtime metadata with routing_status unclassified");
	if (routingEntryPath) {
		if (!pathExists(routingEntryPath)) throw new ImportError(`routing handoff does not exist: ${routingEntryPath}`);
		let handoff;
		try { handoff = JSON.parse(fs.readFileSync(routingEntryPath, "utf8")); } catch (error) { throw new ImportError(`routing handoff is invalid JSON: ${error instanceof Error ? error.message : String(error)}`); }
		const handoffKeys = validateRoutingHandoff(handoff, data, skillRoot, skillId, routingEntryPath, taxonomy.paths, taxonomy.taxonomySha256);
		if (handoffKeys.size !== assignmentKeys.size || [...assignmentKeys].some((key) => !handoffKeys.has(key))) throw new ImportError("routing handoff assignments do not exactly match repo-routing-metadata.json");
	}
	return data;
}

function validateRepoSkill(skillRoot, routingEntryPath, manualUnrouted) {
	const files = collectPortableFiles(skillRoot);
	const rootSkillFile = path.join(skillRoot, "SKILL.md");
	if (!files.includes(rootSkillFile)) throw new ImportError(`runtime repo skill is missing a regular root SKILL.md: ${rootSkillFile}`);
	const seenNames = new Set();
	const markdownFiles = [];
	for (const file of files) {
		if (path.basename(file) === "SKILL.md") validateSkillFile(file, seenNames);
		if (path.extname(file).toLowerCase() === ".md") markdownFiles.push(file);
	}
	const skillId = parseFrontmatter(rootSkillFile).frontmatter.name;
	if (skillId === "repo-skills" || skillId === "repo-skills-router") throw new ImportError(`${skillId} is reserved for the managed repo-skill library`);
	const metadata = validateRoutingMetadata(skillRoot, skillId, routingEntryPath, manualUnrouted);
	validateMarkdownLinks(skillRoot, markdownFiles);
	return { skillId, metadata };
}

function withImportLockScript() { return path.join(SCRIPT_DIR, "with_import_lock.mjs"); }
function routerUpdaterScript() { return path.join(SCRIPT_DIR, "update_repo_skills_router.mjs"); }

function runUnderLock(argv, agentDir, timeout) {
	const lockScript = withImportLockScript();
	if (!pathExists(lockScript)) throw new ImportError(`global import lock helper not found: ${lockScript}`);
	const command = [process.execPath, lockScript, "--agent-dir", agentDir, "--timeout", String(timeout), "--", process.execPath, SCRIPT_PATH, ...argv.filter((item) => item !== "--already-locked"), "--already-locked"];
	const completed = spawnSync(command[0], command.slice(1), { stdio: "inherit" });
	if (completed.error) throw completed.error;
	return completed.status ?? 1;
}

function runRouterUpdater(agentDir, routingEntryPath) {
	const updater = routerUpdaterScript();
	if (!pathExists(updater)) throw new ImportError(`repo-skills-router updater not found: ${updater}`);
	const libraryRoot = path.join(agentDir, "skills", "repositories");
	const updaterArgs = [updater, "--library-root", libraryRoot, "--template-dir", path.join(SCRIPT_DIR, "../../repo-skills-router"), "--router-visibility", "preserve"];
	if (routingEntryPath) updaterArgs.push("--routing-entry", routingEntryPath);
	updaterArgs.push("--already-locked");
	const completed = spawnSync(process.execPath, updaterArgs, { encoding: "utf8", env: process.env });
	if (completed.stdout) process.stdout.write(completed.stdout);
	if (completed.stderr) process.stderr.write(completed.stderr);
	if (completed.error) throw completed.error;
	if (completed.status !== 0) throw new ImportError(`repo-skills-router updater failed with exit code ${completed.status ?? 1}`);
}

function maybeInjectTestFailure(stage) {
	if (process.env.NODE_ENV === "test" && process.env.DISCO_TEST_FAIL_REPO_IMPORT_AT === stage) throw new ImportError(`injected repo-skill import failure at ${stage}`);
}

function rollbackImport({ targetDir, targetBackup, routerDir, routerBackup, routerExisted, indexPath, indexBackup, indexExisted }) {
	const errors = [];
	try { fs.rmSync(targetDir, { recursive: true, force: true }); if (pathExists(targetBackup)) fs.renameSync(targetBackup, targetDir); } catch (error) { errors.push(`could not restore repo skill: ${error instanceof Error ? error.message : String(error)}`); }
	try { fs.rmSync(routerDir, { recursive: true, force: true }); if (routerExisted && pathExists(routerBackup)) fs.renameSync(routerBackup, routerDir); } catch (error) { errors.push(`could not restore repo-skills-router: ${error instanceof Error ? error.message : String(error)}`); }
	try { fs.rmSync(indexPath, { force: true }); if (indexExisted && pathExists(indexBackup)) fs.renameSync(indexBackup, indexPath); } catch (error) { errors.push(`could not restore repository index: ${error instanceof Error ? error.message : String(error)}`); }
	return errors;
}

function importRepoSkill(args) {
	const agentDir = path.resolve(expandHome(args.agentDir));
	const skillsRoot = path.join(agentDir, "skills", "repositories");
	const repoSkillsRoot = path.join(skillsRoot, "repo-skills");
	const routerDir = path.join(skillsRoot, "repo-skills-router");
	const indexPath = path.join(repoSkillsRoot, "repository-index.jsonl");
	const sourceDir = path.resolve(expandHome(args.sourceDir));
	const routingEntryPath = args.routingEntry ? path.resolve(expandHome(args.routingEntry)) : undefined;
	if (!pathExists(sourceDir)) throw new ImportError(`runtime repo skill directory does not exist: ${sourceDir}`);
	if (isWithin(skillsRoot, sourceDir)) throw new ImportError(`runtime repo skill must be staged outside the live DisCo skills root before import: ${skillsRoot}`);
	const { skillId } = validateRepoSkill(sourceDir, routingEntryPath, args.manualUnrouted);
	const targetDir = path.join(repoSkillsRoot, skillId);
	if (pathExists(targetDir) && !args.overwrite) throw new ImportError(`live repo skill already exists: ${targetDir}. Obtain separate overwrite approval, then rerun with --overwrite`);
	fs.mkdirSync(repoSkillsRoot, { recursive: true });
	const transactionId = `${process.pid}.${Date.now()}.${Math.random().toString(36).slice(2)}`;
	const transactionDir = path.join(skillsRoot, `.repo-skill-import.${transactionId}`);
	const stagedDir = path.join(transactionDir, "staged", skillId);
	const targetBackup = path.join(transactionDir, "backups", "previous-skill");
	const routerBackup = path.join(transactionDir, "backups", "previous-router");
	const indexBackup = path.join(transactionDir, "backups", "previous-repository-index.jsonl");
	let mutationStarted = false;
	let preserveTransaction = false;
	let routerExisted = false;
	let indexExisted = false;
	try {
		fs.mkdirSync(path.dirname(stagedDir), { recursive: true });
		fs.mkdirSync(path.dirname(targetBackup), { recursive: true });
		fs.cpSync(sourceDir, stagedDir, { recursive: true, errorOnExist: true, force: false });
		if (validateRepoSkill(stagedDir, routingEntryPath, args.manualUnrouted).skillId !== skillId) throw new ImportError("staged repo skill identity changed during copy");
		const targetExists = pathExists(targetDir);
		if (targetExists && !args.overwrite) throw new ImportError(`live repo skill appeared during import: ${targetDir}. Obtain separate overwrite approval, then rerun with --overwrite`);
		routerExisted = pathExists(routerDir);
		if (routerExisted) fs.cpSync(routerDir, routerBackup, { recursive: true, errorOnExist: true, force: false });
		indexExisted = pathExists(indexPath);
		if (indexExisted) fs.copyFileSync(indexPath, indexBackup);
		if (targetExists) fs.renameSync(targetDir, targetBackup);
		mutationStarted = true;
		fs.renameSync(stagedDir, targetDir);
		validateRepoSkill(targetDir, routingEntryPath, args.manualUnrouted);
		maybeInjectTestFailure("after-install");
			runRouterUpdater(agentDir, routingEntryPath);
		if (!pathExists(path.join(targetDir, "SKILL.md"))) throw new ImportError(`installed repo skill disappeared before commit: ${targetDir}`);
		if (!pathExists(path.join(routerDir, "SKILL.md"))) throw new ImportError(`repo-skills-router was not created or updated: ${routerDir}`);
		maybeInjectTestFailure("after-router-update");
		console.log(`imported and routed repo skill ${skillId} at ${targetDir}`);
		console.log("Start a new /researcher session to use the updated managed repo skill; no cross-agent export is required.");
		return 0;
	} catch (error) {
		if (mutationStarted) {
			const rollbackErrors = rollbackImport({ targetDir, targetBackup, routerDir, routerBackup, routerExisted, indexPath, indexBackup, indexExisted });
			if (rollbackErrors.length > 0) { preserveTransaction = true; throw new ImportError(`${error instanceof Error ? error.message : String(error)}; rollback failed:\n${rollbackErrors.join("\n")}\nRecovery artifacts remain at ${transactionDir}`); }
		}
		throw error;
	} finally {
		if (!preserveTransaction) {
			try { fs.rmSync(transactionDir, { recursive: true, force: true }); } catch (error) { console.warn(`warning: could not remove repo-skill transaction directory ${transactionDir}: ${error instanceof Error ? error.message : String(error)}`); }
		}
	}
}

function main(argv) {
	let args;
	try { args = parseArgs(argv); } catch (error) { console.error(`import_repo_skill.mjs: ${error instanceof Error ? error.message : String(error)}`); return 2; }
	const agentDir = path.resolve(expandHome(args.agentDir));
	if (args.alreadyLocked && !process.env.DISCO_IMPORT_LOCK_PATH) { console.error("import_repo_skill.mjs: --already-locked requires DISCO_IMPORT_LOCK_PATH; run normally or through with_import_lock.mjs"); return 2; }
	if (!args.alreadyLocked && !process.env.DISCO_IMPORT_LOCK_PATH) {
		try { return runUnderLock(argv, agentDir, args.timeout); } catch (error) { console.error(`import_repo_skill.mjs: ${error instanceof Error ? error.message : String(error)}`); return 1; }
	}
	try { return importRepoSkill(args); } catch (error) { console.error(`import_repo_skill.mjs: ${error instanceof Error ? error.message : String(error)}`); return error instanceof ImportError ? 2 : 1; }
}

process.exitCode = main(process.argv.slice(2));
