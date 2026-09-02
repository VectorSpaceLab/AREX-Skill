import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { isAbsolute, join, relative, resolve } from "node:path";

export const MANAGED_INSTALL_SCHEMA_VERSION = 1;
export const MANAGED_PACKAGE_NAME = "@arex-skill/disco";

export interface ManagedInstallMarker {
	schemaVersion: 1;
	packageName: typeof MANAGED_PACKAGE_NAME;
	activeVersion: string;
	installDir: string;
	entrypoint: string;
	nodeSource: "system" | "managed";
	nodeVersion: string;
	nodePath: string;
	installerPath: string;
	bashPath?: string;
	platform: string;
}

function isNonEmptyString(value: unknown): value is string {
	return typeof value === "string" && value.trim().length > 0;
}

function isPathInside(path: string, root: string): boolean {
	const child = resolve(path);
	const parent = resolve(root);
	const remainder = relative(parent, child);
	return remainder !== "" && remainder !== ".." && !remainder.startsWith(`..${pathSeparator()}`) && !isAbsolute(remainder);
}

function pathSeparator(): string {
	return process.platform === "win32" ? "\\" : "/";
}

function markerPathFromEnvironment(): string {
	const explicit = process.env.DISCO_MANAGED_INSTALL_MARKER?.trim();
	if (explicit) return resolve(explicit);
	const installDir = process.env.DISCO_MANAGED_INSTALL_DIR?.trim();
	if (installDir) return resolve(installDir, "managed-install.json");
	const agentDir = process.env.DISCO_CODING_AGENT_DIR?.trim() || join(homedir(), ".disco", "agent");
	return resolve(agentDir, "install", "managed-install.json");
}

function currentVersionPath(installDir: string): string {
	return join(installDir, "current-version");
}

function readCurrentVersion(installDir: string): string | undefined {
	try {
		const value = readFileSync(currentVersionPath(installDir), "utf8").trim();
		return value || undefined;
	} catch {
		return undefined;
	}
}

function parseMarker(raw: unknown, markerPath: string): ManagedInstallMarker | undefined {
	if (!raw || typeof raw !== "object") return undefined;
	const marker = raw as Record<string, unknown>;
	if (marker.schemaVersion !== MANAGED_INSTALL_SCHEMA_VERSION || marker.packageName !== MANAGED_PACKAGE_NAME) return undefined;
	if (
		!isNonEmptyString(marker.activeVersion) ||
		!isNonEmptyString(marker.installDir) ||
		!isNonEmptyString(marker.entrypoint) ||
		!isNonEmptyString(marker.nodeSource) ||
		!isNonEmptyString(marker.nodeVersion) ||
		!isNonEmptyString(marker.nodePath) ||
		!isNonEmptyString(marker.installerPath) ||
		!isNonEmptyString(marker.platform)
	) {
		return undefined;
	}
	if (marker.nodeSource !== "system" && marker.nodeSource !== "managed") return undefined;
	if (!/^[0-9]+\.[0-9]+\.[0-9]+$/u.test(marker.activeVersion)) return undefined;

	const installDir = resolve(marker.installDir);
	const entrypoint = resolve(marker.entrypoint);
	const installerPath = resolve(marker.installerPath);
	if (!isPathInside(entrypoint, installDir) || !isPathInside(installerPath, installDir)) return undefined;
	if (resolve(markerPath) !== resolve(installDir, "managed-install.json")) return undefined;
	if (marker.bashPath !== undefined && marker.bashPath !== null && !isNonEmptyString(marker.bashPath)) return undefined;

	return {
		schemaVersion: 1,
		packageName: MANAGED_PACKAGE_NAME,
		activeVersion: marker.activeVersion,
		installDir,
		entrypoint,
		nodeSource: marker.nodeSource,
		nodeVersion: marker.nodeVersion,
		nodePath: resolve(marker.nodePath),
		installerPath,
		...(isNonEmptyString(marker.bashPath) ? { bashPath: resolve(marker.bashPath) } : {}),
		platform: marker.platform,
	};
}

/** Read and validate the installer-owned marker for the current process. */
export function readManagedInstallMarker(): ManagedInstallMarker | undefined {
	if (process.env.DISCO_MANAGED_INSTALL !== "1") return undefined;
	const markerPath = markerPathFromEnvironment();
	try {
		const markerText = readFileSync(markerPath, "utf8").replace(/^\uFEFF/u, "");
		const marker = parseMarker(JSON.parse(markerText) as unknown, markerPath);
		if (!marker) return undefined;
		if (readCurrentVersion(marker.installDir) !== marker.activeVersion) return undefined;
		const expectedEntrypoint = resolve(
			marker.installDir,
			"releases",
			marker.activeVersion,
			"node_modules",
			"@arex-skill",
			"disco",
			"dist",
			"cli.js",
		);
		return marker.entrypoint === expectedEntrypoint ? marker : undefined;
	} catch {
		return undefined;
	}
}

export function isManagedInstallMarkerUsable(marker: ManagedInstallMarker | undefined): marker is ManagedInstallMarker {
	return Boolean(marker && existsSync(marker.installerPath) && existsSync(marker.entrypoint) && existsSync(marker.nodePath));
}
