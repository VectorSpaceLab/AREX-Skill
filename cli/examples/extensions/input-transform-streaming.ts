/**
 * Streaming-Aware Input Gate
 *
 * Demonstrates `event.streamingBehavior` to skip expensive pre-processing
 * during mid-stream steering, where low latency matters.
 *
 * This extension prepends `git diff --stat` output when the user mentions
 * file changes, giving the model immediate context. During steering the
 * exec call is skipped so the correction reaches the model without delay.
 *
 * Start disco with this extension:
 *   disco -e ./examples/extensions/input-transform-streaming.ts
 */
import type { ExtensionAPI } from "@auto-ml-skills/disco";

const TRIGGER = /\b(changes?|diff|modified)\b/i;

export default function (disco: ExtensionAPI) {
	disco.on("input", async (event) => {
		// During steering, skip the exec call — corrections should be fast
		if (event.streamingBehavior === "steer") {
			return { action: "continue" };
		}

		if (!TRIGGER.test(event.text)) {
			return { action: "continue" };
		}

		const { stdout, code } = await disco.exec("git", ["diff", "--stat"]);
		if (code !== 0 || !stdout.trim()) {
			return { action: "continue" };
		}

		return {
			action: "transform",
			text: `${event.text}\n\nCurrent uncommitted changes:\n\`\`\`\n${stdout.trim()}\n\`\`\``,
		};
	});
}
