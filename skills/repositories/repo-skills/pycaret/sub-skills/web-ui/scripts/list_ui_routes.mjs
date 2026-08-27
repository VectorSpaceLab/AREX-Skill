#!/usr/bin/env node
/**
 * Print the key React Router routes from apps/web/src/App.tsx.
 * No package install required; uses only Node built-ins.
 */

import { existsSync, readFileSync } from 'node:fs';
import { resolve, join } from 'node:path';

function usage() {
  console.log(`Usage: node list_ui_routes.mjs [repo-root]

Print route paths declared in apps/web/src/App.tsx.

Arguments:
  repo-root   Repository root containing apps/web. Defaults to current working directory.

Examples:
  node scripts/list_ui_routes.mjs
  node scripts/list_ui_routes.mjs REPO_ROOT
`);
}

const arg = process.argv[2];
if (arg === '--help' || arg === '-h') {
  usage();
  process.exit(0);
}
if (process.argv.length > 3) {
  console.error('ERROR: expected at most one repo-root argument');
  usage();
  process.exit(2);
}

const repoRoot = resolve(arg ?? process.cwd());
const appPath = join(repoRoot, 'apps', 'web', 'src', 'App.tsx');

if (!existsSync(appPath)) {
  console.error(`ERROR: App.tsx not found at ${appPath}`);
  console.error('Pass the repository root that contains apps/web/src/App.tsx.');
  process.exit(2);
}

const text = readFileSync(appPath, 'utf8');

const imports = new Map();
for (const match of text.matchAll(/import\s+\{\s*([^}]+?)\s*\}\s+from\s+['"]([^'"]+)['"];?/g)) {
  const names = match[1]
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  for (const name of names) imports.set(name, match[2]);
}

function attrsFromRouteTag(tagAttrs) {
  const pathMatch = tagAttrs.match(/\bpath="([^"]+)"/);
  const index = /\bindex\b/.test(tagAttrs);
  const elementMatch = tagAttrs.match(/\belement=\{\s*<([A-Za-z0-9_]+)/);
  return {
    path: index ? '(index)' : pathMatch?.[1] ?? '',
    element: elementMatch?.[1] ?? '',
    index,
  };
}

const routes = [];
for (const match of text.matchAll(/<Route\s+([\s\S]*?)(?:\/?>)/g)) {
  const attrs = attrsFromRouteTag(match[1].replace(/\n/g, ' '));
  if (!attrs.path && !attrs.index && !attrs.element) continue;
  // Skip the wrapper route that has element=<AuthGate> and no path/index.
  if (!attrs.path && !attrs.index) continue;
  routes.push(attrs);
}

if (routes.length === 0) {
  console.error(`No routes found in ${appPath}`);
  process.exit(1);
}

const rows = routes.map((r) => {
  const source = r.element ? imports.get(r.element) ?? '' : '';
  return {
    path: r.path || '(pathless)',
    element: r.element || '(inline)',
    source,
  };
});

const pathWidth = Math.max('Route'.length, ...rows.map((r) => r.path.length));
const elementWidth = Math.max('Element'.length, ...rows.map((r) => r.element.length));

console.log(`${'Route'.padEnd(pathWidth)}  ${'Element'.padEnd(elementWidth)}  Source`);
console.log(`${'-'.repeat(pathWidth)}  ${'-'.repeat(elementWidth)}  ${'-'.repeat(40)}`);
for (const row of rows) {
  console.log(`${row.path.padEnd(pathWidth)}  ${row.element.padEnd(elementWidth)}  ${row.source}`);
}

console.log(`\n${rows.length} routes from ${appPath}`);
