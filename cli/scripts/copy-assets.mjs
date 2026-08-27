import { cp, mkdir, readdir, rm } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const sourceRoot = join(packageRoot, "packages", "coding-agent", "src");
const distRoot = join(packageRoot, "dist");

async function copyDirectory(source, destination) {
  await mkdir(dirname(destination), { recursive: true });
  await cp(source, destination, { recursive: true });
}

async function copyFiles(sourceDirectory, destinationDirectory, predicate) {
  await mkdir(destinationDirectory, { recursive: true });
  for (const entry of await readdir(sourceDirectory, { withFileTypes: true })) {
    if (entry.isFile() && predicate(entry.name)) {
      await cp(join(sourceDirectory, entry.name), join(destinationDirectory, entry.name));
    }
  }
}

await copyFiles(
  join(sourceRoot, "modes", "interactive", "theme"),
  join(distRoot, "modes", "interactive", "theme"),
  (name) => name.endsWith(".json"),
);

await copyFiles(
  join(sourceRoot, "modes", "interactive", "assets"),
  join(distRoot, "modes", "interactive", "assets"),
  (name) => name.endsWith(".png"),
);

await copyFiles(
  join(sourceRoot, "core", "export-html"),
  join(distRoot, "core", "export-html"),
  (name) => name === "template.html" || name === "template.css" || name === "template.js",
);

await copyDirectory(
  join(sourceRoot, "core", "export-html", "vendor"),
  join(distRoot, "core", "export-html", "vendor"),
);

const discoSkills = join(sourceRoot, "disco", "skills");
try {
  await rm(join(distRoot, "disco-resources"), { recursive: true, force: true });
  await copyDirectory(discoSkills, join(distRoot, "disco-resources", "skills"));
} catch (error) {
  if (error?.code !== "ENOENT") throw error;
}
