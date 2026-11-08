// @vitest-environment jsdom
import {beforeEach, expect, test, vi} from 'vitest';
import {installBossExitNavigation} from '../core/static/core/screen/boss_exit.js';

let button, cancelPendingRun;
beforeEach(() => {
  document.body.innerHTML = '<form><button class="boss-exit boss-exit--defeated" type="submit">Exit</button></form>';
  button = document.querySelector('button');
  cancelPendingRun = vi.fn();
  installBossExitNavigation(button, cancelPendingRun);
});

function submitExit() {
  const event = new SubmitEvent('submit', {cancelable: true, submitter: button});
  button.form.dispatchEvent(event);
  return event;
}

test('gold Exit navigates immediately without preventing submission', () => {
  expect(submitExit().defaultPrevented).toBe(false);
});

test('ordinary Exit also navigates immediately', () => {
  button.classList.remove('boss-exit--defeated');
  expect(submitExit().defaultPrevented).toBe(false);
});

test('Exit invalidates pending responses as navigation starts', () => {
  submitExit();
  expect(cancelPendingRun).toHaveBeenCalledTimes(1);
});

test('Exit keeps the submitter enabled for its completion endpoint', () => {
  submitExit();
  expect(button.disabled).toBe(false);
});

test('non-boss pages do not install boss navigation behavior', () => {
  installBossExitNavigation(null, cancelPendingRun);
  expect(cancelPendingRun).not.toHaveBeenCalled();
});
