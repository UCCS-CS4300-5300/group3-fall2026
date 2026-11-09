// @vitest-environment jsdom
import {beforeEach, expect, test} from 'vitest';
import {markBossExitComplete} from '../core/static/core/boss/boss_exit.js';

let button;
beforeEach(() => {
  document.body.innerHTML = '<form action="/missions/2/exit/" method="post"><button class="boss-exit" data-complete-url="/missions/2/next-room/" type="submit">Exit</button></form>';
  button = document.querySelector('button');
});

const destination = () => button.getAttribute('formaction') || button.form.getAttribute('action');

test('initial Exit uses the endpoint that preserves the run', () => {
  expect(destination()).toBe('/missions/2/exit/');
});

test('a failed lesson keeps the ordinary Exit destination', () => {
  markBossExitComplete({passed: false}, button);
  expect(destination()).toBe('/missions/2/exit/');
});

test('a lesson victory sends Exit to the completion and reset endpoint', () => {
  markBossExitComplete({passed: true}, button);
  expect(destination()).toBe('/missions/2/next-room/');
});

test('a successful punch sends Exit to the completion and reset endpoint', () => {
  markBossExitComplete({punched: true}, button);
  expect(destination()).toBe('/missions/2/next-room/');
});

test('a failed retry preserves the previous victory destination', () => {
  markBossExitComplete({passed: true}, button);
  markBossExitComplete({passed: false}, button);
  expect(destination()).toBe('/missions/2/next-room/');
});

test('an explicit lesson failure takes precedence over a punch flag', () => {
  markBossExitComplete({passed: false, punched: true}, button);
  expect(destination()).toBe('/missions/2/exit/');
});

test('the winning Exit turns gold', () => {
  markBossExitComplete({passed: true}, button);
  expect(button.classList.contains('boss-exit--defeated')).toBe(true);
});
