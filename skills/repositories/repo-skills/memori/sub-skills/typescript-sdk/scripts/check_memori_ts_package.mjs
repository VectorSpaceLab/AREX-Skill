#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';

const require = createRequire(import.meta.url);
const expected = {
  name: '@memorilabs/memori',
  version: '0.1.25-beta',
  engines: '>=20.19.0',
};

let installed = false;
let installedMetadata = null;
try {
  const entryPath = require.resolve('@memorilabs/memori');
  const packageRoot = dirname(dirname(entryPath));
  const pkgPath = resolve(packageRoot, 'package.json');
  installedMetadata = JSON.parse(readFileSync(pkgPath, 'utf8'));
  installed = true;
} catch {
  installed = false;
}

console.log(
  JSON.stringify(
    {
      expected,
      installed,
      installedMetadata,
    },
    null,
    2,
  ),
);
