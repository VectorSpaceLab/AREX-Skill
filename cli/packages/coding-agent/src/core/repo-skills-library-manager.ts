import { createHash } from "node:crypto";
import {
	cpSync,
	lstatSync,
	mkdirSync,
	mkdtempSync,
	readFileSync,
	readdirSync,
	renameSync,
	rmSync,
	statSync,
	utimesSync,
	writeFileSync,
} from "node:fs";
import { hostname } from "node:os";
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { parse, parseDocument } from "yaml";
import { getAgentDir, getBundledSkillsDir } from "../config.ts";
import { spawnProcess, waitForChildProcess } from "../utils/child-process.ts";

const STATE_SCHEMA_VERSION = 2;
const OFFICIAL_REPOSITORY = "https://github.com/VectorSpaceLab/AREX-Skill.git";
const LIBRARY_PATH = "skills/repositories";
const ROUTER_ID = "repo-skills-router";
const ROUTER_INDEX_PATH = join("references", "index");
const REPOSITORY_INDEX_ROOT_FILE = "repository-index.jsonl";
const LOCK_TIMEOUT_MS = 900_000;
const LOCK_STALE_MS = 3_600_000;
const LOCK_POLL_MS = 250;
const CANONICAL_SKILL_ID = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const CANONICAL_TAXONOMY_SHA256 = "f8c306386015711634ddbb43a5eb95d1f58909c3513ce2063ba42efdd583a431";
const ROUTING_METADATA_FIELDS = new Set([
	"schema_version",
	"repo_id",
	"skill_id",
	"taxonomy_sha256",
	"routing_status",
	"assignments",
	"unclassified_reason",
]);
const ROUTING_ASSIGNMENT_FIELDS = new Set(["area", "family"]);
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
	"content_sha256",
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
const MANUAL_INSTALL_URL =
	"https://github.com/VectorSpaceLab/AREX-Skill#install-the-published-repository-collection";

export class RepoSkillsLibraryError extends Error {
	readonly exitCode: number;

	constructor(message: string, exitCode = 1) {
		super(message);
		this.name = "RepoSkillsLibraryError";
		this.exitCode = exitCode;
	}
}

export class RepoSkillsLibraryConflictError extends RepoSkillsLibraryError {
	readonly conflicts: string[];

	constructor(conflicts: string[]) {
		super(
			[
				"Repository skill installation has local conflicts:",
				...conflicts.map((conflict) => `- ${conflict}`),
				"Re-run with --force to replace only the conflicting official entries after creating a backup.",
			].join("\n"),
			2,
		);
		this.name = "RepoSkillsLibraryConflictError";
		this.conflicts = conflicts;
	}
}

interface ManagedTreeState {
	digest: string;
	fileCount: number;
}

interface RepoSkillsLibraryState {
	schemaVersion: 2;
	source: {
		repository: string;
		ref: "HEAD";
		commit: string;
	};
	installedAt: string;
	updatedAt: string;
	managedSkills: Record<string, ManagedTreeState>;
	managedRootFiles: Record<string, string>;
	sourceRouterDigest: string;
	liveTreeDigest: string;
	liveRouterDigest?: string;
}

interface SourceInventory {
	libraryRoot: string;
	repoSkillsRoot: string;
	routerDir: string;
	managedSkills: Map<string, ManagedTreeState>;
	managedRootFiles: Map<string, string>;
	routerDigest: string;
}

interface SourceSnapshot {
	commit: string;
	libraryRoot: string;
	cleanup(): void;
}

interface ProcessResult {
	code: number;
	stdout: string;
	stderr: string;
}

export type RepoSkillsTransactionPoint =
	| "before-install-repo-skills"
	| "before-install-router"
	| "before-install-state"
	| "before-restore-repo-skills"
	| "before-restore-router"
	| "before-restore-state";

export interface RepoSkillsLibraryManagerOptions {
	agentDir?: string;
	sourceRepository?: string;
	gitCommand?: string;
	bundledSkillsDir?: string;
	offline?: boolean;
	now?: () => Date;
	env?: NodeJS.ProcessEnv;
	/** Used by transaction recovery tests; the CLI never supplies this hook. */
	transactionFaultInjector?: (point: RepoSkillsTransactionPoint) => void;
}

export interface RepoSkillsInstallResult {
	operation: "install" | "update";
	commit?: string;
	managedSkills: number;
	localSkills: number;
	totalSkills: number;
	repositoryCount?: number;
	assignmentCount?: number;
	areaCount?: number;
	familyCount?: number;
	routerEnabled?: boolean;
	noop: boolean;
	backupPath?: string;
	issues: string[];
}

export interface RepoSkillsRouterToggleResult {
	enabled: boolean;
	changed: boolean;
}

export interface RepoSkillsLibraryStatus {
	installed: boolean;
	managed: boolean;
	sourceRepository?: string;
	commit?: string;
	installedAt?: string;
	updatedAt?: string;
	managedSkills: number;
	localSkills: number;
	totalSkills: number;
	repositoryCount?: number;
	assignmentCount?: number;
	areaCount?: number;
	familyCount?: number;
	totalFiles: number;
	routerPresent: boolean;
	routerEnabled?: boolean;
	issues: string[];
}

function isTruthyEnvironmentFlag(value: string | undefined): boolean {
	if (!value) return false;
	return value === "1" || value.toLowerCase() === "true" || value.toLowerCase() === "yes";
}

function sleep(ms: number): Promise<void> {
	return new Promise((resolvePromise) => setTimeout(resolvePromise, ms));
}

function pathExists(path: string): boolean {
	try {
		lstatSync(path);
		return true;
	} catch (error) {
		if ((error as NodeJS.ErrnoException).code === "ENOENT") return false;
		throw error;
	}
}

function isWithin(parent: string, candidate: string): boolean {
	const relativePath = relative(parent, candidate);
	return (
		relativePath === "" ||
		(!relativePath.startsWith(`..${sep}`) && relativePath !== ".." && !isAbsolute(relativePath))
	);
}

function toPosix(path: string): string {
	return path.split(sep).join("/");
}

function stableJson(value: unknown): string {
	return `${JSON.stringify(value, null, 2)}\n`;
}

function readJsonLines(file: string): Array<Record<string, unknown>> {
	if (!pathExists(file)) return [];
	return readFileSync(file, "utf8").split(/\r?\n/).filter(Boolean).map((line, index) => {
		try {
			const value = JSON.parse(line) as unknown;
			if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("record must be an object");
			return value as Record<string, unknown>;
		} catch (error) {
			throw new RepoSkillsLibraryError(
				`Invalid JSONL record ${file}:${index + 1}: ${error instanceof Error ? error.message : String(error)}`,
			);
		}
	});
}

function writeJsonLines(file: string, records: Array<Record<string, unknown>>): void {
	mkdirSync(dirname(file), { recursive: true });
	writeFileSync(file, records.map((record) => JSON.stringify(record)).join("\n") + (records.length ? "\n" : ""), "utf8");
}

function timestampForPath(date: Date): string {
	return date.toISOString().replace(/[:.]/g, "-");
}

function shortOutput(value: string): string {
	const trimmed = value.trim();
	return trimmed.length > 4_000 ? `${trimmed.slice(0, 4_000)}\n...` : trimmed;
}

async function runProcess(
	command: string,
	args: string[],
	options: { cwd?: string; env: NodeJS.ProcessEnv },
): Promise<ProcessResult> {
	let child;
	try {
		child = spawnProcess(command, args, {
			cwd: options.cwd,
			env: options.env,
			stdio: ["ignore", "pipe", "pipe"],
		});
	} catch (error) {
		throw new RepoSkillsLibraryError(
			`Could not start ${command}: ${error instanceof Error ? error.message : String(error)}`,
		);
	}
	let stdout = "";
	let stderr = "";
	child.stdout?.setEncoding("utf8");
	child.stderr?.setEncoding("utf8");
	child.stdout?.on("data", (chunk: string) => {
		stdout += chunk;
	});
	child.stderr?.on("data", (chunk: string) => {
		stderr += chunk;
	});
	let code: number | null;
	try {
		code = await waitForChildProcess(child);
	} catch (error) {
		throw new RepoSkillsLibraryError(
			`Could not run ${command}: ${error instanceof Error ? error.message : String(error)}`,
		);
	}
	return { code: code ?? 1, stdout, stderr };
}

function lockOwnerPayload(): object {
	return {
		pid: process.pid,
		host: hostname(),
		started_at: new Date().toISOString(),
		argv: process.argv,
	};
}

function lockIsStale(lockDir: string, staleAfterMs: number): boolean {
	try {
		return Date.now() - statSync(join(lockDir, "owner.json")).mtimeMs > staleAfterMs;
	} catch {
		return false;
	}
}

async function withDirectoryLock<T>(
	lockDir: string,
	callback: () => Promise<T>,
	options: { timeoutMs?: number; staleAfterMs?: number } = {},
): Promise<T> {
	const timeoutMs = options.timeoutMs ?? LOCK_TIMEOUT_MS;
	const staleAfterMs = options.staleAfterMs ?? LOCK_STALE_MS;
	const deadline = Date.now() + timeoutMs;
	let heartbeat: NodeJS.Timeout | undefined;

	for (;;) {
		try {
			mkdirSync(dirname(lockDir), { recursive: true });
			mkdirSync(lockDir);
			const ownerFile = join(lockDir, "owner.json");
			writeFileSync(ownerFile, stableJson(lockOwnerPayload()), "utf8");
			heartbeat = setInterval(() => {
				const now = new Date();
				try {
					utimesSync(ownerFile, now, now);
					utimesSync(lockDir, now, now);
				} catch {
					// Lock release may race the final heartbeat tick.
				}
			}, Math.max(1_000, Math.floor(staleAfterMs / 4)));
			heartbeat.unref();
			break;
		} catch (error) {
			if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
			if (lockIsStale(lockDir, staleAfterMs)) {
				rmSync(lockDir, { recursive: true, force: true });
				continue;
			}
			if (Date.now() >= deadline) {
				throw new RepoSkillsLibraryError(`Timed out waiting for repository skill lock at ${lockDir}`);
			}
			await sleep(LOCK_POLL_MS);
		}
	}

	try {
		return await callback();
	} finally {
		if (heartbeat) clearInterval(heartbeat);
		rmSync(lockDir, { recursive: true, force: true });
	}
}

function collectPortableFiles(root: string): string[] {
	if (!pathExists(root)) {
		throw new RepoSkillsLibraryError(`Required directory does not exist: ${root}`);
	}
	const rootStat = lstatSync(root);
	if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) {
		throw new RepoSkillsLibraryError(`Expected a real directory: ${root}`);
	}
	const files: string[] = [];
	const visit = (directory: string): void => {
		for (const entry of readdirSync(directory, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
			const entryPath = join(directory, entry.name);
			if (entry.isSymbolicLink()) {
				throw new RepoSkillsLibraryError(`Repository skill data contains a symbolic link: ${entryPath}`);
			}
			if (entry.isDirectory()) {
				visit(entryPath);
			} else if (entry.isFile()) {
				files.push(entryPath);
			} else {
				throw new RepoSkillsLibraryError(`Repository skill data contains a non-regular file: ${entryPath}`);
			}
		}
	};
	visit(root);
	return files;
}

function digestTree(root: string): ManagedTreeState {
	const hash = createHash("sha256");
	const files = collectPortableFiles(root);
	for (const file of files) {
		const relativePath = toPosix(relative(root, file));
		const stat = lstatSync(file);
		hash.update(`file\0${relativePath}\0${stat.mode & 0o111}\0${stat.size}\0`);
		hash.update(readFileSync(file));
		hash.update("\0");
	}
	return { digest: `sha256:${hash.digest("hex")}`, fileCount: files.length };
}

function digestFile(file: string): string {
	const stat = lstatSync(file);
	if (!stat.isFile() || stat.isSymbolicLink()) {
		throw new RepoSkillsLibraryError(`Expected a regular file: ${file}`);
	}
	return `sha256:${createHash("sha256").update(readFileSync(file)).digest("hex")}`;
}

// The collection builder/updater stores content_sha256 using file bytes and
// portable relative paths, without executable-mode bits. Keep this separate
// from the manager's live-tree digest, whose mode-sensitive value detects local
// mutations during managed collection updates.
function digestRepositorySkillContent(root: string): string {
	const hash = createHash("sha256");
	for (const file of collectPortableFiles(root).sort((left, right) => left.localeCompare(right))) {
		const relativePath = toPosix(relative(root, file));
		const content = readFileSync(file);
		hash.update(`file\0${relativePath}\0${content.byteLength}\0`);
		hash.update(content);
		hash.update("\0");
	}
	return `sha256:${hash.digest("hex")}`;
}

function sortJsonValue(value: unknown): unknown {
	if (Array.isArray(value)) return value.map(sortJsonValue);
	if (!value || typeof value !== "object") return value;
	return Object.fromEntries(
		Object.entries(value as Record<string, unknown>)
			.sort(([left], [right]) => left.localeCompare(right))
			.map(([key, entry]) => [key, sortJsonValue(entry)]),
	);
}

function parseSkillName(skillFile: string): string {
	const content = readFileSync(skillFile, "utf8");
	const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match?.[1]) {
		throw new RepoSkillsLibraryError(`${skillFile} is missing YAML frontmatter`);
	}
	let frontmatter: unknown;
	try {
		frontmatter = parse(match[1]);
	} catch (error) {
		throw new RepoSkillsLibraryError(
			`${skillFile} has invalid YAML frontmatter: ${error instanceof Error ? error.message : String(error)}`,
		);
	}
	if (!frontmatter || typeof frontmatter !== "object" || Array.isArray(frontmatter)) {
		throw new RepoSkillsLibraryError(`${skillFile} frontmatter must be a mapping`);
	}
	const name = (frontmatter as Record<string, unknown>).name;
	if (typeof name !== "string" || !CANONICAL_SKILL_ID.test(name) || name.length > 64) {
		throw new RepoSkillsLibraryError(`${skillFile} must declare a canonical lowercase-hyphen name`);
	}
	return name;
}

function validateSkillDirectory(skillDir: string): string {
	const skillFile = join(skillDir, "SKILL.md");
	if (!pathExists(skillFile) || !lstatSync(skillFile).isFile()) {
		throw new RepoSkillsLibraryError(`Repository skill is missing a regular SKILL.md: ${skillDir}`);
	}
	const skillId = parseSkillName(skillFile);
	if (skillId !== basename(skillDir)) {
		throw new RepoSkillsLibraryError(`${skillFile} name must match directory basename ${basename(skillDir)}`);
	}
	return skillId;
}

function loadRepositoryIndex(repoSkillsRoot: string): Set<string> {
	const indexPath = join(repoSkillsRoot, "repository-index.jsonl");
	if (!pathExists(indexPath) || !lstatSync(indexPath).isFile()) {
		throw new RepoSkillsLibraryError(`Source repo-skills is missing ${indexPath}`);
	}
	const skillIds = new Set<string>();
	const repoIds = new Set<string>();
	const caseFoldedRepoIds = new Map<string, string>();
	for (const [lineIndex, line] of readFileSync(indexPath, "utf8").split(/\r?\n/).filter(Boolean).entries()) {
		let value: unknown;
		try {
			value = JSON.parse(line);
		} catch (error) {
			throw new RepoSkillsLibraryError(`Invalid repository-index.jsonl line ${lineIndex + 1}: ${error instanceof Error ? error.message : String(error)}`);
		}
		if (!value || typeof value !== "object" || Array.isArray(value)) {
			throw new RepoSkillsLibraryError(`Invalid repository-index.jsonl record ${lineIndex + 1}`);
		}
		const record = value as Record<string, unknown>;
		const unknownField = Object.keys(record).find((key) => !REPOSITORY_INDEX_FIELDS.has(key));
		const legacyRepoId = record.legacy_repo_id;
		const normalizedSourceUrl = typeof record.source_url === "string"
			? record.source_url.replace(/\/+$/, "").replace(/\.git$/i, "")
			: "";
		const sourceMatch = normalizedSourceUrl.match(/^https:\/\/github\.com\/([^/]+)\/([^/]+)$/i);
		if (
			unknownField ||
			record.schema_version !== 1 ||
			typeof record.repo_id !== "string" ||
			!/^[^/\s]+\/[^/\s]+$/.test(record.repo_id) ||
			record.repo_name !== record.repo_id.split("/").at(-1) ||
			typeof record.skill_id !== "string" ||
			!CANONICAL_SKILL_ID.test(record.skill_id) ||
			!sourceMatch ||
			`${sourceMatch[1]}/${sourceMatch[2]}`.toLowerCase() !== record.repo_id.toLowerCase() ||
			!(legacyRepoId === null || (typeof legacyRepoId === "string" && legacyRepoId.trim().length > 0)) ||
			!(record.source_commit === null || (typeof record.source_commit === "string" && /^[0-9a-f]{40}$/i.test(record.source_commit))) ||
			!(record.source_skill_root === null || (typeof record.source_skill_root === "string" && record.source_skill_root.trim() && !isAbsolute(record.source_skill_root))) ||
			record.target_skill_root !== `repo-skills/${record.skill_id}`
			|| !Array.isArray(record.aliases) || record.aliases.some((alias) => typeof alias !== "string")
			|| typeof record.content_sha256 !== "string" || !/^sha256:[0-9a-f]{64}$/i.test(record.content_sha256)
			|| typeof record.description !== "string" || !record.description.trim()
		) {
			throw new RepoSkillsLibraryError(`Invalid repository-index.jsonl identity at line ${lineIndex + 1}${unknownField ? ` (unknown field ${unknownField})` : ""}`);
		}
		if (skillIds.has(record.skill_id)) throw new RepoSkillsLibraryError(`Duplicate skill_id in repository-index.jsonl: ${record.skill_id}`);
		const foldedRepoId = record.repo_id.toLowerCase();
		if (repoIds.has(record.repo_id) || caseFoldedRepoIds.has(foldedRepoId)) throw new RepoSkillsLibraryError(`Duplicate repo_id in repository-index.jsonl: ${record.repo_id}`);
		skillIds.add(record.skill_id);
		repoIds.add(record.repo_id);
		caseFoldedRepoIds.set(foldedRepoId, record.repo_id);
	}
	if (skillIds.size === 0) throw new RepoSkillsLibraryError("repository-index.jsonl must contain at least one repository skill");
	return skillIds;
}

function inventorySource(libraryRoot: string): SourceInventory {
	const repoSkillsRoot = join(libraryRoot, "repo-skills");
	const routerDir = join(libraryRoot, ROUTER_ID);
	if (!pathExists(repoSkillsRoot) || !lstatSync(repoSkillsRoot).isDirectory()) {
		throw new RepoSkillsLibraryError(`Source snapshot is missing ${LIBRARY_PATH}/repo-skills`);
	}
	if (!pathExists(routerDir) || !lstatSync(routerDir).isDirectory()) {
		throw new RepoSkillsLibraryError(`Source snapshot is missing ${LIBRARY_PATH}/${ROUTER_ID}`);
	}
	if (parseSkillName(join(routerDir, "SKILL.md")) !== ROUTER_ID) {
		throw new RepoSkillsLibraryError("Source router SKILL.md has the wrong name");
	}
	const indexedSkillIds = loadRepositoryIndex(repoSkillsRoot);
	const managedSkills = new Map<string, ManagedTreeState>();
	const lowerCaseIds = new Map<string, string>();
	const managedRootFiles = new Map<string, string>();
	for (const entry of readdirSync(repoSkillsRoot, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
		const entryPath = join(repoSkillsRoot, entry.name);
		if (entry.isSymbolicLink()) {
			throw new RepoSkillsLibraryError(`Source repo-skills contains a symbolic link: ${entryPath}`);
		}
		if (entry.isFile()) {
			managedRootFiles.set(entry.name, digestFile(entryPath));
			continue;
		}
		if (!entry.isDirectory()) {
			throw new RepoSkillsLibraryError(`Source repo-skills contains a non-portable entry: ${entryPath}`);
		}
		if (!indexedSkillIds.has(entry.name)) {
			throw new RepoSkillsLibraryError(
				`repository-index.jsonl does not cover direct repository skill directory: ${entryPath}`,
			);
		}
		const skillId = validateSkillDirectory(entryPath);
		const lower = skillId.toLowerCase();
		const previous = lowerCaseIds.get(lower);
		if (previous && previous !== skillId) {
			throw new RepoSkillsLibraryError(`Source skill IDs collide on case-insensitive filesystems: ${previous}, ${skillId}`);
		}
		lowerCaseIds.set(lower, skillId);
		const digest = digestTree(entryPath);
		managedSkills.set(skillId, { digest: digest.digest, fileCount: digest.fileCount });
	}
	for (const skillId of indexedSkillIds) {
		if (!managedSkills.has(skillId)) throw new RepoSkillsLibraryError(`repository-index.jsonl references missing skill directory: ${skillId}`);
	}
	if (managedSkills.size === 0) {
		throw new RepoSkillsLibraryError("Source snapshot does not contain any repository skills");
	}
	const routerDigest = digestTree(routerDir).digest;
	return { libraryRoot, repoSkillsRoot, routerDir, managedSkills, managedRootFiles, routerDigest };
}

function assertState(value: unknown, statePath: string): RepoSkillsLibraryState {
	if (!value || typeof value !== "object" || Array.isArray(value)) {
		throw new RepoSkillsLibraryError(`Managed repository skill state must be a JSON object: ${statePath}`);
	}
	const state = value as Partial<RepoSkillsLibraryState>;
	if (state.schemaVersion !== STATE_SCHEMA_VERSION) {
		throw new RepoSkillsLibraryError(`Unsupported repository skill state schema in ${statePath}`);
	}
	if (
		!state.source ||
		typeof state.source.repository !== "string" ||
		state.source.ref !== "HEAD" ||
		!/^[0-9a-fA-F]{40}$/.test(state.source.commit)
	) {
		throw new RepoSkillsLibraryError(`Invalid source metadata in ${statePath}`);
	}
	if (!state.managedSkills || typeof state.managedSkills !== "object" || Array.isArray(state.managedSkills)) {
		throw new RepoSkillsLibraryError(`Invalid managedSkills map in ${statePath}`);
	}
	for (const [skillId, entry] of Object.entries(state.managedSkills)) {
		if (
			!CANONICAL_SKILL_ID.test(skillId) ||
			!entry ||
			typeof entry.digest !== "string" ||
			!Number.isInteger(entry.fileCount) ||
			entry.fileCount < 1
		) {
			throw new RepoSkillsLibraryError(`Invalid managed skill entry ${skillId} in ${statePath}`);
		}
	}
	if (!state.managedRootFiles || typeof state.managedRootFiles !== "object" || Array.isArray(state.managedRootFiles)) {
		throw new RepoSkillsLibraryError(`Invalid managedRootFiles map in ${statePath}`);
	}
	for (const [relativePath, digest] of Object.entries(state.managedRootFiles)) {
		if (
			!relativePath ||
			relativePath === "." ||
			relativePath === ".." ||
			basename(relativePath) !== relativePath ||
			typeof digest !== "string"
		) {
			throw new RepoSkillsLibraryError(`Invalid managed root file entry ${relativePath} in ${statePath}`);
		}
	}
	if (typeof state.installedAt !== "string" || typeof state.updatedAt !== "string") {
		throw new RepoSkillsLibraryError(`Invalid timestamps in ${statePath}`);
	}
	if (typeof state.sourceRouterDigest !== "string") {
		throw new RepoSkillsLibraryError(`Invalid source router digest in ${statePath}`);
	}
	if (typeof state.liveTreeDigest !== "string") {
		throw new RepoSkillsLibraryError(`Invalid live tree digest in ${statePath}`);
	}
	if (state.liveRouterDigest !== undefined && typeof state.liveRouterDigest !== "string") {
		throw new RepoSkillsLibraryError(`Invalid live router digest in ${statePath}`);
	}
	return state as RepoSkillsLibraryState;
}

function readState(statePath: string): RepoSkillsLibraryState | undefined {
	if (!pathExists(statePath)) return undefined;
	try {
		return assertState(JSON.parse(readFileSync(statePath, "utf8")), statePath);
	} catch (error) {
		if (error instanceof RepoSkillsLibraryError) throw error;
		throw new RepoSkillsLibraryError(
			`Could not read managed repository skill state ${statePath}: ${error instanceof Error ? error.message : String(error)}`,
		);
	}
}

function stateFromInventory(
	inventory: SourceInventory,
	commit: string,
	repository: string,
	now: Date,
	previous: RepoSkillsLibraryState | undefined,
	liveTreeDigest: string,
	liveRouterDigest: string,
): RepoSkillsLibraryState {
	return {
		schemaVersion: STATE_SCHEMA_VERSION,
		source: { repository, ref: "HEAD", commit },
		installedAt: previous?.installedAt ?? now.toISOString(),
		updatedAt: now.toISOString(),
		managedSkills: Object.fromEntries([...inventory.managedSkills].sort(([left], [right]) => left.localeCompare(right))),
		managedRootFiles: Object.fromEntries(
			[...inventory.managedRootFiles]
				.filter(([relativePath]) => relativePath !== REPOSITORY_INDEX_ROOT_FILE)
				.sort(([left], [right]) => left.localeCompare(right)),
		),
		sourceRouterDigest: inventory.routerDigest,
		liveTreeDigest,
		liveRouterDigest,
	};
}

function parseRouterFrontmatter(routerFile: string): {
	content: string;
	frontmatterEnd: number;
	newline: "\n" | "\r\n";
	document: ReturnType<typeof parseDocument>;
} {
	if (!pathExists(routerFile)) {
		throw new RepoSkillsLibraryError(`Repository skill router is missing ${routerFile}`);
	}
	const routerFileStat = lstatSync(routerFile);
	if (!routerFileStat.isFile() || routerFileStat.isSymbolicLink()) {
		throw new RepoSkillsLibraryError(`Repository skill router must use a regular SKILL.md: ${routerFile}`);
	}
	const content = readFileSync(routerFile, "utf8");
	const match = content.match(/^---(\r?\n)([\s\S]*?)\r?\n---(?:\r?\n|$)/);
	if (!match?.[2]) {
		throw new RepoSkillsLibraryError(`${routerFile} is missing YAML frontmatter`);
	}
	const document = parseDocument(match[2], { keepSourceTokens: true });
	if (document.errors.length > 0) {
		throw new RepoSkillsLibraryError(`${routerFile} has invalid YAML frontmatter: ${document.errors[0]?.message}`);
	}
	const value = document.toJS() as unknown;
	if (!value || typeof value !== "object" || Array.isArray(value)) {
		throw new RepoSkillsLibraryError(`${routerFile} frontmatter must be a mapping`);
	}
	if ((value as Record<string, unknown>).name !== ROUTER_ID) {
		throw new RepoSkillsLibraryError(`${routerFile} frontmatter name must be ${ROUTER_ID}`);
	}
	return {
		content,
		frontmatterEnd: match[0].length,
		newline: match[1] as "\n" | "\r\n",
		document,
	};
}

function assertRouterDirectory(routerDir: string): void {
	const routerStat = lstatSync(routerDir);
	if (!routerStat.isDirectory() || routerStat.isSymbolicLink()) {
		throw new RepoSkillsLibraryError(`Repository skill router must be a real directory: ${routerDir}`);
	}
}

function digestRouterTree(routerDir: string): string {
	assertRouterDirectory(routerDir);
	const hash = createHash("sha256");
	for (const file of collectPortableFiles(routerDir)) {
		const relativePath = toPosix(relative(routerDir, file));
		const stat = lstatSync(file);
		let content = readFileSync(file);
		if (relativePath === "SKILL.md") {
			const parsed = parseRouterFrontmatter(file);
			const frontmatter = parsed.document.toJS() as Record<string, unknown>;
			delete frontmatter["disable-model-invocation"];
			content = Buffer.from(
				`${JSON.stringify(sortJsonValue(frontmatter))}\n${parsed.content.slice(parsed.frontmatterEnd)}`,
				"utf8",
			);
		}
		hash.update(`file\0${relativePath}\0${stat.mode & 0o111}\0${content.byteLength}\0`);
		hash.update(content);
		hash.update("\0");
	}
	return `sha256:${hash.digest("hex")}`;
}

function routerCoverageIssues(routerDir: string, expectedSkillIds: Set<string>, liveSkills: Map<string, ManagedTreeState>): string[] {
	const indexDir = join(routerDir, ROUTER_INDEX_PATH);
	const repositoriesFile = join(indexDir, "repositories.jsonl");
	const assignmentsFile = join(indexDir, "assignments.jsonl");
	const buildMetadataFile = join(indexDir, "build-metadata.json");
	const taxonomyFile = join(indexDir, "taxonomy.json");
	const issues: string[] = [];
	if (!pathExists(indexDir) || !lstatSync(indexDir).isDirectory()) return ["repo-skills-router is missing references/index"];
	if (!pathExists(repositoriesFile)) issues.push("repo-skills-router is missing references/index/repositories.jsonl");
	if (!pathExists(assignmentsFile)) issues.push("repo-skills-router is missing references/index/assignments.jsonl");
	if (!pathExists(buildMetadataFile)) issues.push("repo-skills-router is missing references/index/build-metadata.json");
	if (!pathExists(taxonomyFile)) issues.push("repo-skills-router is missing references/index/taxonomy.json");
	if (issues.length > 0) return issues;
	const covered = new Set<string>();
	const repoIds = new Set<string>();
	const caseFoldedRepoIds = new Map<string, string>();
	const repositoryBySkill = new Map<string, string>();
	const legacyRepositoryBySkill = new Map<string, string | null>();
	let assignmentCount = 0;
	for (const [lineIndex, line] of readFileSync(repositoriesFile, "utf8").split(/\r?\n/).filter(Boolean).entries()) {
		try {
			const record = JSON.parse(line) as Record<string, unknown>;
			const unknownField = Object.keys(record).find((key) => !REPOSITORY_INDEX_FIELDS.has(key));
			const normalizedSourceUrl = typeof record.source_url === "string"
				? record.source_url.replace(/\/+$/, "").replace(/\.git$/i, "")
				: "";
			const sourceMatch = normalizedSourceUrl.match(/^https:\/\/github\.com\/([^/]+)\/([^/]+)$/i);
			const sourceSkillRoot = typeof record.source_skill_root === "string" ? record.source_skill_root : undefined;
			const legacyRepoId = record.legacy_repo_id;
			const contentSha256 = typeof record.content_sha256 === "string" ? record.content_sha256 : "";
			if (
				unknownField ||
				record.schema_version !== 1 ||
				typeof record.skill_id !== "string" ||
				!CANONICAL_SKILL_ID.test(record.skill_id) ||
				typeof record.repo_id !== "string" ||
				!/^[^/\s]+\/[^/\s]+$/.test(record.repo_id) ||
				record.repo_name !== record.repo_id.split("/").at(-1) ||
				!sourceMatch ||
				`${sourceMatch[1]}/${sourceMatch[2]}`.toLowerCase() !== record.repo_id.toLowerCase() ||
				!(legacyRepoId === null || (typeof legacyRepoId === "string" && legacyRepoId.trim().length > 0)) ||
				!(record.source_commit === null || (typeof record.source_commit === "string" && /^[0-9a-f]{40}$/i.test(record.source_commit))) ||
				!(record.source_skill_root === null || (typeof record.source_skill_root === "string" && record.source_skill_root.trim() && !isAbsolute(record.source_skill_root))) ||
				record.target_skill_root !== `repo-skills/${record.skill_id}` ||
				(sourceSkillRoot !== undefined && (!sourceSkillRoot || isAbsolute(sourceSkillRoot))) ||
				!Array.isArray(record.aliases) || record.aliases.some((alias) => typeof alias !== "string") ||
				!/^sha256:[0-9a-f]{64}$/i.test(contentSha256) ||
				typeof record.description !== "string" || !record.description.trim()
			) throw new Error("missing or invalid repository identity fields");
			if (covered.has(record.skill_id)) throw new Error(`duplicate skill_id ${record.skill_id}`);
			const foldedRepoId = record.repo_id.toLowerCase();
			if (repoIds.has(record.repo_id) || caseFoldedRepoIds.has(foldedRepoId)) throw new Error(`duplicate repo_id ${record.repo_id}`);
			covered.add(record.skill_id);
			repoIds.add(record.repo_id);
			caseFoldedRepoIds.set(foldedRepoId, record.repo_id);
			repositoryBySkill.set(record.skill_id, record.repo_id);
			legacyRepositoryBySkill.set(record.skill_id, legacyRepoId);
			const liveSkillRoot = join(dirname(routerDir), "repo-skills", record.skill_id);
			if (contentSha256.toLowerCase() !== digestRepositorySkillContent(liveSkillRoot).toLowerCase()) {
				throw new Error(`content_sha256 does not match live skill ${record.skill_id}`);
			}
		} catch (error) {
			issues.push(`invalid repository index line ${lineIndex + 1}: ${error instanceof Error ? error.message : String(error)}`);
		}
	}
	const missing = [...expectedSkillIds].filter((skillId) => !covered.has(skillId)).sort();
	const stale = [...covered].filter((skillId) => !liveSkills.has(skillId)).sort();
	if (missing.length > 0) issues.push(`repo-skills-router is missing skill coverage: ${missing.join(", ")}`);
	if (stale.length > 0) issues.push(`repo-skills-router references missing skills: ${stale.join(", ")}`);
	let taxonomyPaths = new Set<string>();
	try {
		if (digestFile(taxonomyFile).toLowerCase() !== `sha256:${CANONICAL_TAXONOMY_SHA256}`) {
			issues.push("repo-skills-router taxonomy content digest is stale");
		}
		const taxonomy = JSON.parse(readFileSync(taxonomyFile, "utf8")) as { areas?: Array<{ name?: unknown; families?: Array<{ name?: unknown }> }> };
		if (!Array.isArray(taxonomy.areas)) throw new Error("taxonomy areas must be an array");
		for (const area of taxonomy.areas) {
			if (typeof area.name !== "string" || !Array.isArray(area.families)) throw new Error("invalid taxonomy area");
			for (const family of area.families) {
				if (typeof family.name !== "string") throw new Error("invalid taxonomy family");
				taxonomyPaths.add(`${area.name}\0${family.name}`);
			}
		}
	} catch (error) {
		issues.push(`invalid repo-skills-router taxonomy: ${error instanceof Error ? error.message : String(error)}`);
	}
	const assignmentKeys = new Set<string>();
	const assignedFamilyPaths = new Set<string>();
	for (const [lineIndex, line] of readFileSync(assignmentsFile, "utf8").split(/\r?\n/).filter(Boolean).entries()) {
		try {
			const record = JSON.parse(line) as Record<string, unknown>;
			const unknownField = Object.keys(record).find((key) => !ASSIGNMENT_INDEX_FIELDS.has(key));
			if (
				unknownField ||
				typeof record.skill_id !== "string" ||
				!covered.has(record.skill_id) ||
				typeof record.repo_id !== "string" ||
				repositoryBySkill.get(record.skill_id) !== record.repo_id ||
				record.legacy_repo_id !== legacyRepositoryBySkill.get(record.skill_id) ||
				typeof record.area !== "string" ||
				typeof record.family !== "string" ||
				!new Set(["high", "medium", "low"]).has(record.confidence as string) ||
				!taxonomyPaths.has(`${record.area}\0${record.family}`)
			) throw new Error("invalid assignment identity or taxonomy path");
			const key = `${record.repo_id}\0${record.area}\0${record.family}`;
			if (assignmentKeys.has(key)) throw new Error(`duplicate assignment ${record.repo_id} -> ${record.area} -> ${record.family}`);
			assignmentKeys.add(key);
			assignedFamilyPaths.add(`${record.area}\0${record.family}`);
			assignmentCount += 1;
		} catch (error) {
			issues.push(`invalid assignment index line ${lineIndex + 1}: ${error instanceof Error ? error.message : String(error)}`);
		}
	}
	const repoSkillsRoot = join(dirname(routerDir), "repo-skills");
	for (const skillId of covered) {
		const metadataFile = join(repoSkillsRoot, skillId, "references", "repo-routing-metadata.json");
		try {
			const metadata = JSON.parse(readFileSync(metadataFile, "utf8")) as Record<string, unknown>;
			const unknownMetadataField = Object.keys(metadata).find((key) => !ROUTING_METADATA_FIELDS.has(key));
			if (unknownMetadataField) throw new Error(`metadata contains unknown field ${unknownMetadataField}`);
			if (metadata.schema_version !== "2.0" || metadata.skill_id !== skillId || metadata.repo_id !== repositoryBySkill.get(skillId)) {
				throw new Error("metadata identity does not match repository index");
			}
			if (metadata.taxonomy_sha256 !== CANONICAL_TAXONOMY_SHA256) {
				throw new Error("metadata taxonomy hash is stale");
			}
			const metadataAssignments = metadata.assignments;
			if (!Array.isArray(metadataAssignments)) throw new Error("metadata assignments must be an array");
			if (metadata.routing_status !== "classified" && metadata.routing_status !== "unclassified") {
				throw new Error("metadata routing_status must be classified or unclassified");
			}
			const metadataKeys = new Set<string>();
			for (const [index, assignment] of metadataAssignments.entries()) {
				if (!assignment || typeof assignment !== "object" || Array.isArray(assignment)) {
					throw new Error(`metadata assignment ${index} is invalid`);
				}
				const item = assignment as Record<string, unknown>;
				const unknownAssignmentField = Object.keys(item).find((key) => !ROUTING_ASSIGNMENT_FIELDS.has(key));
				if (unknownAssignmentField) {
					throw new Error(`metadata assignment ${index} contains unknown field ${unknownAssignmentField}`);
				}
				if (typeof item.area !== "string" || typeof item.family !== "string") {
					throw new Error(`metadata assignment ${index} requires area and family strings`);
				}
				const key = `${repositoryBySkill.get(skillId)}\0${item.area}\0${item.family}`;
				if (metadataKeys.has(key)) throw new Error(`metadata contains duplicate assignment ${item.area} -> ${item.family}`);
				metadataKeys.add(key);
			}
			const indexKeys = new Set([...assignmentKeys].filter((key) => key.startsWith(`${repositoryBySkill.get(skillId)}\0`)));
			if (metadata.routing_status === "classified" && metadataKeys.size === 0) throw new Error("classified metadata has no assignments");
			if (metadata.routing_status === "unclassified" && (metadataKeys.size !== 0 || typeof metadata.unclassified_reason !== "string" || !metadata.unclassified_reason.trim())) {
				throw new Error("unclassified metadata requires a reason and no assignments");
			}
			if (metadata.routing_status === "classified" && metadata.unclassified_reason !== undefined) throw new Error("classified metadata must not contain unclassified_reason");
			if (metadataKeys.size !== indexKeys.size || [...metadataKeys].some((key) => !indexKeys.has(key))) throw new Error("metadata assignments do not match assignment index");
		} catch (error) {
			issues.push(`invalid routing metadata for ${skillId}: ${error instanceof Error ? error.message : String(error)}`);
		}
	}
	try {
		const metadata = JSON.parse(readFileSync(buildMetadataFile, "utf8")) as Record<string, unknown>;
		const taxonomy = JSON.parse(readFileSync(taxonomyFile, "utf8")) as { areas?: Array<{ families?: unknown[] }> };
		const taxonomyAreaCount = Array.isArray(taxonomy.areas) ? taxonomy.areas.length : 0;
		const taxonomyFamilyCount = Array.isArray(taxonomy.areas)
			? taxonomy.areas.reduce((count, area) => count + (Array.isArray(area.families) ? area.families.length : 0), 0)
			: 0;
		if (metadata.schema_version !== 1) issues.push("repo-skills-router build metadata schema_version is invalid");
		if (metadata.repository_count !== covered.size) issues.push("repo-skills-router build metadata repository_count is stale");
		if (metadata.assignment_count !== assignmentCount) issues.push("repo-skills-router build metadata assignment_count is stale");
		if (metadata.area_count !== taxonomyAreaCount) issues.push("repo-skills-router build metadata area_count is stale");
		if (metadata.family_count !== taxonomyFamilyCount) issues.push("repo-skills-router build metadata family_count is stale");
		if (metadata.non_empty_family_count !== assignedFamilyPaths.size) issues.push("repo-skills-router build metadata non_empty_family_count is stale");
		if (metadata.taxonomy_sha256 !== CANONICAL_TAXONOMY_SHA256) issues.push("repo-skills-router build metadata taxonomy hash is stale");
		if (metadata.repository_index_sha256 !== digestFile(repositoriesFile)) issues.push("repo-skills-router repository index digest is stale");
		if (metadata.assignment_index_sha256 !== digestFile(assignmentsFile)) issues.push("repo-skills-router assignment index digest is stale");
		const repositoryRootIndex = join(dirname(routerDir), "repo-skills", "repository-index.jsonl");
		if (!pathExists(repositoryRootIndex)) {
			issues.push("repo-skills is missing repository-index.jsonl");
		} else if (digestFile(repositoryRootIndex) !== digestFile(repositoriesFile)) {
			issues.push("repo-skills repository-index.jsonl differs from router repository index");
		}
	} catch (error) {
		issues.push(`invalid repo-skills-router build metadata: ${error instanceof Error ? error.message : String(error)}`);
	}
	return issues;
}

function routerBuildCounts(routerDir: string): { repositoryCount: number; assignmentCount: number; areaCount: number; familyCount: number } | undefined {
	const buildFile = join(routerDir, ROUTER_INDEX_PATH, "build-metadata.json");
	if (!pathExists(buildFile)) return undefined;
	try {
		const value = JSON.parse(readFileSync(buildFile, "utf8")) as Record<string, unknown>;
		if (!["repository_count", "assignment_count", "area_count", "family_count"].every((key) => Number.isInteger(value[key]))) return undefined;
		return {
			repositoryCount: value.repository_count as number,
			assignmentCount: value.assignment_count as number,
			areaCount: value.area_count as number,
			familyCount: value.family_count as number,
		};
	} catch {
		return undefined;
	}
}

function routerEnabled(routerDir: string): boolean | undefined {
	if (!pathExists(routerDir)) return undefined;
	assertRouterDirectory(routerDir);
	const routerFile = join(routerDir, "SKILL.md");
	if (!pathExists(routerFile)) return undefined;
	const { document } = parseRouterFrontmatter(routerFile);
	const value = document.toJS() as Record<string, unknown>;
	if (!("disable-model-invocation" in value)) return true;
	if (value["disable-model-invocation"] !== true) {
		throw new RepoSkillsLibraryError(`${routerFile} disable-model-invocation must be true when present`);
	}
	return false;
}

function writeRouterEnabled(routerDir: string, enabled: boolean): boolean {
	if (pathExists(routerDir)) assertRouterDirectory(routerDir);
	const routerFile = join(routerDir, "SKILL.md");
	if (!pathExists(routerFile)) {
		throw new RepoSkillsLibraryError(
			`Repository skill router is not installed at ${routerFile}. Run "disco repo-skills install" first.`,
			2,
		);
	}
	const parsed = parseRouterFrontmatter(routerFile);
	const currentValue = parsed.document.toJS() as Record<string, unknown>;
	if (
		"disable-model-invocation" in currentValue &&
		currentValue["disable-model-invocation"] !== true
	) {
		throw new RepoSkillsLibraryError(`${routerFile} disable-model-invocation must be true when present`);
	}
	const currentlyEnabled = !("disable-model-invocation" in currentValue);
	if (currentlyEnabled === enabled) return false;
	if (enabled) {
		parsed.document.delete("disable-model-invocation");
	} else {
		parsed.document.set("disable-model-invocation", true);
	}
	const serialized = parsed.document.toString({ lineWidth: 0 }).trimEnd().replace(/\n/g, parsed.newline);
	const body = parsed.content.slice(parsed.frontmatterEnd);
	const next = `---${parsed.newline}${serialized}${parsed.newline}---${parsed.newline}${body}`;
	const temporary = `${routerFile}.tmp.${process.pid}.${Date.now()}`;
	try {
		writeFileSync(temporary, next, "utf8");
		renameSync(temporary, routerFile);
	} finally {
		rmSync(temporary, { force: true });
	}
	return true;
}

function copyDirectory(source: string, destination: string): void {
	cpSync(source, destination, { recursive: true, errorOnExist: true, force: false, verbatimSymlinks: true });
}

function listLiveSkillTrees(repoSkillsRoot: string): Map<string, ManagedTreeState> {
	const result = new Map<string, ManagedTreeState>();
	if (!pathExists(repoSkillsRoot)) return result;
	const rootStat = lstatSync(repoSkillsRoot);
	if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) {
		throw new RepoSkillsLibraryError(`Live repo-skills path must be a real directory: ${repoSkillsRoot}`);
	}
	const caseMap = new Map<string, string>();
	for (const entry of readdirSync(repoSkillsRoot, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name))) {
		if (entry.isSymbolicLink()) {
			throw new RepoSkillsLibraryError(`Live repo-skills contains a symbolic link: ${join(repoSkillsRoot, entry.name)}`);
		}
		if (!entry.isDirectory()) continue;
		const skillDir = join(repoSkillsRoot, entry.name);
		if (!pathExists(join(skillDir, "SKILL.md"))) continue;
		const skillId = validateSkillDirectory(skillDir);
		const lower = skillId.toLowerCase();
		const previous = caseMap.get(lower);
		if (previous && previous !== skillId) {
			throw new RepoSkillsLibraryError(`Live skill IDs collide on case-insensitive filesystems: ${previous}, ${skillId}`);
		}
		caseMap.set(lower, skillId);
		const digest = digestTree(skillDir);
		result.set(skillId, { digest: digest.digest, fileCount: digest.fileCount });
	}
	return result;
}

function rootFileDigest(repoSkillsRoot: string, relativePath: string): string | undefined {
	const target = resolve(repoSkillsRoot, relativePath);
	if (!isWithin(repoSkillsRoot, target) || !pathExists(target)) return undefined;
	return digestFile(target);
}

export class RepoSkillsLibraryManager {
	private readonly agentDir: string;
	private readonly sourceRepository: string;
	private readonly gitCommand: string;
	private readonly bundledSkillsDir: string;
	private readonly offline: boolean;
	private readonly now: () => Date;
	private readonly env: NodeJS.ProcessEnv;
	private readonly transactionFaultInjector?: (point: RepoSkillsTransactionPoint) => void;

	constructor(options: RepoSkillsLibraryManagerOptions = {}) {
		this.agentDir = resolve(options.agentDir ?? getAgentDir());
		this.sourceRepository = options.sourceRepository ?? OFFICIAL_REPOSITORY;
		this.gitCommand = options.gitCommand ?? "git";
		this.bundledSkillsDir = resolve(options.bundledSkillsDir ?? getBundledSkillsDir());
		this.env = options.env ?? process.env;
		this.offline = options.offline ?? isTruthyEnvironmentFlag(this.env.DISCO_OFFLINE);
		this.now = options.now ?? (() => new Date());
		this.transactionFaultInjector = options.transactionFaultInjector;
	}

	private get skillsRoot(): string {
		return join(this.agentDir, "skills", "repositories");
	}

	private get repoSkillsRoot(): string {
		return join(this.skillsRoot, "repo-skills");
	}

	private get routerDir(): string {
		return join(this.skillsRoot, ROUTER_ID);
	}

	private get statePath(): string {
		return join(this.agentDir, "repo-skills-library.json");
	}

	private get liveLockPath(): string {
		return join(this.agentDir, "locks", "repo-skills-import.lockdir");
	}

	private get sourceLockPath(): string {
		return join(this.agentDir, "locks", "repo-skills-source.lockdir");
	}

	private get sourceCacheDir(): string {
		return join(this.agentDir, "cache", "repo-skills-source");
	}

	private async git(args: string[]): Promise<ProcessResult> {
		return runProcess(this.gitCommand, args, { env: this.env });
	}

	private async cloneSource(destination: string): Promise<void> {
		const partialArgs = [
			"clone",
			"--depth",
			"1",
			"--filter=blob:none",
			"--sparse",
			"--no-tags",
			this.sourceRepository,
			destination,
		];
		let result: ProcessResult;
		try {
			result = await this.git(partialArgs);
		} catch (error) {
			throw new RepoSkillsLibraryError(
				`Git is required to install repository skills. ${error instanceof Error ? error.message : String(error)}\nManual fallback: ${MANUAL_INSTALL_URL}`,
			);
		}
		if (result.code === 0) {
			const sparse = await this.git(["-C", destination, "sparse-checkout", "set", LIBRARY_PATH]);
			if (sparse.code === 0) return;
		}
		rmSync(destination, { recursive: true, force: true });
		const fallback = await this.git([
			"clone",
			"--depth",
			"1",
			"--no-tags",
			this.sourceRepository,
			destination,
		]);
		if (fallback.code !== 0) {
			throw new RepoSkillsLibraryError(
				`Could not clone the official repository skill source: ${shortOutput(fallback.stderr || result.stderr)}`,
			);
		}
	}

	private async refreshSourceCache(): Promise<string> {
		const cacheDir = this.sourceCacheDir;
		let cacheIsRealDirectory = false;
		if (pathExists(cacheDir)) {
			const cacheStat = lstatSync(cacheDir);
			cacheIsRealDirectory = cacheStat.isDirectory() && !cacheStat.isSymbolicLink();
		}
		if (cacheIsRealDirectory && pathExists(join(cacheDir, ".git"))) {
			const remote = await this.git(["-C", cacheDir, "config", "--get", "remote.origin.url"]);
			const fetch =
				remote.code === 0 && remote.stdout.trim() === this.sourceRepository
					? await this.git(["-C", cacheDir, "fetch", "--depth", "1", "--no-tags", "origin", "HEAD"])
					: undefined;
			if (fetch?.code === 0) {
				const reset = await this.git(["-C", cacheDir, "reset", "--hard", "FETCH_HEAD"]);
				const clean = reset.code === 0 ? await this.git(["-C", cacheDir, "clean", "-ffdx"]) : reset;
				if (reset.code === 0 && clean.code === 0) {
					await this.git(["-C", cacheDir, "sparse-checkout", "set", LIBRARY_PATH]);
					const rev = await this.git(["-C", cacheDir, "rev-parse", "HEAD"]);
					if (rev.code === 0 && /^[0-9a-f]{40}$/i.test(rev.stdout.trim())) return rev.stdout.trim();
				}
			}
		}

		mkdirSync(dirname(cacheDir), { recursive: true });
		const freshCache = `${cacheDir}.tmp.${process.pid}.${Date.now()}`;
		const oldCache = `${cacheDir}.old.${process.pid}.${Date.now()}`;
		rmSync(freshCache, { recursive: true, force: true });
		try {
			await this.cloneSource(freshCache);
		} catch (error) {
			rmSync(freshCache, { recursive: true, force: true });
			throw error;
		}
		const rev = await this.git(["-C", freshCache, "rev-parse", "HEAD"]);
		if (rev.code !== 0 || !/^[0-9a-f]{40}$/i.test(rev.stdout.trim())) {
			rmSync(freshCache, { recursive: true, force: true });
			throw new RepoSkillsLibraryError(`Could not resolve source commit: ${shortOutput(rev.stderr)}`);
		}
		try {
			if (pathExists(cacheDir)) renameSync(cacheDir, oldCache);
			renameSync(freshCache, cacheDir);
			rmSync(oldCache, { recursive: true, force: true });
		} catch (error) {
			if (!pathExists(cacheDir) && pathExists(oldCache)) renameSync(oldCache, cacheDir);
			rmSync(freshCache, { recursive: true, force: true });
			throw error;
		}
		return rev.stdout.trim();
	}

	private async prepareSourceSnapshot(): Promise<SourceSnapshot> {
		this.assertOnline();
		return withDirectoryLock(this.sourceLockPath, async () => {
			const commit = await this.refreshSourceCache();
			const sourceLibrary = join(this.sourceCacheDir, LIBRARY_PATH);
			if (!pathExists(sourceLibrary)) {
				throw new RepoSkillsLibraryError(`Source checkout is missing ${LIBRARY_PATH}`);
			}
			const snapshotsRoot = join(this.agentDir, "cache", "repo-skills-snapshots");
			mkdirSync(snapshotsRoot, { recursive: true });
			const snapshotRoot = mkdtempSync(join(snapshotsRoot, "snapshot-"));
			const libraryRoot = join(snapshotRoot, LIBRARY_PATH);
			copyDirectory(sourceLibrary, libraryRoot);
			return {
				commit,
				libraryRoot,
				cleanup: () => rmSync(snapshotRoot, { recursive: true, force: true }),
			};
		});
	}

	private assertOnline(): void {
		if (!this.offline) return;
		throw new RepoSkillsLibraryError(
			"Repository skill install/update is unavailable in offline mode. Re-run without --offline or DISCO_OFFLINE.",
			2,
		);
	}

	private async runRouterUpdater(
		libraryRoot: string,
		visibility: "preserve" | "enabled" | "disabled",
		templateDir?: string,
	): Promise<void> {
		const updater = join(this.bundledSkillsDir, "verify-repo-skill", "scripts", "update_repo_skills_router.mjs");
		if (!pathExists(updater)) {
			throw new RepoSkillsLibraryError(`Bundled repo-skills-router updater not found: ${updater}`);
		}
		const args = [
			updater,
			"--library-root",
			libraryRoot,
			"--router-visibility",
			visibility,
		];
		if (templateDir) args.push("--template-dir", templateDir);
		const result = await runProcess(process.execPath, args, { env: this.env });
		if (result.code !== 0) {
			throw new RepoSkillsLibraryError(
				`Repository skill router validation failed: ${shortOutput(result.stderr || result.stdout)}`,
			);
		}
	}

	private detectConflicts(
		state: RepoSkillsLibraryState | undefined,
		inventory: SourceInventory,
		liveSkills: Map<string, ManagedTreeState>,
	): string[] {
		const conflicts: string[] = [];
		for (const [skillId, desired] of inventory.managedSkills) {
			const current = liveSkills.get(skillId);
			if (!current) {
				if (pathExists(join(this.repoSkillsRoot, skillId))) {
					conflicts.push(`${skillId}: live path is not a valid repository skill directory`);
				} else if (state?.managedSkills[skillId]) {
					conflicts.push(`${skillId}: managed skill is missing locally`);
				}
				continue;
			}
			const previous = state?.managedSkills[skillId];
			if (!previous) {
				if (current.digest !== desired.digest) conflicts.push(`${skillId}: local skill uses an official skill ID`);
				continue;
			}
			if (current.digest !== previous.digest && current.digest !== desired.digest) {
				conflicts.push(`${skillId}: managed skill has local modifications`);
			}
		}
		if (state) {
			for (const [skillId, previous] of Object.entries(state.managedSkills)) {
				if (inventory.managedSkills.has(skillId)) continue;
				const current = liveSkills.get(skillId);
				const livePath = join(this.repoSkillsRoot, skillId);
				if (!current && pathExists(livePath)) {
					conflicts.push(`${skillId}: locally changed managed skill was removed upstream`);
				} else if (current && current.digest !== previous.digest) {
					conflicts.push(`${skillId}: locally modified managed skill was removed upstream`);
				}
			}
		}
		for (const [relativePath, desiredDigest] of inventory.managedRootFiles) {
			if (relativePath === REPOSITORY_INDEX_ROOT_FILE) continue;
			let currentDigest: string | undefined;
			try {
				currentDigest = rootFileDigest(this.repoSkillsRoot, relativePath);
			} catch {
				conflicts.push(`${relativePath}: local root path conflicts with the official collection`);
				continue;
			}
			if (!currentDigest) {
				if (state?.managedRootFiles[relativePath]) conflicts.push(`${relativePath}: managed root file is missing locally`);
				continue;
			}
			const previousDigest = state?.managedRootFiles[relativePath];
			if (!previousDigest && currentDigest !== desiredDigest) {
				conflicts.push(`${relativePath}: local root file conflicts with the official collection`);
			} else if (previousDigest && currentDigest !== previousDigest && currentDigest !== desiredDigest) {
				conflicts.push(`${relativePath}: managed root file has local modifications`);
			}
		}
		if (state) {
			for (const [relativePath, previousDigest] of Object.entries(state.managedRootFiles)) {
				if (relativePath === REPOSITORY_INDEX_ROOT_FILE) continue;
				if (inventory.managedRootFiles.has(relativePath)) continue;
				let currentDigest: string | undefined;
				try {
					currentDigest = rootFileDigest(this.repoSkillsRoot, relativePath);
				} catch {
					conflicts.push(`${relativePath}: locally changed managed root path was removed upstream`);
					continue;
				}
				if (currentDigest && currentDigest !== previousDigest) {
					conflicts.push(`${relativePath}: locally modified managed root file was removed upstream`);
				}
			}
		}
		return conflicts.sort();
	}

	private applyInventoryToStage(
		stagedRepoSkills: string,
		state: RepoSkillsLibraryState | undefined,
		inventory: SourceInventory,
	): void {
		mkdirSync(stagedRepoSkills, { recursive: true });
		for (const skillId of Object.keys(state?.managedSkills ?? {})) {
			if (!inventory.managedSkills.has(skillId)) {
				rmSync(join(stagedRepoSkills, skillId), { recursive: true, force: true });
			}
		}
		for (const skillId of inventory.managedSkills.keys()) {
			const target = join(stagedRepoSkills, skillId);
			rmSync(target, { recursive: true, force: true });
			copyDirectory(join(inventory.repoSkillsRoot, skillId), target);
		}
		for (const relativePath of Object.keys(state?.managedRootFiles ?? {})) {
			if (!inventory.managedRootFiles.has(relativePath)) {
				rmSync(join(stagedRepoSkills, relativePath), { recursive: true, force: true });
			}
		}
		for (const relativePath of inventory.managedRootFiles.keys()) {
			const target = join(stagedRepoSkills, relativePath);
			mkdirSync(dirname(target), { recursive: true });
			rmSync(target, { recursive: true, force: true });
			cpSync(join(inventory.repoSkillsRoot, relativePath), target, { force: true });
		}
	}

	private readLocalRoutingRows(
		stagedSkillsRoot: string,
		inventory: SourceInventory,
	): { repositories: Array<Record<string, unknown>>; assignments: Array<Record<string, unknown>> } {
		const stagedRepoSkills = join(stagedSkillsRoot, "repo-skills");
		const stagedRouter = join(stagedSkillsRoot, ROUTER_ID);
		const officialSkillIds = new Set(inventory.managedSkills.keys());
		const repositories = readJsonLines(join(stagedRepoSkills, "repository-index.jsonl"))
			.filter((record) => typeof record.skill_id === "string" && !officialSkillIds.has(record.skill_id));
		const localSkillIds = new Set(repositories.map((record) => record.skill_id as string));
		const assignments = readJsonLines(join(stagedRouter, ROUTER_INDEX_PATH, "assignments.jsonl"))
			.filter((record) => typeof record.skill_id === "string" && localSkillIds.has(record.skill_id));
		return { repositories, assignments };
	}

	private mergeLocalRoutingRows(
		stagedSkillsRoot: string,
		inventory: SourceInventory,
		localRoutingRows: { repositories: Array<Record<string, unknown>>; assignments: Array<Record<string, unknown>> },
	): void {
		const stagedRepoSkills = join(stagedSkillsRoot, "repo-skills");
		const stagedRouter = join(stagedSkillsRoot, ROUTER_ID);
		const officialRepositories = readJsonLines(join(inventory.repoSkillsRoot, "repository-index.jsonl"));
		writeJsonLines(join(stagedRepoSkills, "repository-index.jsonl"), [...officialRepositories, ...localRoutingRows.repositories]);
		const officialAssignments = readJsonLines(join(inventory.routerDir, ROUTER_INDEX_PATH, "assignments.jsonl"));
		writeJsonLines(join(stagedRouter, ROUTER_INDEX_PATH, "assignments.jsonl"), [...officialAssignments, ...localRoutingRows.assignments]);
	}

	private swapLiveTree(
		transactionRoot: string,
		stagedRepoSkills: string,
		stagedRouter: string,
		stagedState: string,
		preserveBackup: boolean,
	): string | undefined {
		const backupRoot = join(transactionRoot, "backup");
		const backupRepoSkills = join(backupRoot, "repo-skills");
		const backupRouter = join(backupRoot, ROUTER_ID);
		const backupState = join(backupRoot, "repo-skills-library.json");
		mkdirSync(backupRoot, { recursive: true });
		mkdirSync(this.skillsRoot, { recursive: true });
		const hadRepoSkills = pathExists(this.repoSkillsRoot);
		const hadRouter = pathExists(this.routerDir);
		const hadState = pathExists(this.statePath);
		let installedRepoSkills = false;
		let installedRouter = false;
		let installedState = false;
		try {
			if (hadRepoSkills) renameSync(this.repoSkillsRoot, backupRepoSkills);
			if (hadRouter) renameSync(this.routerDir, backupRouter);
			if (hadState) renameSync(this.statePath, backupState);
			this.transactionFaultInjector?.("before-install-repo-skills");
			renameSync(stagedRepoSkills, this.repoSkillsRoot);
			installedRepoSkills = true;
			this.transactionFaultInjector?.("before-install-router");
			renameSync(stagedRouter, this.routerDir);
			installedRouter = true;
			this.transactionFaultInjector?.("before-install-state");
			renameSync(stagedState, this.statePath);
			installedState = true;
		} catch (error) {
			const rollbackErrors: string[] = [];
			for (const [installed, livePath, backupPath, hadPrevious] of [
				[installedState, this.statePath, backupState, hadState],
				[installedRouter, this.routerDir, backupRouter, hadRouter],
				[installedRepoSkills, this.repoSkillsRoot, backupRepoSkills, hadRepoSkills],
			] as const) {
				try {
					if (installed) rmSync(livePath, { recursive: true, force: true });
					if (hadPrevious && pathExists(backupPath)) {
						const restorePoint =
							livePath === this.statePath
								? "before-restore-state"
								: livePath === this.routerDir
									? "before-restore-router"
									: "before-restore-repo-skills";
						this.transactionFaultInjector?.(restorePoint);
						renameSync(backupPath, livePath);
					}
				} catch (rollbackError) {
					rollbackErrors.push(
						`${livePath}: ${rollbackError instanceof Error ? rollbackError.message : String(rollbackError)}`,
					);
				}
			}
			if (rollbackErrors.length > 0) {
				throw new RepoSkillsLibraryError(
					`${error instanceof Error ? error.message : String(error)}; rollback failed:\n${rollbackErrors.join("\n")}\nRecovery artifacts remain at ${transactionRoot}`,
				);
			}
			rmSync(backupRoot, { recursive: true, force: true });
			throw error;
		}

		if (!preserveBackup || (!hadRepoSkills && !hadRouter && !hadState)) {
			rmSync(backupRoot, { recursive: true, force: true });
			return undefined;
		}
		const backupsRoot = join(this.agentDir, "backups", "repo-skills-library");
		mkdirSync(backupsRoot, { recursive: true });
		const destination = join(backupsRoot, timestampForPath(this.now()));
		try {
			renameSync(backupRoot, destination);
			return destination;
		} catch {
			return backupRoot;
		}
	}

	private async installSnapshot(
		operation: "install" | "update",
		snapshot: SourceSnapshot,
		force: boolean,
	): Promise<RepoSkillsInstallResult> {
		const inventory = inventorySource(snapshot.libraryRoot);
		return withDirectoryLock(this.liveLockPath, async () => {
			const previousState = readState(this.statePath);
			if (operation === "install" && previousState) {
				const status = this.statusUnlocked(previousState);
				return {
					operation,
					commit: status.commit,
					managedSkills: status.managedSkills,
					localSkills: status.localSkills,
					totalSkills: status.totalSkills,
					repositoryCount: status.repositoryCount,
					assignmentCount: status.assignmentCount,
					areaCount: status.areaCount,
					familyCount: status.familyCount,
					routerEnabled: status.routerEnabled,
					noop: true,
					issues: status.issues,
				};
			}
			if (operation === "update" && !previousState) {
				throw new RepoSkillsLibraryError(
					'Repository skills are not managed yet. Run "disco repo-skills install" to install or adopt them first.',
					2,
				);
			}
			const liveSkills = listLiveSkillTrees(this.repoSkillsRoot);
			const conflicts = this.detectConflicts(previousState, inventory, liveSkills);
			if (conflicts.length > 0 && !force) throw new RepoSkillsLibraryConflictError(conflicts);

			let visibility: "enabled" | "disabled" = "enabled";
			const currentRouterEnabled = routerEnabled(this.routerDir);
			if (currentRouterEnabled === false) visibility = "disabled";
			const currentLiveTreeDigest = pathExists(this.repoSkillsRoot) ? digestTree(this.repoSkillsRoot).digest : undefined;
			const currentLiveRouterDigest =
				currentRouterEnabled === undefined ? undefined : digestRouterTree(this.routerDir);
			if (
				operation === "update" &&
				previousState?.source.commit === snapshot.commit &&
				conflicts.length === 0 &&
				currentLiveTreeDigest === previousState.liveTreeDigest &&
				currentLiveRouterDigest === previousState.liveRouterDigest &&
				currentRouterEnabled !== undefined
			) {
				const localSkills = [...liveSkills.keys()].filter((skillId) => !inventory.managedSkills.has(skillId)).length;
				return {
					operation,
					commit: snapshot.commit,
					managedSkills: inventory.managedSkills.size,
					localSkills,
					totalSkills: liveSkills.size,
					repositoryCount: routerBuildCounts(this.routerDir)?.repositoryCount,
					assignmentCount: routerBuildCounts(this.routerDir)?.assignmentCount,
					areaCount: routerBuildCounts(this.routerDir)?.areaCount,
					familyCount: routerBuildCounts(this.routerDir)?.familyCount,
					routerEnabled: currentRouterEnabled,
					noop: true,
					issues: [],
				};
			}
			const transactionRoot = join(
				this.agentDir,
				`.repo-skills-library.${process.pid}.${Date.now()}.${Math.random().toString(36).slice(2)}`,
			);
			const stagedSkillsRoot = join(transactionRoot, "stage", "skills");
			const stagedRepoSkills = join(stagedSkillsRoot, "repo-skills");
			const stagedRouter = join(stagedSkillsRoot, ROUTER_ID);
			const stagedState = join(transactionRoot, "stage", "repo-skills-library.json");
			let preserveTransaction = false;
			try {
				mkdirSync(stagedSkillsRoot, { recursive: true });
				if (pathExists(this.repoSkillsRoot)) copyDirectory(this.repoSkillsRoot, stagedRepoSkills);
				else mkdirSync(stagedRepoSkills, { recursive: true });
				if (pathExists(this.routerDir) && liveSkills.size > 0) {
					copyDirectory(this.routerDir, stagedRouter);
					await this.runRouterUpdater(stagedSkillsRoot, "preserve");
				}
				const localRoutingRows = this.readLocalRoutingRows(stagedSkillsRoot, inventory);
				this.applyInventoryToStage(stagedRepoSkills, previousState, inventory);
				rmSync(stagedRouter, { recursive: true, force: true });
				copyDirectory(inventory.routerDir, stagedRouter);
				this.mergeLocalRoutingRows(stagedSkillsRoot, inventory, localRoutingRows);
				await this.runRouterUpdater(stagedSkillsRoot, visibility, inventory.routerDir);

				for (const [skillId, expected] of inventory.managedSkills) {
					const actual = digestTree(join(stagedRepoSkills, skillId));
					if (actual.digest !== expected.digest) {
						throw new RepoSkillsLibraryError(`Staged official skill changed during validation: ${skillId}`);
					}
				}
				const stagedLiveTreeDigest = digestTree(stagedRepoSkills).digest;
				const stagedLiveRouterDigest = digestRouterTree(stagedRouter);
				const nextState = stateFromInventory(
					inventory,
					snapshot.commit,
					this.sourceRepository,
					this.now(),
					previousState,
					stagedLiveTreeDigest,
					stagedLiveRouterDigest,
				);
				mkdirSync(dirname(stagedState), { recursive: true });
				writeFileSync(stagedState, stableJson(nextState), "utf8");
				const finalSkills = listLiveSkillTrees(stagedRepoSkills);
				const localSkills = [...finalSkills.keys()].filter((skillId) => !inventory.managedSkills.has(skillId)).length;
				const stagedRouterCounts = routerBuildCounts(stagedRouter);
				const backupPath = this.swapLiveTree(
					transactionRoot,
					stagedRepoSkills,
					stagedRouter,
					stagedState,
					force && conflicts.length > 0,
				);
				if (backupPath?.startsWith(transactionRoot)) preserveTransaction = true;
				return {
					operation,
					commit: snapshot.commit,
					managedSkills: inventory.managedSkills.size,
					localSkills,
					totalSkills: finalSkills.size,
					repositoryCount: stagedRouterCounts?.repositoryCount,
					assignmentCount: stagedRouterCounts?.assignmentCount,
					areaCount: stagedRouterCounts?.areaCount,
					familyCount: stagedRouterCounts?.familyCount,
					routerEnabled: visibility === "enabled",
					noop: false,
					backupPath,
					issues: [],
				};
			} catch (error) {
				if (pathExists(join(transactionRoot, "backup"))) preserveTransaction = true;
				throw error;
			} finally {
				if (!preserveTransaction) rmSync(transactionRoot, { recursive: true, force: true });
			}
		});
	}

	async install(options: { force?: boolean } = {}): Promise<RepoSkillsInstallResult> {
		this.assertOnline();
		const existingState = readState(this.statePath);
		if (existingState) {
			const status = this.statusUnlocked(existingState);
			return {
				operation: "install",
				commit: status.commit,
				managedSkills: status.managedSkills,
				localSkills: status.localSkills,
				totalSkills: status.totalSkills,
				routerEnabled: status.routerEnabled,
				noop: true,
				issues: status.issues,
			};
		}
		const snapshot = await this.prepareSourceSnapshot();
		try {
			return await this.installSnapshot("install", snapshot, options.force ?? false);
		} finally {
			snapshot.cleanup();
		}
	}

	async update(options: { force?: boolean } = {}): Promise<RepoSkillsInstallResult> {
		this.assertOnline();
		if (!readState(this.statePath)) {
			throw new RepoSkillsLibraryError(
				'Repository skills are not managed yet. Run "disco repo-skills install" to install or adopt them first.',
				2,
			);
		}
		const snapshot = await this.prepareSourceSnapshot();
		try {
			return await this.installSnapshot("update", snapshot, options.force ?? false);
		} finally {
			snapshot.cleanup();
		}
	}

	async setRouterEnabled(enabled: boolean): Promise<RepoSkillsRouterToggleResult> {
		return withDirectoryLock(this.liveLockPath, async () => {
			const changed = writeRouterEnabled(this.routerDir, enabled);
			return { enabled, changed };
		});
	}

	private statusUnlocked(state: RepoSkillsLibraryState | undefined): RepoSkillsLibraryStatus {
		const issues: string[] = [];
		let liveSkills = new Map<string, ManagedTreeState>();
		let totalFiles = 0;
		let currentLiveTreeDigest: string | undefined;
		try {
			liveSkills = listLiveSkillTrees(this.repoSkillsRoot);
			if (pathExists(this.repoSkillsRoot)) {
				const liveTree = digestTree(this.repoSkillsRoot);
				totalFiles = liveTree.fileCount;
				currentLiveTreeDigest = liveTree.digest;
			}
			if (pathExists(this.routerDir)) totalFiles += digestTree(this.routerDir).fileCount;
		} catch (error) {
			issues.push(error instanceof Error ? error.message : String(error));
		}
		if (state) {
			for (const [skillId, expected] of Object.entries(state.managedSkills)) {
				const current = liveSkills.get(skillId);
				if (!current) issues.push(`${skillId}: managed skill is missing`);
				else if (current.digest !== expected.digest) issues.push(`${skillId}: managed skill is modified`);
			}
			for (const [relativePath, expected] of Object.entries(state.managedRootFiles)) {
				if (relativePath === REPOSITORY_INDEX_ROOT_FILE) continue;
				try {
					const current = rootFileDigest(this.repoSkillsRoot, relativePath);
					if (!current) issues.push(`${relativePath}: managed root file is missing`);
					else if (current !== expected) issues.push(`${relativePath}: managed root file is modified`);
				} catch (error) {
					issues.push(error instanceof Error ? error.message : String(error));
				}
			}
		}
		let enabled: boolean | undefined;
		try {
			enabled = routerEnabled(this.routerDir);
			if (enabled === undefined && (state || liveSkills.size > 0)) issues.push("repo-skills-router is missing");
			else if (enabled !== undefined) {
				const expectedSkillIds = state ? new Set(Object.keys(state.managedSkills)) : new Set(liveSkills.keys());
				issues.push(...routerCoverageIssues(this.routerDir, expectedSkillIds, liveSkills));
				if (
					state &&
					currentLiveTreeDigest === state.liveTreeDigest &&
					(!state.liveRouterDigest || digestRouterTree(this.routerDir) !== state.liveRouterDigest)
				) {
					issues.push("repo-skills-router is modified or stale");
				}
			}
		} catch (error) {
			issues.push(error instanceof Error ? error.message : String(error));
		}
		const managedIds = new Set(Object.keys(state?.managedSkills ?? {}));
		const localSkills = [...liveSkills.keys()].filter((skillId) => !managedIds.has(skillId)).length;
		return {
			installed: liveSkills.size > 0 && enabled !== undefined,
			managed: !!state,
			sourceRepository: state?.source.repository,
			commit: state?.source.commit,
			installedAt: state?.installedAt,
			updatedAt: state?.updatedAt,
			managedSkills: state ? Object.keys(state.managedSkills).length : 0,
			localSkills,
			totalSkills: liveSkills.size,
			repositoryCount: routerBuildCounts(this.routerDir)?.repositoryCount,
			assignmentCount: routerBuildCounts(this.routerDir)?.assignmentCount,
			areaCount: routerBuildCounts(this.routerDir)?.areaCount,
			familyCount: routerBuildCounts(this.routerDir)?.familyCount,
			totalFiles,
			routerPresent: enabled !== undefined,
			routerEnabled: enabled,
			issues: issues.sort(),
		};
	}

	status(): RepoSkillsLibraryStatus {
		try {
			return this.statusUnlocked(readState(this.statePath));
		} catch (error) {
			const status = this.statusUnlocked(undefined);
			return {
				...status,
				managed: pathExists(this.statePath),
				issues: [error instanceof Error ? error.message : String(error), ...status.issues].sort(),
			};
		}
	}
}
