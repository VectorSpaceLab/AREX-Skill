import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { copyFile, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const sourceScript = fileURLToPath(new URL("./upstream-provenance.mjs", import.meta.url));
const expectedUpstream = {
	repository: "https://github.com/earendil-works/pi.git",
	tag: "v0.83.0",
	commit: "845d6ff1f6643aba440341cce877ce1c43ebbc39",
};

function digest(content) {
	return createHash("sha256").update(content).digest("hex");
}

async function write(root, path, content) {
	const absolute = join(root, path);
	await mkdir(dirname(absolute), { recursive: true });
	await writeFile(absolute, content);
}

async function createFixture() {
	const root = await mkdtemp(join(tmpdir(), "disco-provenance-"));
	for (const path of [
		"scripts",
		"packages/coding-agent/src",
		"packages/coding-agent/test",
		"docs",
		"examples",
	]) {
		await mkdir(join(root, path), { recursive: true });
	}
	await copyFile(sourceScript, join(root, "scripts/upstream-provenance.mjs"));

	const upstreamContent = "same as upstream\n";
	const localContent = "local before refresh\n";
	await write(root, "docs/mapped.md", upstreamContent);
	await write(root, "packages/coding-agent/src/local.ts", localContent);
	const manifest = {
		schemaVersion: 1,
		upstream: expectedUpstream,
		scope: { description: "fixture", nonMigratedPackages: [] },
		scopes: [
			{
				name: "fixture",
				entries: [
					{
						upstreamPath: "packages/coding-agent/docs/mapped.md",
						upstreamSha256: digest(upstreamContent),
						disposition: "retained_unchanged",
						localPath: "docs/mapped.md",
						localSha256: digest(upstreamContent),
					},
				],
			},
		],
		codingAgentPackageEntries: [],
		piAiOAuthEntries: [],
		localAdditions: [
			{
				localPath: "packages/coding-agent/src/local.ts",
				localSha256: digest(localContent),
				origin: "disco_owned",
			},
		],
	};
	await write(
		root,
		"packages/coding-agent/UPSTREAM_MANIFEST.json",
		`${JSON.stringify(manifest, null, 2)}\n`,
	);
	return { root, manifest };
}

function run(root, ...args) {
	return spawnSync(process.execPath, ["scripts/upstream-provenance.mjs", ...args], {
		cwd: root,
		encoding: "utf8",
	});
}

async function readManifest(root) {
	return JSON.parse(
		await readFile(join(root, "packages/coding-agent/UPSTREAM_MANIFEST.json"), "utf8"),
	);
}

test("refresh-local updates local hashes and explicitly approved additions only", async (t) => {
	const { root, manifest } = await createFixture();
	t.after(() => rm(root, { recursive: true, force: true }));
	await write(root, "docs/mapped.md", "locally modified\n");
	await write(root, "packages/coding-agent/src/local.ts", "local after refresh\n");
	await write(root, "docs/new.md", "new local document\n");

	const result = run(root, "--refresh-local", "--add-local", "docs/new.md");
	assert.equal(result.status, 0, result.stderr);
	const refreshed = await readManifest(root);

	assert.deepEqual(refreshed.upstream, manifest.upstream);
	assert.equal(refreshed.scopes[0].entries[0].upstreamPath, manifest.scopes[0].entries[0].upstreamPath);
	assert.equal(
		refreshed.scopes[0].entries[0].upstreamSha256,
		manifest.scopes[0].entries[0].upstreamSha256,
	);
	assert.equal(refreshed.scopes[0].entries[0].localSha256, digest("locally modified\n"));
	assert.equal(refreshed.scopes[0].entries[0].disposition, "retained_modified");
	assert.deepEqual(refreshed.localAdditions.find((entry) => entry.localPath === "docs/new.md"), {
		localPath: "docs/new.md",
		localSha256: digest("new local document\n"),
		origin: "disco_owned",
	});
	assert.equal(
		refreshed.localAdditions.find((entry) => entry.localPath === "packages/coding-agent/src/local.ts").localSha256,
		digest("local after refresh\n"),
	);

	const check = run(root, "--check");
	assert.equal(check.status, 0, check.stderr);
});

test("refresh-local rejects an unapproved unclassified file without changing the manifest", async (t) => {
	const { root } = await createFixture();
	t.after(() => rm(root, { recursive: true, force: true }));
	await write(root, "docs/unapproved.md", "temporary\n");
	const before = await readFile(join(root, "packages/coding-agent/UPSTREAM_MANIFEST.json"), "utf8");

	const result = run(root, "--refresh-local");
	assert.notEqual(result.status, 0);
	assert.match(result.stderr, /approve each with --add-local/u);
	assert.match(result.stderr, /docs\/unapproved\.md/u);
	assert.equal(
		await readFile(join(root, "packages/coding-agent/UPSTREAM_MANIFEST.json"), "utf8"),
		before,
	);
});

test("refresh-local rejects a missing declared file", async (t) => {
	const { root } = await createFixture();
	t.after(() => rm(root, { recursive: true, force: true }));
	await rm(join(root, "packages/coding-agent/src/local.ts"));

	const result = run(root, "--refresh-local");
	assert.notEqual(result.status, 0);
	assert.match(result.stderr, /Cannot refresh missing local file/u);
});

test("refresh-local rejects invalid additions and conflicting modes", async (t) => {
	const { root } = await createFixture();
	t.after(() => rm(root, { recursive: true, force: true }));

	for (const [args, pattern] of [
		[["--refresh-local", "--add-local", "../outside.md"], /escapes the package root/u],
		[["--refresh-local", "--add-local", "package.json"], /outside the inventoried roots/u],
		[["--refresh-local", "--add-local", "docs/missing.md"], /does not exist/u],
		[["--refresh-local", "--add-local", "docs/mapped.md"], /already declared/u],
		[["--refresh-local", "--upstream-root", root], /cannot be combined/u],
		[["--check", "--add-local", "docs/new.md"], /only be used with --refresh-local/u],
	]) {
		const result = run(root, ...args);
		assert.notEqual(result.status, 0, args.join(" "));
		assert.match(result.stderr, pattern);
	}
});
