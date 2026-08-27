import type { Component } from "@earendil-works/pi-tui";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";
import chalk from "chalk";

const DISCO_SPLASH_FRAMES = [
	"o     ",
	" o    ",
	"  o   ",
	"   o  ",
	"    o ",
	"     o",
	"    o ",
	"   o  ",
	"  o   ",
	" o    ",
];

export const DISCO_SPLASH_FRAME_MS = 80;
export const DISCO_SPLASH_DURATION_MS = 880;

const DISCO_DANCER_PIXEL_WIDTH = 9;
const DISCO_DANCER_PIXEL = "█";
const DISCO_DANCER_EMPTY_PIXEL = " ";
const DISCO_SIDE_GAP = "    ";

export const DISCO_COLORS = {
	forest: "#36663E",
	olive: "#889F4E",
	moss: "#C4C248",
	gold: "#F8D042",
	amber: "#F9B43F",
} as const;

const DISCO_LOGO_PALETTE = [
	DISCO_COLORS.forest,
	DISCO_COLORS.olive,
	DISCO_COLORS.moss,
	DISCO_COLORS.gold,
	DISCO_COLORS.amber,
] as const;

const DISCO_DANCER_FRAMES = [
	["..s...s..", ".s.hhh.s.", "...hss...", "...ttt...", "..sttts..", "...ppp...", "..p...p..", ".ww...ww."],
	[".s.....s.", "..shhh.s.", "..hss....", "...ttts..", "..sttd...", "..ppp....", ".p...p...", "ww....ww."],
	[".s.....s.", "s..hhh..s", ".s.hssh.s", "...ttt...", "..sttts..", "..ppppp..", ".p.....p.", "ww.....ww"],
	[".s.....s.", ".s.hhh.s.", "....ssh..", "..sttt...", "...dtts..", "....ppp..", "...p...p.", ".ww....ww"],
] as const;

const DISCO_LOGO_LINES = [
	"██████╗ ██╗███████╗ ██████╗ ██████╗ ",
	"██╔══██╗██║██╔════╝██╔════╝██╔═══██╗",
	"██║  ██║██║███████╗██║     ██║   ██║",
	"██║  ██║██║╚════██║██║     ██║   ██║",
	"██████╔╝██║███████║╚██████╗╚██████╔╝",
	"╚═════╝ ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ",
];

const DISCO_LOGO_WIDTH = Math.max(...DISCO_LOGO_LINES.map((line) => visibleWidth(line)));
const DISCO_WIDE_SCENE_WIDTH =
	DISCO_DANCER_PIXEL_WIDTH * visibleWidth(DISCO_DANCER_PIXEL) * 2 +
	DISCO_SIDE_GAP.length * 2 +
	DISCO_LOGO_WIDTH;

const DISCO_DANCER_PALETTES = {
	left: {
		d: DISCO_COLORS.forest,
		h: DISCO_COLORS.forest,
		s: DISCO_COLORS.gold,
		t: DISCO_COLORS.amber,
		p: DISCO_COLORS.moss,
		w: DISCO_COLORS.gold,
	},
	right: {
		d: DISCO_COLORS.forest,
		h: DISCO_COLORS.olive,
		s: DISCO_COLORS.gold,
		t: DISCO_COLORS.moss,
		p: DISCO_COLORS.amber,
		w: DISCO_COLORS.gold,
	},
} as const;

type DisCoDancerSide = keyof typeof DISCO_DANCER_PALETTES;
type DisCoDancerSymbol = keyof (typeof DISCO_DANCER_PALETTES)["left"];

function isTruthyEnvFlag(value: string | undefined): boolean {
	if (!value) return false;
	const normalized = value.toLowerCase();
	return normalized === "1" || normalized === "true" || normalized === "yes";
}

export function shouldShowDisCoStartupSplash(options: {
	stdinIsTTY: boolean;
	stdoutIsTTY: boolean;
	verbose?: boolean;
	quietStartup: boolean;
	env?: NodeJS.ProcessEnv;
}): boolean {
	const env = options.env ?? process.env;
	return (
		options.stdinIsTTY &&
		options.stdoutIsTTY &&
		!isTruthyEnvFlag(env.DISCO_NO_SPLASH) &&
		!isTruthyEnvFlag(env.DISCO_STARTUP_BENCHMARK) &&
		(options.verbose === true || !options.quietStartup)
	);
}

export function discoFg(color: string, text: string): string {
	return chalk.hex(color)(text);
}

export function discoBold(color: string, text: string): string {
	return chalk.bold(discoFg(color, text));
}

function logoPaletteColor(position: number): string {
	const clamped = Math.max(0, Math.min(1, position));
	const index = Math.min(Math.round(clamped * (DISCO_LOGO_PALETTE.length - 1)), DISCO_LOGO_PALETTE.length - 1);
	return DISCO_LOGO_PALETTE[index] ?? DISCO_COLORS.forest;
}

export function formatStartupTagline(version: string): string {
	return `${discoBold(DISCO_COLORS.gold, "DisCo")} ${discoFg(DISCO_COLORS.moss, `v${version}`)} ${discoFg(DISCO_COLORS.olive, "· skill-powered research agent")}`;
}

function renderDancerRow(row: string, side: DisCoDancerSide): string {
	const palette = DISCO_DANCER_PALETTES[side];
	let rendered = "";
	for (const rawSymbol of row.padEnd(DISCO_DANCER_PIXEL_WIDTH, ".").slice(0, DISCO_DANCER_PIXEL_WIDTH)) {
		if (rawSymbol === ".") {
			rendered += DISCO_DANCER_EMPTY_PIXEL;
			continue;
		}
		const symbol = rawSymbol as DisCoDancerSymbol;
		rendered += discoFg(palette[symbol] ?? DISCO_COLORS.gold, DISCO_DANCER_PIXEL);
	}
	return rendered;
}

function dancerLines(frame: number, side: DisCoDancerSide): string[] {
	const pose = DISCO_DANCER_FRAMES[frame % DISCO_DANCER_FRAMES.length] ?? DISCO_DANCER_FRAMES[0];
	return pose.map((row) => renderDancerRow(row, side));
}

export function discoSceneContentWidth(terminalWidth: number): number {
	return Math.max(1, terminalWidth - 4);
}

export function centerText(text: string, width: number): string {
	const padding = Math.max(0, Math.floor((width - visibleWidth(text)) / 2));
	return `${" ".repeat(padding)}${text}`;
}

function tintLogoLine(line: string, row: number): string {
	let tinted = "";
	const chars = [...line];
	const rowRatio = DISCO_LOGO_LINES.length <= 1 ? 0 : row / (DISCO_LOGO_LINES.length - 1);
	for (let i = 0; i < chars.length; i++) {
		const ch = chars[i] ?? "";
		const columnRatio = chars.length <= 1 ? 0 : i / (chars.length - 1);
		const color = logoPaletteColor(columnRatio * 0.88 + rowRatio * 0.12);
		tinted += ch === " " ? " " : discoFg(color, ch);
	}
	return tinted;
}

export function formatDisCoScene(frame: number, terminalWidth = process.stdout.columns || 120): string[] {
	const contentWidth = discoSceneContentWidth(terminalWidth);
	if (contentWidth < DISCO_LOGO_WIDTH) {
		const compactLogo = truncateToWidth(discoBold(DISCO_COLORS.gold, "DisCo"), contentWidth, "");
		return [centerText(compactLogo, contentWidth)];
	}

	const logo = DISCO_LOGO_LINES.map((line, row) => centerText(tintLogoLine(line, row), contentWidth));
	if (contentWidth < DISCO_WIDE_SCENE_WIDTH) {
		return logo;
	}

	const leftDancer = dancerLines(frame, "left");
	const rightDancer = dancerLines(frame + 1, "right");
	const logoTop = Math.floor((leftDancer.length - DISCO_LOGO_LINES.length) / 2);
	return leftDancer.map((left, row) => {
		const logoIndex = row - logoTop;
		const rawLogo = DISCO_LOGO_LINES[logoIndex] ?? "";
		const renderedLogo = rawLogo ? tintLogoLine(rawLogo, logoIndex) : " ".repeat(DISCO_LOGO_WIDTH);
		const right = rightDancer[row] ?? " ".repeat(DISCO_DANCER_PIXEL_WIDTH);
		return centerText(`${left}${DISCO_SIDE_GAP}${renderedLogo}${DISCO_SIDE_GAP}${right}`, contentWidth);
	});
}

export function formatDisCoSplash(version: string, sweep: string, frame: number, terminalWidth: number): string {
	const contentWidth = discoSceneContentWidth(terminalWidth);
	const fullTagline = formatStartupTagline(version);
	const compactTagline = `${discoBold(DISCO_COLORS.gold, "DisCo")} ${discoFg(DISCO_COLORS.moss, `v${version}`)}`;
	const tagline = visibleWidth(fullTagline) <= contentWidth ? fullTagline : compactTagline;
	const status = visibleWidth(tagline) + 2 <= contentWidth ? `${discoFg(DISCO_COLORS.amber, sweep)} ${tagline}` : tagline;
	return [...formatDisCoScene(frame, terminalWidth), "", centerText(truncateToWidth(status, contentWidth, ""), contentWidth)].join(
		"\n",
	);
}

export class DisCoSplash implements Component {
	private frame = 0;
	private readonly version: string;

	constructor(version: string) {
		this.version = version;
	}

	nextFrame(): void {
		this.frame = (this.frame + 1) % DISCO_SPLASH_FRAMES.length;
	}

	render(width: number): string[] {
		const sweep = DISCO_SPLASH_FRAMES[this.frame] ?? DISCO_SPLASH_FRAMES[0];
		return formatDisCoSplash(this.version, sweep, this.frame, width).split("\n");
	}

	invalidate(): void {}
}

export async function animateDisCoSplash(
	splash: DisCoSplash,
	requestRender: () => void,
	options: { signal?: AbortSignal; frameMs?: number; durationMs?: number } = {},
): Promise<"completed" | "aborted"> {
	const signal = options.signal;
	if (signal?.aborted) return "aborted";

	let finish: ((result: "completed" | "aborted") => void) | undefined;
	const result = new Promise<"completed" | "aborted">((resolve) => {
		finish = resolve;
	});
	const interval = setInterval(() => {
		splash.nextFrame();
		requestRender();
	}, options.frameMs ?? DISCO_SPLASH_FRAME_MS);
	const timeout = setTimeout(() => finish?.("completed"), options.durationMs ?? DISCO_SPLASH_DURATION_MS);
	const onAbort = () => finish?.("aborted");
	signal?.addEventListener("abort", onAbort, { once: true });

	try {
		return await result;
	} finally {
		clearInterval(interval);
		clearTimeout(timeout);
		signal?.removeEventListener("abort", onAbort);
	}
}
