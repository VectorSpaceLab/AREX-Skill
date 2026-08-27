export function getDiscoUserAgent(version: string): string {
	const runtime = process.versions.bun ? `bun/${process.versions.bun}` : `node/${process.version}`;
	return `disco/${version} (${process.platform}; ${runtime}; ${process.arch})`;
}
