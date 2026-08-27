export function areExperimentalFeaturesEnabled(): boolean {
	return process.env.DISCO_EXPERIMENTAL === "1";
}
