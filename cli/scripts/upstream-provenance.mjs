import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFile, readdir, stat, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const manifestPath = join(packageRoot, "packages", "coding-agent", "UPSTREAM_MANIFEST.json");
const expectedUpstream = {
	repository: "https://github.com/earendil-works/pi.git",
	tag: "v0.83.0",
	commit: "845d6ff1f6643aba440341cce877ce1c43ebbc39",
};
const inventoriedLocalRoots = [
	"packages/coding-agent/src",
	"packages/coding-agent/test",
	"docs",
	"examples",
];

function parseArguments(argv) {
	let requestedMode;
	let upstreamRoot;
	const addLocalPaths = [];
	for (let index = 0; index < argv.length; index += 1) {
		const argument = argv[index];
		if (["--check", "--write", "--refresh-local"].includes(argument)) {
			const mode = argument.slice(2);
			if (requestedMode && requestedMode !== mode) {
				throw new Error(`Cannot combine --${requestedMode} with --${mode}`);
			}
			requestedMode = mode;
		}
		else if (argument === "--upstream-root") upstreamRoot = argv[++index];
		else if (argument === "--add-local") {
			const path = argv[++index];
			if (!path || path.startsWith("--")) {
				throw new Error("--add-local requires a relative path");
			}
			addLocalPaths.push(path);
		}
		else throw new Error(`Unknown argument: ${argument}`);
	}
	const mode = requestedMode ?? "check";
	if (mode === "write" && !upstreamRoot) {
		throw new Error("--write requires --upstream-root <pi repository>");
	}
	if (mode === "refresh-local" && upstreamRoot) {
		throw new Error("--refresh-local cannot be combined with --upstream-root");
	}
	if (mode !== "refresh-local" && addLocalPaths.length > 0) {
		throw new Error("--add-local can only be used with --refresh-local");
	}
	return {
		mode,
		upstreamRoot: upstreamRoot ? resolve(upstreamRoot) : undefined,
		addLocalPaths,
	};
}

function git(upstreamRoot, args) {
	return execFileSync("git", args, { cwd: upstreamRoot, encoding: "utf8" }).trim();
}

function toPosix(path) {
	return path.replaceAll("\\", "/");
}

async function sha256(path) {
	return createHash("sha256").update(await readFile(path)).digest("hex");
}

async function pathExists(path) {
	try {
		await stat(path);
		return true;
	} catch (error) {
		if (error?.code === "ENOENT") return false;
		throw error;
	}
}

async function walkFiles(root) {
	const result = [];
	for (const entry of await readdir(root, { withFileTypes: true })) {
		const path = join(root, entry.name);
		if (entry.isDirectory()) result.push(...(await walkFiles(path)));
		else if (entry.isFile()) result.push(toPosix(relative(packageRoot, path)));
	}
	return result.sort();
}

async function describeMapping(upstreamRoot, upstreamPath, localPath, dispositionOverride) {
	const upstreamAbsolute = join(upstreamRoot, upstreamPath);
	const entry = {
		upstreamPath,
		upstreamSha256: await sha256(upstreamAbsolute),
		disposition: dispositionOverride ?? "excluded",
	};
	if (!localPath) return entry;

	const localAbsolute = join(packageRoot, localPath);
	if (!(await pathExists(localAbsolute))) {
		throw new Error(`Mapped local file is missing: ${localPath}`);
	}
	entry.localPath = localPath;
	entry.localSha256 = await sha256(localAbsolute);
	if (!dispositionOverride) {
		entry.disposition =
			entry.upstreamSha256 === entry.localSha256 ? "retained_unchanged" : "retained_modified";
	}
	return entry;
}

function trackedFiles(upstreamRoot, prefix) {
	const output = git(upstreamRoot, ["ls-files", "--", prefix]);
	return output ? output.split("\n").sort() : [];
}

async function buildManifest(upstreamRoot) {
	const remote = git(upstreamRoot, ["remote", "get-url", "origin"]).replace(/\.git$/u, "");
	const expectedRemote = expectedUpstream.repository.replace(/\.git$/u, "");
	if (remote !== expectedRemote) {
		throw new Error(`Unexpected upstream origin: ${remote}`);
	}
	const head = git(upstreamRoot, ["rev-parse", "HEAD"]);
	if (head !== expectedUpstream.commit) {
		throw new Error(`Unexpected upstream commit: ${head}`);
	}
	const tag = git(upstreamRoot, ["describe", "--tags", "--exact-match", "HEAD"]);
	if (tag !== expectedUpstream.tag) {
		throw new Error(`Unexpected upstream tag: ${tag}`);
	}
	const trackedChanges = git(upstreamRoot, ["status", "--short", "--untracked-files=no"]);
	if (trackedChanges) {
		throw new Error(`Upstream tracked files are modified:\n${trackedChanges}`);
	}

	const scopes = [
		{
			name: "coding_agent_runtime",
			upstreamPrefix: "packages/coding-agent/src/",
			localPrefix: "packages/coding-agent/src/",
			rename: new Map([
				[
					"packages/coding-agent/src/utils/pi-user-agent.ts",
					"packages/coding-agent/src/utils/disco-user-agent.ts",
				],
			]),
		},
		{
			name: "coding_agent_tests",
			upstreamPrefix: "packages/coding-agent/test/",
			localPrefix: "packages/coding-agent/test/",
			rename: new Map(),
		},
		{
			name: "coding_agent_docs",
			upstreamPrefix: "packages/coding-agent/docs/",
			localPrefix: "docs/",
			rename: new Map(),
		},
		{
			name: "coding_agent_examples",
			upstreamPrefix: "packages/coding-agent/examples/",
			localPrefix: "examples/",
			rename: new Map(),
		},
	];

	const mappedLocalPaths = new Set();
	const manifestScopes = [];
	for (const scope of scopes) {
		const entries = [];
		for (const upstreamPath of trackedFiles(upstreamRoot, scope.upstreamPrefix)) {
			const relativePath = upstreamPath.slice(scope.upstreamPrefix.length);
			const renamedPath = scope.rename.get(upstreamPath);
			const localPath = renamedPath ?? `${scope.localPrefix}${relativePath}`;
			const exists = await pathExists(join(packageRoot, localPath));
			const disposition = !exists
				? "excluded"
				: renamedPath
					? "renamed_modified"
					: undefined;
			const entry = await describeMapping(
				upstreamRoot,
				upstreamPath,
				exists ? localPath : undefined,
				disposition,
			);
			if (entry.localPath) mappedLocalPaths.add(entry.localPath);
			entries.push(entry);
		}
		manifestScopes.push({ name: scope.name, entries });
	}

	const topLevelMappings = new Map([
		["packages/coding-agent/.gitignore", ".gitignore"],
		["packages/coding-agent/CHANGELOG.md", "packages/coding-agent/UPSTREAM_CHANGELOG.md"],
		["packages/coding-agent/README.md", "README.md"],
		["packages/coding-agent/package.json", "packages/coding-agent/upstream-package.json"],
		["packages/coding-agent/tsconfig.build.json", "tsconfig.build.json"],
		["packages/coding-agent/tsconfig.examples.json", "tsconfig.examples.json"],
		["packages/coding-agent/vitest.config.ts", "vitest.config.ts"],
	]);
	const scopedPrefixes = scopes.map((scope) => scope.upstreamPrefix);
	const packageEntries = [];
	for (const upstreamPath of trackedFiles(upstreamRoot, "packages/coding-agent/")) {
		if (scopedPrefixes.some((prefix) => upstreamPath.startsWith(prefix))) continue;
		const localPath = topLevelMappings.get(upstreamPath);
		const entry = await describeMapping(upstreamRoot, upstreamPath, localPath);
		if (entry.localPath) mappedLocalPaths.add(entry.localPath);
		packageEntries.push(entry);
	}

	const oauthMappings = new Map([
		[
			"packages/ai/src/auth/oauth/anthropic.ts",
			"packages/coding-agent/src/core/oauth/anthropic.ts",
		],
		[
			"packages/ai/src/auth/oauth/device-code.ts",
			"packages/coding-agent/src/core/oauth/device-code.ts",
		],
		[
			"packages/ai/src/auth/oauth/oauth-page.ts",
			"packages/coding-agent/src/core/oauth/oauth-page.ts",
		],
		[
			"packages/ai/src/auth/oauth/openai-codex.ts",
			"packages/coding-agent/src/core/oauth/openai-codex.ts",
		],
		[
			"packages/ai/src/auth/oauth/openrouter.ts",
			"packages/coding-agent/src/core/oauth/openrouter.ts",
		],
		[
			"packages/ai/src/auth/oauth/pkce.ts",
			"packages/coding-agent/src/core/oauth/pkce.ts",
		],
	]);
	const oauthEntries = [];
	for (const upstreamPath of trackedFiles(upstreamRoot, "packages/ai/src/auth/oauth/")) {
		const localPath = oauthMappings.get(upstreamPath);
		const entry = await describeMapping(
			upstreamRoot,
			upstreamPath,
			localPath,
			localPath ? undefined : "external_dependency",
		);
		if (entry.localPath) mappedLocalPaths.add(entry.localPath);
		oauthEntries.push(entry);
	}

	const localAdditions = [];
	for (const root of inventoriedLocalRoots) {
		for (const localPath of await walkFiles(join(packageRoot, root))) {
			if (mappedLocalPaths.has(localPath)) continue;
			localAdditions.push({
				localPath,
				localSha256: await sha256(join(packageRoot, localPath)),
				origin: "disco_owned",
			});
		}
	}

	return {
		schemaVersion: 1,
		upstream: expectedUpstream,
		scope: {
			description:
				"Tracked Pi coding-agent files, selected callback-based pi-ai OAuth flows, and every local runtime/test/docs/example file.",
			nonMigratedPackages: [
				"packages/agent (provided by @earendil-works/pi-agent-core@0.83.0)",
				"packages/ai except the listed OAuth adapters (provided by @earendil-works/pi-ai@0.83.0)",
				"packages/tui (provided by @earendil-works/pi-tui@0.83.0)",
			],
		},
		scopes: manifestScopes,
		codingAgentPackageEntries: packageEntries,
		piAiOAuthEntries: oauthEntries,
		localAdditions: localAdditions.sort((a, b) => a.localPath.localeCompare(b.localPath)),
	};
}

function collectEntries(manifest) {
	return [
		...manifest.scopes.flatMap((scope) => scope.entries),
		...manifest.codingAgentPackageEntries,
		...manifest.piAiOAuthEntries,
	];
}

function assertManifestIdentity(manifest) {
	if (JSON.stringify(manifest.upstream) !== JSON.stringify(expectedUpstream)) {
		throw new Error("Manifest upstream identity does not match the pinned Pi baseline");
	}
}

function normalizeLocalPath(path) {
	const candidate = toPosix(path);
	if (!candidate || isAbsolute(path) || candidate.startsWith("/") || /^[A-Za-z]:\//u.test(candidate)) {
		throw new Error(`--add-local requires a relative path inside the package: ${path}`);
	}
	const absolute = resolve(packageRoot, candidate);
	const localPath = toPosix(relative(packageRoot, absolute));
	if (!localPath || localPath === ".." || localPath.startsWith("../")) {
		throw new Error(`--add-local path escapes the package root: ${path}`);
	}
	if (!inventoriedLocalRoots.some((root) => localPath === root || localPath.startsWith(`${root}/`))) {
		throw new Error(`--add-local path is outside the inventoried roots: ${localPath}`);
	}
	return localPath;
}

async function refreshLocalManifest(manifest, addLocalPaths) {
	assertManifestIdentity(manifest);
	const refreshed = structuredClone(manifest);
	const localEntries = collectEntries(refreshed).filter((entry) => entry.localPath);
	const declaredLocalPaths = new Set([
		...localEntries.map((entry) => entry.localPath),
		...refreshed.localAdditions.map((entry) => entry.localPath),
	]);

	for (const entry of [...localEntries, ...refreshed.localAdditions]) {
		const absolute = join(packageRoot, entry.localPath);
		if (!(await pathExists(absolute))) {
			throw new Error(`Cannot refresh missing local file: ${entry.localPath}`);
		}
		entry.localSha256 = await sha256(absolute);
		if (entry.upstreamPath && ["retained_unchanged", "retained_modified"].includes(entry.disposition)) {
			entry.disposition = entry.upstreamSha256 === entry.localSha256 ? "retained_unchanged" : "retained_modified";
		}
	}

	const requestedAdditions = addLocalPaths.map(normalizeLocalPath);
	const requestedAdditionSet = new Set(requestedAdditions);
	if (requestedAdditionSet.size !== requestedAdditions.length) {
		throw new Error("--add-local paths must be unique");
	}
	for (const localPath of requestedAdditions) {
		if (declaredLocalPaths.has(localPath)) {
			throw new Error(`--add-local file is already declared: ${localPath}`);
		}
		const absolute = join(packageRoot, localPath);
		if (!(await pathExists(absolute))) {
			throw new Error(`--add-local file does not exist: ${localPath}`);
		}
		const fileStat = await stat(absolute);
		if (!fileStat.isFile()) {
			throw new Error(`--add-local path is not a regular file: ${localPath}`);
		}
		refreshed.localAdditions.push({
			localPath,
			localSha256: await sha256(absolute),
			origin: "disco_owned",
		});
		declaredLocalPaths.add(localPath);
	}

	const unclassified = [];
	for (const root of inventoriedLocalRoots) {
		for (const localPath of await walkFiles(join(packageRoot, root))) {
			if (!declaredLocalPaths.has(localPath)) unclassified.push(localPath);
		}
	}
	if (unclassified.length > 0) {
		throw new Error(
			`Local refresh found unclassified files; approve each with --add-local:\n- ${unclassified.join("\n- ")}`,
		);
	}

	refreshed.localAdditions.sort((a, b) => a.localPath.localeCompare(b.localPath));
	return refreshed;
}

async function verifyLocalManifest(manifest) {
	const failures = [];
	const localEntries = collectEntries(manifest).filter((entry) => entry.localPath);
	const declaredLocalPaths = new Set([
		...localEntries.map((entry) => entry.localPath),
		...manifest.localAdditions.map((entry) => entry.localPath),
	]);

	for (const entry of [...localEntries, ...manifest.localAdditions]) {
		const absolute = join(packageRoot, entry.localPath);
		if (!(await pathExists(absolute))) {
			failures.push(`missing local file: ${entry.localPath}`);
			continue;
		}
		const actual = await sha256(absolute);
		if (actual !== entry.localSha256) failures.push(`local hash changed: ${entry.localPath}`);
	}

	for (const root of ["packages/coding-agent/src", "packages/coding-agent/test", "docs", "examples"]) {
		for (const localPath of await walkFiles(join(packageRoot, root))) {
			if (!declaredLocalPaths.has(localPath)) failures.push(`unclassified local file: ${localPath}`);
		}
	}

	if (failures.length > 0) {
		throw new Error(`Upstream provenance verification failed:\n- ${failures.join("\n- ")}`);
	}
}

const { mode, upstreamRoot, addLocalPaths } = parseArguments(process.argv.slice(2));
if (mode === "write") {
	const manifest = await buildManifest(upstreamRoot);
	await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
	console.log(`Wrote ${toPosix(relative(packageRoot, manifestPath))}.`);
} else if (mode === "refresh-local") {
	const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
	const refreshed = await refreshLocalManifest(manifest, addLocalPaths);
	await writeFile(manifestPath, `${JSON.stringify(refreshed, null, 2)}\n`);
	console.log(`Refreshed local provenance in ${toPosix(relative(packageRoot, manifestPath))}.`);
} else {
	const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
	assertManifestIdentity(manifest);
	await verifyLocalManifest(manifest);
	if (upstreamRoot) {
		const regenerated = await buildManifest(upstreamRoot);
		if (JSON.stringify(regenerated) !== JSON.stringify(manifest)) {
			throw new Error("Manifest does not match the supplied upstream tree or current local tree");
		}
	}
	const entries = collectEntries(manifest);
	console.log(
		`Verified ${entries.length} upstream decisions and ${manifest.localAdditions.length} DisCo-owned files.`,
	);
}
