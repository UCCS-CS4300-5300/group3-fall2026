import {readFileSync, existsSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {expect, test} from 'vitest';

const bundlePath = fileURLToPath(
  new URL('../core/static/core/screen/dist/screen.js', import.meta.url)
);

test('screen bundle references generated chunks that exist', () => {
  const bundle = readFileSync(bundlePath, 'utf8');
  const imports = [...bundle.matchAll(/(?:from|import)\s*(?:\(\s*)?["']([^"']+)["']/g)]
    .map((match) => match[1])
    .filter((specifier) => specifier.startsWith('.'));

  expect(imports.length).toBeGreaterThan(0);
  expect(imports).toContain('../../shared/chunks/blockly_setup.js');
  for (const specifier of imports) {
    const dependencyPath = resolve(dirname(bundlePath), specifier.split('?')[0]);
    expect(existsSync(dependencyPath), `${specifier} should exist`).toBe(true);
  }
});
