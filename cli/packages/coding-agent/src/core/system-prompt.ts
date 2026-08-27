/**
 * System prompt construction and project context loading
 */

import { getDocsPath, getExamplesPath, getReadmePath } from "../config.ts";
import { formatSkillsForPrompt, type Skill } from "./skills.ts";

export interface BuildSystemPromptOptions {
	/** Custom system prompt (replaces default). */
	customPrompt?: string;
	/** Tools to include in prompt. Default: [read, bash, edit, write] */
	selectedTools?: string[];
	/** Optional one-line tool snippets keyed by tool name. */
	toolSnippets?: Record<string, string>;
	/** Additional guideline bullets appended to the default system prompt guidelines. */
	promptGuidelines?: string[];
	/** Text to append to system prompt. */
	appendSystemPrompt?: string;
	/** Working directory. */
	cwd: string;
	/** Pre-loaded context files. */
	contextFiles?: Array<{ path: string; content: string }>;
	/** Pre-loaded skills. */
	skills?: Skill[];
}

function appendContextAndSkills(
	prompt: string,
	options: {
		contextFiles: Array<{ path: string; content: string }>;
		skills: Skill[];
		includeSkills: boolean;
		promptCwd: string;
	},
): string {
	let result = prompt;
	if (options.contextFiles.length > 0) {
		result += "\n\n<project_context>\n\n";
		result += "Project-specific instructions and guidelines:\n\n";
		for (const { path: filePath, content } of options.contextFiles) {
			result += `<project_instructions path="${filePath}">\n${content}\n</project_instructions>\n\n`;
		}
		result += "</project_context>\n";
	}

	if (options.includeSkills && options.skills.length > 0) {
		result += formatSkillsForPrompt(options.skills);
	}

	result += `\nCurrent working directory: ${options.promptCwd}`;
	return result;
}

/** Build the system prompt with tools, guidelines, context, and mode contract. */
export function buildSystemPrompt(options: BuildSystemPromptOptions): string {
	const {
		customPrompt,
		selectedTools,
		toolSnippets,
		promptGuidelines,
		appendSystemPrompt,
		cwd,
		contextFiles: providedContextFiles,
		skills: providedSkills,
	} = options;
	const promptCwd = cwd.replace(/\\/g, "/");
	const appendSection = appendSystemPrompt ? `\n\n${appendSystemPrompt}` : "";
	const contextFiles = providedContextFiles ?? [];
	const skills = providedSkills ?? [];

	if (customPrompt) {
		return appendContextAndSkills(`${customPrompt}${appendSection}`, {
			contextFiles,
			skills,
			includeSkills: !selectedTools || selectedTools.includes("read"),
			promptCwd,
		});
	}

	const readmePath = getReadmePath();
	const docsPath = getDocsPath();
	const examplesPath = getExamplesPath();
	const tools = selectedTools || ["read", "bash", "edit", "write"];
	const visibleTools = tools.filter((name) => Boolean(toolSnippets?.[name]));
	const toolsList =
		visibleTools.length > 0 ? visibleTools.map((name) => `- ${name}: ${toolSnippets![name]}`).join("\n") : "(none)";

	const guidelinesList: string[] = [];
	const guidelinesSet = new Set<string>();
	const addGuideline = (guideline: string): void => {
		if (!guidelinesSet.has(guideline)) {
			guidelinesSet.add(guideline);
			guidelinesList.push(guideline);
		}
	};

	if (tools.includes("bash") && !tools.includes("grep") && !tools.includes("find") && !tools.includes("ls")) {
		addGuideline("Use bash for file operations like ls, rg, find");
	}
	for (const guideline of promptGuidelines ?? []) {
		const normalized = guideline.trim();
		if (normalized.length > 0) addGuideline(normalized);
	}
	addGuideline("Be concise in your responses");
	addGuideline("Show file paths clearly when working with files");

	const prompt = `You are DisCo, operating inside a coding-agent harness. The active <disco_mode> contract appended below defines your current role, its scope, and the resources you may use. Inspect the actual working tree and environment, perform requested work with the available tools, and verify outcomes instead of stopping at advice when the user asks you to act.

Available tools:
${toolsList}

In addition to the tools above, you may have access to other custom tools depending on the project.

Guidelines:
${guidelinesList.map((guideline) => `- ${guideline}`).join("\n")}

DisCo documentation (read only when the user asks about DisCo itself, its SDK, extensions, themes, skills, or TUI):
- Main documentation: ${readmePath}
- Additional docs: ${docsPath}
- Examples: ${examplesPath} (extensions, custom tools, SDK)
- Resolve docs/... under Additional docs and examples/... under Examples, not the current working directory.
- When asked about extensions, themes, skills, prompt templates, keybindings, SDK integrations, providers, models, or packages, read the relevant bundled documentation before implementing; for environment variables (docs/environment-variables.md), resolve that path under Additional docs.
- When working on DisCo topics, read referenced Markdown files completely and follow their cross-references.${appendSection}`;

	return appendContextAndSkills(prompt, {
		contextFiles,
		skills,
		includeSkills: tools.includes("read"),
		promptCwd,
	});
}
